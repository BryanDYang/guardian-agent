-- Accounts and project membership
-- (docs/writeups/systems/Accounts & Voice Identity.md, Section 7, Phase 1).
--
-- Supabase Auth owns identity (auth.users). This adds the app-side profile,
-- project membership, invitations, and who-did-what columns.
-- Like every other table, the new ones have RLS enabled with no policies:
-- only the backend's direct database connection can read or write (D5).
-- Voice tables come later with the voice plan.

-- ============================================================================
-- 1. PROFILES
-- One row per Supabase auth user, created by the trigger below (D14).
-- Emails are stored lowercase so invitations can match on equality.
-- ============================================================================
CREATE TABLE profiles (
    id                       UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email                    TEXT NOT NULL CHECK (email = lower(email)),
    display_name             VARCHAR(255),
    title                    VARCHAR(255),
    avatar_url               TEXT,
    auth_provider            VARCHAR(32) NOT NULL,  -- 'email' | 'google'
    onboarding_completed_at  TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_email ON profiles(email);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Runs as the table owner because Supabase Auth inserts users with a role
-- that has no access to public tables. search_path is empty so every name is
-- schema-qualified and nothing can be shadowed.
CREATE FUNCTION public.handle_new_user() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name, auth_provider)
    VALUES (
        NEW.id,
        lower(NEW.email),
        -- Email sign-up sends full_name; Google sends name.
        left(NULLIF(btrim(COALESCE(
            NEW.raw_user_meta_data ->> 'full_name',
            NEW.raw_user_meta_data ->> 'name'
        )), ''), 255),
        COALESCE(NEW.raw_app_meta_data ->> 'provider', 'email')
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Keeps profiles.email current when a user changes their email in Supabase Auth,
-- so invitation matching never uses a stale address.
CREATE FUNCTION public.handle_user_email_change() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
    UPDATE public.profiles
    SET email = lower(NEW.email), updated_at = now()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_email_changed
    AFTER UPDATE OF email ON auth.users
    FOR EACH ROW
    WHEN (NEW.email IS DISTINCT FROM OLD.email)
    EXECUTE FUNCTION public.handle_user_email_change();

-- Trigger functions only; nobody should call them through the Data API.
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.handle_user_email_change() FROM PUBLIC, anon, authenticated;

-- ============================================================================
-- 2. PROJECT MEMBERS
-- A user sees a project only through a row here (D15).
-- ============================================================================
CREATE TABLE project_members (
    project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role        VARCHAR(16) NOT NULL CHECK (role IN ('owner', 'member')),
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (project_id, user_id)
);

-- The primary key serves "members of a project"; this serves "my projects".
CREATE INDEX idx_project_members_user_id ON project_members(user_id);

ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3. PROJECT INVITATIONS
-- Only a SHA-256 hash of the invite token is stored (FR-INV-3).
-- "Expired" is not a status: a pending row past expires_at is expired.
-- ============================================================================
CREATE TABLE project_invitations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    email        TEXT NOT NULL CHECK (email = lower(email)),
    role         VARCHAR(16) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
    token_hash   BYTEA NOT NULL UNIQUE CHECK (octet_length(token_hash) = 32),
    invited_by   UUID REFERENCES profiles(id) ON DELETE SET NULL,
    status       VARCHAR(16) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'declined', 'revoked')),
    expires_at   TIMESTAMPTZ NOT NULL,
    accepted_by  UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at  TIMESTAMPTZ,
    CONSTRAINT chk_project_invitations_resolved
        CHECK ((status = 'pending') = (resolved_at IS NULL))
);

-- At most one open invitation per person per project (FR-INV-2).
CREATE UNIQUE INDEX uq_project_invitations_pending
    ON project_invitations(project_id, email) WHERE status = 'pending';
-- "Invitations for my email" in Profile > Workspaces (FR-INV-8).
CREATE INDEX idx_project_invitations_pending_email
    ON project_invitations(email) WHERE status = 'pending';

ALTER TABLE project_invitations ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 4. WHO DID WHAT (FR-PROJ-6, FR-PROJ-8, FR-SPK-4)
-- Nullable because rows written before accounts have no author. Phase 9
-- backfills the hosted data; NOT NULL can follow in a later migration.
-- ON DELETE SET NULL keeps a deleted user's shared content (FR-ACCT-5).
-- ============================================================================
ALTER TABLE projects
    ADD COLUMN created_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE meetings
    ADD COLUMN uploaded_by UUID REFERENCES profiles(id) ON DELETE SET NULL;

ALTER TABLE tasks
    ADD COLUMN assignee_user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    ADD COLUMN approved_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    ADD COLUMN approved_at TIMESTAMPTZ;

CREATE INDEX idx_tasks_assignee_user_id ON tasks(assignee_user_id);

ALTER TABLE task_audit_log
    ADD COLUMN actor_id UUID REFERENCES profiles(id) ON DELETE SET NULL;

-- Conversations are private to their creator (D10) and go with the account.
ALTER TABLE chat_conversations
    ADD COLUMN user_id UUID REFERENCES profiles(id) ON DELETE CASCADE;

CREATE INDEX idx_chat_conversations_user_project
    ON chat_conversations(user_id, project_id);

-- Links a signed-up user to their speaker identity (one attendee per user).
ALTER TABLE attendees
    ADD COLUMN user_id UUID UNIQUE REFERENCES profiles(id) ON DELETE SET NULL;
