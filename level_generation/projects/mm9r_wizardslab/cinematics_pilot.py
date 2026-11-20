#!/usr/bin/env python3
"""
The summoning's cinematic without a conversion (README "Cinematics"): citylua.cinematic_scenes builds the scene the
converter installs; this writes it and the installed wizardslab.lua, changed as the converter's citylua.py now writes
the ritual and with the cinematic block appended, into the scratch root output/mm9_rework/cinematics_pilot_root
(mm9r_common/cutscenes.py pilot). Actor indices come from the last build (work/build_report.json).

    python3 level_generation/projects/mm9r_wizardslab/cinematics_pilot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import citylua  # noqa: E402
import cutscenes  # noqa: E402

# The installed Lua's ritual as citylua.py wrote it before, and as it writes it now.
REPLACEMENTS = [
    ("-- cinema is not carried: the party watches. WizardSummoner.scr (six apprentices, friends of the party):",
     "-- cinema is the cinematic summoning (cinematic_scenes), whose steps run the ritual's ticks below (each once,\n"
     "-- in order; a skip runs them at once). WizardSummoner.scr (six apprentices, friends of the party):"),
    ("local function ritualStep()",
     "-- timed: timer 270 runs a summoning an old save left half-way (it plays the sounds the cinematic's cues play\n"
     "-- and arms the next tick)\n"
     "local function ritualStep(timed)"),
    ('        sound("ambient/thunder/thunderlong.wav")',
     '        if timed then sound("ambient/thunder/thunderlong.wav") end'),
    ("        set(\"RitualStep\", step + 1)\n        arm(270, 2.5)",
     "        set(\"RitualStep\", step + 1)\n        if timed then arm(270, 2.5) end"),
    ('        sound("magic/cast03.wav")\n        set("RitualStep", 8)\n        arm(270, 2.5)',
     '        if timed then sound("magic/cast03.wav") end\n        set("RitualStep", 8)\n'
     '        if timed then arm(270, 2.5) end'),
    ('        sound("animsounds/dragon/fidget2.wav")',
     '        if timed then sound("animsounds/dragon/fidget2.wav") end'),
    ("local function startRitual()   -- DestinationPurple -> CameraSummon 'next' (once)\n"
     "    if var(\"RitualStep\") ~= 0 then return end\n"
     "    set(\"RitualStep\", 1)\n"
     "    arm(270, 2.0)\n"
     "end\n"
     "handlers[270] = function() if fired(270) then ritualStep() end end",
     "local function ritualAdvance(step)   -- a step of the cinematic summoning: the ritual's tick `step`\n"
     "    if var(\"RitualStep\") == step then ritualStep(false) end\n"
     "end\n"
     "local function startRitual()   -- DestinationPurple -> CameraSummon 'next' (once): the cinematic\n"
     "    if var(\"RitualStep\") ~= 0 then return end\n"
     "    set(\"RitualStep\", 1)\n"
     "    MM9Cinematic.start(\"summoning\")\n"
     "end\n"
     "handlers[270] = function() if fired(270) then ritualStep(true) end end"),
]


def main() -> int:
    actors = json.loads((PROJECT / "work/build_report.json").read_text())["scripted"]["actors"]
    scenes = citylua.cinematic_scenes(actors)
    target = cutscenes.pilot("wizardslab", scenes, REPLACEMENTS)
    print(f"wrote {target} and wizardslab.cinematics.yml ({scenes[0].cinema.shots_seconds:.1f} s of shots)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
