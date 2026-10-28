/*
 BUOC 3.24
 THU NGHIEM KHI TUONG 13 TINH DBSCL
 Thang 01/2022
*/

// 1. Danh sach 13 tinh
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

// 2. Lay ranh gioi GAUL 2015
var provinces = ee
  .FeatureCollection("FAO/GAUL/2015/level1")
  .filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"))
  .filter(ee.Filter.inList("ADM1_NAME", provinceNames));

// 3. Khoang thoi gian
var start = "2022-01-01";
var end = "2022-02-01";

// 4. Du lieu ERA5-Land
var era5 = ee
  .ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
  .filterDate(start, end)
  .select("temperature_2m");

// 5. Du lieu CHIRPS
var chirps = ee
  .ImageCollection("UCSB-CHG/CHIRPS/DAILY")
  .filterDate(start, end)
  .select("precipitation");

// 6. Anh tong hop thang
var temperature = era5.mean().subtract(273.15).rename("temperature_c");

var rainfall = chirps.sum().rename("rainfall_mm");

// 7. Trich xuat theo tung tinh
var results = provinces.map(function (feature) {
  var region = feature.geometry();

  var temp = temperature
    .reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: region,
      scale: 11132,
      maxPixels: 1e9,
    })
    .get("temperature_c");

  var rain = rainfall
    .reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: region,
      scale: 5566,
      maxPixels: 1e9,
    })
    .get("rainfall_mm");

  return ee.Feature(null, {
    gaul_name: feature.get("ADM1_NAME"),
    adm1_code: feature.get("ADM1_CODE"),
    month: "2022-01",
    temperature_c: temp,
    rainfall_mm: rain,
    era5_days: era5.size(),
    chirps_days: chirps.size(),
  });
});

// 8. Kiem tra ket qua
print("=== SO TINH ===", results.size());

print("=== SO NGAY ERA5 ===", era5.size());
print("=== SO NGAY CHIRPS ===", chirps.size());

print(
  "=== SO TINH CO DU NHIET DO VA LUONG MUA ===",
  results.filter(ee.Filter.notNull(["temperature_c", "rainfall_mm"])).size(),
);

print("=== DANH SACH TINH ===", results.aggregate_array("gaul_name").sort());

print("=== DU LIEU 13 TINH ===", results);

Map.centerObject(provinces, 8);
Map.addLayer(
  provinces.style({
    color: "blue",
    fillColor: "3399FF22",
    width: 2,
  }),
  {},
  "13 tinh DBSCL",
);

print("=== HOAN THANH BUOC 3.24 ===");

/*
 BUOC 3.25
 XUAT DU LIEU KHI TUONG 13 TINH
 THANG 01/2022
*/

Export.table.toDrive({
  collection: results,

  description: "climate_13provinces_2022_01",

  fileNamePrefix: "climate_13provinces_2022_01",

  fileFormat: "CSV",

  selectors: [
    "adm1_code",
    "gaul_name",
    "month",
    "temperature_c",
    "rainfall_mm",
    "era5_days",
    "chirps_days",
  ],
});

print("=== DA TAO TAC VU XUAT CSV ===");
