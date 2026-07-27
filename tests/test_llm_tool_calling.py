import pytest
from llm import chat

# These tests make real calls to the Groq API to verify that the prompt
# instructions (like not fabricating emails or spreadsheet IDs) are followed.
# Run with `pytest -m integration` to execute.

@pytest.mark.integration
def test_llm_weather_routing():
    """Verify LLM picks current weather vs forecast correctly based on prompt."""
    
    # Test current weather
    res = list(chat("What is the weather in New York right now?"))
    combined = "".join(r["text"] for r in res)
    assert "get_weather" in combined or "current" in combined.lower()

@pytest.mark.integration
def test_llm_no_fabricated_email():
    """Verify LLM refuses to create an event with a fabricated email."""
    
    # We ask to create an event with John, but John's email is not in context.
    # The prompt instructs it to use lookup_contact or ask, NOT to guess john@example.com.
    res = list(chat("Create a meeting with John for tomorrow at 2pm."))
    combined = "".join(r["text"] for r in res)
    
    # It should either ask for the email or call lookup_contact. 
    # It should NOT call create_event with a fake email.
    assert "john@example.com" not in combined.lower()

@pytest.mark.integration
def test_llm_no_placeholder_spreadsheet():
    """Verify LLM refuses to append to a spreadsheet with a fake ID."""
    
    # We ask to log an expense, but we don't provide a spreadsheet name.
    res = list(chat("Log an expense of 50 dollars for lunch."))
    combined = "".join(r["text"] for r in res)
    
    # It should not call append_row with '{ssid}' or 'xxx'.
    assert "{ssid}" not in combined
    assert "xxx" not in combined
