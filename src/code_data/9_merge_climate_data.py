
from pathlib import Path
import pandas as pd
import calendar

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "interim"

files = [
    "climate_13provinces_1999_2004.csv",
    "climate_13provinces_2005_2010.csv",
    "climate_13provinces_2011_2016.csv",
    "climate_13provinces_2017_2020.csv",
    "climate_13provinces_2021_2022.csv"
]

# 1. Doc va kiem tra cac file
dataframes = []

print("\n=== 1. KIEM TRA FILE DAU VAO ===")

for filename in files:
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay: {path}")

    df = pd.read_csv(path)
    dataframes.append(df)

    print(f"{filename}: {len(df)} dong")

# 2. Gop du lieu
climate = pd.concat(
    dataframes,
    ignore_index=True
)

# 3. Sap xep
climate = climate.sort_values(
    ["adm1_code", "month"]
).reset_index(drop=True)

print("\n=== 2. TONG QUAN SAU KHI GHEP ===")
print("Tong so dong:", len(climate))
print("So tinh:", climate["adm1_code"].nunique())
print("So thang:", climate["month"].nunique())
print("Thang dau:", climate["month"].min())
print("Thang cuoi:", climate["month"].max())

# 4. Kiem tra trung lap
duplicates = climate.duplicated(
    subset=["adm1_code", "month"]
).sum()

print("\n=== 3. KIEM TRA TRUNG LAP ===")
print("Trung lap tinh-thang:", duplicates)

# 5. Kiem tra gia tri thieu
print("\n=== 4. KIEM TRA GIA TRI THIEU ===")
print(climate.isnull().sum())

# 6. Kiem tra do phu theo tinh
print("\n=== 5. SO THANG THEO TINH ===")
print(
    climate.groupby(["adm1_code", "gaul_name"])
    ["month"]
    .nunique()
    .to_string()
)

# 7. Kiem tra so ngay trong thang
climate["year_check"] = climate["month"].str[:4].astype(int)
climate["month_check"] = climate["month"].str[5:7].astype(int)

climate["expected_days"] = climate.apply(
    lambda row: calendar.monthrange(
        int(row["year_check"]),
        int(row["month_check"])
    )[1],
    axis=1
)

invalid_days = climate[
    (climate["era5_days"] != climate["expected_days"])
    | (climate["chirps_days"] != climate["expected_days"])
]

print("\n=== 6. KIEM TRA SO NGAY ===")
print("Dong co so ngay khong khop:", len(invalid_days))

# 8. Kiem tra day du 13 tinh x 288 thang
expected_months = pd.period_range(
    "1999-01", "2022-12", freq="M"
).astype(str)

expected_codes = climate["adm1_code"].dropna().unique()

expected_index = pd.MultiIndex.from_product(
    [expected_codes, expected_months],
    names=["adm1_code", "month"]
)

actual_index = pd.MultiIndex.from_frame(
    climate[["adm1_code", "month"]]
)

missing_pairs = expected_index.difference(actual_index)

print("\n=== 7. KIEM TRA DO PHU ===")
print("So to hop tinh-thang thieu:", len(missing_pairs))

# 9. Luu du lieu neu dat
is_valid = (
    len(climate) == 3744
    and climate["adm1_code"].nunique() == 13
    and duplicates == 0
    and climate.isnull().sum().sum() == 0
    and len(invalid_days) == 0
    and len(missing_pairs) == 0
)

if is_valid:
    climate = climate.drop(
        columns=["year_check", "month_check", "expected_days"]
    )

    output = DATA_DIR / "climate_monthly_1999_2022.csv"

    climate.to_csv(
        output,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=== GHEP THANH CONG ===")
    print("Da luu:", output)
else:
    print("\n=== CAN KIEM TRA LAI DU LIEU ===")
    print("Chua luu file hop nhat.")
