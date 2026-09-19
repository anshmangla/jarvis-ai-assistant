import os
import subprocess
import webbrowser
from datetime import datetime
from typing import Any, Dict

from skills.base import BaseSkill
from utils.logger import logger
from config import config

class SystemControlSkill(BaseSkill):
    """Skill to control the local system (open apps, sites, screenshot)."""
    
    name = "system_control"
    description = "Controls the system to open applications, open websites in the browser, or take screenshots."
    parameters = {
        "action": {
            "type": "string",
            "description": "The action to perform. Valid values: 'open_app', 'open_browser', 'take_screenshot'."
        },
        "target": {
            "type": "string",
            "description": "The target of the action (e.g., the URL to open, or the name of the application like 'notepad', 'calc'). Leave empty for screenshots.",
            "default": ""
        }
    }

    def run(self, **kwargs: Dict[str, Any]) -> str:
        action = kwargs.get("action", "")
        target = kwargs.get("target", "")
        
        if action == "open_app":
            return self._open_app(target)
        elif action == "open_browser":
            return self._open_browser(target)
        elif action == "take_screenshot":
            return self._take_screenshot()
        else:
            return f"Error: Unknown action '{action}'. Valid actions are 'open_app', 'open_browser', 'take_screenshot'."

    def _open_app(self, app_name: str) -> str:
        if not app_name:
            return "No application name provided."
        
        try:
            # Note: On Windows, simple commands like 'calc' or 'notepad' work directly.
            # More complex apps might need full paths or shell execution depending on the system PATH.
            if os.name == 'nt':
                os.startfile(app_name)
            else:
                # Basic fallback for linux/mac if needed, although user is on Windows.
                subprocess.Popen([app_name], shell=True)
            return f"Successfully opened application: {app_name}"
        except Exception as e:
            logger.error(f"Failed to open app '{app_name}': {e}")
            return f"Failed to open '{app_name}'. Error: {e}"

    def _open_browser(self, url: str) -> str:
        if not url:
            return "No URL provided."
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        try:
            webbrowser.open(url)
            return f"Opened browser targeting: {url}"
        except Exception as e:
            logger.error(f"Failed to open browser for '{url}': {e}")
            return f"Failed to open browser. Error: {e}"

    def _take_screenshot(self) -> str:
        try:
            # We use pyautogui for a reliable cross-platform screenshot
            import pyautogui
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(config.BASE_DIR, filename)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            return f"Screenshot taken and saved to: {filepath}"
        except ImportError:
            return "Cannot take screenshot. 'pyautogui' or 'Pillow' is not installed."
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return f"Failed to take screenshot: {e}"
