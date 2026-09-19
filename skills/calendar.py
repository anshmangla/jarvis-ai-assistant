import os
from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from skills.base import BaseSkill
from utils.logger import logger
from config import config

# Google Calendar OAuth2 scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Paths for OAuth credentials files
CREDENTIALS_FILE = os.path.join(config.BASE_DIR, "credentials.json")   # Downloaded from Google Cloud Console
TOKEN_FILE = os.path.join(config.DATA_DIR, "token.json")               # Auto-generated after first auth


class CalendarSkill(BaseSkill):
    """Skill to manage Google Calendar events (create, list, delete)."""

    name = "calendar"
    description = "Create, list, or delete Google Calendar events."
    parameters = {
        "action": {
            "type": "string",
            "description": "Action to perform: 'create', 'list', or 'delete'.",
        },
        "title": {
            "type": "string",
            "description": "Title of the event (required for 'create').",
            "default": "",
        },
        "start_time": {
            "type": "string",
            "description": "Event start time in ISO 8601 format e.g. '2026-03-05T17:00:00' (required for 'create').",
            "default": "",
        },
        "duration_minutes": {
            "type": "integer",
            "description": "Duration of the event in minutes (default: 60).",
            "default": 60,
        },
        "event_id": {
            "type": "string",
            "description": "Calendar event ID to delete (required for 'delete').",
            "default": "",
        },
        "days_ahead": {
            "type": "integer",
            "description": "For 'list', how many days ahead from today to show events (default: 7).",
            "default": 7,
        },
    }

    # ------------------------------------------------------------------
    # Google Auth Helper
    # ------------------------------------------------------------------

    def _get_service(self):
        """Authenticate and return a Google Calendar API service object."""
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Google OAuth credentials file not found at '{CREDENTIALS_FILE}'. "
                        "Download credentials.json from the Google Cloud Console and place it in ai_assistant/."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Opens a browser window for first-time OAuth consent
                creds = flow.run_local_server(port=0)

            # Persist the token for future runs
            with open(TOKEN_FILE, "w") as token_out:
                token_out.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self, **kwargs: Any) -> str:
        action: str = str(kwargs.get("action", ""))

        try:
            service = self._get_service()
        except FileNotFoundError as e:
            return str(e)
        except Exception as e:
            logger.error(f"Google Calendar auth failed: {e}")
            return f"Google Calendar authentication failed: {e}"

        if action == "create":
            return self._create_event(
                service,
                title=str(kwargs.get("title", "")),
                start_time=str(kwargs.get("start_time", "")),
                duration_minutes=int(str(kwargs.get("duration_minutes", 60))),
            )
        elif action == "list":
            return self._list_events(service, days_ahead=int(str(kwargs.get("days_ahead", 7))))
        elif action == "delete":
            return self._delete_event(service, event_id=str(kwargs.get("event_id", "")))
        else:
            return f"Unknown action '{action}'. Use 'create', 'list', or 'delete'."

    # ------------------------------------------------------------------
    # Create Event
    # ------------------------------------------------------------------

    def _create_event(self, service: Any, title: str, start_time: str, duration_minutes: int) -> str:
        if not title or not start_time:
            return "Error: 'title' and 'start_time' are required to create an event."

        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            event_body = {
                "summary": title,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "Asia/Kolkata",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "Asia/Kolkata",
                },
            }

            created = service.events().insert(calendarId="primary", body=event_body).execute()
            link = created.get("htmlLink", "No link")
            logger.info(f"Calendar event created: {title} at {start_time}")
            return (
                f"Event '{title}' created successfully!\n"
                f"Start: {start_dt.strftime('%B %d, %Y at %I:%M %p')}\n"
                f"Duration: {duration_minutes} minutes\n"
                f"Link: {link}"
            )
        except ValueError as e:
            return f"Invalid start_time format. Use ISO 8601 (e.g., '2026-03-05T17:00:00'). Error: {e}"
        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return f"Failed to create event: {e}"

    # ------------------------------------------------------------------
    # List Events
    # ------------------------------------------------------------------

    def _list_events(self, service: Any, days_ahead: int = 7) -> str:
        try:
            now = datetime.now(timezone.utc)
            time_max = now + timedelta(days=days_ahead)

            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max.isoformat(),
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                return f"No events found in the next {days_ahead} days."

            lines = [f"Upcoming events in the next {days_ahead} days:\n"]
            for i, event in enumerate(events, 1):
                title = event.get("summary", "(No title)")
                start = event["start"].get("dateTime", event["start"].get("date", "Unknown"))
                event_id = event.get("id", "")
                lines.append(f"{i}. {title}\n   Start: {start}\n   ID: {event_id}")

            return "\n\n".join(lines)
        except Exception as e:
            logger.error(f"Failed to list calendar events: {e}")
            return f"Failed to list events: {e}"

    # ------------------------------------------------------------------
    # Delete Event
    # ------------------------------------------------------------------

    def _delete_event(self, service: Any, event_id: str) -> str:
        if not event_id:
            return "Error: 'event_id' is required to delete an event. Use 'list' to find event IDs."

        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Deleted calendar event: {event_id}")
            return f"Event with ID '{event_id}' has been successfully deleted."
        except Exception as e:
            logger.error(f"Failed to delete event '{event_id}': {e}")
            return f"Failed to delete event: {e}"
