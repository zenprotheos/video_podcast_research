import os
import re
from typing import Optional


_SAFE_CHARS_RE = re.compile(r"[^a-zA-Z0-9._-]+")


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

