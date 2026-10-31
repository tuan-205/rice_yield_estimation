"""Export selected-model metadata and data for the Python inference backend."""
from pathlib import Path
import hashlib,json,sys
import joblib,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'web'/'dist'/'data'
OUT.mkdir(parents=True,exist_ok=True)
artifact=joblib.load(ROOT/'models/model_comparison/rice_best_model.joblib')
meta=json.loads((ROOT/'models/model_comparison/rice_best_model_metadata.json').read_text())
df=pd.read_csv(ROOT/'data/processed/rice_ml_features_2000_2022.csv')
# JSON cannot represent NaN; preserve missing values as null for browser imputation.
def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
    return v
model=clean({'name':artifact['model_name'],'feature_names':artifact['feature_names'],'schema':artifact['preprocessing'],
    'engine':'python', 'training_years':meta['final_fit_period'],
    'evaluation_years':meta['test_period'],'evaluation_metrics':meta['saved_model_metrics'],
    'selection_rule':meta['saved_model_selection_rule'],'votes':meta['selected_model_top3_appearances'],
    'vci_baseline':[2000,2015],'rice_mask_year':2020,
    'artifact_sha256':hashlib.sha256((ROOT/'models/model_comparison/rice_best_model.joblib').read_bytes()).hexdigest(),
    'numeric_ranges':{k:[df[k].min(),df[k].max()] for k in artifact['preprocessing']['numeric_features']}})
(OUT/'model.json').write_text(json.dumps(model,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'history.json').write_text(json.dumps(clean(df.to_dict('records')),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
provinces=df[['adm1_code','tinh_thanh']].drop_duplicates().sort_values('tinh_thanh')
(OUT/'provinces.json').write_text(provinces.to_json(orient='records',force_ascii=False),encoding='utf-8')
metrics=pd.read_csv(ROOT/'reports/model_comparison/rice_model_ranking.csv')
(OUT/'comparison.json').write_text(json.dumps(clean(metrics.to_dict('records')),ensure_ascii=False),encoding='utf-8')
# Reference predictions from original Python pipeline for every row, never used as browser prediction output.
sys.path.insert(0,str(ROOT))
from web.api.model_service import predict_rows
reference=clean(predict_rows(clean(df.to_dict('records'))))
(OUT/'reference.json').write_text(json.dumps(reference),encoding='utf-8')
print('Exported model, 579 observations, provinces, ranking and Python parity reference to',OUT)
