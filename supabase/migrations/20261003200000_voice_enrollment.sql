-- Voice consent and voiceprints
-- (docs/writeups/systems/Accounts & Voice Identity.md, Section 7, Phase 4).
--
-- A voiceprint is biometric data. It is stored only with active consent, never
-- leaves the backend, and is deleted when consent is revoked or the account is
-- deleted. Raw enrollment audio is never stored (D11).
-- Like every other table, RLS is on with no policies (D5).

-- ============================================================================
-- 1. VOICE CONSENTS
-- One row per grant, kept after revocation as the consent history (FR-VOICE-1).
-- ============================================================================
CREATE TABLE voice_consents (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    consent_version  VARCHAR(32) NOT NULL,
    granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at       TIMESTAMPTZ
);

-- At most one active consent per user.
CREATE UNIQUE INDEX voice_consents_one_active
    ON voice_consents(user_id) WHERE revoked_at IS NULL;

ALTER TABLE voice_consents ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. VOICE PROFILES
-- One voiceprint per user: the L2-normalized average of their enrollment clips,
-- from the same model the diarization pipeline uses (D9).
-- ============================================================================
CREATE TABLE voice_profiles (
    user_id             UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    embedding           vector(256) NOT NULL,
    embedding_model_id  VARCHAR(128) NOT NULL,
    quality             JSONB NOT NULL,  -- per-clip speech, levels, pairwise similarity
    enrolled_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE voice_profiles ENABLE ROW LEVEL SECURITY;
