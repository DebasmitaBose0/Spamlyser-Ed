"""Threat intelligence export system for Spamlyser Pro.

Generates structured threat intelligence reports in STIX 2.1 format
and CSV/JSON formats for sharing with security teams and SIEM systems.
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def build_stix_observation(
    message: str,
    confidence: float,
    threat_type: str,
    sender: str | None = None,
    source: str = "Spamlyser Pro",
) -> dict[str, Any]:
    """Build a STIX 2.1 Observation object from an SMS classification."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    obs_id = f"observed-data--{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"

    return {
        "type": "observed-data",
        "id": obs_id,
        "created": timestamp,
        "modified": timestamp,
        "first_observed": timestamp,
        "last_observed": timestamp,
        "number_observed": 1,
        "objects": {
            "0": {
                "type": "message",
                "content": message[:500],
                "content_ref": "message--sms",
            },
            "1": {
                "type": "x-spam-classification",
                "threat_type": threat_type,
                "confidence": confidence,
                "source": source,
            },
        },
        "x_spamlyser_metadata": {
            "sender": sender,
            "message_length": len(message),
            "threat_type": threat_type,
            "confidence_score": confidence,
        },
    }


def build_stix_indicator(
    threat_type: str,
    confidence: float,
    indicator_pattern: str,
    description: str = "",
) -> dict[str, Any]:
    """Build a STIX 2.1 Indicator object."""
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    ind_id = f"indicator--{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"

    return {
        "type": "indicator",
        "id": ind_id,
        "created": timestamp,
        "modified": timestamp,
        "name": f"SMS {threat_type} Indicator",
        "description": description or f"Detected {threat_type} pattern in SMS message",
        "indicator_types": ["malicious-activity"],
        "pattern": indicator_pattern,
        "pattern_type": "stix",
        "valid_from": timestamp,
        "confidence": int(confidence * 100),
    }


def export_as_stix_bundle(
    records: list[dict[str, Any]],
) -> str:
    """Export a list of classification records as a STIX 2.1 bundle."""
    objects: list[dict[str, Any]] = []
    for record in records:
        obs = build_stix_observation(
            message=record.get("message", ""),
            confidence=record.get("confidence", 0.0),
            threat_type=record.get("threat_type", "unknown"),
            sender=record.get("sender"),
        )
        objects.append(obs)

        indicator_pattern = f"[x-spam-classification:threat_type = '{record.get('threat_type', 'unknown')}']"
        ind = build_stix_indicator(
            threat_type=record.get("threat_type", "unknown"),
            confidence=record.get("confidence", 0.0),
            indicator_pattern=indicator_pattern,
            description=f"SMS classified as {record.get('threat_type', 'unknown')} with {record.get('confidence', 0):.0%} confidence",
        )
        objects.append(ind)

    bundle = {
        "type": "bundle",
        "id": f"bundle--{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        "objects": objects,
    }
    return json.dumps(bundle, indent=2, default=str)


def export_as_csv(
    records: list[dict[str, Any]],
) -> str:
    """Export records as CSV for SIEM ingestion."""
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = [
        "timestamp",
        "sender",
        "message_snippet",
        "label",
        "confidence",
        "threat_type",
        "model_used",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for record in records:
        row = {
            "timestamp": record.get("timestamp", ""),
            "sender": record.get("sender", ""),
            "message_snippet": record.get("message", "")[:100],
            "label": record.get("label", ""),
            "confidence": record.get("confidence", 0.0),
            "threat_type": record.get("threat_type", ""),
            "model_used": record.get("model_used", "ensemble"),
        }
        writer.writerow(row)

    return output.getvalue()


def export_as_json_report(
    records: list[dict[str, Any]],
    include_stats: bool = True,
) -> str:
    """Export records as a structured JSON threat report."""
    report: dict[str, Any] = {
        "report_metadata": {
            "generator": "Spamlyser Pro",
            "generated_at": datetime.now(UTC).isoformat(),
            "format_version": "1.0",
            "record_count": len(records),
        },
        "records": records,
    }

    if include_stats and records:
        total = len(records)
        spam_count = sum(1 for r in records if r.get("label") == "SPAM")
        threat_counts: dict[str, int] = {}
        for r in records:
            tt = r.get("threat_type", "unknown")
            threat_counts[tt] = threat_counts.get(tt, 0) + 1

        report["statistics"] = {
            "total_classifications": total,
            "spam_count": spam_count,
            "ham_count": total - spam_count,
            "spam_ratio": round(spam_count / total, 3) if total > 0 else 0,
            "threat_type_breakdown": threat_counts,
        }

    return json.dumps(report, indent=2, default=str)
