# Lúa Lab — web kiểm nghiệm năng suất lúa

Bản chạy riêng tư: https://mekong-rice-yield-lab.elatedboar4096.chatgpt.site

Giao diện tiếng Việt chạy mô hình Bayesian Ridge đã chọn trong notebook, theo 13 tỉnh GAUL 2015 và hai nhóm vụ. Mô hình web được xuất từ pipeline đã fit, không huấn luyện một mô hình khác và không dùng số dự đoán định sẵn.

## Có thể dùng ngay

- Chọn tỉnh/năm/vụ lịch sử 2000–2022; so sánh dự đoán với nhãn năng suất thực.
- Xem 19 đặc trưng, chất lượng vệ tinh, biểu đồ lịch sử và bảng so sánh 13 mô hình.
- Nhập CSV đặc trưng theo vụ (19 cột như CSV huấn luyện), hoặc CSV dữ liệu tháng xuất từ GEE. Tải kết quả CSV.
- Chọn năm 2026: yêu cầu dữ liệu thực của vụ; chặn cửa sổ chưa kết thúc, dữ liệu khí hậu thiếu và tháng trùng. Không tự lấy số liệu 2022 để giả làm 2026.
- API GEE là kết nối tùy chọn, cần máy chủ có xác thực Google. Chỉ nhập ID không tạo quyền truy cập.

## Chạy web tại máy

Từ gốc repository:

```sh
python -m http.server 8080 --directory web/dist
```

Mở `http://localhost:8080`. Chế độ lịch sử và CSV không cần khóa API hoặc backend.

## Thử vụ 2026 bằng CSV GEE (không cần dựng API)

1. Mở https://code.earthengine.google.com/ và chọn Cloud Project `du-lieu-ve-tinh-vietnam` đã đăng ký Earth Engine.
2. Dán nội dung `web/gee/export_season_monthly.js` vào Code Editor.
3. Sửa `YIELD_YEAR`, `SEASON`, `PROVINCE_CODE` ở đầu script. Mặc định là đông xuân 2026, An Giang (3326).
4. Giữ `RICE_ASSET = projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020` đúng nguồn mô hình. Run, mở Tasks và chạy task xuất CSV vào Drive.
5. Tải CSV. Trên web chọn Vụ mới → tỉnh/năm/vụ tương ứng → CSV do bạn cung cấp → tải tệp lên → Ước lượng.

Chỉ chạy cho vụ đã hoàn tất. Đông xuân 2026 cần tháng 11/2025–4/2026; hè thu–thu đông 2026 cần tháng 4–11/2026. Tháng 11 chưa kết thúc thì chưa có đủ dữ liệu cả vụ.

## Bật lấy dữ liệu trực tiếp từ GEE

Các ID được người dùng xác nhận:

- Project: `du-lieu-ve-tinh-vietnam`
- Asset: `projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020`

Backend `web/api/` dùng FastAPI và Earth Engine Python API, cùng thuật toán nguồn: ERA5 Land, CHIRPS; MODIS Terra/Aqua QA <= 1; NDVI/EVI trailing 3 tháng; VCI 2000–2015; mặt nạ lúa 2020, ngưỡng 0.6, lưới 500m. Không thay nguồn hoặc thêm cột mới cho mô hình hiện tại.

### Chạy backend cục bộ

Cài Google Cloud CLI, đăng nhập bằng tài khoản có quyền trên project/asset. Những lệnh này chạy trên máy của bạn, không gửi khóa hoặc access token vào chat:

```sh
gcloud auth application-default login
gcloud auth application-default set-quota-project du-lieu-ve-tinh-vietnam
python -m pip install -r web/api/requirements.txt
export GEE_PROJECT_ID=du-lieu-ve-tinh-vietnam
export GEE_RICE_ASSET_ID=projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020
export WEB_ALLOWED_ORIGINS=http://localhost:8080
python -m uvicorn web.api.app:app --host 127.0.0.1 --port 8000
```

Trên Windows PowerShell dùng `$env:GEE_PROJECT_ID = "..."` thay cho `export`. Mở web cục bộ → Dữ liệu & kết nối → nhập `http://localhost:8000` → Kiểm tra kết nối. Chọn nguồn GEE để gửi yêu cầu lấy dữ liệu thật. Health chỉ kiểm tra cấu hình; quyền dữ liệu chỉ được xác nhận sau một yêu cầu thật thành công.

### Backend cho web đã xuất bản

Triển khai `web/api/Dockerfile` từ gốc repository trên một dịch vụ HTTPS như Cloud Run. Dùng service account gắn với runtime (ADC), không nhúng khóa JSON vào web. Đặt hai biến ID ở trên và `WEB_ALLOWED_ORIGINS` thành đúng origin của web. Identity chạy backend cần project đã bật/đăng ký Earth Engine và được đọc asset; có thể cần Earth Engine Resource Viewer và Service Usage Consumer. Vào web nhập URL HTTPS backend. Chưa có backend xác thực thì dùng luồng CSV GEE ở trên.

API: `GET /health`, `POST /v1/monthly` với `{"adm1_code":3326,"year":2026,"season":"dong_xuan"}`. Kết quả là dữ liệu tháng và provenance; trình duyệt tổng hợp theo cùng quy tắc huấn luyện. Cache 24h, tối đa 128 truy vấn trong bộ nhớ. Không có credential Google trong trình duyệt.

Tài liệu: https://developers.google.com/earth-engine/guides/auth và https://developers.google.com/earth-engine/guides/service_account

## Kiểm tra và cập nhật mô hình

```sh
# Sau khi notebook chọn mô hình mới, xuất lại bundle web:
python web/tools/export_browser_model.py
cd web
npm ci
npm test
node tests/ui.test.mjs
# Từ gốc repository, sau khi cài httpx:
python -m unittest web.tests.test_api -v
```

Exporter chủ động từ chối mô hình khác Bayesian Ridge. Nếu notebook chọn thuật toán khác, cần bổ sung bộ chạy tương ứng hoặc chuyển suy luận sang backend, rồi kiểm tra lại tính tương đương.

Đã kiểm tra 579 dự đoán khớp Python với sai số tối đa khoảng 3.6e-15; dữ liệu tháng gốc tái tạo toàn bộ 579 dòng đặc trưng; kiểm tra luồng DOM, API với nguồn giả lập, CSV và cửa sổ quan sát. Chưa xác minh giao dịch GEE thực vì runtime này chưa có danh tính Google được cấp quyền; chưa có QA trình duyệt thật trong môi trường hiện tại.

## Phạm vi kết quả

Mô hình fit 2000–2018; bảng chỉ số 2019–2022 đã dùng để lựa chọn và không phải đánh giá độc lập sau lựa chọn. Ước lượng theo tỉnh và nhóm vụ, không theo thửa ruộng và không dự báo trước thu hoạch. Mặt nạ 2020 và ranh giới GAUL 2015 cần được cân nhắc khi dùng cho năm mới. Không hiển thị khoảng tin cậy chưa được hiệu chỉnh.
