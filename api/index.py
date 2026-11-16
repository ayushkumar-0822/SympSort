from __future__ import annotations

import os
import sys
import tempfile
import urllib.parse
from pathlib import Path

# Add project root to sys.path so all imports resolve seamlessly in serverless
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Matplotlib uses writable temp directory for font cache and config
mpl_dir = os.path.join(tempfile.gettempdir(), ".matplotlib")
os.environ.setdefault("MPLCONFIGDIR", mpl_dir)

from app import create_app

flask_app = create_app()

def app(environ, start_response):
    """Normalize Vercel rewrite paths before dispatching to Flask."""
    qs = environ.get("QUERY_STRING", "")
    params = urllib.parse.parse_qs(qs, keep_blank_values=True)

    # 1. Check if the true path was forwarded in query parameter __path__
    if "__path__" in params:
        target = params.pop("__path__")[0]
        environ["PATH_INFO"] = target
        environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)
    # 2. If Vercel rewrote to /api/index without __path__, check headers or default to /
    elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api", ""):
        raw_path = (
            environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("REQUEST_URI")
            or environ.get("RAW_URI")
            or ""
        )
        if "?" in raw_path:
            raw_path = raw_path.split("?", 1)[0]
        if raw_path and not raw_path.startswith("/api/index"):
            environ["PATH_INFO"] = raw_path
        else:
            environ["PATH_INFO"] = "/"

    return flask_app(environ, start_response)

application = app
