import os
import pytest
from models.drift_tracker import ModelDriftTracker

def test_drift_tracker_empty_history(tmp_path):
    history_file = os.path.join(tmp_path, "drift_history.json")
    tracker = ModelDriftTracker(baseline_accuracy=0.95, history_file=history_file)
    assert tracker.history == []

def test_drift_calculation():
    tracker = ModelDriftTracker(baseline_accuracy=0.95)
    assert tracker.calculate_drift(0.90) == 0.05
    assert tracker.calculate_drift(0.98) == 0.0

def test_kl_divergence():
    tracker = ModelDriftTracker()
    p = [0.8, 0.2]
    q = [0.75, 0.25]
    # KL-Divergence should be small and positive
    kl = tracker.calculate_kl_divergence(p, q)
    assert kl > 0.0

def test_psi_calculation():
    tracker = ModelDriftTracker()
    baseline = [0.9, 0.1]
    actual = [0.85, 0.15]
    psi = tracker.calculate_psi(baseline, actual)
    assert psi >= 0.0

def test_record_evaluation(tmp_path):
    history_file = os.path.join(tmp_path, "drift_history.json")
    tracker = ModelDriftTracker(baseline_accuracy=0.95, history_file=history_file)
    
    baseline_dist = [0.9, 0.1]
    actual_dist = [0.7, 0.3]
    
    entry = tracker.record_evaluation(0.88, actual_dist, baseline_dist)
    assert entry["accuracy"] == 0.88
    assert entry["status"] in ["Stable", "Warning", "Action Required"]
    assert len(tracker.history) == 1
    assert os.path.exists(history_file)
