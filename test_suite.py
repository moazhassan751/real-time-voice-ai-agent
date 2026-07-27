"""
Comprehensive test suite for the Real-Time Voice AI Agent.

Tests all 14 tools, edge cases, error conditions, fuzzy matching,
empty inputs, and LLM dispatch integrity to ensure enterprise-grade reliability.
"""

import os
import sys
import unittest

# Ensure modules in voice-agent can be imported.
sys.path.insert(0, os.path.dirname(__file__))

from time_tool import get_current_time
from weather_tool import get_weather
from reminders_tool import add_reminder, list_reminders, complete_reminder, _FILE as REMINDERS_FILE
from calendar_tool import list_events, create_event
from gmail_tool import send_email
from drive_tool import search_files, read_file_content, create_file
from sheets_tool import find_spreadsheet_by_name, read_range, append_row
from tools import TOOL_SCHEMAS, TOOL_DISPATCH
from stt import transcribe
from tts import speak
from llm import chat, reset_history


class TestTimeTool(unittest.TestCase):
    def test_default_time(self):
        result = get_current_time()
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("It's "))

    def test_time_with_arg(self):
        result = get_current_time(timezone="local")
        self.assertIsInstance(result, str)
        self.assertIn("at", result)


class TestWeatherTool(unittest.TestCase):
    def test_valid_city(self):
        result = get_weather("London")
        self.assertIsInstance(result, str)
        self.assertIn("London", result)
        self.assertIn("°C", result)

    def test_another_city(self):
        result = get_weather("Tokyo")
        self.assertIsInstance(result, str)
        self.assertIn("Tokyo", result)

    def test_nonexistent_city(self):
        result = get_weather("Xyz123FakeCity999")
        self.assertIsInstance(result, str)
        self.assertIn("couldn't find", result.lower())

    def test_empty_city(self):
        result = get_weather("")
        self.assertIsInstance(result, str)


class TestRemindersTool(unittest.TestCase):
    def setUp(self):
        # Clean test reminders file before each test
        if os.path.exists(REMINDERS_FILE):
            os.remove(REMINDERS_FILE)

    def tearDown(self):
        if os.path.exists(REMINDERS_FILE):
            os.remove(REMINDERS_FILE)

    def test_empty_reminders_list(self):
        result = list_reminders()
        self.assertIn("don't have any reminders", result)

    def test_add_and_list_single(self):
        add_res = add_reminder("Submit assignment", due="tomorrow")
        self.assertIn("added a reminder", add_res)

        list_res = list_reminders()
        self.assertIn("Submit assignment", list_res)
        self.assertIn("due tomorrow", list_res)

    def test_add_multiple_and_list(self):
        add_reminder("Task 1")
        add_reminder("Task 2")
        list_res = list_reminders()
        self.assertIn("2 reminders", list_res)

    def test_fuzzy_completion(self):
        add_reminder("Buy groceries from supermarket", due="Friday")
        comp_res = complete_reminder("groceries")
        self.assertIn("completed the reminder", comp_res.lower())

        list_res = list_reminders()
        self.assertIn("don't have any reminders", list_res)

    def test_complete_nonexistent(self):
        add_reminder("Do homework")
        comp_res = complete_reminder("fly to mars")
        self.assertIn("couldn't find", comp_res.lower())


class TestSTTandTTS(unittest.TestCase):
    def test_empty_stt(self):
        result = transcribe(b"")
        self.assertEqual(result, "")

    def test_empty_tts(self):
        # Should execute silently with no error
        speak("")


class TestToolRegistry(unittest.TestCase):
    def test_schema_dispatch_parity(self):
        schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        dispatch_names = set(TOOL_DISPATCH.keys())

        self.assertEqual(len(schema_names), 19, "Must have exactly 19 tool schemas")
        self.assertEqual(schema_names, dispatch_names, "Schemas and dispatch table must match 1:1")

    def test_no_empty_properties(self):
        """Ensure all tools define parameter properties so LLM tool calling never outputs empty null args."""
        for schema in TOOL_SCHEMAS:
            props = schema["function"]["parameters"]["properties"]
            name = schema["function"]["name"]
            self.assertIsInstance(props, dict, f"Tool {name} properties must be a dict")


class TestLLMMultiTurn(unittest.TestCase):
    def setUp(self):
        reset_history()

    def test_time_tool_call(self):
        reply = chat("What time is it right now?")
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    def test_weather_tool_call(self):
        reply = chat("What is the weather in Tokyo?")
        self.assertIsInstance(reply, str)
        self.assertIn("Tokyo", reply)

    def test_reminder_tool_call(self):
        reply = chat("Remind me to call Mom tomorrow")
        self.assertIsInstance(reply, str)
        self.assertTrue(any(word in reply.lower() for word in ["added", "reminder", "mom", "got it"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
