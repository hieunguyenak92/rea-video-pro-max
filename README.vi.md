# REA-Video-Pro-Max

## Trao cho Claude & Codex con mắt của một người dựng phim.

**Giải mã nhịp dựng, phụ đề và chuyển động trong video tham khảo. Biến những quyết định dựng đó thành phong cách có thể tái sử dụng. Render một video mới bằng câu chuyện và tư liệu của riêng bạn.**

Mỗi bản dựng cuốn hút đều có ngôn ngữ riêng. Hãy đưa ngôn ngữ ấy vào bộ công cụ sáng tạo của bạn.

[**▶ Khám phá demo trực tiếp**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**Tải skill**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [Bản phát hành v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Skill cho Claude Code / Codex · CLI + MCP tùy chọn · Xử lý cục bộ · Apache-2.0**

---

## Từ “Video này dựng hay quá” đến “Đây là phiên bản của tôi.”

Bạn bắt gặp một video đúng chất mình đang tìm: nhịp cắt đầy năng lượng, cách phụ đề xuất hiện, màu nhấn chạy qua từng cụm từ, cú zoom khiến một bức ảnh tĩnh có sức sống.

REA-Video-Pro-Max biến những phần phong cách được hỗ trợ thành dữ liệu bạn có thể xem, chỉnh và tái sử dụng. Đưa vào kịch bản, hình ảnh, cảnh quay hoặc lời thuyết minh mới. Nhận lại một project có thể chỉnh sửa cùng một video đã render thực sự.

| Video tham khảo A | Video B mới của bạn |
| :---: | :---: |
| [![Khung hình từ video tham khảo do dự án tự tạo](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![Khung hình đã render với lời mới và tư liệu độc lập](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| Phân tích nhịp cảnh và cách thể hiện phụ đề. | Áp dụng phong cách đã trích xuất vào một câu chuyện khác. |

*Đây là khung hình thực từ demo do dự án tự tạo. B dùng văn bản mới, tư liệu được tạo độc lập và mốc thời gian phụ đề mới. [Demo tương tác](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) cho phép bạn tua cả hai video và xem timeline, template, project cùng kết quả kiểm chứng đã ghi lại.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## Biến video tham khảo thành công cụ sáng tạo

| Điều bạn muốn làm | Kết quả bạn nhận được |
| --- | --- |
| Hiểu điều gì tạo nên cảm giác của một bản dựng | Khoảng thời gian từng cảnh, chữ nhìn thấy, diện mạo phụ đề, chuyển động biểu kiến và tín hiệu âm thanh, gắn với mốc thời gian và bằng chứng. |
| Mang cách làm phụ đề sang câu chuyện mới | Kiểu chữ, bố cục và bảng màu nhấn có thể tái sử dụng, áp dụng cho lời mới với thời gian mới. |
| Xây dựng một định dạng video cho cả loạt nội dung | Template phong cách có thể kết hợp với kịch bản và bộ tư liệu khác. |
| Chủ động điều chỉnh kết quả | Timeline/project JSON của hệ thống, kèm tư liệu đã sao chép và mã băm, để bạn kiểm tra, sửa và render lại. |
| Đưa dữ liệu phân tích vào quy trình riêng | Tệp có cấu trúc, trình xem ngoại tuyến, bản xuất phụ đề và các định dạng trao đổi timeline trong phạm vi được hỗ trợ. |

Dùng cho video giới thiệu sản phẩm, clip kiến thức, chuỗi nội dung của creator, nghiên cứu kỹ thuật dựng hoặc công cụ video do bạn tự xây. Khi chỉ cần bóc tách video, bản phân tích và timeline đã là những đầu ra hoàn chỉnh.

## Một prompt để bắt đầu

Cài skill đi kèm, cung cấp video tham khảo cùng nội dung mới cho agent, rồi yêu cầu:

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

Bạn định hướng câu chuyện. Skill cung cấp cho agent quy trình cụ thể và công cụ thực thi để phân tích, biên soạn, render và kiểm chứng.

## Chuyên môn nằm trong từng bước xử lý

- **Bản dựng có thể truy vết.** Mốc thời gian trình chiếu được giải mã, bằng chứng từng khung hình và phạm vi khảo sát giúp bạn kiểm tra nguồn gốc của timeline. Tín hiệu đo được, kết quả từ mô hình và quyết định dựng suy luận được gắn nhãn riêng.
- **Chi tiết phụ đề được giữ lại để tái sử dụng.** Ước lượng kích thước, vị trí, màu chữ và viền; giữ các bảng màu nhấn và biến thể phong cách đã quan sát. Tự xuống dòng và tính lại thời gian cho lời mới khi biên soạn.
- **Chuyển động giữ đúng chiều.** Khớp các mô hình chuyển động similarity/affine và đường cong theo thời gian trong giới hạn xác định. Renderer của hệ thống có thể tái sử dụng thành phần zoom có hướng được hỗ trợ, kể cả zoom ra.
- **Project để bạn tiếp tục phát triển.** Hình ảnh, cảnh quay, font và âm thanh tùy chọn được sao chép vào project có thể di chuyển. Liên kết nội dung tường minh và mã băm giúp bạn kiểm tra chính xác tư liệu đã chọn.
- **Nhận dạng lời nói khi công việc cần đến.** ASR faster-whisper cục bộ tùy chọn cung cấp khoảng thời gian từng từ do mô hình ước lượng. Đối chiếu chặt kịch bản/âm thanh cho phép gắn chúng vào nội dung mới; bạn phải chỉ định mô hình cục bộ.
- **Đầu ra có thể kiểm chứng.** Đối chiếu danh tính project/đầu ra, giải mã video đã render và dùng OCR độc lập để kiểm tra nội dung phụ đề. Bằng chứng được lưu cùng kết quả.

Renderer của hệ thống hỗ trợ **phụ đề static / fade / pop / slide**, **chuyển cảnh cut / dissolve / fade / wipe** và **nền static / signed panzoom**. Phân tích có thể giữ lại các quan sát chuyển động phong phú hơn khả năng tái hiện của renderer. [Phạm vi hỗ trợ chi tiết — tiếng Anh](docs/SUPPORT-MATRIX.md).

## Tạo kết quả đầu tiên

### 1. Cài môi trường chạy

Cần **Python 3.11+**, **FFmpeg + FFprobe** và bản FFmpeg có **libx264**. Cài **Tesseract với dữ liệu ngôn ngữ `eng`** để chạy ví dụ OCR và kiểm chứng phụ đề đi kèm. Các thư viện Python được cài bằng lệnh dưới đây.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

Các lệnh shell này dành cho macOS/Linux. CI của bản phát hành đã chạy đạt trên Linux và macOS; render trực tiếp trên Windows chưa được xác nhận. `doctor` báo những công cụ thực sự có trên máy bạn.

### 2. Cài skill cho agent

Sao chép **toàn bộ** thư mục `skills/rea-video-pro-max` vào thư mục skill của project:

| Agent | Đường dẫn trong project |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

Bạn cũng có thể giải nén [skill ZIP](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) vào đó. Giữ nguyên `lib`, `assets`, `scripts` và `references` cùng nhau. Nếu chỉ cài từ ZIP, cài thư viện Python bằng `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`; chạy qua `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`. Các lệnh console bên dưới được cung cấp bởi bước cài từ mã nguồn ở trên. Agent phải dùng đúng trình thông dịch Python đã cài các thư viện này.

### Tự động phân tích video từ URL công khai

Với video công khai trên YouTube, Facebook hoặc TikTok mà bạn được phép sử dụng, hãy cài phần mở rộng nhận URL tùy chọn để skill tải một bản sao cục bộ có giới hạn rồi phân tích:

```sh
python -m pip install 'rea-video-pro-max[url]'
rea-video-pro-max analyze-url 'https://www.youtube.com/shorts/VIDEO_ID' --out work/url-analysis --ocr required --ocr-lang eng
```

Nếu dùng skill ZIP đã giải nén, hãy cài trực tiếp `yt-dlp>=2025.01.15,<2027`; ZIP không tự cài phần phụ thuộc tùy chọn.

Skill ZIP v0.1.1 được liên kết ở trên được phát hành trước adapter URL tùy chọn này; hãy dùng checkout hiện tại để nhận URL cho đến bản phát hành kế tiếp.

Lệnh lưu video, `url-source.json` chứa URL, bộ trích xuất, thời lượng, dung lượng và SHA-256, sau đó ghi các tệp phân tích thông thường dưới `work/url-analysis/analysis/`. Lệnh không dùng thông tin đăng nhập, không vượt DRM, không nhận playlist/livestream và không tải model. Quyền truy cập, bản quyền và điều khoản nền tảng vẫn thuộc trách nhiệm của bạn. [Chi tiết nhận URL — tiếng Anh](skills/rea-video-pro-max/references/url-ingestion.md).

### 3. Chạy ví dụ A → B đi kèm

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

Mở `work/video-b.mp4`. Project có thể di chuyển nằm ở `work/project/`; dữ liệu phân tích video tham khảo ở `work/analysis/`. Mỗi lần biên soạn nên dùng một thư mục đầu ra mới. Để tạo trình xem phân tích ngoại tuyến, chạy:

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

Sau đó mở `work/report/timeline.html` ngay trên máy. [CLI, skill và MCP tùy chọn dùng chung một lõi xử lý — tài liệu tiếng Anh](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>Đưa câu chuyện của bạn vào: tệp liên kết nội dung gồm những gì?</strong></summary>

Tệp liên kết nội dung là JSON xác định các cảnh, lời, tư liệu và âm thanh/font tùy chọn cho video mới. Agent có thể tạo tệp này từ yêu cầu thông thường của bạn. Bắt đầu với [examples/content.json](examples/content.json).

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

Thêm đường dẫn `asset` cho ảnh hoặc video, và `audio` để chọn nhạc hoặc lời thuyết minh cụ thể. Đường dẫn tư liệu được tính tương đối từ tệp JSON này. Renderer dùng nội dung mới đã chọn; muốn dùng lại chính tư liệu của video tham khảo, bạn phải cho phép tường minh.

Lời mới có thời gian mới. Phân bổ thời gian theo số ký tự chỉ là ước lượng. Khi cần bám lời nói, hãy cung cấp khoảng thời gian từ mới hoặc dùng ASR cục bộ với đối chiếu nội dung chặt chẽ. [Hướng dẫn lời nói và chuyển động — tiếng Anh](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## Xem bằng chứng phía sau lời hứa

**v0.1.1 đã vượt qua 176 bài kiểm thử cục bộ**, bao gồm trường hợp thực chạy ASR cục bộ tùy chọn. [CI đã chạy đạt ba tác vụ trên Linux/macOS](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). Sáu tệp phát hành đã được tải xuống và đối chiếu với dữ liệu byte cùng checksum cục bộ.

Bằng chứng bao gồm một lần chạy hoàn chỉnh **A → phân tích → phong cách → B mới** trên video do dự án tự tạo; một tác vụ tiếng Việt độc lập với kiểu chữ/viền đã hiệu chỉnh và hai chế độ màu nhấn; cùng tác vụ chuyển động giữ đúng chiều zoom vào/zoom ra. Các trường hợp này có phạm vi xác định, xác minh quy trình đã trình diễn; chúng chưa chứng minh độ chính xác trên nhiều thể loại hoặc ngôn ngữ.

[Xem phân tích](docs/evidence/reference-analysis.json) · [Đọc template](docs/evidence/style-template.json) · [Mở project](docs/evidence/project.json) · [Xem kết quả kiểm chứng](docs/evidence/verification.json) · [Chi tiết kiểm thử — tiếng Anh](docs/VALIDATION.md)

## Giữ trọn đầu ra. Mở rộng khả năng.

| Định dạng | Dữ liệu được mang theo |
| --- | --- |
| JSON của hệ thống | Phân tích, timeline, dữ liệu phụ đề/phong cách/chuyển động/âm thanh, template và project có thể chỉnh sửa. |
| CSV | Các dòng dữ liệu cảnh để kiểm tra và xử lý tiếp. |
| SRT / WebVTT | Chữ nhìn thấy cùng khoảng thời gian hiển thị. |
| ASS | Thời gian phụ đề với phong cách thay thế được chỉ rõ; diện mạo quan sát được và độ bất định vẫn nằm trong bằng chứng của hệ thống. |
| OTIO / EDL | OTIO tùy chọn chứa các đoạn video tham khảo kèm chú thích; EDL cho các điểm cắt đo được ở tốc độ khung hình cố định nguyên. Biên nhận xuất mô tả dữ liệu bị mất. |
| MP4 + HTML ngoại tuyến | Video mới cùng báo cáo phân tích có thể xem trên máy. |

Project của hệ thống là JSON có thể chỉnh sửa. Bản này chưa xuất project gốc của Premiere, Resolve, After Effects hoặc CapCut, cũng chưa xuất FCPXML. Việc nhập các tệp trao đổi được hỗ trợ vào phần mềm dựng bên ngoài vẫn chưa được kiểm chứng. [Giới hạn xuất tệp và render — tiếng Anh](docs/SUPPORT-MATRIX.md).

## Nắm rõ phạm vi để sáng tạo chủ động

Bản hiện tại tập trung vào bằng chứng dựng nhìn thấy được và tái sử dụng phong cách **2D** trong phạm vi hỗ trợ. Font gốc chính xác, lớp ẩn, plugin, tư liệu nguồn và lịch sử project có thể vẫn chưa biết. OCR và phép khớp chuyển động có thể sai; phạm vi lấy mẫu và độ bất định luôn được thể hiện.

Cảnh quay đưa vào phải đúng chiều và dùng pixel vuông. Âm thanh của từng cảnh quay bị tắt; hãy chỉ định âm thanh riêng. Chữ viết phức tạp cần font và bộ xử lý định hình chữ phù hợp; hệ thống từ chối phụ đề hai chiều. Chín bản README là chín ngôn ngữ tài liệu, chưa phải chín ngôn ngữ OCR/render đã được xác nhận. Đánh giá phong cách sáng tạo và âm thanh vẫn cần người xem. [Toàn bộ phạm vi hỗ trợ — tiếng Anh](docs/SUPPORT-MATRIX.md).

Lõi xử lý chạy cục bộ, không cần API mô hình trả phí hay tải nội dung lên dịch vụ. Cài thư viện và mô hình tùy chọn có thể cần mạng; môi trường Claude/Codex có chính sách dữ liệu riêng. Báo cáo cục bộ mặc định chứa bản sao video tham khảo và ảnh cắt. `report --no-media` bỏ bản sao toàn bộ video, nhưng vẫn giữ chữ và ảnh cắt. [Quyền riêng tư — tiếng Anh](docs/PRIVACY.md).

## Cùng xây cách dựng video tiếp theo

**Nếu bạn muốn có quy trình này trong bộ công cụ sáng tạo của mình, hãy tặng dự án một star.** Đó là cách giúp các creator và người xây công cụ AI khác tìm thấy dự án.

**Fork để xây ngôn ngữ dựng của riêng bạn:** thêm một kiểu phụ đề, phát triển adapter render, mở rộng cách xuất tệp hoặc đóng góp ví dụ từ video tham khảo đến kết quả trên tư liệu bạn sở hữu. Mang theo bằng chứng có thể chạy lại để mỗi khả năng mới đều đứng vững.

[**⭐ Tặng star trên GitHub**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Fork và phát triển**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [Đóng góp — tiếng Anh](CONTRIBUTING.md) · [Gửi tác vụ cần giải quyết](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

Dự án độc lập, lấy cảm hứng từ [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). [Apache-2.0](LICENSE); điều khoản riêng của font, codec và mô hình được giữ trong [NOTICE](NOTICE).

[Hỗ trợ — tiếng Anh](SUPPORT.md) · [Bảo trì — tiếng Anh](docs/MAINTENANCE.md) · [Hướng dẫn skill — tiếng Anh](skills/rea-video-pro-max/SKILL.md)
