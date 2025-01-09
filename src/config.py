""" Configuration file for the project. """

import os
from pathlib import Path

# Base configuration
BASE_DIR = Path(__file__).resolve().parent
TMP_BASE_PATH = BASE_DIR / "tmp"

# Timeout settings
CLONE_TIMEOUT = int(os.getenv("GITINGEST_CLONE_TIMEOUT", 300))  # 5 minutes
REQUEST_TIMEOUT = int(os.getenv("GITINGEST_REQUEST_TIMEOUT", 600))  # 10 minutes
PROCESSING_TIMEOUT = int(os.getenv("GITINGEST_PROCESSING_TIMEOUT", 480))  # 8 minutes

# Host settings
DEFAULT_HOSTS = "gitingest.com,*.gitingest.com,localhost,127.0.0.1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", DEFAULT_HOSTS).replace(" ", "").split(",")

MAX_DISPLAY_SIZE: int = 300_000
TMP_BASE_PATH = Path("/tmp/gitingest")
DELETE_REPO_AFTER: int = 60 * 60  # In seconds

EXAMPLE_REPOS: list[dict[str, str]] = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Tldraw", "url": "https://github.com/tldraw/tldraw"},
    {"name": "ApiAnalytics", "url": "https://github.com/tom-draper/api-analytics"},
]
