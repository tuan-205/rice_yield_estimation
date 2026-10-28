/*
 BUOC 3.22 - KIEM TRA KHI TUONG THEO THANG

 Khu vuc: Can Tho (GAUL 2015)
 Thoi gian: 01/2021 - 12/2022
 Nguon:
 - ERA5-Land: Nhiet do trung binh
 - CHIRPS: Tong luong mua
*/

// 1. Lay ranh gioi Can Tho
var provinces = ee.FeatureCollection("FAO/GAUL/2015/level1");

var canTho = provinces.filter(
  ee.Filter.and(
    ee.Filter.eq("ADM0_NAME", "Viet Nam"),
    ee.Filter.eq("ADM1_NAME", "Can Tho city"),
  ),
);

var region = canTho.geometry();

// 2. Nap du lieu khi tuong
var era5 = ee
  .ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
  .select("temperature_2m");

var chirps = ee
  .ImageCollection("UCSB-CHG/CHIRPS/DAILY")
  .select("precipitation");

// 3. Tao danh sach 24 thang
var firstMonth = ee.Date("2021-01-01");

var monthIndices = ee.List.sequence(0, 23);

// 4. Tinh khi tuong cho tung thang
var monthlyData = ee.FeatureCollection(
  monthIndices.map(function (index) {
    var start = firstMonth.advance(index, "month");
    var end = start.advance(1, "month");

    // Loc du lieu theo thang
    var tempImages = era5.filterDate(start, end);
    var rainImages = chirps.filterDate(start, end);

    // Nhiet do trung binh (Kelvin)
    var tempImage = tempImages.mean();

    // Tong luong mua (mm)
    var rainImage = rainImages.sum();

    // Trung binh khong gian tren Can Tho
    var tempStats = tempImage.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: region,
      scale: 11132,
      maxPixels: 1e9,
    });

    var rainStats = rainImage.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: region,
      scale: 5566,
      maxPixels: 1e9,
    });

    // Chuyen Kelvin sang Celsius
    var temperatureC = ee
      .Number(tempStats.get("temperature_2m"))
      .subtract(273.15);

    return ee.Feature(null, {
      month: start.format("YYYY-MM"),
      temperature_c: temperatureC,
      rainfall_mm: rainStats.get("precipitation"),
      era5_days: tempImages.size(),
      chirps_days: rainImages.size(),
    });
  }),
);

// 5. Hien thi ket qua
print("=== SO THANG ===");
print(monthlyData.size());

print("=== DU LIEU KHI TUONG THEO THANG ===");
print(monthlyData);

print("=== KIEM TRA 3 THANG DAU ===");
print(monthlyData.limit(3));

print("=== HOAN THANH BUOC 3.22 ===");

// 6. Hien thi khu vuc
Map.centerObject(canTho, 9);
Map.addLayer(canTho, { color: "red" }, "Can Tho");

/*
 BUOC 3.23
 XUAT DU LIEU KHI TUONG THEO THANG
 CAN THO - 2021 DEN 2022
*/

Export.table.toDrive({
  collection: monthlyData,

  description: "climate_monthly_can_tho_2021_2022",

  fileNamePrefix: "climate_monthly_can_tho_2021_2022",

  fileFormat: "CSV",

  selectors: [
    "month",
    "temperature_c",
    "rainfall_mm",
    "era5_days",
    "chirps_days",
  ],
});

print("=== DA TAO TAC VU XUAT CSV ===");
