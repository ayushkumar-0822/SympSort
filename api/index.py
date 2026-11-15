from __future__ import annotations

import os
import sys
import tempfile
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
    path = environ.get("PATH_INFO", "")
    if path in ("/api/index", "/api/index.py", "/api", ""):
        environ["PATH_INFO"] = "/"
    return flask_app(environ, start_response)

application = app
