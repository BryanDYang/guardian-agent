from labsync.chunking import Turn, windows


def turn(order, words, speaker="SPEAKER_01"):
    content = " ".join(f"w{order}_{i}" for i in range(words))
    return Turn(order, speaker, order * 1000, content)


def test_packs_whole_turns_up_to_the_word_limit():
    result = windows([turn(0, 4), turn(1, 4, "SPEAKER_02"), turn(2, 4)], max_words=10)
    assert [(w.first_order, w.last_order, w.start_time_ms) for w in result] == [
        (0, 1, 0),
        (2, 2, 2000),
    ]
    assert result[0].content.splitlines() == [
        "SPEAKER_01: " + turn(0, 4).content,
        "SPEAKER_02: " + turn(1, 4).content,
    ]


def test_long_turn_is_cut_into_pieces_that_point_at_it():
    result = windows([turn(0, 2), turn(1, 25), turn(2, 2)], max_words=10)
    assert [(w.first_order, w.last_order) for w in result] == [
        (0, 0), (1, 1), (1, 1), (1, 1), (2, 2),
    ]
    pieces = [w.content.removeprefix("SPEAKER_01: ") for w in result[1:4]]
    assert " ".join(pieces) == turn(1, 25).content  # nothing lost or duplicated
    assert {w.start_time_ms for w in result[1:4]} == {1000}


def test_missing_speaker_and_empty_input():
    assert windows([]) == []
    [window] = windows([Turn(0, None, 5, "hello there")])
    assert window.content == "UNKNOWN: hello there"