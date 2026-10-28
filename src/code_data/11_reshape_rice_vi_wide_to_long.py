
import csv
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE / "data" / "interim"

INPUT_FILE = DATA_DIR / (
    "rice_vi_13provinces_2021_2022_wide.csv"
)

OUTPUT_FILE = DATA_DIR / (
    "rice_vi_13provinces_2021_2022_long.csv"
)

months = [
    f"{year}_{month:02d}"
    for year in [2021, 2022]
    for month in range(1, 13)
]

records = []

with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    source_rows = list(reader)

for province in source_rows:

    code = int(province["ADM1_CODE"])
    name = province["ADM1_NAME"]
    mask_pixels = int(float(province["rice_mask_count"]))

    if mask_pixels <= 0:
        raise ValueError(f"Mat na khong hop le: {name}")

    for month in months:
        ndvi = float(
            province[f"{month}_ndvi_trailing3_mean"]
        )
        evi = float(
            province[f"{month}_evi_trailing3_mean"]
        )

        ndvi_pixels = int(float(
            province[f"{month}_ndvi_trailing3_count"]
        ))
        evi_pixels = int(float(
            province[f"{month}_evi_trailing3_count"]
        ))

        if not all(math.isfinite(x) for x in [ndvi, evi]):
            raise ValueError(f"Gia tri khong hop le: {name}, {month}")

        if not (0 <= ndvi_pixels <= mask_pixels):
            raise ValueError(f"Loi pixel NDVI: {name}, {month}")

        if not (0 <= evi_pixels <= mask_pixels):
            raise ValueError(f"Loi pixel EVI: {name}, {month}")

        coverage = 100 * min(
            ndvi_pixels, evi_pixels
        ) / mask_pixels

        records.append({
            "adm1_code": code,
            "gaul_name": name,
            "month": month.replace("_", "-"),
            "ndvi_trailing3": ndvi,
            "evi_trailing3": evi,
            "mask_pixels": mask_pixels,
            "ndvi_valid_pixels": ndvi_pixels,
            "evi_valid_pixels": evi_pixels,
            "coverage_pct": round(coverage, 4),
            "quality_flag": (
                "ok_80pct" if coverage >= 80
                else "review_below_80pct"
            )
        })

records.sort(
    key=lambda x: (x["adm1_code"], x["month"])
)

# Kiem tra tinh day du
unique_provinces = {
    x["adm1_code"] for x in records
}

unique_pairs = {
    (x["adm1_code"], x["month"])
    for x in records
}

if not (
    len(source_rows) == 13
    and len(records) == 312
    and len(unique_provinces) == 13
    and len(unique_pairs) == 312
):
    raise ValueError("Du lieu khong day du hoac bi trung lap!")

# Luu CSV
DATA_DIR.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=list(records[0].keys())
    )
    writer.writeheader()
    writer.writerows(records)

# Bao cao
review = [
    x for x in records
    if x["quality_flag"] == "review_below_80pct"
]

print("=== KET QUA CHUYEN DOI ===")
print("So tinh:", len(unique_provinces))
print("So thang:", len(months))
print("Tong ban ghi:", len(records))
print("Ban ghi do phu >= 80%:", len(records) - len(review))
print("Ban ghi can xem xet:", len(review))

print("\n=== CAC BAN GHI CAN XEM XET ===")
for x in review:
    print(
        x["gaul_name"],
        x["month"],
        f'{x["coverage_pct"]:.2f}%'
    )

print("\n=== HOAN THANH ===")
print("File:", OUTPUT_FILE)
