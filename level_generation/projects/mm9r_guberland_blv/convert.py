#!/usr/bin/env python3
"""
Guberland, MM9 rework: MM9's GUBERLAND.dat as a BLV open to the sky (devdocs/mm9_rework/OUTDOOR_BLV_ALL.md; the shared
part is ../mm9r_common/outdoor_blv.py, template Sturmford). Installs into output/mm9_rework/isleofashes_blv_root.

    python3 level_generation/projects/mm9r_guberland_blv/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_guberland_blv/convert.py --plan     # rooms only: work/rooms*.png
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

import cutscenes  # noqa: E402
import dungeon  # noqa: E402
import terrain_blend  # noqa: E402


class Guberland(outdoor_blv.OutdoorBlvHooks):
    generator = "mm9r_guberland_blv"


if __name__ == "__main__":
    if not review_root.ASSETS.exists():
        sys.exit(f"{review_root.ASSETS} is missing: create it first (../mm9r_isleofashes_blv/README.md)")
    # outdoor_blv.convert_region's steps, keeping the hooks: regionlua.py's map script leaves the cutscenes on them
    hooks = Guberland(PROJECT)
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        project = dungeon.source.Project.load(PROJECT)
        print(f"boat arrivals rewritten: {outdoor_blv.rewrite_transport(project)}")
        if (project.work / "props.json").exists():
            print(f"indoor decoration bindings added: {outdoor_blv.bind_indoor_decorations(project.work / 'props.json')}")
        print(terrain_blend.install(PROJECT))
        # Scandlan and Broccan's new-game talk (regionlua.scenes): the engine loads it beside the map
        print(f"cinematics installed: {cutscenes.install('guberland', getattr(hooks, 'scenes', []))}")
    sys.exit(code)
