hostra-ai-poc/
│
├── .env.example                         # Mẫu biến môi trường, được push GitHub
├── .gitignore                           # Bỏ qua secrets, cache, generated artifacts
├── README.md
├── pyproject.toml                       # Cấu hình Python package (dự kiến)
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt                 # Dependencies phát triển (dự kiến)
├── requirements-gpu.txt                 # Dependencies GPU (dự kiến)
│
├── .github/
│   └── workflows/
│       └── ci.yml                       # CI/CD: lint, unit, contract, integration tests
│
├── configs/
│   ├── app.yaml                         # Cấu hình ứng dụng, LLM, TTS, providers
│   ├── demo_scenario.yaml               # Kịch bản và timeline demo
│   ├── comment_policy.yaml              # M01: Triage, duplicate, queue, fairness
│   └── rag.yaml                         # M02: Chunking, retrieval, embedding, ranking
│
├── shared_data/
│   │
│   ├── inputs/                          # Dữ liệu nguồn, không bị ghi đè
│   │   ├── catalog_skus.json            # 2 laptop: ASUS và Lenovo
│   │   ├── product_faq.md               # 39 FAQ có tham chiếu bằng chứng
│   │   ├── mock_comments.json           # 20 bình luận mô phỏng
│   │   ├── creator_license.json         # Dữ liệu giấy phép mô phỏng
│   │   ├── base_operator.mp4            # Video nền liên tục (cần chuẩn bị)
│   │   └── approved_product_scripts.json # Kịch bản chờ review/phê duyệt
│   │
│   ├── indexes/                         # M02: Generated RAG indexes, không commit
│   │   └── rag/
│   │       ├── faq_chunks.json          # Parsed/chunked knowledge (generated)
│   │       ├── lexical_index/           # Keyword/BM25 index
│   │       ├── vector_index/            # Vector embeddings và index
│   │       └── index_manifest.json      # Knowledge/index/model version
│   │
│   └── runs/                            # Artifacts sinh khi chạy, không commit
│       └── <run_id>/
│           │
│           ├── manifest.json            # RunManifest
│           │
│           ├── step1_agent_audio/
│           │   ├── comment_decisions.json
│           │   ├── answers.json         # AgentResponse đã kiểm chứng
│           │   ├── speech_turns.json
│           │   ├── retrieval_trace.json # M02/M03: Evidence và truy xuất (đề xuất)
│           │   └── audio/
│           │       └── <audio_id>.wav
│           │
│           ├── step2_lipsync/
│           │   ├── render_jobs.json
│           │   ├── video_artifacts.json
│           │   └── overlays/
│           │       └── <render_id>.mp4
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
│       ├── pipeline.py                  # Điều phối pipeline toàn hệ thống
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py                # Cấu hình chung
│       │   ├── logging.py               # Logging, tracing
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── common.py
│       │       ├── part1.py             # CommentEvent, CommentDecision,
│       │       │                        # AgentResponse, SpeechTurn, AudioArtifact
│       │       ├── part2.py             # RenderJob, VideoArtifact
│       │       └── part3.py             # RunManifest, TimelineEvent, AuditRecord
│       │
│       ├── part1_agent_tts/
│       │   ├── __init__.py
│       │   │
│       │   │   # ==========================================
│       │   │   # MILESTONE 01 - COMMENT PROCESSING
│       │   │   # ĐÃ TRIỂN KHAI VÀ KIỂM THỬ CHỨC NĂNG
│       │   │   # ==========================================
│       │   │
│       │   ├── comment_ingest.py        # JSON -> CommentEvent
│       │   ├── comment_policy.py        # Đọc policy YAML
│       │   ├── comment_decisions.py     # Factory tạo CommentDecision
│       │   ├── comment_triage.py        # Duplicate, spam, off-topic, scoring
│       │   ├── comment_queue.py         # Ready, deferred, TTL, fairness
│       │   │
│       │   │   # ==========================================
│       │   │   # MILESTONE 02 - KNOWLEDGE ENGINE & RAG
│       │   │   # MODULAR RAG ARCHITECTURE (MỚI)
│       │   │   # ==========================================
│       │   │
│       │   ├── knowledge_engine.py      # Facade/API nội bộ của Knowledge Engine
│       │   │
│       │   ├── knowledge/
│       │   │   ├── __init__.py
│       │   │   │
│       │   │   │   # M02.1 - KNOWLEDGE PREPARATION
│       │   │   ├── models.py             # FAQChunk, RetrievedEvidence,
│       │   │   │                         # internal metadata models
│       │   │   ├── catalog_repository.py # Structured Catalog Lookup
│       │   │   ├── faq_parser.py         # Parse Markdown FAQ
│       │   │   ├── chunking.py           # Structure-aware FAQ chunking
│       │   │   │
│       │   │   │   # M02.2 - LEXICAL RETRIEVAL
│       │   │   ├── lexical_retriever.py  # Keyword Search / BM25 baseline
│       │   │   │
│       │   │   │   # M02.3 - SEMANTIC RETRIEVAL
│       │   │   ├── embedding_provider.py # Embedding model adapter
│       │   │   ├── vector_index.py      # Vector index build/load/search
│       │   │   │
│       │   │   │   # M02.4 - HYBRID RETRIEVAL
│       │   │   ├── retriever.py         # Retrieval routing, filtering,
│       │   │   │                        # combine lexical + semantic results
│       │   │   └── ranker.py            # Reranking / fusion / Top-K
│       │   │
│       │   │   # ==========================================
│       │   │   # MILESTONE 03 - VERIFIED AI SALES AGENT
│       │   │   # ==========================================
│       │   │
│       │   ├── conversation_memory.py   # Memory theo run_id + viewer_id
│       │   ├── verified_agent.py        # Observation, intent, tool calling,
│       │   │                            # LLM generation
│       │   ├── answer_verifier.py       # Kiểm chứng nội dung bằng evidence
│       │   │
│       │   │   # ==========================================
│       │   │   # MILESTONE 04 - SPEECH PLANNER & TTS
│       │   │   # ==========================================
│       │   │
│       │   ├── speech_planner.py        # AgentResponse/Script -> SpeechTurn
│       │   ├── tts_provider.py          # SpeechTurn -> WAV + AudioArtifact
│       │   │
│       │   │   # ==========================================
│       │   │   # MILESTONE 05 - INTEGRATION & EVALUATION
│       │   │   # ==========================================
│       │   │
│       │   └── pipeline.py              # Pipeline tích hợp Part 1
│       │
│       ├── orchestration/
│       │   ├── __init__.py
│       │   └── speech_scheduler.py      # Admission -> TTS -> Final Scheduling
│       │                                # Kiểm soát timeline, overlap, duration
│       │
│       ├── part2_video_lipsync/
│       │   ├── __init__.py
│       │   ├── license_gate.py          # Kiểm tra quyền hình ảnh/giọng nói
│       │   ├── frame_mapper.py          # Timestamp -> Video frame range
│       │   ├── lipsync_adapter.py       # Kết nối model lip-sync
│       │   ├── artifact_validator.py    # Kiểm tra file và metadata render
│       │   └── render_service.py        # Điều phối render jobs
│       │
│       ├── part3_demo_compositor/
│       │   ├── __init__.py
│       │   ├── run_manager.py           # Khởi tạo RunManifest
│       │   ├── timeline_builder.py      # Xây dựng timeline
│       │   ├── timeline_validator.py    # Kiểm tra constraints
│       │   ├── video_compositor.py      # Ghép audio/overlay lên base video
│       │   ├── audit_service.py         # Audit trail
│       │   ├── benchmark_collector.py   # Đo latency, chất lượng, hiệu năng
│       │   └── teleprompter.py          # Operator cues theo timeline
│       │
│       └── api/
│           ├── __init__.py
│           ├── app.py                   # FastAPI application
│           └── routes.py                # API endpoints
│
├── notebooks/
│   └── colab_lipsync_worker.ipynb       # GPU lip-sync experiments
│
├── web/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── scripts/
│   ├── validate_inputs.py              # Kiểm tra dữ liệu đầu vào
│   ├── run_part1.py                    # Entry point Part 1 hoàn chỉnh
│   ├── prepare_lipsync.py
│   ├── import_lipsync.py
│   ├── run_demo.py                     # Chạy pipeline demo tổng thể
│   │
│   ├── script_part1/
│   │   └── run_milestone01.py          # Runner M01 đã chạy thành công
│   │
│   └── script_rag/                     # Scripts M02 (tạo khi triển khai)
│       ├── prepare_knowledge.py        # M02.1: Parse và validate knowledge
│       ├── build_index.py              # M02.2/3: Build lexical/vector indexes
│       └── evaluate_retrieval.py       # M02.5: Đánh giá Retrieval
│
├── tests/
│   ├── fixtures/
│   │   ├── part1/
│   │   ├── part2/
│   │   ├── part3/
│   │   └── rag/
│   │       └── retrieval_eval.json     # M02.5: Golden query/evidence dataset
│   │
│   ├── unit/
│   │   ├── test_part1.py               # Pydantic contract validators
│   │   ├── test_part2.py
│   │   ├── test_part3.py
│   │   │
│   │   └── test_part1_code/
│   │       │
│   │       │   # M01 - ĐÃ TRIỂN KHAI
│   │       ├── test_comment_ingest.py
│   │       ├── test_comment_triage.py
│   │       ├── test_comment_queue.py
│   │       │
│   │       │   # M02 - BỔ SUNG DẦN
│   │       ├── test_catalog_repository.py
│   │       ├── test_faq_parser.py
│   │       ├── test_chunking.py
│   │       ├── test_knowledge_engine.py
│   │       ├── test_lexical_retriever.py
│   │       ├── test_embedding_provider.py
│   │       ├── test_vector_index.py
│   │       ├── test_retriever.py
│   │       └── test_ranker.py
│   │
│   ├── contract/
│   │   ├── test_part1_contract.py
│   │   ├── test_part2_contract.py
│   │   └── test_part3_contract.py
│   │
│   └── integration/
│       ├── test_comment_processing.py  # M01: Ingest -> Triage -> Queue
│       ├── test_knowledge_engine.py     # M02: Catalog + FAQ + Retrieval
│       ├── test_part1_pipeline.py       # Part 1 end-to-end
│       ├── test_part2_pipeline.py
│       ├── test_part3_pipeline.py
│       └── test_demo_pipeline.py
│
└── docs/
    ├── architecture.md                 # Kiến trúc tổng thể + Modular RAG
    ├── project_structure.md            # Cây thư mục và mô tả chức năng
    ├── data_contract_vi.md             # 10 public data contracts
    ├── setup_guide.md
    ├── test_plan.md
    ├── benchmark.md
    ├── demo_script.md
    └── rag_design.md                   # M02: Chunking, Retrieval,
                                        # Embeddings, Ranking, Evidence, Eval


=============================================================
QUY ƯỚC TRIỂN KHAI
=============================================================

1. Đây là CẤU TRÚC MỤC TIÊU V2.1, không phải danh sách
   tất cả file đã tồn tại trên máy.

2. Milestone 01 đã hoàn thành kiểm thử chức năng:
   - 17/17 unit tests M01 passed
   - 17/17 contract tests Part 1 passed
   - 241 tests và 65 subtests trong full suite passed

3. Milestone 02 bắt đầu từ M02.1:
   - knowledge/models.py
   - knowledge/catalog_repository.py
   - knowledge/faq_parser.py
   - knowledge/chunking.py
   - knowledge_engine.py (facade)

4. Các file M02.2 - M02.5 chỉ được tạo khi triển khai
   nhiệm vụ tương ứng.

5. Knowledge Engine có hai pipeline:
   A. Offline Indexing:
      Catalog/FAQ -> Parse -> Chunk -> Index
   B. Query Retrieval:
      Query -> Catalog Lookup / FAQ Retrieval
            -> Ranking -> Evidence

6. Catalog là nguồn chuẩn cho giá, tồn kho và thông số.

7. FAQ dùng để cung cấp kiến thức, giải thích, so sánh
   và hỗ trợ tư vấn. Không tự coi FAQ là bằng chứng
   đã xác minh nếu mâu thuẫn với Catalog.

8. LLM Generation và Answer Verification thuộc M03.
   Không đặt logic gọi LLM trong FAQ Parser, Chunker
   hoặc Vector Index.

9. Speech Scheduler thuộc Orchestration, không thuộc
   Knowledge Engine hay Comment Queue.

10. Không thay đổi 10 public Pydantic Data Contracts
    nếu chưa được nhóm review và phê duyệt.

11. Không commit:
    - .env
    - generated vector indexes
    - shared_data/runs/
    - model weights lớn
    - dữ liệu hình ảnh/giọng nói chưa được phép sử dụng

12. M02.1 và M02.2 chạy local, không cần API Key.
    M02.3 có thể dùng embedding API hoặc model local.

13. Mỗi thay đổi phải có unit tests và regression tests.
    Không được phá vỡ kết quả Milestone 01.

14. Tất cả các file đánh dấu "dự kiến" hoặc thuộc
    Milestone chưa triển khai chỉ là kế hoạch kiến trúc.
    Không tạo trước hàng loạt file rỗng.
