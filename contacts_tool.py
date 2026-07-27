"""
Contacts tool — local JSON-backed contact manager with fuzzy name matching.

Stores contacts in ``contacts.json`` next to this file.  Each contact has a
display name (the key), an email, and optional notes.

Example contacts.json:
    {
        "Ahmed":  {"email": "ahmed@example.com", "notes": "classmate"},
        "Moaz":   {"email": "rmoazhassam555@gmail.com"}
    }
"""

import json
import os
from difflib import get_close_matches

_FILE = os.path.join(os.path.dirname(__file__), "contacts.json")


# ---------------------------------------------------------------------------
# Internal helpers (not exposed as LLM tools)
# ---------------------------------------------------------------------------

def _load() -> dict:
    """Load contacts dict from disk."""
    if not os.path.exists(_FILE):
        return {}
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError):
        return {}


def _save(contacts: dict) -> None:
    """Persist contacts dict to disk."""
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)


def get_contact_names() -> list[str]:
    """Return all stored contact names (for Whisper prompt biasing).

    This is NOT an LLM tool — it is called internally by stt.py.
    """
    return list(_load().keys())


# ---------------------------------------------------------------------------
# LLM-callable tool functions
# ---------------------------------------------------------------------------

def lookup_contact(name: str) -> str:
    """Look up a contact by name using fuzzy matching.

    Args:
        name: The spoken name to search for (case-insensitive, typo-tolerant).

    Returns a spoken sentence with the contact's email, or a 'not found' message.
    """
    contacts = _load()
    if not contacts:
        return (
            f"I don't have any contacts saved yet. "
            f"I don't have {name}'s email address. Could you tell me their email?"
        )

    # Build a lowercase-to-original mapping for fuzzy matching.
    lower_map = {k.lower(): k for k in contacts}
    query = name.strip().lower()

    # 1. Exact match (case-insensitive).
    if query in lower_map:
        original = lower_map[query]
        contact = contacts[original]
        email = contact.get("email", "no email on file")
        notes = contact.get("notes", "")
        notes_part = f" (notes: {notes})" if notes else ""
        return f"{original}'s email is {email}{notes_part}."

    # 2. Fuzzy match — tolerates STT misspellings.
    close = get_close_matches(query, lower_map.keys(), n=1, cutoff=0.6)
    if close:
        original = lower_map[close[0]]
        contact = contacts[original]
        email = contact.get("email", "no email on file")
        notes = contact.get("notes", "")
        notes_part = f" (notes: {notes})" if notes else ""
        return (
            f"I found a close match: {original}'s email is {email}{notes_part}. "
            f"(Matched from '{name}'.)"
        )

    # 3. Not found.
    return (
        f"I don't have anyone named {name} in your contacts. "
        f"Could you tell me their email address so I can save it?"
    )


def add_contact(name: str, email: str, notes: str = "") -> str:
    """Add or update a contact.

    Args:
        name: Display name for the contact.
        email: Their email address.
        notes: Optional notes (e.g. 'classmate', 'project partner').

    Returns a spoken confirmation.
    """
    try:
        contacts = _load()
        entry = {"email": email.strip()}
        if notes:
            entry["notes"] = notes.strip()
        contacts[name.strip()] = entry
        _save(contacts)
        return f"Saved! I've added {name.strip()} with email {email.strip()} to your contacts."
    except Exception as e:
        return f"Sorry, I couldn't save that contact. {e}"


def list_contacts() -> str:
    """List all saved contacts with names and emails.

    Returns a spoken-friendly summary.
    """
    contacts = _load()
    if not contacts:
        return "You don't have any contacts saved yet."

    count = len(contacts)
    items = []
    for name, info in contacts.items():
        email = info.get("email", "no email")
        items.append(f"{name} ({email})")

    if count == 1:
        return f"You have one contact: {items[0]}."

    if count == 2:
        joined = f"{items[0]} and {items[1]}"
    else:
        joined = ", ".join(items[:-1]) + f", and {items[-1]}"

    return f"You have {count} contacts: {joined}."
