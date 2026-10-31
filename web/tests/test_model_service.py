import json
import unittest

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from web.api.app import app
from web.api.model_service import ROOT

class SelectedModelTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.rows = json.loads((ROOT / 'web/dist/data/history.json').read_text())

    def test_full_history_and_test_metrics(self):
        response = self.client.post('/v1/predict', json={'rows': self.rows})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        metadata = json.loads((ROOT / 'models/model_comparison/rice_best_model_metadata.json').read_text())
        bundle = json.loads((ROOT / 'web/dist/data/model.json').read_text())
        self.assertEqual(result['model'], metadata['saved_model'])
        self.assertEqual(result['artifact_sha256'], bundle['artifact_sha256'])
        expected = pd.read_csv(ROOT / 'reports/model_comparison/rice_test_predictions.csv')
        actual = [p for row, p in zip(self.rows, result['predictions']) if 2019 <= row['nam'] <= 2022]
        # CSV and history have different sort orders; match the original row keys.
        by_key = {(str(int(row['adm1_code'])), row['nam'], row['mua_vu']): p
                  for row, p in zip(self.rows, result['predictions'])}
        matched = [by_key[(str(int(row.adm1_code)), row.nam, row.mua_vu)]
                   for row in expected.itertuples()]
        np.testing.assert_allclose(matched, expected[f"prediction_{result['model']}_t_ha"], atol=1e-10)
        self.assertEqual(len(actual), 104)
        self.assertEqual(len(result['predictions']), 579)

    def test_missing_invalid_and_nullable_inputs(self):
        for rows in [[], [{}], [{**self.rows[0], 'adm1_code': 3326.5}],
                     [{**self.rows[0], 'rainfall_sum_mm': 'invalid'}]]:
            self.assertEqual(self.client.post('/v1/predict', json={'rows': rows}).status_code, 422)
        row = {**self.rows[0], 'adm1_code': '3326.0', 'ndvi_mean': None}
        self.assertEqual(self.client.post('/v1/predict', json={'rows': [row]}).status_code, 200)

if __name__ == '__main__':
    unittest.main()
