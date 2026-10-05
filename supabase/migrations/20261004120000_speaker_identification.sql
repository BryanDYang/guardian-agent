-- Speaker identification results per meeting
-- (docs/writeups/systems/Accounts & Voice Identity.md, Section 7, Phase 5).
--
-- A meeting_attendees row links a matched speaker to the member's attendee.
-- Every speaker's result, matched or not, is also kept in
-- meetings.model_metadata.speaker_identification.

ALTER TABLE meeting_attendees
    -- The name shown for this speaker, snapshotted at processing time (FR-SPK-5).
    ADD COLUMN display_label       VARCHAR(255),
    -- Cosine similarity between the speaker and the member's voiceprint.
    ADD COLUMN match_score         REAL,
    ADD COLUMN match_method        VARCHAR(16) NOT NULL DEFAULT 'none'
        CHECK (match_method IN ('voice', 'none')),
    ADD COLUMN embedding_model_id  VARCHAR(128);
