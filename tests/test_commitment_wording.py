import pytest

from labsync.followup import explicit_self_commitment


@pytest.mark.parametrize(
    "text, expected",
    [
        ("I’ll prepare the rubric by Friday.", True),
        ("Yeah, I’ll prepare the rubric by Friday.", True),
        ("Okay, so I will prepare the rubric by Friday.", True),
        ("I’ll try to prepare the rubric by Friday.", False),
        ("Maybe I’ll prepare the rubric by Friday.", False),
        ("Will says I will prepare the rubric.", False),
        ("I will prepare the rubric if the results arrive.", False),
    ],
)
def test_spoken_commitment_wording(text, expected):
    assert explicit_self_commitment(text, text) == expected


def test_curly_apostrophe_quote_matches_straight_transcript():
    assert explicit_self_commitment(
        "I will prepare the rubric. I'll send it.", "I’ll send it."
    )
