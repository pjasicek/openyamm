#!/usr/bin/env python3
"""
Thronheim, MM9 rework: MM9's THRONHEIM.dat as a BLV open to the sky (devdocs/mm9_rework/OUTDOOR_BLV_ALL.md; the shared
part is ../mm9r_common/outdoor_blv.py, template Sturmford). Installs into output/mm9_rework/isleofashes_blv_root.

    python3 level_generation/projects/mm9r_thronheim_blv/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_thronheim_blv/convert.py --plan     # rooms only: work/rooms*.png
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import review_root  # noqa: E402

review_root.ASSETS = review_root.REVIEW / "isleofashes_blv_root"
review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"

import outdoor_blv  # noqa: E402

if __name__ == "__main__":
    if not review_root.ASSETS.exists():
        sys.exit(f"{review_root.ASSETS} is missing: create it first (../mm9r_isleofashes_blv/README.md)")
    sys.exit(outdoor_blv.convert_region(PROJECT, "mm9r_thronheim_blv"))
