#!/usr/bin/env python3
"""
The break_ice and bob_and_doug cinematics without a conversion (README "Cinematics"): writes
frosgardcity.cinematics.yml from
citylua.scenes() and the installed frosgardcity.lua with the ice part as the changed citylua.py now writes it into the
scratch root output/mm9_rework/cinematics_pilot_root (mm9r_common/cutscenes.py pilot):

    python3 level_generation/projects/mm9r_frosgardcity/cinematics_pilot.py

The replacements turn the installed (pre-cinematic) ice code into citylua.py's: the poll's waves become the
cinematic's steps, the barrel's click starts it, the load hides the ice on 72 or 174, the poll starts Bob and Doug's
banter near Douglas; the barrel's death handler and the scenes' block are appended as map_script appends them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
import citylua  # noqa: E402

OLD_HEAD = """-- cannon (Shooter0, FrosgardShooter.scr), whose start runs BreakIce's cinema (cameras, cannon shots); the floes
-- break in five waves and :GivePoints gives 72 and 8 000 experience (with 71), else 174 and 8 000. Here a click
-- on the barrel sets it off; the waves follow on the 1-second poll; each floe drops under the ocean surface.
"""
NEW_HEAD = """-- cannon (Shooter0, FrosgardShooter.scr), whose start runs BreakIce's cinema; here its click or its breaking
-- does, and the cinema is the cinematic break_ice: Shooter1-4 bolt the first floes, the rest break in MM9's
-- waves (each floe drops under the ocean surface) and :GivePoints gives 72 and 8 000 experience (with 71), else
-- 174 and 8 000: its steps (the block at the end of this file).
"""
OLD_WAVE = """local function iceWave()
    local stage = var("IceStage")
    if stage < 1 then return end
    if stage <= #ICE then
        MM9.playSound("sounds/events/iceimpact.wav")
        for _, n in ipairs(ICE[stage]) do open(n) end
        set("IceStage", stage + 1)
        return
    end
    set("IceStage", 0)
    iceGone()
"""
NEW_WAVE = """local function floes(names) for _, n in ipairs(names) do if DOORS[n] then open(n) end end end
local function iceReward()   -- BreakIce.scr :GivePoints
    iceGone()
"""


def replacements(text: str) -> list[tuple[str, str]]:
    start = text.index("local ICE = {")
    ice_line = text[start:text.index("\n", start) + 1]
    return [
        (OLD_HEAD + ice_line, NEW_HEAD),
        (OLD_WAVE, NEW_WAVE),
        ("""    set("IceStage", 1)
    set("CannonShots", 8); evt.StartTimer(235, seconds(0.1))
end
""", """    set("CannonShots", 8); evt.StartTimer(235, seconds(0.1))
    MM9Cinematic.start("break_ice")
end
"""),
        ("local function poll()\n    shopHours()\n    iceWave()\n",
         "\n".join(citylua.banter_lua(built_actors()["Douglas"])) + "\nlocal function poll()\n    shopHours()\n    banter()\n"),
        ("    if has(72) then iceGone() end   -- BreakIce.scr :Init\n",
         "    if has(72) or has(174) then iceGone() end   -- BreakIce.scr :Init (TELP 1.3)\n"),
    ]


def built_actors() -> dict:
    """The built map's actor indices by DAT name (convert.py's hooks.actor, in work/build_report.json)."""
    return json.loads((PROJECT / "work/build_report.json").read_text())["scripted"]["actors"]


def main() -> int:
    installed = (cutscenes.INSTALLED / "worlds/mm9/events/maps/frosgardcity.lua").read_text(encoding="latin-1")
    target = cutscenes.pilot("frosgardcity", citylua.scenes(built_actors()), replacements(installed),
                             extra_lua=citylua.barrel_death_lua())
    print(f"wrote {target} and frosgardcity.cinematics.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
