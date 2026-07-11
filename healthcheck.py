"""Health check script for Docker container orchestration.

Provides a lightweight HTTP-based health check that verifies:
1. The Streamlit application is running and responding
2. Python runtime and critical imports are available
3. The data directory is writable
"""

import json
import os
import sys
import urllib.request


def check_streamlit():
    try:
        resp = urllib.request.urlopen(
            "http://localhost:8501", timeout=5
        )
        return resp.status == 200
    except Exception:
        return False


def check_imports():
    required = [
        "streamlit",
        "numpy",
        "pandas",
        "plotly",
        "torch",
        "transformers",
    ]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    return len(missing) == 0, missing


def check_data_dir():
    data_dir = os.getenv("SPAMLYSER_DATA_DIR", "/app/data")
    try:
        os.makedirs(data_dir, exist_ok=True)
        test_file = os.path.join(data_dir, ".healthcheck")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return True
    except Exception:
        return False


def main():
    results = {
        "status": "healthy",
        "checks": {},
    }

    streamlit_ok = check_streamlit()
    results["checks"]["streamlit"] = "up" if streamlit_ok else "down"

    imports_ok, missing = check_imports()
    results["checks"]["imports"] = {
        "status": "ok" if imports_ok else "missing",
        "missing": missing,
    }

    data_ok = check_data_dir()
    results["checks"]["data_dir"] = "writable" if data_ok else "readonly"

    if not (streamlit_ok and imports_ok and data_ok):
        results["status"] = "unhealthy"

    print(json.dumps(results, indent=2))
    sys.exit(0 if results["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
