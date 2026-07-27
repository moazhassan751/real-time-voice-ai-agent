"""
Time tool — returns the current local date and time in a spoken-friendly format.
"""

from datetime import datetime


def get_current_time(timezone: str = "local") -> str:
    """Return the current local date and time as a natural sentence.

    Example: "It's Friday, July 24th, 2:45 PM."
    """
    try:
        now = datetime.now()

        # Ordinal suffix for the day.
        day = now.day
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        formatted = now.strftime(f"%A, %B {day}{suffix}, %Y at %-I:%M %p")
        # Windows strftime doesn't support %-I, fall back gracefully.
        return f"It's {formatted}."
    except ValueError:
        # Fallback for Windows where %-I is unsupported.
        now = datetime.now()
        day = now.day
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

        hour = now.hour % 12 or 12
        am_pm = "AM" if now.hour < 12 else "PM"
        month = now.strftime("%B")
        weekday = now.strftime("%A")
        year = now.year
        minute = now.strftime("%M")

        return f"It's {weekday}, {month} {day}{suffix}, {year} at {hour}:{minute} {am_pm}."
