/*
 BUOC 3.34B.10
 NDVI/EVI VUNG LUA - 13 TINH DBSCL
 Terra + Aqua, cua so 3 thang
 Giai doan 2021-2022

 Xuat bang tam dang rong: 13 dong.
*/

// 1. DANH SACH 13 TINH
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
  .filter(ee.Filter.inList("ADM1_NAME", provinceNames));

// 2. BAN DO LUA NAM 2020
// THAY BANG ASSET ID THUC TE
var riceMap = ee
  .Image("projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020")
  .select(0);

// 3. DOC TERRA + AQUA
// Lay them 11-12/2020 cho cua so dau 2021
var terraRaw = ee
  .ImageCollection("MODIS/061/MOD13Q1")
  .filterDate("2020-11-01", "2023-01-01");

var aquaRaw = ee
  .ImageCollection("MODIS/061/MYD13Q1")
  .filterDate("2020-11-01", "2023-01-01");

var projection = terraRaw.first().select("NDVI").projection();

// 4. MAT NA LUA >= 60%
var riceBinary = riceMap
  .eq(1)
  .unmask(0)
  .clip(provinces.geometry().bounds().buffer(1000));

var riceMask = riceBinary
  .reduceResolution({
    reducer: ee.Reducer.mean(),
    maxPixels: 4096,
  })
  .reproject({ crs: projection })
  .gte(0.6)
  .selfMask()
  .rename("rice_mask");

// 5. LOC CHAT LUONG
function prepare(collection) {
  return collection.map(function (image) {
    var qa = image.select("SummaryQA").lte(1);

    return image
      .select(["NDVI", "EVI"])
      .multiply(0.0001)
      .updateMask(qa)
      .copyProperties(image, ["system:time_start"]);
  });
}

var combined = prepare(terraRaw).merge(prepare(aquaRaw));

// 6. ANH 3 THANG CHO TUNG THANG
var firstMonth = ee.Date("2021-01-01");
var indices = ee.List.sequence(0, 23);

var monthlyImages = indices.map(function (i) {
  var start = firstMonth.advance(ee.Number(i), "month");

  var end = start.advance(1, "month");

  var trailing = combined
    .filterDate(start.advance(-2, "month"), end)
    .mean()
    .rename(["ndvi_trailing3", "evi_trailing3"])
    .updateMask(riceMask);

  return trailing.set("system:index", start.format("YYYY_MM"));
});

// 7. GOM 24 THANG THANH 1 ANH
var stacked = ee.ImageCollection.fromImages(monthlyImages)
  .sort("system:index")
  .toBands()
  .addBands(riceMask);

// 8. TINH MEAN VA COUNT THEO 13 TINH
var reducer = ee.Reducer.mean().combine({
  reducer2: ee.Reducer.count(),
  sharedInputs: true,
});

var stats = stacked.reduceRegions({
  collection: provinces,
  reducer: reducer,
  crs: projection,
  scale: 500,
  tileScale: 8,
  maxPixelsPerRegion: 10000000,
});

// Bo geometry lon, chi giu thuoc tinh
var results = stats.map(function (feature) {
  return ee.Feature(null, feature.toDictionary());
});

// 9. KIEM TRA THONG SO NHE
print("=== SO TINH ===");
print(provinces.size());

print("=== SO BANG ANH ===");
print(stacked.bandNames().size());

print("=== DA TAO TAC VU XUAT ===");

// 10. XUAT CSV
Export.table.toDrive({
  collection: results,
  description: "rice_vi_13provinces_2021_2022_wide",
  fileNamePrefix: "rice_vi_13provinces_2021_2022_wide",
  fileFormat: "CSV",
});
