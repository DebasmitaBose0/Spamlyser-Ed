#!/bin/bash
set -e

echo "=== Spamlyser Docker Entrypoint ==="

mkdir -p /app/data /root/.cache/huggingface

if [ "$SPAMLYSER_DOWNLOAD_MODELS" = "true" ]; then
    echo "Pre-downloading transformer models..."
    python -c "
from transformers import AutoTokenizer, AutoModelForSequenceClassification
models = ['distilbert-base-uncased', 'bert-base-uncased']
for m in models:
    try:
        AutoTokenizer.from_pretrained(m)
        AutoModelForSequenceClassification.from_pretrained(m)
        print(f'Downloaded {m}')
    except Exception as e:
        print(f'Failed to download {m}: {e}')
"
fi

echo "Starting Streamlit app..."
exec streamlit run app.py \
    --server.port="${PORT:-8501}" \
    --server.address="0.0.0.0" \
    --server.maxUploadSize="${MAX_UPLOAD_SIZE:-10}" \
    --browser.gatherUsageStats=false
