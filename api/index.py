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


class VercelPathMiddleware:
    """WSGI middleware to restore original request paths from Vercel rewrites and edge headers."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get("QUERY_STRING", "")
        params = urllib.parse.parse_qs(qs, keep_blank_values=True)

        # 1. Check if the true path was forwarded in query parameter __path__
        if "__path__" in params:
            target = params.pop("__path__")[0]
            environ["PATH_INFO"] = target
            environ["QUERY_STRING"] = urllib.parse.urlencode(params, doseq=True)
        # 2. Check if Vercel passed original path in standard proxy/edge headers
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api", ""):
            raw_path = (
                environ.get("HTTP_X_MATCHED_PATH")
                or environ.get("HTTP_X_FORWARDED_URI")
                or environ.get("HTTP_X_FORWARDED_PATH")
                or environ.get("HTTP_X_ORIGINAL_URL")
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

        return self.wsgi_app(environ, start_response)


# Initialize Flask app and attach middleware
app = create_app()
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
application = app
