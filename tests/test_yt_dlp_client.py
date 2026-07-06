import json
import subprocess

from shared.clients import YtDlpClient


def test_version_invokes_local_yt_dlp(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["cmd"] = args[0]
        captured["cwd"] = kwargs["cwd"]
        return subprocess.CompletedProcess(args[0], 0, stdout="2026.06.01\n", stderr="")

    monkeypatch.setattr("shared.clients.yt_dlp.subprocess.run", fake_run)

    client = YtDlpClient(root_dir=tmp_path, downloads_dir=tmp_path / "downloads")

    assert client.version() == "2026.06.01"
    assert captured["cmd"] == ["python", "-m", "yt_dlp", "--version"]
    assert captured["cwd"] == str(tmp_path.resolve())


def test_extract_info_uses_dump_single_json(monkeypatch, tmp_path):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout=json.dumps({"id": "abc123", "title": "Sample"}) + "\n",
            stderr="",
        )

    monkeypatch.setattr("shared.clients.yt_dlp.subprocess.run", fake_run)

    client = YtDlpClient(root_dir=tmp_path, downloads_dir=tmp_path / "downloads")
    payload = client.extract_info("https://example.com/watch?v=abc123")

    assert payload["id"] == "abc123"
    assert payload["title"] == "Sample"


def test_download_builds_expected_args(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured["cmd"] = args[0]
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout=str((tmp_path / "downloads" / "sample.mp3").resolve()) + "\n",
            stderr="",
        )

    monkeypatch.setattr("shared.clients.yt_dlp.subprocess.run", fake_run)

    client = YtDlpClient(root_dir=tmp_path, downloads_dir=tmp_path / "downloads")
    result = client.download(
        "https://example.com/watch?v=abc123",
        audio_only=True,
        format_selector="bestaudio/best",
    )

    assert result["saved_paths"] == [str((tmp_path / "downloads" / "sample.mp3").resolve())]
    assert "--extract-audio" in captured["cmd"]
    assert "--audio-format" in captured["cmd"]
    assert "--format" in captured["cmd"]
