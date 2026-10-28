
from pathlib import Path
import pandas as pd
import numpy as np

# 1. Xác định đường dẫn dữ liệu
BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data" / "raw" / "raw_mekong_delta_rice.csv"

# 2. Đọc dữ liệu gốc
df = pd.read_csv(FILE_PATH)

# 3. Kiểm tra kích thước
print("\n=== 1. KICH THUOC DU LIEU ===")
print("So dong:", df.shape[0])
print("So cot:", df.shape[1])

# 4. Kiểm tra tên cột và kiểu dữ liệu
print("\n=== 2. TEN COT VA KIEU DU LIEU ===")
print(df.dtypes)

# 5. Kiểm tra giá trị thiếu
print("\n=== 3. GIA TRI THIEU ===")
print(df.isnull().sum())

# 6. Kiểm tra bản ghi trùng lặp
print("\n=== 4. TRUNG LAP ===")
print("Trung lap toan bo:", df.duplicated().sum())

keys = ["tinh_thanh", "nam", "mua_vu"]
print("Trung lap theo tinh-nam-vu:",
      df.duplicated(subset=keys).sum())

# 7. Kiểm tra phạm vi thời gian
print("\n=== 5. PHAM VI THOI GIAN ===")
print("Nam dau:", df["nam"].min())
print("Nam cuoi:", df["nam"].max())

# 8. Kiểm tra tỉnh và mùa vụ
print("\n=== 6. TINH THANH ===")
print(df["tinh_thanh"].value_counts())

print("\n=== 7. MUA VU ===")
print(df["mua_vu"].value_counts())

# 9. Thống kê mô tả các cột số
print("\n=== 8. THONG KE MO TA ===")
print(df.describe().to_string())

# 10. Xem các dòng thiếu diện tích hoặc sản lượng
print("\n=== 9. CAC DONG THIEU DU LIEU NONG NGHIEP ===")

missing = df[
    df["dien_tich"].isna() |
    df["san_luong"].isna()
]

print(missing.to_string(index=False))

print("\n=== HOAN THANH KIEM TRA ===")
