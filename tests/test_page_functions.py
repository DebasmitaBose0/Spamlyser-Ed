"""Tests for page_functions module — navigation and feedback page behaviour."""

from unittest.mock import MagicMock, patch

import pytest


class TestShowFeedbackPage:
    """Verify that show_feedback_page handles missing navigate_to gracefully."""

    def test_no_argument_does_not_crash(self):
        from page_functions import show_feedback_page

        with patch("page_functions.st") as mock_st:
            mock_st.session_state = {"feedback_submitted": False, "feedback_rating": 3}
            mock_st.button.return_value = False
            mock_st.form.return_value.__enter__ = MagicMock()
            mock_st.form.return_value.__exit__ = MagicMock()
            try:
                show_feedback_page()
            except Exception as exc:
                pytest.fail(f"show_feedback_page() raised {exc}")

    def test_explicit_navigate_to_passed(self):
        from page_functions import show_feedback_page

        tracker = {"called": False, "page": None}

        def mock_navigate(page):
            tracker["called"] = True
            tracker["page"] = page

        with patch("page_functions.st") as mock_st:
            mock_st.session_state = {"feedback_submitted": False, "feedback_rating": 3}
            mock_st.button.return_value = True
            mock_st.form.return_value.__enter__ = MagicMock()
            mock_st.form.return_value.__exit__ = MagicMock()
            try:
                show_feedback_page(navigate_to=mock_navigate)
            except Exception as exc:
                pytest.fail(f"show_feedback_page(navigate_to=...) raised {exc}")


class TestImportNavigateTo:
    def test_fallback_returns_callable(self):
        from page_functions import _import_navigate_to

        fn = _import_navigate_to()
        assert callable(fn)
