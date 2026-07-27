"""
Tool registry for the voice agent.

Imports all tool functions from dedicated modules, defines their OpenAI-style
JSON schemas for the LLM, and provides a single TOOL_DISPATCH dict for
llm.py to execute tool calls.
"""

# ---------------------------------------------------------------------------
# Import tool functions from each module
# ---------------------------------------------------------------------------

from time_tool import get_current_time
from weather_tool import get_weather, get_weather_forecast
from reminders_tool import add_reminder, list_reminders, complete_reminder
from contacts_tool import lookup_contact, add_contact, list_contacts
from calendar_tool import create_event, list_events
from gmail_tool import send_email
from drive_tool import search_files, read_file_content, create_file
from sheets_tool import find_spreadsheet_by_name, create_spreadsheet, read_range, append_row

# ---------------------------------------------------------------------------
# Dispatch table: tool name → callable
# ---------------------------------------------------------------------------

TOOL_DISPATCH = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast,
    "add_reminder": add_reminder,
    "list_reminders": list_reminders,
    "complete_reminder": complete_reminder,
    "lookup_contact": lookup_contact,
    "add_contact": add_contact,
    "list_contacts": list_contacts,
    "create_event": create_event,
    "list_events": list_events,
    "send_email": send_email,
    "search_files": search_files,
    "read_file_content": read_file_content,
    "create_file": create_file,
    "find_spreadsheet_by_name": find_spreadsheet_by_name,
    "create_spreadsheet": create_spreadsheet,
    "read_range": read_range,
    "append_row": append_row,
}

# ---------------------------------------------------------------------------
# OpenAI-style tool schemas sent to the LLM
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    # ---- Time ------------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": (
                "Get the current local date and time. "
                "Use when the user asks what time it is, what today's date is, "
                "or what day of the week it is."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Optional timezone name or 'local' (default).",
                    },
                },
                "required": [],
            },
        },
    },
    # ---- Weather ---------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the CURRENT real weather for a city right now. Returns temperature, "
                "conditions, and wind speed. Use only when the user asks about current "
                "conditions, temperature, or weather right now or today."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'London', 'New York', 'Islamabad'.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": (
                "Get the weather FORECAST for a city for future days (e.g. tomorrow or days ahead). "
                "Use when the user asks 'is it going to rain tomorrow?', 'what's the weather forecast?', "
                "or asks about future days."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. 'London', 'New York', 'Islamabad'.",
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days ahead to forecast (1 = tomorrow, 2 = day after tomorrow). Defaults to 1.",
                    },
                },
                "required": ["city"],
            },
        },
    },
    # ---- Contacts --------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "lookup_contact",
            "description": (
                "Look up a person's email address from the saved contacts list. "
                "ALWAYS call this FIRST when the user mentions a person by name for "
                "sending an email, scheduling a meeting, or any action that needs their email. "
                "Uses fuzzy matching so minor misspellings still work."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The person's name to look up.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_contact",
            "description": (
                "Save a new contact with their name and email address. Call this after "
                "the user provides and confirms a new person's email address, so it is "
                "remembered for future use."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The person's display name.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Their email address.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes (e.g. 'classmate', 'project partner').",
                    },
                },
                "required": ["name", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_contacts",
            "description": (
                "List all saved contacts with their names and email addresses. "
                "Use when the user asks 'show my contacts', 'who do I have saved?', "
                "or 'list contacts'."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    # ---- Reminders -------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": (
                "Add a new reminder or task. Use when the user says things like "
                "'remind me to…', 'add a task…', 'don't let me forget…'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Description of the reminder or task.",
                    },
                    "due": {
                        "type": "string",
                        "description": "Optional due date or time (e.g. 'tomorrow', 'July 25', '3 PM').",
                    },
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": (
                "List all current reminders and tasks. Use when the user asks "
                "'what are my reminders?', 'show my tasks', 'what do I need to do?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Optional filter status, e.g. 'active' (default).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_reminder",
            "description": (
                "Mark a reminder or task as completed and remove it. Use when "
                "the user says 'I finished…', 'mark … as done', 'complete the … task'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of the reminder to mark as done (fuzzy matched).",
                    },
                },
                "required": ["task_description"],
            },
        },
    },
    # ---- Google Calendar -------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": (
                "Create a new Google Calendar event. DO NOT call this tool if the user asks to "
                "schedule a meeting with someone whose email address has not been provided in this "
                "conversation — ask the user for their email address first instead of calling this tool or inventing an email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title (e.g. 'Team standup', 'Meeting with Ahmed').",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 start time (e.g. '2026-07-25T15:00:00+05:00').",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO 8601 end time (e.g. '2026-07-25T16:00:00+05:00').",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional event description or agenda.",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses. Only include an attendee if the user has explicitly provided their email address in this conversation. Never guess, infer, or invent an email address.",
                    },
                    "add_meet_link": {
                        "type": "boolean",
                        "description": "If true, attach a Google Meet video link. Defaults to true.",
                    },
                },
                "required": ["summary", "start_time", "end_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": (
                "List upcoming Google Calendar events. Use when the user asks "
                "'what's on my calendar?', 'do I have any meetings?', "
                "'what am I doing tomorrow?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "ISO 8601 start bound (defaults to now if omitted).",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "Optional ISO 8601 end bound to limit the search window.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum events to return (default 10).",
                    },
                },
                "required": [],
            },
        },
    },
    # ---- Gmail -----------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email via Gmail. Use when the user says 'send an email', "
                "'email … to …', 'write to … about …', 'message …'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address.",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line.",
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain-text body of the email.",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    # ---- Google Drive ----------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": (
                "Search Google Drive for files by name. Use when the user asks "
                "'find my … file', 'do I have a document called …?', "
                "'search Drive for …'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to match against file names.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default 5).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": (
                "Read the text content of a file from Google Drive. Supports "
                "Google Docs and plain text files. Use when the user asks "
                "'read my … document', 'what does … say?', 'open the … file'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The exact name of the file to read.",
                    },
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": (
                "Create a new Google Doc on Drive with the given name and text "
                "content. Use when the user says 'create a document', "
                "'write a file called …', 'make a new doc'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name/title of the new document.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write into the document.",
                    },
                },
                "required": ["name", "content"],
            },
        },
    },
    # ---- Google Sheets ---------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "find_spreadsheet_by_name",
            "description": (
                "Find an existing Google Sheets spreadsheet by its name and return its ID. "
                "Call this first when the user refers to a spreadsheet by name. "
                "If no spreadsheet is found, call create_spreadsheet to create a new sheet and get its ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The spreadsheet name to search for.",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_spreadsheet",
            "description": (
                "Create a new Google Spreadsheet via the Sheets API and return its real ID. "
                "Call this when find_spreadsheet_by_name returns not-found or when creating a new "
                "spreadsheet or expense log, then use the returned real ID with append_row."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the new spreadsheet (e.g. 'Expenses', 'Project Budget').",
                    },
                    "headers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional header row values (e.g. ['Date', 'Description', 'Amount']).",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_range",
            "description": (
                "Read values from a Google Sheets range. Use when the user asks "
                "'read the spreadsheet', 'what's in column A?', 'show me the data'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "This must be a real spreadsheet ID returned by a previous call to find_spreadsheet_by_name or create_spreadsheet in this conversation. Never invent, guess, or use a placeholder value for this field.",
                    },
                    "range_name": {
                        "type": "string",
                        "description": "A1-notation range (e.g. 'Sheet1!A1:C10').",
                    },
                },
                "required": ["spreadsheet_id", "range_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_row",
            "description": (
                "Append a row of values to a Google Sheet. Use when the user says "
                "'add a row', 'log this data', 'put … in the spreadsheet'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {
                        "type": "string",
                        "description": "This must be a real spreadsheet ID returned by a previous call to find_spreadsheet_by_name or create_spreadsheet in this conversation. Never invent, guess, or use a placeholder value for this field.",
                    },
                    "range_name": {
                        "type": "string",
                        "description": "Target sheet/range (e.g. 'Sheet1').",
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cell values for the new row.",
                    },
                },
                "required": ["spreadsheet_id", "range_name", "values"],
            },
        },
    },
]
