"""Load the exact selected notebook artifact; never fit models during inference."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / 'models' / 'model_comparison'

@lru_cache(maxsize=1)
def selected_model():
    path = MODEL_DIR / 'rice_best_model.joblib'
    artifact = joblib.load(path)
    metadata = json.loads((MODEL_DIR / 'rice_best_model_metadata.json').read_text(encoding='utf-8'))
    if artifact['model_name'] != metadata['saved_model']:
        raise ValueError('Model và metadata không cùng phiên bản.')
    return artifact, hashlib.sha256(path.read_bytes()).hexdigest()

def predict_rows(rows):
    artifact, digest = selected_model()
    features, schema = artifact['feature_names'], artifact['preprocessing']
    frame = pd.DataFrame(rows)
    missing = set(features) - set(frame.columns)
    if missing:
        raise ValueError(f'Thiếu đặc trưng: {sorted(missing)}')
    frame = frame.loc[:, features].copy()
    for col in schema['numeric_features']:
        frame[col] = pd.to_numeric(frame[col].replace('', np.nan), errors='raise').astype(float)
        if np.isinf(frame[col]).any():
            raise ValueError(f'{col} chứa giá trị vô cực.')
    for col in schema['categorical_features']:
        values = frame[col]
        if col == 'adm1_code':
            numeric = pd.to_numeric(values, errors='raise')
            observed = numeric.dropna().to_numpy(dtype=float)
            if not np.isfinite(observed).all() or (observed % 1 != 0).any():
                raise ValueError('adm1_code phải là mã nguyên hoặc thiếu.')
            values = numeric.astype('Int64').astype('string')
        else:
            values = values.astype('string').str.strip().replace('', pd.NA)
        frame[col] = values.fillna(schema['categorical_missing_token']).astype(str)
    if artifact['kind'] == 'stacking':
        meta_input = pd.DataFrame({name: artifact['base_models'][name].predict(frame)
                                   for name in artifact['top4']}, index=frame.index)
        predictions = artifact['meta_learner'].predict(meta_input)
    else:
        predictions = artifact['model'].predict(frame)
    predictions = np.asarray(predictions, dtype=float)
    if not np.isfinite(predictions).all():
        raise ValueError('Mô hình trả về dự đoán không hữu hạn.')
    return {'model': artifact['model_name'], 'artifact_sha256': digest,
            'predictions': predictions.tolist()}
