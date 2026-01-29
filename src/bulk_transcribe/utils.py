import os
import re
from typing import Optional

_SAFE_CHARS_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def try_copy_via_pyperclip(text: str) -> bool:
    """
    Copy text to the system clipboard using pyperclip (server-side).
    Returns True if copy succeeded, False otherwise (e.g. headless or unavailable).
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def slugify(value: str, max_len: int = 80) -> str:
    """
    Windows-safe filename slug.
    """
    v = (value or "").strip()
    if not v:
        return "untitled"
    v = v.replace(" ", "_")
    v = _SAFE_CHARS_RE.sub("_", v)
    v = re.sub(r"_+", "_", v).strip("._-")
    if not v:
        v = "untitled"
    return v[:max_len]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def safe_join(*parts: str) -> str:
    return os.path.join(*parts)

