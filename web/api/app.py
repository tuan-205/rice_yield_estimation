from datetime import datetime
from zoneinfo import ZoneInfo
from functools import lru_cache
import os,time,threading,logging
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel,Field
from typing import Literal
from .gee_provider import GEEProvider,PROVINCE_CODES,require_complete
app=FastAPI(title='Lúa Lab · GEE data API',version='1.0.0')
origins=[o.strip().rstrip('/') for o in os.getenv('WEB_ALLOWED_ORIGINS','http://localhost:8080,http://127.0.0.1:8080').split(',') if o.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Content-Type'])
class SeasonRequest(BaseModel):
    adm1_code:int
    year:int=Field(ge=2000,le=2100)
    season:Literal['dong_xuan','he_thu-thu_dong']
@lru_cache(maxsize=1)
def provider():
    project=os.getenv('GEE_PROJECT_ID','').strip();asset=os.getenv('GEE_RICE_ASSET_ID','').strip()
    if not project or not asset:raise HTTPException(503,'Chưa cấu hình GEE_PROJECT_ID và GEE_RICE_ASSET_ID ở máy chủ.')
    return GEEProvider(project,asset)
@app.get('/health')
def health():
    return {'service':'lua-lab-gee-api','gee_configured':bool(os.getenv('GEE_PROJECT_ID') and os.getenv('GEE_RICE_ASSET_ID')),
            'authentication_verified':False,'note':'Actual source permissions are verified only on a successful data request.'}
_cache={};_lock=threading.Lock()
@app.post('/v1/monthly')
def monthly(request:SeasonRequest):
    if request.adm1_code not in PROVINCE_CODES:raise HTTPException(422,'Mô hình chỉ hỗ trợ 13 tỉnh theo ranh giới dữ liệu huấn luyện.')
    try:require_complete(request.year,request.season,datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).date())
    except ValueError as e:raise HTTPException(422,str(e))
    source=provider();key=(request.adm1_code,request.year,request.season)
    with _lock:
        hit=_cache.get(key)
        if hit and time.monotonic()-hit[0]<86400:return hit[1]
        try:rows=source.monthly(*key)
        except Exception:
            logging.exception('GEE feature extraction failed')
            raise HTTPException(502,'Không đọc được GEE. Kiểm tra ADC, project đăng ký Earth Engine, quyền asset và hạn mức tính toán ở backend.')
        response={'rows':rows,'provenance':{'source':'Google Earth Engine','project_id':source.project_id,'rice_asset_id':source.rice_asset_id,
                  'vci_baseline':'2000-2015','rice_mask_year':2020,'vi_scale_m':500,
                  'retrieved_at':datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()}}
        if len(_cache)>=128:_cache.clear()
        _cache[key]=(time.monotonic(),response)
        return response

class PredictionRequest(BaseModel):
    rows:list[dict]=Field(min_length=1,max_length=1000)

@app.post('/v1/predict')
def predict(request:PredictionRequest):
    from .model_service import predict_rows
    try:
        return predict_rows(request.rows)
    except FileNotFoundError:
        raise HTTPException(503,'Chưa có mô hình đã lưu. Chạy notebook huấn luyện trước.')
    except (ValueError, TypeError) as error:
        raise HTTPException(422,str(error))

# Only serve built web assets. Credential files and backend source are never exposed.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[1] / "dist", html=True, check_dir=False), name="frontend")
