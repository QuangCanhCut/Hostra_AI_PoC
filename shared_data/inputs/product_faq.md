# HOSTRA AI PoC — Product FAQ: ASUS Vivobook S 14 OLED & Lenovo IdeaPad Slim 5 Xiaoxin 14

**Phiên bản:** 1.1 (mock knowledge base; thống nhất SKU/FAQ IDs)  
**Ngày chuẩn bị:** 27/10/2026  
**Mục đích:** Câu trả lời tham khảo cho Verified AI Agent + RAG trong phiên demo tư vấn và so sánh 2 laptop.  
**Trạng thái:** Nội dung tư vấn do nhóm biên soạn, **không phải FAQ chính thức của hãng/cửa hàng**.

## 0. Cách sử dụng và quy tắc bán hàng an toàn

- **Nguồn dữ liệu ưu tiên:** `shared_data/inputs/catalog_skus.json` (giá, tồn kho, thông số đã chuẩn hóa). FAQ này diễn giải thông tin thành lời tư vấn. Khi có mâu thuẫn, **không tự chọn**: yêu cầu đối chiếu và cập nhật dữ liệu trước khi trả lời.
- **SKU:** ASUS = `LAPTOP-ASUS-001`; Lenovo = `LAPTOP-LENOVO-002`. Khi trả lời so sánh, truy xuất **cả hai** sản phẩm và dẫn đủ bằng chứng.
- **Giá demo:** ASUS **26.500.000 VNĐ**; Lenovo **25.690.000 VNĐ**. **Tồn kho demo:** 10 máy mỗi mẫu. Đây là số liệu giả lập của HOSTRA PoC, **không phải giá/tồn kho đang có trên thị trường**. Nói rõ là “trong phiên demo” khi khách hỏi.
- **Không cam kết nếu thiếu dữ liệu:** thời lượng pin thực tế (giờ), FPS/game, benchmark CPU/GPU, khuyến mãi, giao hàng, trả góp, thu cũ đổi mới, đổi trả, bảo hành ASUS trong demo, mức giá tại cửa hàng thật, hiệu năng ứng dụng cụ thể. Có thể giải thích điều đã biết và xin kiểm tra điều chưa rõ.
- **Bảo hành Lenovo:** `catalog_skus.json` lưu **12 tháng tham khảo từ LaptopAZ**; đây **không** tự động là chính sách bán hàng của HOSTRA PoC. Bảo hành ASUS chưa được chốt trong Catalog. Không khẳng định cửa hàng PoC đang áp dụng chính sách của bên thứ ba.
- **Tránh thổi phồng:** không nói “máy nào mạnh hơn toàn diện” chỉ vì tên CPU/số nhân; không khẳng định OLED không mỏi mắt, pin 75Wh chắc chắn dùng lâu hơn 50Wh, hay GPU tích hợp chạy game/AI chuyên sâu ở FPS nhất định khi chưa có benchmark.
- **Phong cách tư vấn:** trả lời thẳng câu hỏi → nêu lợi ích phù hợp với nhu cầu → hỏi **một câu ngắn** để chốt tiêu chí. Không gây áp lực bằng ưu đãi, tồn kho hay thời gian đếm ngược không có thật.
- **Tra cứu RAG:** Mỗi mục `FAQ-*` là một đoạn độc lập; có `SKU`, `Câu hỏi`, `Trả lời gợi ý`, `Hỏi thêm`, `Bằng chứng`. Có thể index theo tiêu đề + câu hỏi + câu trả lời. `FAQ-*` là ID đoạn kiến thức; `catalog:<SKU>` là tham chiếu đến bản ghi sản phẩm. Cần kiểm tra tính đúng đắn của thông tin trước khi tạo `AgentResponse.status="answered"`.

### Nguồn tham khảo

- `catalog:LAPTOP-ASUS-001` — `catalog_skus.json`, ASUS Vivobook S 14 OLED S5406MA-PP136W.
- `catalog:LAPTOP-LENOVO-002` — `catalog_skus.json`, Lenovo IdeaPad Slim 5 Xiaoxin 14 AHP10R 2025 NKFV.
- ASUS: https://www.thegioididong.com/laptop/asus-vivobook-s-14-oled-s5406ma-ultra-5-pp136w
- Lenovo: https://laptopaz.vn/lenovo-ideapad-slim-5-ahp10r-2025-nkfv-ryzen-7-h-255-16gb-512gb-14-fhd-120hz.html

> **Lưu ý giá và tình trạng:** Trang tham khảo ASUS ghi *ngừng kinh doanh*; Lenovo có thể thay đổi giá theo thời điểm. Giá và tồn kho nêu trong FAQ này chỉ là kịch bản giả lập, không phải báo giá từ các website.

---

## 1. FAQ — ASUS Vivobook S 14 OLED S5406MA-PP136W

### FAQ-ASUS-001 — ASUS này giá bao nhiêu, còn hàng không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “ASUS này giá nhiêu? Có sẵn không?”
- **Trả lời gợi ý:** “Dạ, **trong phiên demo HOSTRA**, ASUS Vivobook S 14 OLED có giá **26.500.000 đồng**, số lượng giả lập còn **10 máy**. Đây là giá và tồn kho để thử hệ thống, không phải báo giá bán hàng thực tế ạ.”
- **Hỏi thêm:** “Anh/chị đang ưu tiên màn hình đẹp hay khả năng nâng cấp về lâu dài ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-002 — ASUS dùng chip gì, có phù hợp học và làm việc không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Chip con ASUS này là gì, học đại học/làm văn phòng ổn không?”
- **Trả lời gợi ý:** “Máy sử dụng **Intel Core Ultra 5 125H, 14 nhân/18 luồng**, RAM **16GB** và SSD **1TB**. Cấu hình này phù hợp để cân nhắc cho học tập, lập trình và làm việc nhiều tác vụ. Mức mượt ở từng phần mềm còn tùy yêu cầu thực tế, nên em không cam kết hiệu năng khi chưa thử ạ.”
- **Hỏi thêm:** “Anh/chị thường dùng Office, lập trình hay phần mềm đồ họa nào nhất ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-003 — Màn hình ASUS có gì nổi bật?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Màn hình OLED ASUS có đẹp hơn màn bình thường không?”
- **Trả lời gợi ý:** “Điểm nổi bật của mẫu ASUS là màn hình **14 inch OLED, 2880 × 1800 (2.8K), 120Hz**. OLED có ưu thế về độ tương phản và khả năng hiển thị màu đen; độ phân giải cao giúp hình ảnh, chữ sắc nét. Đây là lựa chọn đáng cân nhắc nếu anh/chị ưu tiên trải nghiệm hình ảnh và sáng tạo nội dung.”
- **Hỏi thêm:** “Anh/chị thường chỉnh ảnh, xem phim hay làm việc với văn bản nhiều hơn ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-004 — ASUS có nâng cấp RAM được không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “RAM ASUS này nâng lên 32GB được không?”
- **Trả lời gợi ý:** “Dạ **không**. Mẫu ASUS này dùng **16GB LPDDR5X onboard** và Catalog ghi **không hỗ trợ nâng cấp RAM**. Nếu anh/chị dự kiến tăng RAM sau này, Lenovo trong bộ demo sẽ linh hoạt hơn ở tiêu chí này.”
- **Hỏi thêm:** “Anh/chị đang cần 16GB hiện tại hay có kế hoạch chạy nhiều máy ảo/container trong tương lai ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-ASUS-005 — Ổ cứng ASUS bao nhiêu, có nâng thêm được không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “ASUS có 1TB thật không? Lắp thêm SSD được chứ?”
- **Trả lời gợi ý:** “Máy có **SSD 1TB NVMe PCIe Gen 4** theo thông tin Catalog. Còn việc có thêm khe SSD hay hỗ trợ nâng cấp cụ thể, **bộ dữ liệu hiện chưa xác nhận** nên em không dám khẳng định ạ.”
- **Hỏi thêm:** “Anh/chị cần nhiều dung lượng để lưu tài liệu, game hay video ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-006 — ASUS có card đồ họa rời không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Máy ASUS dùng RTX hay card rời ạ?”
- **Trả lời gợi ý:** “Mẫu này sử dụng **Intel Arc Graphics tích hợp**, không phải card đồ họa rời NVIDIA RTX trong cấu hình đang lưu. Máy phù hợp cân nhắc cho công việc phổ thông và một số tác vụ đồ họa; nếu cần dựng 3D nặng hoặc chạy AI bằng CUDA, nên xem thêm máy có GPU NVIDIA chuyên dụng.”
- **Hỏi thêm:** “Anh/chị dùng Photoshop/Figma hay dựng 3D, render và học deep learning ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-007 — ASUS pin bao nhiêu, dùng được mấy tiếng?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Pin ASUS này trâu không, dùng được 10 tiếng không?”
- **Trả lời gợi ý:** “Máy có pin **75Wh** và trọng lượng khoảng **1,3kg**. Đây là thông số thuận lợi khi cần mang máy đi học, đi làm. Tuy nhiên, **chưa có phép đo thời lượng pin theo cùng điều kiện sử dụng**, nên em chưa thể cam kết số giờ cụ thể.”
- **Hỏi thêm:** “Anh/chị chủ yếu làm việc trên pin hay thường cắm sạc ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-008 — ASUS có những cổng kết nối gì?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Máy có HDMI, Thunderbolt và cổng USB không?”
- **Trả lời gợi ý:** “Có ạ. Theo Catalog, máy có **2 Thunderbolt 4** hỗ trợ Power Delivery/DisplayPort, **2 USB 3.2**, HDMI, khe microSD và jack tai nghe 3,5mm. Cấu hình cổng này thuận tiện cho kết nối màn hình ngoài và phụ kiện.”
- **Hỏi thêm:** “Anh/chị muốn kết nối một hay nhiều màn hình ngoài ạ? Em sẽ kiểm tra phương án tương thích cụ thể.”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-009 — ASUS dùng Windows và kết nối không dây thế nào?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Máy có Windows bản quyền, Wi-Fi 6E không?”
- **Trả lời gợi ý:** “Theo Catalog, cấu hình ASUS đi kèm **Windows 11 Home**, hỗ trợ **Wi-Fi 6E** và **Bluetooth 5.3**. Nếu anh/chị cần bộ phần mềm Office cụ thể, em cần kiểm tra riêng chứ không mặc định đã kèm giấy phép Office.”
- **Hỏi thêm:** “Anh/chị có cần sử dụng Office bản quyền ngay khi nhận máy không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-ASUS-010 — ASUS hợp với người làm thiết kế không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “Mình làm Figma, chỉnh ảnh, edit video nhẹ thì nên chọn ASUS không?”
- **Trả lời gợi ý:** “Nếu ưu tiên **màn OLED 2.8K 120Hz**, bộ nhớ **16GB** và SSD **1TB**, ASUS là phương án đáng xem xét cho Figma, chỉnh ảnh và sáng tạo nội dung. Tuy nhiên, hiệu năng dựng video tùy dự án; máy dùng GPU tích hợp nên em không hứa sẽ render nhanh mọi tác vụ nặng.”
- **Hỏi thêm:** “Anh/chị chủ yếu chỉnh ảnh 2D hay dựng video 4K nhiều hiệu ứng ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

---

## 2. FAQ — Lenovo IdeaPad Slim 5 Xiaoxin 14 AHP10R 2025 NKFV

### FAQ-LENOVO-001 — Lenovo giá bao nhiêu, còn hàng không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo Xiaoxin này giá nhiêu, còn máy không?”
- **Trả lời gợi ý:** “Trong **phiên demo HOSTRA**, Lenovo Xiaoxin 14 có giá **25.690.000 đồng** và tồn kho giả lập là **10 máy**. Giá này được cố định cho bài thử AI, **không phải giá niêm yết hiện tại tại LaptopAZ** ạ.”
- **Hỏi thêm:** “Anh/chị muốn so sánh thêm với mẫu ASUS cùng phân khúc không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-002 — CPU Lenovo là gì, dùng lập trình được không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Ryzen 7 H 255 là chip gì? Sinh viên IT dùng ổn không?”
- **Trả lời gợi ý:** “Máy sử dụng **AMD Ryzen 7 H 255, 8 nhân/16 luồng**, RAM **16GB DDR5** và SSD **512GB**. Đây là cấu hình đáng cân nhắc cho học tập, lập trình và đa nhiệm; mức đáp ứng với project lớn còn phụ thuộc IDE, máy ảo và môi trường chạy thực tế.”
- **Hỏi thêm:** “Anh/chị học web, mobile, data hay thường chạy nhiều máy ảo ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-003 — RAM Lenovo nâng cấp được không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo này lắp thêm RAM được không?”
- **Trả lời gợi ý:** “Dạ **có hỗ trợ nâng cấp RAM**. Cấu hình hiện tại là **16GB DDR5**. Mức dung lượng tối đa, loại thanh RAM tương thích và công lắp đặt cần kiểm tra đúng phiên bản trước khi tư vấn nâng cấp cụ thể ạ.”
- **Hỏi thêm:** “Anh/chị muốn giữ 16GB hay đang dự tính tăng RAM về sau?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-004 — SSD Lenovo có thể mở rộng không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo có 512GB thôi à, nâng SSD được chứ?”
- **Trả lời gợi ý:** “Máy đang có **SSD 512GB M.2 NVMe PCIe** và Catalog ghi **hỗ trợ nâng cấp lưu trữ**. Nếu anh/chị lưu nhiều video hoặc dự án, có thể hỏi thêm phương án tăng dung lượng; cần xác nhận loại SSD và cấu hình khe trước khi lắp.”
- **Hỏi thêm:** “Anh/chị đang muốn dùng 512GB trước hay cần nâng từ đầu ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-005 — Lenovo có GPU gì, chơi game được không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Con này có card rời không, chơi game được không?”
- **Trả lời gợi ý:** “Máy dùng **AMD Radeon 780M tích hợp**, không phải GPU rời trong cấu hình Catalog. Đây là dòng đồ họa tích hợp có thể cân nhắc cho giải trí và công việc hằng ngày. Để biết một trò chơi chạy được bao nhiêu FPS, cần tên game, độ phân giải, mức thiết lập và kết quả thử thực tế.”
- **Hỏi thêm:** “Anh/chị chơi game gì, và có yêu cầu FPS cụ thể không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-006 — Màn hình Lenovo bao nhiêu Hz, có OLED không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Màn Lenovo có OLED với 120Hz không?”
- **Trả lời gợi ý:** “Lenovo trong bộ demo có màn **14 inch, 1920 × 1200 (FHD+), 120Hz**. Catalog **chưa ghi nhận loại tấm nền** nên em chưa xác nhận đó là OLED. Nếu tiêu chí chắc chắn cần OLED 2.8K, mẫu ASUS có thông số rõ ràng hơn ở phần này.”
- **Hỏi thêm:** “Anh/chị ưu tiên tần số quét hay màu sắc và độ phân giải màn hình hơn ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`, `catalog:LAPTOP-ASUS-001`

### FAQ-LENOVO-007 — Pin Lenovo dùng được bao lâu?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo pin bao nhiêu, có trụ cả ngày học không?”
- **Trả lời gợi ý:** “Máy có pin **50Wh** theo Catalog. Dung lượng pin không đủ để suy ra chắc chắn số giờ dùng: còn phụ thuộc độ sáng màn hình, ứng dụng và tác vụ. Hiện bộ demo chưa có bài test thời lượng pin thực tế nên em chưa cam kết dùng được cả ngày ạ.”
- **Hỏi thêm:** “Anh/chị dùng chủ yếu học online, code hay chạy phần mềm nặng trên pin?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`

### FAQ-LENOVO-008 — Lenovo có USB-C sạc, HDMI và webcam không?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo có USB-C để sạc và HDMI để xuất màn hình không?”
- **Trả lời gợi ý:** “Có ạ. Theo Catalog, Lenovo có **2 USB-C hỗ trợ Power Delivery**, **2 USB-A 3.2 Gen 1**, HDMI, khe microSD và cổng tai nghe 3,5mm. Tư liệu tham khảo cũng nêu webcam **5MP**; đây là điểm đáng cân nhắc nếu anh/chị hay học hoặc họp trực tuyến.”
- **Hỏi thêm:** “Anh/chị có thường dùng màn hình rời hoặc webcam để họp online không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`; nguồn tham khảo Lenovo

### FAQ-LENOVO-009 — Lenovo được bảo hành bao lâu?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Lenovo này bảo hành mấy tháng, có 1 đổi 1 không?”
- **Trả lời gợi ý:** “Nguồn tham khảo **LaptopAZ** nêu **bảo hành 12 tháng** cho phiên bản này. Tuy nhiên, đây là **chính sách của nơi bán được tham khảo**, không tự động là cam kết của HOSTRA PoC. Điều kiện đổi trả/1 đổi 1 cần xác nhận với đơn vị bán hàng thực tế.”
- **Hỏi thêm:** “Anh/chị muốn em ghi nhận yêu cầu kiểm tra chính sách bảo hành trước khi quyết định không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`; nguồn tham khảo Lenovo

### FAQ-LENOVO-010 — Lenovo phù hợp với ai?
- **SKU:** `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Ai nên mua Lenovo Xiaoxin 14 này?”
- **Trả lời gợi ý:** “Lenovo phù hợp để **cân nhắc** cho người học tập, làm văn phòng hoặc lập trình muốn laptop **14 inch, 16GB DDR5, 120Hz** và đặc biệt **có khả năng nâng cấp RAM/SSD**. Nếu anh/chị đặt ưu tiên cao nhất vào màn OLED 2.8K và SSD sẵn 1TB, nên xem thêm mẫu ASUS.”
- **Hỏi thêm:** “Anh/chị muốn máy dùng ngay hay ưu tiên dễ nâng cấp về sau ạ?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`, `catalog:LAPTOP-ASUS-001`

---

## 3. FAQ — So sánh và tư vấn chọn giữa hai laptop

### FAQ-COMPARE-001 — Hai máy giá bao nhiêu, máy nào rẻ hơn?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “ASUS với Lenovo cái nào rẻ hơn?”
- **Trả lời gợi ý:** “Trong **bảng giá giả lập của HOSTRA**, ASUS là **26.500.000 đồng**, Lenovo là **25.690.000 đồng**; **Lenovo có giá thấp hơn**. Giá này chỉ phục vụ phiên demo, không phải báo giá hiện hành tại hai website.”
- **Hỏi thêm:** “Anh/chị đang ưu tiên ngân sách hay sẵn sàng trả thêm cho OLED và SSD lớn hơn ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-002 — Máy nào có màn hình đẹp hơn?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Màn hình ASUS hay Lenovo đẹp hơn?”
- **Trả lời gợi ý:** “Nếu đánh giá theo **thông số đã lưu**, ASUS nổi bật hơn về màn hình với **OLED 2880 × 1800**; Lenovo là **1920 × 1200**. Cả hai cùng **120Hz**. Nếu anh/chị ưu tiên độ phân giải cao và tương phản của OLED, em nghiêng về ASUS; trải nghiệm thực tế còn tùy sở thích mắt nhìn.”
- **Hỏi thêm:** “Anh/chị hay làm ảnh/video hay chủ yếu viết code và học tập?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-003 — Máy nào nâng cấp RAM tốt hơn?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Hai máy cái nào sau này thêm RAM được?”
- **Trả lời gợi ý:** “Cả hai đều có **16GB RAM** ban đầu, nhưng khác ở khả năng nâng cấp: **ASUS LPDDR5X onboard không nâng RAM**, còn **Lenovo DDR5 hỗ trợ nâng cấp**. Vì vậy, nếu anh/chị muốn linh hoạt tăng RAM về sau, Lenovo hợp tiêu chí hơn.”
- **Hỏi thêm:** “Anh/chị dự tính chạy nhiều tab, máy ảo, Docker hoặc project lớn không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-004 — Máy nào có nhiều dung lượng SSD hơn?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Máy nào ổ cứng to hơn, dễ lưu dữ liệu hơn?”
- **Trả lời gợi ý:** “**ASUS có SSD 1TB**, còn **Lenovo có SSD 512GB** khi xuất phát. Nếu anh/chị muốn nhiều dung lượng ngay mà chưa nâng cấp, ASUS đang lợi thế. Lenovo cũng được ghi nhận hỗ trợ nâng cấp SSD, nên có thể cân nhắc nếu muốn mở rộng sau.”
- **Hỏi thêm:** “Anh/chị cần lưu chủ yếu tài liệu, source code hay nhiều ảnh/video nặng ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-005 — Máy nào mạnh hơn để lập trình?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Em học CNTT nên mua ASUS hay Lenovo, máy nào code khỏe hơn?”
- **Trả lời gợi ý:** “Hai máy đều có **16GB RAM**, CPU dòng H và SSD NVMe nên đều đáng cân nhắc cho học lập trình. **ASUS có SSD 1TB và màn OLED 2.8K**; **Lenovo có khả năng nâng cấp RAM**, hữu ích khi nhu cầu chạy nhiều môi trường tăng lên. Chưa có benchmark cùng điều kiện nên em không kết luận máy nào chạy code nhanh hơn toàn diện.”
- **Hỏi thêm:** “Em học web/mobile cơ bản, hay dự định chạy nhiều máy ảo và Docker ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-006 — Máy nào mạnh hơn để chơi game hoặc đồ họa?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Intel Arc với Radeon 780M thì card nào mạnh hơn?”
- **Trả lời gợi ý:** “ASUS dùng **Intel Arc Graphics tích hợp**, Lenovo dùng **Radeon 780M tích hợp**. Cả hai không phải card rời trong cấu hình này. Không thể chốt GPU nào nhanh hơn ở mọi game hoặc phần mềm chỉ từ tên chip; cần benchmark cho đúng tác vụ. Nếu anh/chị render 3D hoặc cần CUDA, nên cân nhắc dòng laptop GPU rời phù hợp hơn.”
- **Hỏi thêm:** “Anh/chị định chơi game nào, chỉnh ảnh hay làm 3D/AI?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-007 — Máy nào pin lâu hơn?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Pin ASUS 75Wh, Lenovo 50Wh, vậy ASUS dùng lâu hơn đúng không?”
- **Trả lời gợi ý:** “**ASUS có dung lượng pin 75Wh**, Lenovo **50Wh**. Đây là lợi thế về **dung lượng pin danh định** cho ASUS, nhưng thời gian dùng thực tế còn phụ thuộc CPU, màn hình, độ sáng và tác vụ. Em không khẳng định ASUS chắc chắn dùng lâu hơn bao nhiêu giờ nếu chưa có bài đo cùng điều kiện ạ.”
- **Hỏi thêm:** “Anh/chị thường làm việc xa ổ cắm bao lâu và dùng ứng dụng gì?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-008 — Máy nào phù hợp thiết kế, xem phim?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Mình xem phim, chỉnh ảnh và làm content, nên chọn máy nào?”
- **Trả lời gợi ý:** “Nếu trải nghiệm hiển thị là ưu tiên lớn, **ASUS đáng cân nhắc hơn** nhờ **OLED 2.8K 120Hz** và SSD **1TB**. Lenovo cũng có màn **120Hz**, đồng thời có khả năng nâng cấp RAM/SSD, nhưng độ phân giải hiện tại thấp hơn ASUS. Với công việc đồ họa chuyên sâu, nên xem yêu cầu phần mềm cụ thể trước khi quyết định.”
- **Hỏi thêm:** “Anh/chị thường dùng Canva/Figma, Photoshop hay Premiere ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-009 — Ngân sách khoảng 26 triệu nên chọn máy nào?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Em có khoảng 26 triệu, mua con nào?”
- **Trả lời gợi ý:** “Theo **giá demo**, Lenovo là **25.690.000 đồng**, nằm trong mức 26 triệu; ASUS là **26.500.000 đồng**, cao hơn mức đó. Nếu ngân sách là giới hạn cứng, Lenovo phù hợp hơn về giá. Nếu có thể tăng ngân sách, ASUS đáng xem nếu thích OLED 2.8K và SSD 1TB.”
- **Hỏi thêm:** “26 triệu là ngân sách tối đa, hay anh/chị có thể linh động thêm ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-COMPARE-010 — Khách hỏi “máy kia” là máy nào?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Thế con kia có nâng RAM được không?”
- **Trả lời gợi ý:** “Dạ, cho em hỏi anh/chị đang nói tới **ASUS Vivobook S 14 OLED** hay **Lenovo Xiaoxin 14** ạ? Em xác nhận đúng mẫu rồi tư vấn để tránh nhầm thông tin.”
- **Hỏi thêm:** “Anh/chị muốn hỏi mẫu ASUS hay Lenovo ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`; cần Conversation Memory nếu muốn tự phân giải ngữ cảnh

### FAQ-COMPARE-011 — Có thể vừa nâng RAM vừa có OLED 2.8K không?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Có máy nào trong hai con vừa OLED đẹp, vừa nâng được RAM không?”
- **Trả lời gợi ý:** “Với **hai cấu hình trong bộ demo**, chưa có mẫu nào được xác nhận đáp ứng **đồng thời cả hai tiêu chí**. ASUS có **OLED 2.8K** nhưng không nâng RAM; Lenovo nâng RAM được nhưng **Catalog chưa xác nhận tấm nền OLED**, và màn đang là FHD+. Nếu cả hai điều kiện bắt buộc, em không ép anh/chị chọn một trong hai ạ.”
- **Hỏi thêm:** “Trong hai nhu cầu đó, điều nào là bắt buộc và điều nào có thể linh động ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

---

## 4. FAQ — Xử lý băn khoăn và chốt nhu cầu an toàn

### FAQ-SALES-001 — Giá cao quá, có giảm thêm không?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Giảm thêm được không? Có mã ưu đãi không?”
- **Trả lời gợi ý:** “Em hiểu mình đang cân đối ngân sách. Hiện em chỉ có **giá cố định trong demo** là ASUS **26.500.000 đồng** và Lenovo **25.690.000 đồng**; **chưa có dữ liệu khuyến mãi được xác nhận**. Em có thể giúp anh/chị chọn máy phù hợp nhất với số tiền dự kiến, còn ưu đãi thực tế cần kiểm tra riêng.”
- **Hỏi thêm:** “Ngân sách tối đa anh/chị muốn giữ là bao nhiêu ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-SALES-002 — Có trả góp, freeship, tặng quà không?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Shop có trả góp 0%, freeship và tặng chuột không?”
- **Trả lời gợi ý:** “Trong dữ liệu bán hàng **HOSTRA PoC hiện chưa thiết lập chính sách** trả góp, vận chuyển hoặc quà tặng. Một số website tham khảo có chương trình riêng, nhưng em không thể mặc định áp dụng cho phiên demo này. Nếu cần, em sẽ ghi nhận để xác minh chính sách thực tế.”
- **Hỏi thêm:** “Anh/chị ưu tiên trả góp hay chi phí giao hàng ạ?”
- **Bằng chứng:** Catalog hai SKU; chính sách cửa hàng PoC chưa có

### FAQ-SALES-003 — Có thể đặt đơn luôn không?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Chốt con Lenovo, lên đơn cho mình nhé?”
- **Trả lời gợi ý:** “Em ghi nhận anh/chị đang chọn **Lenovo Xiaoxin 14**. Hiện đây là **bản demo tư vấn**, chưa có chức năng đặt đơn hoặc thanh toán thật. Nếu triển khai bán hàng thật, đơn hàng sẽ cần được xác nhận giá, hàng, bảo hành và thông tin giao nhận trước khi hoàn tất ạ.”
- **Hỏi thêm:** “Anh/chị muốn em tóm tắt lại các tiêu chí đã chọn để chuyển người phụ trách xác nhận không?”
- **Bằng chứng:** `catalog:LAPTOP-LENOVO-002`; trạng thái PoC

### FAQ-SALES-004 — ASUS có bảo hành hai năm không?
- **SKU:** `LAPTOP-ASUS-001`
- **Câu hỏi:** “ASUS bảo hành 24 tháng chính hãng phải không?”
- **Trả lời gợi ý:** “Em có thấy thông tin bảo hành trên một số nơi bán tham khảo, nhưng **Catalog HOSTRA hiện chưa chốt chính sách bảo hành cho ASUS**. Vì chính sách có thể phụ thuộc mã hàng và đơn vị bán, em xin không cam kết số tháng hoặc điều kiện bảo hành cho phiên demo khi chưa kiểm tra ạ.”
- **Hỏi thêm:** “Anh/chị muốn ưu tiên máy có thời gian bảo hành tối thiểu bao nhiêu tháng?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`

### FAQ-SALES-005 — Giá ở website khác với trong livestream?
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Sao web khác giá, shop báo giá kỳ vậy?”
- **Trả lời gợi ý:** “Cảm ơn anh/chị đã kiểm tra. Giá em vừa nêu là **giá được cấu hình cho phiên demo HOSTRA**, không phải giá cập nhật trực tiếp từ trang bán hàng. Trong hoạt động bán hàng thật, em phải tra cứu báo giá tại thời điểm đặt hàng trước khi xác nhận.”
- **Hỏi thêm:** “Anh/chị muốn so sánh cấu hình hai máy trước để xem mẫu nào đáng cân nhắc hơn không ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-SALES-006 — Khách đòi cam kết FPS, nhiệt độ và pin thực tế
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Cam kết Valorant 200 FPS, máy không nóng và pin 12 tiếng được không?”
- **Trả lời gợi ý:** “Em không thể cam kết các chỉ số đó khi chưa có **bài thử đúng game, mức đồ họa, điều kiện sử dụng và phiên bản máy**. Em có thể cung cấp cấu hình xác thực và cùng anh/chị xác định yêu cầu tối thiểu, rồi đề xuất kiểm tra benchmark trước khi mua.”
- **Hỏi thêm:** “Anh/chị cần ưu tiên FPS game, nhiệt độ hay thời gian dùng pin nhất?”
- **Bằng chứng:** Catalog hai SKU; **không có benchmark**

### FAQ-SALES-007 — Khách muốn mua cho sinh viên, cần tư vấn nhanh
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Mình mua laptop cho em học đại học, tư vấn nhanh với.”
- **Trả lời gợi ý:** “Dạ, em gợi ý theo nhu cầu: nếu ưu tiên **màn hình OLED 2.8K, SSD 1TB sẵn có**, hãy xem ASUS; nếu muốn **linh hoạt nâng RAM/SSD**, hãy xem Lenovo. Hai máy đều 14 inch và có 16GB RAM. Để chọn đúng mà không mua thừa, em cần biết ngành học và ngân sách của em ạ.”
- **Hỏi thêm:** “Em học ngành gì và mức ngân sách tối đa là bao nhiêu ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

### FAQ-SALES-008 — Khách yêu cầu tóm tắt để quyết định
- **SKU:** `LAPTOP-ASUS-001`, `LAPTOP-LENOVO-002`
- **Câu hỏi:** “Nói gọn giúp mình, nên chốt ASUS hay Lenovo?”
- **Trả lời gợi ý:** “**ASUS:** giá demo **26,5 triệu**, ưu tiên **OLED 2.8K và SSD 1TB**, đổi lại RAM không nâng cấp. **Lenovo:** giá demo **25,69 triệu**, màn **FHD+ 120Hz**, SSD **512GB**, có đường nâng cấp RAM/SSD. Em khuyên chọn theo tiêu chí quan trọng nhất của anh/chị, không có một máy thắng mọi mặt.”
- **Hỏi thêm:** “Nếu chỉ chọn một: màn đẹp và bộ nhớ lớn sẵn có, hay khả năng nâng cấp về sau ạ?”
- **Bằng chứng:** `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002`

---

## 5. Kịch bản fallback khi không đủ bằng chứng

- **Thiếu giá, tồn kho, ưu đãi:** “Em chưa có dữ liệu đã xác minh cho thông tin này. Em xin kiểm tra trước khi báo chính xác ạ.”
- **Hỏi mơ hồ giữa hai máy:** “Anh/chị đang hỏi ASUS Vivobook S 14 OLED hay Lenovo Xiaoxin 14 ạ?”
- **Đòi benchmark cụ thể:** “Em chưa có kết quả đo trong cùng điều kiện để khẳng định. Anh/chị cho em tên phần mềm hoặc game để xác định bài test phù hợp nhé.”
- **Hỏi thông tin nhạy cảm/không liên quan hoặc yêu cầu vượt phạm vi:** “Em xin phép chỉ hỗ trợ tư vấn hai mẫu laptop dựa trên thông tin có thể kiểm chứng. Nếu cần vấn đề khác, em sẽ chuyển yêu cầu cho người phụ trách.”
- **Không suy diễn từ FAQ:** Nếu câu trả lời bị chặn ở Agent, **không chuyển chính câu trả lời chưa kiểm chứng sang TTS**. Chỉ phát `safe_fallback` từ script đã được duyệt theo Data Contract.

## 6. Ghi chú kỹ thuật để tích hợp Part 1 — Agent + RAG

1. Mỗi mục FAQ có mã ổn định `FAQ-ASUS-*`, `FAQ-LENOVO-*`, `FAQ-COMPARE-*`, `FAQ-SALES-*`. Khi index RAG, lưu ID và SKU liên quan trong metadata; mỗi mục có thể là một chunk.
2. Với câu hỏi **giá/tồn kho/thông số chính xác**, nên tra cứu trực tiếp `catalog_skus.json` trước; dùng FAQ để diễn đạt. Không dựa duy nhất vào embedding để quyết định số tiền hoặc tồn kho.
3. `AgentResponse.evidence_refs` có thể tham chiếu `catalog:LAPTOP-ASUS-001`, `catalog:LAPTOP-LENOVO-002` và/hoặc `faq:FAQ-COMPARE-003` theo quy ước retrieval của nhóm. **Không coi ID nguồn tồn tại là chứng minh nội dung đã đúng**: cần kiểm tra bằng chứng hỗ trợ mệnh đề nào.
4. Với câu **so sánh hai SKU**, lấy đủ cả hai nguồn. Trường `resolved_sku_id` hiện chỉ là một SKU hoặc `null`; nhóm Part 1 cần thống nhất cách biểu diễn câu trả lời nhiều SKU trong service, không tự ý thay schema ngay.
5. Phần `Hỏi thêm` là gợi ý chốt nhu cầu, **không bắt buộc đọc nguyên văn** trong mọi câu trả lời. Tránh lời thoại dài và lặp đi lặp lại.
6. Không sử dụng bảng FAQ làm bằng chứng cho **đơn hàng đã được tạo**, **video đã render** hoặc **giấy phép đã được xác minh**.

**Tiêu chí review:** Không mâu thuẫn Catalog; không tự bịa giá/tồn kho/chính sách; câu hỏi so sánh trích được hai SKU; các trường hợp thiếu bằng chứng trả lời an toàn; lời thoại đủ tự nhiên để chuyển sang SpeechTurn/TTS.


## 7. Liên kết dữ liệu Mock Comments — Phiên RUN-001

- Tệp bình luận: `shared_data/inputs/mock_comments.json`.
- `run_id`: `RUN-001`; mốc bắt đầu timeline phải khớp `2026-10-27T13:00:00Z` trong cấu hình demo/RunManifest khi tạo.
- `active_sku_id` cố định: `LAPTOP-ASUS-001` (sản phẩm chính của phiên); câu hỏi vẫn được phép nhắc và so sánh Lenovo qua Catalog và FAQ.
- File mock comments là **danh sách `CommentEvent` đầu vào**, không phải câu trả lời có sẵn. `CommentDecision` và `AgentResponse` là đầu ra do Part 1 thực sự xử lý.
- FAQ cung cấp **nội dung tham khảo để retrieval và xác minh**. Không phát lời thoại gợi ý nguyên văn nếu thiếu bằng chứng hoặc chưa qua logic duyệt lời thoại.
- Giá và tồn kho là **dữ liệu mô phỏng**, không phải lời đề nghị giao dịch với cửa hàng ngoài đời.
