"""
Google Calendar tool — create and list events, with Google Meet link support.
"""

import uuid
from datetime import datetime, timezone

from googleapiclient.discovery import build

from google_auth import get_google_credentials


def _get_service():
    return build("calendar", "v3", credentials=get_google_credentials())


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: list[str] = None,
    add_meet_link: bool = True,
) -> str:
    """Create a Google Calendar event.

    Args:
        summary: Event title (e.g. "Team standup").
        start_time: ISO 8601 start (e.g. "2026-07-25T15:00:00+05:00").
        end_time: ISO 8601 end (e.g. "2026-07-25T16:00:00+05:00").
        description: Optional event description.
        attendees: Optional list of email addresses to invite.
        add_meet_link: If True, automatically attach a Google Meet link.

    Returns a spoken confirmation with the event and Meet link.
    """
    try:
        service = _get_service()

        event_body = {
            "summary": summary,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }

        if description:
            event_body["description"] = description

        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]

        conference_version = 0
        if add_meet_link:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": uuid.uuid4().hex,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
            conference_version = 1

        created = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=conference_version,
            sendUpdates="all" if attendees else "none",
        ).execute()

        link = created.get("htmlLink", "")
        meet_link = ""
        conf_data = created.get("conferenceData", {})
        entry_points = conf_data.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri", "")
                break

        parts = [f"Done! I've created the event '{summary}'."]
        if meet_link:
            parts.append(f"A Google Meet link has been added: {meet_link}")
        if link:
            parts.append(f"Event link: {link}")

        return " ".join(parts)

    except Exception as e:
        return f"Sorry, I couldn't create that calendar event. {e}"


def list_events(
    time_min: str = None,
    time_max: str = None,
    max_results: int = 10,
) -> str:
    """List upcoming Google Calendar events.

    Args:
        time_min: ISO 8601 start bound (defaults to now).
        time_max: Optional ISO 8601 end bound.
        max_results: Maximum number of events to return.

    Returns a spoken summary of upcoming events.
    """
    try:
        service = _get_service()

        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()

        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_max:
            params["timeMax"] = time_max

        result = service.events().list(**params).execute()
        events = result.get("items", [])

        if not events:
            return "You don't have any upcoming events."

        lines = []
        for ev in events:
            title = ev.get("summary", "Untitled event")
            start = ev.get("start", {})
            start_str = start.get("dateTime", start.get("date", "unknown time"))
            # Try to make the time more readable.
            try:
                dt = datetime.fromisoformat(start_str)
                hour = dt.hour % 12 or 12
                am_pm = "AM" if dt.hour < 12 else "PM"
                friendly = dt.strftime(f"%A at {hour}:%M {am_pm}")
            except (ValueError, TypeError):
                friendly = start_str
            lines.append(f"{title} on {friendly}")

        if len(lines) == 1:
            return f"You have one upcoming event: {lines[0]}."

        joined = ", ".join(lines[:-1]) + f", and {lines[-1]}"
        return f"You have {len(lines)} upcoming events: {joined}."

    except Exception as e:
        return f"Sorry, I couldn't retrieve your calendar events. {e}"
