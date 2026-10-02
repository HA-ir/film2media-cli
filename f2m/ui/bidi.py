from __future__ import annotations

import re
from rich.cells import cell_len
from rich.markup import escape


def escape_text(text: str | None) -> str:
    """
    Safely escape dynamic strings so bracketed tokens (e.g. [1080p], [Dubbed])
    are not parsed as Rich BBCode markup tags.
    """
    if not text:
        return ""
    return escape(str(text))


def get_cell_width(text: str | None) -> int:
    """
    Calculate visual character cell width accurately, taking into account
    wide characters, Persian scripts, and zero-width non-joiners (\\u200c).
    """
    if not text:
        return 0
    return cell_len(str(text))


def protect_ltr(token: str | None) -> str:
    """
    Ensure machine tokens (URLs, paths, filenames, flags, numbers) remain strictly
    verbatim LTR strings without phantom directional characters or visual distortion.
    """
    if not token:
        return ""
    # Strip any accidental non-printable directional marks
    cleaned = re.sub(r"[‎‏‪-‮]", "", str(token))
    return cleaned
