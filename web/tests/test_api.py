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

class LocalCredentialFlowTest(unittest.TestCase):
 def test_ui_and_api_share_server_and_no_key_route(self):
  client=TestClient(api.app)
  response=client.get('/')
  self.assertEqual(response.status_code,200)
  self.assertIn('Lúa Lab',response.text)
  self.assertEqual(client.get('/api/.env.example').status_code,404)
  self.assertEqual(client.get('/run_local.py').status_code,404)
 def test_configure_uses_path_without_copying_key(self):
  import tempfile
  from pathlib import Path
  from argparse import Namespace
  from web.run_local import configure,ROOT
  with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ):
   p=Path(temp)/'test-key.json';p.write_text('not a real credential')
   configure(Namespace(credentials=str(p),project='test-project',asset='test-asset'))
   self.assertEqual(os.environ['GOOGLE_APPLICATION_CREDENTIALS'],str(p.resolve()))
   self.assertEqual(os.environ['GEE_PROJECT_ID'],'test-project')
   with self.assertRaises(ValueError):configure(Namespace(credentials=str(p.parent/'missing.json'),project='p',asset='a'))
   with self.assertRaises(ValueError):configure(Namespace(credentials=str(ROOT/'web/dist/data/model.json'),project='p',asset='a'))
 def test_file_scopes_and_attached_adc(self):
  from web.api.gee_provider import GEEProvider
  import ee,google.auth
  for using_file in [True,False]:
   with patch.dict(os.environ,{'GOOGLE_APPLICATION_CREDENTIALS':'/test/key.json' if using_file else ''}),patch.object(google.auth,'default',return_value=(object(),'p')) as auth,patch.object(ee,'Initialize') as initialize:
    GEEProvider('project','asset')._initialize()
    if using_file:auth.assert_called_once_with(scopes=ee.oauth.SCOPES)
    else:auth.assert_called_once_with()
    self.assertEqual(initialize.call_args.kwargs['project'],'project')

if __name__=='__main__':unittest.main()
