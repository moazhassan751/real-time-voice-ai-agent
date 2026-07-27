"""
Manual verification script for all voice agent tools.

Tests every tool function directly (no mic, no STT, no LLM, no TTS).
Runs each tool with safe inputs, handles errors gracefully, and prints a final summary.

NOTE: Before running, update the placeholder values below:
  - YOUR_EMAIL_HERE@gmail.com (in gmail_tool test)
  - YOUR_SHEET_NAME_HERE (in sheets_tool test)
"""

import sys

# ---------------------------------------------------------------------------
# 1. Google OAuth Check (One-Time Consent Window)
# ---------------------------------------------------------------------------
print("==================================================")
print("  Voice Agent Tools Manual Verification Script")
print("==================================================")
print("\n--- 1. Testing Google OAuth Credentials ---")

try:
    from google_auth import get_google_credentials
    creds = get_google_credentials()
    print("[OK] Google OAuth Check PASSED: Valid credentials loaded.")
except Exception as e:
    print(f"[FAILED] Google OAuth Check: {e}")
    print("   Make sure credentials.json is placed in the project directory.")

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
from time_tool import get_current_time
from weather_tool import get_weather
from reminders_tool import add_reminder, list_reminders, complete_reminder
from calendar_tool import list_events, create_event
from gmail_tool import send_email
from drive_tool import search_files, read_file_content, create_file
from sheets_tool import find_spreadsheet_by_name, read_range, append_row

passed_tests = []
failed_tests = []


def run_test(test_name: str, fn, *args, **kwargs):
    """Helper to run a tool test inside try/except and record results."""
    print(f"\n=== {test_name} ===")
    try:
        result = fn(*args, **kwargs)
        print(f"RESULT: {result}")
        passed_tests.append(test_name)
    except Exception as e:
        print(f"FAILED: {e}")
        failed_tests.append((test_name, str(e)))


# ---------------------------------------------------------------------------
# 2. Time Tool
# ---------------------------------------------------------------------------
run_test("time_tool: get_current_time", get_current_time)


# ---------------------------------------------------------------------------
# 3. Weather Tool
# ---------------------------------------------------------------------------
run_test("weather_tool: get_weather (Islamabad)", get_weather, "Islamabad")


# ---------------------------------------------------------------------------
# 4. Reminders Tool
# ---------------------------------------------------------------------------
run_test(
    "reminders_tool: add_reminder",
    add_reminder,
    "Test reminder from test_tools.py",
    due="tomorrow",
)
run_test("reminders_tool: list_reminders", list_reminders)
run_test(
    "reminders_tool: complete_reminder",
    complete_reminder,
    "Test reminder from test_tools.py",
)


# ---------------------------------------------------------------------------
# 5. Calendar Tool
# ---------------------------------------------------------------------------
run_test("calendar_tool: list_events", list_events)
run_test(
    "calendar_tool: create_event",
    create_event,
    summary="Test Event - safe to delete",
    start_time="2026-07-26T15:00:00+05:00",
    end_time="2026-07-26T15:30:00+05:00",
    description="Created by test_tools.py",
    add_meet_link=True,
)


# ---------------------------------------------------------------------------
# 6. Gmail Tool
# ---------------------------------------------------------------------------
# REMINDER: Replace 'YOUR_EMAIL_HERE@gmail.com' with a real recipient email address
TEST_EMAIL_RECIPIENT = "YOUR_EMAIL_HERE@gmail.com"

run_test(
    "gmail_tool: send_email",
    send_email,
    to=TEST_EMAIL_RECIPIENT,
    subject="Voice Agent Test Email",
    body="This is a test email sent from test_tools.py",
)


# ---------------------------------------------------------------------------
# 7. Drive Tool
# ---------------------------------------------------------------------------
run_test("drive_tool: search_files", search_files, query="test")
run_test(
    "drive_tool: create_file",
    create_file,
    "Voice Agent Test File",
    "This file was created by test_tools.py",
)
run_test(
    "drive_tool: read_file_content",
    read_file_content,
    file_name="Voice Agent Test File",
)


# ---------------------------------------------------------------------------
# 8. Sheets Tool
# ---------------------------------------------------------------------------
# REMINDER: Replace 'YOUR_SHEET_NAME_HERE' with a real spreadsheet name in your Google Drive
TEST_SHEET_NAME = "Voice Agent Test Spreadsheet"

run_test(
    "sheets_tool: find_spreadsheet_by_name",
    find_spreadsheet_by_name,
    TEST_SHEET_NAME,
)


# ---------------------------------------------------------------------------
# 9. Summary Section
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("  TEST SUMMARY")
print("=" * 50)
print(f"Total Tests Run : {len(passed_tests) + len(failed_tests)}")
print(f"Passed          : {len(passed_tests)}")
print(f"Failed          : {len(failed_tests)}")

if passed_tests:
    print("\n[OK] Passed Tools:")
    for name in passed_tests:
        print(f"  - {name}")

if failed_tests:
    print("\n[FAILED] Failed Tools:")
    for name, err in failed_tests:
        print(f"  - {name}: {err}")

print("\nNote: Placeholder values (YOUR_EMAIL_HERE@gmail.com, YOUR_SHEET_NAME_HERE) will fail until replaced with real data.")
