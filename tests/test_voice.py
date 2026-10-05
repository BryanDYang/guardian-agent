"""Voice consent and enrollment (Accounts & Voice Identity spec, Section 9.1,
FR-VOICE-1 to FR-VOICE-9).

The quality checks run on synthetic audio. The API tests replace decoding and
the speaker model, and run against a local database only, e.g. after
`supabase start`:
TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
Never point this at the Supabase project."""

import math
import os
import random
from array import array

import psycopg
import pytest
from conftest import JWT_SECRET, SUPABASE_URL
from fastapi.testclient import TestClient

from labsync import voice
from labsync.extraction import Transcript, Turn
from labsync.server import create_app

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL not set")


def audio(seconds, *, speech_dbfs=-20.0, noise_dbfs=-60.0, talking=0.7):
    """Syllable-like bursts of a voiced tone over steady room noise, 16 kHz."""
    rng = random.Random(seconds)
    peak = 32768 * math.sqrt(2) * 10 ** (speech_dbfs / 20)
    noise = 32768 * 10 ** (noise_dbfs / 20)
    samples = array("h")
    for n in range(int(seconds * voice.SAMPLE_RATE)):
        t = n / voice.SAMPLE_RATE
        on = (t % 0.5) < 0.5 * talking and speech_dbfs > -100
        value = peak * math.sin(2 * math.pi * 180 * t) if on else 0.0
        value += rng.gauss(0, noise)
        samples.append(int(max(-32768, min(32767, value))))  # 16-bit clipping
    return samples


def check(samples, minimum=8.0):
    return voice.check_clip(samples, minimum)


def test_clear_speech_passes():
    result = check(audio(15))
    assert result.reason is None
    assert 9.5 < result.speech_seconds < 11.5  # 70% of 15 s is speech
    assert -24 < result.speech_dbfs < -16


@pytest.mark.parametrize(
    ("samples", "reason"),
    [
        (array("h"), "too_short"),
        (audio(15, speech_dbfs=-200), "too_quiet"),  # room noise only
        (audio(15, speech_dbfs=-50, noise_dbfs=-80), "too_quiet"),
        (audio(15, speech_dbfs=0), "too_loud"),  # peaks clip at full scale
        (audio(15, speech_dbfs=-20, noise_dbfs=-28), "noisy"),
        (audio(5), "too_short"),
    ],
    ids=["empty", "silent", "quiet", "clipped", "noisy", "short"],
)
def test_each_problem_has_its_own_reason(samples, reason):
    assert check(samples).reason == reason


def voices(base, **odd):
    """Embeddings near `base`, except clips named in `odd`."""

    def embed(samples):
        name = embed.order.pop(0)
        return odd.get(name, [x + 0.05 * (i % 3) for i, x in enumerate(base)])

    embed.order = list(voice.CLIPS)
    return embed


BASE = [math.sin(i) for i in range(256)]
OTHER = [math.cos(3 * i) for i in range(256)]


def test_voiceprint_is_the_normalized_average(monkeypatch):
    monkeypatch.setattr(voice, "decode", lambda path: audio(15))
    monkeypatch.setattr(voice, "embed", voices(BASE))
    result = voice.enroll({name: f"clip-{name}" for name in voice.CLIPS})
    assert result.failures == []
    assert len(result.embedding) == 256
    assert math.isclose(sum(x * x for x in result.embedding), 1.0)
    assert voice.cosine(result.embedding, BASE) > 0.99
    assert set(result.quality["pairwise_similarity"]) == {"A-B", "A-C", "B-C"}


def test_a_different_voice_is_named(monkeypatch):
    monkeypatch.setattr(voice, "decode", lambda path: audio(15))
    monkeypatch.setattr(voice, "embed", voices(BASE, B=OTHER))
    result = voice.enroll({name: f"clip-{name}" for name in voice.CLIPS})
    assert result.embedding is None
    assert result.failures == [{"clip": "B", "reason": "inconsistent"}]


def test_all_clips_together_need_thirty_seconds_of_speech(monkeypatch):
    lengths = {"clip-A": 13, "clip-B": 12, "clip-C": 14}  # each passes, ~29 s in all
    monkeypatch.setattr(voice, "decode", lambda path: audio(lengths[path]))
    monkeypatch.setattr(voice, "embed", voices(BASE))
    result = voice.enroll({name: f"clip-{name}" for name in voice.CLIPS})
    # B has the least speech, but only C (in your own words) can be made longer.
    assert result.failures == [{"clip": "C", "reason": "too_short"}]


# ------------------------------------------------- speaker identification


def at(degrees):
    """A unit vector whose cosine with at(d) is cos(degrees - d)."""
    return [math.cos(math.radians(degrees)), math.sin(math.radians(degrees))]


def member(name, degrees, email=None):
    return {
        "user_id": f"id-{name}",
        "name": name,
        "email": email or f"{name.lower()}@example.com",
        "embedding": at(degrees),
    }


def cluster(degrees, seconds=30.0):
    return {"embedding": at(degrees), "speech_seconds": seconds}


def transcript(*speakers):
    turns = [
        Turn(id=f"m:turn:{i}", speaker=s, start_time_ms=i, end_time_ms=i, content="Hi")
        for i, s in enumerate(speakers)
    ]
    return Transcript(project_id="p", meeting_id="m", turns=turns)


def displays(speakers):
    return {label: info["display"] for label, info in speakers.items()}


def test_a_clear_match_gets_the_members_name():
    labels = ["SPEAKER_00", "SPEAKER_01"]
    clusters = {"SPEAKER_00": cluster(10), "SPEAKER_01": cluster(200)}
    speakers = voice.match_speakers(labels, clusters, [member("Will", 0)])
    assert displays(speakers) == {"SPEAKER_00": "Will", "SPEAKER_01": "SPEAKER_1"}
    assert speakers["SPEAKER_00"] | {"speech_seconds": 0} == {
        "display": "Will",
        "user_id": "id-Will",
        "score": round(math.cos(math.radians(10)), 3),
        "method": "voice",
        "speech_seconds": 0,
    }
    assert speakers["SPEAKER_01"]["method"] == "none"


def test_each_member_matches_at_most_one_speaker():
    clusters = {"SPEAKER_00": cluster(5), "SPEAKER_01": cluster(10)}
    speakers = voice.match_speakers(
        ["SPEAKER_00", "SPEAKER_01"], clusters, [member("Will", 0), member("Ana", 120)]
    )
    assert displays(speakers) == {"SPEAKER_00": "Will", "SPEAKER_01": "SPEAKER_1"}


def test_assignment_maximizes_total_similarity():
    # SPEAKER_01 is a little closer to Will, but giving Will to SPEAKER_00 and
    # Ana to SPEAKER_01 has the higher total (spec step 4). SPEAKER_01 is then
    # rejected for Ana by the margin, since Will is closer.
    members = [member("Will", 0), member("Ana", 50)]
    clusters = {"SPEAKER_00": cluster(-25), "SPEAKER_01": cluster(15)}
    speakers = voice.match_speakers(["SPEAKER_00", "SPEAKER_01"], clusters, members)
    assert displays(speakers) == {"SPEAKER_00": "Will", "SPEAKER_01": "SPEAKER_1"}


@pytest.mark.parametrize(
    ("members", "speaker"),
    [
        ([member("Will", 0)], cluster(60)),  # cos 0.50: below the threshold
        ([member("Will", 0), member("Ana", 30)], cluster(15)),  # no margin
        ([member("Will", 0)], cluster(0, seconds=4.9)),  # too little speech
    ],
    ids=["threshold", "margin", "short"],
)
def test_doubtful_speakers_stay_unmatched(members, speaker):
    speakers = voice.match_speakers(["SPEAKER_00"], {"SPEAKER_00": speaker}, members)
    assert displays(speakers) == {"SPEAKER_00": "SPEAKER_1"}


def test_unmatched_speakers_are_numbered_by_first_appearance():
    meeting = transcript("SPEAKER_02", "UNKNOWN", "SPEAKER_00", "SPEAKER_01")
    diarized = {
        "embedding_model_id": voice.EMBEDDING_MODEL_ID,
        "speakers": {
            "SPEAKER_00": cluster(0),
            "SPEAKER_01": cluster(180),
            "SPEAKER_02": cluster(90),
        },
    }
    result = voice.identify(meeting, diarized, [member("Will", 0)])
    assert result["reason"] is None
    assert displays(result["speakers"]) == {
        "SPEAKER_02": "SPEAKER_1",
        "SPEAKER_00": "Will",
        "SPEAKER_01": "SPEAKER_2",
    }
    labeled = voice.relabel(meeting, result)
    assert [turn.speaker for turn in labeled.turns] == [
        "SPEAKER_1",
        "UNKNOWN",
        "Will",
        "SPEAKER_2",
    ]
    assert [turn.id for turn in labeled.turns] == [turn.id for turn in meeting.turns]


def test_members_with_the_same_name_get_different_labels():
    members = [member("Alex", 0, "alex@a.com"), member("Alex", 180, "alex@b.com")]
    clusters = {"SPEAKER_00": cluster(0), "SPEAKER_01": cluster(180)}
    speakers = voice.match_speakers(["SPEAKER_00", "SPEAKER_01"], clusters, members)
    assert displays(speakers) == {
        "SPEAKER_00": "Alex (alex@a.com)",
        "SPEAKER_01": "Alex (alex@b.com)",
    }


@pytest.mark.parametrize(
    ("diarized", "candidates", "reason"),
    [
        (None, [member("Will", 0)], "diarization_not_run"),
        (
            {
                "embedding_model_id": "other/model",
                "speakers": {"SPEAKER_00": cluster(0)},
            },
            [member("Will", 0)],
            "embedding_model_mismatch",
        ),
        (
            {"embedding_model_id": voice.EMBEDDING_MODEL_ID, "speakers": {}},
            [member("Will", 0)],
            "no_speaker_embeddings",
        ),
        (
            {
                "embedding_model_id": voice.EMBEDDING_MODEL_ID,
                "speakers": {"SPEAKER_00": cluster(0)},
            },
            [],
            "no_enrolled_members",
        ),
    ],
    ids=["no-diarization", "other-model", "no-embeddings", "no-members"],
)
def test_without_matching_everyone_is_speaker_n(diarized, candidates, reason):
    result = voice.identify(transcript("SPEAKER_00"), diarized, candidates)
    assert result["reason"] == reason
    assert displays(result["speakers"]) == {"SPEAKER_00": "SPEAKER_1"}


# ------------------------------------------------------------------- API


@pytest.fixture
def client(tmp_path):
    app = create_app(
        tmp_path,
        tmp_path,
        database_url=DATABASE_URL,
        supabase_url=SUPABASE_URL,
        jwt_secret=JWT_SECRET,
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fake_audio(monkeypatch):
    """Clips decode to clear speech; the speaker model returns BASE. Records
    which files were decoded, so tests can check they are gone afterwards."""
    decoded = []

    def decode(path):
        decoded.append(path)
        assert path.exists()
        return audio(15)

    monkeypatch.setattr(voice, "decode", decode)
    monkeypatch.setattr(voice, "embed", lambda samples: BASE)
    return decoded


CLIP_FILES = {
    f"clip_{name}": (f"{name}.m4a", b"fake-aac", "audio/mp4")
    for name in ("a", "b", "c")
}


def enroll(client, headers):
    return client.post(
        "/api/v1/me/voice-enrollments", files=CLIP_FILES, headers=headers
    )


def consent(client, headers, version="2026-10"):
    url = "/api/v1/me/voice-consent"
    return client.post(url, json={"consent_version": version}, headers=headers)


def stored(user_id):
    with psycopg.connect(DATABASE_URL) as conn:
        profile = conn.execute(
            "SELECT vector_dims(embedding), embedding_model_id FROM voice_profiles "
            "WHERE user_id = %s",
            (user_id,),
        ).fetchone()
        consents = conn.execute(
            "SELECT consent_version, revoked_at IS NULL FROM voice_consents "
            "WHERE user_id = %s ORDER BY granted_at",
            (user_id,),
        ).fetchall()
    return profile, consents


@needs_db
def test_enrollment_needs_consent_then_saves_a_voiceprint(
    client, make_user, fake_audio
):
    user_id, auth = make_user("Voice", onboarded=False)
    assert enroll(client, auth).status_code == 403
    assert fake_audio == []  # nothing was even read

    status = consent(client, auth).json()
    assert (status["consented"], status["enrolled"]) == (True, False)
    response = enroll(client, auth)
    assert response.status_code == 200
    body = response.json()
    assert body["enrolled"] and body["enrolled_at"]
    assert body["embedding_model_id"] == voice.EMBEDDING_MODEL_ID
    assert body["needs_rerecord"] is False
    assert "embedding" not in body  # FR-VOICE-7

    me = client.get("/api/v1/me", headers=auth).json()
    assert me["voice_enrolled_at"] == body["enrolled_at"]
    assert me["onboarding_step"] == "complete"  # FR-ONB-2
    assert stored(user_id) == ((256, voice.EMBEDDING_MODEL_ID), [("2026-10", True)])
    assert len(fake_audio) == 3
    assert not any(path.exists() for path in fake_audio)  # FR-VOICE-6


@needs_db
def test_quality_failures_name_the_clip_and_save_nothing(
    client, make_user, fake_audio, monkeypatch
):
    user_id, auth = make_user()
    consent(client, auth)
    monkeypatch.setattr(
        voice, "decode", lambda path: audio(3 if "clip-C" in path.name else 15)
    )
    response = enroll(client, auth)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "voice_quality",
        "failures": [{"clip": "C", "reason": "too_short"}],
    }
    assert stored(user_id)[0] is None


@needs_db
def test_revoking_consent_deletes_the_voiceprint(client, make_user, fake_audio):
    user_id, auth = make_user()
    consent(client, auth)
    enroll(client, auth)
    revoked = client.delete("/api/v1/me/voice-consent", headers=auth).json()
    assert (revoked["consented"], revoked["enrolled"]) == (False, False)
    assert stored(user_id) == (None, [("2026-10", False)])  # history is kept
    assert client.get("/api/v1/me", headers=auth).json()["voice_enrolled_at"] is None
    assert enroll(client, auth).status_code == 403


@needs_db
def test_newer_consent_text_replaces_the_old_grant(client, make_user):
    user_id, auth = make_user()
    consent(client, auth, "2026-10")
    consent(client, auth, "2026-10")  # agreeing again changes nothing
    consent(client, auth, "2027-01")
    assert stored(user_id)[1] == [("2026-10", False), ("2027-01", True)]


@needs_db
def test_server_without_the_voice_model_says_so(
    client, make_user, fake_audio, monkeypatch
):
    def unavailable(samples):
        raise voice.VoiceUnavailable("install the diarize extra (pyannote)")

    _, auth = make_user()
    consent(client, auth)
    monkeypatch.setattr(voice, "embed", unavailable)
    response = enroll(client, auth)
    assert response.status_code == 503
    assert "diarize extra" in response.json()["detail"]
    assert not any(path.exists() for path in fake_audio)
