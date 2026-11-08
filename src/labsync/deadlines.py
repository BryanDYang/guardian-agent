"""Resolve calendar deadlines using the recorded meeting day as context."""

import re
from datetime import date, datetime, timedelta


def explicit_deadline(
    text: str | None, meeting_date: date | None = None
) -> date | None:
    if not text:
        return None
    value = re.sub(r"^(?:by|on|due(?:\s+(?:by|on))?)\s+", "", text.strip(), flags=re.I)
    value = value.rstrip(".").strip()
    if isinstance(meeting_date, datetime):
        meeting_date = meeting_date.date()
    if meeting_date and value.lower() in {
        "today",
        "tomorrow",
        "the day after tomorrow",
    }:
        days = {"today": 0, "tomorrow": 1, "the day after tomorrow": 2}[value.lower()]
        return meeting_date + timedelta(days=days)
    # Numeric slash dates remain unresolved because the locale is ambiguous.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    value = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", value, flags=re.I)
    if re.fullmatch(r"(?:[A-Za-z]+\s+\d{1,2}|\d{1,2}\s+[A-Za-z]+)", value):
        if meeting_date is None:
            return None
        # The next occurrence includes the meeting day and handles year rollover
        # and leap days. Do not use today's date when replaying older recordings.
        for year in range(meeting_date.year, min(meeting_date.year + 9, 10000)):
            resolved = explicit_deadline(f"{value} {year}")
            if resolved is not None and resolved >= meeting_date:
                return resolved
        return None
    if not re.fullmatch(
        r"(?:[A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})", value
    ):
        return None
    for pattern in (
        "%B %d, %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None
