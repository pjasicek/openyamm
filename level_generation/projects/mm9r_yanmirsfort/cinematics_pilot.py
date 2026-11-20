#!/usr/bin/env python3
"""
yanmir_death without a conversion: the scratch root output/mm9_rework/cinematics_pilot_root gets
yanmirsfort.cinematics.yml (cutscene.py) and the installed yanmirsfort.lua with the parts convert.py now writes
differently (trapFires and the T_FALL handler from cutscene.trap_lua, the load line, the cinematic's block).

    python3 level_generation/projects/mm9r_yanmirsfort/cinematics_pilot.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
import cutscene  # noqa: E402
from dungeon.source import Project, Source  # noqa: E402

T_FALL = 151
SHAFT = (492, -8192, -8960)


def main() -> None:
    installed = (cutscenes.INSTALLED / f"worlds/mm9/events/maps/{cutscene.STEM}.lua").read_text(encoding="latin-1")
    yanmir = int(re.search(r"^local YANMIR = (\d+)$", installed, re.M).group(1))
    exp_trap = int(re.search(r"^    giveEeps\((\d+)\)$", installed, re.M).group(1))
    start = installed.index("-- TriggerYanmirTrap (AIOnly")
    end = installed.index("handlers[241] = function(context)")
    project = Project.load(PROJECT)
    trap = "\n".join(cutscene.trap_lua(cutscene.watch_boxes(project, Source(project)), SHAFT, T_FALL, exp_trap)) + "\n"
    load_old = '    if var("TrapFired") == 1 then openGroup("TrapFloor"); openGroup("TrapPlanks") end\n'
    replacements = [(installed[start:end], trap), (load_old, load_old + cutscene.load_lua() + "\n")]
    scenes = cutscene.scenes(yanmir)
    print(cutscenes.pilot(cutscene.STEM, scenes, replacements))


if __name__ == "__main__":
    main()
