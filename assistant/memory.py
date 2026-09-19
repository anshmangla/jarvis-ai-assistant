import json
import os
from datetime import datetime
from typing import Any

from config import config
from utils.logger import logger

# Memory schema:
# {
#   "history": [{"role": "user"|"assistant", "content": "...", "timestamp": "..."}],
#   "facts": {"user_name": "Alice", "city": "Mumbai", ...}
# }

_EMPTY_MEMORY: dict = {"history": [], "facts": {}}


class Memory:
    """Persistent memory system backed by a local JSON file."""

    def __init__(self) -> None:
        self.filepath = config.MEMORY_FILE
        self._data: dict = self._load()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        """Load memory from disk, creating an empty file if needed."""
        if not os.path.exists(self.filepath):
            self._write(_EMPTY_MEMORY.copy())
            return _EMPTY_MEMORY.copy()

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure both keys are present even on old/corrupt files
                data.setdefault("history", [])
                data.setdefault("facts", {})
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Memory file corrupted or unreadable ({e}). Starting fresh.")
            return _EMPTY_MEMORY.copy()

    def _write(self, data: dict) -> None:
        """Persist current memory state to disk atomically."""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Failed to write memory file: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_message(self, role: str, content: str) -> None:
        """
        Append a single conversation turn to history.

        Args:
            role (str): Either ``"user"`` or ``"assistant"``.
            content (str): The message text.
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        self._data["history"].append(entry)
        # Keep last 50 turns to prevent the file from growing unbounded
        self._data["history"] = self._data["history"][-50:]
        self._write(self._data)

    def get_recent_history(self, turns: int = 10) -> str:
        """
        Return the last N conversation turns as a formatted string.

        Args:
            turns (int): Number of recent turns to include.

        Returns:
            str: Formatted conversation history.
        """
        recent = self._data["history"][-turns:]
        if not recent:
            return ""
        lines = [f"{entry['role'].capitalize()}: {entry['content']}" for entry in recent]
        return "\n".join(lines)

    def add_fact(self, key: str, value: Any) -> None:
        """
        Store or update a user fact.

        Args:
            key (str): Fact name (e.g. ``"user_name"``, ``"city"``).
            value (Any): The value to store.
        """
        self._data["facts"][key] = value
        self._write(self._data)
        logger.info(f"Memory — stored fact: {key} = {value}")

    def get_facts_summary(self) -> str:
        """
        Return all stored facts as a human-readable string.

        Returns:
            str: Facts formatted for injection into the LLM prompt.
        """
        facts = self._data.get("facts", {})
        if not facts:
            return ""
        return "\n".join(f"- {k}: {v}" for k, v in facts.items())

    def retrieve_memory(self, keyword: str = "") -> str:
        """
        Retrieve combined memory context: relevant facts + recent history.

        Args:
            keyword (str): Optional keyword to filter history entries. If empty,
                           the last 10 turns are returned.

        Returns:
            str: Formatted memory context string.
        """
        facts_str = self.get_facts_summary()

        if keyword:
            kw_lower = keyword.lower()
            matching = [
                e for e in self._data["history"]
                if kw_lower in e["content"].lower()
            ][-10:]
            history_str = "\n".join(
                f"{e['role'].capitalize()}: {e['content']}" for e in matching
            )
        else:
            history_str = self.get_recent_history(10)

        parts = []
        if facts_str:
            parts.append(f"Known facts:\n{facts_str}")
        if history_str:
            parts.append(f"Recent conversation:\n{history_str}")

        return "\n\n".join(parts)

    def clear(self) -> None:
        """Wipe all memory (history + facts) from disk and in-memory cache."""
        self._data = _EMPTY_MEMORY.copy()
        self._write(self._data)
        logger.info("Memory cleared.")
