# MobileSAM local cho CVAT

Tích hợp **MobileSAM vit_t** vào CVAT Community để chọn nhãn, chấm point dương/âm và nhận mask có thể chỉnh sửa. Mã triển khai nằm trong repo bài thực hành; model và dữ liệu CVAT chạy trên máy local.

Môi trường mục tiêu: Windows + Docker Desktop WSL2, CVAT **v2.74.1**, NVIDIA MX250 **2 GB VRAM**, CPU i5-10210U và khoảng 12 GB RAM. Kết quả kiểm chứng thực tế được lưu tại [báo cáo SAM](../../report/sam/README.md).

## Luồng xử lý

```text
CVAT UI: chọn label, chấm point
  -> CVAT server lấy ảnh và dịch tọa độ ROI nếu có
  -> Nuclio / pth-mobilesam-local
  -> MobileSAM encoder + prompt/mask decoder local
  -> mask CVAT RLE với tọa độ ảnh gốc
  -> CVAT UI xem trước, chỉnh sửa, xác nhận và Save
```

Function dùng giao thức interactor `version: 2`, trả `shapes` kiểu `mask`. Không dùng ID của function SAM ViT-H vì ID đó được plugin SAM trong UI xử lý đặc biệt. Không thay decoder ONNX hoặc sửa mã giao diện CVAT. Label do người dùng chọn trong CVAT, model không tự phân loại.

Một worker giữ một `SamPredictor`; embedding được tái sử dụng khi nội dung ảnh không đổi. Chuyển ảnh/ROI sẽ tính embedding mới. Mỗi lần gọi vẫn truyền đủ point dương/âm để không lẫn trạng thái giữa các object. Không có chức năng tự chạy annotation theo task.

## Triển khai trên Windows

Yêu cầu Docker Desktop đang chạy, WSL2 distro `Ubuntu` có Docker CLI, và container `cvat_server` hiện có. Khởi chạy các lệnh sau từ **gốc repo bài thực hành** bằng PowerShell:

```powershell
.\integrations\cvat-sam\scripts\check-environment.ps1
.\integrations\cvat-sam\scripts\deploy.ps1 -Device gpu
```

Script tự xác định project, network và các file Compose từ container `cvat_server`, tải checkpoint có checksum, build base image và đăng ký function bằng Nuclio 1.16.3. Chỉ bổ sung Nuclio và áp dụng override lên `cvat_server`/`cvat_worker_annotation`; không chỉnh file Compose gốc và không chạy `down` hoặc xóa volumes. `cvat_server` có thể gián đoạn ngắn khi được tạo lại: Save thao tác đang làm trước khi triển khai.

Nếu WSL dùng tên distro khác, thêm `-Distro TenDistro`. Có thể truyền `-CvatComposeFiles @('C:\path\docker-compose.yml', 'C:\path\override.yml')` nếu cấu hình Compose đang dùng không được nhận diện đúng. Giữ các override đã dùng trước đó. Sau lần triển khai đầu, tiếp tục khởi động CVAT cùng file `compose.override.yml` này để giữ `CVAT_SERVERLESS=1`.

GPU dùng **PyTorch 2.5.1 / torchvision 0.20.1 / CUDA 11.8** để phục vụ GPU cũ; không lấy tùy ý bản CUDA/PyTorch mới nhất. `CUDA Version` hiển thị bởi `nvidia-smi` là khả năng của driver, không phải phiên bản runtime mà model đang dùng. Trường `cuda_runtime` ở kết quả kiểm tra cho biết runtime thực tế.

Chạy CPU nếu GPU không tương thích hoặc hết VRAM:

```powershell
.\integrations\cvat-sam\scripts\deploy.ps1 -Device cpu
```

CPU và GPU dùng cùng function ID nên chuyển chế độ sẽ thay function, không tạo hai bản model chạy đồng thời. Khi chỉ sửa handler/config và base image đã có, có thể dùng `-SkipBuild`; khi sửa Dockerfile, requirements, tests hoặc script smoke-test thì cần build lại base image.

Dashboard Nuclio ở `http://localhost:8070`, chỉ bind dashboard vào loopback. Cổng inference được Nuclio cấp khi deploy. Xem trạng thái/log:

```powershell
docker ps --filter name=nuclio
docker logs --tail 100 nuclio-nuclio-pth-mobilesam-local
```

## Sử dụng trong CVAT

1. Save job đang mở và tải lại trang CVAT.
2. Mở job, vào AI Tools/Interactors (tên menu có thể khác theo UI).
3. Chọn **MobileSAM Local (points)** và label muốn tạo.
4. Bấm Interact, chấm point dương bên trong đối tượng.
5. Thêm point dương vào phần thiếu; dùng thao tác point âm theo hướng dẫn UI để loại phần tràn.
6. Kết thúc tương tác, kiểm tra mask bằng mắt, sửa bằng brush khi cần và Save.

Object Medium đầu tiên của bài phải tự vẽ trước khi dùng gợi ý theo `RULES.md`. Model hỗ trợ dựng mask, người làm bài vẫn kiểm class, phần nhìn thấy, object thiếu/thừa và gộp/tách instance. Function không ghi annotation trực tiếp vào task; chỉ khi người dùng xác nhận và Save thì CVAT mới lưu.

## Kiểm chứng và số liệu

Chạy toàn bộ kiểm tra (task `easy_semantic` phải đã có ảnh trong CVAT):

```powershell
.\integrations\cvat-sam\scripts\verify.ps1 -Device gpu
```

Kết quả ở `integrations/cvat-sam/runtime/`: JSON số đo, ảnh overlay và kết quả đường gọi CVAT. Thêm `-SkipCvat` nếu chỉ muốn kiểm model/Nuclio khi chưa tạo task. Dùng `-Device cpu` nếu đã build bản CPU.

Unit tests kiểm tra RLE giữ đúng lỗ, vùng rời, biên ảnh, bbox inclusive và từ chối point không hợp lệ:

```powershell
docker run --rm cvat.mobilesam.base:gpu python -m unittest discover -s /opt/mobilesam/tests -v
```

`scripts/smoke-test.py` chạy ảnh thật qua model hoặc URL Nuclio, ghi JSON thời gian/VRAM và ảnh overlay. Cần mount ảnh chỉ đọc và thư mục output riêng khi chạy trong container. Dùng `--url http://host.docker.internal:<port>` để kiểm HTTP; bỏ `--url` để đo model trực tiếp. Hỗ trợ `--point x y`, `--negative x y`, `--repeat N`, `--output PATH`.

`scripts/verify-cvat.py` được đưa vào Django shell để kiểm đường gọi CVAT thực sự, gồm positive point, negative point, cache và ROI. Script dùng test client trong tiến trình với user owner hiện có, không tạo token; so hash annotation trước/sau để xác nhận dữ liệu không bị sửa. Đây là kiểm chứng backend, không thay thế lần thử click trên trình duyệt.

Số đo encoder/decoder và HTTP là độ trễ kỹ thuật. Muốn kết luận tăng năng suất cần đo thêm thời gian thao tác thực tế (vẽ tay so với SAM, gồm cả chỉnh sửa) trên các object tương đương. Không suy ra mIoU hoặc điểm từ confidence của SAM.

## File đưa lên Git

- Commit: handler, config, Dockerfile, scripts, tests, tài liệu và bằng chứng thực tế đã chọn.
- Không commit: `weights/`, `.cache/`, `runtime/`, `.venv/`, `.env` và Docker volumes. `.gitignore` riêng trong thư mục này đã loại trừ chúng.
- Không đưa file ground truth, token hay password vào bằng chứng. ZIP bài làm cuối vẫn xuất từ CVAT vào `submissions/` theo yêu cầu đề.

## Nguồn và giấy phép

- [MobileSAM](https://github.com/ChaoningZhang/MobileSAM), revision `f706ad9c4eb7f219c00d9050e46328518ffb65d2`, Apache-2.0. Trọng số gốc `weights/mobile_sam.pt`, **40,728,226 bytes**.
- SHA256 checkpoint: `6dbb90523a35330fedd7f1d3dfc66f995213d81b29a5ca8108dbcdd4e37d6c2f`.
- [CVAT v2.74.1](https://github.com/cvat-ai/cvat/tree/v2.74.1), MIT; tham khảo API interactor và quy tắc RLE.
- [Nuclio 1.16.3](https://github.com/nuclio/nuclio/releases/tag/1.16.3), Apache-2.0.

Mã adapter trong thư mục này được viết riêng cho bài thực hành; không đóng gói lại mã nguồn hoặc trọng số của dự án bên thứ ba vào Git. Môi trường tải và cài thư viện từ nguồn được dẫn ở trên.
