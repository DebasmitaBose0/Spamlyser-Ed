"""Tests for calibration module — graceful fallback when scipy is absent."""

import pytest

from models.calibration import SCIPY_AVAILABLE, ConfidenceCalibrator


class TestCalibratorScipyFallback:
    def test_scipy_flag_defined(self):
        assert isinstance(SCIPY_AVAILABLE, bool)

    def test_fit_temperature_returns_default_without_scipy(self):
        calibrator = ConfidenceCalibrator()
        import numpy as np

        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([0.9, 0.2, 0.8, 0.3])
        temp = calibrator.fit_temperature(y_true, y_prob)
        assert temp > 0

    def test_fit_platt_returns_default_without_scipy(self):
        calibrator = ConfidenceCalibrator()
        import numpy as np

        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([0.9, 0.2, 0.8, 0.3])
        a, b = calibrator.fit_platt(y_true, y_prob)
        assert a == 1.0
        assert b == 0.0

    def test_calibrate_probability_temperature(self):
        calibrator = ConfidenceCalibrator(temperature=1.5)
        prob = calibrator.calibrate_probability(0.8, method="temperature")
        assert 0.0 <= prob <= 1.0

    def test_calibrate_probability_platt(self):
        calibrator = ConfidenceCalibrator(platt_a=1.2, platt_b=0.1)
        prob = calibrator.calibrate_probability(0.8, method="platt")
        assert 0.0 <= prob <= 1.0

    def test_expected_calibration_error(self):
        calibrator = ConfidenceCalibrator()
        import numpy as np

        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([0.9, 0.2, 0.8, 0.3])
        ece = calibrator.expected_calibration_error(y_true, y_prob)
        assert 0.0 <= ece <= 1.0
