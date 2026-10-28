"""Chạy lại bình luận mock không cần API key, từ bất kỳ thư mục làm việc nào."""
from collections import Counter
from datetime import timedelta
from pathlib import Path
import sys

# Xác định root theo vị trí script để import và đọc dữ liệu đúng trên Windows.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hostra_ai.part1_agent_tts.comment_ingest import ingest_comments, load_catalog_skus
from hostra_ai.part1_agent_tts.comment_policy import load_policy
from hostra_ai.part1_agent_tts.comment_queue import CommentQueue
from hostra_ai.part1_agent_tts.comment_triage import CommentTriage


def main() -> None:
    """Mô phỏng ingest → triage → queue và in quyết định cuối của từng bình luận."""
    policy = load_policy(ROOT / "configs/comment_policy.yaml")
    skus = load_catalog_skus(ROOT / "shared_data/inputs/catalog_skus.json")
    events = ingest_comments(ROOT / "shared_data/inputs/mock_comments.json", run_id="RUN-001", catalog_skus=skus)
    triage, queue = CommentTriage(policy), CommentQueue(policy)
    handed_off = []
    # Giả lập một lượt bàn giao mỗi 12 giây, không dùng giờ thực của máy.
    next_service = events[0].received_at if events else None
    for event in events:
        while next_service is not None and next_service < event.received_at:
            queue.reevaluate(now=next_service)
            item = queue.pop(now=next_service)
            if item:
                handed_off.append(item)
            next_service += timedelta(seconds=12)
        # Trước khi nhận bình luận mới, cập nhật những mục đang deferred.
        queue.reevaluate(now=event.received_at)
        queue.admit(event, triage.evaluate(event), now=event.received_at)
    # Tiếp tục đồng hồ đến khi không còn mục sẵn sàng hoặc đang chờ.
    while queue.ready_count or queue.deferred_count:
        queue.reevaluate(now=next_service)
        item = queue.pop(now=next_service)
        if item:
            handed_off.append(item)
        next_service += timedelta(seconds=12)
    # Một bình luận có thể có nhiều quyết định; bảng hiển thị quyết định cuối.
    latest = {(d.run_id, d.comment_id): d for d in queue.decisions}
    print("comment_id  action     reason       score")
    for event in events:
        d = latest[(event.run_id, event.comment_id)]
        print(f"{d.comment_id:11} {d.action:10} {(d.reason_code or '-'):12} {d.priority_score:3}")
    print(f"Comments: {len(events)}; actions: {dict(Counter(d.action for d in latest.values()))}; handed off: {len(handed_off)}")


if __name__ == "__main__":
    main()
