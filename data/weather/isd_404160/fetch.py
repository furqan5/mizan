"""
Fetch NOAA NCEI ISD-Lite hourly files for Dhahran King Abdulaziz AB
(USAF 404160, WBAN 99999), 2011-2024, and verify each against the SHA-256
recorded in SOURCES.json.

Why the raw files are NOT committed
-----------------------------------
The repository is public. ISD-Lite for a Saudi station is non-U.S. data that
NCEI redistributes from WMO exchange; NCEI's ISD documentation carries a
WMO Resolution 40 notice that lets the originating country restrict
commercial re-export, and Mizan is a commercial venture's repository even
though it is licensed noncommercially. [J -- a precaution, not legal advice.]
What is committed instead:

  SOURCES.json                           URL, byte size, SHA-256 per file
  fetch.py                               this script
  dewpoint_climatology_2011_2024.csv     derived month x local-hour means
  station_years_2011_2024.csv            derived per-year coverage/summary

The aggregates reproduce scenario W1 without the raw files; the hashes let
anyone confirm they hold the same bytes. Raw files land in `raw/`, which is
git-ignored.

Usage
  python data/weather/isd_404160/fetch.py                 # download
  python data/weather/isd_404160/fetch.py --from-dir DIR  # copy a local mirror
Both refuse any file whose SHA-256 differs from the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest() -> list[dict]:
    return json.loads((HERE / "SOURCES.json").read_text(encoding="utf-8"))["files"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-dir", type=pathlib.Path, default=None,
                    help="copy from a local mirror instead of downloading")
    args = ap.parse_args()
    RAW.mkdir(exist_ok=True)
    bad = 0
    for ent in manifest():
        dest = RAW / ent["file"]
        if not (dest.exists() and sha256(dest) == ent["sha256"]):
            if args.from_dir:
                shutil.copyfile(args.from_dir / ent["file"], dest)
            else:
                with urllib.request.urlopen(ent["url"], timeout=60) as r:
                    dest.write_bytes(r.read())
        got = sha256(dest)
        ok = got == ent["sha256"] and dest.stat().st_size == ent["bytes"]
        bad += not ok
        print(f"{ent['file']:28s} {dest.stat().st_size:>8d} B  "
              f"{'OK' if ok else 'HASH MISMATCH ' + got}")
    if bad:
        print(f"{bad} file(s) failed verification. NCEI may have reissued "
              "them; do not use them silently -- record the new hashes and "
              "say so.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
