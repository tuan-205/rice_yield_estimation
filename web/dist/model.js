export const SEASONS={dong_xuan:'Đông xuân','he_thu-thu_dong':'Hè thu – Thu đông'};
export function windowFor(year,season){
 if(!Number.isInteger(+year)||+year<2000||+year>2100||!SEASONS[season])throw Error('Năm hoặc mùa vụ không hợp lệ.');
 const start=season==='dong_xuan'?`${year-1}-11`:`${year}-04`;
 const end=season==='dong_xuan'?`${year}-04`:`${year}-11`;
 const months=[];for(let y=+start.slice(0,4),m=+start.slice(5);`${y}-${String(m).padStart(2,'0')}`<=end;m++){if(m===13){m=1;y++;}const key=`${y}-${String(m).padStart(2,'0')}`;if(key<=end)months.push(key);}
 return {start,end,months,availableAfter:season==='dong_xuan'?`${year}-05-01`:`${year}-12-01`};
}
export function windowComplete(year,season,now=new Date()){
 const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now).map(p=>[p.type,p.value]));const today=`${parts.year}-${parts.month}-${parts.day}`;
 return today>=windowFor(year,season).availableAfter;
}
export function predict(model,row){
 const raw=model.schema.numeric_features.map(k=>{if(!(k in row))throw Error(`Thiếu cột ${k}.`);const v=row[k];if(v===null||v===undefined||v==='')return null;const n=Number(v);if(!Number.isFinite(n))throw Error(`${k} phải là số hữu hạn.`);return n;});
 const values=raw.map((v,i)=>v===null?model.imputer.statistics[i]:v);
 for(const i of model.imputer.indicator_features)values.push(raw[i]===null?1:0);
 const vector=values.map((v,i)=>(v-model.scaler.mean[i])/model.scaler.scale[i]);
 for(let i=0;i<model.schema.categorical_features.length;i++){
  const key=model.schema.categorical_features[i];let v=row[key];
  if(key==='adm1_code'&&v!=null&&v!==''){const n=Number(v);if(!Number.isInteger(n))throw Error('Mã tỉnh phải là số nguyên.');v=String(n);}
  else v=v==null||String(v).trim()===''?model.schema.categorical_missing_token:String(v).trim();
  for(const category of model.categories[i])vector.push(v===category?1:0);
 }
 if(vector.length!==model.regressor.coef.length)throw Error('Phiên bản mô hình không khớp.');
 const value=vector.reduce((s,v,i)=>s+v*model.regressor.coef[i],model.regressor.intercept);
 if(!Number.isFinite(value))throw Error('Không tính được kết quả từ dữ liệu đầu vào.');
 return value;
}
const number=v=>v==null||String(v).trim()===''?null:(Number.isFinite(Number(v))?Number(v):null);
const mean=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
const min=a=>a.length?Math.min(...a):null,max=a=>a.length?Math.max(...a):null;
export function aggregateMonthly(rows,code,year,season){
 const window=windowFor(year,season),matches=rows.filter(r=>String(Number(r.adm1_code))===String(Number(code))&&window.months.includes(r.month));
 if(matches.length!==window.months.length||new Set(matches.map(r=>r.month)).size!==window.months.length)throw Error(`Cần đúng ${window.months.length} tháng, không trùng, từ ${window.start} đến ${window.end}.`);
 for(const r of matches){if(r.rice_mask_year!=null&&+r.rice_mask_year!==2020)throw Error('Mặt nạ lúa CSV không khớp chuẩn 2020.');if(r.vci_baseline_years!=null&&r.vci_baseline_years!=='2000-2015')throw Error('Chuẩn VCI CSV không khớp 2000–2015.');}
 const temp=matches.map(r=>number(r.temperature_c)),rain=matches.map(r=>number(r.rainfall_mm));
 if([...temp,...rain].some(x=>x===null))throw Error('Dữ liệu khí hậu chưa đầy đủ trong cửa sổ vụ.');
 for(const r of matches){const y=+r.month.slice(0,4),m=+r.month.slice(5),days=new Date(Date.UTC(y,m,0)).getUTCDate();for(const k of ['era5_days','chirps_days'])if(r[k]!=null&&r[k]!==''&&+r[k]!==days)throw Error(`Nguồn khí hậu ${r.month} chưa đủ ngày.`);}
 const valid=matches.filter(r=>['ndvi_trailing3','evi_trailing3','vci'].every(k=>number(r[k])!==null));
 const quality=valid.filter(r=>number(r.coverage_pct)!==null&&+r.coverage_pct>=80);
 const vals=k=>quality.map(r=>+r[k]);
 return {adm1_code:String(Number(code)),nam:+year,mua_vu:season,window_start:window.start,window_end:window.end,window_months:window.months.length,
  temperature_mean_c:mean(temp),temperature_min_c:min(temp),temperature_max_c:max(temp),rainfall_sum_mm:rain.reduce((s,x)=>s+x,0),rainfall_max_month_mm:max(rain),rainy_months_100mm:rain.filter(v=>v>=100).length,
  ndvi_mean:mean(vals('ndvi_trailing3')),ndvi_max:max(vals('ndvi_trailing3')),evi_mean:mean(vals('evi_trailing3')),evi_max:max(vals('evi_trailing3')),vci_mean:mean(vals('vci')),vci_min:min(vals('vci')),
  vi_months_available:valid.length,vi_months_quality80:quality.length,vi_quality80_ratio:quality.length/window.months.length,vi_mean_coverage_pct:mean(vals('coverage_pct'))};
}
export function validateRow(model,row,knownCodes){
 const code=String(Number(row.adm1_code));if(!knownCodes.includes(code))throw Error('Tỉnh nằm ngoài 13 tỉnh trong dữ liệu mô hình.');
 if(!SEASONS[row.mua_vu])throw Error('Nhóm vụ phải là dong_xuan hoặc he_thu-thu_dong.');
 windowFor(+row.nam,row.mua_vu);
 for(const key of model.feature_names)if(!(key in row))throw Error(`CSV thiếu cột ${key}.`);
 const essential=['temperature_mean_c','temperature_min_c','temperature_max_c','rainfall_sum_mm','rainfall_max_month_mm','rainy_months_100mm','vi_months_available','vi_months_quality80','vi_quality80_ratio'];
 for(const k of essential)if(number(row[k])===null)throw Error(`Cần dữ liệu thực cho ${k}; không tự điền khí hậu hoặc độ phủ bị thiếu.`);
 if(+row.rainfall_sum_mm<0||+row.rainfall_max_month_mm<0)throw Error('Lượng mưa không được âm.');
 if(+row.temperature_min_c>+row.temperature_mean_c||+row.temperature_mean_c>+row.temperature_max_c)throw Error('Nhiệt độ min / trung bình / max không hợp lệ.');
 const months=windowFor(+row.nam,row.mua_vu).months.length;
 for(const k of ['vi_months_available','vi_months_quality80','rainy_months_100mm'])if(!Number.isInteger(+row[k])||+row[k]<0||+row[k]>months)throw Error(`${k} phải là số tháng hợp lệ.`);
 if(+row.vi_months_quality80>+row.vi_months_available||+row.vi_quality80_ratio<0||+row.vi_quality80_ratio>1)throw Error('Độ phủ vệ tinh không hợp lệ.');
 if(Math.abs(+row.vi_quality80_ratio-(+row.vi_months_quality80/months))>1e-5)throw Error('Tỷ lệ tháng đạt chất lượng không khớp số tháng.');
 for(const k of ['ndvi_mean','ndvi_max','evi_mean','evi_max']){const v=number(row[k]);if(v!==null&&(v<-.2||v>1))throw Error(`${k} ngoài khoảng hợp lệ.`);}
 for(const k of ['vci_mean','vci_min','vi_mean_coverage_pct']){const v=number(row[k]);if(v!==null&&(v<0||v>100))throw Error(`${k} ngoài khoảng 0–100.`);}
 for(const k of model.schema.numeric_features)if(row[k]!==null&&row[k]!==''&&!Number.isFinite(Number(row[k])))throw Error(`${k} phải là số hữu hạn.`);
 return row;
}
export function parseCSV(text){
 text=text.replace(/^\uFEFF/,'');const rows=[];let row=[],field='',quoted=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}else if(c===','&&!quoted){row.push(field);field='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(field);if(row.some(v=>v.trim()))rows.push(row);row=[];field='';}else field+=c;}
 if(quoted)throw Error('CSV có dấu ngoặc kép chưa đóng.');row.push(field);if(row.some(v=>v.trim()))rows.push(row);
 if(rows.length<2)throw Error('CSV cần dòng tiêu đề và ít nhất một dòng dữ liệu.');const headers=rows.shift().map(x=>x.trim());
 if(new Set(headers).size!==headers.length)throw Error('CSV bị trùng tên cột.');
 return rows.map((r,i)=>{if(r.length!==headers.length)throw Error(`Dòng ${i+2} không khớp số cột.`);return Object.fromEntries(headers.map((k,j)=>[k,r[j].trim()===''?null:r[j].trim()]));});
}
export function makeCSV(rows){const headers=Object.keys(rows[0]);const escape=v=>v==null?'':`"${String(v).replaceAll('"','""')}"`;return '\uFEFF'+[headers.map(escape).join(','),...rows.map(r=>headers.map(k=>escape(r[k])).join(','))].join('\r\n');}
