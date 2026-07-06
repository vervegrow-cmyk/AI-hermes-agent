import subprocess

from shared.clients import BrowserHarnessClient


def test_version_invokes_wrapper(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    wrapper_script = tmp_path / "browser-harness.ps1"
    wrapper_script.write_text("", encoding="utf-8")

    def fake_run(*args, **kwargs):
        captured["cmd"] = args[0]
        captured["cwd"] = kwargs["cwd"]
        return subprocess.CompletedProcess(args[0], 0, stdout="0.1.3\n", stderr="")

    monkeypatch.setattr("shared.clients.browser_harness.subprocess.run", fake_run)

    client = BrowserHarnessClient(wrapper_script=wrapper_script, root_dir=tmp_path)

    assert client.version() == "0.1.3"
    assert captured["cmd"] == [
        "powershell.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper_script.resolve()),
        "--version",
    ]
    assert captured["cwd"] == str(tmp_path.resolve())


def test_doctor_returns_process_payload(monkeypatch, tmp_path):
    wrapper_script = tmp_path / "browser-harness.ps1"
    wrapper_script.write_text("", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0],
            1,
            stdout="doctor output",
            stderr="doctor error",
        )

    monkeypatch.setattr("shared.clients.browser_harness.subprocess.run", fake_run)

    client = BrowserHarnessClient(wrapper_script=wrapper_script, root_dir=tmp_path)
    result = client.doctor(check=False)

    assert result["stdout"] == "doctor output"
    assert result["stderr"] == "doctor error"
    assert result["returncode"] == 1


def test_run_script_passes_stdin(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    wrapper_script = tmp_path / "browser-harness.ps1"
    wrapper_script.write_text("", encoding="utf-8")

    def fake_run(*args, **kwargs):
        captured["cmd"] = args[0]
        captured["input"] = kwargs["input"]
        return subprocess.CompletedProcess(
            args[0],
            0,
            stdout="ok\n",
            stderr="",
        )

    monkeypatch.setattr("shared.clients.browser_harness.subprocess.run", fake_run)

    client = BrowserHarnessClient(wrapper_script=wrapper_script, root_dir=tmp_path)
    result = client.run_script("print(page_info())")

    assert captured["cmd"] == [
        "powershell.exe",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(wrapper_script.resolve()),
    ]
    assert captured["input"] == "print(page_info())"
    assert result["stdout"] == "ok\n"
