import pytest
import os
import json
from unittest.mock import MagicMock

# Mock Groq Client
@pytest.fixture
def mock_groq(mocker):
    mock_client = MagicMock()
    mocker.patch("llm._client", mock_client)
    return mock_client

# Temp storage fixtures
@pytest.fixture(autouse=True)
def mock_json_storage(tmp_path, mocker):
    """
    Redirects contacts.json and reminders.json to a temporary directory 
    for the duration of the test so local data is not overwritten.
    """
    contacts_file = tmp_path / "contacts.json"
    reminders_file = tmp_path / "reminders.json"
    
    # Write empty defaults
    contacts_file.write_text("{}")
    reminders_file.write_text("[]")
    
    mocker.patch("contacts_tool._FILE", str(contacts_file))
    mocker.patch("reminders_tool._FILE", str(reminders_file))
    
    return tmp_path

# Mock Google Auth
@pytest.fixture(autouse=True)
def mock_google_auth(mocker):
    """
    Mock google_auth.get_google_credentials to return a dummy creds object
    so we don't trigger browser OAuth flows in tests.
    """
    mock_creds = MagicMock()
    mock_creds.valid = True
    mocker.patch("google_auth.get_google_credentials", return_value=mock_creds)
    return mock_creds

# Mock Google API Services
@pytest.fixture
def mock_google_services(mocker):
    """
    Mock the Google API 'build' function so tool functions get mocked
    service objects instead of making real network requests.
    """
    services = {
        "calendar": MagicMock(name="MockService_calendar"),
        "gmail": MagicMock(name="MockService_gmail"),
        "drive": MagicMock(name="MockService_drive"),
        "sheets": MagicMock(name="MockService_sheets")
    }
    
    def side_effect_build(serviceName, version, credentials=None):
        return services[serviceName]
        
    mocker.patch("calendar_tool.build", side_effect=side_effect_build)
    mocker.patch("gmail_tool.build", side_effect=side_effect_build)
    mocker.patch("drive_tool.build", side_effect=side_effect_build)
    mocker.patch("sheets_tool.build", side_effect=side_effect_build)
    return services
