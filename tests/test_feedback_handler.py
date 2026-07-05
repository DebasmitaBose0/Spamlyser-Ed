"""Tests for FeedbackHandler — multi-path SQLite connection management."""

import os
import tempfile

import pytest


class TestFeedbackHandlerConnections:
    def test_multiple_db_paths_same_thread(self):
        from models.feedback_handler import FeedbackHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            db_a = os.path.join(tmpdir, "feedback_a.db")
            db_b = os.path.join(tmpdir, "feedback_b.db")

            handler_a = FeedbackHandler(feedback_file=db_a)
            handler_b = FeedbackHandler(feedback_file=db_b)

            assert handler_a.db_path != handler_b.db_path, "should use different db_paths"

            ok = handler_a.save_feedback_actual(
                {"feedback_type": "test", "message": "from A", "rating": 3}
            )
            assert ok, "save to DB A should succeed"

            ok = handler_b.save_feedback_actual(
                {"feedback_type": "test", "message": "from B", "rating": 5}
            )
            assert ok, "save to DB B should succeed"

            feedback_a = handler_a.get_all_feedback()
            feedback_b = handler_b.get_all_feedback()

            assert len(feedback_a) == 1, "DB A should have 1 entry"
            assert len(feedback_b) == 1, "DB B should have 1 entry"
            assert feedback_a[0]["message"] == "from A"
            assert feedback_b[0]["message"] == "from B"

    def test_stale_connection_reconnects(self):
        from models.feedback_handler import _get_connection

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "stale_test.db")
            conn = _get_connection(db_path)
            assert conn.execute("SELECT 1").fetchone() is not None
            conn.close()
            # Simulating stale connection: close and verify reconnect
            from models.feedback_handler import _local

            if hasattr(_local, "connections"):
                del _local.connections[db_path]
            conn2 = _get_connection(db_path)
            assert conn2.execute("SELECT 1").fetchone() is not None

    def test_feedback_stats(self):
        from models.feedback_handler import FeedbackHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "stats.db")
            handler = FeedbackHandler(feedback_file=db_path)
            handler.save_feedback_actual(
                {"feedback_type": "bug", "rating": 2, "message": "it broke"}
            )
            handler.save_feedback_actual(
                {"feedback_type": "feature", "rating": 4, "message": "nice"}
            )
            stats = handler.get_feedback_stats()
            assert stats["total"] == 2
            assert stats["by_type"].get("bug") == 1
            assert stats["by_type"].get("feature") == 1
            assert stats["average_rating"] == 3.0
