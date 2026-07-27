import pytest
from unittest.mock import MagicMock
import json

from time_tool import get_current_time
from weather_tool import get_weather, get_weather_forecast
from reminders_tool import add_reminder, list_reminders, complete_reminder
from contacts_tool import add_contact, lookup_contact, list_contacts
from calendar_tool import create_event
from gmail_tool import send_email
from drive_tool import search_files
from sheets_tool import append_row

# --- Time Tool ---
def test_time_tool():
    res = get_current_time()
    assert isinstance(res, str)
    assert len(res) > 0
    assert "It's" in res or "at" in res

# --- Weather Tool ---
def test_weather_tool_success(mocker):
    mock_get = mocker.patch("requests.get")
    
    # Mock Geocoding response
    mock_geo_resp = MagicMock()
    mock_geo_resp.json.return_value = {"results": [{"latitude": 40.71, "longitude": -74.01}]}
    
    # Mock Weather response
    mock_weather_resp = MagicMock()
    mock_weather_resp.json.return_value = {
        "current_weather": {"temperature": 22.5, "weathercode": 0}
    }
    
    mock_get.side_effect = [mock_geo_resp, mock_weather_resp]
    
    res = get_weather("New York")
    assert "22.5" in res
    assert "clear sky" in res.lower()

def test_weather_tool_not_found(mocker):
    mock_get = mocker.patch("requests.get")
    mock_geo_resp = MagicMock()
    mock_geo_resp.json.return_value = {} # No results
    mock_get.return_value = mock_geo_resp
    
    res = get_weather("UnknownCityXYZ")
    assert "couldn't find a city called" in res

# --- Reminders Tool ---
def test_reminders_flow(mock_json_storage):
    add_reminder("Buy groceries and milk", "today")
    add_reminder("Call mom", "tomorrow")
    
    lst = list_reminders()
    assert "Buy groceries and milk" in lst
    assert "Call mom" in lst
    
    # Test fuzzy completion
    comp = complete_reminder("milk")
    assert "Buy groceries and milk" in comp
    
    lst2 = list_reminders()
    assert "milk" not in lst2
    assert "Call mom" in lst2

# --- Contacts Tool ---
def test_contacts_flow(mock_json_storage):
    add_contact("Moaz", "moaz@example.com", "Friend")
    add_contact("Ahmed", "ahmed@example.com")
    
    lst = list_contacts()
    assert "Moaz" in lst
    
    # Exact lookup
    res = lookup_contact("Moaz")
    assert "moaz@example.com" in res
    
    # Fuzzy lookup
    res2 = lookup_contact("Moas")
    assert "moaz@example.com" in res2
    
    # Not found
    res3 = lookup_contact("Unknown Person")
    assert "I don't have anyone named" in res3

# --- Calendar Tool ---
def test_calendar_create_event(mock_google_services):
    mock_service = mock_google_services["calendar"]
    mock_events = mock_service.events.return_value
    mock_insert = mock_events.insert.return_value
    mock_insert.execute.return_value = {
        "htmlLink": "http://cal.link", 
        "conferenceData": {
            "entryPoints": [{"entryPointType": "video", "uri": "http://meet.link"}]
        }
    }
    
    res = create_event("Meeting", "2026-07-27T10:00:00", "2026-07-27T11:00:00", attendees=["test@test.com"], add_meet_link=True)
    
    # Assert API was called correctly
    mock_events.insert.assert_called_once()
    call_args = mock_events.insert.call_args[1]
    assert call_args["calendarId"] == "primary"
    assert call_args["conferenceDataVersion"] == 1
    assert "test@test.com" in json.dumps(call_args["body"]["attendees"])
    
    assert "http://cal.link" in res
    assert "http://meet.link" in res

# --- Gmail Tool ---
def test_gmail_send(mock_google_services):
    mock_service = mock_google_services["gmail"]
    mock_users = mock_service.users.return_value
    mock_messages = mock_users.messages.return_value
    mock_send = mock_messages.send.return_value
    mock_send.execute.return_value = {"id": "12345"}
    
    res = send_email("test@example.com", "Hello", "World")
    
    mock_messages.send.assert_called_once()
    call_args = mock_messages.send.call_args[1]
    assert "raw" in call_args["body"]
    assert "sent an email" in res

# --- Error Handling ---
def test_gmail_error(mock_google_services):
    mock_service = mock_google_services["gmail"]
    mock_service.users.return_value.messages.return_value.send.side_effect = Exception("API error")
    
    res = send_email("test@example.com", "Hello", "World")
    assert "couldn't send that email" in res
