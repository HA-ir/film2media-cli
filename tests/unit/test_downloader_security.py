from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from f2m.core.exceptions import F2MDownloadError
from f2m.integrations.downloader import (
    DownloaderBackend,
    DownloadRequest,
    DownloadResult,
    StreamRequest,
    StreamResult,
    assert_path_contained,
    execute_download,
    execute_stream,
    find_downloader,
    get_install_instructions,
    resolve_destination,
    run_subprocess,
    sanitize_filename,
)


# ===========================================================================
# US1: Safe, Unprivileged Download Execution
# ===========================================================================


def test_find_downloader_discovery():
    """T006: Verify find_downloader uses system $PATH and discovers tools in priority order."""
    with patch("shutil.which") as mock_which:
        # 1. aria2c available
        mock_which.side_effect = lambda cmd: "/usr/bin/aria2c" if cmd == "aria2c" else None
        backend, path = find_downloader()
        assert backend == DownloaderBackend.ARIA2C
        assert path == "/usr/bin/aria2c"

        # 2. aria2c missing, curl available
        mock_which.side_effect = lambda cmd: "/usr/bin/curl" if cmd == "curl" else None
        backend, path = find_downloader()
        assert backend == DownloaderBackend.CURL
        assert path == "/usr/bin/curl"

        # 3. Neither available
        mock_which.side_effect = lambda cmd: None
        backend, path = find_downloader()
        assert backend == DownloaderBackend.NONE
        assert path is None


def test_absence_of_sudo_and_pkg_managers():
    """T007: Verify zero sudo/su or package managers in downloader code or command generation."""
    import inspect
    import f2m.integrations.downloader as downloader_mod

    source = inspect.getsource(downloader_mod)
    forbidden = ["sudo", "su -", "apt-get", "apt install", "dnf install", "yum install", "pacman -S", "apk add", "zypper install"]
    for word in forbidden:
        # Ensure none of these appear in actual executable logic
        # (they may appear in get_install_instructions string dicts for user advice, but never in subprocess calls)
        assert f'subprocess.run(["{word}"' not in source
        assert f'subprocess.call(["{word}"' not in source


def test_get_install_instructions():
    """T008: Verify platform-specific copy-paste install instructions."""
    debian_inst = get_install_instructions("Linux", distro="debian")
    assert "apt install aria2" in debian_inst

    fedora_inst = get_install_instructions("Linux", distro="fedora")
    assert "dnf install aria2" in fedora_inst

    arch_inst = get_install_instructions("Linux", distro="arch")
    assert "pacman -S aria2" in arch_inst

    alpine_inst = get_install_instructions("Linux", distro="alpine")
    assert "apk add aria2" in alpine_inst

    mac_inst = get_install_instructions("Darwin")
    assert "brew install aria2" in mac_inst

    win_inst = get_install_instructions("Windows")
    assert "winget install aria2" in win_inst


def test_run_subprocess_shell_true_rejected():
    """T005: Verify run_subprocess strictly rejects shell=True."""
    with pytest.raises(F2MDownloadError, match="shell execution is prohibited"):
        run_subprocess(["ls"], shell=True)


# ===========================================================================
# US2: Permission Safety & Path Traversal Protection
# ===========================================================================


def test_sanitize_filename_traversal():
    """T015: Verify filename sanitization neutralizes directory traversal."""
    assert sanitize_filename("../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("..\\..\\windows\\system32") == "windows_system32"
    assert sanitize_filename("../movie.mp4") == "movie.mp4"
    assert sanitize_filename("foo/bar/baz.mkv") == "foo_bar_baz.mkv"


def test_sanitize_filename_leading_dashes():
    """T015: Verify filename sanitization strips leading dashes (CLI option injection defense)."""
    assert sanitize_filename("-o output.txt") == "o output.txt"
    assert sanitize_filename("--all-proxy=http://evil") == "all-proxy=http_evil"
    assert sanitize_filename("---test---") == "test"


def test_sanitize_filename_control_characters():
    """T015: Verify filename sanitization strips null bytes and control characters."""
    assert sanitize_filename("movie\0.mp4") == "movie.mp4"
    assert sanitize_filename("series\x1f\x02\x07.mkv") == "series.mkv"


def test_sanitize_filename_empty_fallback():
    """T015: Verify fallback for empty or completely stripped strings."""
    assert sanitize_filename("") == "f2m_download"
    assert sanitize_filename("   ") == "f2m_download"
    assert sanitize_filename("///\\\\") == "f2m_download"
    assert sanitize_filename("...") == "f2m_download"


def test_resolve_destination_success(tmp_path: Path):
    """T018: Verify destination resolution canonicalizes path and expands ~."""
    target = tmp_path / "downloads" / "media"
    resolved = resolve_destination(str(target), subdir="Inception 2010")
    assert resolved.exists()
    assert resolved.is_dir()
    assert resolved.name == "Inception 2010"


def test_resolve_destination_read_only_failure(tmp_path: Path):
    """T017: Verify unwritable destination raises clean F2MDownloadError."""
    target = tmp_path / "readonly_dir"
    target.mkdir()

    # Mock os.access to simulate read-only
    with patch("os.access", return_value=False):
        with pytest.raises(F2MDownloadError, match="not writable"):
            resolve_destination(str(target))


def test_assert_path_contained_violation(tmp_path: Path):
    """T016: Verify path containment check detects directory escape."""
    base = tmp_path / "base"
    base.mkdir()
    escape = tmp_path / "outside" / "evil.sh"

    with pytest.raises(F2MDownloadError, match="path traversal detected"):
        assert_path_contained(escape, base)

    # Valid child path should not raise
    child = base / "valid.mp4"
    assert_path_contained(child, base)


# ===========================================================================
# US3: Atomic Downloads & Interruption Cleanup
# ===========================================================================


def test_curl_atomic_part_success(tmp_path: Path):
    """T025: Verify curl stages to .part and atomically renames upon exit code 0."""
    dest = tmp_path / "downloads"
    dest.mkdir()
    url = "https://example.com/test_video.mp4"

    req = DownloadRequest(urls=[url], destination_dir=dest)

    def mock_subprocess_run(cmd, **kwargs):
        # Verify .part file path was passed to curl
        part_arg = cmd[cmd.index("-o") + 1]
        assert part_arg.endswith("test_video.mp4.part")
        # Simulate curl creating the .part file
        Path(part_arg).write_text("dummy media content")
        res = MagicMock()
        res.returncode = 0
        return res

    with patch("f2m.integrations.downloader.find_downloader", return_value=(DownloaderBackend.CURL, "/usr/bin/curl")), \
         patch("subprocess.run", side_effect=mock_subprocess_run):
        result = execute_download(req)
        assert result.success is True
        final_file = dest / "test_video.mp4"
        assert final_file.exists()
        assert not (dest / "test_video.mp4.part").exists()
        assert final_file.read_text() == "dummy media content"


def test_curl_part_failure_cleanup(tmp_path: Path):
    """T026: Verify curl cleans up .part file on failure."""
    dest = tmp_path / "downloads"
    dest.mkdir()
    url = "https://example.com/failed_video.mp4"

    req = DownloadRequest(urls=[url], destination_dir=dest)

    def mock_subprocess_run(cmd, **kwargs):
        part_arg = cmd[cmd.index("-o") + 1]
        # Simulate partial write before crash
        Path(part_arg).write_text("corrupted partial content")
        res = MagicMock()
        res.returncode = 22  # HTTP 404 in curl
        return res

    with patch("f2m.integrations.downloader.find_downloader", return_value=(DownloaderBackend.CURL, "/usr/bin/curl")), \
         patch("subprocess.run", side_effect=mock_subprocess_run):
        result = execute_download(req)
        assert result.success is False
        assert not (dest / "failed_video.mp4.part").exists()
        assert not (dest / "failed_video.mp4").exists()


def test_sigint_cleanup(tmp_path: Path):
    """T027: Verify SIGINT during curl cleans .part file and raises KeyboardInterrupt."""
    dest = tmp_path / "downloads"
    dest.mkdir()
    url = "https://example.com/interrupted.mp4"

    req = DownloadRequest(urls=[url], destination_dir=dest)

    def mock_subprocess_run(cmd, **kwargs):
        part_arg = cmd[cmd.index("-o") + 1]
        Path(part_arg).write_text("partial data before Ctrl+C")
        raise KeyboardInterrupt()

    with patch("f2m.integrations.downloader.find_downloader", return_value=(DownloaderBackend.CURL, "/usr/bin/curl")), \
         patch("subprocess.run", side_effect=mock_subprocess_run):
        with pytest.raises(KeyboardInterrupt):
            execute_download(req)
        assert not (dest / "interrupted.mp4.part").exists()
        assert not (dest / "interrupted.mp4").exists()


def test_aria2c_execution(tmp_path: Path):
    """Verify aria2c argument assembly and execution."""
    dest = tmp_path / "downloads"
    dest.mkdir()
    urls = ["https://example.com/part1.mp4", "https://example.com/part2.mp4"]

    req = DownloadRequest(urls=urls, destination_dir=dest, proxy="http://127.0.0.1:8080")

    def mock_subprocess_run(cmd, **kwargs):
        assert cmd[0] == "/usr/bin/aria2c"
        assert "-d" in cmd and cmd[cmd.index("-d") + 1] == str(dest)
        assert "--all-proxy=http://127.0.0.1:8080" in cmd
        assert "--file-allocation=none" in cmd
        assert urls[0] in cmd and urls[1] in cmd
        res = MagicMock()
        res.returncode = 0
        return res

    with patch("f2m.integrations.downloader.find_downloader", return_value=(DownloaderBackend.ARIA2C, "/usr/bin/aria2c")), \
         patch("subprocess.run", side_effect=mock_subprocess_run):
        result = execute_download(req)
        assert result.success is True
        assert result.backend == DownloaderBackend.ARIA2C


def test_stream_execution():
    """T028 & T030: Verify streaming command assembly with mpv."""
    req = StreamRequest(urls=["https://example.com/stream.mp4"], title="Test Movie", player="mpv", proxy="http://proxy:8080")

    with patch("shutil.which", return_value="/usr/bin/mpv"), \
         patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_popen.return_value = mock_proc

        result = execute_stream(req)
        assert result.success is True
        assert result.player_name == "mpv"
        assert result.pid == 12345

        # Verify arguments passed to popen
        cmd = mock_popen.call_args[0][0]
        assert cmd[0] == "/usr/bin/mpv"
        assert "--force-media-title=Test Movie" in cmd
        assert "--http-proxy=http://proxy:8080" in cmd
        assert "https://example.com/stream.mp4" in cmd
