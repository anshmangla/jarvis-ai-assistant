import os
import shutil
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
            "description": "The target of the action (e.g., the URL to open, or the name of the application like 'chrome', 'firefox', 'notepad', 'calc'). Leave empty for screenshots.",
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
        
        target = app_name.strip()
        target_lower = target.lower()

        # Route website names or URLs to browser
        if any(target_lower.startswith(p) for p in ("http://", "https://", "www.")) or any(
            target_lower.endswith(tld) for tld in (".com", ".org", ".net", ".io", ".gov", ".edu")
        ):
            return self._open_browser(target)

        # General browser request
        if target_lower in ("browser", "web browser", "internet"):
            return self._open_browser("https://www.google.com")

        # Known Windows application paths and aliases
        app_candidates = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                "chrome.exe",
            ],
            "google chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                "chrome.exe",
            ],
            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                "firefox.exe",
            ],
            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                "msedge.exe",
            ],
            "microsoft edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                "msedge.exe",
            ],
            "notepad": ["notepad.exe"],
            "calc": ["calc.exe"],
            "calculator": ["calc.exe"],
            "code": ["code.cmd", "code.exe"],
            "vscode": ["code.cmd", "code.exe"],
            "vs code": ["code.cmd", "code.exe"],
            "explorer": ["explorer.exe"],
            "cmd": ["cmd.exe"],
            "terminal": ["wt.exe", "cmd.exe"],
            "spotify": [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                "spotify.exe",
            ],
        }

        try:
            if os.name == 'nt':
                candidates = app_candidates.get(target_lower, [target, f"{target}.exe"])
                
                # Try finding valid executable
                exec_path = None
                for cand in candidates:
                    if os.path.isabs(cand) and os.path.exists(cand):
                        exec_path = cand
                        break
                    which_path = shutil.which(cand)
                    if which_path:
                        exec_path = which_path
                        break

                if exec_path:
                    subprocess.Popen([exec_path], shell=False)
                    logger.info(f"Opened application: '{target}' using {exec_path}")
                    return f"Successfully opened {target}."

                # Fallback to os.startfile or shell start
                os.startfile(target)
                logger.info(f"Launched application via startfile: {target}")
                return f"Successfully opened application: {target}"
            else:
                subprocess.Popen([target], shell=True)
                return f"Successfully opened application: {target}"
        except Exception as e:
            logger.error(f"Failed to open app '{target}': {e}")
            return f"Failed to open '{target}'. Error: {e}"

    def _open_browser(self, url: str) -> str:
        if not url:
            url = "https://www.google.com"
        
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        try:
            webbrowser.open(url)
            logger.info(f"Opened browser to: {url}")
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
