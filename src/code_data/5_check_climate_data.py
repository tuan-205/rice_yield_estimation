
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data/interim/rice_labeled_valid.csv"

df = pd.read_csv(INPUT_FILE)

climate_cols = [
    "tổng số giờ nắng",
    "tổng lượng mưa",
    "độ ẩm trung bình",
    "nhiệt độ trung bình"
]

print("\n=== 1. THONG KE KHI TUONG THEO MUA VU ===")

summary = df.groupby("mua_vu")[climate_cols].agg(
    ["count", "mean", "min", "max", "std"]
)

print(summary.to_string())

print("\n=== 2. KIEM TRA GIA TRI KHONG HOP LE ===")

checks = {
    "So gio nang am": (df["tổng số giờ nắng"] < 0).sum(),
    "Luong mua am": (df["tổng lượng mưa"] < 0).sum(),
    "Do am ngoai 0-100": (
        (df["độ ẩm trung bình"] < 0)
        | (df["độ ẩm trung bình"] > 100)
    ).sum(),
    "Nhiet do ngoai 0-45": (
        (df["nhiệt độ trung bình"] < 0)
        | (df["nhiệt độ trung bình"] > 45)
    ).sum()
}

for name, count in checks.items():
    print(f"{name}: {count}")

print("\n=== 3. GIA TRI TRUNG BINH THEO MUA VU ===")

print(
    df.groupby("mua_vu")[climate_cols]
    .mean()
    .round(2)
    .to_string()
)

print("\n=== 4. KIEM TRA GIA TRI THIEU ===")

print(df[climate_cols].isna().sum())

print("\nHOAN THANH KIEM TRA KHI TUONG")
