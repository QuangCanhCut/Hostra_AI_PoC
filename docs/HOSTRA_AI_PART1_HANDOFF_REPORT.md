# HOSTRA AI PoC — BÁO CÁO HOÀN THÀNH VÀ BÀN GIAO PART 1

**Verified AI Agent · Comment Processing · Knowledge/RAG · Speech Planner · Text-to-Speech · Integration/Evaluation**

| Thuộc tính | Giá trị |
|---|---|
| Dự án | HOSTRA AI PoC — Hybrid AI Live Commerce |
| Phạm vi | Part 1, Milestone M01–M05 và đợt cải thiện Sales Persona sau M05 |
| Thời điểm tổng hợp | 29/10/2026 |
| Nhánh phát triển | `feature/part1-agent-tts` |
| Nhóm đọc chính | Kỹ sư tiếp quản Part 1, nhóm Part 2 Lip-sync, Orchestration, kiểm thử |
| Mức nghiệm thu | **Đã có pipeline offline tích hợp và tạo artifacts; bàn giao có điều kiện cho Part 2.** Real TTS đã được người triển khai chạy thử một số WAV, nhưng chưa có báo cáo nghiệm thu chính thức đầy đủ cho provider, độ tự nhiên và lip-sync. |
| Nguồn xác nhận | Tài liệu thiết kế V2.1; báo cáo M03/M04/M05 do Codex và người triển khai cung cấp; mã nguồn nhánh GitHub hiện truy cập được; `run_part1.py` và các script preview người dùng cung cấp. |

> **QUAN TRỌNG — phạm vi chứng cứ.** Bản GitHub `feature/part1-agent-tts` được đối chiếu tại thời điểm viết vẫn có `src/hostra_ai/part1_agent_tts/pipeline.py` **rỗng** và chưa có các script M05/Sales Persona mới trong `scripts/script_part1/`. Trong khi đó, ảnh VS Code và báo cáo của người triển khai cho thấy các file này đã có trên máy local và được chạy. Vì thế tài liệu này phân biệt **[CODE]** (đã đọc code), **[REPORT]** (theo báo cáo Codex), **[USER TEST]** (người triển khai đã thử), và **[LOCAL — CẦN ĐỐI CHIẾU]** (chưa có source local mới nhất). Trước khi coi đây là tài liệu bàn giao chính thức trên GitHub, hãy commit/push M05, Sales Persona, các scripts và docs đang còn untracked, rồi rà lại các đường dẫn.

---

## 1. TÓM TẮT CHO NGƯỜI TIẾP QUẢN

Part 1 đã xây dựng nền tảng xử lý bình luận livestream giả lập, lọc các bình luận đáng trả lời, lấy dữ kiện từ Catalog/FAQ theo SKU, sinh và xác minh câu trả lời, lập lượt nói, chuyển sang WAV và xuất dữ liệu phục vụ render/lip-sync. M05 nối các thành phần M01–M04 thành một pipeline chạy offline từ một entry point. Nguyên tắc trọng tâm: **không đưa candidate answer chưa verified hoặc script chưa approved vào TTS**.

**Năng lực đạt được:**

- **M01:** đọc và validate mock comments; triage spam/trùng/ngoài phạm vi; priority, fairness, deferred và queue service. [CODE]
- **M02:** Catalog có cấu trúc, FAQ parser/chunking; BM25 lexical; semantic embeddings + vector index có thể bật tường minh; hybrid Reciprocal Rank Fusion; `EvidencePackage`. [CODE]
- **M03:** `ConversationMemory`, phân giải intent/SKU, lấy evidence, deterministic candidate generation, `AnswerVerifier`, `AgentResponse` theo `answered`/`clarification_needed`/`blocked`. Mức độ hỗ trợ free-form LLM vẫn hạn chế. [CODE, REPORT]
- **M04:** `SpeechPlanner`, approval gate, `SpeechAdmission`, Mock/OpenAI TTS adapters, `TTSService`, PCM WAV validation và `AudioArtifact`. [CODE, REPORT]
- **M05:** `Part1Pipeline.run(run_id)` nối toàn bộ quy trình, trusted in-process handoff M03→M04, tránh tổng hợp lặp theo logical response, run isolation, ghi JSON/WAV, thống kê và đánh giá 20 comments. [REPORT, USER TEST]
- **Sales Persona enhancement:** đã có thay đổi local đối với `verified_agent.py`, `answer_verifier.py`, `configs/sales_persona.yaml`, tests và script so sánh trước/sau; cần đối chiếu mã local mới nhất và chốt chất lượng thực tế. [LOCAL — CẦN ĐỐI CHIẾU]

**Chưa được khẳng định hoàn tất:** LLM sinh lời thoại tự do và xác minh claim tổng quát; phê duyệt 15 script vận hành; resampling có anti-aliasing; worker Part 2; video lip-sync; scheduler timestamp cuối; `hostra_demo.mp4`; cơ chế chạy nhiều tiến trình/phục hồi run.

## 2. KIẾN TRÚC HỆ THỐNG VÀ RANH GIỚI PART 1

```text
INPUTS: catalog_skus.json · product_faq.md · mock_comments.json
        comment_policy.yaml · rag.yaml · app.yaml · approved_product_scripts.json
                                      │
                                      ▼
 M01  CommentEvent → CommentTriage → CommentQueue (selected/deferred/skipped)
                                      │ QueueItem
                                      ▼
 M02  CatalogRepository + FAQ → BM25 / Semantic / Hybrid → EvidencePackage
                                      │ evidence
                                      ▼
 M03  ConversationMemory → Intent/SKU → Candidate Generation
                             → AnswerVerifier → AgentResponse
                                      │ trusted handoff
                                      ▼
 M04  SpeechPlanner / Approved Script → SpeechTurn → SpeechAdmission
                                      │ accepted turn
                                      ▼
      MockTTSProvider / OpenAITTSProvider → TTSService
                                      │
                                      ▼
      WAV PCM 16-bit mono 16 kHz + AudioArtifact
                                      │
                                      ▼
 M05  Part1Pipeline / run writer / evaluation.json
                                      │
                     BÀN GIAO Part 2 + Orchestration
```

**Ranh giới cần nhớ:** Part 1 quyết định **nội dung nào được phép phát và tạo âm thanh**. Admission quyết định **có tổng hợp lượt lời không**, nhưng không bố trí audio trên timeline cuối. Orchestration/Final Scheduler dùng `duration_ms` từ WAV để chọn thời điểm; Part 2 xử lý lip-sync; Part 3 ghép video liên tục và xuất MP4. Không coi một bản MP4 đã render sẵn là livestream tương tác realtime.

### 2.1. Năm public contracts quan trọng với Part 1

| Contract | Vai trò và kiểm tra bắt buộc |
|---|---|
| `CommentEvent` | Bình luận gốc: `comment_id`, `run_id`, `viewer_id`, text, active SKU, source, received timestamp có timezone. |
| `CommentDecision` | Hành động triage/queue, score, reason, version policy; một comment có thể trải qua nhiều quyết định. |
| `AgentResponse` | `answered` (text + evidence), `clarification_needed` (text hỏi lại), `blocked` (không có text phát). **Schema hợp lệ không chứng minh provenance từ M03.** |
| `SpeechTurn` | `comment_reply`, `product_intro`, `safe_fallback`; giữ `response_id` hoặc `script_ref` theo loại, text đúng nguồn. |
| `AudioArtifact` | Liên kết `audio_id`, `speech_turn_id`, `response_id`, `run_id`, `voice_id`, relative WAV path, codec/sample rate/channels/duration thực. |

Schema tập trung tại `src/hostra_ai/core/schemas/part1.py`; **10 public Data Contracts của ba Part không được thay đổi tùy tiện**. Các schema `part2.py`, `part3.py` mô tả hợp đồng các bước downstream, **không phải bằng chứng runtime các phần đó đã triển khai**.

### 2.2. Dữ liệu mock đang sử dụng

| Dữ liệu | Trạng thái và lưu ý |
|---|---|
| Hai SKU laptop | `LAPTOP-ASUS-001` (ASUS Vivobook S 14 OLED), `LAPTOP-LENOVO-002` (Lenovo IdeaPad Slim 5 Xiaoxin 14). |
| Giá mock | ASUS 26.500.000 VND, Lenovo 25.690.000 VND, chênh lệch 810.000 VND. **Không phải giá thương mại đang bán**. |
| FAQ | Bộ FAQ thiết kế gồm 39 mục, gắn bằng chứng và cờ `needs_review` theo nội dung. |
| Comments | 20 bình luận mock `CMT-001`–`CMT-020`, nhiều viewer, gồm hỏi giá, RAM, màn hình, Docker, so sánh, chính sách và spam. |
| Product scripts | 15 script trong `approved_product_scripts.json`, trạng thái tập hợp `pending_team_review`; từng script `pending_review` theo audit M04. **Không dùng làm product intro/fallback vận hành khi chưa phê duyệt thật.** |

---

## 3. CÁC MILESTONE ĐÃ THỰC HIỆN

### 3.1. M01 — Comment Ingestion, Triage & Queue

**Mục tiêu:** chỉ chuyển những bình luận đáng xử lý sang AI Agent, giữ công bằng tối thiểu khi có nhiều người hỏi và bảo lưu lịch sử quyết định. [CODE]

**Đã triển khai:** `ingest_comments()` validate JSON, ID và active SKU; policy YAML; score theo nhóm từ khóa; normalize văn bản để phát hiện trùng; spam/off-topic filtering; queue có trạng thái ready/deferred, TTL, giới hạn kích thước, fairness theo viewer và FIFO. `run_milestone01.py` mô phỏng service mỗi 12 giây, in action cuối của mỗi bình luận. M01 không tự gọi LLM hoặc TTS.

**Giới hạn:** Triage bằng rules/keywords, không phải moderation/intent classifier tổng quát; queue in-memory, không phải broker phân tán.

### 3.2. M02 — Knowledge Engine & Retrieval

**Mục tiêu:** tạo dữ kiện có nguồn, đúng SKU và có khả năng truy xuất trước khi Agent phát ngôn. [CODE]

**Đã triển khai:** Catalog đọc JSON có cấu trúc; FAQ parser giữ refs và review flags; one-FAQ-one-chunk; BM25 lexical offline; vector index exact cosine lưu JSON cùng fingerprint/manifest; OpenAI embedding adapter cần opt-in; semantic/hybrid retrieval và RRF; routing/grounding qua KnowledgeEngine. `EvidencePackage` ghi lại candidate hits và tình trạng nguồn.

**Giới hạn:** raw FAQ hit hoặc package `status=ok` **chưa phải câu trả lời verified**; retrieval OOD có các ca false-accept được ghi nhận trong đánh giá trước; embedding API có chi phí khi `--allow-api`; benchmark semantic/hybrid không thể đại diện latency hệ thống thực.

### 3.3. M03 — Verified AI Sales Agent

**Mục tiêu:** tạo câu trả lời bán hàng dựa trên evidence, giữ ngữ cảnh viewer và ngăn thông tin thương mại không có nguồn. [CODE, REPORT]

**Đã triển khai:** memory theo `(run_id, viewer_id)` giới hạn lịch sử mặc định; phân giải follow-up, intent và SKU; lấy Catalog/FAQ; deterministic generator; independent verifier cho các mẫu câu/fact được hỗ trợ; output `AgentResponse` phân biệt answered/clarification/blocked. Các tình huống đã báo cáo gồm hỏi giá, RAM/SSD, Docker, chỉnh ảnh, giá demo khác website, so sánh chênh lệch 810.000 VND.

**Nghiệm thu báo cáo M03:** 391 tests passed và 65 subtests passed sau bản hardening (theo Codex, không chạy lại độc lập trong lần biên soạn này).

**Giới hạn:** verifier nhận biết tập câu văn và claim giới hạn, chưa chứng minh xác minh tùy ý mọi câu LLM tiếng Việt; mặc định bản mã GitHub tham chiếu sử dụng `DeterministicProvider`, không mặc định gọi Chat Completion API. Đợt nâng cấp Sales Persona đã thay đổi bản local sau M05, cần rà code lại để ghi nhận chính xác phạm vi thay đổi.

### 3.4. M04 — Speech Planner & TTS

**Mục tiêu:** biến nội dung hợp lệ thành lượt nói và WAV có metadata kiểm chứng được. [CODE, REPORT]

**Đã triển khai:** `SpeechPlanner.from_response` giữ nguyên text answered/clarification; blocked chỉ dùng fallback được approved; `product_intro` yêu cầu active SKU khớp; callback kiểm tra `use_when`/evidence; `SpeechAdmission` nhận turn do planner phát hành, ưu tiên safe_fallback→reply→intro, một lần consume; `TTSService` tạo/kiểm tra WAV và `AudioArtifact`; mock/provider API tách biệt.

**Âm thanh kỹ thuật:** output mặc định WAV PCM signed 16-bit mono 16.000 Hz; duration tính từ frames; input chuyển đổi giới hạn WAV PCM 16-bit mono/stereo, resample tuyến tính. Mock WAV **là khoảng lặng**, không phải giọng nói.

**Nghiệm thu báo cáo M04:** 402 passed / 0 failed / 0 skipped; 65 subtests passed; 11 test riêng M04 (7 unit, 4 integration). **CONDITIONAL GO** offline; không đồng nghĩa live TTS verified.

**Giới hạn:** planner tự nó không chứng minh source AgentResponse; cùng response có thể thành hai turn ID; approval scripts còn pending; linear resampling chưa anti-aliasing; OpenAI TTS chưa live trong báo cáo audit M04.

### 3.5. M05 — Part 1 Offline Integration & Evaluation

**Mục tiêu:** chạy M01–M04 end-to-end bằng một runner, ghi artifacts cho mỗi run, đánh giá tính đúng đắn và có khả năng bàn giao. [REPORT, USER TEST]

**Đã được báo cáo triển khai local:** `Part1Pipeline.run(run_id)` tạo một phiên với state mới, thực hiện ingest→triage→queue→agent→planner→admission→mock TTS; không mở external API nhận một `AgentResponse` tùy ý; đối chiếu run/comment/viewer và tồn tại refs ở ranh giới M03→M04; dedup logical key `(run_id, response_id, speech_type)`; ghi JSON, WAV và evaluation. Nếu run folder đã tồn tại thì từ chối; không có resume sau restart.

**CLI offline:** `scripts/script_part1/run_part1.py` (sau khi chuyển thư mục theo ảnh VS Code) cho phép chọn comments, config, output root, `service-interval-seconds`; TTS mode `mock` duy nhất. `0` mô phỏng xử lý tức thời theo sự kiện; `12` giây mô phỏng một lượt queue service mỗi 12 giây, **không phải TTS latency**.

**Kết quả người dùng chia sẻ:** Codex/ảnh màn hình báo cáo một run khoảng **17 bình luận được chọn, 3 bỏ qua, 11 answered, 6 blocked**; toàn bộ suite **423 tests** sau đợt cải thiện Sales Persona. Đây là **số liệu báo cáo/ảnh** không phải phép đo lặp lại từ environment người nhận tài liệu. Cần đối chiếu `evaluation.json` theo run ID cụ thể để chốt.

**Giới hạn:** output ghi file riêng lẻ, chưa transactional toàn phiên; `status=partial` có lỗi theo comment, CLI exit 2; lỗi nghiêm trọng exit 1 có thể để run dở dang; thống kê intent/SKU golden chưa tự động đầy đủ; memory/dedup state in-memory.

### 3.6. Bổ sung sau M05 — Natural Vietnamese Sales Presenter

**Mục tiêu:** tăng tính tự nhiên của lời thoại thay vì chỉ đọc facts ngắn. [LOCAL — CẦN ĐỐI CHIẾU]

Theo ảnh Codex, bản local cập nhật `configs/sales_persona.yaml`, `verified_agent.py`, `answer_verifier.py`, `tests/unit/test_part1_code/test_sales_presenter.py`, `scripts/script_part1/evaluate_sales_style.py`. Cải tiến tập trung vào templates/wording có kiểm soát và đánh giá before/after. **Không thể kết luận một LLM sinh tự do đã hoạt động chỉ vì OpenAI TTS tạo được tiếng nói**. TTS chỉ đọc text đã sinh/được duyệt.

**Cần xác nhận:** những template mới nào verifier chấp nhận; số từ và chất lượng before/after; ảnh hưởng lên số answered/blocked; liệu optional LLM provider có thật hay vẫn deterministic; tests của bản local cuối.

---

## 4. TRA CỨU TỪNG FILE TRONG `src/`

**Cây thư mục thuộc Part 1 (tên module có bằng chứng từ nhánh GitHub; riêng `pipeline.py` là implementation local chưa thấy trong bản GitHub đã kiểm tra):**

```text
src/hostra_ai/
├── __init__.py
├── core/
│   └── schemas/
│       ├── __init__.py
│       ├── common.py
│       ├── part1.py
│       ├── part2.py
│       └── part3.py
└── part1_agent_tts/
    ├── __init__.py
    ├── comment_ingest.py
    ├── comment_policy.py
    ├── comment_decisions.py
    ├── comment_triage.py
    ├── comment_queue.py
    ├── conversation_memory.py
    ├── knowledge_engine.py
    ├── knowledge/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── catalog_repository.py
    │   ├── faq_parser.py
    │   ├── chunking.py
    │   ├── lexical_retriever.py
    │   ├── embedding_provider.py
    │   ├── vector_index.py
    │   ├── retriever.py
    │   └── ranker.py
    ├── verified_agent.py
    ├── answer_verifier.py
    ├── speech_planner.py
    ├── tts_provider.py
    └── pipeline.py
```

### 4.1. Core/Data Contracts

| File | Công dụng | Lưu ý khi sửa |
|---|---|---|
| `src/hostra_ai/__init__.py` | Đánh dấu Python package, nhánh GitHub ghi nhận rỗng. | Không chứa logic pipeline. |
| `core/schemas/__init__.py` | Re-export schema/import chung cho các Part. | Giữ import path ổn định. |
| `core/schemas/common.py` | Validators/kiểu dùng chung cho các schema. | Thay đổi có thể ảnh hưởng cả ba Part. |
| `core/schemas/part1.py` | 5 public Pydantic models của Part 1, reason codes/status/đường dẫn WAV. | **Contract freeze**; viết migration/tests trước khi chỉnh. |
| `core/schemas/part2.py` | Contracts dành cho render/lip-sync downstream. | Chỉ là schema; không chứng minh worker có sẵn. |
| `core/schemas/part3.py` | Contracts timeline, audit, manifest/video output. | Không nằm trong runtime Part 1. |

### 4.2. M01 — Comment Processing

| File | Công dụng | Input → Output |
|---|---|---|
| `comment_ingest.py` | `load_catalog_skus`, `ingest_comments`: load/validate comment JSON, ID, source run và active SKU. | JSON catalog/comments → `CommentEvent[]`. |
| `comment_policy.py` | `CommentPolicy`, `load_policy`: đọc/validate `configs/comment_policy.yaml`. | YAML → policy cho triage/queue. |
| `comment_decisions.py` | `make_decision`: tạo `CommentDecision` hợp lệ, có decision ID duy nhất. | Event + action/reason/score/time → decision. |
| `comment_triage.py` | `CommentTriage`, `normalize_text`, spam/off-topic + score theo rule. | Comment + policy → quyết định ban đầu. |
| `comment_queue.py` | `QueueItem`, `CommentQueue`: ready/deferred, TTL, reevaluate, pop, priority/fairness/FIFO. | Decisions → `QueueItem` bàn giao M03. |

### 4.3. M02 — Knowledge/RAG

| File | Công dụng | Điểm cần nhớ |
|---|---|---|
| `knowledge_engine.py` | Facade tải Catalog + FAQ và truy xuất `search`, `retrieve`, `get_catalog_evidence`, index. | Trả **evidence ứng viên**, không phải final verified response. |
| `knowledge/models.py` | Kiểu dữ liệu nội bộ: FAQRecord, FAQChunk, hits, RagConfig, IndexManifest, EvidencePackage. | Internal models, phân biệt với 10 public contracts. |
| `knowledge/catalog_repository.py` | Đọc Catalog có cấu trúc; lookup SKU/field; defensive snapshot. | Nguồn authoritative cho giá/thông số trong PoC. |
| `knowledge/faq_parser.py` | Parse Markdown FAQ, trích câu hỏi/đề xuất/bằng chứng/review flag. | FAQ cần review không được xem là evidence chắc chắn. |
| `knowledge/chunking.py` | Mỗi FAQ thành một chunk ổn định cùng metadata. | Không cắt tùy tiện câu trả lời. |
| `knowledge/lexical_retriever.py` | BM25 Okapi offline, tokenize tiếng Việt ở mức chuỗi chữ/số. | Baseline không dùng API. |
| `knowledge/embedding_provider.py` | Interface embedding, OpenAIEmbeddingProvider, validate vectors và API errors. | API embeddings cần opt-in/credential; có thể phát sinh phí. |
| `knowledge/vector_index.py` | Exact cosine vector index; build/load/save với fingerprint/checksum/manifest. | Kiểm tra version/mô hình/dimensions khi nạp lại. |
| `knowledge/retriever.py` | `KnowledgeRetriever`, `load_rag_config`: chọn lexical/semantic/hybrid, scope SKU, evidence package. | Retrieval status không thay AnswerVerifier. |
| `knowledge/ranker.py` | Kết hợp lexical + semantic bằng Reciprocal Rank Fusion. | Không cộng trực tiếp raw scores hai bộ tìm kiếm. |
| `knowledge/__init__.py` | Package marker. | Không tự chứa retrieval engine. |

### 4.4. M03–M05 — Agent, Audio & Pipeline

| File | Công dụng | Safety/giới hạn |
|---|---|---|
| `conversation_memory.py` | ConversationTurn/Context/Memory theo `(run_id, viewer_id)`, hỗ trợ follow-up. | RAM only, không bền qua restart. |
| `verified_agent.py` | `LLMProvider` protocol, `DeterministicProvider`, `VerifiedAgent`: phân giải intent/SKU, query knowledge, tạo candidate và AgentResponse. | Provider không tự chứng minh claim; bản local Sales Persona có thể khác GitHub. |
| `answer_verifier.py` | `CandidateAnswer`, `AnswerVerifier` kiểm tra candidate dựa trên Catalog/FAQ evidence, SKU, claims hỗ trợ. | Không bảo đảm kiểm chứng freeform Vietnamese bất kỳ. |
| `speech_planner.py` | `SpeechPlanner`: response/script→SpeechTurn; approval gate; `SpeechAdmission` kiểm tra hợp lệ/ưu tiên/consume. | Không bypass pending scripts, không tự xác thực provenance. |
| `tts_provider.py` | `TTSConfig`, Mock/OpenAI providers, `normalize_wav`, `validate_wav`, `TTSService`, `write_run_metadata`. | Mock silence; live opt-in; resampling tuyến tính. |
| `pipeline.py` | `Part1Pipeline.run(run_id)` kết nối M01–M04, chặn response injection ở entry point, dedup, ghi artifacts/evaluation. | **Implementation local theo M05 report; nhánh GitHub đã kiểm tra vẫn là file rỗng.** |
| `part1_agent_tts/__init__.py` | Package marker. | Không chứa logic chính ở snapshot GitHub. |

### 4.5. Những file `src/` ngoài Part 1

`src/hostra_ai/api/`, `part2_video_lipsync/`, `part3_demo_compositor/` thuộc phạm vi kế tiếp. Đã có tên thư mục/tài liệu thiết kế và schema liên quan, nhưng **không nên suy ra** API, GPU worker, compositor đã hoàn thiện chỉ từ cấu trúc dự án. Tại bản GitHub khảo sát, không thấy `src/hostra_ai/pipeline.py` runtime tổng thể trong cây `src/hostra_ai/`.

---

## 5. `scripts/` — MỤC ĐÍCH VÀ LỆNH CHẠY TRÊN WINDOWS

**Quy ước:** chạy terminal **từ thư mục gốc project**; tất cả lệnh dùng `.venv`. Trước tiên `cd` đến thư mục `Hostra_AI_PoC` trong VS Code. Các script Part 1 đã được chuyển vào `scripts/script_part1/` theo ảnh người triển khai; nếu bản local của bạn còn nằm tại `scripts/`, sửa lệnh tương ứng. **Mọi script dùng `ROOT = Path(__file__).resolve().parents[1]` phải đổi sang `parents[2]` sau khi đưa từ `scripts/` xuống `scripts/script_part1/`.** Riêng `run_milestone01.py` và các script RAG bản GitHub đã dùng `parents[2]`.

### 5.1. M01 runner

**`scripts/script_part1/run_milestone01.py`** — chạy chỉ M01, in bảng decision theo mock 20 comments; không tạo TTS, không cần API.

```powershell
.\.venv\Scripts\python.exe scripts\script_part1\run_milestone01.py
```

**Dùng khi:** thay đổi policy, kiểm thử spam/duplicate, queue fairness, TTL/deferred. Trong runner này mô phỏng mỗi 12 giây một lượt phục vụ.

### 5.2. M02 RAG scripts

**`scripts/script_rag/prepare_knowledge.py`** — validate catalog/FAQ, in số sản phẩm, số FAQ/chunks, cờ review.

```powershell
.\.venv\Scripts\python.exe scripts\script_rag\prepare_knowledge.py
```

**`scripts/script_rag/search_faq.py`** — tìm FAQ BM25 offline; hỗ trợ `--top-k`, `--sku`, `--eval`, `--mode`; semantic/hybrid cần index/provider đã cấu hình.

```powershell
.\.venv\Scripts\python.exe scripts\script_rag\search_faq.py "ASUS nâng RAM được không?" --mode lexical --top-k 5
.\.venv\Scripts\python.exe scripts\script_rag\search_faq.py --eval --mode lexical
```

**`scripts/script_rag/build_index.py`** — build/load vector index; `--rebuild` có tác dụng tạo index lại; dùng OpenAI Embeddings khi cấu hình provider tương ứng và `--allow-api`. `--smoke` cần `--allow-api` và có thể phát sinh phí.

```powershell
.\.venv\Scripts\python.exe scripts\script_rag\build_index.py --help
# Sau khi kiểm tra config, API key và chi phí:
.\.venv\Scripts\python.exe scripts\script_rag\build_index.py --rebuild --allow-api
```

**`scripts/script_rag/evaluate_rag.py`** — đánh giá lexical/semantic/hybrid trên retrieval evaluation fixture: Recall@K, MRR@10, trạng thái OOD/ambiguous và latency theo công thức đã cài; output JSON khi chỉ định `--output`.

```powershell
.\.venv\Scripts\python.exe scripts\script_rag\evaluate_rag.py --help
.\.venv\Scripts\python.exe scripts\script_rag\evaluate_rag.py --output "shared_data\runs\rag_eval_report.json"
```

> `build_index.py` và `evaluate_rag.py` phải đọc `--help`, `configs/rag.yaml` và `--allow-api` trước khi bật semantic/hybrid. Không tự suy ra chạy được hoàn toàn offline nếu cấu hình cần OpenAI Embeddings.

**`scripts/script_rag/_common.py`** — tiện ích import/config/permission dùng chung; **không phải script người dùng chạy trực tiếp**.

### 5.3. M05 offline runner (chạy đầy đủ Part 1)

**`scripts/script_part1/run_part1.py`** — chạy M01→M02→M03→M04 (mock) trong một run, tạo JSON + WAV silence và evaluation. Đã đọc code bản user gửi khi nó còn ở `scripts/run_part1.py`; phiên bản sau khi di chuyển cần kiểm tra lại `ROOT`.

```powershell
# Tạo run ID mới, không ghi đè lần cũ
.\.venv\Scripts\python.exe scripts\script_part1\run_part1.py --run-id RUN-PART1-HANDOFF-001

# Mô phỏng queue xử lý một lượt mỗi 12 giây
.\.venv\Scripts\python.exe scripts\script_part1\run_part1.py --run-id RUN-PART1-QUEUE-012 --service-interval-seconds 12

# Kiểm tra các option của bản local
.\.venv\Scripts\python.exe scripts\script_part1\run_part1.py --help
```

Tham số đã thấy trong code: `--run-id`, `--comments`, `--config`, `--output-root`, `--tts-provider` (chỉ `mock`), `--service-interval-seconds`. `--tts-provider openai` **không được hỗ trợ bởi runner offline này**. Không sửa nhanh `choices` mà bỏ qua kiến trúc approval/trusted handoff.

**Exit code M05 theo báo cáo:** `0` = completed; `2` = partial (có lỗi xử lý comment); `1` = lỗi nghiêm trọng. Nếu run folder đã tồn tại, mặc định từ chối và không resume; tạo ID mới.

### 5.4. Preview TTS thật từ output M05/RAG

**`scripts/script_part1/preview_part1_rag_tts.py`** — script nghe thử do trợ lý cung cấp; chạy một M05 offline run **mới**, chọn câu trả lời answered/clarification có SpeechTurn và refs khớp, in text/source, rồi (chỉ khi `--confirm-live`) gọi OpenAI TTS để tạo WAV preview thật. Không tạo `AudioArtifact` chính thức cho hai WAV preview và không thay đổi run đã ghi.

```powershell
# Dry run: chạy M05/RAG, in nội dung; KHÔNG gọi TTS có phí
.\.venv\Scripts\python.exe scripts\script_part1\preview_part1_rag_tts.py --reply-comment-id CMT-001 --intro-comment-id CMT-007

# Live: tạo reply.wav và product_highlight_from_reply.wav (có phí)
.\.venv\Scripts\python.exe scripts\script_part1\preview_part1_rag_tts.py --reply-comment-id CMT-001 --intro-comment-id CMT-007 --confirm-live

# Chỉ cần một câu trả lời thực từ M03
.\.venv\Scripts\python.exe scripts\script_part1\preview_part1_rag_tts.py --reply-comment-id CMT-001 --no-intro --confirm-live
```

**Phân biệt intro:** `--intro-comment-id CMT-007` chỉ dùng **comment_reply** đã được M03 xác minh làm đoạn product highlight, không phải `product_intro` chính thức. Để phát `product_intro`, cần `--intro-script-id` trỏ tới script **đã approved thật** và `--confirm-intro-conditions`; script hỗ trợ kiểm tra điều kiện rất giới hạn (catalog-only), có thể từ chối script có FAQ refs. **Không dùng cờ xác nhận để biến script pending thành approved.**

**Đầu ra:** `shared_data/tts_previews/PREVIEW-RAG-<id>/reply.wav`, có thể thêm `product_highlight_from_reply.wav` hoặc `intro.wav`, và `preview_info.json`. Hai WAV này **không ở** `shared_data/runs/.../audio/` và không được ghi vào `audio_artifacts.json` chính thức.

**Thử nghe trên Windows:**

```powershell
# Đổi đường dẫn theo PREVIEW-RAG thư mục thực vừa in trên terminal
ii ".\shared_data\tts_previews\PREVIEW-RAG-<id>\reply.wav"
```

**Cần chuẩn bị trước khi dùng `--confirm-live`:** SDK/dependencies, `OPENAI_API_KEY` trong environment terminal, model Speech API có quyền truy cập, cấu hình `configs/app.yaml`, và đồng ý chi phí. Đừng commit API key lên GitHub.

### 5.5. So sánh câu trả lời trước và sau Sales Persona

**`scripts/script_part1/evaluate_sales_style.py`** — script Codex đã tạo local; đọc **hai thư mục run** chứa `evaluation.json` và `answers.json`, so sánh cùng bộ comment/viewer và xuất JSON với old/new answer, word count, status, decision, SKU và refs. **Không tự chạy RAG, không sinh audio, không chấm chất lượng tự nhiên một cách độc lập.**

```powershell
.\.venv\Scripts\python.exe scripts\script_part1\evaluate_sales_style.py `
  --before "shared_data/runs/RUN-STYLE-BEFORE-20261029/step1_agent_audio" `
  --after  "shared_data/runs/RUN-STYLE-AFTER-20261029/step1_agent_audio" `
  --output "sales_comparison_new.json"
```

Đổi tên run theo thư mục hiện có; file output phải **chưa tồn tại** (mở mode `x`). So sánh chỉ có ý nghĩa nếu hai run cùng bộ dữ liệu/phạm vi queue và phiên bản code mong muốn. Số từ tính theo `split()`, chưa phải đánh giá tính thuyết phục hay kiểm chứng độc lập.

### 5.6. Script preview TTS hardcoded cũ — không dùng làm bằng chứng RAG

**`preview_part1_real_tts.py`** (nếu vẫn còn ở máy) là công cụ audition hai đoạn text có thể hardcode `INTRO_PREVIEW` và `REPLY_PREVIEW`; chỉ reply có thể đọc từ `answers.json` khi chỉ định `--answers-json`. Đây là bản thử kỹ thuật TTS, **không chứng minh M02/M03 đã chạy**. Để kiểm chứng lời thoại thật từ Part 1, ưu tiên `preview_part1_rag_tts.py`.

### 5.7. Kiểm thử sau thay đổi

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Sau khi chuyển script sang `scripts/script_part1/`, chạy `--help` và test các lệnh thực tế, kiểm tra `ROOT = Path(__file__).resolve().parents[2]` ở các runner mới và cập nhật mọi tài liệu/tests còn trỏ đến `scripts/run_part1.py`.

---

## 6. KẾT QUẢ ĐẦU RA VÀ CÁCH ĐỌC ARTIFACTS

### 6.1. Một run offline thành công

```text
shared_data/
├── runs/
│   └── <run_id>/
│       └── step1_agent_audio/
│           ├── comment_decisions.json
│           ├── answers.json
│           ├── speech_turns.json
│           ├── audio_artifacts.json
│           ├── evaluation.json
│           └── audio/
│               ├── <audio_id>.wav
│               └── ...
└── tts_previews/
    └── PREVIEW-RAG-<id>/
        ├── reply.wav
        ├── product_highlight_from_reply.wav  # nếu chọn comment highlight
        └── preview_info.json
```

| Artifact | Mục đích | Kiểm tra nhanh |
|---|---|---|
| `comment_decisions.json` | **Toàn bộ lịch sử** quyết định M01, kể cả deferred→selected sau reevaluate. | Một comment có thể có nhiều decision. |
| `answers.json` | Các `AgentResponse` thực do M03 tạo khi queue chọn. | Skipped không có answer; blocked không có text phát. |
| `speech_turns.json` | Các `SpeechTurn` được planner lập/admission chọn theo luồng. | `response_id`/`script_ref` phù hợp speech_type. |
| `audio_artifacts.json` | Metadata mỗi WAV được M04 tạo. | `file_path`, duration, run/turn/response links phải khớp file. |
| `audio/<audio_id>.wav` | WAV MockTTSProvider: **silence** 16-bit mono 16 kHz. | File có duration dương **không nghĩa là có tiếng nói**. |
| `evaluation.json` | Summary + một dòng mỗi comment, timings và trạng thái run. | Xem `status`, counts và lỗi; đây là bằng chứng cho run cụ thể. |
| `tts_previews/.../reply.wav` | WAV giọng TTS API thật cho **nghe thử riêng**. | Có thể dùng trong thử nghiệm thủ công, chưa phải artifact hợp đồng chính thức. |

### 6.2. Trình tự kiểm tra khi tiếp nhận một run

1. `evaluation.json` tồn tại, `status='completed'` nếu được tuyên bố thành công; nếu `partial` hoặc thiếu evaluation, không chấp nhận nghiệm thu run.
2. `comment_decisions.json`: đối chiếu số và hành động; không kỳ vọng cả 20 comments đều answered.
3. `answers.json`: kiểm tra answered/clarification/blocked, evidence refs, SKU; **đọc status không đủ chứng minh claim** nếu bypass M03.
4. `speech_turns.json`: kiểm tra reply giữ nguyên answer text, script_ref thuộc approved script khi intro/fallback.
5. `audio_artifacts.json`: đối chiếu mỗi `speech_turn_id`/`audio_id` với WAV tồn tại và đúng run.
6. Dùng Python `wave` hoặc ffprobe đọc WAV: PCM 16-bit, 1 channel, sample rate mục tiêu, frame count và `duration_ms` thực.
7. Không mở nhầm WAV `shared_data/runs/.../audio/` (mock silence) với `shared_data/tts_previews/...` (giọng API thực).

### 6.3. Lệnh kiểm tra nhanh artifacts

```powershell
# Liệt kê các run đã tạo
Get-ChildItem .\shared_data\runs -Directory | Select-Object Name

# Liệt kê các TTS preview WAV thật
Get-ChildItem .\shared_data\tts_previews -Recurse -Filter *.wav | Select-Object FullName,Length

# Đọc evaluation.json của một run (thay RUN_ID)
Get-Content ".\shared_data\runs\RUN_ID\step1_agent_audio\evaluation.json" -Encoding UTF8
```

---

## 7. KẾT QUẢ KIỂM THỬ, NGHIỆM THU VÀ CÁCH DIỄN GIẢI

| Mốc | Bằng chứng đã có | Kết luận đúng phạm vi |
|---|---|---|
| M01 | Mã ingest/triage/queue + runner + unit/integration. | Hoạt động ở phạm vi rules/offline PoC. |
| M02 | Mã BM25, vector, RRF, CLI và eval fixture. | Retrieval hoạt động; có OOD false-accept, không đồng nghĩa verified answer. |
| M03 hardening | **391 tests + 65 subtests passed**, theo Codex. | Conditional GO; verifier freeform còn giới hạn. |
| M04 audit | **402 passed, 0 failed, 0 skipped, 65 subtests passed**; mock WAV 16 kHz PCM 16-bit mono. | Conditional GO offline; NO-GO phát TTS thật tại thời điểm audit. |
| M05 + cải thiện Sales Persona | Ảnh/báo cáo triển khai: **423 tests**, khoảng **17 selected, 3 skipped, 11 answered, 6 blocked** trong một run. | Có pipeline offline; cần chốt lại trên local HEAD bằng full pytest và evaluation file cụ thể. |
| Live TTS preview sau M05 | Người triển khai đã chạy vài WAV API thật và nghe đạt mức sơ bộ; terminal từng cho thấy `reply.wav` khoảng 9,95 giây. | **User smoke thực nghiệm**, không phải chứng nhận QA toàn bộ model/voice/speech quality. |
| Part 2 | Chưa có worker xác minh chính thức được bàn giao. | Chưa nghiệm thu lip-sync thực. |

**Không cộng số tests giữa các mốc.** Các giá trị là snapshots của toàn bộ suite tại các thời điểm khác nhau, không phải 391+402+423 bài test độc lập. Sau khi commit bản cuối cần chạy lại full suite và gắn commit SHA + terminal log vào phụ lục nghiệm thu.

### 7.1. Ý nghĩa các trạng thái

- **Offline PASS**: pipeline kiểm soát business rules và tạo JSON/WAV mock nhất quán trên test fixtures; chưa chứng minh giọng người thật.
- **Real TTS preview OK**: đã có giọng nghe được từ Speech API qua preview script và sample thực; chưa chứng minh toàn bộ lịch phát và mọi kịch bản.
- **Part 1 Conditional GO for Part 2**: giao diện/media format có thể dùng để thiết kế handoff, nhưng final audio và lip-sync vẫn cần thực nghiệm.
- **Production ready**: **chưa đạt**; dự án hiện là PoC.

---

## 8. VẤN ĐỀ CHƯA HOÀN THÀNH VÀ KHUYẾN NGHỊ

| Ưu tiên | Vấn đề | Hướng xử lý / người phụ trách |
|---|---|---|
| P0 | 15 scripts vận hành vẫn pending review. | Nhóm nghiệp vụ/owner đối chiếu facts, `use_when`, rights; duyệt thật với `approved_by`, `approved_at`. |
| P0 | Tính đúng claim M03 không tổng quát cho freeform LLM. | Nhóm M03 giữ provider deterministic/fail-closed; bổ sung verifier theo claim, kiểm thử adversarial trước bật LLM. |
| P0 | Nhánh GitHub chưa có M05 implementation và Sales Persona local theo lần kiểm tra này. | Người triển khai rà `git status`, bảo đảm secrets/WAV không bị stage, commit/push source/tests/docs đúng nhánh, ghi SHA. |
| P1 | Resampling M04 bằng linear interpolation, chưa anti-aliasing. | Đánh giá polyphase/FFmpeg, phổ/tần số, nghe thử, regression. |
| P1 | Chưa kiểm thử producer/consumer end-to-end với Part 2 worker cụ thể. | Part 2 chốt sample rate, codec, duration, model version, padding/trimming. |
| P1 | M05 không hỗ trợ resume, distributed concurrency hay transactional run. | Phạm vi PoC chấp nhận có điều kiện; bổ sung run lifecycle khi mở rộng. |
| P1 | Chưa có golden-labeled SKU metrics tự động và đánh giá hội thoại tự nhiên toàn diện. | Lưu before/after, human listening score, factual correctness, word count, TTS duration. |
| P1 | Runtime M05 runner chỉ mock TTS; preview TTS không tạo official AudioArtifact. | Dùng preview riêng cho nghe thử; khi cần official real-run, thiết kế adapter opt-in ngay trong trusted runtime và tests. |
| P2 | Script paths đã được chuyển xuống `scripts/script_part1/`. | Kiểm tra ROOT parents, `--help`, README và các lệnh trong docs/tests. |

### 8.1. Checklist phải làm trước khi bàn giao cho kỹ sư mới

- [ ] Commit/push bản local M05, Sales Persona, tests và scripts; ghi commit SHA.
- [ ] Chạy full pytest trên máy bàn giao; lưu terminal log `passed/failed/skipped/subtests`.
- [ ] Chạy một `run_part1.py` mới, kiểm tra `evaluation.json`, tất cả JSON và WAV header.
- [ ] Ghi rõ run ID tham chiếu và đường dẫn run output đã nghiệm thu.
- [ ] Kiểm tra demo prices là mock; không dùng làm báo giá thật.
- [ ] Giữ nguyên trạng thái approval pending cho tới khi có phê duyệt thực.
- [ ] Xác nhận cấu hình provider/model voice đang còn dùng được tại ngày triển khai.
- [ ] Đưa cho Part 2 mẫu WAV **giọng nói thật** riêng, không nhầm silence mock.
- [ ] Thống nhất giao thức Final Scheduler: khi nào comment xuất hiện và khi nào audio được phát.
- [ ] Đối chiếu mọi file script local đã chuyển với đường dẫn trong README/docs.

---

## 9. HANDOFF CHO ORCHESTRATION VÀ PART 2

**Những thứ Part 1 có thể bàn giao ngay:** cấu trúc CommentDecision/AgentResponse/SpeechTurn/AudioArtifact, file JSON theo run, WAV PCM 16-bit mono 16 kHz **mock** và những preview WAV TTS thật đã chạy thử ở thư mục riêng. Trước khi thực nghiệm worker, người nhận cần chỉ định model/version và xác nhận resampling/format.

**Những gì Part 2 và Orchestration phải tự xây:**

- Admission toàn cục khi nhiều luồng/lượt chạy (nếu cần), không coi SpeechAdmission in-memory là durable broker.
- Final scheduling dựa trên duration WAV đo được, không overlap, không phát trả lời trước lúc comment xuất hiện và không vượt độ dài demo.
- `RenderJob`/VideoArtifact, license gate đối với hình ảnh/giọng nói, chạy GPU worker lip-sync thực, validate media output.
- Video overlays/lip-sync và compositor/timeline của Part 3; bảo toàn video nền liên tục.

**Lưu ý bản quyền và minh bạch:** chỉ dùng hình/giọng thuộc quyền sử dụng hợp lệ và thông báo rõ nội dung audio/video được AI tạo ra khi demo công khai.

---

## 10. QUY TRÌNH TIẾP QUẢN NHANH — 10 PHÚT

1. **Nhận repo + branch:** checkout `feature/part1-agent-tts`; xem `git status` và commit SHA. Đừng giả định GitHub đã chứa toàn bộ M05 chưa push.
2. **Mở đúng project root trong VS Code**; xác nhận `.venv` tồn tại và Python hỗ trợ các dependencies của `requirements.txt`.
3. **Đọc nhanh:** `docs/architecture.md`, `docs/data_contracts.md`, `docs/m04_speech_tts.md`, `docs/m05_part1_pipeline.md` (bản local), `configs/app.yaml`, `configs/comment_policy.yaml`, `configs/rag.yaml`.
4. **Chạy full tests** bằng lệnh pytest ở §5.7. Nếu có regression, kiểm tra file và revision local trước khi sửa.
5. **Chạy M01** qua `run_milestone01.py` để hiểu decisions/deferred/fairness.
6. **Chạy M02** qua `prepare_knowledge.py` và `search_faq.py --mode lexical` để hiểu Catalog/FAQ evidence.
7. **Chạy M05 offline** bằng `run_part1.py --run-id <mới>`; mở `evaluation.json` và `answers.json`.
8. **Nghe giọng thật có chủ đích** qua `preview_part1_rag_tts.py --confirm-live` sau khi kiểm tra API key/model/chi phí. Không mở nhầm file WAV silence trong `runs/`.
9. **So sánh chất lượng Sales Persona** bằng `evaluate_sales_style.py` trên hai runs có cùng 20 comments.
10. **Chốt handoff:** ghi run ID, mẫu WAV thật, các P0/P1 mở và điều kiện cho Part 2.

---

## 11. NGUỒN THAM KHẢO NỘI BỘ VÀ ĐƯỜNG DẪN

**Tài liệu:**

- HOSTRA_AI_PoC V2.1 — tài liệu thiết kế 243 trang do nhóm cung cấp.
- `docs/architecture.md` — kiến trúc dự án: https://github.com/QuangCanhCut/Hostra_AI_PoC/blob/feature/part1-agent-tts/docs/architecture.md
- `docs/data_contracts.md` — public schemas: https://github.com/QuangCanhCut/Hostra_AI_PoC/blob/feature/part1-agent-tts/docs/data_contracts.md
- `docs/m04_speech_tts.md` — chi tiết M04: https://github.com/QuangCanhCut/Hostra_AI_PoC/blob/feature/part1-agent-tts/docs/m04_speech_tts.md
- `docs/rag_design.md` — M02 RAG: https://github.com/QuangCanhCut/Hostra_AI_PoC/blob/feature/part1-agent-tts/docs/rag_design.md
- `docs/m05_part1_pipeline.md` — tài liệu M05 trong ảnh local, **chưa thể xác minh có trên nhánh GitHub đã kiểm tra**.

**Source chính:** https://github.com/QuangCanhCut/Hostra_AI_PoC/tree/feature/part1-agent-tts/src/hostra_ai/part1_agent_tts

**Lưu ý nguồn:** các file `run_part1.py`, `preview_part1_rag_tts.py` và `evaluate_sales_style.py` có nội dung do người triển khai cung cấp trong cuộc trao đổi, nhưng source mới nhất sau khi di chuyển file và nâng cấp Sales Persona chưa được kiểm tra trực tiếp từ workspace. Khi có commit mới, cập nhật báo cáo theo revision thay vì suy đoán.

---

## 12. QUYẾT ĐỊNH CUỐI VÀ TRẠNG THÁI CHUYỂN GIAO

**Part 1 (M01–M05): ĐÃ CÓ BẢN TÍCH HỢP OFFLINE CHẠY ĐƯỢC, ĐẠT MỤC TIÊU KỸ THUẬT PoC THEO BÁO CÁO CỦA NGƯỜI TRIỂN KHAI.** Các module M01–M04 có code và tests; M05 tạo run artifacts và evaluation; bước nghe thử TTS API thật đã thực hiện ở một số mẫu và nhận xét ban đầu tích cực.

**Trạng thái bàn giao đề xuất: CONDITIONAL GO** cho nhóm Part 2 tiếp nhận giao diện và bắt đầu kiểm thử kỹ thuật. Chưa được tuyên bố production-ready hoặc end-to-end lip-sync verified, bởi còn thiếu phê duyệt script, xác nhận worker, chính sách tích hợp âm thanh thật và nghiệm thu chất lượng trong điều kiện video demo.

**Hành động quan trọng nhất sau tài liệu này:** đồng bộ nhánh Git với bản local mới nhất, chạy lại full test và xác nhận một run ID tiêu biểu. Sau đó nhóm Part 2 có thể bắt đầu từ `SpeechTurn`, `AudioArtifact`, WAV và các ràng buộc thời gian đã mô tả.
