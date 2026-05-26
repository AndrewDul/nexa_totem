#!/usr/bin/env python3
"""Run the localhost NeXa diagnostics API."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from system.services.diagnostics.live_api import HOST, PORT, serve_forever


def main():
    print(f"Starting NeXa diagnostics API on {HOST}:{PORT}")
    serve_forever(HOST, PORT)


if __name__ == "__main__":
    main()
