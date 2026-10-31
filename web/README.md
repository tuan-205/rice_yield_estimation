# Lúa Lab — web kiểm nghiệm năng suất lúa

Bản chạy riêng tư: https://mekong-rice-yield-lab.elatedboar4096.chatgpt.site

Giao diện tiếng Việt dùng backend Python chạy mô hình đã chọn trong notebook (hiện tại là CatBoost), theo 13 tỉnh GAUL 2015 và hai nhóm vụ. Mô hình web được xuất từ pipeline đã fit, không huấn luyện một mô hình khác và không dùng số dự đoán định sẵn.

## Có thể dùng ngay

- Chọn tỉnh/năm/vụ lịch sử 2000–2020; so sánh dự đoán với nhãn năng suất thực.
- Xem 19 đặc trưng, chất lượng vệ tinh, biểu đồ lịch sử và bảng so sánh 7 mô hình.
- Ở chế độ lịch sử: nhập CSV đặc trưng theo vụ (19 cột như CSV huấn luyện), hoặc CSV dữ liệu tháng cho 2000–2020. Tải kết quả CSV.
- Chế độ Vụ mới chỉ có các năm 2021 đến năm hiện tại, nguồn GEE qua API được cố định. Chọn năm 2026: yêu cầu dữ liệu thực của vụ; chặn cửa sổ chưa kết thúc, dữ liệu khí hậu thiếu và tháng trùng. Không tự lấy số liệu 2022 để giả làm 2026.
- API GEE là kết nối tùy chọn, cần máy chủ có xác thực Google. Chỉ nhập ID không tạo quyền truy cập.

## Chạy web tại máy

Từ gốc repository:

```sh
python -m pip install -r requirements.txt
python -m web.run_local
```

Mở `http://localhost:8080`. Chế độ lịch sử và CSV không cần khóa GEE. Backend cùng máy chủ nạp mô hình đã lưu; cần chạy bằng lệnh trên thay cho máy chủ file tĩnh.

## Dùng file JSON xác thực — không nhập API URL

Giữ file khóa service account ở ngoài thư mục dự án, ví dụ `C:\gee-keys\gee-key.json`. Không gửi nội dung khóa vào chat, GitHub hoặc upload vào web. Chương trình chỉ nhận đường dẫn trên máy bạn và Google SDK đọc file đó ở backend.

Từ gốc repository, sau khi `git pull`:

```sh
python -m pip install -r web/api/requirements.txt
python -m web.run_local --credentials "C:\gee-keys\gee-key.json" --check-gee
```

Trên macOS/Linux thay bằng đường dẫn thật, ví dụ `"/Users/ban/gee-keys/gee-key.json"`. Mặc định đã điền Project ID và Asset ID của bạn. `--check-gee` kiểm tra khóa và quyền đọc asset trước khi khởi động; không in khóa ra màn hình.

Mở **http://127.0.0.1:8080** trên cùng máy. Web tự nhận backend nên không cần nhập URL. Chọn Vụ mới → tỉnh, năm và vụ → Google Earth Engine → Ước lượng. Dừng bằng Ctrl+C. Chỉ mở địa chỉ cục bộ này khi chạy bằng file JSON trên máy; bản Sites online không thể đọc file khóa trên máy bạn.

Nếu file hợp lệ nhưng vẫn bị từ chối, cấp quyền đọc asset cho địa chỉ `client_email` của service account, đồng thời bảo đảm service account có quyền sử dụng project Earth Engine. Không cần gửi `private_key` cho bất kỳ ai.

Nếu dùng khóa trên máy chủ riêng, đặt biến `GOOGLE_APPLICATION_CREDENTIALS` bằng đường dẫn file khóa đã mount ở máy chủ. Backend cũng phục vụ web tại `/`, tự kết nối cùng origin. Trên Cloud Run vẫn có thể dùng service account gắn với runtime thay cho file khóa.

## Hai chế độ dữ liệu

- **Kiểm nghiệm lịch sử:** năm 2000–2020, chọn bộ dữ liệu lịch sử hoặc CSV do người dùng cung cấp.
- **Vụ mới:** năm 2021 đến năm hiện tại (theo múi giờ Việt Nam), nguồn cố định Google Earth Engine - qua API, không có menu chọn nguồn và không nhập CSV trong chế độ này. Có thể chạy bản cục bộ bằng file JSON như hướng dẫn trên để tự kết nối backend.

Mã `web/gee/export_season_monthly.js` vẫn có thể dùng xuất dữ liệu GEE để đối chiếu ngoài ứng dụng. Chỉ ước lượng sau khi đủ toàn bộ cửa sổ vụ. Đông xuân 2026 cần tháng 11/2025–4/2026; hè thu–thu đông 2026 cần tháng 4–11/2026.

Bấm logo Lúa Lab để thu gọn hoặc mở rộng thanh điều hướng. Các menu chọn hỗ trợ bàn phím mũi tên, Home/End, Enter và Escape.

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

# Backend phải đang chạy; đặt PREDICTION_API=http://127.0.0.1:8080 theo README gốc.
cd web
npm ci
npm test
node tests/ui.test.mjs
node tests/local-ui.test.mjs
node tests/interface.test.mjs
# Từ gốc repository, sau khi cài httpx:
python -m unittest web.tests.test_api web.tests.test_model_service -v
```

Exporter xuất metadata và dữ liệu cho web; backend nạp trực tiếp `models/model_comparison/rice_best_model.joblib`. Hỗ trợ mô hình đơn và stacking theo schema artifact của notebook. Sau huấn luyện, chạy exporter, khởi động lại backend rồi tải lại trang. `POST /v1/predict` nhận `{"rows":[{...19 đặc trưng...}]}` và trả dự đoán, tên mô hình, SHA-256 để giao diện kiểm tra phiên bản.

Kiểm tra 579 dự đoán qua API so với Python và 104 dự đoán Test so với báo cáo notebook; dữ liệu tháng gốc tái tạo toàn bộ 579 dòng đặc trưng; kiểm tra luồng DOM, API với nguồn giả lập, CSV và cửa sổ quan sát. Chưa xác minh giao dịch GEE thực vì runtime này chưa có danh tính Google được cấp quyền; chưa có QA trình duyệt thật trong môi trường hiện tại.

## Phạm vi kết quả

Mô hình fit 2000–2018; bảng chỉ số 2019–2022 đã dùng để lựa chọn và không phải đánh giá độc lập sau lựa chọn. Ước lượng theo tỉnh và nhóm vụ, không theo thửa ruộng và không dự báo trước thu hoạch. Mặt nạ 2020 và ranh giới GAUL 2015 cần được cân nhắc khi dùng cho năm mới. Không hiển thị khoảng tin cậy chưa được hiệu chỉnh.
