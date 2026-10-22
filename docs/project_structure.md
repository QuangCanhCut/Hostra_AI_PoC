# HOSTRA AI PoC — Tài liệu chú thích cấu trúc Project

**Project:** HOSTRA AI — Hybrid AI Live Commerce Proof of Concept  
**Repository:** https://github.com/QuangCanhCut/Hostra_AI_PoC  
**Stack dự kiến:** Python 3.11, Pydantic v2, Gemini, TTS, MuseTalk, FFmpeg, HTML/CSS/JS, Pytest  
**Giai đoạn:** Proof of Concept (PoC)

## 1. Mục đích tài liệu

Tài liệu mô tả vai trò, chức năng, dữ liệu đầu vào (Input) và dữ liệu đầu ra (Output) của các folder và file trong repository HOSTRA AI PoC.

Mục đích:

- Giúp ba thành viên hiểu kiến trúc tổng thể trước khi lập trình.
- Xác định trách nhiệm của từng module và cách chúng kết nối.
- Hạn chế trùng lặp công việc hoặc viết sai cấu trúc dữ liệu.
- Làm tài liệu tham chiếu khi triển khai task, review code và tích hợp.
- Giúp thành viên mới nhanh chóng hiểu project.

**Lưu ý:** Cấu trúc dưới đây là thiết kế dự kiến. Một số module, file và data contract chưa được triển khai hoặc chốt chính thức. Khi hoàn thành từng task, nhóm cần cập nhật tài liệu theo implementation thực tế.

## 2. Tổng quan kiến trúc

HOSTRA AI PoC được chia thành ba phần chính:

**Part 1 — Verified AI Agent & TTS**

Nhận bình luận khách hàng, truy xuất thông tin sản phẩm, xác minh nội dung câu trả lời và chuyển văn bản thành giọng nói.

**Part 2 — Video Lip-sync**

Nhận âm thanh và video gốc, kiểm tra quyền sử dụng danh tính số, thực hiện lip-sync và tạo các video clip AI.

**Part 3 — Live Compositor & Demo**

Đồng bộ timeline, ghép các clip, hiển thị teleprompter, xây dựng giao diện demo và xuất báo cáo đánh giá.

Luồng dữ liệu tổng thể:

```text
Product Catalog + FAQ + Mock Comments + License
                       |
                       v
           PART 1: AI AGENT & TTS
                       |
              answers.json + WAV
                       |
                       v
           PART 2: VIDEO LIP-SYNC
                       |
                MP4 + Manifest
                       |
                       v
          PART 3: LIVE COMPOSITOR
                       |
                       v
              Final Demo Video
              Timeline + Audit
              Benchmark Results
```

PoC ưu tiên xử lý video trước (pre-rendered), chưa đặt mục tiêu livestream AI thời gian thực hoàn chỉnh.

## 3. Chú thích các folder và file

### 3.1. Root Directory — Cấu hình chung

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `hostra-ai-poc/` | Thư mục gốc chứa toàn bộ source code, tài liệu, cấu hình và công cụ của dự án | Code, tài liệu, cấu hình của nhóm | Repository hoàn chỉnh |
| `.env.example` | Khai báo mẫu các biến môi trường cần thiết để chạy hệ thống | Tên biến như API key, provider, đường dẫn, chế độ demo | Mẫu để mỗi thành viên tự tạo file `.env` |
| `.gitignore` | Quy định những file Git không được theo dõi | Các pattern cần bỏ qua | Giúp tránh commit secrets, file tạm và output lớn |
| `README.md` | Tài liệu giới thiệu project, hướng dẫn setup và chạy thử | Kiến trúc, quy trình cài đặt, lệnh chạy | Hướng dẫn cho thành viên và người review |
| `requirements.txt` | Danh sách thư viện Python cần cho môi trường chạy cơ bản | Các package và phiên bản phụ thuộc | Dùng để cài dependencies bằng pip |
| `requirements-gpu.txt` | Danh sách dependencies bổ sung cho các tác vụ GPU, đặc biệt là lip-sync | PyTorch, thư viện inference và các dependencies GPU cần thiết | Môi trường chạy GPU phù hợp |
| `pyproject.toml` | Cấu hình Python project và các công cụ như Ruff, pytest, packaging | Metadata, dependencies và cấu hình công cụ | Cấu hình thống nhất cho quá trình phát triển |

**Ghi chú:**

- `.env.example` chỉ chứa tên biến và giá trị mẫu, không chứa API key thật.
- `.env` tuyệt đối không được commit lên GitHub.
- `requirements.txt` và `pyproject.toml` cần có chiến lược quản lý dependencies nhất quán, tránh khai báo phiên bản mâu thuẫn.

### 3.2. `.github/` — CI và quy trình làm việc

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `.github/` | Chứa cấu hình dành riêng cho GitHub | GitHub configuration | Quy trình cộng tác và tự động hóa |
| `.github/workflows/` | Lưu các workflow của GitHub Actions | Workflow YAML | Các workflow có thể được GitHub thực thi |
| `ci.yml` | Tự động kiểm tra chất lượng code khi push hoặc tạo Pull Request theo cấu hình trigger | Source code, dependencies, test suite | Kết quả lint, test và trạng thái CI |

CI dự kiến kiểm tra:

1. Cài đặt dependencies.
2. Chạy Ruff.
3. Chạy Pytest.
4. Báo kết quả pass/fail.
5. Ngăn merge khi chưa đạt quality gate nếu repository được cấu hình yêu cầu CI thành công.

### 3.3. `configs/` — Cấu hình hoạt động

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `configs/` | Lưu các cấu hình nghiệp vụ và kịch bản demo, tách khỏi source code | Các file YAML | Cấu hình được application đọc khi chạy |
| `app.yaml` | Cấu hình hoạt động chung như provider, timeout, mode và tham số pipeline | Tham số hệ thống | Đối tượng cấu hình runtime |
| `demo_scenario.yaml` | Định nghĩa kịch bản trình diễn PoC | SKU, danh sách bình luận, thứ tự xử lý, tình huống demo | Kịch bản được demo pipeline thực thi |

**Ví dụ:** `demo_scenario.yaml` có thể quy định sản phẩm đang giới thiệu, bình luận nào được xử lý và thứ tự phát câu trả lời.

File này giúp thay đổi kịch bản demo mà không cần chỉnh sửa trực tiếp logic Python.

### 3.4. `shared_data/inputs/` — Dữ liệu đầu vào dùng chung

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `shared_data/` | Thư mục lưu dữ liệu trao đổi giữa các phần của hệ thống | Input datasets và artifacts | Tập dữ liệu dùng chung |
| `shared_data/inputs/` | Chứa dữ liệu mẫu phục vụ PoC | Dữ liệu được chuẩn bị và kiểm tra trước | Input cho Part 1 và Part 2 |
| `catalog_skus.json` | Chứa catalog sản phẩm gồm SKU, tên, giá, tồn kho và các thuộc tính cần thiết | Dữ liệu sản phẩm có cấu trúc | Product records để Agent truy xuất |
| `product_faq.md` | Chứa FAQ và mô tả/chính sách sản phẩm đã được duyệt | Nội dung tri thức sản phẩm | Nguồn bằng chứng cho Knowledge Engine |
| `mock_comments.json` | Mô phỏng bình luận từ người xem livestream | Danh sách bình luận giả lập | Comment events cho Agent |
| `creator_license.json` | Mô tả giấy phép sử dụng avatar, khuôn mặt hoặc giọng nói trong phạm vi PoC | Thông tin chủ thể, quyền sử dụng, hiệu lực và giới hạn | Dữ liệu để License Gate kiểm tra |
| `base_operator.mp4` | Video gốc của người thao tác sản phẩm, dùng làm đầu vào cho pipeline lip-sync/compositing | Video quay trong điều kiện phù hợp | Source video cho Part 2 và Part 3 |

**Lưu ý về bảo mật:** Chỉ lưu dữ liệu được phép sử dụng. Video, giọng nói và thông tin giấy phép thật cần có sự đồng ý hợp lệ trước khi đưa vào môi trường chia sẻ; không tự động commit các tài sản này vào Git.

### 3.5. `shared_data/runs/` — Kết quả thực thi

Mỗi lần chạy pipeline được gán một `run_id` duy nhất.

Ví dụ:

```text
shared_data/runs/run_001/
```

Mục tiêu của cách tổ chức này là lưu kết quả từng lần chạy riêng biệt, thuận tiện debug, kiểm thử và benchmark.

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `shared_data/runs/` | Lưu các kết quả phát sinh trong quá trình chạy pipeline | Dữ liệu và artifacts từ các module | Các thư mục được phân theo run |
| `<run_id>/` | Gom toàn bộ dữ liệu và kết quả của một lần chạy cụ thể | Một lần thực thi PoC | Các output liên quan đến cùng run |
| `manifest.json` | Ghi metadata và trạng thái của lần chạy | Run ID, cấu hình, tham chiếu input và trạng thái từng bước | Run manifest dùng để theo dõi và tái hiện pipeline |

**Quan trọng:** `shared_data/runs/` là thư mục phát sinh khi thực thi, không cần tạo sẵn nội dung của từng run trong repository.

### 3.6. `step1_agent_audio/` — Output Part 1

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `step1_agent_audio/` | Chứa kết quả xử lý Agent và TTS của một run | Comment events và dữ liệu sản phẩm | Answers và audio artifacts |
| `answers.json` | Lưu câu trả lời đã xử lý cùng metadata xác minh | Comment, evidence và kết quả Agent | Danh sách AgentResponse để các bước sau sử dụng |
| `audio/` | Lưu file âm thanh do TTS tạo | Văn bản câu trả lời được phép phát | Các file WAV |
| `c001.wav` | File âm thanh tương ứng bình luận `c001` | Answer text của `c001` | Speech audio |
| `c002.wav` | File âm thanh tương ứng bình luận `c002` | Answer text của `c002` | Speech audio |

Tên `c001`, `c002` chỉ là ví dụ. Quy tắc đặt tên thực tế phải thống nhất với `comment_id` trong Pydantic schema.

### 3.7. `step2_lipsync/` — Output Part 2

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `step2_lipsync/` | Chứa các clip được xử lý lip-sync | Audio, source video, cấu hình render và kết quả license check | Video clips và render manifest |
| `c001.mp4` | Clip lip-sync tương ứng audio của bình luận `c001` | Audio `c001.wav` và source video | Video clip đồng bộ môi và lời nói |
| `c002.mp4` | Clip lip-sync tương ứng audio của bình luận `c002` | Audio `c002.wav` và source video | Video clip đồng bộ môi và lời nói |
| `render_manifest.json` | Ghi kết quả các tác vụ render, trạng thái và đường dẫn artifact | Thông tin job, clip, thời lượng và kết quả kiểm tra | Metadata để Part 3 tìm và sử dụng clip hợp lệ |

Part 2 có thể được thực hiện trên Google Colab/GPU worker. Khi đó, các artifact phải được import về đúng `run_id` trước khi thực hiện Part 3.

### 3.8. `step3_final/` — Output cuối cùng

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `step3_final/` | Chứa kết quả cuối cùng của pipeline | Answers, audio, clips và timeline | Demo video và báo cáo |
| `hostra_demo.mp4` | Video demo hoàn chỉnh sau quá trình compositing | Các video clips, timeline và cấu hình | Video trình diễn PoC |
| `timeline.json` | Lưu thứ tự và mốc thời gian của các sự kiện trình diễn | Audio durations, video durations và kịch bản | Timeline để đồng bộ các đoạn nội dung |
| `audit_log.json` | Lưu lịch sử xử lý, kiểm chứng và các quyết định của pipeline | Agent decisions, license checks, render events và lỗi | Audit records phục vụ truy vết |
| `benchmark.json` | Lưu các chỉ số đánh giá hiệu năng và chất lượng | Thời gian xử lý, lỗi và các phép đo thực tế | Báo cáo benchmark có cấu trúc |

Không nên sử dụng số benchmark giả định như kết quả đo thực tế.

## 4. `src/hostra_ai/` — Source Code chính

### 4.1. Python Package

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `src/` | Chứa source code của project | Python source files | Package ứng dụng |
| `src/hostra_ai/` | Python package chính của HOSTRA AI | Các module nội bộ | Các chức năng có thể import và sử dụng |
| `__init__.py` | Đánh dấu và khởi tạo Python package | Không bắt buộc | Package có thể được import theo cấu trúc dự án |

### 4.2. `core/` — Thành phần dùng chung

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `core/` | Chứa những thành phần nền tảng được nhiều module sử dụng | Configuration và dữ liệu chung | Shared utilities, schemas và logging |
| `config.py` | Đọc, kiểm tra và quản lý cấu hình hệ thống | `.env`, `app.yaml` và cấu hình được hỗ trợ | Application settings |
| `schemas.py` | Định nghĩa Pydantic models cho dữ liệu trao đổi giữa các module | Python objects, dict hoặc JSON tương ứng | Các đối tượng đã được validation và dữ liệu có thể serialize |
| `logging.py` | Cấu hình logging chung, hỗ trợ truy vết theo `run_id` | Log events và metadata | Log records thống nhất |

**`schemas.py` là nhiệm vụ A08.**

Các schema dự kiến:

- `CommentEvent`
- `AgentResponse`
- `AudioArtifact`
- `RenderJob`
- `VideoArtifact`
- `TimelineEvent`
- `AuditRecord`

Các trường dữ liệu cụ thể sẽ được thiết kế và review trong A08, chưa mặc định là contract cuối cùng.

## 5. Part 1 — Verified AI Agent & TTS

**Đường dẫn:** `src/hostra_ai/part1_agent_tts/`

**Mục tiêu:** Chuyển bình luận của khách hàng thành câu trả lời được kiểm chứng và file âm thanh.

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `part1_agent_tts/` | Chứa toàn bộ logic AI Agent và chuyển văn bản thành giọng nói | Product data, FAQ và comments | Verified answers và audio |
| `knowledge_engine.py` | Truy xuất thông tin sản phẩm và bằng chứng liên quan đến câu hỏi | Query, SKU, catalog và FAQ | Evidence hoặc kết quả retrieval |
| `verified_agent.py` | Điều phối quá trình tạo câu trả lời dựa trên ngữ cảnh sản phẩm và bằng chứng | CommentEvent, active SKU và retrieved evidence | Candidate answer hoặc AgentResponse theo thiết kế cuối |
| `answer_verifier.py` | Kiểm tra câu trả lời có được bằng chứng hỗ trợ hay không, có vi phạm quy tắc nghiệp vụ không | Candidate answer, evidence, dữ liệu có thẩm quyền | Verification result: cho phép, từ chối hoặc cần xử lý bổ sung |
| `tts_provider.py` | Giao tiếp với dịch vụ Text-to-Speech để tạo âm thanh | Verified answer text và voice settings | AudioArtifact và file WAV |
| `pipeline.py` | Điều phối các bước Comment → Retrieval → Agent → Verification → TTS | Comments, config và product knowledge | `answers.json`, audio files và metadata thực thi |

### Nguyên tắc quan trọng của Part 1

1. Giá bán, tồn kho và các thông tin có cấu trúc phải lấy từ nguồn dữ liệu có thẩm quyền.
2. LLM không được tự suy đoán những thông tin chưa có căn cứ.
3. Câu trả lời không vượt qua verification thì không được đưa trực tiếp sang TTS.
4. Khi thiếu thông tin, hệ thống phải có khả năng từ chối trả lời hoặc chuyển sang xử lý thủ công.
5. Mỗi câu trả lời phải liên kết được với bình luận và run tương ứng.

## 6. Part 2 — Video Lip-sync

**Đường dẫn:** `src/hostra_ai/part2_video_lipsync/`

**Mục tiêu:** Tạo các clip video đồng bộ với âm thanh đã được xác minh, đồng thời bảo đảm điều kiện sử dụng avatar hợp lệ.

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `part2_video_lipsync/` | Chứa logic xử lý và kiểm tra video lip-sync | WAV, source video, license và render settings | Video artifacts |
| `license_gate.py` | Kiểm tra phạm vi và hiệu lực quyền sử dụng danh tính số trước khi render | Creator license, avatar ID, mục đích sử dụng và thời điểm | License decision: allowed/denied cùng lý do |
| `lipsync_adapter.py` | Cung cấp giao diện thống nhất để gọi hoặc chuẩn bị công việc cho lip-sync provider | Audio, video nguồn, render parameters | RenderJob hoặc video artifact |
| `artifact_validator.py` | Kiểm tra output video có tồn tại, đọc được và đáp ứng những tiêu chí kỹ thuật đã thống nhất | Video files, audio và manifest | Validation result, lỗi và metadata chất lượng |

### Nguyên tắc quan trọng của Part 2

- Phải kiểm tra giấy phép trước khi thực hiện render.
- Không render danh tính số ngoài phạm vi được cho phép.
- Cần liên kết từng video clip với audio và comment tương ứng.
- Không coi việc file MP4 tồn tại là bằng chứng render thành công; cần kiểm tra các đặc tính kỹ thuật.
- Tách logic provider để sau này có thể thay đổi phương pháp lip-sync.

## 7. Part 3 — Live Compositor & Demo

**Đường dẫn:** `src/hostra_ai/part3_live_compositor/`

**Mục tiêu:** Điều phối các video clips, tạo timeline và giao diện trình diễn.

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `part3_live_compositor/` | Chứa các thành phần tích hợp và trình diễn kết quả | Answers, audio, clips và demo scenario | Final video, timeline và demo application |
| `timeline_builder.py` | Xây dựng thứ tự và mốc thời gian của các đoạn trình diễn | Answers, audio duration, video duration, kịch bản | `timeline.json` hoặc TimelineEvent objects |
| `video_compositor.py` | Ghép các video clips và xử lý bằng FFmpeg theo timeline | Video artifacts, timeline và cấu hình xuất video | `hostra_demo.mp4` |
| `teleprompter.py` | Điều phối lời nhắc và trạng thái hành động cho người thao tác sản phẩm | Active SKU, kịch bản, timeline và trạng thái xác nhận | Operator cues và trạng thái teleprompter |
| `app_server.py` | Cung cấp backend phục vụ demo, API và khả năng truy cập kết quả được phép | HTTP requests, runtime state và artifacts | API responses, trạng thái pipeline và tài nguyên demo |

### Nguyên tắc quan trọng của Part 3

- Timeline phải bảo đảm thứ tự phát đúng.
- Không phát lời thoại về sai SKU.
- Video và audio phải được đồng bộ theo metadata đo được.
- Demo phải phân biệt trạng thái đang xử lý, thành công và thất bại.
- Tính năng realtime hoàn chỉnh nằm ngoài phạm vi PoC ban đầu.

## 8. `notebooks/` — Môi trường thử nghiệm GPU

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `notebooks/` | Lưu notebook phục vụ thử nghiệm mô hình hoặc xử lý trên cloud | Notebooks và dữ liệu thử nghiệm | Kết quả thực nghiệm |
| `colab_lipsync_worker.ipynb` | Notebook chạy công việc lip-sync trên Google Colab/GPU | Source video, audio và render job metadata | Video clips và render manifest để import về project |

Notebook nên sử dụng cùng quy ước input/output với backend, tránh tạo một định dạng dữ liệu riêng chỉ dùng trong Colab.

## 9. `web/` — Frontend Demo

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `web/` | Chứa giao diện web phục vụ trình diễn PoC | HTML, CSS, JS và dữ liệu backend | Demo UI |
| `index.html` | Định nghĩa bố cục giao diện: video, bình luận, câu trả lời, trạng thái và log | Dữ liệu hiển thị do JS cung cấp | HTML interface |
| `styles.css` | Quy định giao diện trực quan, màu sắc, bố cục và responsive | HTML elements và CSS rules | Giao diện được trình duyệt hiển thị |
| `app.js` | Xử lý tương tác người dùng và giao tiếp với backend | User actions và API responses | Cập nhật UI, gọi API và điều khiển các thành phần demo |

Frontend dự kiến có các khu vực:

1. Video Demo Player
2. Product Information
3. Mock Comment Feed
4. AI Answer Display
5. Pipeline Status
6. Audit/Benchmark Summary

Danh sách này là đề xuất, chưa phải UI đã được triển khai.

## 10. `scripts/` — Các lệnh thực thi pipeline

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `scripts/` | Chứa các lệnh tiện ích để chuẩn bị, chạy và kiểm tra pipeline | CLI arguments, config và input files | Artifacts hoặc thông báo trạng thái |
| `validate_inputs.py` | Kiểm tra dữ liệu đầu vào trước khi chạy PoC | SKU catalog, FAQ, comments, license và thông tin file video | Validation report hoặc danh sách lỗi |
| `run_part1.py` | Chạy riêng pipeline Agent + TTS | Demo scenario và dữ liệu đầu vào | Answers, WAV và metadata Part 1 |
| `prepare_lipsync.py` | Chuẩn bị dữ liệu và danh sách job cần xử lý bằng lip-sync worker | Audio artifacts, base video, license decision | Job manifest và bộ input cho worker |
| `import_lipsync.py` | Import và kiểm tra các clip được render từ môi trường GPU | Video clips và render manifest | Artifacts Part 2 được đặt vào đúng run |
| `run_demo.py` | Điều phối quá trình tạo kết quả demo theo thứ tự phù hợp | Config, input data và các artifacts cần thiết | Final demo, timeline, audit và báo cáo |

Các script là điểm vào để chạy tác vụ. Business logic chính nên nằm trong `src/hostra_ai/`, tránh viết lặp lại toàn bộ logic trong scripts.

## 11. `tests/` — Kiểm thử hệ thống

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `tests/` | Chứa toàn bộ automated tests của project | Source code và test fixtures | Kết quả test |
| `fixtures/` | Lưu dữ liệu mẫu phục vụ kiểm thử | JSON và dữ liệu test có kiểm soát | Test inputs tái sử dụng |
| `unit/` | Kiểm thử từng hàm hoặc module độc lập | Hàm và mock dependencies | Unit test results |
| `test_knowledge.py` | Kiểm tra Knowledge Engine truy xuất đúng dữ liệu sản phẩm | Test queries, catalog và FAQ | Assertion pass/fail |
| `test_verification.py` | Kiểm tra khả năng phát hiện câu trả lời không có căn cứ hoặc vi phạm quy tắc | Candidate answers và evidence fixtures | Assertion pass/fail |
| `test_license.py` | Kiểm tra License Gate với giấy phép hợp lệ, hết hạn hoặc không đúng phạm vi | License fixtures và yêu cầu sử dụng | Assertion pass/fail |
| `test_timeline.py` | Kiểm tra thứ tự sự kiện, thời lượng và đồng bộ timeline | Audio/video metadata và scenario fixtures | Assertion pass/fail |
| `contract/` | Kiểm thử dữ liệu trao đổi giữa các module | Pydantic schemas và JSON fixtures | Contract test results |
| `test_artifact_contracts.py` | Kiểm tra các schema và artifact format có đúng hợp đồng dữ liệu đã thống nhất không | Valid/invalid JSON, manifests và schema definitions | Assertion pass/fail |
| `integration/` | Kiểm tra nhiều module hoạt động cùng nhau | Các module đã kết nối và test data | Integration test results |
| `test_demo_pipeline.py` | Kiểm tra luồng PoC từ input đến output bằng mock hoặc artifacts thử nghiệm | Demo fixture, mocked providers và pipeline | Kết quả end-to-end hoặc integration test |

### Các nhóm test cần ưu tiên

**Unit Test:** Một module hoạt động đúng hay không?

**Contract Test:** Module A tạo output có đúng cấu trúc mà module B yêu cầu hay không?

**Integration Test:** Khi kết nối nhiều module, luồng xử lý có hoạt động không?

Đối với A08, nhóm cần ưu tiên contract tests trước khi tích hợp Agent, TTS và Render.

## 12. `docs/` — Tài liệu dự án

| File / Folder | Công dụng | Input | Output |
|---|---|---|---|
| `docs/` | Chứa tài liệu kỹ thuật và hướng dẫn dành cho nhóm | Architecture, contracts, setup và test results | Tài liệu tham chiếu |
| `architecture.md` | Mô tả kiến trúc, vai trò module và luồng xử lý | Thiết kế kỹ thuật | Architecture documentation |
| `data_contracts.md` | Quy định schema và cấu trúc dữ liệu trao đổi giữa các phần | Field definitions, JSON examples và validation rules | Data contract specification |
| `setup_guide.md` | Hướng dẫn cài môi trường và chạy từng phần | OS, Python, dependencies, GPU requirements | Setup instructions |
| `benchmark.md` | Mô tả phương pháp đo, metric, dữ liệu kiểm thử và cách tổng hợp kết quả | Benchmark design và measured results | Benchmark documentation |
| `demo_script.md` | Mô tả kịch bản trình diễn cho người dùng, mentor hoặc giám khảo | Demo scenario, tính năng đã hoàn thành | Hướng dẫn trình diễn PoC |

File tài liệu chú thích cấu trúc project này có thể được lưu bổ sung dưới tên `docs/project_structure.md`.

## 13. Data Contract giữa các module

Đây là phần đặc biệt quan trọng vì ba thành viên có thể phát triển các phần độc lập.

| Nơi tạo dữ liệu | Nơi sử dụng | Dữ liệu trao đổi |
|---|---|---|
| Mock Comment Input | Part 1 Agent | CommentEvent |
| Knowledge Engine | Verified Agent / Verifier | Product evidence |
| Verified Agent / Verifier | TTS Provider | AgentResponse được phép phát |
| TTS Provider | Part 2 Render | AudioArtifact |
| License Gate | Render Adapter | License decision |
| Render Adapter / Colab Worker | Part 3 | VideoArtifact và RenderJob metadata |
| Part 1 + Part 2 | Timeline Builder | Answer, audio và video metadata |
| Timeline Builder | Video Compositor | TimelineEvent |
| Các module xử lý | Audit module / Dashboard | AuditRecord |
| Demo Pipeline | Evaluation / Dashboard | Benchmark results |

Các class và field cụ thể phải được chốt trong A08. Bảng này chỉ xác định vai trò và hướng trao đổi dữ liệu.

## 14. Những quy ước chung nhóm cần thống nhất

### 14.1. Quy tắc định danh

- `run_id`: Mã duy nhất của một lần chạy pipeline.
- `comment_id`: Mã định danh của một bình luận.
- `sku_id`: Mã định danh sản phẩm.
- `render_job_id`: Mã định danh tác vụ render nếu cần theo dõi độc lập.

Không nên sử dụng tên file làm định danh nghiệp vụ duy nhất. Tên file chỉ là cách lưu trữ artifact.

### 14.2. Quy tắc dữ liệu

- JSON sử dụng `snake_case` cho tên trường.
- Timestamp sử dụng định dạng ISO 8601 và quy ước timezone thống nhất, ưu tiên UTC.
- Thời lượng phải ghi rõ đơn vị (ví dụ `duration_ms`).
- Trạng thái được giới hạn bằng Enum hoặc Literal khi phù hợp.
- Trường bắt buộc, trường nullable và trường có giá trị mặc định phải được quy định rõ.
- Input không hợp lệ phải trả lỗi hoặc validation result rõ ràng.
- Không tự ý đổi tên trường trong contract khi chưa trao đổi với các module phụ thuộc.

### 14.3. Quy tắc lưu artifact

- Input và output phải có vị trí lưu thống nhất.
- Output được nhóm theo `run_id`.
- Metadata phải cho phép truy vết artifact đến dữ liệu nguồn.
- `shared_data/runs/` phải được đưa vào `.gitignore`.
- Không commit API key, dữ liệu cá nhân nhạy cảm, model weights lớn hoặc nội dung chưa được phép chia sẻ.
- Dữ liệu demo cần được phân biệt rõ với dữ liệu sản xuất thực tế.

### 14.4. Quy tắc code

- Mỗi file nên có một trách nhiệm chính.
- Business logic đặt trong `src/hostra_ai/`.
- `scripts/` chỉ điều phối hoặc gọi lại logic đã có.
- Những module có kết nối bên ngoài nên dễ mock để kiểm thử.
- Khi bổ sung hoặc thay đổi contract phải cập nhật test và tài liệu.
- Chỉ đánh dấu task hoàn thành khi đạt Acceptance Criteria đã thống nhất.

## 15. Thứ tự triển khai khuyến nghị

| Giai đoạn | Công việc | Kết quả |
|---|---|---|
| 1 | Repository skeleton, `.gitignore`, README, Python environment | Nhóm có môi trường và cấu trúc làm việc chung |
| 2 | Thiết kế data contract, Pydantic schemas | Thống nhất đầu vào/đầu ra giữa các module |
| 3 | Tạo sample data và contract tests | Kiểm tra dữ liệu đúng chuẩn |
| 4 | Phát triển Part 1 Agent + TTS | Verified answers và WAV |
| 5 | Phát triển Part 2 lip-sync | Rendered clips và manifest |
| 6 | Phát triển Part 3 compositor + web | Final demo |
| 7 | Integration testing, audit, benchmark | PoC hoàn chỉnh và có kết quả đánh giá |

Các giai đoạn có thể thực hiện song song khi data contract và dependency đã được thống nhất. Đây là thứ tự tham chiếu, không thay thế backlog task ID và deadline của nhóm.

## 16. Định nghĩa hoàn thành chung

Một task được xem là hoàn thành khi:

- Chức năng đúng với mục tiêu task.
- Input/output tuân thủ data contract đã thống nhất.
- Có test phù hợp và các test liên quan chạy thành công.
- Không chứa hardcoded secrets hoặc dữ liệu không được phép chia sẻ.
- Tài liệu liên quan được cập nhật.
- Pull Request đã được review và merge vào nhánh mục tiêu.

## 17. Kết luận

Cấu trúc HOSTRA AI PoC hướng tới một hệ thống chia module rõ ràng, có hợp đồng dữ liệu thống nhất, dễ kiểm thử và tích hợp.

Ba nguyên tắc quan trọng nhất:

1. **Contract First:** Thống nhất dữ liệu đầu vào và đầu ra trước khi các module phụ thuộc triển khai.
2. **Modular Development:** Các thành viên phát triển độc lập theo trách nhiệm được phân công, đồng thời duy trì khả năng tích hợp.
3. **Verifiable Results:** Mỗi giai đoạn tạo ra output có thể kiểm tra, truy vết và đánh giá.

**Mục tiêu của PoC không phải hoàn thiện mọi chức năng của sản phẩm thương mại, mà là chứng minh một pipeline Hybrid AI Commerce có thể vận hành, tạo ra kết quả quan sát được và đánh giá được về tính chính xác, độ trễ, chất lượng video và chi phí.**