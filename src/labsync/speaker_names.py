"""Conservative self-introduction suggestions, never account identity claims."""

import re

# Limit suggestions to direct sentence-start introductions. Names remain
# unverified ASR text until a person confirms them. General mentions are ignored.
INTRO = re.compile(
    r"(?:^|[.!?]\s+)(?:Okay,?\s+|Well,?\s+|Hi,?\s+|Hello,?\s+|so\s+)*"
    r"(?:[Mm]y name is|[Ii] am|[Ii]['’]m|[Cc]all me)\s+"
    r"(?P<name>[A-Z][a-zA-ZÀ-ÿ'-]+(?:\s+[A-Z][a-zA-ZÀ-ÿ'-]+){0,2})"
    r"(?=\s*(?:[,.!?]|$|and\b))"
)


def suggestions(turns):
    """Return evidence per raw speaker; conflicting names require manual entry."""
    by_speaker = {}
    for turn in turns:
        label = turn["speaker_label"]
        if label.upper() == "UNKNOWN":
            continue
        for match in INTRO.finditer(turn["content"]):
            name = match["name"]
            if name in {
                "Okay",
                "Well",
                "Hi",
                "Hello",
                "Sorry",
                "Yes",
                "No",
                "The",
                "A",
            }:
                continue
            by_speaker.setdefault(label, []).append(
                {
                    "name": name,
                    "quote": match.group().strip(),
                    "turn_key": turn["turn_key"],
                    "timestamp_ms": turn["start_time_ms"],
                }
            )
    return by_speaker
