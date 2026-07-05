"""Analytics data export — download classification history in multiple formats."""

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_to_csv(records: list[dict[str, Any]]) -> str:
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = _normalise_fieldnames(records)
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in records:
        cleaned = _flatten_row(row, fieldnames)
        writer.writerow(cleaned)
    return output.getvalue()


def export_to_json(records: list[dict[str, Any]], indent: int = 2) -> str:
    def _serialise(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    return json.dumps(records, indent=indent, default=_serialise, ensure_ascii=False)


def export_to_html(records: list[dict[str, Any]]) -> str:
    if not records:
        return "<p>No data</p>"

    fieldnames = _normalise_fieldnames(records)
    rows_html = ""
    for row in records:
        cleaned = _flatten_row(row, fieldnames)
        cells = "".join(f"<td>{html_escape(str(cleaned.get(f, '')))}</td>" for f in fieldnames)
        rows_html += f"<tr>{cells}</tr>\n"

    header_html = "".join(f"<th>{html_escape(f)}</th>" for f in fieldnames)
    return f"""<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:sans-serif;font-size:13px;">
<thead style="background:#f0f0f0;"><tr>{header_html}</tr></thead>
<tbody>{rows_html}</tbody>
</table>"""


def export_report_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    spam_count = sum(
        1
        for r in records
        if r.get("label", "").upper() == "SPAM"
        or r.get("prediction", "").upper() == "SPAM"
    )
    ham_count = total - spam_count
    avg_confidence = _safe_mean(
        [r.get("confidence", 0) or 0 for r in records if r.get("confidence") is not None]
    )

    return {
        "total_classified": total,
        "spam_count": spam_count,
        "ham_count": ham_count,
        "spam_percentage": round(spam_count / total * 100, 1) if total else 0.0,
        "ham_percentage": round(ham_count / total * 100, 1) if total else 0.0,
        "average_confidence": round(avg_confidence, 4),
        "exported_at": datetime.now().isoformat(),
        "source": "Spamlyser Pro",
    }


SUPPORTED_FORMATS = {
    "csv": ("text/csv", ".csv", export_to_csv),
    "json": ("application/json", ".json", export_to_json),
    "html": ("text/html", ".html", export_to_html),
}


def _normalise_fieldnames(records: list[dict]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for r in records:
        for k in r:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
    return ordered


def _flatten_row(row: dict, fieldnames: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for f in fieldnames:
        val = row.get(f, "")
        if isinstance(val, (dict, list)):
            val = json.dumps(val, ensure_ascii=False, default=str)
        elif isinstance(val, datetime):
            val = val.isoformat()
        else:
            val = str(val) if val is not None else ""
        result[f] = val
    return result


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
