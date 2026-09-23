"""Import AMI manual transcript segments without reading evaluation annotations."""

import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .extraction import Transcript, Turn

NITE = "{http://nite.sourceforge.net/}"


def load_ami(archive: Path, meeting: str) -> Transcript:
    if not re.fullmatch(r"[A-Z]{2}\d{4}[a-d]?", meeting):
        raise ValueError("Invalid AMI meeting ID")
    turns = []
    with ZipFile(archive) as source:
        files = sorted(
            name
            for name in source.namelist()
            if re.fullmatch(rf"segments/{meeting}\.[A-Z]\.segments\.xml", name)
        )
        if not files:
            raise ValueError(f"No AMI segments found for {meeting}")
        for name in files:
            speaker = name.split(".")[1]
            word_file = f"{meeting}.{speaker}.words.xml"
            words = list(ET.fromstring(source.read("words/" + word_file)))
            indices = {word.attrib[NITE + "id"]: i for i, word in enumerate(words)}
            for segment in ET.fromstring(source.read(name)):
                tokens = []
                for child in segment.findall(NITE + "child"):
                    href = child.attrib["href"]
                    if not href.startswith(word_file + "#"):
                        raise ValueError(f"Unexpected AMI word reference: {href}")
                    ids = re.findall(r"id\(([^)]+)\)", href)
                    if len(ids) not in (1, 2):
                        raise ValueError(f"Invalid AMI word range: {href}")
                    start, end = indices[ids[0]], indices[ids[-1]]
                    if end < start:
                        raise ValueError(f"Reversed AMI word range: {href}")
                    tokens.extend(
                        word.text
                        for word in words[start : end + 1]
                        if word.tag == "w" and word.text
                    )
                if not tokens:
                    continue
                turns.append(
                    Turn(
                        id=segment.attrib[NITE + "id"],
                        speaker=speaker,
                        start_time_ms=round(
                            float(segment.attrib["transcriber_start"]) * 1000
                        ),
                        end_time_ms=round(
                            float(segment.attrib["transcriber_end"]) * 1000
                        ),
                        content=" ".join(tokens),
                    )
                )
    return Transcript(
        project_id="ami-" + meeting.rstrip("abcd"),
        meeting_id=meeting,
        turns=sorted(turns, key=lambda turn: (turn.start_time_ms, turn.id)),
    )
