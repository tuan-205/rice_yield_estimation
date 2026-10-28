from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "interim"

# 1. Doc hai bo du lieu
rice = pd.read_csv(
    DATA_DIR / "rice_with_province_codes.csv"
)

climate = pd.read_csv(
    DATA_DIR / "climate_monthly_1999_2022.csv"
)

# 2. Tach nam tu cot month
climate["year"] = pd.to_datetime(
    climate["month"], format="%Y-%m"
).dt.year

# 3. Dem so thang theo tinh va nam
coverage = (
    climate.groupby(["adm1_code", "year"])
    ["month"].nunique()
)

# 4. Lay cac ban ghi nang suat 2000-2022
rice_check = rice[
    rice["nam"].between(2000, 2022)
].copy()

# 5. Kiem tra du lieu khi tuong cua nam hien tai
rice_check["months_current"] = [
    coverage.get((code, year), 0)
    for code, year in zip(
        rice_check["adm1_code"],
        rice_check["nam"]
    )
]

# 6. Kiem tra nam truoc cho vu Dong Xuan
rice_check["months_previous"] = [
    coverage.get((code, year - 1), 0)
    for code, year in zip(
        rice_check["adm1_code"],
        rice_check["nam"]
    )
]

print("\n=== 1. TONG QUAN ===")
print("Ban ghi nang suat:", len(rice_check))
print("So tinh:", rice_check["adm1_code"].nunique())
print("So nam:", rice_check["nam"].nunique())

print("\n=== 2. DU LIEU NAM HIEN TAI ===")
print(
    "Ban ghi du 12 thang:",
    (rice_check["months_current"] == 12).sum()
)

print(
    "Ban ghi thieu thang:",
    (rice_check["months_current"] < 12).sum()
)

print("\n=== 3. KIEM TRA VU DONG XUAN ===")

winter = rice_check[
    rice_check["mua_vu"] == "dong_xuan"
]

print("So ban ghi Dong Xuan:", len(winter))
print(
    "Co du 12 thang nam truoc:",
    (winter["months_previous"] == 12).sum()
)

print("\n=== 4. CAC BAN GHI THIEU KHI TUONG ===")

missing = rice_check[
    (rice_check["months_current"] < 12)
    | (
        (rice_check["mua_vu"] == "dong_xuan")
        & (rice_check["months_previous"] < 12)
    )
]

print("So ban ghi can kiem tra:", len(missing))

if not missing.empty:
    print(
        missing[
            ["tinh_thanh", "nam", "mua_vu",
             "months_current", "months_previous"]
        ].to_string(index=False)
    )

print("\n=== 5. DU LIEU CHUA CO KHI TUONG ===")
future = rice[rice["nam"] > 2022]

print("So ban ghi 2023-2024:", len(future))

print("\nHOAN THANH")
