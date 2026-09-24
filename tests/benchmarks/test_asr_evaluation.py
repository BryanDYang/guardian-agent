"""Known-error JiWER examples and split/input integrity; no audio inference."""

import copy
import json
import wave
from pathlib import Path
from zipfile import ZipFile

import pytest

from labsync.asr_evaluation import (
    file_hash,
    normalize,
    prepare,
    reference_words,
    score,
    validate_manifest,
    word_counts,
)

MANIFEST = Path(__file__).parents[1] / "fixtures/asr/manifest.json"


def test_known_edit_counts():
    assert word_counts(
        "one two three four five six seven", "one too three five six seven extra"
    ) == {
        "hits": 5,
        "substitutions": 1,
        "deletions": 1,
        "insertions": 1,
        "reference_words": 7,
    }
    assert word_counts("one two", "")["deletions"] == 2
    assert word_counts("", "extra")["insertions"] == 1


def test_normalization_keeps_fillers_and_word_content():
    assert normalize("Um, I’m READY! Twenty-two.") == "um im ready twenty two"
    assert word_counts("Hello, WORLD!", "hello world")["hits"] == 2


def test_manifest_is_series_disjoint():
    manifest = json.loads(MANIFEST.read_text())
    validate_manifest(manifest)
    leaked = copy.deepcopy(manifest["meetings"][0])
    leaked.update(meeting_id="TS3005b", split="test")
    manifest["meetings"].append(leaked)
    with pytest.raises(ValueError, match="crosses splits"):
        validate_manifest(manifest)


def test_reject_duplicate_and_overlapping_windows():
    manifest = json.loads(MANIFEST.read_text())
    manifest["meetings"][0]["windows"] = [[10, 20], [19, 30]]
    with pytest.raises(ValueError, match="overlapping"):
        validate_manifest(manifest)
    manifest = json.loads(MANIFEST.read_text())
    manifest["meetings"].append(manifest["meetings"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        validate_manifest(manifest)


def make_archive(path):
    with ZipFile(path, "w") as archive:
        for speaker in "ABCD":
            text = '<root><w starttime="0" endtime="1">outside</w>'
            if speaker == "A":
                text += '<w starttime="1" endtime="2">hello</w>'
                text += '<w starttime="2" endtime="2" punc="true">.</w>'
                text += '<noise starttime="2" endtime="2.5">noise</noise>'
                text += "<w>untimed</w>"
            if speaker == "B":
                text += '<w starttime="2" endtime="3">world</w>'
                text += '<w starttime="3.5" endtime="4.5">next</w>'
            archive.writestr(f"words/TESTa.{speaker}.words.xml", text + "</root>")


def test_reference_midpoint_and_nonword_filtering(tmp_path):
    archive = tmp_path / "words.zip"
    make_archive(archive)
    words = reference_words(archive, "TESTa", 1, 4)
    assert [w["text"] for w in words] == ["hello", "world"]
    assert [w["speaker"] for w in words] == ["A", "B"]
    with pytest.raises(ValueError, match="four AMI"):
        reference_words(archive, "missing", 1, 4)


def test_prepare_and_score_with_missing_prediction(tmp_path):
    archive = tmp_path / "words.zip"
    make_archive(archive)
    audio_path = tmp_path / "audio.wav"
    with wave.open(str(audio_path), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\0\0" * 16000 * 5)
    manifest = {
        "annotation_archive": str(archive),
        "meetings": [
            {
                "meeting_id": "TESTa",
                "series": "TEST",
                "split": "test",
                "audio_path": str(audio_path),
                "windows": [[1, 3], [3, 5]],
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    prepared = tmp_path / "prepared"
    prepare(manifest_path, prepared)
    dataset_path = prepared / "dataset.json"
    dataset = json.loads(dataset_path.read_text())
    assert dataset["clips"][0]["reference"] == "hello world"
    with wave.open(str(prepared / dataset["clips"][0]["audio"])) as audio:
        assert audio.getnframes() / audio.getframerate() == 2
    with pytest.raises(ValueError, match="already exists"):
        prepare(manifest_path, prepared)
    output = tmp_path / "run"
    output.mkdir()
    (output / "run.json").write_text(
        json.dumps({"dataset_sha256": file_hash(dataset_path)})
    )
    clip = dataset["clips"][0]
    prediction = {
        "id": clip["id"],
        "audio_sha256": clip["audio_sha256"],
        "hypothesis": "hello world",
        "wall_seconds": 1,
    }
    (output / f"{clip['id']}.json").write_text(json.dumps(prediction))
    report = score(dataset_path, output)
    assert report["splits"]["test"]["failures"] == 1
    assert report["splits"]["test"]["reference_words"] == 3
    assert report["splits"]["test"]["wer"] == pytest.approx(1 / 3)
    assert report["splits"]["test"]["real_time_factor"] is None
    prediction["audio_sha256"] = "changed"
    (output / f"{clip['id']}.json").write_text(json.dumps(prediction))
    with pytest.raises(ValueError, match="identity mismatch"):
        score(dataset_path, output)
    dataset_path.write_text(dataset_path.read_text() + " ")
    with pytest.raises(ValueError, match="Dataset differs"):
        score(dataset_path, output)
