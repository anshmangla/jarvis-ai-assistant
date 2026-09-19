# J.A.R.V.I.S. — Personal AI Assistant

A modular, local Personal AI Assistant powered by Groq, LLaMA 3, and Python 3.11+.  
Supports voice interaction, wake word detection, LLM tool calling, and productivity automation.

---

## Architecture

```
Wake Word Detection → Voice Recording → Speech-to-Text (Whisper)
↓
Command Text → LLM Reasoning (Groq/LLaMA 3) → Tool Selection
↓
Plugin Execution → Response Generation → Text-to-Speech
```

---

## Features

| Feature | Tech |
|---|---|
| LLM Reasoning | Groq API · LLaMA3-70B · LangChain |
| Speech-to-Text | faster-whisper (local, offline) |
| Text-to-Speech | pyttsx3 |
| Wake Word | openwakeword |
| Audio Recording | sounddevice |
| Web Search | DuckDuckGo (HTML) + BeautifulSoup |
| Email | Gmail SMTP / IMAP |
| Calendar | Google Calendar API (OAuth2) |
| Memory | JSON-backed persistent store |
| Reminders | JSON file |
| System Control | os, webbrowser, pyautogui |

---

## Installation

### 1. Install uv
```bash
pip install uv
```

### 2. Create virtual environment
```bash
cd ai_assistant
uv venv
# Windows:
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
copy .env.example .env
```
Edit `.env` and fill in your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
WAKE_WORD=Hey Nova
EMAIL_ADDRESS=yourname@gmail.com
EMAIL_APP_PASSWORD=your_google_app_password
```

---

## Google Calendar Setup (one-time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → Create a project
2. Enable the **Google Calendar API**
3. Create **OAuth 2.0 credentials** → Desktop App type
4. Download as `credentials.json` → place it at `ai_assistant/credentials.json`
5. On first run, a browser window will open for Google sign-in consent

---

## Running the Assistant

### Voice Mode (default)
```bash
python main.py
```
Say **"Hey Nova"** (or your configured wake word) to activate.

### Text Mode (no microphone required)
```bash
python main.py --text
```

---

## Example Commands

| Voice Command | Action |
|---|---|
| "Hey Nova, open Chrome" | Opens browser |
| "Search for latest AI news" | DuckDuckGo search |
| "Send email to Rahul saying meeting moved to tomorrow" | Sends Gmail |
| "Add meeting to calendar at 5 PM" | Creates Google Calendar event |
| "Remind me to drink water in 30 minutes" | Saves reminder |
| "What are my events today?" | Lists calendar events |
| "Take a screenshot" | Saves screenshot to disk |

---

## Project Structure

```
ai_assistant/
├── main.py                  # Entry point & main loop
├── config.py                # Environment config & paths
├── requirements.txt
├── .env.example
├── credentials.json         # Google OAuth (you provide)
│
├── assistant/
│   ├── agent.py             # Orchestration: LLM + tools + memory
│   ├── brain.py             # Groq LLM wrapper (LangChain)
│   ├── memory.py            # Persistent conversation memory
│   ├── prompts.py           # System & tool-selection prompts
│   └── router.py
│
├── voice/
│   ├── wakeword.py          # openwakeword wake word detection
│   ├── listen.py            # sounddevice + faster-whisper STT
│   └── speak.py             # pyttsx3 TTS
│
├── skills/
│   ├── base.py              # BaseSkill class
│   ├── system_control.py    # Open apps, screenshot, browser
│   ├── web_search.py        # DuckDuckGo search
│   ├── email.py             # Gmail send/read/summarize
│   ├── calendar.py          # Google Calendar CRUD
│   └── reminders.py         # Local JSON reminders
│
├── plugins/
│   └── plugin_loader.py     # Dynamic skill auto-loader
│
├── utils/
│   ├── logger.py            # Rich-formatted logger
│   └── helpers.py           # JSON parsing, response formatting
│
└── data/
    ├── memory.json          # Persistent conversation memory
    └── reminders.json       # Stored reminders
```

---

## Adding New Skills

1. Create a file `skills/my_skill.py`
2. Inherit from `BaseSkill`:
```python
from skills.base import BaseSkill

class MySkill(BaseSkill):
    name = "my_skill"
    description = "Does something useful"
    parameters = {"input": {"type": "string", "description": "..."}}

    def run(self, **kwargs):
        return "Done!"
```
3. That's it — the plugin loader auto-discovers and registers it on startup.
