# ─── Stage 1: Base ───────────────────────────────────────────────
FROM python:3.13-slim AS base

WORKDIR /app

# Install system dependencies needed by PyTorch / sentencepiece
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ─── Stage 2: Dependencies ───────────────────────────────────────
FROM base AS dependencies

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Stage 3: Runtime ────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy only the installed packages from the dependencies stage
COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY app.py config.py page_functions.py ./
COPY assets/ ./assets/
COPY models/ ./models/
COPY pages/ ./pages/
COPY benchmarks/ ./benchmarks/
COPY .streamlit/ ./.streamlit/
COPY healthcheck.py ./

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=3 \
    CMD python healthcheck.py

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
