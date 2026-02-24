import os
import sys
from unittest.mock import patch

sys.path.append(os.getcwd())

from core.patcher import run_patch


def _write_minimal_patch(tmp_path, app_id: str):
    app_dir = tmp_path / "apps" / app_id
    app_dir.mkdir(parents=True, exist_ok=True)
    patch_file = app_dir / "patch.py"
    patch_file.write_text(
        "def patch(decompiled_dir):\n"
        "    return True\n",
        encoding="utf-8",
    )


def test_run_patch_injects_updater_for_non_spotify(tmp_path, monkeypatch):
    _write_minimal_patch(tmp_path, "demo")
    monkeypatch.chdir(tmp_path)

    with patch("core.patcher.inject_universal_updater", return_value=True) as inject_mock:
        assert run_patch("demo", "build_output") is True
        inject_mock.assert_called_once_with(decompiled_dir="build_output", app_id="demo")


def test_run_patch_skips_updater_for_spotify(tmp_path, monkeypatch):
    _write_minimal_patch(tmp_path, "spotify")
    monkeypatch.chdir(tmp_path)

    with patch("core.patcher.inject_universal_updater", return_value=True) as inject_mock:
        assert run_patch("spotify", "build_output") is True
        inject_mock.assert_not_called()


def test_run_patch_fails_if_updater_fails(tmp_path, monkeypatch):
    _write_minimal_patch(tmp_path, "demo")
    monkeypatch.chdir(tmp_path)

    with patch("core.patcher.inject_universal_updater", return_value=False):
        assert run_patch("demo", "build_output") is False
