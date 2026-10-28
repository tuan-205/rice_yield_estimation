/*
 BUOC 3.14
 KIEM TRA 13 TINH DONG BANG SONG CUU LONG
*/

// Danh sach ten tinh theo GAUL 2015
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

// Lay ranh gioi hanh chinh
var provinces = ee.FeatureCollection("FAO/GAUL/2015/level1");

// Loc Viet Nam
var vietnam = provinces.filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"));

// Loc 13 tinh
var mekong = vietnam.filter(ee.Filter.inList("ADM1_NAME", provinceNames));

// Kiem tra so luong
print("=== SO TINH TIM DUOC ===");
print(mekong.size());

// In danh sach tinh thuc te
print("=== DANH SACH TINH ===");
print(mekong.aggregate_array("ADM1_NAME").sort());

// Kiem tra tinh chua tim thay
var foundNames = mekong.aggregate_array("ADM1_NAME");

var missingNames = ee.List(provinceNames).removeAll(foundNames);

print("=== TINH CHUA TIM THAY ===");
print(missingNames);

// Hien thi ban do
Map.centerObject(mekong, 8);

Map.addLayer(
  mekong.style({
    color: "blue",
    fillColor: "3399FF22",
    width: 2,
  }),
  {},
  "13 tinh DBSCL",
);

print("=== HOAN THANH BUOC 3.14 ===");

/*
 BUOC 3.15.1
 HIEN THI TEN VA MA CUA 13 TINH
*/

// Sap xep theo ten tinh
var sortedProvinces = mekong.sort("ADM1_NAME");

// Lay danh sach ten tinh
var names = sortedProvinces.aggregate_array("ADM1_NAME");

// Lay danh sach ma tinh
var codes = sortedProvinces.aggregate_array("ADM1_CODE");

// Hien thi hai danh sach theo cung thu tu
print("=== TEN 13 TINH ===", names);
print("=== MA 13 TINH ===", codes);

// Tao bang de xem truc tiep
var provinceTable = sortedProvinces.map(function (f) {
  return ee.Feature(null, {
    ten_tinh: f.get("ADM1_NAME"),
    ma_tinh: f.get("ADM1_CODE"),
  });
});

print("=== BANG DOI CHIEU ===", provinceTable);

print("=== HOAN THANH BUOC 3.15.1 ===");

/*
 BUOC 3.16
 XUAT BANG MA TINH GAUL 2015
*/

// Bang doi chieu ten Kaggle va ten GAUL
var kaggleNames = ee.Dictionary({
  "An Giang": "An Giang",
  "Bac Lieu": "Bạc Liêu",
  "Ben Tre": "Bến Tre",
  "Ca Mau": "Cà Mau",
  "Can Tho city": "Cần Thơ",
  "Dong Thap": "Đồng Tháp",
  "Hau Giang": "Hậu Giang",
  "Kien Giang": "Kiên Giang",
  "Long An": "Long An",
  "Soc Trang": "Sóc Trăng",
  "Tien Giang": "Tiền Giang",
  "Tra Vinh": "Trà Vinh",
  "Vinh Long": "Vĩnh Long",
});

// Tao bang xuat
var exportTable = mekong.map(function (feature) {
  var gaulName = ee.String(feature.get("ADM1_NAME"));

  return ee.Feature(null, {
    tinh_thanh: kaggleNames.get(gaulName),
    gaul_name: gaulName,
    adm1_code: feature.get("ADM1_CODE"),
    boundary_version: "GAUL_2015",
  });
});

// Xuat CSV len Google Drive
Export.table.toDrive({
  collection: exportTable,
  description: "mekong_province_codes",
  fileNamePrefix: "mekong_province_codes",
  fileFormat: "CSV",
  selectors: ["tinh_thanh", "gaul_name", "adm1_code", "boundary_version"],
});

print("Da tao tac vu xuat CSV.");
