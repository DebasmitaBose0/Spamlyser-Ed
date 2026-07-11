# Deployment Guide

## Local Development

```bash
# Quick setup
make setup

# Run the app
make run

# Run tests
make test
```

## Docker Deployment

### Prerequisites
- Docker 24+
- Docker Compose v2+

### Build and Run

```bash
# Build and start
docker compose up -d --build

# Check health
docker compose ps
docker compose exec spamlyser python healthcheck.py

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Configuration

Set environment variables in `docker-compose.yml` or via `.env` file:

```yaml
environment:
  - SPAMLYSER_DATA_DIR=/app/data
  - SPAMLYSER_MODEL_CACHE_DIR=/root/.cache/huggingface/transformers
```

### Volumes

- `spamlyser_data`: Persistent data directory (DBs, JSON files)
- `spamlyser_cache`: HuggingFace model cache

### Health Checks

The container includes a built-in health check that verifies:
- Streamlit app is responding on port 8501
- All critical Python imports are available
- Data directory is writable

## Production Considerations

### Resource Requirements
- **Minimum**: 2 CPU cores, 2GB RAM
- **Recommended**: 4 CPU cores, 4GB RAM
- **Disk**: 5GB for models + data

### Security
- Run behind a reverse proxy (Nginx) for TLS termination
- Set `SPAMLYSER_ENABLE_TELEMETRY=false` in production
- Use environment variables for secrets, not hardcoded values
- Enable CSV sanitization (`SPAMLYSER_CSV_SANITIZE_FORMULAS=true`)

### Monitoring
- Streamlit logs to stdout (captured by Docker)
- Health check endpoint at `http://localhost:8501`
- Benchmark dashboard tracks model performance over time
