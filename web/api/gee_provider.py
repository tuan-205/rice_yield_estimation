"""Monthly GEE features compatible with the existing notebook's source data.
No Earth Engine calls run at import. Credentials use Application Default Credentials.
"""
from __future__ import annotations
from datetime import date
from functools import lru_cache
import calendar, os
PROVINCE_CODES={3326,3330,3332,3339,3343,3356,3362,3377,3384,3386,3388,73933,73937}

def season_months(year:int,season:str):
    if season=='dong_xuan':return [(year-1,11),(year-1,12)]+[(year,m) for m in range(1,5)]
    if season=='he_thu-thu_dong':return [(year,m) for m in range(4,12)]
    raise ValueError('Nhóm vụ không hợp lệ.')

def require_complete(year:int,season:str,today:date):
    last_year,last_month=season_months(year,season)[-1]
    if today<=date(last_year,last_month,calendar.monthrange(last_year,last_month)[1]):
        raise ValueError('Cửa sổ vụ chưa kết thúc; không lấy dữ liệu nửa vụ để ước lượng cả vụ.')

class GEEProvider:
    def __init__(self,project_id:str,rice_asset_id:str):
        self.project_id=project_id;self.rice_asset_id=rice_asset_id
        self._initialized=False
    def _initialize(self):
        if self._initialized:return
        import ee,google.auth
        credentials,_=google.auth.default()
        ee.Initialize(credentials=credentials,project=self.project_id)
        self._initialized=True
    def monthly(self,code:int,year:int,season:str):
        self._initialize()
        import ee
        region=ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME','Viet Nam')).filter(ee.Filter.eq('ADM1_CODE',code)).geometry()
        terra=ee.ImageCollection('MODIS/061/MOD13Q1').filterDate('2000-01-01',f'{year+1}-01-01')
        aqua=ee.ImageCollection('MODIS/061/MYD13Q1').filterDate('2000-01-01',f'{year+1}-01-01')
        projection=terra.first().select('NDVI').projection();target_projection=projection.atScale(500)
        all_provinces=ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME','Viet Nam')).filter(ee.Filter.inList('ADM1_CODE',sorted(PROVINCE_CODES)))
        rice=ee.Image(self.rice_asset_id).select(0).eq(1).unmask(0).clip(all_provinces.geometry().bounds().buffer(1000))
        mask=rice.reduceResolution(reducer=ee.Reducer.mean(),maxPixels=4096).reproject(crs=target_projection).gte(0.6).selfMask().rename('rice_mask')
        def preprocess(image):
            return image.select(['NDVI','EVI']).multiply(0.0001).toFloat().updateMask(image.select('SummaryQA').lte(1)).copyProperties(image,['system:time_start'])
        vegetation=terra.map(preprocess).merge(aqua.map(preprocess)).cast({'NDVI':'float','EVI':'float'},['NDVI','EVI'])
        empty=ee.Image.constant([0,0]).rename(['NDVI','EVI']).toFloat().updateMask(ee.Image.constant(0)).setDefaultProjection(projection)
        def trailing(start):
            images=ee.ImageCollection.fromImages([empty]).merge(vegetation.filterDate(start.advance(-2,'month'),start.advance(1,'month'))).cast({'NDVI':'float','EVI':'float'},['NDVI','EVI'])
            return images.mean().toFloat().rename(['NDVI','EVI']).setDefaultProjection(projection)
        era5=ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').select('temperature_2m')
        chirps=ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').select('precipitation')
        reducer=ee.Reducer.mean().combine(reducer2=ee.Reducer.count(),sharedInputs=True)
        features=[]
        for y,m in season_months(year,season):
            start=ee.Date.fromYMD(y,m,1);end=start.advance(1,'month');vi=trailing(start)
            historical=ee.ImageCollection.fromImages([trailing(ee.Date.fromYMD(h,m,1)).select('NDVI') for h in range(2000,2016)]).reduce(ee.Reducer.minMax())
            low=historical.select('NDVI_min');span=historical.select('NDVI_max').subtract(low)
            vci=vi.select('NDVI').subtract(low).divide(span.where(span.eq(0),1)).multiply(100).clamp(0,100).updateMask(span.gt(0.01)).rename('vci')
            image=ee.Image.cat([vi.select('NDVI').rename('ndvi_trailing3'),vi.select('EVI').rename('evi_trailing3'),vci]).updateMask(mask).setDefaultProjection(projection).addBands(mask)
            stats=image.reduceRegion(reducer=reducer,geometry=region,crs=target_projection,scale=500,maxPixels=1000000000,tileScale=8)
            temp=era5.filterDate(start,end);rain=chirps.filterDate(start,end)
            t=temp.mean().subtract(273.15).rename('temperature_c').reduceRegion(reducer=ee.Reducer.mean(),geometry=region,scale=11132,maxPixels=1000000000).get('temperature_c')
            r=rain.sum().rename('rainfall_mm').reduceRegion(reducer=ee.Reducer.mean(),geometry=region,scale=5566,maxPixels=1000000000).get('rainfall_mm')
            props={'adm1_code':code,'month':f'{y}-{m:02d}','temperature_c':t,'rainfall_mm':r,'era5_days':temp.size(),'chirps_days':rain.size(),
                   'ndvi_trailing3':stats.get('ndvi_trailing3_mean'),'evi_trailing3':stats.get('evi_trailing3_mean'),'vci':stats.get('vci_mean'),
                   'mask_pixels':stats.get('rice_mask_count'),'ndvi_valid_pixels':stats.get('ndvi_trailing3_count'),'evi_valid_pixels':stats.get('evi_trailing3_count'),'vci_valid_pixels':stats.get('vci_count')}
            features.append(ee.Feature(None,props))
        result=ee.FeatureCollection(features).getInfo()
        rows=[]
        for feature in result['features']:
            row=feature['properties'];mask_pixels=row.get('mask_pixels') or 0
            complete_vi=all(row.get(k) is not None for k in ['ndvi_trailing3','evi_trailing3','vci'])
            if mask_pixels>0 and complete_vi:
                coverage=round(100*min(row.get(k) or 0 for k in ['ndvi_valid_pixels','evi_valid_pixels','vci_valid_pixels'])/mask_pixels,4)
                row['coverage_pct']=coverage;row['quality_flag']='ok_80pct' if coverage>=80 else 'review_below_80pct'
            else:row['coverage_pct']=None;row['quality_flag']='no_vi' if not complete_vi else 'partial_vi'
            rows.append(row)
        return rows
