
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_FILE = (
    BASE_DIR / "data/interim/rice_with_province_codes.csv"
)

df = pd.read_csv(INPUT_FILE)

periods = {
    "TRAIN_2000_2015": (2000, 2015),
    "VALIDATION_2016_2018": (2016, 2018),
    "TEST_2019_2024": (2019, 2024)
}

print("\n=== 1. SO BAN GHI THEO TAP ===")

total = 0

for name, (start, end) in periods.items():
    subset = df[df["nam"].between(start, end)]

    print(f"\n{name}")
    print("So dong:", len(subset))
    print("So tinh:", subset["tinh_thanh"].nunique())

    print("Theo mua vu:")
    print(subset["mua_vu"].value_counts().to_string())

    total += len(subset)

print("\n=== 2. KIEM TRA TONG ===")
print("Tong so dong 3 tap:", total)

expected_total = len(df[df["nam"].between(2000, 2024)])

print("Tong du lieu 2000-2024:", expected_total)
print("Khop:", total == expected_total)

print("\n=== 3. NANG SUAT THEO TAP ===")

for name, (start, end) in periods.items():
    subset = df[df["nam"].between(start, end)]

    print(f"\n{name}")
    print(
        subset["nang_suat"]
        .describe()
        .round(3)
        .to_string()
    )

print("\nHOAN THANH")
