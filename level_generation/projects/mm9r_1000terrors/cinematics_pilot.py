#!/usr/bin/env python3
"""
Thousand Terrors' cinematics without a conversion (the rebuild hold): the scenes of cinematics_1000t.py (the same code
convert.py runs) into the scratch root output/mm9_rework/cinematics_pilot_root: 1000terrors.cinematics.yml, the
installed 1000terrors.lua with the switch, the taunt and the chess poll changed as convert.py now writes them and the
cinematics block appended, and the cues' MM9 sounds the world lacks.

    python3 level_generation/projects/mm9r_1000terrors/cinematics_pilot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import cinematics_1000t as cinema  # noqa: E402
from cinematics_1000t import cutscenes  # noqa: E402


def between(text: str, start: str, end: str) -> str:
    """The installed text from `start` up to (not including) `end`."""
    i = text.index(start)
    return text[i:text.index(end, i)]


def main() -> int:
    import convert
    from quest_xp import balanced_experience, experience_note
    report = json.loads((PROJECT / "work/build_report.json").read_text())["scripted"]
    scenes = cinema.scenes(report["actors"], report["points"], convert.hall_of_gods_arrival())
    installed = (cutscenes.INSTALLED / "worlds/mm9/events/maps/1000terrors.lua").read_text(encoding="latin-1")
    frame, objects = cinema.Frame(PROJECT), cinema.Objects.load(cinema.STEM)
    experience = (f"{balanced_experience(convert.WIN_EXPERIENCE, convert.KEY_WON, 'winman.scr', 'OnUse')}"
                  f"{experience_note(convert.WIN_EXPERIENCE, convert.KEY_WON, 'winman.scr', 'OnUse')}")
    win = "\n".join(cinema.win_handler(convert.EV_WINMAN, experience, cinema.switch_min_y(frame), frame, objects))
    taunt = "\n".join([
        f"-- TauntMan.scr (Trigger19 Start; key 108 without 497): the cinematic {cinema.TAUNT_ID} (cinematics_1000t.py:",
        "-- key 497, Door0, Njam's walk to TauntMarker and his vanishing).",
        f"handlers[{convert.EV_WINMAN + 9}] = function()",
        "    if MM9.hasKey(108) == 0 or MM9.hasKey(497) == 1 then return end",
        f"    MM9Cinematic.start(\"{cinema.TAUNT_ID}\")",
        "end",
    ])
    replacements = [
        (between(installed, "-- WinMan.scr :onSwitch, on each use", "\n\n-- The genie lamp"), win),
        (between(installed, "-- TauntMan.scr (Trigger19 Start;", "\n\n-- Monsters' DeathTriggerTarget"), taunt),
        # the installed poll's chess test (before the pawn's queening): the square's box, and the capture's call
        ("    local square = false\n    for _, b in ipairs(CHESS) do if inBox(b, x, y, z) then square = true end end",
         "    local square = false\n    for _, b in ipairs(CHESS) do if inBox(b, x, y, z) then square = b end end"),
        ("        set(\"ChessHits\", var(\"ChessHits\") + 1)\n",
         "        set(\"ChessHits\", var(\"ChessHits\") + 1)\n"
         "        MM9Cinematic.chessCapture(square)   -- ChessBase.inc :StartCamera (cinematics_1000t.py)\n"),
    ]
    chess = cinema.lua_block(scenes)[len(cutscenes.lua_block(scenes)):]
    target = cutscenes.pilot(cinema.STEM, scenes, replacements, extra_lua=chess)
    print("pilot:", target, len(scenes), "cinematics")
    for relative, source in cinema.sound_files(scenes):
        path = cutscenes.PILOT_ROOT / relative
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.read_bytes())
            print("sound:", relative)
    return 0


if __name__ == "__main__":
    sys.exit(main())
