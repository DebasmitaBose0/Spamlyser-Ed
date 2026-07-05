"""Unit tests for the StorageManager and JSON persistence layer."""

import json
import os
from pathlib import Path

import pytest

from models.storage_manager import StorageManager, default_json_validator


class TestDefaultJsonValidator:
    def test_valid_json(self):
        assert default_json_validator({"key": "value"}) is True
        assert default_json_validator([]) is True
        assert default_json_validator(None) is True

    def test_invalid_nan(self):
        assert default_json_validator(float("nan")) is False


class TestStorageManager:
    def test_save_and_load(self, temp_data_dir, temp_json_file):
        manager = StorageManager(str(temp_json_file))
        data = {"message": "test", "count": 42}
        assert manager.save(data) is True
        loaded = manager.load()
        assert loaded["message"] == "test"
        assert loaded["count"] == 42

    def test_save_with_backup(self, temp_data_dir):
        path = temp_data_dir / "backup_test.json"
        manager = StorageManager(str(path))
        manager.save({"version": 1})
        manager.save({"version": 2})
        backups = list(temp_data_dir.glob("backup_test_*.json"))
        assert len(backups) >= 1, "expected at least one backup file"

    def test_load_missing_file(self, temp_data_dir):
        path = temp_data_dir / "nonexistent.json"
        manager = StorageManager(str(path))
        result = manager.load()
        assert result is None or result == {}

    def test_corrupted_file_recovery(self, temp_data_dir):
        path = temp_data_dir / "corrupt.json"
        path.write_text("not valid json{{{", encoding="utf-8")
        manager = StorageManager(str(path))
        result = manager.load()
        assert result is None or result == {}, "corrupt file should return empty/default"

    def test_atomic_write(self, temp_data_dir):
        path = temp_data_dir / "atomic.json"
        manager = StorageManager(str(path))
        assert manager.save({"atomic": True}) is True
        content = json.loads(path.read_text(encoding="utf-8"))
        assert content["atomic"] is True

    def test_backup_rotation(self, temp_data_dir):
        path = temp_data_dir / "rotate.json"
        manager = StorageManager(str(path), max_backups=2)
        for i in range(5):
            manager.save({"iteration": i})
        backups = sorted(temp_data_dir.glob("rotate_*.json"))
        assert len(backups) <= 2, "backup rotation should keep at most 2 files"
