
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_FILE = (
    BASE_DIR / "data/interim/rice_labeled_valid.csv"
)

PROVINCE_FILE = (
    BASE_DIR / "data/interim/mekong_province_codes.csv"
)

OUTPUT_FILE = (
    BASE_DIR / "data/interim/rice_with_province_codes.csv"
)

# Doc du lieu
rice = pd.read_csv(DATA_FILE)
provinces = pd.read_csv(PROVINCE_FILE)

# Kiem tra ma tinh co duy nhat
assert provinces["tinh_thanh"].is_unique
assert provinces["adm1_code"].is_unique

# Ghep theo ten tinh
merged = rice.merge(
    provinces,
    on="tinh_thanh",
    how="left",
    validate="many_to_one",
    indicator=True
)

print("\n=== 1. KET QUA GHEP ===")
print("So dong truoc ghep:", len(rice))
print("So dong sau ghep:", len(merged))

print("\n=== 2. TRANG THAI GHEP ===")
print(merged["_merge"].value_counts())

print("\n=== 3. TINH KHONG GHEP DUOC ===")
print(
    merged.loc[
        merged["_merge"] != "both",
        "tinh_thanh"
    ].unique()
)

print("\n=== 4. SO TINH VA MA GAUL ===")
print(
    merged[
        ["tinh_thanh", "gaul_name", "adm1_code"]
    ].drop_duplicates()
    .sort_values("tinh_thanh")
    .to_string(index=False)
)

# Chi luu neu tat ca ban ghi ghep thanh cong
if (
    len(merged) == len(rice)
    and (merged["_merge"] == "both").all()
):
    merged = merged.drop(columns=["_merge"])
    merged.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )
    print("\nGHEP THANH CONG")
    print("Da luu:", OUTPUT_FILE)
else:
    print("\nGHEP CHUA THANH CONG - CHUA LUU FILE")
