import importlib,os,unittest
from datetime import date
from unittest.mock import patch
from fastapi.testclient import TestClient
from web.api.gee_provider import require_complete,season_months
api=importlib.import_module('web.api.app')
class APITest(unittest.TestCase):
 def setUp(self):api._cache.clear();api.provider.cache_clear();self.client=TestClient(api.app)
 def test_health_no_credentials(self):
  with patch.dict(os.environ,{'GEE_PROJECT_ID':'','GEE_RICE_ASSET_ID':''}):
   response=self.client.get('/health');self.assertEqual(response.status_code,200);self.assertFalse(response.json()['gee_configured']);self.assertFalse(response.json()['authentication_verified'])
   response=self.client.post('/v1/monthly',json={'adm1_code':3326,'year':2022,'season':'dong_xuan'});self.assertEqual(response.status_code,503)
 def test_bounds_and_incomplete(self):
  for body in [{'adm1_code':0,'year':2022,'season':'dong_xuan'},{'adm1_code':3326,'year':2100,'season':'dong_xuan'},{'adm1_code':3326,'year':2022,'season':'invalid'}]:self.assertEqual(self.client.post('/v1/monthly',json=body).status_code,422)
  self.assertEqual(len(season_months(2026,'dong_xuan')),6)
  with self.assertRaises(ValueError):require_complete(2026,'he_thu-thu_dong',date(2026,10,29))
  require_complete(2026,'dong_xuan',date(2026,10,29))
 def test_success_cache_and_cors(self):
  class Fake:
   project_id='test-project';rice_asset_id='projects/test/assets/mask';calls=0
   def monthly(self,*args):self.calls+=1;return [{'adm1_code':3326,'month':'2022-04'}]
  fake=Fake()
  with patch.object(api,'provider',return_value=fake):
   for _ in range(2):
    response=self.client.post('/v1/monthly',json={'adm1_code':3326,'year':2022,'season':'dong_xuan'});self.assertEqual(response.status_code,200);self.assertEqual(response.json()['provenance']['vci_baseline'],'2000-2015')
   self.assertEqual(fake.calls,1)
  response=self.client.options('/v1/monthly',headers={'Origin':'http://localhost:8080','Access-Control-Request-Method':'POST'})
  self.assertEqual(response.headers['access-control-allow-origin'],'http://localhost:8080')
if __name__=='__main__':unittest.main()
