/*
 BUOC 3.27
 DU LIEU KHI TUONG 13 TINH DBSCL
 01/1999 - 12/2004
*/

// 1. Danh sach tinh
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

// 2. Ranh gioi GAUL 2015
var provinces = ee
  .FeatureCollection("FAO/GAUL/2015/level1")
  .filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"))
  .filter(ee.Filter.inList("ADM1_NAME", provinceNames));

// 3. Nap du lieu khi tuong
var era5 = ee
  .ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
  .select("temperature_2m");

var chirps = ee
  .ImageCollection("UCSB-CHG/CHIRPS/DAILY")
  .select("precipitation");

// 4. Thoi gian
var firstMonth = ee.Date("2005-01-01");
var monthIndices = ee.List.sequence(0, 71);

// 5. Tao du lieu tung thang, tung tinh
var results = ee
  .FeatureCollection(
    monthIndices.map(function (index) {
      var start = firstMonth.advance(ee.Number(index), "month");
      var end = start.advance(1, "month");

      var tempCollection = era5.filterDate(start, end);
      var rainCollection = chirps.filterDate(start, end);

      var tempImage = tempCollection
        .mean()
        .subtract(273.15)
        .rename("temperature_c");

      var rainImage = rainCollection.sum().rename("rainfall_mm");

      return provinces.map(function (feature) {
        var region = feature.geometry();

        var temp = tempImage
          .reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: region,
            scale: 11132,
            maxPixels: 1e9,
          })
          .get("temperature_c");

        var rain = rainImage
          .reduceRegion({
            reducer: ee.Reducer.mean(),
            geometry: region,
            scale: 5566,
            maxPixels: 1e9,
          })
          .get("rainfall_mm");

        return ee.Feature(null, {
          adm1_code: feature.get("ADM1_CODE"),
          gaul_name: feature.get("ADM1_NAME"),
          month: start.format("YYYY-MM"),
          temperature_c: temp,
          rainfall_mm: rain,
          era5_days: tempCollection.size(),
          chirps_days: rainCollection.size(),
        });
      });
    }),
  )
  .flatten();

// 6. Kiem tra ket qua
print("=== TONG SO BAN GHI ===", results.size());

print(
  "=== SO TINH ===",
  results.aggregate_array("adm1_code").distinct().size(),
);

print("=== SO THANG ===", results.aggregate_array("month").distinct().size());

print(
  "=== BAN GHI DU DU LIEU ===",
  results.filter(ee.Filter.notNull(["temperature_c", "rainfall_mm"])).size(),
);

// 7. Xuat CSV
Export.table.toDrive({
  collection: results,
  description: "climate_13provinces_2005_2010",
  fileNamePrefix: "climate_13provinces_2005_2010",
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

print("=== HOAN THANH BUOC 3.27 ===");
