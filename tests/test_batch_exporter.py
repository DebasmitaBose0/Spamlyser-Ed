import io
import json
import zipfile
from models.batch_exporter import BatchExporter


def test_batch_exporter_json_and_csv():
    sample_data = [
        {"id": 1, "text": "Free prize!", "prediction": "SPAM", "confidence": 0.98},
        {"id": 2, "text": "Hey dinner tonight?", "prediction": "HAM", "confidence": 0.95},
    ]

    json_str = BatchExporter.export_to_json(sample_data)
    assert "Free prize!" in json_str
    parsed = json.loads(json_str)
    assert len(parsed) == 2

    csv_str = BatchExporter.export_to_csv(sample_data)
    assert "prediction" in csv_str
    assert "SPAM" in csv_str


def test_batch_exporter_zip():
    sample_data = [
        {"id": 1, "text": "Win money", "prediction": "SPAM", "confidence": 0.99}
    ]
    zip_bytes = BatchExporter.create_zip_archive(sample_data)
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        file_names = zf.namelist()
        assert "batch_results.json" in file_names
        assert "batch_results.csv" in file_names
