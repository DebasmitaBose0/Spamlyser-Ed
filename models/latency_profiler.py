"""
Model Latency & Performance Profiler for Spamlyser
Measures inference execution time and latency statistics across spam classification pipelines.
"""

import time
from typing import Callable, Any, Dict, List


class LatencyProfiler:
    """Utility to measure execution latency and track performance benchmarks for models."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def profile_call(self, model_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Executes a function while profiling execution latency in milliseconds."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        record = {
            "model_name": model_name,
            "latency_ms": round(elapsed_ms, 3),
            "timestamp": time.time(),
            "status": "success",
        }
        self.history.append(record)
        return {"result": result, "metrics": record}

    def get_summary(self) -> Dict[str, Any]:
        """Computes summary stats (avg latency, min, max, count) from profile history."""
        if not self.history:
            return {"count": 0, "avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}

        latencies = [r["latency_ms"] for r in self.history]
        return {
            "count": len(latencies),
            "avg_ms": round(sum(latencies) / len(latencies), 3),
            "min_ms": round(min(latencies), 3),
            "max_ms": round(max(latencies), 3),
        }
