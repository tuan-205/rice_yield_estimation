
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Khai báo đường dẫn
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data/raw/raw_mekong_delta_rice.csv"
OUTPUT_DIR = BASE_DIR / "data/interim"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Đọc dữ liệu gốc
df = pd.read_csv(INPUT_FILE)

# 3. Phân loại bản ghi
valid_mask = (
    df["dien_tich"].notna()
    & df["san_luong"].notna()
    & np.isfinite(df["dien_tich"])
    & np.isfinite(df["san_luong"])
    & (df["dien_tich"] > 0)
    & (df["san_luong"] >= 0)
)

valid_df = df.loc[valid_mask].copy()
missing_df = df.loc[~valid_mask].copy()

# 4. Tính nhãn năng suất
valid_df["nang_suat"] = (
    valid_df["san_luong"] / valid_df["dien_tich"]
)

# 5. Sắp xếp dữ liệu
sort_cols = ["tinh_thanh", "mua_vu", "nam"]

valid_df = valid_df.sort_values(sort_cols)
missing_df = missing_df.sort_values(sort_cols)

# 6. Lưu thành hai file riêng
valid_file = OUTPUT_DIR / "rice_labeled_valid.csv"
missing_file = OUTPUT_DIR / "rice_missing_values.csv"

valid_df.to_csv(
    valid_file, index=False, encoding="utf-8-sig"
)

missing_df.to_csv(
    missing_file, index=False, encoding="utf-8-sig"
)

# 7. Kiểm tra kết quả
print("\n=== KET QUA XU LY ===")
print("Tong ban ghi goc:", len(df))
print("Ban ghi co nhan hop le:", len(valid_df))
print("Ban ghi khong du dieu kien:", len(missing_df))

print("\n=== KIEM TRA NHAN NANG SUAT ===")
print("Nhan thieu:", valid_df["nang_suat"].isna().sum())
print("Nang suat nho nhat:", valid_df["nang_suat"].min())
print("Nang suat lon nhat:", valid_df["nang_suat"].max())

print("\n=== KIEM TRA TINH TOAN VEN ===")
print("Tong hai nhom:", len(valid_df) + len(missing_df))
print("So dong trung lap tinh-nam-vu:",
      valid_df.duplicated(
          subset=["tinh_thanh", "nam", "mua_vu"]
      ).sum())

print("\n=== FILE DA LUU ===")
print(valid_file)
print(missing_file)

print("\nHOAN THANH")
