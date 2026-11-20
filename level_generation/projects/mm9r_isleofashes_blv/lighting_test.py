#!/usr/bin/env python3
"""
A one-off lighting test of the Isle of Ashes BLV (user, 2026-11-02: not a pipeline step): the Cycles bake
(mm9r_common/dungeon/lighting.py, profile tools/lighting/baked_indoors/profiles/mm9_isleofashes.yml) and then MM9's own
DAT lightmaps transferred onto it (mm9r_common/lightmap_transfer.py), both against this map's own review root.

    python3 level_generation/projects/mm9r_isleofashes_blv/lighting_test.py bake        # the Cycles base, installed
    python3 level_generation/projects/mm9r_isleofashes_blv/lighting_test.py transfer    # MM9's lightmaps, installed
    python3 level_generation/projects/mm9r_isleofashes_blv/lighting_test.py remove      # back to unbaked lighting
"""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import review_root  # noqa: E402

review_root.ASSETS = review_root.REVIEW / "isleofashes_blv_root"
review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"

from dungeon import lighting  # noqa: E402

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "bake":
        sys.exit(lighting.main(PROJECT, sys.argv[2:]))
    if step == "remove":
        sys.exit(lighting.main(PROJECT, ["--remove"]))
    if step == "transfer":
        import lightmap_transfer
        sys.argv = [sys.argv[0], str(PROJECT), "--root", str(review_root.ASSETS), "--install"] + sys.argv[2:]
        sys.exit(lightmap_transfer.main())
    sys.exit(__doc__)
