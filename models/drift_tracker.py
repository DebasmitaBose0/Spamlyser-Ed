import json
import os
import math
from datetime import datetime

class ModelDriftTracker:
    """ModelDriftTracker — Analyzes model performance decay and statistical prediction drift using PSI and KL-Divergence."""

    def __init__(self, baseline_accuracy: float = 0.95, history_file: str = "data/drift_history.json"):
        self.baseline_accuracy = baseline_accuracy
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self) -> list:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def calculate_drift(self, current_accuracy: float) -> float:
        return round(max(0.0, self.baseline_accuracy - current_accuracy), 4)

    def calculate_kl_divergence(self, p: list[float], q: list[float]) -> float:
        """Calculates Kullback-Leibler Divergence D_KL(P || Q) between two distributions."""
        if len(p) != len(q):
            raise ValueError("Distributions must have identical dimensions.")

        epsilon = 1e-10
        kl_div = 0.0
        for pi, qi in zip(p, q):
            pi = max(pi, epsilon)
            qi = max(qi, epsilon)
            kl_div += pi * math.log(pi / qi)
        return round(kl_div, 4)

    def calculate_psi(self, baseline: list[float], actual: list[float]) -> float:
        """Calculates the Population Stability Index (PSI) between baseline and actual distributions."""
        if len(baseline) != len(actual):
            raise ValueError("Distributions must have identical dimensions.")

        epsilon = 1e-10
        psi_value = 0.0
        for b, a in zip(baseline, actual):
            b = max(b, epsilon)
            a = max(a, epsilon)
            psi_value += (a - b) * math.log(a / b)
        return round(psi_value, 4)

    def record_evaluation(self, current_accuracy: float, predictions_distribution: list[float], baseline_distribution: list[float]):
        accuracy_drift = self.calculate_drift(current_accuracy)
        kl_div = self.calculate_kl_divergence(baseline_distribution, predictions_distribution)
        psi = self.calculate_psi(baseline_distribution, predictions_distribution)

        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "accuracy": current_accuracy,
            "accuracy_drift": accuracy_drift,
            "kl_divergence": kl_div,
            "psi": psi,
            "status": "Warning" if psi > 0.1 else ("Action Required" if psi > 0.25 else "Stable")
        }
        self.history.append(entry)
        self.save_history()
        return entry
