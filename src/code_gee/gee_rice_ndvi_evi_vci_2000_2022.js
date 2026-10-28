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
var START_YEAR = 2000;
var END_YEAR = 2022;

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
  .filterDate("2000-01-01", "2023-01-01");

var aquaRaw = ee
  .ImageCollection("MODIS/061/MYD13Q1")
  .filterDate("2000-01-01", "2023-01-01");

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

// 8. XUAT TUNG NAM
for (var year = START_YEAR; year <= END_YEAR; year++) {
  var imagesForYear = [];

  var selectors = ["ADM1_CODE", "ADM1_NAME", "rice_mask_count"];

  for (var month = 1; month <= 12; month++) {
    var mm = ("0" + month).slice(-2);
    var prefix = year + "_" + mm;

    var start = ee.Date.fromYMD(year, month, 1);

    var currentVI = trailing3(start);

    var ndvi = currentVI.select("NDVI");
    var evi = currentVI.select("EVI");

    // VCI: so voi gia tri cuc tri lich su
    // cua cung thang trong 2000-2015
    var historical = baselineByMonth[month];

    var minHist = historical.select("NDVI_hist_min");

    var maxHist = historical.select("NDVI_hist_max");

    var span = maxHist.subtract(minHist);

    var vci = ndvi
      .subtract(minHist)
      .divide(span.where(span.eq(0), 1))
      .multiply(100)
      .clamp(0, 100)
      .updateMask(span.gt(MIN_HIST_RANGE))
      .rename("vci");

    // Ap dung mat na lua
    var image = ee.Image.cat([
      ndvi.rename("ndvi_trailing3"),
      evi.rename("evi_trailing3"),
      vci,
    ])
      .updateMask(riceMask)
      .setDefaultProjection(modisProjection)
      .set("system:index", prefix);

    imagesForYear.push(image);

    // Danh sach cot CSV
    ["ndvi_trailing3", "evi_trailing3", "vci"].forEach(function (bandName) {
      selectors.push(prefix + "_" + bandName + "_mean");
      selectors.push(prefix + "_" + bandName + "_count");
    });
  }

  // 12 thang x 3 chi so + 1 mat na = 37 bang
  var stacked = ee.ImageCollection.fromImages(imagesForYear)
    .sort("system:index")
    .toBands()
    .addBands(riceMask);

  // Mot phep reduceRegions cho moi nam
  var provinceStats = stacked.reduceRegions({
    collection: provinces,
    reducer: spatialReducer,
    crs: targetProjection,
    scale: SCALE_M,
    tileScale: 8,
    maxPixelsPerRegion: 10000000,
  });

  // Chi giu thuoc tinh, bo geometry
  var results = provinceStats.map(function (feature) {
    return ee.Feature(null, feature.toDictionary(selectors));
  });

  var fileName = "rice_vi_vci_" + year + "_wide";

  Export.table.toDrive({
    collection: results,
    description: fileName,
    fileNamePrefix: fileName,
    fileFormat: "CSV",
    selectors: selectors,
  });
}

// 9. THONG BAO
print("=== SO TINH ===");
print(provinces.size());

print("=== SO TASK DUOC TAO ===");
print(END_YEAR - START_YEAR + 1);

print("=== HOAN THANH TAO TASK ===");
