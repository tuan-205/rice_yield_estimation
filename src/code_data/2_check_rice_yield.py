
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data/raw/raw_mekong_delta_rice.csv"
OUTPUT_DIR = BASE_DIR / "data/interim"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Đọc dữ liệu gốc
df = pd.read_csv(INPUT_FILE)

# Tính năng suất, không thay thế giá trị thiếu
valid = (
    df["dien_tich"].notna()
    & df["san_luong"].notna()
    & (df["dien_tich"] > 0)
)

df["nang_suat"] = np.nan

df.loc[valid, "nang_suat"] = (
    df.loc[valid, "san_luong"]
    / df.loc[valid, "dien_tich"]
)

print("\n=== 1. THONG KE NANG SUAT ===")
print(df["nang_suat"].describe())

print("\n=== 2. SO LUONG GIA TRI ===")
print("Hop le de tinh:", valid.sum())
print("Khong tinh duoc:", df["nang_suat"].isna().sum())

print("\n=== 3. 15 NANG SUAT THAP NHAT ===")
print(
    df.nsmallest(15, "nang_suat")[
        ["tinh_thanh", "nam", "mua_vu",
         "dien_tich", "san_luong", "nang_suat"]
    ].to_string(index=False)
)

print("\n=== 4. 15 NANG SUAT CAO NHAT ===")
print(
    df.nlargest(15, "nang_suat")[
        ["tinh_thanh", "nam", "mua_vu",
         "dien_tich", "san_luong", "nang_suat"]
    ].to_string(index=False)
)

print("\n=== 5. GIA TRI CAN KIEM TRA ===")

# Ngưỡng dùng để sàng lọc, không tự động xóa
suspect = df[
    (df["nang_suat"] < 2)
    | (df["nang_suat"] > 10)
]

print("So dong nghi van:", len(suspect))

print(
    suspect[
        ["tinh_thanh", "nam", "mua_vu",
         "dien_tich", "san_luong", "nang_suat"]
    ].to_string(index=False)
)

# Lưu để kiểm tra ở bước tiếp theo
output_file = OUTPUT_DIR / "rice_yield_audit.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\nDa luu:", output_file)
print("HOAN THANH")
