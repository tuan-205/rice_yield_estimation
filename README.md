# Ước lượng năng suất lúa

Khuyến nghị **Python 3.12 64-bit** (hỗ trợ 3.11–3.12). Chạy các lệnh từ gốc repository. Mô hình đã chọn và dữ liệu web đã được lưu, không cần huấn luyện lại sau khi pull.

## Cài đặt và chạy trên máy

```sh
git pull
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\Activate.ps1` (nếu máy chặn kích hoạt, dùng trực tiếp `.venv\Scripts\python.exe` thay cho `python`). macOS/Linux: `source .venv/bin/activate`.

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m web.run_local
```

Mở **http://127.0.0.1:8080**. Lịch sử và CSV dùng mô hình ở backend, không cần tài khoản GEE. Chế độ Vụ mới cần cấu hình GEE theo [hướng dẫn web](web/README.md). Các phiên bản thư viện mô hình được ghim để nạp đúng artifact đã lưu; XGBoost có lựa chọn gói theo hệ điều hành.

## Huấn luyện lại và lưu mô hình cho web

```sh
python notebook/train.py
```

Lệnh chạy toàn bộ notebook bằng chính Python trong môi trường hiện tại; nếu lỗi sẽ dừng. Khi thành công, notebook giữ output và xuất dữ liệu web. Có thể chạy tương tác bằng VS Code/Jupyter, chọn kernel của `.venv`, Restart Kernel → Run All, sau đó chạy `python web/tools/export_browser_model.py`.

- 5 base ensemble được huấn luyện, chọn 4 bằng Validation rồi tạo stacking; CatBoost là đối chứng riêng.
- Quy tắc chọn mô hình lưu: số lần xuất hiện trong top 3 MAE/RMSE/R² cao nhất; hòa phiếu ưu tiên MAE, RMSE, R² rồi tên. Test đã dùng chọn mô hình, nên cần dữ liệu mới để đánh giá độc lập.
- `models/model_comparison/rice_best_model.joblib` chứa đúng mô hình thắng và tiền xử lý cần thiết (nếu stacking thắng, chứa 4 base cùng meta learner).
- `rice_best_model_metadata.json` cùng thư mục lưu schema, tham số, phiên bản và chỉ số; `reports/model_comparison/` lưu bảng so sánh và biểu đồ.
- Phiên bản hiện tại chọn **CatBoost**. Web nạp trực tiếp artifact này qua `POST /v1/predict`; không huấn luyện lại trong request. Sau huấn luyện/xuất bundle, khởi động lại backend và tải lại trang để nạp phiên bản mới.

Chỉ nạp file joblib từ repository/nguồn bạn tin cậy. Không commit `.venv` hoặc file khóa GEE.

## Kiểm tra

```sh
python -m pip install -r requirements-dev.txt
python -m unittest web.tests.test_api web.tests.test_model_service -v
```

Với Node.js 20+ và backend đang chạy ở cổng 8080:

```sh
cd web
npm ci
```

PowerShell: `$env:PREDICTION_API="http://127.0.0.1:8080"`; macOS/Linux: `export PREDICTION_API=http://127.0.0.1:8080`. Sau đó chạy `npm test`, `node tests/ui.test.mjs`, `node tests/local-ui.test.mjs`, `node tests/interface.test.mjs`.
