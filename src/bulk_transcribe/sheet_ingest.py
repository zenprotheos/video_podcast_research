import csv
import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import openpyxl


@dataclass
class ParsedSheet:
    columns: List[str]
    rows: List[Dict[str, str]]

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass
class ColumnMapping:
    source_type: str
    youtube_url: str
    mp3_url: str
    title: str
    description: str
    episode_url: str


def _clean_header(h: str) -> str:
    return (h or "").strip()


def _read_csv_tsv(filename: str, data: bytes) -> ParsedSheet:
    text = data.decode("utf-8", errors="replace")
    # Heuristic: TSV if filename ends with .tsv, else CSV
    delimiter = "\t" if filename.lower().endswith(".tsv") else ","
    f = io.StringIO(text)
    reader = csv.DictReader(f, delimiter=delimiter)
    if reader.fieldnames is None:
        raise ValueError("No header row found")
    columns = [_clean_header(c) for c in reader.fieldnames if _clean_header(c)]
    rows: List[Dict[str, str]] = []
    for r in reader:
        row: Dict[str, str] = {}
        for c in columns:
            v = r.get(c, "")
            row[c] = "" if v is None else str(v)
        rows.append(row)
    return ParsedSheet(columns=columns, rows=rows)


def _read_xlsx(data: bytes) -> ParsedSheet:
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb.active
    values = ws.iter_rows(values_only=True)
    try:
        header_row = next(values)
    except StopIteration:
        raise ValueError("XLSX has no rows")
    columns = [_clean_header(str(c) if c is not None else "") for c in header_row]
    columns = [c for c in columns if c]
    if not columns:
        raise ValueError("XLSX header row is empty")

    rows: List[Dict[str, str]] = []
    for row_values in values:
        row_dict: Dict[str, str] = {}
        for idx, col in enumerate(columns):
            v = row_values[idx] if idx < len(row_values) else ""
            row_dict[col] = "" if v is None else str(v)
        # Skip completely empty rows
        if any((row_dict.get(c, "").strip() for c in columns)):
            rows.append(row_dict)
    return ParsedSheet(columns=columns, rows=rows)


def parse_spreadsheet(filename: str, data: bytes) -> ParsedSheet:
    """
    Parse spreadsheet (CSV/TSV/XLSX) or simple URL list (.txt with one URL per line).
    For .txt files, auto-converts to a CSV-like format with source_type='youtube' and youtube_url.
    """
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        return _read_xlsx(data)
    if lower.endswith(".csv") or lower.endswith(".tsv"):
        return _read_csv_tsv(filename, data)
    if lower.endswith(".txt"):
        return _read_url_list(data)
    raise ValueError("Unsupported file type (expected .csv, .tsv, .xlsx, or .txt)")


def _read_url_list(data: bytes) -> ParsedSheet:
    """
    Parse a simple text file with one URL per line (blank lines ignored).
    Auto-converts to CSV format with source_type='youtube' and youtube_url columns.
    """
    text = data.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    
    # Filter out blank lines and non-URL lines (heuristic: contains youtube.com or youtu.be)
    urls = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Simple heuristic: if it looks like a YouTube URL, use it
        if "youtube.com" in line or "youtu.be" in line:
            urls.append(line)
    
    if not urls:
        raise ValueError("No YouTube URLs found in .txt file")
    
    # Convert to CSV-like format
    columns = ["source_type", "youtube_url"]
    rows: List[Dict[str, str]] = []
    for url in urls:
        rows.append({"source_type": "youtube", "youtube_url": url})
    
    return ParsedSheet(columns=columns, rows=rows)


def resolve_column_mapping(columns: Sequence[str]) -> ColumnMapping:
    """
    Best-effort defaults; UI will allow user overrides.
    """
    cols_lower = {c.lower(): c for c in columns}

    def pick(*candidates: str, default: str = "") -> str:
        for cand in candidates:
            if cand.lower() in cols_lower:
                return cols_lower[cand.lower()]
        return default or (columns[0] if columns else "")

    none_value = "(none)"
    return ColumnMapping(
        source_type=pick("source_type", "type", "source"),
        youtube_url=pick("youtube_url", "youtube", "url", default=none_value),
        mp3_url=pick("mp3_url", "audio_url", "mp3", default=none_value),
        title=pick("title", default=none_value),
        description=pick("description", "desc", default=none_value),
        episode_url=pick("episode_url", "episode", "page_url", default=none_value),
    )


def _get(row: Dict[str, str], col: str) -> str:
    if not col or col == "(none)":
        return ""
    return (row.get(col) or "").strip()


def normalize_rows(parsed: ParsedSheet, mapping: ColumnMapping) -> List[Dict[str, str]]:
    """
    Returns a list of normalized rows with stable keys used by pipelines.
    """
    out: List[Dict[str, str]] = []
    for idx, row in enumerate(parsed.rows):
        source_type = _get(row, mapping.source_type).lower()
        normalized = {
            "_row_index": str(idx + 1),
            "source_type": source_type,
            "youtube_url": _get(row, mapping.youtube_url),
            "mp3_url": _get(row, mapping.mp3_url),
            "title": _get(row, mapping.title),
            "description": _get(row, mapping.description),
            "episode_url": _get(row, mapping.episode_url),
        }
        out.append(normalized)
    return out


def validate_normalized_rows(rows: List[Dict[str, str]]) -> Tuple[List[str], Dict[str, int]]:
    """
    Returns (errors, counts).
    - errors: human-readable error messages (MVP-level)
    - counts: simple metrics for UI
    """
    errors: List[str] = []
    counts = {"total": 0, "youtube": 0, "podcast": 0, "invalid": 0}

    for r in rows:
        counts["total"] += 1
        stype = (r.get("source_type") or "").strip().lower()
        if stype == "youtube":
            counts["youtube"] += 1
            if not (r.get("youtube_url") or "").strip():
                errors.append(f"Row {r.get('_row_index')}: source_type=youtube but youtube_url is blank")
                counts["invalid"] += 1
        elif stype == "podcast":
            counts["podcast"] += 1
            if not (r.get("mp3_url") or "").strip():
                errors.append(f"Row {r.get('_row_index')}: source_type=podcast but mp3_url is blank")
                counts["invalid"] += 1
        else:
            errors.append(f"Row {r.get('_row_index')}: source_type must be 'youtube' or 'podcast' (got '{stype or ''}')")
            counts["invalid"] += 1

    if counts["youtube"] == 0 and counts["podcast"] == 0:
        errors.append("No valid rows found: source_type must be 'youtube' or 'podcast'.")

    return errors, counts

