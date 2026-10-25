# HOSTRA AI PoC — Tài liệu chú thích cấu trúc Project

**Project:** HOSTRA AI — Hybrid AI Live Commerce Proof of Concept

**Repository:** https://github.com/QuangCanhCut/Hostra_AI_PoC

**Công nghệ:** Python, Pydantic v2, LLM, RAG, TTS, Lip-sync, FFmpeg, FastAPI, HTML/CSS/JS, Pytest

**Giai đoạn:** Proof of Concept (PoC)

**Phiên bản tài liệu:** V2.0

**Ngày cập nhật:** 24/10/2026

**Trạng thái:** Kiến trúc đề xuất đã review, triển khai từng module theo backlog.

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

HOSTRA AI PoC được chia thành ba Part chính và một lớp Orchestration.

## 3.1. Part 1 — Verified AI Agent, Comment Triage & TTS

Nhiệm vụ:

- Tiếp nhận bình luận.
- Lọc spam và bình luận trùng lặp.
- Chấm điểm và ưu tiên câu hỏi.
- Quản lý ngữ cảnh hội thoại.
- Truy xuất dữ liệu sản phẩm.
- Kiểm chứng câu trả lời.
- Chuẩn bị lời giới thiệu và lời trả lời.
- Chuyển lời thoại thành audio.

Output:

- CommentDecision
- AgentResponse
- SpeechTurn
- AudioArtifact

## 3.2. Orchestration — Speech Scheduling

Nhiệm vụ:

- Quản lý thứ tự các lượt lời.
- Xác định thời điểm bắt đầu phát audio.
- Điều phối giữa lời giới thiệu và lời trả lời khách hàng.
- Không cho phép các lời thoại chồng thời gian.
- Kiểm tra giới hạn thời lượng video.
- Cung cấp kế hoạch thời gian cho Part 2 và Part 3.

## 3.3. Part 2 — Time-aligned Video Lip-sync

Nhiệm vụ:

- Kiểm tra quyền sử dụng khuôn mặt và giọng nói.
- Xác định những khung hình cần xử lý.
- Thực hiện lip-sync theo audio.
- Tạo artifact có timestamp.
- Kiểm tra kết quả render.

Output:

- RenderJob
- VideoArtifact
- Lip-sync overlays

## 3.4. Part 3 — Continuous Video Compositor

Nhiệm vụ:

- Quản lý metadata phiên demo.
- Xây dựng timeline.
- Kiểm tra các sự kiện trên timeline.
- Áp dụng lip-sync lên video nền liên tục.
- Đồng bộ audio và bình luận.
- Xuất video cuối.
- Ghi audit và benchmark.

Output:

- RunManifest
- TimelineEvent
- AuditRecord
- hostra_demo.mp4
- benchmark.json

## 3.5. Luồng xử lý tổng thể

```text
PRODUCT DATA + FAQ + APPROVED SCRIPTS
                   |
                   v
             PART 1 AGENT
                   ^
                   |
             MOCK COMMENTS
                   |
                   v
            COMMENT TRIAGE
                   |
          Filter / Rank / Queue
                   |
                   v
             VERIFIED AGENT
                   |
                   v
             SPEECH PLANNER
                   |
                   v
              SPEECH TURN
                   |
                   v
               TTS AUDIO
                   |
                   v
             AUDIO ARTIFACT
                   |
                   v
            SPEECH SCHEDULER
                   |
          Time-aligned Speech Plan
                   |
                   v
         PART 2 VIDEO LIP-SYNC <---- BASE VIDEO
                   |
                   v
            VIDEO ARTIFACTS
                   |
                   v
          PART 3 VIDEO COMPOSITOR <---- BASE VIDEO
                   |
                   v
              FINAL DEMO
                   |
       +-----------+-----------+
       |           |           |
    Timeline     Audit      Benchmark
```

Lưu ý:

Speech Scheduler phải xác định thời điểm phát lời thoại trước khi Part 2 tạo RenderJob.

Vì vậy, luồng thực thi thực tế không hoàn toàn tuyến tính theo thứ tự Part 1 → Part 2 → Part 3.

---

# 4. CẤU TRÚC THƯ MỤC PROJECT

```text
hostra-ai-poc/
│
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── requirements-gpu.txt
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── configs/
│   ├── app.yaml
│   ├── demo_scenario.yaml
│   └── comment_policy.yaml
│
├── shared_data/
│   ├── inputs/
│   │   ├── catalog_skus.json
│   │   ├── product_faq.md
│   │   ├── mock_comments.json
│   │   ├── creator_license.json
│   │   ├── base_operator.mp4
│   │   └── approved_product_scripts.json
│   │
│   └── runs/
│       └── <run_id>/
│           │
│           ├── manifest.json
│           │
│           ├── step1_agent_audio/
│           │   ├── comment_decisions.json
│           │   ├── answers.json
│           │   ├── speech_turns.json
│           │   └── audio/
│           │       ├── intro_001.wav
│           │       └── reply_001.wav
│           │
│           ├── step2_lipsync/
│           │   ├── render_jobs.json
│           │   ├── video_artifacts.json
│           │   └── overlays/
│           │       ├── intro_001.mp4
│           │       └── reply_001.mp4
│           │
│           └── step3_final/
│               ├── hostra_demo.mp4
│               ├── timeline.json
│               ├── audit_log.json
│               └── benchmark.json
│
├── src/
│   └── hostra_ai/
│       ├── __init__.py
│       ├── pipeline.py
│       │
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
│       │   ├── comment_ingest.py
│       │   ├── comment_triage.py
│       │   ├── comment_queue.py
│       │   ├── conversation_memory.py
│       │   ├── knowledge_engine.py
│       │   ├── verified_agent.py
│       │   ├── answer_verifier.py
│       │   ├── speech_planner.py
│       │   ├── tts_provider.py
│       │   └── pipeline.py
│       │
│       ├── orchestration/
│       │   ├── __init__.py
│       │   └── speech_scheduler.py
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
│   ├── validate_inputs.py
│   ├── run_part1.py
│   ├── prepare_lipsync.py
│   ├── import_lipsync.py
│   └── run_demo.py
│
├── tests/
│   ├── conftest.py
│   │
│   ├── fixtures/
│   │   ├── part1/
│   │   ├── part2/
│   │   └── part3/
│   │
│   ├── unit/
│   │   ├── test_part1.py
│   │   ├── test_part2.py
│   │   └── test_part3.py
│   │
│   ├── contract/
│   │   ├── test_part1_contract.py
│   │   ├── test_part2_contract.py
│   │   └── test_part3_contract.py
│   │
│   └── integration/
│       ├── test_part1_pipeline.py
│       ├── test_part2_pipeline.py
│       ├── test_part3_pipeline.py
│       └── test_demo_pipeline.py
│
└── docs/
    ├── architecture.md
    ├── project_structure.md
    ├── data_contract_vi.md
    ├── setup_guide.md
    ├── test_plan.md
    ├── benchmark.md
    └── demo_script.md
```

**Lưu ý:**

- Cây thư mục thể hiện kiến trúc mục tiêu.
- Những file chưa được triển khai sẽ được bổ sung theo backlog.
- Không cần tạo trước mọi file Python rỗng.
- Các thư mục kết quả trong `shared_data/runs/` phải được sinh khi thực thi.
- Không commit các output lớn hoặc dữ liệu chưa có quyền sử dụng.

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

| File | Công dụng | Input | Output |
|---|---|---|---|
| `app.yaml` | Cấu hình runtime và provider | LLM, TTS, timeout, paths | Application configuration |
| `demo_scenario.yaml` | Kịch bản phiên demo | SKU, video nguồn, cấu hình sự kiện | Demo scenario |
| `comment_policy.yaml` | Quy tắc lọc và ưu tiên bình luận | Threshold, queue settings | Comment policy |

## 7.1. `app.yaml`

Dự kiến chứa:

- Chế độ chạy offline.
- Cấu hình LLM provider.
- Cấu hình TTS provider.
- Cấu hình lip-sync provider.
- Đường dẫn dữ liệu.
- Timeout và giới hạn tài nguyên.
- Logging configuration.

Không lưu credentials thật trong file YAML.

## 7.2. `demo_scenario.yaml`

Dự kiến chứa:

- Run configuration.
- Active SKU.
- Base video.
- Avatar.
- Nguồn mock comments.
- Nguồn kịch bản giới thiệu đã duyệt.
- Thời lượng và thông số video mục tiêu.

File này không nên chứa logic chọn bình luận đã hardcode theo từng `comment_id`.

Việc chọn bình luận phải được thực hiện bởi Comment Triage theo policy.

## 7.3. `comment_policy.yaml`

Dự kiến chứa:

- Bật/tắt spam filtering.
- Deduplication policy.
- Trọng số ưu tiên câu hỏi.
- Giới hạn kích thước hàng đợi.
- Thời gian chờ tối đa.
- Giới hạn lượt trả lời của một viewer.
- Quy tắc xử lý câu hỏi hết hạn.

Các ngưỡng ban đầu là cấu hình thử nghiệm và phải được điều chỉnh dựa trên test.

---

# 8. `shared_data/inputs/` — DỮ LIỆU ĐẦU VÀO

| File | Công dụng | Module sử dụng |
|---|---|---|
| `catalog_skus.json` | Dữ liệu có cấu trúc của sản phẩm | Knowledge Engine |
| `product_faq.md` | FAQ và thông tin sản phẩm đã duyệt | Retrieval, Verifier |
| `mock_comments.json` | Mô phỏng bình luận khách hàng | Comment Ingest |
| `creator_license.json` | Thông tin quyền sử dụng hình ảnh/giọng nói | License Gate |
| `base_operator.mp4` | Video nền duy nhất của phiên demo | Part 2, Part 3 |
| `approved_product_scripts.json` | Nội dung giới thiệu đã được duyệt | Speech Planner |

## 8.1. `catalog_skus.json`

Chứa những thông tin như:

- SKU ID.
- Tên sản phẩm.
- Giá.
- Mô tả.
- Thuộc tính.
- Thông tin khuyến mãi hoặc tồn kho trong dữ liệu demo nếu có.

Giá, tồn kho và ưu đãi phải lấy từ nguồn dữ liệu có thẩm quyền.

LLM không được tự tạo những thông tin này.

## 8.2. `mock_comments.json`

Lưu danh sách bình luận giả lập.

Mỗi bình luận cần được liên kết với:

- Comment ID.
- Viewer ID.
- Nội dung.
- Thời điểm xuất hiện trong kịch bản.
- Active SKU khi được tiếp nhận.

Thời gian xuất hiện trong video nên được biểu diễn bằng offset theo mili giây trong kịch bản đầu vào.

Không nhầm offset trên video với timestamp UTC của dữ liệu nghiệp vụ.

Sau khi được chuẩn hóa, dữ liệu hợp lệ trở thành `CommentEvent`.

## 8.3. `base_operator.mp4`

Là video nguồn xuyên suốt của một phiên demo.

Yêu cầu:

1. Góc quay ổn định.
2. Khuôn mặt nhìn thấy rõ.
3. Hạn chế che vùng miệng.
4. Sản phẩm được cầm và thao tác tự nhiên.
5. Ánh sáng tương đối ổn định.
6. Thời lượng đủ cho toàn bộ kịch bản.
7. Có quyền sử dụng hình ảnh phù hợp.

Không tự ý lặp hoặc cắt video nguồn để kéo dài thời lượng nếu chưa kiểm tra tính liên tục.

## 8.4. `approved_product_scripts.json`

Chứa kịch bản giới thiệu sản phẩm được phê duyệt.

Mỗi nội dung nên có:

- Script ID.
- SKU ID.
- Loại lời thoại.
- Text.
- Thông tin phê duyệt.

Nội dung này được dùng để tạo `SpeechTurn` ngay cả khi chưa có comment.

Không tạo bình luận giả của khách hàng chỉ để kích hoạt lời giới thiệu.

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

# 11. PART 1 — VERIFIED AGENT, COMMENT TRIAGE & TTS

Đường dẫn:

`src/hostra_ai/part1_agent_tts/`

## 11.1. Mục tiêu

Part 1 xử lý bình luận và nội dung lời thoại.

Hệ thống phải:

1. Nhận dữ liệu bình luận.
2. Kiểm tra Active SKU.
3. Lọc spam và bình luận trùng.
4. Ưu tiên những câu hỏi phù hợp.
5. Quản lý ngữ cảnh của viewer.
6. Truy xuất thông tin sản phẩm.
7. Kiểm chứng câu trả lời.
8. Chuẩn bị lời thoại.
9. Tạo audio bằng TTS.

## 11.2. Chức năng từng file

| File | Input | Output | Chức năng |
|---|---|---|---|
| `comment_ingest.py` | Mock comments, Active SKU | CommentEvent | Chuẩn hóa đầu vào |
| `comment_triage.py` | CommentEvent, policy | CommentDecision | Lọc, gộp, chấm ưu tiên |
| `comment_queue.py` | CommentDecision | Pending comments | Quản lý hàng đợi |
| `conversation_memory.py` | Viewer ID, lịch sử | Conversation context | Nối ngữ cảnh hội thoại |
| `knowledge_engine.py` | SKU, query, catalog, FAQ | Evidence | Truy xuất dữ liệu |
| `verified_agent.py` | Comment, context, evidence | Candidate answer | Tạo câu trả lời |
| `answer_verifier.py` | Candidate answer, evidence | Verification result | Kiểm tra câu trả lời |
| `speech_planner.py` | Verified answer hoặc approved script | SpeechTurn | Tạo lượt lời |
| `tts_provider.py` | SpeechTurn | WAV, AudioArtifact | Chuyển text thành audio |
| `pipeline.py` | Part 1 inputs | Part 1 artifacts | Điều phối Part 1 |

## 11.3. Comment Triage

Comment Triage không chỉ kiểm tra nội dung độc hại.

Nó còn thực hiện:

- Spam filtering.
- Duplicate detection.
- Active SKU relevance.
- Priority scoring.
- Basic fairness giữa các viewer.
- Queue admission.

Một số hành động của CommentDecision:

- selected
- deferred
- skipped
- escalated

Quyết định phải có lý do rõ ràng để audit.

Không nhất thiết đưa mọi comment vào LLM.

## 11.4. Conversation Memory

Quản lý lịch sử tương tác theo:

- run_id
- viewer_id

Ví dụ:

Viewer hỏi giá sản phẩm.

Sau đó viewer hỏi:

"Thế bảo hành bao lâu?"

Hệ thống có thể sử dụng ngữ cảnh trước để xác định sản phẩm đang được nói đến.

Trong PoC, Conversation Memory có thể sử dụng bộ nhớ tạm trong quá trình chạy.

Chưa bắt buộc xây database riêng.

## 11.5. Verified Agent

Câu trả lời phải dựa trên thông tin sản phẩm đã được kiểm chứng.

Quy tắc:

1. Không tự tạo giá, tồn kho hoặc khuyến mãi.
2. Không sử dụng hướng dẫn từ comment để thay đổi chính sách hệ thống.
3. Không phát câu trả lời thiếu bằng chứng khi nội dung yêu cầu bằng chứng.
4. Nếu không thể xác minh thì từ chối hoặc yêu cầu làm rõ.
5. Câu trả lời bị blocked không được gửi sang TTS.

## 11.6. Speech Planner

Speech Planner chuẩn hóa các loại lời thoại:

- Product introduction.
- Comment reply.
- Safe fallback.

Product introduction sử dụng kịch bản đã duyệt.

Comment reply sử dụng AgentResponse đã được phép phát.

Speech Planner tạo SpeechTurn.

## 11.7. TTS Provider

TTS nhận nội dung từ SpeechTurn.

Output:

- Audio file.
- Duration.
- Sample rate.
- AudioArtifact metadata.

Audio cần được liên kết với SpeechTurn.

Không giả định mọi audio đều phải có viewer_id hoặc response_id.

---

# 12. ORCHESTRATION — SPEECH SCHEDULER

Đường dẫn:

`src/hostra_ai/orchestration/`

## 12.1. Mục tiêu

Speech Scheduler quyết định một lượt lời được phát lúc nào.

Input:

- SpeechTurn.
- AudioArtifact.
- Comment timing.
- RunManifest.
- Timeline constraints.

Output:

- Kế hoạch phát audio theo thời gian.
- Thông tin cần thiết để tạo RenderJob.
- Dữ liệu thời gian cho Timeline Builder.

## 12.2. Các quy tắc chính

1. Không cho hai lời thoại phát cùng lúc.
2. Không phát câu trả lời trước khi comment xuất hiện.
3. Không ngắt lời giới thiệu giữa câu nếu không có điểm ngắt phù hợp.
4. Không vượt quá thời lượng video nguồn.
5. Comment hết hạn không được giữ vô hạn trong hàng đợi.
6. Những câu trả lời được phát phải khớp Active SKU.
7. Không lập lịch phát audio chưa được phép phát.

## 12.3. Ví dụ

Video nền dài 60 giây.

- 0–10 giây: Giới thiệu sản phẩm.
- 12 giây: Comment xuất hiện.
- 15–19 giây: AI trả lời.
- 19–30 giây: Tiếp tục giới thiệu.
- 35 giây: Comment tiếp theo xuất hiện.
- 38–43 giây: AI trả lời.
- 43–60 giây: Tiếp tục video nền và nội dung đã lên lịch.

Các mốc này chỉ là ví dụ minh họa, không phải kịch bản cố định.

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

| Script | Input | Output | Chức năng |
|---|---|---|---|
| `validate_inputs.py` | Input files, config | Validation result | Kiểm tra đầu vào |
| `run_part1.py` | Scenario, product data | Part 1 artifacts | Chạy Agent/TTS |
| `prepare_lipsync.py` | Audio, speech schedule | RenderJobs | Chuẩn bị GPU jobs |
| `import_lipsync.py` | GPU outputs | VideoArtifacts | Import và kiểm tra render |
| `run_demo.py` | Config và artifacts | Final demo | Điều phối toàn bộ pipeline |

## 18.1. Nguyên tắc sử dụng scripts

Các script chỉ đóng vai trò entry point.

Business logic phải nằm trong:

`src/hostra_ai/`

Không viết lại thuật toán lọc comment, verification hoặc video compositing trong scripts.

## 18.2. Pipeline tổng thể

Logic điều phối toàn bộ ứng dụng nằm trong:

`src/hostra_ai/pipeline.py`

Script:

`scripts/run_demo.py`

chỉ gọi lại pipeline và xử lý các tham số chạy.

---

# 19. `tests/` — HỆ THỐNG KIỂM THỬ

## 19.1. Cấu trúc

```text
tests/
├── conftest.py
│
├── fixtures/
│   ├── part1/
│   ├── part2/
│   └── part3/
│
├── unit/
│   ├── test_part1.py
│   ├── test_part2.py
│   └── test_part3.py
│
├── contract/
│   ├── test_part1_contract.py
│   ├── test_part2_contract.py
│   └── test_part3_contract.py
│
└── integration/
    ├── test_part1_pipeline.py
    ├── test_part2_pipeline.py
    ├── test_part3_pipeline.py
    └── test_demo_pipeline.py
```

## 19.2. Unit Tests

### test_part1.py

Kiểm tra:

- CommentEvent.
- CommentDecision.
- AgentResponse.
- SpeechTurn.
- AudioArtifact.
- Các validator tương ứng.

### test_part2.py

Kiểm tra:

- RenderJob.
- VideoArtifact.
- Status validation.
- Timestamp validation.
- Artifact metadata.

### test_part3.py

Kiểm tra:

- RunManifest.
- TimelineEvent.
- AuditRecord.
- Các ràng buộc cấp model.

## 19.3. Contract Tests

### test_part1_contract.py

Kiểm tra hợp đồng dữ liệu Part 1.

### test_part2_contract.py

Kiểm tra hợp đồng dữ liệu Part 2.

### test_part3_contract.py

Kiểm tra hợp đồng dữ liệu Part 3.

Các test cần xác minh:

- JSON serialization.
- JSON deserialization.
- Field types.
- Required fields.
- Enum values.
- Invalid data rejection.
- Tính tương thích giữa producer và consumer.

## 19.4. Integration Tests

### test_part1_pipeline.py

Kiểm tra:

Comment → Triage → Agent → Verification → SpeechTurn → TTS.

### test_part2_pipeline.py

Kiểm tra:

RenderJob → License Gate → Lip-sync Adapter → VideoArtifact.

Có thể mock model GPU trong CI.

### test_part3_pipeline.py

Kiểm tra:

RunManifest → Timeline → Validation → Compositor.

### test_demo_pipeline.py

Kiểm tra luồng tổng thể của PoC bằng dữ liệu thử nghiệm và mocked providers khi phù hợp.

## 19.5. Cách tổ chức test trong mỗi file

Các bài test trong cùng file có thể nhóm theo class.

Ví dụ:

- TestCommentEvent.
- TestCommentDecision.
- TestAgentResponse.
- TestSpeechTurn.
- TestAudioArtifact.

Điều này giúp tập trung test theo Part mà vẫn dễ tìm từng nhóm chức năng.

Nếu file test trở nên quá dài trong tương lai, có thể tách lại theo module.

## 19.6. Chạy test

Chạy toàn bộ:

```powershell
python -m pytest -q
```

Chỉ chạy unit tests:

```powershell
python -m pytest tests/unit -q
```

Chỉ chạy Part 1:

```powershell
python -m pytest tests/unit/test_part1.py -q
```

Chỉ chạy contract Part 2:

```powershell
python -m pytest tests/contract/test_part2_contract.py -q
```

Chạy integration tests:

```powershell
python -m pytest tests/integration -q
```

## 19.7. Quy tắc khi chuyển test cũ

- Giữ nguyên các test case còn hợp lệ.
- Không xóa assertion chỉ để test pass.
- Cập nhật các test bị ảnh hưởng bởi thay đổi contract.
- Chạy regression tests sau khi di chuyển file.
- Không gộp việc đổi cấu trúc test và đổi business logic vào cùng một thay đổi lớn nếu có thể tách.

---

# 20. DATA CONTRACT GIỮA CÁC MODULE

| Producer | Consumer | Dữ liệu |
|---|---|---|
| Comment Ingest | Comment Triage | CommentEvent |
| Comment Triage | Comment Queue / Agent | CommentDecision |
| Comment Queue | Verified Agent | Comment được chọn |
| Knowledge Engine | Verified Agent | Product evidence |
| Verified Agent / Verifier | Speech Planner | AgentResponse |
| Approved Scripts | Speech Planner | Approved script |
| Speech Planner | TTS Provider | SpeechTurn |
| TTS Provider | Speech Scheduler | AudioArtifact |
| Run Manager | Các module cần video metadata | RunManifest |
| Speech Scheduler | Render Service | Speech schedule |
| Render Service | Lip-sync Adapter | RenderJob |
| Lip-sync Adapter | Video Compositor | VideoArtifact |
| Timeline Builder | Video Compositor | TimelineEvent |
| Các module | Audit Service | Audit events |
| Pipeline | Benchmark Collector | Measured metrics |

## 20.1. Quy tắc liên kết dữ liệu

Mỗi artifact phải có khả năng truy vết thông qua ID.

Ví dụ:

```text
CommentEvent
    |
    v
CommentDecision
    |
    v
AgentResponse
    |
    v
SpeechTurn
    |
    v
AudioArtifact
    |
    v
RenderJob
    |
    v
VideoArtifact
    |
    v
TimelineEvent
    |
    v
Final Video
```

Với lời giới thiệu chủ động:

```text
Approved Product Script
    |
    v
SpeechTurn
    |
    v
AudioArtifact
    |
    v
RenderJob
    |
    v
VideoArtifact
    |
    v
TimelineEvent
```

Các ID dùng để liên kết nghiệp vụ.

Tên file chỉ là vị trí lưu dữ liệu, không thay thế cho ID.

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

# 25. THỨ TỰ TRIỂN KHAI ĐỀ XUẤT

| Giai đoạn | Công việc | Kết quả |
|---|---|---|
| 1 | Chốt kiến trúc V2 | Tài liệu cấu trúc và architecture |
| 2 | Bổ sung 3 schema mới | CommentDecision, SpeechTurn, RunManifest |
| 3 | Điều chỉnh schema hiện có | AudioArtifact, RenderJob, VideoArtifact, TimelineEvent |
| 4 | Refactor test theo Part 1/2/3 | Unit và contract tests đạt |
| 5 | Tạo dữ liệu demo mới | Approved scripts, mock comments, video |
| 6 | Xây Comment Triage và Queue | CommentDecision |
| 7 | Xây Verified Agent và TTS | AgentResponse, SpeechTurn, AudioArtifact |
| 8 | Xây Speech Scheduler | Kế hoạch phát lời thoại |
| 9 | Thử nghiệm lip-sync trên video nền | VideoArtifact căn chỉnh |
| 10 | Xây Compositor | hostra_demo.mp4 |
| 11 | Tích hợp API và Web UI | Demo interface |
| 12 | Integration, QA, benchmark | Báo cáo kiểm thử |

## 25.1. Điểm kiểm tra kỹ thuật sớm

Trước khi tích hợp đầy đủ hệ thống, nhóm cần thử nghiệm:

Một video nền ngắn + một đoạn audio TTS + lip-sync tại đúng timestamp.

Mục tiêu là xác định khả năng tạo khẩu hình tự nhiên mà không làm xuất hiện điểm chuyển cảnh rõ rệt.

Nếu thử nghiệm chưa đạt thì cần xử lý kỹ thuật render trước khi mở rộng toàn bộ pipeline.

## 25.2. Phát triển song song

Các module có thể phát triển song song khi contract đã được thống nhất.

Ví dụ:

- Agent/TTS có thể dùng mock SpeechTurn.
- GPU worker có thể dùng mock RenderJob.
- Compositor có thể dùng video artifact thử nghiệm.
- Frontend có thể sử dụng mock API responses.

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

Cấu trúc HOSTRA AI PoC V2 được thiết kế để phục vụ một pipeline Hybrid AI Commerce có khả năng kiểm chứng.

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