"""
Batch Exporter Module for Spamlyser
Provides utilities to bundle message analysis results into structured JSON/CSV ZIP archives.
"""

import io
import json
import zipfile
import pandas as pd
from typing import List, Dict, Any


class BatchExporter:
    """Exports prediction results into JSON, CSV, or ZIP packages."""

    @staticmethod
    def export_to_json(results: List[Dict[str, Any]]) -> str:
        """Serializes results list to a formatted JSON string."""
        return json.dumps(results, indent=2, ensure_ascii=False)

    @staticmethod
    def export_to_csv(results: List[Dict[str, Any]]) -> str:
        """Converts results list to CSV string."""
        if not results:
            return ""
        df = pd.DataFrame(results)
        return df.to_csv(index=False)

    @staticmethod
    def create_zip_archive(results: List[Dict[str, Any]]) -> bytes:
        """Creates a ZIP archive containing both JSON and CSV versions of the results."""
        json_data = BatchExporter.export_to_json(results)
        csv_data = BatchExporter.export_to_csv(results)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("batch_results.json", json_data.encode("utf-8"))
            zf.writestr("batch_results.csv", csv_data.encode("utf-8"))
        buffer.seek(0)
        return buffer.getvalue()
