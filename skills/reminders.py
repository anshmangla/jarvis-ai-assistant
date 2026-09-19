import json
import os
from typing import Any, Dict, List

from skills.base import BaseSkill
from config import config
from utils.logger import logger

class RemindersSkill(BaseSkill):
    """Skill to manage reminders in a local JSON file."""
    
    name = "reminders"
    description = "Create, list, or delete reminders and tasks."
    parameters = {
        "action": {
            "type": "string",
            "description": "The action to perform. Valid values: 'add', 'list', 'delete'."
        },
        "reminder_text": {
            "type": "string",
            "description": "The text of the reminder to add or delete.",
            "default": ""
        }
    }

    def __init__(self):
        self.reminders_file = config.REMINDERS_FILE
        # Ensure the file exists
        if not os.path.exists(self.reminders_file):
            self._save_reminders([])

    def _load_reminders(self) -> List[str]:
        try:
            with open(self.reminders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_reminders(self, reminders: List[str]) -> None:
        try:
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(reminders, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")

    def run(self, **kwargs: Dict[str, Any]) -> str:
        action = kwargs.get("action", "")
        text = kwargs.get("reminder_text", "")
        
        reminders = self._load_reminders()
        
        if action == "add":
            if not text:
                return "You must provide reminder_text to add a reminder."
            reminders.append(text)
            self._save_reminders(reminders)
            return f"Added reminder: '{text}'."
            
        elif action == "list":
            if not reminders:
                return "You currently have no reminders."
            response = "Here are your reminders:\n"
            for i, r in enumerate(reminders, 1):
                response += f"{i}. {r}\n"
            return response.strip()
            
        elif action == "delete":
            if not text:
                return "You must provide reminder_text (or the exact text to delete)."
                
            # Try to match implicitly
            matched_reminders = [r for r in reminders if text.lower() in r.lower()]
            if not matched_reminders:
                return f"No reminders found matching: '{text}'."
                
            # If multiple match, we just delete the first match for simplicity
            target = matched_reminders[0]
            reminders.remove(target)
            self._save_reminders(reminders)
            return f"Deleted reminder: '{target}'."
            
        else:
            return f"Unknown action '{action}'. Use 'add', 'list', or 'delete'."
