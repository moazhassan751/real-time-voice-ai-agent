"""
Shared OAuth2 helper for Google API tools (Calendar, Gmail, Drive, Sheets).

Handles credential caching, refresh, and first-run browser consent flow.
All Google tool modules import ``get_google_credentials()`` from here.
"""

import os
import pickle

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# All scopes needed across the four Google tool modules.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.pickle")
_CREDS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")


def get_google_credentials():
    """Return valid Google OAuth2 credentials.

    - If GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, and GOOGLE_CLIENT_SECRET are set,
      builds credentials directly (Headless/Deployed mode).
    - Otherwise, loads from ``token.pickle`` if available and still valid.
    - Refreshes expired credentials automatically.
    - On first run, opens a browser for one-time consent and caches
      the resulting token.

    Raises:
        FileNotFoundError: if ``credentials.json`` is missing in local mode.
    """
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    # 1. Headless / Deployed Mode
    if refresh_token and client_id and client_secret:
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )

    # 2. Local / Dev Mode
    if not os.path.exists(_CREDS_PATH):
        raise FileNotFoundError(
            "credentials.json not found. Download it from the Google Cloud "
            "Console and place it in the voice-agent/ directory."
        )

    creds = None

    # Load cached token.
    if os.path.exists(_TOKEN_PATH):
        with open(_TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    # Refresh or create new credentials.
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None  # force re-auth below

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(_CREDS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

    # Cache for next run.
    with open(_TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    return creds
