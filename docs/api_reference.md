# Spamlyser Pro API Reference

## Overview

Spamlyser Pro provides a programmatic Python API for SMS spam classification,
threat analysis, and model management. All modules are importable from the
`models` package.

---

## Core Classification

### `models.ensemble_classifier_method.EnsembleSpamClassifier`

The main classifier that aggregates predictions from 4 transformer models.

```python
from models.ensemble_classifier_method import EnsembleSpamClassifier, ModelPerformanceTracker

tracker = ModelPerformanceTracker()
classifier = EnsembleSpamClassifier(performance_tracker=tracker)
result = classifier.predict("Your SMS message here")
```

**Returns:** `PredictionResult` with `label`, `score`, and `spam_probability`.

### `models.model_init`

Handles model loading and verification.

```python
from models.model_init import MODEL_STATUS, verify_model, get_model
```

### `models.label_normalizer.normalize_label(raw_label, spam_probability=None)`
Maps raw HuggingFace labels (`LABEL_0`, `LABEL_1`, etc.) to canonical `SPAM`/`HAM`.

---

## Threat Analysis

### `models.threat_analyzer.classify_threat_type(text)`
Classifies SMS text into threat categories: `phishing`, `scam/fraud`, `unwanted_marketing`, `other`.

### `models.threat_analyzer.get_threat_specific_advice(threat_type)`
Returns safety recommendations based on threat category.

### `models.word_analyzer.WordAnalyzer`
Detects spam-indicative words and phrases with leetspeak decoding.

---

## Sender Reputation

### `models.sender_reputation.SenderReputation`
Tracks reputation scores for SMS senders.

```python
sr = SenderReputation()
sr.record_analysis("+1234567890", is_spam=True, confidence=0.95)
rep = sr.get_reputation("+1234567890")
```

---

## Webhook Notifications

### `models.webhook_notifier.WebhookNotifier`
Sends async HTTP notifications with retry and circuit breaker.

```python
notifier = WebhookNotifier()
notifier.add_webhook("https://hooks.example.com/alerts")
notifier.notify_spam_detected("message", 0.95, threat_type="phishing")
```

---

## Storage & Persistence

### `models.storage_manager.StorageManager`
Atomic JSON file operations with automatic backups.

```python
sm = StorageManager()
sm.save_json("data.json", {"key": "value"})
data = sm.load_json("data.json")
```

---

## Benchmarking

### `models.benchmark_automation`
```python
from models.benchmark_automation import run_automated_benchmark
results = run_automated_benchmark(sample_size=10)
```

---

## Threat Intelligence Export

### `models.threat_intel_exporter`
```python
stix = export_as_stix_bundle(records)
csv_data = export_as_csv(records)
json_report = export_as_json_report(records)
```

---

## Encoding Analysis

### `models.encoding_analyzer`
```python
result = analyze_message_complexity("Your SMS text")
encodings = detect_encoding_type(text)
suspicious = detect_suspicious_chars(text)
```
