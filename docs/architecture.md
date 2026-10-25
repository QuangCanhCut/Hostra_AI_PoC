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
│   └── comment_policy.yaml                 # MỚI
│
├── shared_data/
│   ├── inputs/
│   │   ├── catalog_skus.json
│   │   ├── product_faq.md
│   │   ├── mock_comments.json
│   │   ├── creator_license.json
│   │   ├── base_operator.mp4
│   │   └── approved_product_scripts.json    # MỚI
│   │
│   └── runs/                                # Sinh khi chạy, không commit
│       └── <run_id>/
│           │
│           ├── manifest.json
│           │
│           ├── step1_agent_audio/
│           │   ├── comment_decisions.json    # MỚI
│           │   ├── answers.json
│           │   ├── speech_turns.json         # MỚI
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
│       ├── pipeline.py                     # Điều phối pipeline tổng thể
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
│       │   ├── comment_ingest.py            # MỚI
│       │   ├── comment_triage.py            # MỚI
│       │   ├── comment_queue.py             # MỚI
│       │   ├── conversation_memory.py       # MỚI
│       │   ├── knowledge_engine.py
│       │   ├── verified_agent.py
│       │   ├── answer_verifier.py
│       │   ├── speech_planner.py            # MỚI
│       │   ├── tts_provider.py
│       │   └── pipeline.py
│       │
│       ├── orchestration/                   # MỚI
│       │   ├── __init__.py
│       │   └── speech_scheduler.py
│       │
│       ├── part2_video_lipsync/
│       │   ├── __init__.py
│       │   ├── license_gate.py
│       │   ├── frame_mapper.py             # MỚI
│       │   ├── lipsync_adapter.py
│       │   ├── artifact_validator.py
│       │   └── render_service.py            # MỚI
│       │
│       ├── part3_demo_compositor/
│       │   ├── __init__.py
│       │   ├── run_manager.py               # MỚI
│       │   ├── timeline_builder.py
│       │   ├── timeline_validator.py        # MỚI
│       │   ├── video_compositor.py
│       │   ├── audit_service.py             # MỚI
│       │   ├── benchmark_collector.py       # MỚI
│       │   └── teleprompter.py
│       │
│       └── api/                             # TÁCH TỪ PART 3
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
│   ├── fixtures/
│   │   ├── part1/
│   │   ├── part2/
│   │   └── part3/
│   ├── unit/
│   │   ├── test_part1.py
│   │   ├── test_part2.py
│   │   └── test_part3.py
│   ├── contract/
│   │   ├── test_part1_contract.py
│   │   ├── test_part2_contract.py
│   │   └── test_part3_contract.py
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