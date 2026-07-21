import time
from models.latency_profiler import LatencyProfiler


def test_latency_profiler_execution():
    profiler = LatencyProfiler()

    def dummy_classifier(text: str):
        time.sleep(0.01)
        return "SPAM"

    res = profiler.profile_call("distilbert", dummy_classifier, "Free money now!")
    assert res["result"] == "SPAM"
    assert res["metrics"]["latency_ms"] >= 9.0
    assert profiler.get_summary()["count"] == 1


def test_latency_profiler_summary():
    profiler = LatencyProfiler()
    summary = profiler.get_summary()
    assert summary["count"] == 0
    assert summary["avg_ms"] == 0.0
