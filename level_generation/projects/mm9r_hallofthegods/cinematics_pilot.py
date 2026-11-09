#!/usr/bin/env python3
"""
Hall of the Gods' epilogue without a conversion (the rebuild hold): the scene of cinematics_hall.py (the same code
convert.py runs) into the scratch root output/mm9_rework/cinematics_pilot_root: hallofthegods.cinematics.yml and the
installed hallofthegods.lua with the old timer stand-in replaced as convert.py now writes it and the cinematics block
appended.

    python3 level_generation/projects/mm9r_hallofthegods/cinematics_pilot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import cinematics_hall as cinema  # noqa: E402
from cinematics_hall import cutscenes  # noqa: E402


def main() -> int:
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    actors = report["scripted"]["actors"]
    scene = json.loads((cutscenes.INSTALLED / "worlds/mm9/maps/hallofthegods.scene.yml").read_text())
    hanndl = next(a for a in scene["initial_state"]["actors"] if a["actor_index"] == actors["Hanndl"])
    start = [hanndl["position"][k] for k in ("x", "y", "z")]
    scenes = cinema.scenes(actors, report["hanndl_mark"], start)
    installed = (cutscenes.INSTALLED / "worlds/mm9/events/maps/hallofthegods.lua").read_text(encoding="latin-1")
    i = installed.index("handlers[260] = function()")
    old = installed[i:installed.index("\nend\n", installed.index("handlers[1] = function()")) + len("\nend")]
    replacements = [
        (old, "\n".join(cinema.LOAD_LUA)),
        ('RegisterMapTimerEvent(260, seconds(3), handlers[260], "Cinema", "", seconds(3))\n', ""),
        ("-- The cameras, letterbox, voice lines and DoHighScore are not carried (README).",
         "-- The cinematic gods_epilogue (cinematics_hall.py) plays it; DoHighScore is the world's completion (key 109)."),
    ]
    target = cutscenes.pilot(cinema.STEM, scenes, replacements)
    print("pilot:", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
