-- Storylines are generated per diarized speaker; most speakers have no attendee row.
ALTER TABLE meeting_attendee_storylines ALTER COLUMN attendee_id DROP NOT NULL;
ALTER TABLE meeting_attendee_storylines ADD COLUMN speaker_label VARCHAR(64);
