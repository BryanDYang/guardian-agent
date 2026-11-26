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
    # A clock time beside the day ("tomorrow at 10 a.m.", "seven tonight") is
    # not part of which calendar day was meant.
    hour = r"(?:\d{1,2}|seven|eight|nine|ten|eleven|twelve)(?::\d{2})?"
    ampm = r"[ap]\.?m\.?"
    for _ in range(3):
        trimmed = re.sub(
            rf"\s+(?:before\s+(?:noon|midnight)|(?:at|before|around)\s+{hour}(?:\s*{ampm})?|{hour}\s*{ampm})$",
            "",
            value,
            flags=re.I,
        ).rstrip(", ")
        trimmed = re.sub(
            rf"^(?:(?:at|before|around)\s+)?{hour}(?:\s*{ampm})?\s+(?=(?:today|tonight|tomorrow)\b)",
            "",
            trimmed,
            flags=re.I,
        )
        if trimmed == value:
            break
        value = trimmed
    value = re.sub(r"\s+(?:morning|afternoon|evening|night)$", "", value, flags=re.I)
    if isinstance(meeting_date, datetime):
        meeting_date = meeting_date.date()
    if meeting_date and value.lower() in {
        "today",
        "tonight",
        "tomorrow",
        "the day after tomorrow",
    }:
        days = {"today": 0, "tonight": 0, "tomorrow": 1, "the day after tomorrow": 2}[
            value.lower()
        ]
        return meeting_date + timedelta(days=days)
    weekdays = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]
    weekday = re.fullmatch(
        r"(?:(this|next)\s+)?(" + "|".join(weekdays) + r")", value, re.I
    )
    if meeting_date and weekday:
        offset = (weekdays.index(weekday[2].lower()) - meeting_date.weekday()) % 7
        if weekday[1] and weekday[1].lower() == "next":
            offset = 7 - meeting_date.weekday() + weekdays.index(weekday[2].lower())
        return meeting_date + timedelta(days=offset)
    # A weekday beside an explicit date is a consistency check.
    dated_weekday = re.fullmatch(
        r"(?:today|tomorrow),?\s+("
        + "|".join(weekdays)
        + r"),?\s+(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?",
        value,
        re.I,
    )
    short_date = re.fullmatch(
        r"(?:(?:this|next)\s+)?("
        + "|".join(weekdays)
        + r"),?\s+(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)?",
        value,
        re.I,
    )
    if meeting_date and (dated_weekday or short_date):
        match = dated_weekday or short_date
        for offset in range(32):
            candidate = meeting_date + timedelta(days=offset)
            if candidate.day == int(match[2]) and candidate.weekday() == weekdays.index(
                match[1].lower()
            ):
                if dated_weekday and candidate != meeting_date + timedelta(
                    days=int(value.lower().startswith("tomorrow"))
                ):
                    return None
                return candidate
        return None
    calendar_weekday = re.fullmatch(
        r"(" + "|".join(weekdays) + r"),?\s+(.+)", value, re.I
    )
    if calendar_weekday:
        resolved = explicit_deadline(calendar_weekday[2], meeting_date)
        return (
            resolved
            if resolved
            and resolved.weekday() == weekdays.index(calendar_weekday[1].lower())
            else None
        )
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


def suggested_deadline(
    text: str | None, proposed: str | None, meeting_date: date | None = None
) -> date | None:
    """The parsed deadline, else the model's reading of the same quoted words.

    A model date needs spoken deadline text and cannot precede the meeting.
    It is a pending suggestion that a reviewer confirms or changes."""
    if parsed := explicit_deadline(text, meeting_date):
        return parsed
    if not text or not proposed:
        return None
    try:
        day = date.fromisoformat(proposed)
    except ValueError:
        return None
    if isinstance(meeting_date, datetime):
        meeting_date = meeting_date.date()
    return None if meeting_date and day < meeting_date else day
