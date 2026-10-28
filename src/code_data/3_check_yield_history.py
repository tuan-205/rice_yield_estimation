
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

input_file = (
    BASE_DIR / "data/interim/rice_yield_audit.csv"
)

df = pd.read_csv(input_file)

# Các bản ghi cần kiểm tra
cases = [
    ("Bến Tre", 2016, "dong_xuan"),
    ("Bến Tre", 2020, "dong_xuan"),
    ("Cà Mau", 1998, "dong_xuan"),
]

for province, year, season in cases:

    print("\n" + "=" * 65)
    print(f"TINH: {province} | NAM: {year} | VU: {season}")
    print("=" * 65)

    # Lấy 3 năm trước và 3 năm sau
    subset = df[
        (df["tinh_thanh"] == province)
        & (df["mua_vu"] == season)
        & (df["nam"].between(year - 3, year + 3))
    ].copy()

    subset = subset.sort_values("nam")

    print(
        subset[
            ["nam", "dien_tich", "san_luong", "nang_suat"]
        ].to_string(index=False)
    )

    # Tính trung vị các năm lân cận, trừ năm cần kiểm tra
    neighbors = subset.loc[
        subset["nam"] != year, "nang_suat"
    ].dropna()

    current = subset.loc[
        subset["nam"] == year, "nang_suat"
    ]

    if not current.empty and not neighbors.empty:
        median = neighbors.median()
        value = current.iloc[0]

        print(f"\nNang suat nam can kiem tra: {value:.4f}")
        print(f"Trung vi cac nam lan can: {median:.4f}")

        if median > 0:
            ratio = value / median
            print(f"Ty le so voi trung vi: {ratio:.2%}")

print("\nHOAN THANH KIEM TRA LICH SU")
