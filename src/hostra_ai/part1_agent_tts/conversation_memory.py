"""Isolated, bounded conversation state for the verified sales agent."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConversationTurn:
    question: str
    answer: str


@dataclass(frozen=True)
class ConversationContext:
    last_resolved_sku_ids: tuple[str, ...] = ()
    last_intent: str | None = None
    turns: tuple[ConversationTurn, ...] = ()


class ConversationMemory:
    def __init__(self, max_turns_per_viewer: int = 5):
        if max_turns_per_viewer < 1:
            raise ValueError("max_turns_per_viewer must be positive")
        self.max_turns_per_viewer = max_turns_per_viewer
        self._contexts: dict[tuple[str, str], ConversationContext] = {}

    def get_context(self, run_id: str, viewer_id: str) -> ConversationContext:
        return self._contexts.get((run_id, viewer_id), ConversationContext())

    def update_context(self, run_id: str, viewer_id: str, *, resolved_sku_ids: tuple[str, ...],
                       intent: str, question: str, answer: str) -> None:
        previous = self.get_context(run_id, viewer_id)
        turns = (previous.turns + (ConversationTurn(question, answer),))[-self.max_turns_per_viewer:]
        self._contexts[(run_id, viewer_id)] = ConversationContext(tuple(resolved_sku_ids), intent, turns)

    def clear_viewer(self, run_id: str, viewer_id: str) -> None:
        self._contexts.pop((run_id, viewer_id), None)

    def clear_run(self, run_id: str) -> None:
        for key in tuple(self._contexts):
            if key[0] == run_id:
                del self._contexts[key]
