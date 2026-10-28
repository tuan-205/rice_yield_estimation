
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "interim"
GEE_DIR = DATA / "gee_exports"

CLIMATE_FILE = DATA / "climate_monthly_1999_2022.csv"

OUTPUT_FILE = DATA / "climate_rice_vi_vci_1999_2022.csv"

VI_LONG_FILE = DATA / "vi_gee_2000_2022_long.csv"

VI_COLUMNS = [
    "ndvi_trailing3",
    "evi_trailing3",
    "vci",
    "mask_pixels",
    "ndvi_valid_pixels",
    "evi_valid_pixels",
    "vci_valid_pixels",
    "coverage_pct",
    "quality_flag",
    "rice_mask_year",
    "vi_stat_scale_m",
    "vci_baseline_years",
]


def to_number(value):
    if value is None or str(value).strip() == "":
        return None

    number = float(value)

    if not math.isfinite(number):
        raise ValueError(f"Gia tri khong hop le: {value}")

    return number


def to_count(value):
    number = to_number(value)

    if number is None:
        return None

    if number < 0 or abs(number - round(number)) > 1e-6:
        raise ValueError(f"So pixel khong hop le: {value}")

    return int(round(number))


def read_gee_year(year, path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = set(reader.fieldnames or [])

    if len(rows) != 13:
        raise ValueError(
            f"{path.name}: can 13 tinh, nhan {len(rows)}"
        )

    required = {
        "ADM1_CODE",
        "ADM1_NAME",
        "rice_mask_count",
    }

    for month in range(1, 13):
        prefix = f"{year}_{month:02d}"

        for indicator in [
            "ndvi_trailing3",
            "evi_trailing3",
            "vci",
        ]:
            required.add(f"{prefix}_{indicator}_mean")
            required.add(f"{prefix}_{indicator}_count")

    missing = required - columns

    if missing:
        raise ValueError(
            f"{path.name}: thieu cot {sorted(missing)[:10]}"
        )

    result = []
    seen_codes = set()

    for province in rows:
        code = int(float(province["ADM1_CODE"]))
        name = province["ADM1_NAME"]
        mask_count = to_count(
            province["rice_mask_count"]
        )

        if code in seen_codes:
            raise ValueError(f"Trung ma tinh: {code}")

        seen_codes.add(code)

        for month in range(1, 13):
            prefix = f"{year}_{month:02d}"

            ndvi = to_number(
                province[f"{prefix}_ndvi_trailing3_mean"]
            )

            evi = to_number(
                province[f"{prefix}_evi_trailing3_mean"]
            )

            vci = to_number(
                province[f"{prefix}_vci_mean"]
            )

            ndvi_count = to_count(
                province[f"{prefix}_ndvi_trailing3_count"]
            )

            evi_count = to_count(
                province[f"{prefix}_evi_trailing3_count"]
            )

            vci_count = to_count(
                province[f"{prefix}_vci_count"]
            )

            # Kiem tra gia tri
            for value, low, high, label in [
                (ndvi, -0.2, 1.0, "NDVI"),
                (evi, -0.2, 1.0, "EVI"),
                (vci, 0.0, 100.0, "VCI"),
            ]:
                if value is not None and not low <= value <= high:
                    raise ValueError(
                        f"{name} {prefix}: {label}={value}"
                    )

            for count in [
                ndvi_count,
                evi_count,
                vci_count,
            ]:
                if (
                    count is not None
                    and mask_count is not None
                    and count > mask_count
                ):
                    raise ValueError(
                        f"Pixel hop le vuot mat na: {name}, {prefix}"
                    )

            if (
                mask_count is not None
                and mask_count > 0
                and all(x is not None for x in [
                    ndvi,
                    evi,
                    vci,
                    ndvi_count,
                    evi_count,
                    vci_count,
                ])
            ):
                valid_count = min(
                    ndvi_count,
                    evi_count,
                    vci_count,
                )

                coverage = round(
                    100 * valid_count / mask_count, 4
                )

                flag = (
                    "ok_80pct"
                    if coverage >= 80
                    else "review_below_80pct"
                )

            elif all(x is None for x in [ndvi, evi, vci]):
                coverage = None
                flag = "no_vi"

            else:
                coverage = None
                flag = "partial_vi"

            result.append({
                "adm1_code": code,
                "gaul_name": name,
                "month": f"{year}-{month:02d}",
                "ndvi_trailing3": ndvi,
                "evi_trailing3": evi,
                "vci": vci,
                "mask_pixels": mask_count,
                "ndvi_valid_pixels": ndvi_count,
                "evi_valid_pixels": evi_count,
                "vci_valid_pixels": vci_count,
                "coverage_pct": coverage,
                "quality_flag": flag,
                "rice_mask_year": 2020,
                "vi_stat_scale_m": 500,
                "vci_baseline_years": "2000-2015",
            })

    return result


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    # 1. Doc du lieu khi tuong
    with open(
        CLIMATE_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        reader = csv.DictReader(f)
        climate_columns = list(reader.fieldnames or [])
        climate_rows = list(reader)

    required_climate = {
        "adm1_code",
        "gaul_name",
        "month",
    }

    if not required_climate.issubset(climate_columns):
        raise ValueError("File climate thieu cot bat buoc")

    climate_keys = {
        (int(row["adm1_code"]), row["month"])
        for row in climate_rows
    }

    if len(climate_rows) != 3744 or len(climate_keys) != 3744:
        raise ValueError(
            "Climate phai co 3744 dong khong trung lap"
        )

    # 2. Doc tat ca file CSV da xuat tu GEE
    vi_rows = []
    missing_years = []

    for year in range(2000, 2023):
        filename = f"rice_vi_vci_{year}_wide.csv"
        path = GEE_DIR / filename

        if path.exists():
            vi_rows.extend(
                read_gee_year(year, path)
            )
        else:
            missing_years.append(year)

    # 3. Tao khoa ghep
    vi_lookup = {}

    for row in vi_rows:
        key = (
            int(row["adm1_code"]),
            row["month"],
        )

        if key in vi_lookup:
            raise ValueError(f"Trung du lieu VI: {key}")

        if key not in climate_keys:
            raise ValueError(
                f"Ma tinh/thang khong co trong climate: {key}"
            )

        vi_lookup[key] = row

    # 4. Hop nhat, giu nguyen 3744 dong climate
    merged = []

    for climate in climate_rows:
        key = (
            int(climate["adm1_code"]),
            climate["month"],
        )

        vi = vi_lookup.get(key)

        record = dict(climate)

        for col in VI_COLUMNS:
            record[col] = (
                vi.get(col, "")
                if vi is not None
                else ""
            )

        merged.append(record)

    merged.sort(
        key=lambda row: (
            int(row["adm1_code"]),
            row["month"],
        )
    )

    vi_rows.sort(
        key=lambda row: (
            int(row["adm1_code"]),
            row["month"],
        )
    )

    # 5. Luu hai file
    write_csv(
        VI_LONG_FILE,
        vi_rows,
        ["adm1_code", "gaul_name", "month"] + VI_COLUMNS,
    )

    write_csv(
        OUTPUT_FILE,
        merged,
        climate_columns + VI_COLUMNS,
    )

    # 6. Bao cao
    ndvi_count = sum(
        row["ndvi_trailing3"] not in ("", None)
        for row in merged
    )

    vci_count = sum(
        row["vci"] not in ("", None)
        for row in merged
    )

    print("\n=== KET QUA HOP NHAT ===")
    print("So dong climate:", len(climate_rows))
    print("So dong GEE VI:", len(vi_rows))
    print("So dong co NDVI:", ndvi_count)
    print("So dong co VCI:", vci_count)
    print("So dong sau ghep:", len(merged))
    print("Cac nam chua co CSV GEE:", missing_years)
    print("Da luu:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
