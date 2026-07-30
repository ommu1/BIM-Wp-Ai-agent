# app/utils/session_store.py
# In-memory session store — manages per-user conversation state
# For production at scale, replace with Redis using aioredis

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

SESSION_TTL = 24 * 60 * 60  # 24 hours in seconds

@dataclass
class Session:
    phone: str
    stage: str = "start"
    flow: Optional[str] = None          # training | projects | student | payment
    sub_flow: Optional[str] = None      # arch_bim | mepf_bim | workshop | architecture | bim
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    student_id: Optional[str] = None
    student_data: Optional[Dict] = None
    is_verified: bool = False
    human_mode: bool = False
    awaiting_utr: bool = False
    enroll_course: Optional[Dict] = None
    zoom_link: Optional[str] = None
    message_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def touch(self):
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > SESSION_TTL

    def add_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > 15:
            self.history = self.history[-15:]
        self.touch()
        self.message_count += 1


class SessionStore:
    def __init__(self):
        self._store: Dict[str, Session] = {}

    def get(self, phone: str) -> Optional[Session]:
        session = self._store.get(phone)
        if session is None:
            return None
        if session.is_expired():
            del self._store[phone]
            return None
        return session

    def get_or_create(self, phone: str) -> Session:
        session = self.get(phone)
        if session is None:
            session = Session(phone=phone)
            self._store[phone] = session
        return session

    def update(self, phone: str, **kwargs) -> Session:
        session = self.get_or_create(phone)
        for k, v in kwargs.items():
            if hasattr(session, k):
                setattr(session, k, v)
        session.touch()
        return session

    def reset(self, phone: str):
        """Clear session — start fresh"""
        if phone in self._store:
            del self._store[phone]

    def count(self) -> int:
        return len(self._store)

    def all_active(self) -> List[Dict]:
        active = []
        for phone, s in self._store.items():
            if not s.is_expired():
                active.append({
                    "phone": phone,
                    "stage": s.stage,
                    "flow": s.flow,
                    "last_activity": s.last_activity,
                })
        return active

    def cleanup_expired(self) -> int:
        expired = [p for p, s in self._store.items() if s.is_expired()]
        for phone in expired:
            del self._store[phone]
        return len(expired)


# Global singleton
session_store = SessionStore()
