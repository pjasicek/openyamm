#!/usr/bin/env python3
"""Copy an MM9 map's installed baked lighting (<stem>.lighting, <stem>.bake.json) to its project's
work/lighting_stale_20261031/ and remove it from the review root with review_root.remove() (the mirror entry only; a
hard-linked assets_dev original stays) when tools/lighting/stale_bakes.py finds it stale, or with --force.
User decision 2026-10-31: classic lighting until the end-of-integration lighting pass (MM9_LIGHTING_DECISION.md).

    python3 level_generation/projects/mm9r_common/rebuild_1031/remove_stale_lighting.py <stem> [--force]
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
sys.path.insert(0, str(ROOT / "tools/lighting"))
import review_root  # noqa: E402
from stale_bakes import stale_bakes  # noqa: E402

stem = sys.argv[1]
force = "--force" in sys.argv
maps = review_root.ASSETS / "worlds/mm9/maps"
lighting = maps / f"{stem}.lighting"
if not lighting.exists():
    print(f"{stem}: no sidecar installed")
    sys.exit(0)
stale = stale_bakes(review_root.ASSETS).get(f"worlds/mm9/maps/{stem}.lighting")
if not stale and not force:
    print(f"{stem}: sidecar not stale, kept")
    sys.exit(0)
target = ROOT / f"level_generation/projects/mm9r_{stem}/work/lighting_stale_20261031"
target.mkdir(parents=True, exist_ok=True)
for name in (f"{stem}.lighting", f"{stem}.bake.json"):
    if (maps / name).exists():
        shutil.copy2(maps / name, target / name)
        review_root.remove(f"worlds/mm9/maps/{name}")
(target / "WHY.txt").write_text(f"Removed from the review root 2026-10-31: stale ({', '.join(stale or ['forced'])}).\n"
                                "Classic lighting until the end-of-integration lighting pass "
                                "(devdocs/mm9_rework/MM9_LIGHTING_DECISION.md).\n")
print(f"{stem}: stale ({', '.join((stale or ['forced'])[:4])}); copied to {target} and removed")
