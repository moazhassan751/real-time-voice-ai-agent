"""
Helper script to extract Google OAuth2 credentials from your local environment.
Run this script to get the values to paste into Hugging Face Spaces Secrets.
"""

import os
import json
import pickle

_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.pickle")
_CREDS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")

def extract_tokens():
    if not os.path.exists(_CREDS_PATH):
        print("❌ credentials.json not found. Run main.py locally first to set up auth.")
        return

    if not os.path.exists(_TOKEN_PATH):
        print("❌ token.pickle not found. Run main.py locally first to authorize the app.")
        return

    # Extract Client ID and Secret from credentials.json
    with open(_CREDS_PATH, "r") as f:
        creds_data = json.load(f)
        
    client_type = "installed" if "installed" in creds_data else "web"
    client_id = creds_data.get(client_type, {}).get("client_id")
    client_secret = creds_data.get(client_type, {}).get("client_secret")

    # Extract Refresh Token from token.pickle
    with open(_TOKEN_PATH, "rb") as f:
        user_creds = pickle.load(f)
        
    refresh_token = user_creds.refresh_token

    if not refresh_token:
        print("❌ token.pickle does not contain a refresh token.")
        print("Try deleting token.pickle and running main.py again to force re-authorization.")
        return

    print("✅ Successfully extracted Google OAuth credentials!\n")
    print("Add the following as Secrets in your Hugging Face Space Settings:")
    print("-" * 50)
    print(f"GOOGLE_CLIENT_ID\n{client_id}\n")
    print(f"GOOGLE_CLIENT_SECRET\n{client_secret}\n")
    print(f"GOOGLE_REFRESH_TOKEN\n{refresh_token}")
    print("-" * 50)

if __name__ == "__main__":
    extract_tokens()
