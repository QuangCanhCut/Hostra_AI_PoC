# M02.1 — Chuẩn bị tri thức cho Hybrid Knowledge Engine

M02.1 đọc nguồn local và tạo các đơn vị tri thức có thể truy vết; M02.2 bổ sung tìm kiếm lexical BM25. Chưa có embeddings, tìm kiếm vector, hybrid retrieval, LLM hay xác minh câu trả lời tự động. Hybrid Knowledge Engine là hướng thiết kế kết hợp tra cứu Catalog với nhiều phương pháp truy xuất FAQ trong các milestone sau.

## Nguồn dữ liệu và luồng chuẩn bị

```text
catalog_skus.json → CatalogRepository → tra SKU / CatalogEvidence
product_faq.md ──→ FAQ parser ──→ FAQRecord ──→ chunking ──→ FAQChunk
                         ↑                                  ↓
                   kiểm tra SKU                       KnowledgeEngine
```

Catalog là nguồn ưu tiên để **đối chiếu** giá, tồn kho và thông số. Repository trả giá trị nguyên gốc: ví dụ `specifications.storage.upgradable` của ASUS là `None`, không phải `False`. `CatalogEvidence` mang SKU, field path, giá trị, `data_type` và `catalog:<SKU>`. Giá và tồn kho hiện là dữ liệu **mock**, không phải thông tin bán hàng thực tế. Repo trả bản sao để bên gọi không sửa snapshot hay file nguồn.

FAQ là lời tư vấn tham khảo do nhóm biên soạn. `FAQRecord` giữ ID, tiêu đề, SKU, câu hỏi, trả lời gợi ý, hỏi thêm, nguồn và bằng chứng gốc. Parser chỉ nhận heading `### FAQ-... — ...`, kiểm tra các trường bắt buộc, ID trùng, SKU và catalog ref. Các phần fallback, quy tắc và timeline ngoài FAQ không thành chunk.

## Chunk và bằng chứng

Structure-aware chunking tạo **một FAQChunk cho một FAQRecord**. `chunk_id` ổn định theo FAQ ID; `source_ref` là `faq:<FAQ-ID>`. `retrieval_text` gồm tiêu đề, câu hỏi và nguyên văn Markdown của trả lời gợi ý. Metadata lưu FAQ ID, SKU, source file, các catalog ref tường minh, evidence notes và cờ `needs_review`. Câu hỏi và trả lời không bị cắt rời hay overlap. Ref tường minh chỉ cho biết nguồn tồn tại, chưa xác minh claim.

Trong facade, file FAQ nằm trong repository được biểu diễn bằng đường dẫn tương đối theo root với dấu `/`, ví dụ `shared_data/inputs/product_faq.md`, ổn định giữa Windows, Linux và CI. Với file ngoài repository, bên gọi nên truyền `source_id` logic duy nhất và ổn định vào `load_knowledge(..., source_id="knowledge/product_faq.md")`; nếu không truyền, đường dẫn đầu vào được giữ nguyên và có thể khác giữa các máy. `source_ref` nhận diện FAQ, còn `source_file` nhận diện tài liệu nguồn; khi lưu index cần quy định namespace/phiên bản nguồn để tránh trùng giữa nhiều tài liệu.

Một dòng `---` trong field được giữ là Markdown. Riêng dấu phân cách sau một dòng trống ở cuối field Bằng chứng trước heading tiếp theo được xem là dấu phân cách giữa các mục trong định dạng FAQ hiện tại; cú pháp tại vị trí đó có thể mơ hồ và cần quy ước nếu nguồn thay đổi.

`evidence_raw` giữ nguyên giá trị bằng chứng trong FAQ; `evidence_refs` chỉ chứa `catalog:<SKU>` xuất hiện tường minh và tồn tại trong Catalog. Nội dung còn lại được lưu trong `evidence_notes`, đánh dấu `needs_review`; nếu không có ref tường minh cũng cần review. Parser không tự suy ra ref từ cụm như “Catalog hai SKU” và không xem ref hợp lệ là bằng chứng đã hỗ trợ mọi claim trong câu trả lời.

Dữ liệu hiện tại có 6 mục cần nhóm review: FAQ-LENOVO-008/009 có “nguồn tham khảo Lenovo”; FAQ-COMPARE-010 có ghi chú về Conversation Memory; FAQ-SALES-002 và FAQ-SALES-006 nhắc “Catalog hai SKU” cùng chính sách/benchmark chưa có; FAQ-SALES-003 ghi trạng thái PoC. Các ghi chú này được giữ lại, không tự biến thành nguồn Catalog đã xác minh.

## Indexing và query

**Indexing pipeline** chuẩn bị nguồn, kiểm tra, chia chunk và tạo thống kê BM25 trong bộ nhớ; chưa ghi index ra file. **Query pipeline** M02.2 nhận câu hỏi và trả các FAQ có từ khóa khớp, kèm metadata nguồn. Bước xác minh chưa được triển khai; không nhầm chunk truy xuất được với câu trả lời đã được xác minh.

`KnowledgeEngine.search_faq(query, top_k=5, sku_ids=None)` dùng BM25 Okapi với `k1=1.5`, `b=0.75` và IDF `log(1 + (N - df + 0.5)/(df + 0.5))`. Tính độ dài, tần suất và IDF trên toàn bộ corpus, kể cả khi lọc SKU. Mỗi token query chỉ tính một lần; chỉ trả điểm dương, điểm bằng nhau sắp theo chunk ID. Không cần thư viện ngoài vì corpus hiện nhỏ. `sku_ids` nếu truyền phải là tuple không rỗng; FAQ phải chứa **tất cả** SKU yêu cầu. Không có lọc Active SKU tự động.

Tokenizer chuẩn hóa Unicode NFC, casefold, tách chuỗi chữ/số bằng regex Unicode; giữ dấu, `không` và các token RAM/SSD/CPU. Query rỗng hoặc chỉ dấu câu trả danh sách rỗng; `top_k` phải là số nguyên dương. Đây là tách theo chữ/số, không phân đoạn từ ghép tiếng Việt, không xử lý từ đồng nghĩa hay ngữ nghĩa; tên kỹ thuật có dấu câu bị tách, ví dụ `2.8K`. Điểm BM25 là điểm liên quan, không phải xác suất hay độ tin cậy.

Bộ [lexical_eval.json](../tests/fixtures/rag/lexical_eval.json) có 12 câu, mỗi câu có một FAQ kỳ vọng do người viết gán nhãn. `--eval` tính macro Recall@K: trung bình tỉ lệ FAQ được gán liên quan xuất hiện trong top K cho mỗi câu. Bộ nhỏ này chỉ là baseline, chưa đầy đủ và chưa có đánh giá độc lập; nhiều FAQ khác cũng có thể phù hợp. Cần mở rộng bộ câu hỏi và rà soát nhãn trước khi dùng làm tiêu chí chất lượng. Kết quả tìm kiếm giữ `source_ref`, `sku_ids`, `evidence_refs`, `evidence_notes` và `needs_review`; không tự suy ra nguồn hay bỏ qua mục cần review.

## Chạy thử

```powershell
python scripts/script_rag/prepare_knowledge.py
python scripts/script_rag/search_faq.py "ASUS nâng RAM được không?" --top-k 5
python scripts/script_rag/search_faq.py --eval
python -m pytest tests/unit/test_part1_code -v
python -m pytest tests/contract/test_part1_contract.py -v
python -m pytest -q
```

Không cần `.env`, API key hay mạng. Xem [hướng dẫn Milestone 01](milestone01_comment_processing.md) nếu pytest báo lỗi quyền với thư mục tạm Windows. Parser hiện hỗ trợ định dạng Markdown cụ thể của nguồn; nếu thay đổi quy ước heading hoặc nhãn field, cần cập nhật parser và kiểm thử trước khi nạp dữ liệu mới.
