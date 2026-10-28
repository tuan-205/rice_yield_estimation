/*
  BUOC 3.11 - KIEM TRA DU LIEU KHI TUONG
  Khu vuc: Can Tho (diem thu nghiem)
  Thoi gian: 01/01/2020 - 31/01/2020
*/

// 1. Toa do diem thu nghiem tai Can Tho
var point = ee.Geometry.Point([105.78, 10.03]);

Map.centerObject(point, 9);
Map.addLayer(point, { color: "red" }, "Diem Can Tho");

// 2. Khoang thoi gian thu nghiem
var startDate = "2020-01-01";
var endDate = "2020-02-01"; // Ngay ket thuc khong bao gom

// 3. Lay du lieu ERA5-Land
var era5 = ee
  .ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
  .filterDate(startDate, endDate)
  .select("temperature_2m");

// 4. Lay du lieu CHIRPS
var chirps = ee
  .ImageCollection("UCSB-CHG/CHIRPS/DAILY")
  .filterDate(startDate, endDate)
  .select("precipitation");

// 5. Kiem tra so ngay co du lieu
print("=== KIEM TRA SO ANH ===");
print("ERA5-Land:", era5.size());
print("CHIRPS:", chirps.size());

// 6. Tinh nhiet do trung binh (do C)
var temperature = era5.mean().subtract(273.15);

var tempValue = temperature.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: point,
  scale: 11132,
  maxPixels: 1e6,
});

print("=== NHIET DO TRUNG BINH (C) ===");
print(tempValue);

// 7. Tinh tong luong mua (mm)
var rainfall = chirps.sum();

var rainValue = rainfall.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: point,
  scale: 5566,
  maxPixels: 1e6,
});

print("=== TONG LUONG MUA (mm) ===");
print(rainValue);

// 8. Hien thi luong mua tren ban do
Map.addLayer(
  rainfall,
  {
    min: 0,
    max: 200,
    palette: ["white", "lightblue", "blue", "purple"],
  },
  "Tong luong mua 01/2020",
);

print("=== HOAN THANH KIEM TRA ===");

/*
  BUOC 3.12
  KIEM TRA RANH GIOI CAN THO
  VA TINH KHI TUONG TOAN TINH
*/

// 1. Lay ranh gioi hanh chinh GAUL 2015
var provinces = ee.FeatureCollection("FAO/GAUL/2015/level1");

// 2. Loc khu vuc Viet Nam
var vietnam = provinces.filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"));

// 3. Kiem tra ten cac tinh co chu "Can Tho"
var canTho = vietnam.filter(ee.Filter.stringContains("ADM1_NAME", "Can Tho"));

print("=== SO RANH GIOI CAN THO ===");
print(canTho.size());

print("=== THONG TIN RANH GIOI ===");
print(canTho);

// 4. Hien thi ranh gioi
Map.addLayer(
  canTho.style({
    color: "red",
    fillColor: "00000000",
    width: 2,
  }),
  {},
  "Ranh gioi Can Tho",
);

Map.centerObject(canTho, 9);

// 5. Tinh nhiet do trung binh theo ranh gioi
var tempProvince = temperature.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: canTho.geometry(),
  scale: 11132,
  maxPixels: 1e9,
});

print("=== NHIET DO TRUNG BINH CAN THO ===");
print(tempProvince);

// 6. Tinh luong mua trung binh theo ranh gioi
var rainProvince = rainfall.reduceRegion({
  reducer: ee.Reducer.mean(),
  geometry: canTho.geometry(),
  scale: 5566,
  maxPixels: 1e9,
});

print("=== TONG LUONG MUA TRUNG BINH CAN THO ===");
print(rainProvince);

print("=== HOAN THANH BUOC 3.13 ===");
