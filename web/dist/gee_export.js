// LÚA LAB — xuất dữ liệu THÁNG cho một tỉnh và vụ; nhập CSV vào web.
// 1. Chọn Cloud Project đã đăng ký Earth Engine trong Code Editor.
// 2. Sửa ba giá trị dưới đây, kiểm tra RICE_ASSET rồi Run và chạy task Export.
var YIELD_YEAR = 2026;
var SEASON = 'dong_xuan'; // hoặc 'he_thu-thu_dong'
var PROVINCE_CODE = 3326; // An Giang, theo mã GAUL trong web
/*
 NDVI / EVI / VCI - 13 tinh DBSCL, 2000-2022

 - MODIS Terra + Aqua
 - Mat na lua Viet Nam nam 2020
 - Cua so 3 thang: thang hien tai va 2 thang truoc
 - VCI theo baseline 2000-2015, cung thang
 - Thong ke o do phan giai 500 m
 - Moi nam xuat mot file CSV
*/

// THAY ASSET ID CUA BAN
var RICE_ASSET =
  "projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020";

// Chay thu nam 2020 truoc:
// var START_YEAR = 2020;
// var END_YEAR = 2020;

// Chay day du:
var START_YEAR = 2026;
var END_YEAR = 2026;

var BASELINE_START = 2000;
var BASELINE_END = 2015;

var SCALE_M = 500;
var RICE_THRESHOLD = 0.6;
var MIN_HIST_RANGE = 0.01;

// 1. RANH GIOI 13 TINH
var provinceNames = [
  "An Giang",
  "Bac Lieu",
  "Ben Tre",
  "Ca Mau",
  "Can Tho city",
  "Dong Thap",
  "Hau Giang",
  "Kien Giang",
  "Long An",
  "Soc Trang",
  "Tien Giang",
  "Tra Vinh",
  "Vinh Long",
];

var provinces = ee
  .FeatureCollection("FAO/GAUL/2015/level1")
  .filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"))
  .filter(ee.Filter.inList("ADM1_NAME", provinceNames))
  .select(["ADM1_CODE", "ADM1_NAME"]);

// 2. DOC DU LIEU MODIS
var terraRaw = ee
  .ImageCollection("MODIS/061/MOD13Q1")
  .filterDate("2000-01-01", (YIELD_YEAR + 1) + "-01-01");

var aquaRaw = ee
  .ImageCollection("MODIS/061/MYD13Q1")
  .filterDate("2000-01-01", (YIELD_YEAR + 1) + "-01-01");

var modisProjection = terraRaw.first().select("NDVI").projection();

var targetProjection = modisProjection.atScale(SCALE_M);

// 3. MAT NA VUNG LUA
var riceMap = ee.Image(RICE_ASSET).select(0);

var riceBinary = riceMap
  .eq(1)
  .unmask(0)
  .clip(provinces.geometry().bounds().buffer(1000));

// Tinh ty le dien tich lua truc tiep tren luoi 500 m
var riceFraction = riceBinary
  .reduceResolution({
    reducer: ee.Reducer.mean(),
    maxPixels: 4096,
  })
  .reproject({
    crs: targetProjection,
  })
  .rename("rice_fraction");

var riceMask = riceFraction.gte(RICE_THRESHOLD).selfMask().rename("rice_mask");

// 4. LOC CHAT LUONG NDVI/EVI

function preprocess(collection) {
  return collection.map(function (image) {
    var qualityMask = image.select("SummaryQA").lte(1);

    return image
      .select(["NDVI", "EVI"])
      .multiply(0.0001)
      .toFloat()
      .updateMask(qualityMask)
      .copyProperties(image, ["system:time_start"]);
  });
}

var vegetation = preprocess(terraRaw)
  .merge(preprocess(aquaRaw))
  .cast({ NDVI: "float", EVI: "float" }, ["NDVI", "EVI"]);

// Anh rong, dung cho cac thang khong co MODIS

var emptyVI = ee.Image.constant([0, 0])
  .rename(["NDVI", "EVI"])
  .toFloat()
  .updateMask(ee.Image.constant(0))
  .setDefaultProjection(modisProjection);

// 5. HAM TINH NDVI/EVI CUA SO 3 THANG

function trailing3(date) {
  var filtered = vegetation.filterDate(
    date.advance(-2, "month"),
    date.advance(1, "month"),
  );

  var images = ee.ImageCollection.fromImages([emptyVI])
    .merge(filtered)
    .cast({ NDVI: "float", EVI: "float" }, ["NDVI", "EVI"]);

  return images
    .mean()
    .toFloat()
    .rename(["NDVI", "EVI"])
    .setDefaultProjection(modisProjection);
}

// 6. TAO CHUAN VCI THEO TUNG THANG
var baselineByMonth = {};

for (var monthNum = 1; monthNum <= 12; monthNum++) {
  var currentMonth = monthNum;

  var historicalNDVI = ee.ImageCollection.fromImages(
    ee.List.sequence(BASELINE_START, BASELINE_END).map(function (year) {
      return trailing3(
        ee.Date.fromYMD(ee.Number(year), currentMonth, 1),
      ).select("NDVI");
    }),
  );

  baselineByMonth[monthNum] = historicalNDVI
    .reduce(ee.Reducer.minMax())
    .rename(["NDVI_hist_min", "NDVI_hist_max"])
    .setDefaultProjection(modisProjection);
}

// 7. BO THONG KE TRUNG BINH VA SO PIXEL
var spatialReducer = ee.Reducer.mean().combine({
  reducer2: ee.Reducer.count(),
  sharedInputs: true,
});


var selected = ee.Feature(provinces.filter(ee.Filter.eq('ADM1_CODE', PROVINCE_CODE)).first());
var region = selected.geometry();
var monthStart = SEASON === 'dong_xuan' ? ee.Date.fromYMD(YIELD_YEAR - 1, 11, 1) : ee.Date.fromYMD(YIELD_YEAR, 4, 1);
var numberMonths = SEASON === 'dong_xuan' ? 6 : 8;
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').select('temperature_2m');
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY').select('precipitation');
var results = ee.FeatureCollection(ee.List.sequence(0, numberMonths - 1).map(function(i) {
 var start=monthStart.advance(ee.Number(i),'month'), end=start.advance(1,'month');
 var month=ee.Number(start.get('month')).toInt();
 // BaselineByMonth is a JS dictionary; use a server-side list to select the month.
 var baselines=ee.List([]);
 for(var j=1;j<=12;j++) baselines=baselines.add(baselineByMonth[j]);
 var baseline=ee.Image(baselines.get(month.subtract(1))),vi=trailing3(start);
 var low=baseline.select('NDVI_hist_min'),span=baseline.select('NDVI_hist_max').subtract(low);
 var vci=vi.select('NDVI').subtract(low).divide(span.where(span.eq(0),1)).multiply(100).clamp(0,100).updateMask(span.gt(MIN_HIST_RANGE)).rename('vci');
 var image=ee.Image.cat([vi.select('NDVI').rename('ndvi_trailing3'),vi.select('EVI').rename('evi_trailing3'),vci]).updateMask(riceMask).setDefaultProjection(modisProjection).addBands(riceMask);
 var stats=image.reduceRegion({reducer:spatialReducer,geometry:region,crs:targetProjection,scale:SCALE_M,tileScale:8,maxPixels:1e9});
 var temp=era5.filterDate(start,end),rain=chirps.filterDate(start,end);
 var t=temp.mean().subtract(273.15).rename('temperature_c').reduceRegion({reducer:ee.Reducer.mean(),geometry:region,scale:11132,maxPixels:1e9}).get('temperature_c');
 var r=rain.sum().rename('rainfall_mm').reduceRegion({reducer:ee.Reducer.mean(),geometry:region,scale:5566,maxPixels:1e9}).get('rainfall_mm');
 var maskCount=ee.Number(stats.get('rice_mask_count',0));
 var counts=ee.List([stats.get('ndvi_trailing3_count',0),stats.get('evi_trailing3_count',0),stats.get('vci_count',0)]);
 var minCount=ee.Number(counts.reduce(ee.Reducer.min()));
 var coverage=ee.Algorithms.If(maskCount.gt(0),minCount.divide(maskCount.max(1)).multiply(100).multiply(10000).round().divide(10000),null);
 return ee.Feature(null,{adm1_code:PROVINCE_CODE,month:start.format('YYYY-MM'),temperature_c:t,rainfall_mm:r,era5_days:temp.size(),chirps_days:rain.size(),
 ndvi_trailing3:stats.get('ndvi_trailing3_mean'),evi_trailing3:stats.get('evi_trailing3_mean'),vci:stats.get('vci_mean'),coverage_pct:coverage,
 rice_mask_year:2020,vci_baseline_years:'2000-2015'});
}));
print('Tháng quan sát:', results);
print('Chỉ dùng khi đã đủ toàn bộ cửa sổ mùa vụ; web kiểm tra đủ ngày khí hậu và tháng dữ liệu.');
Export.table.toDrive({collection:results,description:'lua_lab_'+PROVINCE_CODE+'_'+YIELD_YEAR+'_'+SEASON,fileFormat:'CSV',selectors:['adm1_code','month','temperature_c','rainfall_mm','era5_days','chirps_days','ndvi_trailing3','evi_trailing3','vci','coverage_pct','rice_mask_year','vci_baseline_years']});
