"""Capture screenshots of the Spamlyser Pro app for PR documentation."""

import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 8510
BASE_URL = f"http://{HOST}:{PORT}"
OUTPUT_DIR = Path(__file__).resolve().parent / "screenshots"
OUTPUT_DIR.mkdir(exist_ok=True)

NAV_BUTTONS = [
    "top_nav_home",
    "top_nav_analyzer",
    "top_nav_models",
    "top_nav_feedback",
    "top_nav_about",
    "top_nav_analytics",
]

SCREENSHOT_NAMES = [
    ("01_home", "home"),
    ("02_analyzer", "analyzer"),
    ("03_models", "models"),
    ("04_feedback", "feedback"),
    ("05_about", "about"),
    ("06_analytics", "analytics"),
]


def wait_for_app(proc, timeout=60):
    import urllib.request
    import urllib.error

    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            raise RuntimeError(
                f"Streamlit exited early with code {proc.returncode}"
            )
        try:
            urllib.request.urlopen(f"{BASE_URL}/healthz", timeout=2)
            return
        except urllib.error.URLError:
            pass
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(f"App did not start within {timeout}s")


PAGE_NAV_MAP = {
    "home":      ("Home",      "nav_top_home"),
    "analyzer":  ("SMS Analyzer", "nav_top_analyzer"),
    "models":    ("Models",    "nav_top_models"),
    "feedback":  ("Feedback",  "nav_top_feedback"),
    "about":     ("About",     "nav_top_about"),
    "analytics": ("Analytics","nav_top_analytics"),
}


def click_nav_and_screenshot(page, page_name, filename):
    """Navigate by clicking the top nav button for a page."""
    try:
        label, key = PAGE_NAV_MAP[page_name]

        # Try by Streamlit key attribute first
        button = page.locator(f'button:has([key="{key}"])')
        if button.count() == 0:
            # Fallback: by text
            button = page.locator(f'button:has-text("{label}")')

        if button.count() > 0:
            button.first.click()
            print(f"  [INFO] Clicked '{label}'")
        else:
            print(f"  [WARN] Button '{label}' not found, capturing current page")

        page.wait_for_timeout(5000)
        page.screenshot(
            path=str(OUTPUT_DIR / filename),
            full_page=True,
        )
        print(f"  [OK] Saved {filename}")
    except Exception as e:
        print(f"  [FAIL] {e}")


def main():
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            "--server.headless",
            "true",
            "--server.port",
            str(PORT),
            "--server.address",
            HOST,
            "--global.developmentMode",
            "false",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=Path(__file__).resolve().parent,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        print("Waiting for app to start...")
        wait_for_app(proc)
        print(f"App ready at {BASE_URL}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                device_scale_factor=2,
            )
            page = context.new_page()

            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(5000)
            print("  [OK] Loaded home page")

            for name, page_key in SCREENSHOT_NAMES:
                filename = f"{name}.png"
                print(f"  Capturing {name} ({page_key})...")
                click_nav_and_screenshot(page, page_key, filename)

            browser.close()
        print(f"\nAll screenshots saved to {OUTPUT_DIR}")
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()
