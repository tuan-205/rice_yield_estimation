
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = (
    BASE_DIR / "data/interim/rice_with_province_codes.csv"
)

df = pd.read_csv(INPUT_FILE)

# Chi kiem tra giai doan 2000-2024
subset = df[
    df["nam"].between(2000, 2024)
].copy()

print("\n=== 1. TONG QUAN ===")
print("Tong ban ghi:", len(subset))
print("So tinh:", subset["tinh_thanh"].nunique())
print("So nam:", subset["nam"].nunique())
print("So nhom vu:", subset["mua_vu"].nunique())

# So ban ghi theo nam
print("\n=== 2. SO BAN GHI THEO NAM ===")
print(
    subset.groupby("nam")
    .size()
    .to_string()
)

# So ban ghi theo nhom vu
print("\n=== 3. SO BAN GHI THEO NHOM VU ===")
print(
    subset["mua_vu"]
    .value_counts()
    .to_string()
)

# Bang bao phu tinh - nhom vu - nam
coverage = subset.pivot_table(
    index=["tinh_thanh", "mua_vu"],
    columns="nam",
    values="nang_suat",
    aggfunc="count",
    fill_value=0
)

# Xac dinh cac to hop con thieu
all_years = range(2000, 2025)

print("\n=== 4. CAC NAM THIEU THEO TINH - VU ===")

missing_count = 0

for (province, season), row in coverage.iterrows():
    missing_years = [
        year for year in all_years
        if row.get(year, 0) == 0
    ]

    if missing_years:
        missing_count += len(missing_years)
        print(
            f"{province} | {season}: {missing_years}"
        )

print("\nTong so to hop thieu:", missing_count)

print("\n=== 5. SO BAN GHI DU KIEN ===")

expected = 13 * 2 * 25

print("Neu day du:", expected)
print("Thuc te:", len(subset))
print("Chenh lech:", expected - len(subset))

print("\nHOAN THANH")
