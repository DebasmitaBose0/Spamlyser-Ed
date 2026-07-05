"""Tests for model_init — verifying cache detection and model availability checks."""

import pytest


class TestModelCacheDetection:
    def test_cache_pattern_matches_huggingface_structure(self):
        from models.model_init import verify_model_availability

        # The function should not crash; result is environment-dependent
        result = verify_model_availability()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_model_status_info_structure(self):
        from models.model_init import get_model_status_info

        info = get_model_status_info()
        assert "available" in info
        assert "error_message" in info
        assert "warnings" in info

    def test_display_status_ui_does_not_crash(self):
        from models.model_init import display_model_status_ui

        try:
            display_model_status_ui()
        except Exception as exc:
            pytest.fail(f"display_model_status_ui raised {exc}")
