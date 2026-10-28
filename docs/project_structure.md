# HOSTRA AI PoC — Tài liệu chú thích cấu trúc Project


**Project:** HOSTRA AI — Hybrid AI Live Commerce Proof of Concept


**Repository:** https://github.com/QuangCanhCut/Hostra_AI_PoC


**Công nghệ:** Python, Pydantic v2, LLM, RAG, TTS, Lip-sync, FFmpeg, FastAPI, HTML/CSS/JS, Pytest


**Giai đoạn:** Proof of Concept (PoC)


**Phiên bản tài liệu:** V2.1 — Modular Knowledge Engine / RAG


**Ngày cập nhật:** 28/10/2026


**Trạng thái:** M01 đã nghiệm thu chức năng qua kiểm thử local; M02 (Knowledge Engine & RAG) đang thiết kế. Các file ghi "dự kiến" trong cây thư mục chưa được xác nhận tồn tại hoặc hoàn thiện.


---


# 1. MỤC ĐÍCH TÀI LIỆU


Tài liệu mô tả cấu trúc thư mục, vai trò của từng module, dữ liệu đầu vào (Input), dữ liệu đầu ra (Output) và mối quan hệ giữa các thành phần của dự án HOSTRA AI PoC.


Tài liệu phục vụ các mục tiêu:


1. Giúp các thành viên hiểu kiến trúc tổng thể trước khi lập trình.
2. Xác định trách nhiệm và phạm vi xử lý của từng module.
3. Thống nhất cách tổ chức source code và data contracts.
4. Hạn chế việc viết trùng chức năng giữa các thành viên.
5. Đảm bảo các module có thể phát triển, kiểm thử và tích hợp độc lập.
6. Cung cấp tài liệu tham chiếu khi review code và Pull Request.
7. Đảm bảo kiến trúc phục vụ đúng đầu ra cuối cùng của PoC.


## 1.1. Phạm vi tài liệu


Tài liệu tập trung vào kiến trúc và cấu trúc repository.


Chi tiết field, Enum, validator và các quy tắc của Pydantic schemas được quản lý trong:


`docs/data_contract_vi.md`


Chi tiết sơ đồ kiến trúc và tương tác giữa các thành phần được quản lý trong:


`docs/architecture.md`


## 1.2. Nguyên tắc thiết kế


HOSTRA AI PoC áp dụng các nguyên tắc:


- Contract First: Thống nhất dữ liệu trước khi tích hợp.
- Modular Development: Chia hệ thống thành các module có trách nhiệm rõ ràng.
- Separation of Concerns: Tách logic nghiệp vụ, API, dữ liệu và giao diện.
- Verifiable Results: Mọi đầu ra quan trọng đều có thể kiểm tra.
- Reproducibility: Một lần chạy có thể truy vết cấu hình, nguồn dữ liệu và kết quả.
- Offline-first PoC: Ưu tiên chứng minh pipeline offline trước khi triển khai realtime.


**Lưu ý:** Một số file trong tài liệu là thành phần dự kiến, chưa phải tất cả đều đã được triển khai. Nhóm chỉ tạo file khi bắt đầu task tương ứng và cập nhật tài liệu theo implementation thực tế.


---


# 2. ĐẦU RA MỤC TIÊU CỦA PROJECT


## 2.1. Mô tả sản phẩm demo


HOSTRA AI PoC mô phỏng một phiên livestream bán hàng bằng AI.


Hệ thống sử dụng một video nền quay sẵn người thật đang cầm và thao tác với sản phẩm.


AI có khả năng:


1. Chủ động giới thiệu sản phẩm khi chưa có bình luận.
2. Nhận các bình luận khách hàng được mô phỏng.
3. Lọc và lựa chọn những bình luận phù hợp.
4. Truy xuất thông tin sản phẩm.
5. Tạo câu trả lời có kiểm chứng.
6. Chuyển lời thoại thành giọng nói.
7. Đồng bộ khẩu hình người trong video với giọng AI.
8. Tiếp tục giới thiệu hoặc trả lời các bình luận tiếp theo.


## 2.2. Yêu cầu đặc biệt về video


Video cuối cùng phải sử dụng một video nền liên tục.


Không xây dựng video cuối bằng cách nối nhiều cảnh quay độc lập.


Thay vào đó:


- `base_operator.mp4` là nguồn hình ảnh chính xuyên suốt.
- Hình ảnh người bán, sản phẩm và bối cảnh phải liên tục theo timeline gốc.
- Lip-sync được áp dụng tại những thời điểm có lời thoại.
- Khi không có lời thoại, video nền tiếp tục phát bình thường.
- Âm thanh được đồng bộ theo timeline.
- Bình luận xuất hiện đúng thời điểm được định nghĩa trong kịch bản.


Part 2 được phép tạo các video artifact trung gian để xử lý lip-sync.


Tuy nhiên, các artifact này phải được căn chỉnh với video nền và không được xem là các cảnh quay độc lập để nối tuần tự.


## 2.3. Đầu ra cuối cùng


Một lần chạy thành công tạo ra:


| Output | Nội dung |
|---|---|
| hostra_demo.mp4 | Video demo hoàn chỉnh |
| manifest.json | Cấu hình và metadata của lần chạy |
| comment_decisions.json | Kết quả chọn lọc bình luận |
| answers.json | Câu trả lời đã kiểm chứng |
| speech_turns.json | Danh sách lượt lời của AI |
| audio/*.wav | Âm thanh do TTS tạo |
| render_jobs.json | Các tác vụ lip-sync |
| video_artifacts.json | Metadata kết quả render |
| timeline.json | Các sự kiện theo timeline |
| audit_log.json | Nhật ký xử lý |
| benchmark.json | Kết quả đo hiệu năng thực tế |


## 2.4. Những chức năng ngoài phạm vi PoC


Phiên bản PoC chưa yêu cầu:


- Phát livestream thực tế lên TikTok hoặc Shopee.
- Xử lý video và lip-sync thời gian thực hoàn chỉnh.
- Kết nối trực tiếp API bình luận từ nền tảng livestream.
- Tự động nhận diện mọi hành động vật lý của operator.
- Quản lý hàng nghìn người dùng đồng thời.
- Marketplace cấp phép avatar hoàn chỉnh.
- Hệ thống thanh toán hoặc xử lý đơn hàng thật.


Các chức năng này thuộc các giai đoạn MVP và phát triển sản phẩm sau PoC.


---


# 3. TỔNG QUAN KIẾN TRÚC

HOSTRA AI PoC chia thành **Part 1, Part 2, Part 3** và một lớp **Orchestration**. Đây là kiến trúc mục tiêu, không phải tuyên bố các module đều đã triển khai.

## 3.1. Part 1 — Comment Processing, Knowledge Engine, Verified Agent & TTS

- **M01 — Comment Processing (đã kiểm thử chức năng):** nhận mock comments, xác thực CommentEvent, lọc trùng/spam/off-topic bằng quy tắc, chấm điểm, quản lý hàng đợi và bàn giao `QueueItem`. Không dùng LLM.
- **M02 — Knowledge Engine & RAG (đang thiết kế):** parse Catalog + 39 FAQ, chia chunk theo mục FAQ, xây chỉ mục lexical và vector, retrieval/ranking có dẫn nguồn. Không tạo câu trả lời LLM trong M02.
- **M03 — Verified AI Sales Agent:** observation, Conversation Memory theo viewer/run, phân giải tham chiếu SKU, gọi Knowledge Engine/Tools, sinh ứng viên trả lời bằng LLM và kiểm chứng trước khi tạo AgentResponse.
- **M04 — Speech Planner & TTS:** lựa chọn lời giới thiệu đã duyệt / câu trả lời hợp lệ / fallback, chuẩn hóa SpeechTurn và tạo WAV + AudioArtifact.
- **M05 — Integration & Evaluation:** kiểm thử luồng Part 1, độ chính xác truy xuất và phát ngôn, lỗi, độ trễ, chi phí, audit và hợp đồng bàn giao.

**Output chính của Part 1:** CommentDecision, AgentResponse, SpeechTurn, AudioArtifact. `QueueItem`, `FAQChunk`, `RetrievedEvidence` là cấu trúc nội bộ, không tự ý đổi 10 public data contracts hiện có.

## 3.2. Orchestration — Speech Scheduling

Orchestration quản lý giới hạn 120 giây, mức ưu tiên và thứ tự phát, không cho lời thoại chồng nhau, và đảm bảo mọi lời thoại thực sự phát được đối chiếu với audio/time window/video nguồn.

**Thiết kế đích đề xuất gồm hai giai đoạn:** (1) admission chọn lời thoại cần tổng hợp, (2) final scheduling sau khi biết thời lượng WAV thực. Interface cụ thể phải thống nhất khi tích hợp M04–M05, không xem một `QueueItem.pop()` là một lời thoại sẽ phát.

## 3.3. Part 2 — Time-aligned Video Lip-sync

Kiểm tra quyền sử dụng, ánh xạ frame từ timeline và video nền, tạo RenderJob / VideoArtifact / overlays tại đúng vị trí được đặt lịch. Không nối các cảnh quay rời để thay thế video nền liên tục.

## 3.4. Part 3 — Continuous Video Compositor

Tạo RunManifest, timeline, audit và benchmark; căn overlays + audio + comment theo video nền `base_operator.mp4` duy nhất; xuất `hostra_demo.mp4`.

## 3.5. Luồng xử lý tổng thể (thiết kế mục tiêu)

```text
MOCK COMMENTS                  CATALOG + PRODUCT FAQ
      |                                |
      v                                v
M01: INGEST -> TRIAGE -> QUEUE  M02: KNOWLEDGE PREPARATION
      |                        (parse/chunk/index)
      |                                |
      v                                v
Selected CommentEvent ------> M03: VERIFIED AI AGENT
                  (memory + SKU resolver + evidence + LLM + verifier)
                                       |
                                 AgentResponse
                                       |
                   APPROVED SCRIPTS ---+--- SAFE FALLBACK
                                       |
                               M04: SPEECH PLANNER
                                       |
                                  SpeechTurn
                                       |
                         ORCHESTRATION: ADMISSION
                                       |
                                  TTS -> WAV
                                       |
                            AudioArtifact (real duration)
                                       |
                        ORCHESTRATION: FINAL SCHEDULE
                                       |
                    PART 2: TIME-ALIGNED LIP-SYNC
                                       |
                    PART 3: CONTINUOUS COMPOSITOR
                                       |
                                 hostra_demo.mp4
                              + timeline/audit/benchmark
```

M01 hiện mô phỏng một lượt bàn giao mỗi **12 giây**, `pop()` 16 comments đến **giây 188** vì runner drain queue. Đây là chế độ test hàng đợi, **không phải** lịch phát của video mục tiêu 120 giây. Mốc UTC phiên RUN-001 theo tài liệu là `2026-10-27T13:00:00Z`; video offset cần tính từ `RunManifest.timeline_start_at` khi tích hợp.

---

# 4. CẤU TRÚC THƯ MỤC PROJECT — V2.1

Dưới đây là **cây thư mục mục tiêu sau khi bổ sung Modular RAG**, trong đó chú thích `M01: đã triển khai` nghĩa là đã đối chiếu được từ các file code và kết quả chạy local bạn cung cấp; các mục `dự kiến` **chưa có nghĩa đã tồn tại trong repository**. Những file đang trống hoặc chưa được code không nên mô tả như tính năng hoàn thiện.

```text
hostra-ai-poc/
├── .env.example                        # Mẫu biến môi trường; được commit
├── .gitignore                          # Ignore .env, .venv, runs và index sinh ra
├── README.md
├── pytest.ini
├── requirements.txt
├── pyproject.toml                       # Dự kiến / tùy cách quản lý package
├── requirements-dev.txt                # Dự kiến
├── requirements-gpu.txt                # Dự kiến, GPU worker
│
├── .github/
│   └── workflows/
│       └── ci.yml                      # Dự kiến
│
├── configs/
│   ├── app.yaml
│   ├── demo_scenario.yaml               # Dự kiến
│   ├── comment_policy.yaml             # M01: đã sử dụng
│   └── rag.yaml                        # M02: dự kiến (retrieval/index/eval)
│
├── shared_data/
│   ├── inputs/
│   │   ├── catalog_skus.json
│   │   ├── product_faq.md
│   │   ├── mock_comments.json
│   │   ├── creator_license.json
│   │   ├── approved_product_scripts.json  # Nội dung phải duyệt trước khi phát
│   │   └── base_operator.mp4           # Chưa có video nguồn hoàn chỉnh
│   │
│   ├── indexes/                        # M02.3: chỉ mục sinh ra; không commit
│   │   └── knowledge/                  # Dự kiến; version + checksum nguồn
│   │
│   └── runs/                           # Artifact từng run; không commit
│       └── <run_id>/
│           ├── manifest.json
│           ├── step1_agent_audio/
│           │   ├── comment_decisions.json
│           │   ├── answers.json
│           │   ├── speech_turns.json
│           │   └── audio/
│           │       └── <audio_id>.wav
│           ├── step2_lipsync/
│           │   ├── render_jobs.json
│           │   ├── video_artifacts.json
│           │   └── overlays/
│           └── step3_final/
│               ├── hostra_demo.mp4
│               ├── timeline.json
│               ├── audit_log.json
│               └── benchmark.json
│
├── src/
│   └── hostra_ai/
│       ├── __init__.py
│       ├── pipeline.py                  # Điều phối toàn ứng dụng (dự kiến)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── common.py
│       │       ├── part1.py
│       │       ├── part2.py
│       │       └── part3.py
│       │
│       ├── part1_agent_tts/
│       │   ├── __init__.py
│       │   ├── comment_ingest.py        # M01: đã triển khai
│       │   ├── comment_policy.py        # M01: đã triển khai
│       │   ├── comment_decisions.py     # M01: factory CommentDecision
│       │   ├── comment_triage.py        # M01: đã triển khai
│       │   ├── comment_queue.py         # M01: đã triển khai
│       │   │
│       │   ├── knowledge_engine.py      # M02: facade, không chứa toàn bộ RAG
│       │   ├── knowledge/               # M02: Modular Knowledge Engine
│       │   │   ├── __init__.py
│       │   │   ├── models.py            # M02.1: FAQChunk, RetrievedEvidence nội bộ
│       │   │   ├── catalog_repository.py # M02.1: lookup Catalog theo SKU/field
│       │   │   ├── faq_parser.py        # M02.1: parse 39 mục FAQ
│       │   │   ├── chunking.py          # M02.1: mỗi mục FAQ = 1 chunk
│       │   │   ├── lexical_retriever.py # M02.2: keyword/BM25 baseline
│       │   │   ├── embedding_provider.py # M02.3: embeddings provider
│       │   │   ├── vector_index.py      # M02.3: local vector index
│       │   │   ├── retriever.py         # M02.4: hybrid retrieval / metadata filters
│       │   │   └── ranker.py           # M02.4: ranking/fusion
│       │   │
│       │   ├── conversation_memory.py   # M03: theo run_id, viewer_id
│       │   ├── verified_agent.py        # M03: LLM/tool orchestration
│       │   ├── answer_verifier.py       # M03: kiểm chứng phát ngôn
│       │   ├── speech_planner.py        # M04: SpeechTurn/approved scripts
│       │   ├── tts_provider.py          # M04: AudioArtifact/WAV
│       │   └── pipeline.py             # M05: tích hợp Part 1
│       │
│       ├── orchestration/
│       │   ├── __init__.py
│       │   └── speech_scheduler.py      # M04-M05: admission + final scheduling
│       │
│       ├── part2_video_lipsync/
│       │   ├── __init__.py
│       │   ├── license_gate.py
│       │   ├── frame_mapper.py
│       │   ├── lipsync_adapter.py
│       │   ├── artifact_validator.py
│       │   └── render_service.py
│       │
│       ├── part3_demo_compositor/
│       │   ├── __init__.py
│       │   ├── run_manager.py
│       │   ├── timeline_builder.py
│       │   ├── timeline_validator.py
│       │   ├── video_compositor.py
│       │   ├── audit_service.py
│       │   ├── benchmark_collector.py
│       │   └── teleprompter.py
│       │
│       └── api/
│           ├── __init__.py
│           ├── app.py
│           └── routes.py
│
├── notebooks/
│   └── colab_lipsync_worker.ipynb
│
├── web/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── scripts/
│   ├── script_part1/
│   │   └── run_milestone01.py           # M01: runner thực tế
│   ├── run_milestone02.py              # M02: runner truy xuất, dự kiến
│   ├── validate_inputs.py
│   ├── run_part1.py
│   ├── prepare_lipsync.py
│   ├── import_lipsync.py
│   └── run_demo.py
│
├── tests/
│   ├── fixtures/
│   │   ├── part1/
│   │   ├── part2/
│   │   └── part3/
│   ├── unit/
│   │   ├── test_part1.py
│   │   ├── test_part2.py
│   │   ├── test_part3.py
│   │   └── test_part1_code/             # M01 đã tạo; M02 thêm test tại đây
│   │       ├── test_comment_ingest.py
│   │       ├── test_comment_triage.py
│   │       ├── test_comment_queue.py
│   │       ├── test_catalog_repository.py  # M02.1 dự kiến
│   │       ├── test_faq_parser.py           # M02.1 dự kiến
│   │       ├── test_chunking.py            # M02.1 dự kiến
│   │       ├── test_lexical_retriever.py   # M02.2 dự kiến
│   │       ├── test_vector_index.py        # M02.3 dự kiến
│   │       └── test_ranker.py              # M02.4 dự kiến
│   ├── contract/
│   │   ├── test_part1_contract.py
│   │   ├── test_part2_contract.py
│   │   └── test_part3_contract.py
│   └── integration/
│       ├── test_comment_processing.py     # Tùy backlog
│       ├── test_knowledge_engine.py       # M02 dự kiến
│       ├── test_part1_pipeline.py
│       ├── test_part2_pipeline.py
│       ├── test_part3_pipeline.py
│       └── test_demo_pipeline.py
│
└── docs/
    ├── architecture.md
    ├── project_structure.md             # Tài liệu này (V2.1)
    ├── rag_design.md                    # M02: thiết kế RAG, dự kiến
    ├── data_contract_vi.md
    ├── setup_guide.md
    ├── test_plan.md
    ├── benchmark.md
    └── demo_script.md
```

## 4.1. Nguyên tắc cập nhật cấu trúc

1. **Không tái cấu trúc M01:** giữ nguyên năm module `comment_*` và factory `comment_decisions.py`, cùng các bài test đã qua kiểm thử.
2. **M02 sử dụng package `knowledge/`:** mỗi module đảm nhiệm một phần parsing, chunking, indexing, retrieval hoặc ranking. `knowledge_engine.py` ở thư mục cha là **facade duy nhất** mà Verified Agent sẽ gọi.
3. **Tạo file theo từng sub-milestone:** M02.1 chỉ cần `models.py`, `catalog_repository.py`, `faq_parser.py`, `chunking.py` và facade; chưa cần file vector/embedding thực thi.
4. **Không chuyển lẫn trách nhiệm:** `ConversationMemory`, `VerifiedAgent`, `AnswerVerifier` thuộc M03; generation bằng LLM không nằm trong M02; Speech Scheduler ở `orchestration/`.
5. **Đường dẫn thực tế ưu tiên hơn cây đề xuất:** runner M01 đang là `scripts/script_part1/run_milestone01.py`; các unit tests M01 đang ở `tests/unit/test_part1_code/`.
6. **Chỉ mục là dữ liệu dẫn xuất:** có thể xóa và rebuild từ Catalog/FAQ; không commit `shared_data/indexes/` hoặc các dữ liệu chứa credentials.
7. **Không nhầm file có tên `approved` với đã phê duyệt:** scripts, ảnh/video và license cần kiểm tra trạng thái và quyền thực trước khi phát hoặc render.

## 4.2. Trạng thái được xác nhận đến 28/10/2026

- **M01:** `ingest_comments`, `load_policy`, `CommentTriage.evaluate`, `CommentQueue.admit/reevaluate/pop` và `make_decision` đã có code được người dùng cung cấp. Unit tests M01 `17/17` pass, contract Part 1 `17/17` pass, full suite `241 passed, 65 subtests passed` theo log chạy local.
- **Runner M01:** 20 comments vào, 16 được bàn giao trong chế độ drain đến giây 188; 4 bị skipped gồm duplicate/spam/off-topic/expired. **Không có SpeechTurn, LLM hoặc TTS nào được tạo trong runner này.**
- **M02:** có dữ liệu 2 SKU, 39 FAQ; phương án modular đã được chốt ở mức kiến trúc. Chưa xác nhận đã có parser/index/retriever chạy được.
- **M03–M05, Orchestration, Part 2/3:** các file trong cây là kiến trúc mục tiêu; cần đối chiếu implementation thực tế và test trước khi xem là hoàn thành.

---

# 5. ROOT DIRECTORY — CẤU HÌNH CHUNG


| File | Công dụng | Input | Output |
|---|---|---|---|
| `.env.example` | Khai báo mẫu biến môi trường | Tên biến, provider, đường dẫn | Mẫu cấu hình cho developer |
| `.gitignore` | Quy định các file không đưa vào Git | Ignore patterns | Repository không chứa file tạm và secrets |
| `README.md` | Giới thiệu và hướng dẫn chạy nhanh | Thông tin project | Tài liệu onboarding |
| `pyproject.toml` | Cấu hình Python package và công cụ | Metadata, dependencies, Ruff | Cấu hình phát triển thống nhất |
| `pytest.ini` | Cấu hình Pytest | Test paths, options | Thiết lập mặc định khi chạy test |
| `requirements.txt` | Hỗ trợ cài môi trường cơ bản | Runtime dependencies | Môi trường Python |
| `requirements-dev.txt` | Hỗ trợ cài công cụ phát triển | Pytest, Ruff và công cụ dev | Môi trường kiểm thử |
| `requirements-gpu.txt` | Phụ thuộc phục vụ GPU worker | PyTorch, lip-sync dependencies | Môi trường xử lý video |


## 5.1. Quy tắc quản lý dependencies


Nhóm cần thống nhất một nguồn khai báo dependencies chính để tránh xung đột phiên bản.


Nếu sử dụng `pyproject.toml` làm nguồn cấu hình chính thì các file requirements nên đóng vai trò hỗ trợ cài đặt.


Môi trường ứng dụng và môi trường GPU có thể dùng phiên bản Python khác nhau khi thư viện lip-sync yêu cầu.


Không bắt buộc cài toàn bộ dependencies GPU trên máy của mọi thành viên.


## 5.2. Quy tắc bảo mật


- Không commit `.env`.
- Không đưa API key thật vào `.env.example`.
- Không commit model weights lớn nếu không cần thiết.
- Không đưa video hoặc giọng nói của người thật lên repository khi chưa được phép.
- Không lưu thông tin nhạy cảm trong log.


---


# 6. `.github/` — CI VÀ QUẢN LÝ CHẤT LƯỢNG


| File/Folder | Công dụng |
|---|---|
| `.github/workflows/` | Lưu cấu hình GitHub Actions |
| `ci.yml` | Tự động kiểm tra code khi push hoặc tạo Pull Request |


CI dự kiến:


1. Cài dependencies cần thiết.
2. Kiểm tra cú pháp và coding style.
3. Chạy unit tests.
4. Chạy contract tests.
5. Chạy integration tests không phụ thuộc GPU.
6. Báo kết quả pass/fail.


Các bài benchmark GPU và kiểm thử chất lượng video có thể được chạy riêng.


Không yêu cầu GitHub Actions chạy model lip-sync nặng trong mỗi Pull Request.


---


# 7. `configs/` — CẤU HÌNH HOẠT ĐỘNG

| File | Công dụng | Trạng thái |
|---|---|---|
| `app.yaml` | Runtime, cấu hình LLM/TTS/provider và đường dẫn nếu được hỗ trợ | Cấu hình app; giá trị model phải kiểm tra với tài khoản API thực tế |
| `demo_scenario.yaml` | Run ID, Active SKU, video nguồn, time window và kịch bản mô phỏng | Dự kiến / chưa xác nhận hoàn thiện |
| `comment_policy.yaml` | Quy tắc duplicate, deferred TTL, queue capacity, fairness, scoring | **M01 đã sử dụng** |
| `rag.yaml` | Tham số FAQ chunking, search top-k, embedding provider, index và eval | **M02 dự kiến, chưa cần API Key ở M02.1–M02.2** |

## 7.1. `app.yaml`

Quản lý cấu hình provider và runtime ở cấp ứng dụng; không chứa secrets. Tách `OPENAI_API_KEY` trong file `.env` không commit. Không mặc định model ID do tài liệu đề xuất là model đã khả dụng trên tài khoản API.

## 7.2. `demo_scenario.yaml`

Kịch bản phiên demo cho `RUN-001` phải liên kết với `RunManifest`, thời điểm bắt đầu UTC và video offset. Mốc mẫu từ FAQ: `2026-10-27T13:00:00Z`. Khung thời gian mục tiêu 120 giây cần được kiểm tra bởi Orchestration, không ép M01 Queue tự phát audio.

## 7.3. `comment_policy.yaml` (M01)

Cấu hình đang được M01 đọc: policy version, duplicate cùng viewer/run trong 30 giây, deferred TTL 30 giây từ `received_at`, giới hạn queue, fairness và điểm theo nhóm từ khóa. Chính sách chọn bình luận **không** phải nguồn bằng chứng về thông số sản phẩm.

## 7.4. `rag.yaml` (M02, đề xuất)

Chứa các nhóm `knowledge`, `lexical`, `embedding`, `retrieval`, `ranking`, `evaluation` và phiên bản chỉ mục khi đã triển khai. Mọi lựa chọn `top_k`, model, phương pháp fusion/rerank phải thử nghiệm; không ghi URL/token bí mật. Với dữ liệu hiện tại (39 FAQ, 2 SKU), ưu tiên index chạy local và có khả năng rebuild.

---

# 8. `shared_data/inputs/` — DỮ LIỆU ĐẦU VÀO VÀ KNOWLEDGE INDEX

| File | Vai trò | Module sử dụng |
|---|---|---|
| `catalog_skus.json` | 2 SKU, giá/tồn kho **giả lập** và thông số cấu trúc | M01 kiểm tra Active SKU; M02 Catalog Repository |
| `product_faq.md` | 39 FAQ gồm gợi ý tư vấn và evidence; **không phải FAQ chính thức hãng** | M02 FAQ Parser/Chunking; M03 Verified Agent |
| `mock_comments.json` | 20 bình luận giả lập của RUN-001 | M01 Comment Ingest |
| `creator_license.json` | Mã tham chiếu cấp phép trong dữ liệu mô phỏng; **không phải chứng nhận đồng ý thực** | Part 2 License Gate |
| `base_operator.mp4` | Video nền liên tục cho phiên demo | Part 2, Part 3 (chưa quay hoàn chỉnh) |
| `approved_product_scripts.json` | 15 kịch bản gợi ý, cần phê duyệt thực trước khi phát | M04 Speech Planner |

## 8.1. `catalog_skus.json` — Structured Source of Truth

Các giá trị trong Catalog được tra trực tiếp theo SKU và field, **không** yêu cầu semantic search để lấy giá, tồn kho hay số liệu kỹ thuật. ASUS `LAPTOP-ASUS-001`: giá demo 26.500.000 VNĐ, 16GB RAM không nâng cấp, SSD 1TB và cờ nâng cấp SSD chưa xác nhận (`null`). Lenovo `LAPTOP-LENOVO-002`: giá demo 25.690.000 VNĐ, 16GB RAM có thể nâng cấp, SSD 512GB có thể nâng cấp. Các thông tin giá/tồn kho không phải báo giá bán hàng thực.

## 8.2. `product_faq.md` — FAQ Knowledge Base

Tài liệu chứa 39 mục: **10 ASUS, 10 Lenovo, 11 Compare, 8 Sales**. Mỗi mục `### FAQ-*` có ID ổn định, SKU, Câu hỏi, Trả lời gợi ý, Hỏi thêm và Bằng chứng. M02.1 parse theo cấu trúc heading, chuẩn bị `FAQChunk` với metadata (ID, SKU liên quan, version và tham chiếu), không fixed-size chunking phá ranh giới FAQ.

**Nguồn trích dẫn:** `faq:FAQ-ASUS-004` tham chiếu FAQ; `catalog:LAPTOP-ASUS-001` tham chiếu Catalog. ID nguồn chỉ cho biết nguồn tồn tại, chưa tự chứng minh mọi mệnh đề trong câu trả lời. Nếu thông tin mâu thuẫn hoặc chưa xác nhận, Agent cần xử lý an toàn thay vì tự suy diễn.

## 8.3. `mock_comments.json`

M01 dùng `run_id`, `viewer_id`, `received_at`, `active_sku_id`. Mốc bắt đầu video `timeline_start_at` và UTC business timestamp cần được ánh xạ rõ ràng khi tạo RunManifest; không dùng thời gian thực máy để tính TTL cho dữ liệu replay lịch sử.

## 8.4. `base_operator.mp4`

Một video nền liên tục với góc quay rõ mặt, điều kiện ánh sáng ổn định, quyền sử dụng hợp lệ. Thời lượng thực khi đã quay là ràng buộc đầu vào của Scheduler/Compositor, không phải kết quả mô phỏng hàng đợi.

## 8.5. `approved_product_scripts.json`

Các script có mã, SKU, nội dung, loại lượt nói và trạng thái phê duyệt. **Chưa coi 15 scripts đã được approved chỉ vì tên file.** Chỉ cho phép phát script khi có bằng chứng phê duyệt phù hợp.

## 8.6. `shared_data/indexes/knowledge/` — Generated Index (M02.3)

Thư mục dự kiến lưu local index, version của source Catalog/FAQ, embedding model ID và checksum để phát hiện index cũ. Không dùng làm nguồn sự thật thay Catalog/FAQ. M02.1–M02.2 có thể chạy hoàn toàn không cần index vector hay API Key. Ignore thư mục này trong Git nếu chứa dữ liệu dẫn xuất lớn.

---

# 9. `shared_data/runs/` — ARTIFACTS CỦA MỘT LẦN CHẠY


Mỗi lần chạy được định danh bằng `run_id`.


Ví dụ:


`shared_data/runs/run_001/`


Các artifact của các lần chạy khác nhau không được ghi đè lên nhau.


## 9.1. `manifest.json`


Được tạo từ `RunManifest`.


Chứa:


- Run ID.
- Base video path.
- Base duration.
- FPS.
- Resolution.
- Active SKU.
- Avatar và license reference.
- Execution mode.
- Output path.


`manifest.json` là nguồn tham chiếu thống nhất cho các bước xử lý.


## 9.2. `step1_agent_audio/`


| File | Nội dung | Schema |
|---|---|---|
| `comment_decisions.json` | Kết quả lọc và chọn comment | CommentDecision |
| `answers.json` | Câu trả lời đã kiểm chứng | AgentResponse |
| `speech_turns.json` | Các lượt lời được phép phát | SpeechTurn |
| `audio/*.wav` | Giọng nói TTS | AudioArtifact |


Không phải mọi CommentEvent đều tạo AgentResponse.


Không phải mọi SpeechTurn đều xuất phát từ AgentResponse.


Ví dụ:


- Product introduction → SpeechTurn → AudioArtifact.
- Selected comment → AgentResponse → SpeechTurn → AudioArtifact.
- Skipped comment → CommentDecision, không sinh lời thoại.


## 9.3. `step2_lipsync/`


| File | Nội dung |
|---|---|
| `render_jobs.json` | Các tác vụ lip-sync |
| `video_artifacts.json` | Metadata kết quả render |
| `overlays/` | Các artifact lip-sync trung gian |


Kết quả Part 2 phải liên kết được với:


- Run ID.
- SpeechTurn.
- AudioArtifact.
- RenderJob.
- Video source.
- Source timestamp.
- Target timestamp.


Các output trong `overlays/` không phải cảnh quay độc lập.


## 9.4. `step3_final/`


| File | Nội dung |
|---|---|
| `hostra_demo.mp4` | Video demo hoàn chỉnh |
| `timeline.json` | Sự kiện theo thời gian |
| `audit_log.json` | Nhật ký kiểm toán |
| `benchmark.json` | Kết quả đo thực tế |


Không được ghi số benchmark giả định vào file kết quả như thể đã được đo.


---


# 10. `core/` — THÀNH PHẦN DÙNG CHUNG


Đường dẫn:


`src/hostra_ai/core/`


| File | Input | Output | Chức năng |
|---|---|---|---|
| `config.py` | Environment, YAML | Settings | Đọc và kiểm tra cấu hình |
| `logging.py` | Log events | Structured logs | Logging theo run_id |
| `schemas/common.py` | Shared definitions | Constants, Enum | Quy tắc chung |
| `schemas/part1.py` | Part 1 data | Pydantic models | Contracts Part 1 |
| `schemas/part2.py` | Part 2 data | Pydantic models | Contracts Part 2 |
| `schemas/part3.py` | Part 3 data | Pydantic models | Contracts Part 3 |
| `schemas/__init__.py` | Các schema | Package exports | Cung cấp import thống nhất |


## 10.1. Bộ 10 schema


### Part 1


1. CommentEvent
2. CommentDecision
3. AgentResponse
4. SpeechTurn
5. AudioArtifact


### Part 2


6. RenderJob
7. VideoArtifact


### Part 3


8. RunManifest
9. TimelineEvent
10. AuditRecord


## 10.2. `common.py`


Chứa những thành phần thực sự được chia sẻ:


- ID validation patterns.
- Shared Enum hoặc Literal definitions khi cần.
- Reason codes dùng chung.
- Validation helpers thực sự tái sử dụng.


Không đặt business logic hoặc logic gọi provider trong `common.py`.


## 10.3. Quy tắc schema


- Dùng Pydantic v2.
- Tên trường dùng snake_case.
- ID phải tuân thủ định dạng đã thống nhất.
- Timestamp có timezone.
- Thời lượng ghi đơn vị rõ ràng, ưu tiên mili giây.
- Trạng thái dùng Enum hoặc Literal khi phù hợp.
- Không chấp nhận field ngoài contract nếu schema quy định `extra="forbid"`.
- Không tự ý thay đổi field đang được module khác sử dụng.
- Khi đổi contract phải cập nhật unit/contract tests.


Chi tiết từng field nằm trong:


`docs/data_contract_vi.md`


---


# 11. PART 1 — COMMENT, KNOWLEDGE, VERIFIED AGENT & TTS

**Đường dẫn:** `src/hostra_ai/part1_agent_tts/`.

## 11.1. Trách nhiệm và ranh giới

Part 1 cung cấp các năng lực theo milestone: M01 xử lý comment và queue, M02 tìm bằng chứng, M03 sinh và kiểm chứng câu trả lời, M04 chuẩn bị SpeechTurn/TTS và M05 tích hợp/đánh giá. Không coi comment được `selected` là đã được trả lời/phát.

## 11.2. Bảng module cấp Part 1

| Module | Input | Output | Milestone |
|---|---|---|---|
| `comment_ingest.py` | Mock comments, run ID, catalog SKU | `list[CommentEvent]` | M01, đã code |
| `comment_policy.py` | `comment_policy.yaml` | `CommentPolicy` nội bộ | M01, đã code |
| `comment_decisions.py` | CommentEvent, action/reason/score/clock | `CommentDecision` | M01, đã code |
| `comment_triage.py` | CommentEvent, CommentPolicy | `CommentDecision` | M01, đã code |
| `comment_queue.py` | CommentEvent, CommentDecision, clock | `QueueItem`, decision history | M01, đã code |
| `knowledge_engine.py` | Query, SKU, Catalog/FAQ | Evidence / lookups | M02, facade |
| `knowledge/models.py` | Knowledge data | FAQChunk / RetrievedEvidence | M02.1 |
| `knowledge/catalog_repository.py` | Catalog JSON | Structured field lookup | M02.1 |
| `knowledge/faq_parser.py` | FAQ Markdown | Parsed FAQ records | M02.1 |
| `knowledge/chunking.py` | Parsed FAQ | FAQChunk + metadata | M02.1 |
| `knowledge/lexical_retriever.py` | Query + chunks | Ranked lexical candidates | M02.2 |
| `knowledge/embedding_provider.py` | Text + embedding config | Vectors | M02.3 |
| `knowledge/vector_index.py` | Vectors + metadata | Similarity candidates | M02.3 |
| `knowledge/retriever.py` | Query, filters, index/candidates | Combined evidence | M02.4 |
| `knowledge/ranker.py` | Candidate evidence | Ranked evidence | M02.4 |
| `conversation_memory.py` | run_id, viewer_id, events | Conversation context | M03 |
| `verified_agent.py` | Selected comment + memory + evidence | Candidate answer; sau verification mới có AgentResponse | M03 |
| `answer_verifier.py` | Candidate + Catalog/FAQ evidence | Verification/allowed response | M03 |
| `speech_planner.py` | Verified answer / approved script | SpeechTurn | M04 |
| `tts_provider.py` | SpeechTurn | WAV, AudioArtifact | M04 |
| `pipeline.py` | Part 1 inputs | Part 1 artifacts | M05 |

## 11.3. M01 — Comment Processing (đã kiểm thử chức năng)

Thứ tự thực thi:

```text
mock_comments.json + Catalog SKU -> ingest_comments()
  -> CommentEvent -> CommentTriage.evaluate()
  -> CommentDecision -> CommentQueue.admit()
  -> reevaluate(now) / pop(now) -> QueueItem
```

M01 dùng **rule-based**: duplicate cùng run/viewer/text chuẩn hóa trong cửa sổ 30 giây (gồm biên), spam bảo thủ, off-topic bảo thủ, priority 0–100, queue capacity 5, deferred TTL 30 giây, fairness giữa viewers. `now` là **simulation clock**. Factory `make_decision()` tạo ID riêng cho mỗi thay đổi quyết định. Queue lưu `_ready`, `_deferred`, `_terminal`; `pop()` không đồng nghĩa AI Agent đã trả lời thành công.

**Runner đang sử dụng:** `scripts/script_part1/run_milestone01.py`, một lượt `pop` mỗi 12 giây, drain queue đến rỗng. Theo log thực tế: 20 đầu vào, 16 handed-off, 4 skipped; 17 bài unit M01, 17 contract Part1, full suite 241 tests và 65 subtests đạt. Video mục tiêu 120 giây **chưa áp dụng** cho runner này.

## 11.4. M02 — Modular Knowledge Engine & RAG (đang triển khai)

**Nguyên tắc:** Catalog là nguồn structured truth cho giá, tồn kho, thông số; FAQ là kiến thức giải thích có thể search. Không dùng vector similarity để quyết định số tiền, không coi FAQ gợi ý là phát ngôn đã kiểm chứng.

### M02.1. Preparation / Chunking

- Parse `product_faq.md` theo heading `### FAQ-*`: **1 FAQ = 1 chunk**, giữ đủ question, answer suggestion, follow-up, nguồn và SKU metadata.
- Catalog lookup trực tiếp theo SKU / field, giữ `null` là chưa xác nhận; kiểm tra SKU trùng hoặc tham chiếu sai.
- Models nội bộ: `FAQChunk` và `RetrievedEvidence`; schema hiện có trong `core/schemas/part1.py` không thay đổi.
- Đọc dữ liệu và test hoàn toàn offline, không cần embeddings/LLM.

### M02.2. Lexical Retrieval Baseline

- Keyword/BM25 retrieval trên 39 chunks; tạo bộ câu hỏi kiểm thử cùng expected relevant FAQ IDs; đánh giá Recall@K/MRR; không cần API Key.

### M02.3. Embeddings & Vector Index

- Embedding provider có thể thay thế; chỉ gọi API khi có khóa hợp lệ hoặc chọn model local tương thích. Cache/index có phiên bản và checksum, không embed lại mỗi comment.

### M02.4. Routing, Hybrid Retrieval & Ranking

- Query router quyết định Catalog direct lookup, FAQ retrieval hoặc kết hợp; khi so sánh 2 SKU phải lấy evidence cả 2. Hybrid fusion và reranking chỉ dùng nếu thử nghiệm tốt hơn baseline.

### M02.5. Evaluation & Evidence Handoff

- Đánh giá kết quả retrieval theo các câu hỏi từ mock comments và tập golden questions (giá, RAM, so sánh, thiếu benchmark, chính sách chưa xác nhận).
- Đầu ra có `ref`, `source_type`, `sku_ids`, `content`, `score`, `source_version` nếu khả dụng.
- Evidence cho M03 được truyền thông qua `knowledge_engine.py` facade; **không gọi LLM generation trong M02**.

### Chú ý FAQ và Evidence

Các mục `FAQ-ASUS-*`, `FAQ-LENOVO-*`, `FAQ-COMPARE-*`, `FAQ-SALES-*` không tự bảo đảm các mệnh đề bên trong đúng. `faq:FAQ-COMPARE-003` và `catalog:LAPTOP-ASUS-001` là refs, không phải verification verdict. Với source bị mâu thuẫn hoặc giá trị thiếu, Agent phải báo không đủ căn cứ hoặc yêu cầu xác minh.

## 11.5. M03 — Verified AI Agent / Observation / Conversation Memory

Agent nhận **CommentEvent đã được Queue bàn giao**, kèm run/viewer context; có thể dùng QueueItem ở ranh giới orchestration nhưng không khóa Agent vào implementation `_ready`/`_deferred`. Agent phân giải câu hỏi tiếp nối (ví dụ viewer đang hỏi Lenovo mặc dù Active SKU là ASUS), gọi Knowledge Engine rồi tạo ứng viên câu trả lời. Deterministic Answer Verifier kiểm tra các facts và policy; chỉ output đã xác minh mới được đóng gói thành `AgentResponse.status="answered"`. Khi thiếu dữ liệu dùng `clarification_needed` hoặc `blocked` theo contract.

## 11.6. M04 — Speech Planner & TTS

Ba loại lời thoại: `product_intro` từ script thực sự đã duyệt, `comment_reply` từ AgentResponse hợp lệ và `safe_fallback` từ kịch bản dự phòng an toàn. Scheduler admission chọn SpeechTurn hợp lệ để TTS tổng hợp; TTS tạo file WAV mono hợp lệ, đo thời lượng thực, xuất AudioArtifact; final scheduling mới đặt phát vào video. Không phát nội dung `AgentResponse` đang blocked.

## 11.7. M05 — Integration & Evaluation

Kiểm thử: comment → evidence → verified AgentResponse → SpeechTurn → AudioArtifact; đánh giá FAQ retrieval Recall@K, groundedness/verification, các trường hợp không biết, chi phí provider, thời lượng WAV và đúng mốc video. Benchmark chỉ dùng số đo thực, phân biệt simulation delay và latency inference.

## 11.8. Public Contracts và internal models

Các public contracts của Part 1 vẫn là **CommentEvent, CommentDecision, AgentResponse, SpeechTurn, AudioArtifact**. Internal `QueueItem`, `CommentPolicy`, `FAQChunk`, `RetrievedEvidence` được phép tách module riêng để dễ kiểm thử nhưng không tự ý bổ sung field vào public contract. `AgentResponse.evidence_refs` phải tham chiếu nguồn có thật và kiểm tra claim-level ở Verifier.

---

# 12. ORCHESTRATION — SPEECH SCHEDULER

**Đường dẫn mục tiêu:** `src/hostra_ai/orchestration/speech_scheduler.py`.

## 12.1. Mục tiêu và ranh giới

Scheduler quản lý thời điểm phát, mức ưu tiên speech (khác `CommentDecision.priority_score`), không cho audio chồng nhau, và giữ tất cả sự kiện trong độ dài video nền. Scheduler không được biến mọi comment `selected` thành lượt nói và không tự kiểm chứng dữ liệu sản phẩm.

## 12.2. Thiết kế hai giai đoạn (đề xuất khi tích hợp)

1. **Admission Scheduling:** chọn SpeechTurn cần tổng hợp dựa trên policy, tình trạng audio/queue và giới hạn video; chỉ gọi TTS cho những lượt được chấp nhận.
2. **TTS:** tổng hợp WAV, kiểm tra file thật và đo `duration_ms` để tạo AudioArtifact.
3. **Final Scheduling:** đặt start/end time theo thời lượng thực, không phát trước comment, không chồng lời, không vượt video; xuất kế hoạch cho Part 2/3.

Interface và cách xử lý speech bị loại sau TTS cần nhóm chốt khi triển khai M04–M05. Không dùng giả định "mỗi comment chiếm 12 giây" của runner M01 làm thời lượng speech.

## 12.3. Quy tắc bắt buộc

- Không phát các SpeechTurn trùng giờ và không cắt ngang lời thoại không có điểm ngắt hợp lệ.
- Không phát trả lời trước thời điểm comment xuất hiện.
- Không vượt độ dài video nền; kiểm tra liên kết RunManifest/video timeline.
- Không phát câu trả lời bị blocked hoặc script chưa approved.
- Ưu tiên speech và fairness là chính sách lịch phát, không dùng trực tiếp `CommentDecision.priority_score` như thời lượng hoặc điểm xác minh.
- Mốc business UTC và relative time `ms` phải ánh xạ từ `timeline_start_at` rõ ràng.

## 12.4. Ví dụ minh họa (không phải timeline đã chạy)

Video nguồn dài 120 giây; lời giới thiệu được admission, sau đó comment phù hợp được Agent trả lời, TTS sinh WAV và final scheduler quyết định vị trí phát. Lời thoại không đủ thời gian ở cuối video bị xử lý theo chính sách đã thống nhất, **không kéo dài video hoặc tự nối các clip nguồn rời**.

---

# 13. PART 2 — TIME-ALIGNED VIDEO LIP-SYNC


Đường dẫn:


`src/hostra_ai/part2_video_lipsync/`


## 13.1. Mục tiêu


Part 2 nhận audio đã được lên lịch và video nền.


Hệ thống tạo kết quả lip-sync tại đúng những khung hình cần thiết.


Part 2 không chịu trách nhiệm ghép toàn bộ video cuối.


## 13.2. Chức năng từng file


| File | Input | Output | Chức năng |
|---|---|---|---|
| `license_gate.py` | License, avatar, scope | License decision | Kiểm tra quyền sử dụng |
| `frame_mapper.py` | Timestamp, FPS | Frame range | Ánh xạ thời gian sang frame |
| `lipsync_adapter.py` | Audio, source frames | Lip-sync output | Kết nối lip-sync provider |
| `artifact_validator.py` | VideoArtifact, media file | Validation result | Kiểm tra output |
| `render_service.py` | RenderJobs | VideoArtifacts | Điều phối các tác vụ render |


## 13.3. License Gate


Phải kiểm tra giấy phép trước khi render.


Kiểm tra:


- Avatar ID.
- Quyền sử dụng hình ảnh.
- Quyền sử dụng giọng nói.
- Thời hạn.
- Phạm vi sử dụng.
- Mục đích được phép.


Nếu không hợp lệ, hệ thống phải từ chối render.


## 13.4. Frame Mapper


Nhận timestamp từ Speech Scheduler.


Xác định:


- Source start.
- Target start.
- Duration.
- Frame range.


Không để kết quả lip-sync bị lệch so với vị trí trên video nền.


## 13.5. Lip-sync Adapter


Cung cấp giao diện chung để sử dụng các provider hoặc model khác nhau.


Có thể sử dụng GPU local hoặc GPU worker bên ngoài.


Output cần được chuẩn hóa thành VideoArtifact.


## 13.6. Artifact Validator


Kiểm tra:


- File có tồn tại.
- File đọc được.
- Format hợp lệ.
- Duration hợp lệ.
- FPS hợp lệ.
- Resolution phù hợp.
- Metadata thời gian chính xác.
- Audio/video synchronization theo các phép đo được hỗ trợ.


Một file MP4 tồn tại không đồng nghĩa đã render thành công.


## 13.7. Nguyên tắc video nền liên tục


Kết quả Part 2 phải được căn chỉnh với các frame gốc.


Part 3 chỉ áp dụng phần chỉnh sửa cần thiết tại đúng vị trí.


Không dùng phương pháp nối tuần tự các video clip độc lập làm cơ chế dựng cuối.


---


# 14. PART 3 — CONTINUOUS VIDEO COMPOSITOR


Đường dẫn:


`src/hostra_ai/part3_demo_compositor/`


## 14.1. Mục tiêu


Part 3 sử dụng video nền và các artifact được tạo trước đó để xuất một video demo liên tục.


## 14.2. Chức năng từng file


| File | Input | Output | Chức năng |
|---|---|---|---|
| `run_manager.py` | Run config, inputs | RunManifest | Quản lý phiên demo |
| `timeline_builder.py` | Speech plan, comments, artifacts | TimelineEvent | Xây dựng timeline |
| `timeline_validator.py` | TimelineEvents, RunManifest | Validation result | Kiểm tra timeline |
| `video_compositor.py` | Base video, overlays, audio, timeline | Final MP4 | Tổng hợp video |
| `audit_service.py` | Processing events | AuditRecord | Ghi nhật ký |
| `benchmark_collector.py` | Measured metrics | Benchmark data | Thu thập số đo |
| `teleprompter.py` | SKU, timeline, action cues | Operator cues | Hỗ trợ nhắc thao tác |


## 14.3. Run Manager


Khởi tạo và quản lý một lần chạy.


RunManifest phải xác định:


- Run ID.
- Video nền.
- Thời lượng.
- FPS.
- Resolution.
- Active SKU.
- Avatar.
- License reference.
- Output path.


RunManifest cần được tạo hoặc xác thực trước các tác vụ phụ thuộc vào thông số video.


## 14.4. Timeline Builder


Xây dựng các sự kiện như:


- Comment xuất hiện.
- Lời giới thiệu được phát.
- Câu trả lời được phát.
- Cue liên quan sản phẩm nếu cần.


TimelineEvent không đại diện cho việc nối cảnh quay.


Nó đại diện cho các sự kiện diễn ra trên một video nền duy nhất.


## 14.5. Timeline Validator


Kiểm tra:


1. Start time nhỏ hơn end time.
2. Event nằm trong thời lượng video.
3. Không chồng lời thoại.
4. Không phát trả lời trước bình luận.
5. Audio và video artifact có tham chiếu hợp lệ.
6. SKU nhất quán.
7. Các khoảng thời gian phát có thể thực thi.


Validation giữa nhiều sự kiện phải được xử lý ở cấp timeline tổng thể.


## 14.6. Video Compositor


Video Compositor phải:


1. Sử dụng base_operator.mp4 làm video hình ảnh chính.
2. Giữ nguyên timeline của video gốc.
3. Áp dụng kết quả chỉnh sửa khuôn mặt tại thời điểm cần thiết.
4. Trộn audio TTS.
5. Hiển thị comment overlay nếu cấu hình yêu cầu.
6. Đảm bảo đồng bộ âm thanh và hình ảnh.
7. Xuất video cuối.


Output:


`hostra_demo.mp4`


Không được cắt bỏ những khoảng thời gian không có lời thoại chỉ để nối các đoạn nói lại với nhau.


## 14.7. Audit Service


Ghi nhận:


- Comment decisions.
- Verification results.
- Speech scheduling.
- License decisions.
- Render results.
- Timeline validation.
- Final export results.


Audit phải cho phép truy vết lỗi nhưng không làm lộ thông tin nhạy cảm.


## 14.8. Benchmark Collector


Thu thập:


- Agent processing time.
- TTS processing time.
- Render time.
- Video duration.
- FPS.
- Audio/video synchronization.
- Số comment được nhận.
- Số comment được chọn.
- Số comment được bỏ qua.
- Tỷ lệ câu trả lời vượt qua verification.
- Lỗi pipeline.


Các chỉ số phải được phân biệt giữa:


- Thời gian xử lý offline thực tế.
- Kết quả benchmark GPU.
- Mục tiêu realtime tương lai.


Không coi thời gian chờ được mô phỏng trong video là latency inference thực tế.


## 14.9. Teleprompter


Teleprompter giúp xác định:


- SKU đang giới thiệu.
- Nội dung tiếp theo.
- Thao tác mong muốn của operator.
- Trạng thái lời thoại.


Trong PoC quay sẵn, module này có thể chỉ quản lý cue theo kịch bản.


Điều khiển operator vật lý theo thời gian thực là hướng phát triển sau.


---


# 15. `api/` — BACKEND DEMO


Đường dẫn:


`src/hostra_ai/api/`


| File | Chức năng |
|---|---|
| `app.py` | Khởi tạo FastAPI application |
| `routes.py` | Các HTTP endpoint |


API phục vụ:


- Danh sách run.
- Trạng thái run.
- Video output.
- Product information.
- Comment decisions.
- Timeline.
- Audit summary.
- Benchmark results.


API không tự thực thi business logic của Agent hoặc Video Compositor.


Các endpoint nên gọi lại service tương ứng.


---


# 16. `web/` — FRONTEND DEMO


| File | Công dụng |
|---|---|
| `index.html` | Cấu trúc giao diện |
| `styles.css` | Giao diện và responsive |
| `app.js` | Logic tương tác và API calls |


## 16.1. Các khu vực giao diện dự kiến


1. Video Demo Player.
2. Product Information.
3. Mock Comment Feed.
4. Comment Selection Status.
5. AI Speech/Answer Display.
6. Pipeline Status.
7. Audit Summary.
8. Benchmark Summary.


## 16.2. Quy tắc đồng bộ giao diện


Nếu bình luận được hiển thị trong giao diện web thay vì ghi trực tiếp vào MP4, thời gian xuất hiện của comment phải căn chỉnh với thời gian phát video.


Giao diện không được tự đặt thời điểm comment khác với timeline đã được tạo.


## 16.3. Giới hạn của demo offline


Khi phát một MP4 đã render sẵn, việc nhập comment mới vào giao diện không thể tự động thay đổi khẩu hình của video đã xuất.


Muốn hỗ trợ comment mới trong lúc video đang phát sẽ cần pipeline render/streaming tương tác ở giai đoạn tiếp theo.


---


# 17. `notebooks/` — MÔI TRƯỜNG GPU


| File | Chức năng |
|---|---|
| `colab_lipsync_worker.ipynb` | Chạy lip-sync experiments hoặc worker trên Google Colab |


Notebook nhận:


- Base video hoặc cửa sổ frame nguồn.
- Audio artifact.
- RenderJob.
- Configuration.


Output:


- Lip-sync artifacts.
- Render metadata.
- Thông tin lỗi hoặc kết quả xử lý.


Notebook phải tuân thủ cùng data contract với backend.


Không tự tạo cấu trúc JSON riêng không tương thích với Pydantic schemas.


Môi trường GPU có thể được cài độc lập với môi trường backend.


---


# 18. `scripts/` — CÁC LỆNH THỰC THI

| Script | Mục tiêu | Trạng thái |
|---|---|---|
| `scripts/script_part1/run_milestone01.py` | Demo ingest → triage → queue, drain toàn bộ queue | **Đã chạy local** |
| `scripts/run_milestone02.py` | M02: load Catalog, FAQ chunks và in Retrieval results | Đề xuất |
| `scripts/validate_inputs.py` | Kiểm tra dữ liệu và chính sách đầu vào | Theo backlog |
| `scripts/run_part1.py` | Tạo artifact Part 1 (Agent/TTS) | Theo backlog |
| `scripts/prepare_lipsync.py` | Chuẩn bị RenderJob | Theo backlog |
| `scripts/import_lipsync.py` | Import/validate VideoArtifact | Theo backlog |
| `scripts/run_demo.py` | Điều phối PoC end-to-end | Theo backlog |

## 18.1. Quy tắc chung

Scripts chỉ là entry point; business logic ở `src/hostra_ai/`. Không sao chép thuật toán Triage/Queue/Retrieval vào runner. M01 runner tự gắn simulation clock và hiển thị kết quả; không tạo SpeechTurn hoặc file WAV.

## 18.2. Lệnh chạy M01 đã kiểm chứng từ môi trường người dùng

```powershell
python -m pytest tests/unit/test_part1_code -v
python -m pytest tests/contract/test_part1_contract.py -v
python -m pytest -q
python scripts/script_part1/run_milestone01.py
```

## 18.3. M02 sẽ có hai luồng thực thi

- **Preparation/indexing:** parse Catalog/FAQ, chunk, xây lexical index; sau đó mới tùy chọn embedding/index vector; chỉ cần rebuild khi nguồn hoặc config có thay đổi.
- **Online retrieval:** query + SKU context → Catalog lookup/FAQ retrieval → ranked evidence; không gọi LLM trong runner M02.

## 18.4. Pipeline tổng thể

`src/hostra_ai/pipeline.py` giữ vai trò điều phối toàn ứng dụng khi đã tích hợp; `scripts/run_demo.py` chỉ gọi pipeline với cấu hình, không thay thế nó.

---

# 19. `tests/` — HỆ THỐNG KIỂM THỬ

## 19.1. Cấu trúc test phù hợp repository hiện tại

```text
tests/
├── unit/
│   ├── test_part1.py                  # Kiểm tra schemas Part 1
│   ├── test_part2.py
│   ├── test_part3.py
│   └── test_part1_code/
│       ├── test_comment_ingest.py     # M01 đã chạy
│       ├── test_comment_triage.py     # M01 đã chạy
│       ├── test_comment_queue.py      # M01 đã chạy
│       ├── test_catalog_repository.py # M02.1 dự kiến
│       ├── test_faq_parser.py         # M02.1 dự kiến
│       ├── test_chunking.py           # M02.1 dự kiến
│       ├── test_lexical_retriever.py  # M02.2 dự kiến
│       ├── test_vector_index.py       # M02.3 dự kiến
│       └── test_ranker.py             # M02.4 dự kiến
├── contract/
│   ├── test_part1_contract.py
│   ├── test_part2_contract.py
│   └── test_part3_contract.py
├── integration/
│   ├── test_comment_processing.py    # Khi cần test M01 end-to-end
│   ├── test_knowledge_engine.py      # M02 dự kiến
│   ├── test_part1_pipeline.py
│   ├── test_part2_pipeline.py
│   ├── test_part3_pipeline.py
│   └── test_demo_pipeline.py
└── fixtures/
    ├── part1/
    ├── part2/
    └── part3/
```

Các file `dự kiến` chưa chắc đã tồn tại. Không xóa hoặc di chuyển test M01 chỉ để làm cây đẹp.

## 19.2. Unit Tests

- **M01:** validation ingest, duplicate window, spam/off-topic, priority, queue admission, TTL, FIFO và fairness.
- **M02.1:** parse đủ 39 FAQ (10/10/11/8), ID và SKU hợp lệ, multi-SKU compare, Catalog lookup giữ `null`, từ chối tham chiếu không rõ.
- **M02.2:** câu hỏi/FAQ relevant ID, lexical retrieval regression.
- **M02.3:** vector shape, top-k, index version, stale index và offline fake embedding provider.
- **M02.4:** filter SKU, fusion/ranking, evidence traceability và missing data.
- **M03/M04:** verification, multi-turn memory, blocked/fallback, SpeechTurn và audio file validation.

## 19.3. Contract Tests

Giữ nguyên test cho 10 public schemas, serialization, required/nullable fields, timestamps, ID reference. M02 internal models không làm thay đổi schema công khai nếu chưa có yêu cầu tích hợp được chốt.

## 19.4. Integration Tests

- M01: replay 20 mock comments deterministic theo event time, không dùng wall-clock.
- M02: load Catalog + 39 FAQ + retrieval, không phụ thuộc API Key trong baseline.
- M03–M05: comment → evidence → verified response → speech → artifact; mock các external providers trong CI.

## 19.5. Kết quả đã ghi nhận (không phải chạy lại trong lần sửa tài liệu)

Theo log từ máy Windows Python 3.13.2: M01 unit 17 passed, Part1 contract 17 passed, full suite **241 passed, 65 subtests passed**. Đây là kết quả kiểm thử **trước thay đổi M02**, không phải tuyên bố M02 đã có bài test đạt.

## 19.6. Lệnh chạy

```powershell
python -m pytest tests/unit/test_part1_code -v
python -m pytest tests/contract/test_part1_contract.py -v
python -m pytest -q
python scripts/script_part1/run_milestone01.py
```

## 19.7. Quy tắc regression

Không sửa/xóa unit/contract tests cũ chỉ để pass; thay đổi schema công khai bắt buộc có review. Không trộn refactor M01 với triển khai M02 trong một PR nếu không có lý do.

---

# 20. DATA CONTRACT GIỮA CÁC MODULE

| Producer | Consumer | Dữ liệu / Ranh giới |
|---|---|---|
| Comment Ingest | Comment Triage | `CommentEvent` |
| Comment Triage | Comment Queue | `CommentDecision` + CommentEvent |
| Comment Queue | Orchestration → Verified Agent | `QueueItem` nội bộ; Agent nhận CommentEvent đã được bàn giao kèm context |
| FAQ Parser / Chunking | Knowledge Retrieval | `FAQChunk` và metadata nội bộ |
| Catalog Repository | Knowledge Engine | Structured facts, `catalog:<SKU>` |
| Lexical / Vector Retriever | Ranker / Knowledge Engine | Evidence candidates và retrieval scores |
| Knowledge Engine (facade) | Verified Agent / Answer Verifier | `RetrievedEvidence` có refs, SKU, version, provenance |
| Conversation Memory | Verified Agent | Lịch sử theo run_id/viewer_id, tham chiếu SKU nếu có |
| Verified Agent + Verifier | Speech Planner | `AgentResponse` đã được kiểm chứng |
| Approved Product Scripts | Speech Planner | Approved script, phải kiểm tra trạng thái duyệt |
| Speech Planner | Orchestration: Admission | `SpeechTurn` |
| Orchestration: Admission | TTS Provider | SpeechTurn được phép tổng hợp |
| TTS Provider | Orchestration: Final Scheduling | `AudioArtifact` và thời lượng WAV thực |
| Run Manager | Orchestration/Part2/Part3 | `RunManifest` và mốc `timeline_start_at` |
| Final Scheduling | Part 2 Render Service / Part 3 Timeline | Speech schedule và thời điểm audio |
| Render Service | Lip-sync Adapter | `RenderJob` |
| Lip-sync Adapter | Video Compositor | `VideoArtifact` |
| Timeline Builder | Video Compositor | `TimelineEvent` |
| Pipeline | Audit / Benchmark | Run events và số đo thực |

## 20.1. Traceability

```text
CommentEvent -> CommentDecision -> (QueueItem delivered)
  -> [Knowledge Evidence + Conversation Memory]
  -> AgentResponse (verified) -> SpeechTurn
  -> AudioArtifact -> RenderJob -> VideoArtifact
  -> TimelineEvent -> hostra_demo.mp4
```

**Ngoại lệ:** Product intro không có CommentEvent/AgentResponse bắt buộc; được tạo từ script đã duyệt. Skipped comment chỉ có quyết định, không sinh speech. Evidence refs là dữ liệu nội bộ nhưng khi `AgentResponse.status="answered"`, `evidence_refs` phải chứa nguồn truy vết hợp lệ và được Verifier kiểm tra nội dung hỗ trợ claim.

## 20.2. Không nhầm các loại ưu tiên hoặc thời gian

- `priority_score` ở CommentDecision điều khiển ưu tiên Queue, không phải speech priority.
- `received_at` là UTC nghiệp vụ; video offset tính theo `timeline_start_at`.
- `QueueItem` được `pop` không đồng nghĩa được phát; Speech Scheduler sử dụng thời lượng WAV thực và giới hạn video.

---

# 21. QUY TẮC CHỌN LỌC BÌNH LUẬN


## 21.1. Mục tiêu


Không xử lý toàn bộ comment khi lưu lượng bình luận tăng cao.


Hệ thống phải chọn câu hỏi phù hợp với:


- Sản phẩm đang giới thiệu.
- Nội dung cần được giải đáp.
- Độ ưu tiên.
- Thời gian còn lại.
- Giới hạn xử lý.


## 21.2. Luồng xử lý


1. Nhận CommentEvent.
2. Kiểm tra hợp lệ.
3. Lọc spam hoặc nội dung không phù hợp.
4. Phát hiện câu hỏi trùng.
5. Chấm điểm ưu tiên.
6. Quyết định selected/deferred/skipped/escalated.
7. Đưa comment phù hợp sang Agent.
8. Lưu CommentDecision và AuditRecord.


## 21.3. Chính sách hàng đợi


Hàng đợi cần có giới hạn.


Những comment không còn phù hợp sau khi chờ quá lâu có thể được đánh dấu hết hạn.


Không để comment cũ của SKU trước tiếp tục được trả lời như thể thuộc SKU hiện tại.


Không để một viewer gửi liên tục và chiếm toàn bộ lượt phát biểu.


## 21.4. Phân biệt lựa chọn và trả lời


Comment được selected không đồng nghĩa chắc chắn sẽ có câu trả lời phát ra.


Agent vẫn phải thực hiện verification.


Nếu không đủ bằng chứng hoặc không đáp ứng policy, AgentResponse có thể bị blocked hoặc yêu cầu làm rõ.


Những trường hợp này không được tự động gửi TTS.


---


# 22. QUY TẮC ĐỒNG BỘ VIDEO VÀ AUDIO


## 22.1. Video nền duy nhất


RunManifest xác định video nền.


Các RenderJob phải tham chiếu đúng nguồn video của run.


## 22.2. Mốc thời gian


Dùng mili giây để biểu diễn:


- Comment appearance time.
- Speech start.
- Speech end.
- Render source window.
- Render target window.
- Timeline events.


## 22.3. Không phát chồng audio


Hai lời thoại chính không được có khoảng phát trùng nhau.


## 22.4. Không vượt thời lượng video


Mọi speech event phải nằm trong thời lượng video nền.


Nếu audio không còn đủ thời gian, Scheduler phải xử lý trước khi render.


## 22.5. Giữ tính liên tục


Compositor không được loại bỏ các đoạn không có lời thoại.


Phải kiểm tra:


- Video không bị nhảy cảnh ngoài kịch bản.
- Chuyển động nền liên tục.
- Thời lượng đúng.
- FPS phù hợp.
- Audio/video đồng bộ.
- Điểm chuyển giữa khuôn mặt gốc và khuôn mặt đã chỉnh sửa đủ tự nhiên.


---


# 23. `docs/` — TÀI LIỆU DỰ ÁN


| File | Chức năng |
|---|---|
| `architecture.md` | Kiến trúc tổng thể và luồng xử lý |
| `project_structure.md` | Cây thư mục và chức năng từng file |
| `data_contract_vi.md` | Đặc tả 10 Pydantic schemas |
| `setup_guide.md` | Hướng dẫn môi trường và chạy project |
| `test_plan.md` | Kế hoạch kiểm thử |
| `benchmark.md` | Phương pháp và kết quả benchmark |
| `demo_script.md` | Kịch bản trình diễn PoC |


## 23.1. Phân biệt architecture.md và project_structure.md


`architecture.md` trả lời:


- Hệ thống hoạt động như thế nào?
- Dữ liệu đi qua những module nào?
- Các module tương tác ra sao?
- Cơ chế chọn comment và đồng bộ video hoạt động thế nào?


`project_structure.md` trả lời:


- File nằm ở đâu?
- File có chức năng gì?
- Input và Output của file là gì?
- Module nào chịu trách nhiệm?


Không nên duy trì hai tài liệu có nội dung trùng lặp hoàn toàn.


---


# 24. QUY ƯỚC CHUNG


## 24.1. Quy tắc đặt tên


- Python modules: snake_case.
- JSON fields: snake_case.
- Class names: PascalCase.
- Constants: UPPER_SNAKE_CASE.
- Test files: test_*.py.
- ID: Theo pattern đã thống nhất trong core schemas.


## 24.2. Quy tắc timestamp


Timestamp nghiệp vụ sử dụng timezone rõ ràng, ưu tiên UTC.


Timestamp tương đối trên video dùng mili giây.


Không sử dụng lẫn hai loại thời gian.


## 24.3. Quy tắc artifact


- Nhóm output theo run_id.
- Không ghi đè artifact của run khác.
- Artifact metadata phải tham chiếu được nguồn.
- Không dùng tên file làm định danh nghiệp vụ.
- shared_data/runs/ phải được gitignore.


## 24.4. Quy tắc bảo mật


- Không commit secrets.
- Không lưu video/voice chưa được phép sử dụng.
- Không log thông tin cá nhân không cần thiết.
- Không sử dụng dữ liệu giả lập như dữ liệu khách hàng thật.
- Không tự động phát nội dung chưa được kiểm chứng.


## 24.5. Quy tắc phát triển


- Một module có trách nhiệm chính rõ ràng.
- Logic nghiệp vụ nằm trong src/.
- Scripts chỉ gọi lại logic.
- API không chứa business logic phức tạp.
- Provider bên ngoài phải dễ mock.
- Mỗi thay đổi contract phải có test.
- Pull Request cần được review trước khi merge.


---


# 25. THỨ TỰ TRIỂN KHAI ĐỀ XUẤT — SAU KHI CÓ M01

| Giai đoạn | Công việc | Trạng thái/đầu ra |
|---|---|---|
| Foundation | 10 public Pydantic contracts, input data, pytest | Đã có các contract tests được chạy local |
| **M01** | Comment Ingest + Policy + Decisions + Triage + Queue | **Hoàn thành kiểm thử chức năng** (20 comments, 16 handed off ở chế độ drain) |
| **M02.1** | Catalog Repository + FAQ Parser + Chunking + models nội bộ | Tiếp theo; 2 SKU, 39 FAQ |
| **M02.2** | Keyword/BM25 baseline + retrieval eval | Chưa triển khai |
| **M02.3** | Embedding provider + local Vector Index | Chưa triển khai; phụ thuộc lựa chọn model/provider |
| **M02.4** | Hybrid Routing / Retrieval / Ranking | Chưa triển khai |
| **M02.5** | Evidence validation, benchmark Recall@K, handoff facade | Chưa triển khai |
| **M03** | Conversation Memory + Verified Agent + Answer Verifier | Chưa triển khai; cần LLM provider khi tích hợp |
| **M04** | Speech Planner + TTS + Scheduler admission/final | Chưa triển khai; cần provider hoặc mock TTS |
| **M05** | Part 1 integration + QA / audit / benchmark | Chưa triển khai |
| Part 2 | License Gate + Lip-sync overlays căn theo timestamp | Phát triển song song theo contract |
| Part 3 | Timeline + Compositor cho một video nền liên tục | Phát triển song song theo contract |
| Demo | API/Web + video thành phẩm + review chất lượng | Chỉ hoàn thành khi có artifact và kiểm thử thực |

## 25.1. Điểm kiểm tra kỹ thuật sớm

Với Part 2 cần thử nghiệm một đoạn video nền + audio hợp lệ + lip-sync tại timestamp đã chốt để đánh giá độ tự nhiên. Với M02 cần chốt tập câu hỏi đánh giá trước khi chọn Embedding/Ranking; không chọn công nghệ chỉ vì nó phổ biến.

## 25.2. Phát triển song song

- M02.1 và M02.2 không cần OpenAI Key.
- M03 có thể mock Evidence từ Knowledge Engine để test công cụ/verification.
- Part 2 có thể dùng mock AudioArtifact/RenderJob, Part 3 mock overlays.
- API/Web được phát triển dựa trên schema, không yêu cầu video cuối đã render ngay từ đầu.

---

# 26. DEFINITION OF DONE


Một task được xem là hoàn thành khi:


1. Chức năng đúng với Acceptance Criteria.
2. Input/Output tuân thủ data contract.
3. Unit tests liên quan pass.
4. Contract tests liên quan pass.
5. Integration tests liên quan pass khi đã có dependency.
6. Không chứa secrets.
7. Không sử dụng dữ liệu không được phép.
8. Tài liệu được cập nhật.
9. Pull Request đã được review và merge.


## 26.1. Definition of Done cho toàn bộ PoC


PoC hoàn thành khi có thể chứng minh:


- Một video nền liên tục được sử dụng.
- AI chủ động giới thiệu sản phẩm.
- Mock comment xuất hiện đúng thời gian.
- Hệ thống chọn lọc các comment.
- Các câu trả lời quan trọng được kiểm chứng.
- TTS tạo audio hợp lệ.
- Khẩu hình đồng bộ với audio ở mức chất lượng chấp nhận được.
- Không có các đoạn lời thoại phát chồng nhau.
- Video cuối không xuất hiện khoảng trống do nối clip.
- Có thể truy vết các quyết định xử lý.
- Có kết quả benchmark thực tế.
- Nhóm có thể chạy lại demo theo tài liệu hướng dẫn.


---


# 27. KẾT LUẬN


Cấu trúc HOSTRA AI PoC V2.1 được thiết kế để phục vụ một pipeline Hybrid AI Commerce có khả năng kiểm chứng.


Hệ thống gồm:


**Part 1 — Verified Agent, Comment Triage & TTS**


Phụ trách bình luận, quyết định ưu tiên, kiểm chứng nội dung và tạo audio.


**Orchestration — Speech Scheduler**


Phụ trách thứ tự và thời điểm phát lời thoại.


**Part 2 — Time-aligned Video Lip-sync**


Phụ trách đồng bộ khẩu hình với âm thanh trên các khung hình của video nền.


**Part 3 — Continuous Video Compositor**


Phụ trách dựng một video hoàn chỉnh, đồng bộ audio, video, comment và xuất báo cáo.


Cấu trúc sử dụng 10 data contracts:


1. CommentEvent
2. CommentDecision
3. AgentResponse
4. SpeechTurn
5. AudioArtifact
6. RenderJob
7. VideoArtifact
8. RunManifest
9. TimelineEvent
10. AuditRecord


Ba nguyên tắc xuyên suốt:


**Contract First:** Thiết kế và xác minh hợp đồng dữ liệu trước khi tích hợp.


**Continuous Video:** Duy trì một video nền liên tục, chỉ áp dụng các thay đổi cần thiết theo timeline.


**Verifiable AI:** Câu trả lời, quyết định chọn lọc, kết quả render và chất lượng đầu ra phải có khả năng kiểm tra, đo lường và truy vết.


Mục tiêu của giai đoạn này không phải xây dựng ngay một hệ thống livestream AI thương mại hoàn chỉnh.


Mục tiêu là tạo ra một PoC có tính thuyết phục, kiểm chứng được khả năng kết hợp AI Agent, xử lý bình luận, TTS và lip-sync trên một video bán hàng liên tục.


Đây là nền tảng để nhóm tiếp tục phát triển MVP và đánh giá khả năng triển khai realtime trong tương lai.


