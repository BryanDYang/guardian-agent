"""Group diarized transcript turns into retrieval windows along turn boundaries."""

from dataclasses import dataclass

# Small windows keep retrieval precise: a hit points at about a minute of
# speech, not a whole meeting. (text-embedding-3-small itself accepts 8192 tokens.)
MAX_WORDS = 150


@dataclass(frozen=True)
class Turn:
    order: int
    speaker: str | None
    start_time_ms: int
    content: str


@dataclass(frozen=True)
class Window:
    first_order: int
    last_order: int
    start_time_ms: int
    content: str


def windows(turns: list[Turn], max_words: int = MAX_WORDS) -> list[Window]:
    """Pack consecutive whole turns into windows of at most max_words.

    A turn is only cut when it alone exceeds max_words. Its pieces become
    separate windows that all point back at that one turn and its start time.
    Every line keeps its speaker label so the speaker is searchable.
    """
    result: list[Window] = []
    pending: list[Turn] = []
    count = 0

    def flush() -> None:
        nonlocal pending, count
        if pending:
            result.append(
                Window(
                    pending[0].order,
                    pending[-1].order,
                    pending[0].start_time_ms,
                    "\n".join(_line(t.speaker, t.content) for t in pending),
                )
            )
        pending, count = [], 0

    for turn in turns:
        words = turn.content.split()
        if len(words) > max_words:
            flush()
            for start in range(0, len(words), max_words):
                piece = " ".join(words[start : start + max_words])
                result.append(
                    Window(
                        turn.order,
                        turn.order,
                        turn.start_time_ms,
                        _line(turn.speaker, piece),
                    )
                )
            continue
        if count + len(words) > max_words:
            flush()
        pending.append(turn)
        count += len(words)
    flush()
    return result


def _line(speaker: str | None, text: str) -> str:
    return f"{speaker or 'UNKNOWN'}: {text}"