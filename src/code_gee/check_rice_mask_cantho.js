/*
 BUOC 3.34B.3
 KIEM TRA MAT NA LUA VIET NAM 2020

 Khu vuc: Can Tho
 Nguon: Harvard Dataverse
 Du lieu: rice_spatial_distribution.tif
*/

// 1. Doc ban do lua tu Earth Engine Assets
// THAY DUONG DAN BEN DUOI BANG ASSET ID CUA BAN
var riceMap = ee
  .Image("projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020")
  .select(0)
  .rename("rice_class");

// 2. Lay ranh gioi Can Tho - GAUL 2015
var canTho = ee
  .FeatureCollection("FAO/GAUL/2015/level1")
  .filter(ee.Filter.eq("ADM0_NAME", "Viet Nam"))
  .filter(ee.Filter.eq("ADM1_NAME", "Can Tho city"));

var region = canTho.geometry();

// 3. Kiem tra thong tin anh
print("=== TEN BANG ANH ===");
print(riceMap.bandNames());

print("=== HE TOA DO VA DO PHAN GIAI ===");
print(riceMap.projection());

print("=== KIEU DU LIEU PIXEL ===");
print(riceMap.bandTypes());

// 4. Kiem tra gia tri pixel bang lay mau
var samples = riceMap.sample({
  region: region,
  scale: 30,
  numPixels: 3000,
  seed: 42,
  tileScale: 4,
  geometries: false,
});

print("=== SO MAU HOP LE ===");
print(samples.size());

print("=== PHAN BO GIA TRI PIXEL ===");
print(samples.aggregate_histogram("rice_class"));

// 5. Tao mat na: pixel = 1 la lua
var riceMask = riceMap.eq(1).selfMask();

// 6. Hien thi tren ban do
Map.centerObject(canTho, 10);

Map.addLayer(
  riceMask.clip(region),
  { palette: ["00FF00"] },
  "Vung trong lua 2020",
);

Map.addLayer(
  canTho.style({
    color: "red",
    fillColor: "00000000",
    width: 2,
  }),
  {},
  "Ranh gioi Can Tho",
);

print("=== HOAN THANH KIEM TRA MAT NA ===");
