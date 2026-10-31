// UI-only fixture; real model/API parity is checked by test_model_service.py and model.test.mjs.
import fs from 'node:fs';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../dist/data/${name}.json`,import.meta.url),'utf8'));
const history=read('history'),reference=read('reference');
export function mockPrediction(options){
 const {rows}=JSON.parse(options.body);
 const predictions=rows.map(row=>{
  const i=history.findIndex(r=>String(r.adm1_code)===String(row.adm1_code)&&r.nam===row.nam&&r.mua_vu===row.mua_vu);
  if(i<0)throw Error('UI fixture supports historical rows only.');
  return reference.predictions[i];
 });
 return {ok:true,json:async()=>({...reference,predictions})};
}
