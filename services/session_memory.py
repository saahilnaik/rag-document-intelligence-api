import threading
from collections import deque
from uuid import UUID

from core.config import get_settings


class SessionMemory:
    def __init__(self):
        self._sessions: dict[str, deque] = {}
        self._lock = threading.Lock()

    def _get_or_create(self, session_id: str) -> deque:
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=get_settings().MAX_CONVERSATION_TURNS)
        return self._sessions[session_id]

    def get_turns(self, session_id: UUID) -> list[dict]:
        sid = str(session_id)
        with self._lock:
            return list(self._get_or_create(sid))

    def add_turn(self, session_id: UUID, question: str, answer: str) -> None:
        sid = str(session_id)
        with self._lock:
            self._get_or_create(sid).append({"question": question, "answer": answer})

    def clear(self, session_id: UUID) -> None:
        sid = str(session_id)
        with self._lock:
            self._sessions.pop(sid, None)


session_memory = SessionMemory()
