"""S: 状态存储 — 跨轮次持久化 + 崩溃恢复"""

import json
import os

from harness.base import BaseStateStore


class JsonStateStore(BaseStateStore):
    """基于 JSON 文件的状态存储。

    每个 session 一个 JSON 文件，保存在指定目录下。
    支持崩溃恢复和状态过期清理。
    """

    def __init__(self, store_dir: str = "./data/state"):
        self._store_dir = store_dir
        os.makedirs(store_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        # 安全文件名
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_.")
        return os.path.join(self._store_dir, f"{safe_id}.json")

    def save_state(self, session_id: str, state: dict) -> None:
        path = self._path(session_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)

    def load_state(self, session_id: str) -> dict | None:
        path = self._path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def delete_state(self, session_id: str) -> None:
        path = self._path(session_id)
        if os.path.exists(path):
            os.remove(path)

    def list_sessions(self) -> list[str]:
        sessions = []
        if os.path.exists(self._store_dir):
            for fname in os.listdir(self._store_dir):
                if fname.endswith(".json"):
                    sessions.append(fname[:-5])
        return sessions
