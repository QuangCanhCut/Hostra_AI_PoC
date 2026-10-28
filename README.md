# HOSTRA AI — Hybrid AI Live Commerce PoC

**Real Products. Digital Faces. Borderless Commerce.**

HOSTRA AI là dự án nghiên cứu mô hình **Hybrid AI Live Commerce**: người thật thao tác với sản phẩm vật lý, còn hệ thống AI hỗ trợ xử lý câu hỏi, tạo lời thoại có kiểm chứng, tổng hợp giọng nói và hiển thị Digital Human được cấp phép.

Repository này phục vụ việc phát triển **Proof of Concept (PoC)** nhằm kiểm chứng tính khả thi kỹ thuật. Đây **chưa phải** hệ thống livestream AI thời gian thực hay một sản phẩm thương mại hoàn chỉnh.

> **Trạng thái cập nhật: 25/10/2026 — Contract-first development.** Nhóm đã hoàn thành thiết kế, hiện thực và kiểm thử Data Contract bằng Pydantic cho cả ba Part (10 schema), cập nhật tài liệu liên quan và merge lên `main`. Các runtime services, workers, API, Web UI và pipeline end-to-end **chưa được triển khai hoặc xác nhận hoạt động**.

Milestone 01 bổ sung xử lý bình luận offline trong Part 1. Xem [hướng dẫn Comment Processing](docs/milestone01_comment_processing.md) để chạy demo, kiểm thử và tìm hiểu các giả định.

## 1. Project Overview

Trong hoạt động bán hàng qua livestream/video, người dẫn thường phải đồng thời thao tác sản phẩm, trình bày, đọc bình luận và tư vấn. HOSTRA AI nghiên cứu cách tách hai vai trò:

- **Human Operator:** Người thật cầm, mở, xoay và trình diễn sản phẩm. Trong PoC, hoạt động này được ghi lại bằng video nguồn `base_operator.mp4`.
- **Verified AI Sales Agent:** Đọc bình luận giả lập, gắn với SKU đang được giới thiệu, truy xuất thông tin sản phẩm và tạo câu trả lời dựa trên bằng chứng.
- **AI Voice & Licensed Digital Human:** Chuyển câu trả lời hợp lệ thành âm thanh TTS và tạo video lip-sync bằng tài sản số có quyền sử dụng.
- **Timeline & Compositor:** Lập lịch, đồng bộ lời nói/video theo timeline và ghép thành một video demo liên tục.
- **Teleprompter & Audit:** Hỗ trợ kịch bản thao tác và ghi dấu vết xử lý; các cơ chế vận hành thực tế vẫn nằm trong backlog.

Tầm nhìn dài hạn còn bao gồm live studio, kết nối nền tảng thương mại và mô hình cấp phép Digital Human. Những năng lực này **không thuộc phạm vi đã hoàn thành của PoC hiện tại**.

## 2. PoC Scope & Objectives

### Phạm vi thử nghiệm

- Một merchant và bộ sản phẩm/FAQ mẫu.
- Một nguồn video người thao tác (`base_operator.mp4`).
- Một tài sản Digital Human/Avatar và giấy phép sử dụng hợp lệ.
- Một danh sách mock comments, trạng thái Active SKU và kịch bản demo.
- Một luồng xử lý **offline / pre-rendered** để tạo ra **một video MP4 liên tục** cùng artifacts, timeline và audit tương ứng.

### Mục tiêu kỹ thuật

1. Xây dựng luồng tiếp nhận/lọc bình luận, trả lời có kiểm chứng và cơ chế từ chối khi thiếu dữ liệu hoặc điều kiện xử lý.
2. Tạo `SpeechTurn` và audio TTS cho các câu trả lời được phép phát.
3. Kiểm tra điều kiện giấy phép/media đầu vào và tạo video lip-sync tương ứng.
4. Đồng bộ comment, câu trả lời, âm thanh, clip và video nguồn trên một timeline chung.
5. Ghép video demo, hiển thị artifacts/trạng thái qua giao diện và ghi audit.
6. Kiểm thử chất lượng trả lời, độ trễ từng bước, tính đồng bộ A/V, thời gian render và chi phí.

### Ngoài phạm vi PoC hiện tại

- Livestream AI tương tác thời gian thực hoàn chỉnh.
- Tự động lấy bình luận hoặc phát trực tiếp lên TikTok Shop/Shopee/YouTube.
- Multi-merchant SaaS, thanh toán, đơn hàng thật và Digital Human Marketplace.
- Tự động nhận diện mọi thao tác sản phẩm bằng Computer Vision.

## 3. System Architecture

Hệ thống được chia thành ba Part, kết nối qua các **Data Contract** dùng chung.

### Part 1 — Verified AI Agent & TTS

**Input:** Mock comments, Active SKU, Product Catalog, FAQ, các quy tắc xử lý.

**Luồng dự kiến:**

1. Tiếp nhận và chuẩn hóa comment.
2. Quyết định comment có đủ điều kiện xử lý hay cần bỏ qua/chặn/làm rõ.
3. Truy xuất tri thức, tạo câu trả lời và đối chiếu bằng chứng.
4. Lập lịch lượt phát ngôn (`SpeechTurn`).
5. Tổng hợp TTS cho câu trả lời đủ điều kiện, tạo `AudioArtifact`.

**Data Contracts:** `CommentEvent`, `CommentDecision`, `AgentResponse`, `SpeechTurn`, `AudioArtifact`.

**Nguyên tắc:** Phản hồi `blocked` không được đưa tới TTS để phát thành tiếng. Kiểm tra bằng chứng, đối chiếu SKU và file thực tế thuộc tầng service/integration.

### Part 2 — Digital Human Video Lip-sync

**Input:** `SpeechTurn`, `AudioArtifact`, source video, thông tin quyền sử dụng Digital Human.

**Luồng dự kiến:**

1. License/Media Preflight.
2. Điều phối một lần xử lý lip-sync qua `RenderJob`.
3. Worker/adapter gọi công nghệ lip-sync (MuseTalk là phương án đang dự kiến thử nghiệm).
4. Kiểm tra artifact và phát hành `VideoArtifact` cho Part 3.

**Data Contracts:** `RenderJob`, `VideoArtifact`.

Mỗi `RenderJob` là một snapshot cho lần thử render; trạng thái công việc, quyền sử dụng, sự tồn tại của file và chất lượng media phải được kiểm tra ở tầng runtime, không suy ra rằng schema hợp lệ là video đã render thành công.

### Part 3 — Timeline, Compositor & Audit

**Input:** Manifest phiên chạy, video nguồn, comments, speech/audio artifacts, video overlays và demo scenario.

**Luồng dự kiến:**

1. Tạo manifest cho một `run_id` và mốc neo timeline (`timeline_start_at`).
2. Quy đổi sự kiện sang trục thời gian video đích; xây dựng các `TimelineEvent`.
3. Lập lịch/kiểm tra khoảng phát và các điều kiện đồng bộ.
4. Compositor dùng FFmpeg để ghép video liên tục và âm thanh tương ứng.
5. Ghi `AuditRecord`, kết quả thực thi và số liệu benchmark.

**Data Contracts:** `RunManifest`, `TimelineEvent`, `AuditRecord`.

PoC đang thiết kế trên timeline **CFR 25 FPS**. Các khoảng frame dùng quy ước `[start_frame, end_frame)`; timestamp UTC và offset tương đối của video phải được quy đổi nhất quán. Đây là quy tắc thiết kế, **chưa phải kết quả kiểm thử đồng bộ A/V thực tế**.

### Overall Pipeline (target design)

```text
Product Catalog / FAQ / Active SKU       Mock Comments
                 \                           /
                  v                         v
             Comment Processing & Decision
                            |
                  Verified AI Response
                            |
                   SpeechTurn / TTS
                            |
                       AudioArtifact
                            |
              License Check / RenderJob
                            |
                  Lip-sync VideoArtifact
                            |
Base Operator Video ------> Timeline / Frame Mapping
                            |
                 FFmpeg Video Compositor
                            |
          Final Demo MP4 + Audit + Benchmarks
```

Sơ đồ trên biểu diễn luồng **dự kiến triển khai**, không khẳng định các module đã chạy end-to-end.

## 4. Data Contracts — Completed

Data Contract là hạng mục kỹ thuật đã được nhóm hoàn thành và merge vào `main` ngày **25/10/2026**.

| Part | Schema | Vai trò |
|---|---|---|
| Part 1 | `CommentEvent` | Bình luận đầu vào cùng thông tin phiên, người xem, SKU và thời điểm |
| Part 1 | `CommentDecision` | Quyết định xử lý/chặn/làm rõ bình luận |
| Part 1 | `AgentResponse` | Nội dung phản hồi, trạng thái và tham chiếu bằng chứng |
| Part 1 | `SpeechTurn` | Lượt lời thoại và dữ liệu lập lịch phát |
| Part 1 | `AudioArtifact` | Metadata và đường dẫn file âm thanh TTS |
| Part 2 | `RenderJob` | Yêu cầu/lần thử render lip-sync và trạng thái xử lý |
| Part 2 | `VideoArtifact` | Metadata clip overlay do worker tạo ra |
| Part 3 | `RunManifest` | Ngữ cảnh, chế độ thực thi và timeline của một run |
| Part 3 | `TimelineEvent` | Sự kiện `clip`/`pause` trên timeline video đích |
| Part 3 | `AuditRecord` | Bản ghi truy vết xử lý và sự kiện hệ thống |

Các schema dùng **Pydantic v2**, áp dụng nguyên tắc strict validation (`extra="forbid"`), immutable snapshots (`frozen=True`), định danh nhất quán và UTC-aware timestamps.

**Ranh giới trách nhiệm:** Schema kiểm tra tính hợp lệ nội bộ của một bản ghi. Việc xác minh file tồn tại, giấy phép thực tế, bằng chứng, quan hệ chéo giữa records, chuyển trạng thái, FPS/PTS, A/V sync và xử lý FFmpeg thuộc **services, workers và integration tests**.

## 5. Technology Stack (Planned / Under Evaluation)

| Component | Technology | Status |
|---|---|---|
| Programming Language | Python 3.11 (target) | Chọn làm môi trường mục tiêu |
| Data Validation | Pydantic v2 | Đã dùng cho Data Contracts |
| Unit / Contract Testing | Pytest | Đã kiểm thử schema ba Part |
| Backend/API | FastAPI | Chưa triển khai |
| LLM | Gemini | Dự kiến tích hợp |
| Product Retrieval | Structured JSON + FAQ retrieval | Dự kiến tích hợp |
| TTS | TTS provider (chưa chốt) | Dự kiến thử nghiệm |
| Video Lip-sync | MuseTalk | Dự kiến thử nghiệm |
| Video Compositing | FFmpeg | Chưa tích hợp end-to-end |
| GPU Runtime | Colab / GPU environment | Dự kiến dùng cho thử nghiệm |
| Frontend | HTML, CSS, JavaScript | Chưa triển khai demo hoàn chỉnh |
| Code Quality / CI | Ruff, GitHub Actions | Cấu hình/hoàn thiện theo tiến độ |
| Version Control | Git & GitHub | Feature branch + Pull Request |

Technology/provider có thể được thay đổi sau khi đo chất lượng, độ trễ, chi phí và mức độ ổn định.

## 6. Repository Structure

Cấu trúc module dưới đây là **bố cục thiết kế**. Một số thư mục mới ở dạng skeleton/placeholder; không mặc định mỗi module đã có implementation:

```text
hostra-ai-poc/
├── configs/                     # App, scenario và comment policies
├── shared_data/
│   ├── inputs/                  # Catalog, FAQ, mock comments, source media, license
│   └── runs/                    # Outputs theo run_id (không commit)
├── src/hostra_ai/
│   ├── core/
│   │   └── schemas/
│   │       ├── common.py        # Shared enums, constraints, constants
│   │       ├── part1.py         # 5 Data Contracts của Part 1
│   │       ├── part2.py         # 2 Data Contracts của Part 2
│   │       ├── part3.py         # 3 Data Contracts của Part 3
│   │       └── __init__.py
│   ├── part1_agent_tts/         # Agent, verification, TTS (planned runtime)
│   ├── part2_video_lipsync/     # License gate, render worker (planned runtime)
│   └── part3_live_compositor/   # Timeline, FFmpeg, orchestration (planned runtime)
├── tests/
│   ├── unit/                    # Unit tests, gồm schema tests
│   ├── contract/                # Contract validation tests
│   └── integration/             # Integration tests (to be implemented)
├── notebooks/                   # Experiments (GPU / lip-sync)
├── web/                         # Demo frontend (planned)
├── scripts/                     # Run/demo/utility scripts
├── docs/                        # Architecture, Data Contract, setup, worklogs
├── .github/workflows/           # CI configuration
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

Xem tài liệu Data Contract trong `docs/` để biết chi tiết field, giá trị hợp lệ, các bất biến và quy tắc kiểm thử. Sơ đồ này sẽ tiếp tục được đối chiếu với cây thư mục thực tế khi nhóm triển khai runtime.

## 7. Getting Started (Current Stage)

```bash
git clone https://github.com/QuangCanhCut/Hostra_AI_PoC.git
cd Hostra_AI_PoC
```

Môi trường mục tiêu của nhóm là Python 3.11. Sau khi cài dependency development theo hướng dẫn/cấu hình của repository, có thể chạy test hiện có bằng:

```bash
python -m pytest
```

**Lưu ý:** Test Data Contract thành công **không đồng nghĩa** pipeline Agent → TTS → Lip-sync → Compositor đã chạy. Hướng dẫn cài model/GPU/provider và chạy demo end-to-end sẽ được cập nhật khi các module hoàn thành.

## 8. Development Workflow

Nhóm sử dụng **GitHub Flow + Feature Branch**:

1. Đồng bộ `main` trước khi bắt đầu task.
2. Tạo nhánh riêng theo công việc, ví dụ `feature/part1-agent-service`, `feature/part2-lipsync-worker`, `feature/part3-video-compositor`.
3. Triển khai và viết tests phù hợp.
4. Push branch, tạo Pull Request và review cùng nhóm.
5. Merge vào `main` sau khi đạt các điều kiện đã thống nhất.
6. Đồng bộ `main` trước khi bắt đầu nhiệm vụ mới.

Không triển khai tính năng mới trực tiếp trên `main`.

## 9. Engineering Principles

- **Contract First:** Thống nhất input/output và invariants trước tích hợp.
- **Modular & Testable:** Tách schemas, services, workers và adapters; kiểm thử từng phần độc lập.
- **Verified AI:** Không tự tạo giá, tồn kho, công dụng hoặc chính sách sản phẩm khi không có bằng chứng phù hợp.
- **Human-in-the-loop:** Có cơ chế từ chối, làm rõ, tạm dừng hoặc chuyển sang thao tác thủ công.
- **Timeline Consistency:** Phân biệt UTC event timestamps với video-relative offsets và target frames.
- **Traceability:** Liên kết artifacts qua `run_id`, các IDs/correlation IDs; lưu trạng thái và audit.
- **Responsible AI:** Chỉ sử dụng hình ảnh/giọng nói/avatar trong phạm vi được cấp phép.
- **Measured Outcomes:** Đo cả độ chính xác, độ trễ, chất lượng A/V và chi phí thay vì chỉ hoàn thành demo trực quan.

## 10. Development Status — 25/10/2026

### Completed

- [x] Thống nhất mục tiêu và ranh giới kỹ thuật của PoC theo hướng **pre-rendered**.
- [x] Thiết kế kiến trúc 3 Part và repository skeleton.
- [x] Xây dựng **10 Pydantic Data Contracts** cho Part 1, Part 2, Part 3.
- [x] Xây dựng và chạy kiểm thử unit/contract cho các schema của cả 3 Part.
- [x] Hoàn thiện tài liệu Data Contract và merge các thay đổi liên quan vào `main`.

### Next — Runtime Implementation & Integration

- [ ] Rà soát backlog, phân công module và thống nhất điểm tích hợp giữa các thành viên.
- [ ] Triển khai comment handling, retrieval, answer verification, conversation memory và Agent orchestration.
- [ ] Triển khai SpeechScheduler và TTS service; tạo AudioArtifact thực.
- [ ] Triển khai License/Media Preflight, RenderJob Controller và MuseTalk worker.
- [ ] Triển khai FrameMapper, TimelineBuilder, TimelineValidator và FFmpeg compositor.
- [ ] Triển khai session orchestration, monitoring/audit và Web Demo.
- [ ] Viết integration/E2E tests cho toàn bộ pipeline, bao gồm trường hợp lỗi và phục hồi.
- [ ] Benchmark chất lượng trả lời, A/V sync, thời gian render, khả năng chạy GPU và chi phí.

**Nguyên tắc báo cáo tiến độ:** Các mục được đánh dấu hoàn thành chỉ phản ánh schema, kiểm thử contract và tài liệu; **chưa có xác nhận video demo end-to-end, hiệu năng thực tế hoặc livestream production**.

## 11. Security, Privacy & Content Rights

- Không commit API keys, secrets, `.env` hay thông tin nhạy cảm.
- Không commit video/voice/avatar chưa được cấp phép, model weights hoặc artifacts lớn khi chưa có chính sách lưu trữ.
- Chỉ sử dụng Digital Human trong phạm vi thời gian, mục đích, lãnh thổ và loại nội dung được cấp phép.
- Không giả định rằng schema `Creator License` hợp lệ thay thế được kiểm tra giấy phép thực tế ở runtime.
- Phân biệt dữ liệu **mock**, kết quả thực nghiệm, benchmark và kết quả vận hành thật.
- Không kết nối hoặc tự động phát trên nền tảng thương mại khi chưa xác minh quyền và chính sách tương ứng.

## 12. Project Vision

HOSTRA AI nghiên cứu một mô hình thương mại nơi **con người tiếp tục trình diễn sản phẩm thật**, còn AI đảm nhiệm phần tương tác và sản xuất nội dung có thể kiểm chứng, truy vết và đo lường.

PoC hiện tại là bước **technical validation**. Kết quả triển khai và benchmark thực tế sẽ quyết định liệu các module có đủ chất lượng, hiệu năng và độ an toàn để bước sang MVP hay không.

---

**HOSTRA AI — Hybrid AI Live Commerce**  
*Developed as a Proof of Concept for technical validation and product research.*
