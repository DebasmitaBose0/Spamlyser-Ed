# Spamlyser Pro Architecture

## System Overview

Spamlyser Pro is a Streamlit-based web application that uses an ensemble of
4 transformer models (DistilBERT, BERT, RoBERTa, ALBERT) to classify SMS
messages as SPAM or HAM, with multi-class threat categorization.

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│  ┌──────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ Home │ │ Analyzer │ │Analytics │ │  Settings/Help  │ │
│  └──────┘ └──────────┘ └──────────┘ └────────────────┘ │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                Page Router (app.py)                      │
│    Routes navigation events to page rendering functions  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              Models Package (models/)                    │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────────────┐     │
│  │  Ensemble         │  │  Threat Analysis         │     │
│  │  Classifier       │  │  - Word Analyzer         │     │
│  │  - DistilBERT     │  │  - Threat Categorizer    │     │
│  │  - BERT           │  │  - Encoding Analyzer     │     │
│  │  - RoBERTa        │  │  - Language Detector     │     │
│  │  - ALBERT         │  └──────────────────────────┘     │
│  └──────────────────┘                                    │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────────────┐     │
│  │  Persistence     │  │  Integration              │     │
│  │  - StorageManager│  │  - Webhook Notifier       │     │
│  │  - SenderRep     │  │  - Intel Exporter         │     │
│  │  - Feedback      │  │  - Report Encryptor       │     │
│  │  - Benchmark     │  │  - Error Boundary         │     │
│  └──────────────────┘  └──────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **User Input**: SMS message entered in Analyzer page
2. **Sanitization**: HTML stripped, text validated
3. **Feature Extraction**: Word analysis, threat patterns, language detection
4. **Ensemble Prediction**: All 4 models classify, weighted voting
5. **Post-processing**: Label normalization, confidence calibration
6. **Result Display**: Classification, threat type, explanations
7. **Side Effects**: Sender reputation updated, webhook notifications sent, feedback stored

## Key Design Decisions

- **Ensemble approach**: Weighted 0.20/0.30/0.30/0.20 across models
- **Thread safety**: RLock for webhooks, Lock for sender reputation
- **Atomic writes**: StorageManager uses temp file + rename pattern
- **Async notifications**: Webhooks fire in daemon threads
- **Circuit breaker**: Automatic disable after 5 consecutive webhook failures
- **Auto-flush**: Sender reputation persists every 60 seconds
