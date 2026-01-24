import csv
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SessionConfig:
    output_root: str


@dataclass
class Session:
    session_id: str
    session_dir: str
    youtube_dir: str
    podcasts_dir: str


class SessionManager:
    def __init__(self, cfg: SessionConfig):
        self.cfg = cfg

    def create_session(self) -> Session:
        os.makedirs(self.cfg.output_root, exist_ok=True)
        created_at = datetime.now().isoformat(timespec="seconds")
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.cfg.output_root, session_id)
        youtube_dir = os.path.join(session_dir, "youtube")
        podcasts_dir = os.path.join(session_dir, "podcasts")

        os.makedirs(youtube_dir, exist_ok=True)
        os.makedirs(podcasts_dir, exist_ok=True)

        # optional supporting dirs (created lazily later)
        os.makedirs(os.path.join(podcasts_dir, "audio"), exist_ok=True)

        self.write_manifest(
            session_dir,
            {
                "session_id": session_id,
                "created_at": created_at,
                "items": [],
            },
        )

        return Session(
            session_id=session_id,
            session_dir=session_dir,
            youtube_dir=youtube_dir,
            podcasts_dir=podcasts_dir,
        )

    def manifest_path(self, session_dir: str) -> str:
        return os.path.join(session_dir, "manifest.json")

    def write_manifest(self, session_dir: str, manifest: Dict[str, Any]) -> None:
        p = self.manifest_path(session_dir)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def read_manifest(self, session_dir: str) -> dict:
        """Read the manifest file for a session."""
        p = self.manifest_path(session_dir)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"items": []}

    def write_items_csv(self, session_dir: str, rows: List[Dict[str, str]]) -> str:
        p = os.path.join(session_dir, "items.csv")
        if not rows:
            with open(p, "w", encoding="utf-8") as f:
                f.write("")
            return p
        fieldnames = list(rows[0].keys())
        with open(p, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return p

