from datetime import date

import pytest

from labsync.deadlines import explicit_deadline, suggested_deadline


@pytest.mark.parametrize(
    "text",
    [
        "by November 9, 2026",
        "November 9 2026",
        "on Nov 9, 2026.",
        "due on 9 November 2026",
        "by November 9th, 2026",
        "2026-11-09",
    ],
)
def test_explicit_calendar_deadline(text):
    assert explicit_deadline(text) == date(2026, 11, 9)


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "next Friday",
        "tomorrow",
        "November 9",
        "11/09/2026",
        "by November 31, 2026",
        "2026-02-29",
        "maybe November 9, 2026",
        "before November 9, 2026",
        "November 9 or 10, 2026",
    ],
)
def test_ambiguous_or_invalid_deadline_stays_unresolved(text):
    assert explicit_deadline(text) is None


@pytest.mark.parametrize(
    "text, anchor, expected",
    [
        ("by November 20th", date(2026, 11, 7), date(2026, 11, 20)),
        ("November 7", date(2026, 11, 7), date(2026, 11, 7)),
        ("by January 5", date(2026, 12, 20), date(2027, 1, 5)),
        ("20 November", date(2026, 11, 21), date(2027, 11, 20)),
        ("February 29", date(2027, 1, 1), date(2028, 2, 29)),
        ("tomorrow", date(2026, 12, 31), date(2027, 1, 1)),
        ("by today", date(2026, 11, 7), date(2026, 11, 7)),
        ("the day after tomorrow", date(2026, 11, 7), date(2026, 11, 9)),
        ("by November 20, 2025", date(2026, 11, 7), date(2025, 11, 20)),
    ],
)
def test_meeting_day_anchors_missing_year_and_relative_days(text, anchor, expected):
    assert explicit_deadline(text, anchor) == expected


def test_ambiguous_dates_stay_unresolved_with_context():
    for text in ("next week", "11/20", "November 31", "maybe November 20"):
        assert explicit_deadline(text, date(2026, 11, 7)) is None


@pytest.mark.parametrize(
    "text, expected",
    [
        ("tomorrow afternoon", date(2026, 11, 25)),
        ("tonight before 9", date(2026, 11, 24)),
        ("Friday", date(2026, 11, 27)),
        ("next Wednesday", date(2026, 12, 2)),
        ("Friday, November 27th", date(2026, 11, 27)),
        ("by Friday, November 27, 2026", date(2026, 11, 27)),
        ("Friday the 27th", date(2026, 11, 27)),
        ("Monday the 30th, before noon", date(2026, 11, 30)),
        ("tomorrow, Wednesday the 25th", date(2026, 11, 25)),
        ("tomorrow, Thursday the 26th", None),
        ("Friday, November 26, 2026", None),
        ("next week", None),
    ],
)
def test_spoken_deadlines(text, expected):
    assert explicit_deadline(text, date(2026, 11, 24)) == expected


@pytest.mark.parametrize(
    "text, proposed, expected",
    [
        ("end of the week", "2026-11-27", date(2026, 11, 27)),
        ("in two weeks", "2026-12-08", date(2026, 12, 8)),
        ("Friday", "2026-12-04", date(2026, 11, 27)),
        ("end of the week", None, None),
        (None, "2026-11-27", None),
        ("end of the week", "not a date", None),
        ("end of the week", "2026-11-20", None),
    ],
)
def test_model_date_fills_only_what_the_parser_cannot(text, proposed, expected):
    assert suggested_deadline(text, proposed, date(2026, 11, 24)) == expected
