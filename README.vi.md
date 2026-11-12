# REA-Video-Pro-Max

## Giải mã cách dựng. Tạo nội dung mới cùng phong cách.

**Biến video tham chiếu thành timeline có bằng chứng và template phong cách tái sử dụng. Sau đó đưa script và media khác vào để render video của bạn.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[Xem walkthrough](docs/index.html) · [Video A](docs/media/reference.mp4) · [Video B](docs/media/adapted.mp4) · [Kiểm chứng (English)](docs/VALIDATION.md)

Một bản edit tốt chứa nhiều quyết định: cắt ở đâu, chia chữ thế nào, từ nào sáng lên, chuyển động kết thúc khi nào và hình gặp tiếng ra sao. REA-Video-Pro-Max làm những phần được hỗ trợ của hệ quyết định đó có thể kiểm tra và tái sử dụng.

```text
Video A → phân tích + timeline suy luận → style template + nội dung mới → project chỉnh sửa được → Video B
```

Demo dùng media synthetic do dự án sở hữu. A và B có chữ/media khác nhau. Website chỉ trình bày kết quả đã ghi; không chạy inference trực tiếp hay upload video của người xem.

## Bạn có thể yêu cầu gì?

- Bóc toàn bộ video thành shot, subtitle/style, motion, cue âm thanh và timeline có timestamp.
- Chỉ phân tích một frame: typography, bố cục và màu; frame đơn không đủ để suy timing hay âm thanh.
- Rút ra style rồi dùng script, ảnh hoặc footage mới để tạo một video khác.
- Giữ timeline và file phân tích riêng khi bạn chỉ cần REA.

```text
Dùng REA-Video-Pro-Max phân tích reference.mp4 thành timeline và style. Sau đó dùng script mới và assets của tôi để tạo video khác có cách chạy subtitle, motion và nhịp dựng tương tự. Bàn giao template, project, video và các phần chưa kiểm chứng.
```

## Kết quả đầu tiên

Cần Python 3.11+, FFmpeg và FFprobe. Runtime Python dùng Pillow, NumPy và PyAV. Tesseract là tùy chọn cho OCR; language data đã cài quyết định ngôn ngữ có thể chạy. [Phạm vi hỗ trợ (English)](docs/SUPPORT-MATRIX.md) ghi ranh giới kiểm chứng.

macOS là nền tảng đã đo kiểm. Linux là mục tiêu CI dự kiến; chưa chứng nhận renderer native trên Windows. Kiểm chứng tạo video cần render receipt khớp hash và một lượt OCR độc lập, nên luồng demo đầy đủ cần Tesseract cùng dữ liệu `eng`.

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Các lệnh dùng cấu trúc Git checkout. Với gói skill đã giải nén, entrypoint là `scripts/rea-video-pro-max.py`; giữ nguyên các thư mục `lib`, `assets`, `references`. Dùng Python đã cài dependencies; không chỉ sao chép file entrypoint.

## Đưa nội dung của bạn vào

`examples/content.json` là ví dụ synthetic của content binding: các scene mới gồm `id`, `text`, `duration`, `background`, `accent` và `asset` tùy chọn. `width`, `height`, `fps` đặt đầu ra; `audio`/`font` tùy chọn. Đường dẫn media tính từ thư mục file bindings. Project sao chép asset và ghi hash; không âm thầm lấy footage/nhạc của A làm nội dung B. Lời mới cần timing mới; phương pháp ước lượng được ghi rõ khi chưa có alignment chính xác.

Âm thanh của footage scene bị tắt; muốn có tiếng hãy đưa `audio` mới vào riêng. Footage ngắn giữ frame cuối; footage đưa vào renderer native phải thẳng chiều và pixel vuông. CSV chỉ xuất các dòng shot. Kiểm tra hỗ trợ shaping/grouping trước khi chọn ngôn ngữ phức tạp hoặc hai chiều.

## Dùng với Claude Code / Codex

Sao chép toàn bộ `skills/rea-video-pro-max` vào thư mục skill của host hoặc nhờ agent cài từ checkout này. Vị trí project-local thường là `.claude/skills/rea-video-pro-max` hoặc `.agents/skills/rea-video-pro-max`. Cài skill không tự cài FFmpeg, OCR languages hay model weights. Host có tài khoản, quyền chạy và chính sách dữ liệu riêng. [Skill](skills/rea-video-pro-max/SKILL.md) và các tài liệu kỹ thuật hiện bằng English.

## Dữ liệu và hành vi xuất

- Native JSON giữ analysis, timeline, caption/style/motion/audio, template và project. CSV phục vụ kiểm tra editorial data.
- SRT/WebVTT/ASS xuất text và timing theo khả năng từng format; SRT không giữ đầy đủ typography hoặc motion.
- Timeline interchange chỉ dùng adapter mà phiên bản đang cài báo available; receipt ghi phần xuất được, approximation và losses. Không đảm bảo mọi effect hoạt động ở mọi editor.
- Renderer software dùng nội dung mới và FFmpeg để encode video; không cần filters FFmpeg tùy chọn `drawtext`, `ass`, `subtitles`.

## Giới hạn quan trọng

Metadata đo được, OCR detection, style fitting và giả thuyết cơ chế là những loại bằng chứng khác nhau. Video flatten không xác định duy nhất clip nguồn, layer bị che, font/plugin/editor/project gốc hay prompt AI. Phạm vi đầu tập trung timing, captions và primitive 2D được hỗ trợ; chưa phải universal video decompiler hoặc sản phẩm đã chứng minh mạnh nhất. Occlusion phức tạp, 3D, HDR mastering và NLE round-trip tùy ý nằm ngoài ranh giới đã kiểm. Complex-script shaping cần hỗ trợ và test riêng; chín bản README không chứng nhận chín ngôn ngữ OCR/render.

Video B được kiểm theo nội dung mới, style contract và playback, thay vì điểm giống toàn frame với A. Check kỹ thuật khác đánh giá sáng tạo của con người. [Bằng chứng và giới hạn hiện tại (English)](docs/VALIDATION.md).

## Local và ghi công

Core chạy local, không yêu cầu API trả phí, không upload video lên dịch vụ inference và không tự publish. Cài dependency hoặc dùng provider tùy chọn có thể cần mạng; chính sách host Claude/Codex tách biệt. [Privacy (English)](docs/PRIVACY.md). Lấy cảm hứng từ JuneYaooo/rea-video; đây là sản phẩm độc lập, không phải official upgrade. License source/font/media/codec/model được áp dụng riêng.

Report local mặc định sao chép video tham chiếu và evidence. `report --no-media` chỉ bỏ bản sao media đầy đủ, vẫn giữ OCR text, đường dẫn local và crop. Kiểm tra trước khi chia sẻ.

[Support (English)](SUPPORT.md) · [Maintenance (English)](docs/MAINTENANCE.md) · Các bản dịch chưa có chứng nhận rà soát chuyên nghiệp bởi người bản ngữ.

[Speech local và chuyển động nâng cao (tài liệu kỹ thuật tiếng Anh)](skills/rea-video-pro-max/references/speech-and-motion.md).
