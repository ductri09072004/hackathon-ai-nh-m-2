# ĐỀ THI HACKAITHON 2026

## 1. Bối cảnh

- FPT Play có nguồn nội dung VOD phong phú về phim và thể thao. Việc chọn những khoảnh khắc hấp dẫn, dựng clip, bổ sung nhạc và đóng gói để phục vụ mục đích truyền thông hiện cần nhiều thao tác thủ công.
- Các đội cần xây dựng một prototype ứng dụng AI giúp rút ngắn quy trình này, hỗ trợ đội nội dung tạo highlight/trailer nhanh hơn, nhằm quảng bá nội dung và thu hút người xem về FPT Play.

## 2. Bài toán

- **Đầu vào:** 1 VOD do BTC cung cấp, mỗi đội chọn một loại nội dung (**phim** hoặc **thể thao**).
- **Đầu ra:** 1 clip ngắn được tạo tự động với định dạng MP4, dài khoảng 30–600s (tuỳ thể loại), với tỉ lệ 9:16 hoặc 16:9, bao gồm các tiêu chí:

### Bắt buộc

- Phân tích VOD bằng một hoặc nhiều tín hiệu (hình ảnh, lời thoại, âm thanh, chuyển cảnh, hành động…), tự đề xuất đoạn cắt với timestamp bắt đầu/kết thúc.
- Chọn và sắp xếp các đoạn để tạo clip có ý nghĩa, thay vì ghép ngẫu nhiên.
- Tạo nhạc AI mới và ghép vào clip (không dùng nhạc trending hoặc nhạc có sẵn để thay thế; nhạc phù hợp với cảm xúc và nhịp clip).
- Tự động cắt, ghép và xuất video (giữ ngữ cảnh, âm thanh nghe rõ).
- Có giao diện web chọn VOD, chạy xử lý/xem trạng thái, xem trước và tải clip.
- Cho phép người dùng duyệt đề xuất, nhưng không thay phần chọn đoạn của AI bằng thao tác thủ công.

### Tùy chọn

- Có giải thích ngắn vì sao chọn đoạn đó (không yêu cầu mô hình phải cung cấp diễn giải suy luận nội bộ) nếu được chọn tự động bởi AI.
- Cho phép người dùng chọn trực tiếp trên video hoặc nhập timestamp bắt đầu/kết thúc để thêm, thay thế, loại bỏ, điều chỉnh và sắp xếp lại các đoạn theo mong muốn. Hỗ trợ kết hợp các đoạn AI đề xuất với các đoạn người dùng tự chọn trước khi dựng clip.
- Subtitle/voice-over lời thoại tự động, caption sáng tạo, hài hước, bắt trend.
- Nhiều phong cách: cinematic, dramatic, funny, energetic…
- Tạo nhiều phương án clip để người dùng lựa chọn.
- Tự crop theo nhân vật/quả bóng/vùng hành động.
- Đề xuất tiêu đề/mô tả bài đăng, đăng bài tự động.
- Hiển thị rõ ràng trạng thái đang xử lý.
- Lịch sử tương tác/chỉnh sửa.

### Luồng trải nghiệm kỳ vọng

1. Chọn VOD
2. Chọn cấu hình mục tiêu, thời lượng, phong cách, … hoặc mô tả nhu cầu qua prompt (tuỳ chọn)
3. AI đề xuất đoạn nổi bật hoặc bổ sung timestamp thủ công (tùy chọn)
4. AI tạo nhạc
5. AI tạo subtitle, voice over, caption, … (tuỳ chọn)
6. Dựng clip theo cấu hình (định dạng, tỉ lệ, …)
7. Duyệt, chỉnh sửa
8. Xem trước và tải xuống
9. Đề xuất tiêu đề/mô tả bài đăng/hashtag → Duyệt, chỉnh sửa → Đăng bài tự động (FB, TT, YT) (tuỳ chọn)

## 3. Thành viên và nhiệm vụ

| Vai trò | Trách nhiệm chính |
|---|---|
| AI Engineer | Phân tích VOD, chọn highlight, tích hợp tạo nhạc AI |
| Backend Engineer | API, pipeline xử lý, cắt ghép và render video |
| Frontend Engineer | Giao diện thao tác, trạng thái xử lý, preview và tải clip |
| Business Analyst | Chốt use case, tiêu chí chất lượng, kiểm thử và chuẩn bị trình bày + demo |

## 4. Bài nộp

- Source code và hướng dẫn chạy
- Ứng dụng demo + ít nhất 01 clip đầu ra
- Danh sách timestamp của các đoạn được sử dụng (phân biệt đoạn do AI đề xuất, người dùng chỉnh sửa hoặc người dùng tự chọn)
- Thông tin công cụ và prompt tạo nhạc
- Slide ngắn giới thiệu giải pháp, kết quả và giới hạn

**Trình bày:** 10 phút giới thiệu + 10 phút Q&A

## 5. Một vài điểm chú ý

### Nội dung

- **Với phim:** ưu tiên cảm xúc, xung đột, câu thoại hoặc tình huống tạo tò mò (cảnh cao trào, thoại đắt, cảnh hài, cảnh cảm động, …); **hạn chế tiết lộ kết cục quan trọng**.
- **Với thể thao:** ưu tiên tình huống đáng chú ý, cao trào, kỹ thuật hoặc phản ứng (bàn thắng, cứu thua, thẻ, VAR, va chạm, ăn mừng, …); giữ đủ ngữ cảnh để người xem hiểu diễn biến.
- Có mở, thân, kết; video ngắn cần hook mạnh trong 3 giây đầu.
- Không cắt cụt giữa pha bóng hay giữa câu thoại; bỏ đoạn chết, replay trùng.
- Tự cân thời lượng theo yêu cầu.

### Đầu ra

- **Video ngắn:** [15–90 giây], 9:16, cho TikTok/Reels/Shorts
- **Video dài:** [3–10 phút], 16:9 hoặc 9:16, cho YouTube/Facebook
- **Định dạng xuất:** MP4, 1080×1920 (9:16) hoặc 1920×1080 (16:9)
- **Tệp kèm theo:** file timestamp, file phụ đề SRT, lời dẫn, gợi ý tít/caption/hashtag

## 6. Tiêu chí đánh giá

### Nguyên tắc chung

- Đánh giá khả năng giải quyết bài toán thực tế: từ VOD tạo ra clip có thể dùng để quảng bá hoặc làm highlight/trailer.
- Ưu tiên chất lượng kết quả, mức độ tự động hóa và trải nghiệm sử dụng; không chấm theo số lượng mô hình, công nghệ hoặc tính năng tích hợp.
- Chấp nhận sử dụng mô hình có sẵn, API bên ngoài và công cụ mã nguồn mở. Các đội cần công khai công cụ, mô hình và dịch vụ đã sử dụng.
- Đánh giá phù hợp với loại nội dung đội lựa chọn; không mặc định phim khó hơn hoặc thể thao dễ hơn.
- Không yêu cầu prototype đạt mức sẵn sàng vận hành production.

### Thang điểm

| Nhóm tiêu chí | Điểm tối đa | Nội dung đánh giá |
|---|:---:|---|
| **AI phân tích và lựa chọn highlight** | 20 | • Chọn được khoảnh khắc đáng chú ý, phù hợp mục tiêu clip **(10đ)**<br>• Timestamp hợp lý, giữ đủ ngữ cảnh, hạn chế cắt giữa câu thoại hoặc pha bóng **(5đ)**<br>• Hạn chế đoạn chết, nội dung trùng lặp và lựa chọn không phù hợp như spoiler quan trọng trong trailer phim **(5đ)** |
| **Chất lượng biên tập và clip đầu ra** | 15 | • Các đoạn được sắp xếp có chủ đích, tạo mạch nội dung dễ hiểu **(8đ)**<br>• Có điểm thu hút từ đầu, nhịp dựng và kết thúc phù hợp **(4đ)**<br>• Hình ảnh, âm thanh, tỉ lệ khung hình, thời lượng và định dạng xuất đáp ứng cấu hình đã chọn **(3đ)** |
| **Tạo và sử dụng nhạc AI** | 15 | • Tạo được nhạc mới bằng AI, có thông tin công cụ, prompt hoặc tham số và bằng chứng lần tạo **(5đ)**<br>• Nhạc phù hợp cảm xúc, phong cách và nhịp clip **(6đ)**<br>• Phối trộn hợp lý, không lấn át lời thoại hoặc bình luận, vào/ra nhạc tự nhiên **(4đ)** |
| **Mức độ tự động hóa và khả năng hoạt động** | 15 | • Pipeline chạy được từ VOD → AI đề xuất → tạo nhạc → dựng → xuất clip, không cần chọn đoạn hoặc dựng bằng công cụ ngoài ứng dụng **(10đ)**<br>• Xử lý ổn định, trạng thái và lỗi rõ ràng, có cách phục hồi hoặc chạy lại hợp lý **(2đ)**<br>• Có số liệu thời gian xử lý và chi phí ước tính cho lần demo, nêu được giới hạn **(3đ)** |
| **Trải nghiệm sử dụng** | 10 | • Giao diện web hỗ trợ chọn VOD, chạy xử lý, xem trạng thái, preview và tải clip **(6đ)**<br>• Luồng thao tác dễ hiểu, thuận tiện duyệt các đoạn đề xuất và phân biệt nguồn đoạn AI/người dùng nếu có chỉnh sửa **(4đ)** |
| **Tính năng mở rộng có giá trị** | 10 | • Tính năng tùy chọn hoạt động thực tế và cải thiện kết quả hoặc giảm thao tác: subtitle, caption sáng tạo, chỉnh sửa đoạn, tự crop, nhiều phương án clip, gợi ý bài đăng…<br>• Không cộng điểm đơn thuần theo số lượng tính năng |
| **Bài nộp và trình bày** | 15 | • Bài nộp đầy đủ, hướng dẫn chạy rõ ràng, có thể đối chiếu clip với timestamp và thông tin tạo nhạc **(5đ)**<br>• Trình bày rõ bài toán, giải pháp, kết quả, giới hạn và trả lời Q&A **(10đ)** |
| **Tổng** | **100** | |
