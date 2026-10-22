# HOSTRA AI — Hybrid AI Live Commerce PoC

**Real Products. Digital Faces. Borderless Commerce.**

HOSTRA AI là dự án nghiên cứu và phát triển nền tảng **Hybrid AI Live Commerce**, kết hợp người thao tác sản phẩm thật với AI Sales Agent, Text-to-Speech và công nghệ Digital Human nhằm hỗ trợ tự động hóa hoạt động giới thiệu và tư vấn sản phẩm qua video/livestream.

Repository này được sử dụng để phát triển **Proof of Concept (PoC)**, kiểm chứng tính khả thi về mặt kỹ thuật trước khi mở rộng thành sản phẩm MVP.

## 1. Project Overview

Trong livestream thương mại điện tử truyền thống, người dẫn chương trình phải đồng thời thực hiện nhiều nhiệm vụ: giới thiệu sản phẩm, thao tác trực tiếp, đọc bình luận và trả lời khách hàng.

HOSTRA AI đề xuất mô hình Hybrid AI, trong đó:

- **Human Operator:** Người thật trực tiếp cầm, xoay và trình diễn sản phẩm.
- **Verified AI Sales Agent:** Xử lý bình luận, truy xuất dữ liệu sản phẩm và tạo câu trả lời có kiểm chứng.
- **AI Voice & Digital Human:** Chuyển câu trả lời thành giọng nói và tạo video người đại diện số được cấp phép.
- **AI Teleprompter:** Hỗ trợ điều phối hành động của người thao tác theo kịch bản.
- **Monitoring & Audit:** Theo dõi quá trình xử lý, chất lượng và hiệu năng hệ thống.

Mục tiêu dài hạn là giảm khối lượng công việc lặp lại trong quá trình sản xuất nội dung thương mại, đồng thời duy trì sự hiện diện của sản phẩm vật lý và tính chính xác của thông tin tư vấn.

## 2. PoC Objectives

PoC tập trung kiểm chứng một pipeline Hybrid AI Commerce quy mô nhỏ với:

- Một merchant giả lập.
- Một bộ dữ liệu sản phẩm mẫu.
- Một Digital Human/Avatar có quyền sử dụng hợp lệ.
- Một danh sách bình luận giả lập.
- Một kịch bản trình diễn sản phẩm.
- Một video demo đầu ra.

**Các mục tiêu chính:**

1. Xây dựng AI Agent trả lời câu hỏi dựa trên thông tin sản phẩm có kiểm chứng.
2. Chuyển câu trả lời thành giọng nói bằng TTS.
3. Tạo video lip-sync tương ứng với âm thanh.
4. Đồng bộ video, audio và kịch bản trình diễn.
5. Xây dựng giao diện demo thể hiện kết quả pipeline.
6. Đánh giá độ chính xác, độ trễ, chất lượng output và chi phí xử lý.

**Giới hạn:** PoC ưu tiên phương pháp pre-rendered video. Livestream AI thời gian thực hoàn chỉnh, marketplace và tích hợp trực tiếp nhiều nền tảng chưa nằm trong phạm vi triển khai ban đầu.

## 3. System Architecture

Hệ thống được chia thành ba thành phần chính.

### Part 1 — Verified AI Agent & TTS

**Input:** Product Catalog, Product FAQ, Mock Comments.

**Processing:**

- Comment Processing
- Knowledge Retrieval
- AI Response Generation
- Answer Verification
- Text-to-Speech

**Output:** Verified Answers và Audio Files.

### Part 2 — Digital Human Video Lip-sync

**Input:** Verified Audio, Source Video, Creator License.

**Processing:**

- License Validation
- Video Lip-sync
- Artifact Validation

**Output:** Rendered Video Clips và Render Manifest.

### Part 3 — Live Compositor & Demo

**Input:** Verified Answers, Audio, Rendered Clips và Demo Scenario.

**Processing:**

- Timeline Construction
- Video Composition
- Teleprompter Coordination
- Monitoring & Audit

**Output:** Final Demo Video, Timeline, Audit Logs và Benchmark Results.

### Overall Pipeline

`Product Data + Mock Comments → Verified AI Agent → TTS → Video Lip-sync → Timeline & Compositor → Final Demo`

## 4. Technology Stack

Các công nghệ dự kiến sử dụng trong PoC:

| Component | Technology |
|---|---|
| Programming Language | Python 3.11 |
| Backend/API | FastAPI |
| Data Validation | Pydantic v2 |
| LLM | Gemini |
| Knowledge Retrieval | Structured JSON + FAQ Retrieval |
| Text-to-Speech | TTS Provider |
| Video Lip-sync | MuseTalk |
| Video Processing | FFmpeg |
| GPU Execution | Google Colab / GPU Runtime |
| Frontend | HTML, CSS, JavaScript |
| Testing | Pytest |
| Code Quality | Ruff |
| Version Control | Git & GitHub |
| CI | GitHub Actions |

Công nghệ và provider có thể thay đổi dựa trên kết quả thử nghiệm, độ ổn định, chi phí và chất lượng.

## 5. Repository Structure

| Directory | Responsibility |
|---|---|
| `configs/` | Application configuration và demo scenarios |
| `shared_data/inputs/` | Dữ liệu đầu vào mẫu |
| `shared_data/runs/` | Kết quả thực thi pipeline, không commit lên Git |
| `src/hostra_ai/core/` | Shared schemas, configuration và logging |
| `src/hostra_ai/part1_agent_tts/` | Verified AI Agent và TTS pipeline |
| `src/hostra_ai/part2_video_lipsync/` | License validation và video lip-sync |
| `src/hostra_ai/part3_live_compositor/` | Timeline, video compositing và demo backend |
| `notebooks/` | GPU/Colab experiments |
| `web/` | Frontend demo |
| `scripts/` | Pipeline execution và utility scripts |
| `tests/` | Unit, contract và integration tests |
| `docs/` | Architecture, data contracts và technical documentation |
| `.github/workflows/` | Continuous Integration |

Chi tiết chức năng, input và output của từng file sẽ được cập nhật trong `docs/project_structure.md`.

## 6. Getting Started

### Clone Repository

`git clone https://github.com/QuangCanhCut/Hostra_AI_PoC.git`

`cd Hostra_AI_PoC`

### Development Environment

Dự án sử dụng Python 3.11 làm phiên bản mục tiêu.

Hướng dẫn cài đặt dependencies, cấu hình environment, sử dụng GPU và chạy pipeline sẽ được bổ sung trong `docs/setup_guide.md` khi các module tương ứng được triển khai.

### Development Workflow

Nhóm sử dụng GitHub Flow kết hợp Feature Branch:

1. Đồng bộ branch `main`.
2. Tạo feature branch theo task ID.
3. Phát triển và kiểm thử.
4. Push branch lên GitHub.
5. Tạo Pull Request.
6. Code Review.
7. Merge vào `main` khi đạt yêu cầu.

**Branch naming examples:**

- `feature/A08-pydantic-schemas`
- `feature/agent-verification`
- `feature/video-lipsync`
- `fix/timeline-synchronization`
- `chore/project-skeleton`

Không phát triển trực tiếp các tính năng mới trên `main`.

## 7. Engineering Principles

Dự án tuân theo các nguyên tắc:

- **Contract First:** Thống nhất dữ liệu đầu vào và đầu ra trước khi tích hợp.
- **Modular Design:** Mỗi module có trách nhiệm rõ ràng.
- **Verified AI:** Không đưa ra khẳng định về sản phẩm khi thiếu bằng chứng phù hợp.
- **Human-in-the-loop:** Cho phép can thiệp thủ công trong những tình huống cần thiết.
- **Testable Components:** Ưu tiên các module có thể kiểm thử độc lập.
- **Traceability:** Kết quả xử lý phải liên kết với `run_id` và các định danh liên quan.
- **Responsible AI:** Chỉ sử dụng tài sản Digital Human trong phạm vi được cấp phép.

## 8. Current Development Status

**Status: Initial Development — PoC**

Hiện tại, nhóm đang thiết lập repository, kiến trúc dự án và các hợp đồng dữ liệu dùng chung.

Các hạng mục phát triển tiếp theo:

- [ ] Finalize project structure and development environment
- [ ] Define Pydantic schemas and data contracts
- [ ] Implement Verified AI Agent
- [ ] Integrate TTS
- [ ] Implement video lip-sync pipeline
- [ ] Implement timeline and video compositor
- [ ] Build demo interface
- [ ] Complete integration tests
- [ ] Conduct performance and quality benchmarks

Danh sách trên thể hiện định hướng phát triển, không phải cam kết các chức năng đã hoàn thành.

## 9. Security & Data Usage

- Không commit API keys, credentials hoặc file `.env`.
- Không đưa dữ liệu cá nhân và tài sản số chưa được cấp phép lên GitHub.
- Không commit các file video output, model weights hoặc artifacts lớn nếu chưa có chính sách lưu trữ phù hợp.
- Chỉ sử dụng hình ảnh, giọng nói và avatar trong phạm vi được chủ sở hữu cho phép.
- Phân biệt rõ dữ liệu mock, kết quả thử nghiệm và kết quả thực tế.

## 10. Project Vision

HOSTRA AI hướng tới mô hình thương mại kết hợp giữa khả năng trình diễn sản phẩm thực của con người và năng lực tương tác, tạo nội dung của AI.

PoC là bước đầu tiên để đánh giá khả năng xây dựng một hệ thống có thể mở rộng, với trọng tâm là **tính chính xác, khả năng kiểm soát, chất lượng trải nghiệm và hiệu quả vận hành**.

---

**HOSTRA AI — Hybrid AI Live Commerce**

*Developed as a Proof of Concept for technical validation and product research.*