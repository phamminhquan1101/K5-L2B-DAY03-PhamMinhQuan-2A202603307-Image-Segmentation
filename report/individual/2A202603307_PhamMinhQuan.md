# Báo cáo thực hành Day 3 — điền trực tiếp trong fork của bạn

**Cách dùng:** Thay mọi dấu `…` bằng bài làm thật của bạn trước khi nộp link fork trên [LMS](https://aithucchien.vinuni.edu.vn). Giữ nguyên bốn mục và bảng để coach đọc nhanh. Viết ngắn, cụ thể theo ảnh/vùng; không cần thuật ngữ chuyên sâu. Ví dụ trong [hướng dẫn mẫu](../../reports/REPORT_TEMPLATE.md) chỉ giúp hiểu cách điền, không phải câu trả lời để chép lại.

- Mã học viên theo lớp: 2A202603307
- Ngày / CVAT local: 12/11
- Công cụ đã dùng: CVAT - Tích hợp SAM model

Mã học viên là mã lớp cấp; không cần ghi họ tên trong report nếu kênh [LMS](https://aithucchien.vinuni.edu.vn) đã nhận diện bạn. Chỉ ghi công cụ thật sự đã dùng; không có SAM vẫn làm bài bình thường.

## 1. Bài đã nộp

Tôi đã hoàn thành đủ 9 task, gồm 14 ảnh, và lưu các file ZIP export trong thư mục `submissions/`. Cột điểm dưới đây là điểm tối đa của từng task, **không phải điểm tự chấm**.

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | easy_semantic.zip | 3 / 3 | 20 |
| medium_instance | medium_instance.zip | 3 / 3 | 32 |
| hard_panoptic | hard_panoptic.zip | 2 / 2 | 30 |
| cp1_holes | cp1_holes.zip | 1 / 1 | 3 |
| cp2_slice | cp2_slice.zip | 1 / 1 | 3 |
| cp5_occlusion | cp5_occlusion.zip | 1 / 1 | 3 |
| cp3_thin | cp3_thin.zip | 1 / 1 | 3 |
| cp4_curb | cp4_curb.zip | 1 / 1 | 3 |
| cp6_coverage | cp6_coverage.zip | 1 / 1 | 3 |
| **Tổng tối đa** | **9 file ZIP** | **14 / 14** | **100** |


## 2. Một quyết định trước khi dùng gợi ý

- Task, ảnh/vị trí và object được chọn: Trong task `medium_instance`, tôi chọn người đi bộ gần nhất trong ảnh. Tên file ảnh: data\tiers\medium_instance\images\000000181542.jpg
- Class: `person`.
- Công cụ và thao tác: Tôi dùng SAM để tạo mask gợi ý cho người đi bộ, sau đó điều chỉnh lại mép mask cho sát đường biên nhìn thấy của người đó.
- Quyết định gán nhãn: Tôi chỉnh lại mép vật thể thay vì giữ nguyên toàn bộ mask do SAM đề xuất, nhằm làm cho mask khớp hơn với phần người nhìn thấy trong ảnh.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: Task `easy_semantic`, ảnh `data/tiers/easy_semantic/images/81ae7cbb-6bc63a4a.jpg`, vùng cột đèn.
- Lỗi thuộc loại: Sai lớp.
- Bằng chứng tôi nhìn thấy: Khi kiểm tra lại ảnh, tôi nhận ra vật thể đã gán nhãn như thân cây thực chất là cột đèn.
- Quy tắc và hành động sửa: Cột đèn không thuộc class `vegetation`. Tôi đã sửa lại vùng mask gán nhầm này. Task Easy chỉ có các class `road`, `sidewalk`, `building`, `vegetation`, `sky`, nên không thêm class `pole` vào task hoặc ép cột đèn sang một class không phù hợp.
- Sau sửa đã Save và export lại chưa? Đã export lại

Nếu bạn **đã xem Summary tự đánh giá trên GitHub Actions hoặc tự chạy script**, ghi ngắn một kết quả liên quan lỗi vừa sửa (ví dụ task, metric trước/sau nếu có): … / chưa có điểm. Scorecard ba tier tối đa **82**, không phải điểm cuối trên 100. Không tự ghi PASS/top 3/bonus; người phụ trách xác nhận theo tiêu chí lớp. Không đưa file ground truth vào fork.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

Mỗi ca là một **vùng cụ thể** khiến bạn phải cân nhắc hai cách hiểu. Ghi dấu hiệu nhìn thấy hoặc quy tắc đã dùng, rồi nêu quyết định hoặc câu hỏi cho coach. Không cần ba lỗi; ca đã quyết định được cũng hợp lệ.

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| `data/tiers/easy_semantic/images/81ae7cbb-6bc63a4a.jpg`, vùng cột đèn | Vật thể là thân cây thuộc `vegetation`, hoặc là cột đèn không thuộc các class của Easy. | Khi kiểm tra lại, tôi nhận ra đây là cột đèn. Class `vegetation` dành cho cây cối; Easy không có class `pole`. | Ban đầu tôi gán nhầm cột đèn thành thân cây. Tôi đã sửa vùng mask gán nhầm, không coi cột đèn là `vegetation`. |
| `data/tiers/hard_panoptic/images/000000460147.jpg`, xe tải chở xe con | Chỉ gán nhãn xe tải vì xe con là vật được chở, hoặc gán riêng xe tải và từng xe con nhìn thấy. | Task có cả `truck` và `car`; quy tắc panoptic yêu cầu tách từng vật đếm được và chỉ vẽ phần nhìn thấy. Việc xe con được chở trên xe tải không tự loại bỏ nó khỏi class `car`. | Quyết định hiện tại của tôi là chỉ gán nhãn xe tải, không label xe con trên đó. Cần kiểm tra lại quyết định này theo quy tắc task; câu hỏi cho coach: xe con nhìn thấy trên xe tải có cần được gán thành instance `car` riêng không? |


## 5. Tích hợp mô hình SAM để hỗ trợ gán nhãn

**Mục tiêu và cách thực hiện.** Tôi bổ sung phần tích hợp **MobileSAM**, một biến thể nhẹ của Segment Anything Model, vào CVAT local để tạo mask bằng point dương/âm. Phần triển khai có sự hỗ trợ của Codex; mã nguồn, cấu hình, hướng dẫn và kết quả kiểm chứng được lưu trong repo để có thể tái hiện. Khi sử dụng, tôi chọn label trong CVAT, chấm point vào vùng/vật cần lấy, kiểm tra và sửa mask rồi mới xác nhận, Save. Model không tự quyết định nhãn của đối tượng.

**Cấu hình đã triển khai ngày 12/11/2026.** CVAT Community v2.74.1 chạy bằng Docker Desktop/WSL2; function Nuclio tên **MobileSAM Local (points)**, ID `pth-mobilesam-local`, một worker. Model `vit_t` chạy bằng GPU **GeForce MX250 2 GB**, PyTorch 2.5.1+cu118 và CUDA runtime 11.8. Checkpoint được tải từ nguồn MobileSAM cố định phiên bản và kiểm SHA256. Adapter trả mask CVAT có thể chỉnh sửa; embedding của ảnh đang thao tác được giữ lại để phục vụ các point tiếp theo.

**Kết quả kiểm chứng thực tế.** Trên ảnh `7ee6d192-89e2408b.jpg` kích thước 1280 × 720, point dương (640, 600) trên đường và point âm (640, 150) trên trời tạo được mask gợi ý vùng đường. Độ trễ HTTP tới Nuclio ở lần suy luận đầu sau khởi động là **11.062 giây**; bốn lần gọi lại cùng ảnh có cache là **0.494–0.760 giây/lần**. Snapshot sau suy luận ghi nhận GPU dùng **449 MiB/2048 MiB**, RAM container model khoảng **761.9 MiB**. Đây là số đo trên một ảnh và cấu hình cụ thể.

Đã đạt **5 kiểm thử định dạng mask** và **4 lượt gọi qua backend CVAT** trên `easy_semantic` (task 3, job 3, frame 0): point dương, thêm point âm, lặp ảnh có cache và xử lý ROI. Các lượt gọi trả mask hợp lệ; hash annotation trước/sau giống nhau, không lưu mask thử vào bài đang làm. Phần kiểm chứng qua CVAT dùng APIClient trong tiến trình Django, không phải đo toàn bộ thao tác trên trình duyệt.

**Đánh giá và giới hạn.** Công cụ hướng tới giảm thao tác vẽ biên bằng tay và cho phép sửa gợi ý bằng point/brush. Hiện mới đo độ trễ kỹ thuật, **chưa đo thời gian vẽ tay so với dùng SAM nên chưa kết luận phần trăm tăng năng suất**. Chưa kiểm chứng thao tác click/xác nhận/Save trực tiếp trên trình duyệt do công cụ điều khiển Chrome không xác định được URL. Confidence của SAM không được dùng làm mIoU hoặc điểm bài. Khi dùng trong bài, tôi vẫn phải kiểm class, biên, số object và tuân thủ yêu cầu tự vẽ object Medium đầu tiên trước gợi ý.

**Cách tái hiện:** Xem [mã triển khai và hướng dẫn](../../integrations/cvat-sam/README.md). Checkpoint, Docker image và cache được giữ local, không đưa vào Git.
