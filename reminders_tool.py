"""
Reminders tool — local JSON-backed task/reminder manager.

Stores reminders in ``reminders.json`` next to this file.
"""

import json
import os
from datetime import datetime

_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")


def _load() -> list[dict]:
    """Load reminders from disk (or return empty list)."""
    if not os.path.exists(_FILE):
        return []
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save(reminders: list[dict]) -> None:
    """Persist reminders to disk."""
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=2, ensure_ascii=False)


def add_reminder(task: str, due: str = None) -> str:
    """Add a new reminder.

    Args:
        task: Description of the task/reminder.
        due: Optional due date or time as a string (e.g. "tomorrow", "July 25").

    Returns a spoken confirmation.
    """
    try:
        reminders = _load()
        entry = {
            "task": task,
            "due": due,
            "created": datetime.now().isoformat(),
        }
        reminders.append(entry)
        _save(reminders)
        due_part = f", due {due}" if due else ""
        return f"Got it! I've added a reminder: {task}{due_part}."
    except Exception as e:
        return f"Sorry, I couldn't save that reminder. {e}"


def list_reminders(status: str = "active") -> str:
    """Return all active reminders as a spoken-friendly summary."""
    try:
        reminders = _load()
        if not reminders:
            return "You don't have any reminders right now."

        count = len(reminders)
        if count == 1:
            r = reminders[0]
            due_part = f", due {r['due']}" if r.get("due") else ""
            return f"You have one reminder: {r['task']}{due_part}."

        items = []
        for r in reminders:
            due_part = f" (due {r['due']})" if r.get("due") else ""
            items.append(f"{r['task']}{due_part}")

        # Join with commas and "and" before the last item.
        if len(items) == 2:
            joined = f"{items[0]}, and {items[1]}"
        else:
            joined = ", ".join(items[:-1]) + f", and {items[-1]}"

        return f"You have {count} reminders: {joined}."
    except Exception as e:
        return f"Sorry, I couldn't read your reminders. {e}"


def complete_reminder(task_description: str) -> str:
    """Mark the closest-matching reminder as done and remove it.

    Uses simple substring/case-insensitive matching.
    """
    try:
        reminders = _load()
        if not reminders:
            return "You don't have any reminders to complete."

        query = task_description.strip().lower()

        # Find best match: prefer exact substring, then partial overlap.
        best_idx = None
        best_score = 0
        for i, r in enumerate(reminders):
            task_lower = r["task"].lower()
            if query in task_lower or task_lower in query:
                score = len(query)
                if score > best_score:
                    best_score = score
                    best_idx = i
            else:
                # Word overlap score.
                query_words = set(query.split())
                task_words = set(task_lower.split())
                overlap = len(query_words & task_words)
                if overlap > best_score:
                    best_score = overlap
                    best_idx = i

        if best_idx is None or best_score == 0:
            return f"I couldn't find a reminder matching '{task_description}'."

        completed = reminders.pop(best_idx)
        _save(reminders)
        return f"Done! I've completed the reminder: {completed['task']}."
    except Exception as e:
        return f"Sorry, I couldn't complete that reminder. {e}"
