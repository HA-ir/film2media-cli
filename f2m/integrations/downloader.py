from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any
from urllib import parse as urlparse

from f2m.core.exceptions import F2MDownloadError


class DownloaderBackend(Enum):
    ARIA2C = auto()
    CURL = auto()
    NONE = auto()


@dataclass(frozen=True)
class DownloadRequest:
    urls: list[str]
    destination_dir: Path
    subdir: str | None = None
    proxy: str | None = None
    max_connections: int = 16
    max_concurrent_downloads: int = 4


@dataclass(frozen=True)
class DownloadResult:
    success: bool
    backend: DownloaderBackend
    exit_code: int
    destination_dir: Path
    downloaded_files: list[Path] = field(default_factory=list)
    error_message: str | None = None


@dataclass(frozen=True)
class StreamRequest:
    urls: list[str]
    title: str
    player: str = "auto"
    proxy: str | None = None


@dataclass(frozen=True)
class StreamResult:
    success: bool
    player_name: str
    pid: int | None = None
    error_message: str | None = None


def run_subprocess(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    """
    Safely execute an external process without shell interpolation.
    Strictly enforces list[str] arguments and shell=False.
    """
    if kwargs.get("shell", False):
        raise F2MDownloadError("Security violation: shell execution is prohibited")
    kwargs["shell"] = False
    return subprocess.run(cmd, **kwargs)


def find_downloader() -> tuple[DownloaderBackend, str | None]:
    """
    Discovers available download managers strictly on system $PATH.
    Prioritizes aria2c, then curl. Never checks local application folders.
    """
    aria2c_exe = shutil.which("aria2c")
    if aria2c_exe:
        return DownloaderBackend.ARIA2C, aria2c_exe

    curl_exe = shutil.which("curl")
    if curl_exe:
        return DownloaderBackend.CURL, curl_exe

    return DownloaderBackend.NONE, None


def get_install_instructions(system: str | None = None, distro: str | None = None) -> str:
    """
    Returns platform-tailored manual copy-paste installation commands.
    """
    sys_name = system or platform.system()
    if sys_name == "Linux":
        d = (distro or "").lower()
        if not d and os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "fedora" in content or "rhel" in content or "centos" in content:
                        d = "fedora"
                    elif "arch" in content or "manjaro" in content:
                        d = "arch"
                    elif "alpine" in content:
                        d = "alpine"
                    elif "debian" in content or "ubuntu" in content:
                        d = "debian"
            except OSError:
                pass
        if d == "fedora":
            return "sudo dnf install aria2"
        if d == "arch":
            return "sudo pacman -S aria2"
        if d == "alpine":
            return "apk add aria2"
        return "sudo apt install aria2"
    if sys_name == "Darwin":
        return "brew install aria2"
    if sys_name == "Windows":
        return "winget install aria2"
    return "install aria2 via your system package manager"


def sanitize_filename(name: str) -> str:
    """
    Sanitizes untrusted filenames and subdirectories.
    - NFKC Unicode normalization.
    - Strips directory traversal tokens (..).
    - Strips null bytes and control characters.
    - Replaces path separators and reserved characters with underscores.
    - Strips leading dashes (-) to prevent CLI option injection.
    - Strips leading and trailing dots and spaces.
    - Defaults to 'f2m_download' if empty.
    """
    if not name:
        return "f2m_download"

    # 1. Unicode normalization
    name = unicodedata.normalize("NFKC", name)

    # 2. Strip null bytes and control characters
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)

    # 3. Strip directory traversal sequences
    while ".." in name:
        name = name.replace("..", "")

    # 4. Replace separators and invalid characters
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)

    # 5. Compress multiple underscores
    name = re.sub(r"_+", "_", name)

    # 6. Strip leading and trailing dashes (prevent option injection), dots, underscores, and whitespace
    name = name.strip(" .-_")

    # 7. Fallback if empty
    return name or "f2m_download"


def assert_path_contained(target_path: Path, base_dir: Path) -> None:
    """
    Validates that target_path strictly resides within base_dir.
    Raises F2MDownloadError if the path escapes.
    Compatible with Python 3.8+ (Path.is_relative_to was added in 3.9).
    """
    try:
        resolved_target = target_path.resolve()
        resolved_base = base_dir.resolve()
        try:
            if hasattr(resolved_target, "is_relative_to"):
                is_contained = resolved_target.is_relative_to(resolved_base)
            else:
                resolved_target.relative_to(resolved_base)
                is_contained = True
        except ValueError:
            is_contained = False

        if not is_contained:
            raise F2MDownloadError(
                f"Security violation: path traversal detected for '{target_path}' outside '{base_dir}'"
            )
    except (ValueError, RuntimeError) as exc:
        raise F2MDownloadError(
            f"Security violation: path traversal validation failed for '{target_path}': {exc}"
        ) from exc


def resolve_destination(raw_dir: str, subdir: str | None = None) -> Path:
    """
    Resolves canonical download path and validates write permissions.
    - Expands ~ to user home.
    - Canonicalizes via Path.resolve().
    - Validates write permissions via os.access(W_OK).
    - If non-existent, verifies nearest ancestor write permission before mkdir.
    - Sanitizes optional subdir.
    """
    expanded = os.path.expanduser(raw_dir)
    base_dir = Path(expanded).resolve()

    if subdir:
        clean_subdir = sanitize_filename(subdir)
        target_dir = (base_dir / clean_subdir).resolve()
    else:
        target_dir = base_dir

    if target_dir.exists():
        if not target_dir.is_dir():
            raise F2MDownloadError(f"Destination path '{target_dir}' exists and is not a directory")
        if not os.access(target_dir, os.W_OK):
            raise F2MDownloadError(f"Destination directory '{target_dir}' is not writable")
    else:
        # Check nearest existing parent directory
        curr = target_dir.parent
        while not curr.exists() and curr != curr.parent:
            curr = curr.parent

        if not os.access(curr, os.W_OK):
            raise F2MDownloadError(
                f"Destination directory '{target_dir}' cannot be created (parent '{curr}' is not writable)"
            )
        try:
            target_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        except OSError as exc:
            raise F2MDownloadError(f"Failed to create destination directory '{target_dir}': {exc}") from exc

    return target_dir


def export_links(urls: list[str], destination_dir: Path, filename_hint: str) -> Path:
    """
    Writes links cleanly to <destination_dir>/<sanitized_hint>.txt.
    Optionally copies to clipboard on Windows if clip is available.
    """
    sanitized_hint = sanitize_filename(filename_hint)
    out_file = destination_dir / f"{sanitized_hint}.txt"
    assert_path_contained(out_file, destination_dir)

    try:
        out_file.write_text("\n".join(urls) + "\n", encoding="utf-8")
    except OSError as exc:
        raise F2MDownloadError(f"Failed to write links file '{out_file}': {exc}") from exc

    if os.name == "nt" and shutil.which("clip"):
        try:
            subprocess.run(
                ["clip"],
                input="\n".join(urls).encode("utf-16-le"),
                check=False,
            )
        except OSError:
            pass

    return out_file


def execute_download(request: DownloadRequest) -> DownloadResult:
    """
    Executes download job using available backend without privilege escalation.
    - Zero shell=True calls.
    - aria2c: Runs with --file-allocation=none, -d <dir>, --all-proxy (if proxy set).
    - curl: Downloads each URL to <dest>/<file>.part.
            Atomically replaces <dest>/<file> upon exit code 0.
            Cleans up <dest>/<file>.part upon failure or interruption.
    - Handles KeyboardInterrupt cleanly.
    """
    backend, exe = find_downloader()
    if backend == DownloaderBackend.NONE or not exe:
        return DownloadResult(
            success=False,
            backend=DownloaderBackend.NONE,
            exit_code=1,
            destination_dir=request.destination_dir,
            error_message="Neither aria2c nor curl is installed",
        )

    if backend == DownloaderBackend.ARIA2C:
        cmd = [
            exe,
            "-x", str(request.max_connections),
            "-s", str(request.max_connections),
            "-j", str(request.max_concurrent_downloads),
            "--file-allocation=none",
            "--console-log-level=warn",
            "--summary-interval=0",
            "--download-result=hide",
            "-d", str(request.destination_dir),
        ] + request.urls
        if request.proxy and request.proxy.strip():
            cmd.append(f"--all-proxy={request.proxy.strip()}")

        try:
            proc = subprocess.run(cmd)
            return DownloadResult(
                success=proc.returncode == 0,
                backend=backend,
                exit_code=proc.returncode,
                destination_dir=request.destination_dir,
                error_message=f"aria2c exited with code {proc.returncode}" if proc.returncode != 0 else None,
            )
        except KeyboardInterrupt:
            raise

    # CURL fallback
    downloaded: list[Path] = []
    for u in request.urls:
        raw_name = urlparse.unquote(u.rsplit("/", 1)[-1])
        safe_name = sanitize_filename(raw_name)
        target_path = request.destination_dir / safe_name
        assert_path_contained(target_path, request.destination_dir)

        part_path = request.destination_dir / f"{safe_name}.part"
        cmd = [exe, "-L", "--fail", "-o", str(part_path), u]
        if request.proxy and request.proxy.strip():
            cmd.extend(["--proxy", request.proxy.strip()])

        try:
            proc = subprocess.run(cmd)
            if proc.returncode == 0 and part_path.exists():
                os.replace(part_path, target_path)
                downloaded.append(target_path)
            else:
                part_path.unlink(missing_ok=True)
                return DownloadResult(
                    success=False,
                    backend=backend,
                    exit_code=proc.returncode,
                    destination_dir=request.destination_dir,
                    downloaded_files=downloaded,
                    error_message=f"curl exited with code {proc.returncode}",
                )
        except KeyboardInterrupt:
            part_path.unlink(missing_ok=True)
            raise
        except Exception as exc:
            part_path.unlink(missing_ok=True)
            raise F2MDownloadError(f"curl transfer failed: {exc}") from exc

    return DownloadResult(
        success=True,
        backend=backend,
        exit_code=0,
        destination_dir=request.destination_dir,
        downloaded_files=downloaded,
    )


def find_player(choice: str = "auto") -> tuple[str | None, str]:
    """
    Finds available media player on $PATH or standard locations.
    """
    candidates = ["mpv", "vlc", "potplayer"] if choice == "auto" else [choice]
    for name in candidates:
        if name == "mpv":
            exe = shutil.which("mpv") or shutil.which("mpv.exe")
            if exe:
                return exe, "mpv"
        elif name == "vlc":
            exe = shutil.which("vlc") or shutil.which("vlc.exe")
            for path in (
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            ):
                if not exe and os.path.exists(path):
                    exe = path
            if exe:
                return exe, "vlc"
        elif name == "potplayer":
            for path in (
                r"C:\Program Files\PotPlayer\PotPlayerMini64.exe",
                r"C:\Program Files (x86)\PotPlayer\PotPlayerMini64.exe",
                r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
                r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini64.exe",
            ):
                if os.path.exists(path):
                    return path, "potplayer"
    return None, choice


def execute_stream(request: StreamRequest) -> StreamResult:
    """
    Spawns media player (mpv/vlc/potplayer) using subprocess.Popen.
    - Zero shell=True calls.
    - stdout and stderr redirected to subprocess.DEVNULL.
    """
    exe, name = find_player(request.player.lower())
    if not exe:
        return StreamResult(
            success=False,
            player_name=request.player,
            error_message=f"Player '{request.player}' not found",
        )

    urls = request.urls if isinstance(request.urls, list) else [request.urls]
    proxy = (request.proxy or "").strip()

    if name == "mpv":
        cmd = [exe, f"--force-media-title={request.title}", "--keep-open=no"]
        if proxy:
            cmd.append(f"--http-proxy={proxy}")
        cmd.extend(urls)
    elif name == "vlc":
        cmd = [exe]
        if proxy:
            cmd.append(f"--http-proxy={proxy}")
        cmd.extend(urls)
    else:  # potplayer
        cmd = [exe] + urls

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return StreamResult(success=True, player_name=name, pid=proc.pid)
    except OSError as exc:
        return StreamResult(
            success=False,
            player_name=name,
            error_message=f"Failed to launch player '{name}': {exc}",
        )
