"""Notice for the separately supplied CCB acoustic dependency.

This root file previously contained a supplied third-party snapshot. Its upstream
revision and redistribution license have not been verified. Historical Git
revisions may still contain that copy; Guardian Agent's MIT license does not establish
rights to that upstream code.

The app loads the separately obtained source from
contexts/meeting_transcriber-master/meeting_transcriber.py. This notice is not a
transcriber implementation. See docs/reference/ccb-transcriber.md for provenance,
the audited hash, setup, and runnable alternatives without that dependency.
"""

if __name__ == "__main__":
    raise SystemExit(
        "External transcriber required. See docs/reference/ccb-transcriber.md. "
        "For the runnable offline example, see docs/milestone_5/evaluation.md."
    )
