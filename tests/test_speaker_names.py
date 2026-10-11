from labsync.speaker_names import suggestions


def turn(text, label="SPEAKER_00", key="t1"):
    return {
        "content": text,
        "speaker_label": label,
        "turn_key": key,
        "start_time_ms": 1000,
    }


def test_direct_introductions_keep_evidence_and_do_not_identify_an_account():
    result = suggestions(
        [turn("Okay, so my name is Danny Mangrel. I handle marketing.")]
    )
    assert result["SPEAKER_00"][0] == {
        "name": "Danny Mangrel",
        "quote": "Okay, so my name is Danny Mangrel",
        "turn_key": "t1",
        "timestamp_ms": 1000,
    }


def test_addressing_somebody_quoting_them_and_unknown_voice_do_not_name_speaker():
    assert (
        suggestions(
            [
                turn("Danny, can you prepare the report?"),
                turn("He said my name is Danny."),
                turn("I am going to write the report."),
                turn("My name is Danny.", "UNKNOWN"),
            ]
        )
        == {}
    )


def test_conflicting_introductions_are_preserved_for_review():
    result = suggestions([turn("I'm Alex."), turn("My name is Sam.", key="t2")])
    assert [x["name"] for x in result["SPEAKER_00"]] == ["Alex", "Sam"]


def test_ami_introductions_as_transcribed():
    for name in ["Marijn Plomf", "Imkudio", "Wesley Neymar", "Danny Mangrel"]:
        assert (
            suggestions([turn(f"I'm {name} and I work here.")])["SPEAKER_00"][0]["name"]
            == name
        )
