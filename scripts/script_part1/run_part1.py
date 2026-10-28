"""Run the Part 1 offline pipeline with mock audio."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from hostra_ai.part1_agent_tts.pipeline import Part1Pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description='Run Part 1 offline with mock silence WAVs.')
    parser.add_argument('--run-id', default=None)
    parser.add_argument('--comments', type=Path, default=ROOT / 'shared_data/inputs/mock_comments.json')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/app.yaml')
    parser.add_argument('--output-root', type=Path, default=ROOT,
                        help='Workspace root within the project; output goes under shared_data/runs.')
    parser.add_argument('--tts-provider', choices=['mock'], default='mock')
    parser.add_argument('--service-interval-seconds', type=int, default=0,
                        help='0 processes each arrival immediately; positive values simulate queue service.')
    args = parser.parse_args()
    run_id = args.run_id or 'RUN-M05-' + uuid4().hex[:12]
    try:
        result = Part1Pipeline(project_root=ROOT, output_root=args.output_root,
            comments_path=args.comments, config_path=args.config,
            service_interval_seconds=args.service_interval_seconds).run(run_id)
    except Exception as exc:
        print(f'Part 1 run failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
    print(f"Output: {args.output_root / 'shared_data' / 'runs' / run_id / 'step1_agent_audio'}")
    return 0 if result['status'] == 'completed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
