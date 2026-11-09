#!/usr/bin/env python3
"""
The Thjorad Mine's cinematic and quakes without a conversion (the rebuild hold): writes thjoradmine.cinematics.yml
and the installed thjoradmine.lua, changed as convert.py now writes it, into the scratch root
output/mm9_rework/cinematics_pilot_root (../mm9r_common/cutscenes.py `pilot`). The scenes and the quake Lua come from
convert.py itself (`ebora_scenes`, `quakes_lua`); the replacements below make the installed handlers match the
converter's (README "Cinematics").

    python3 level_generation/projects/mm9r_thjoradmine/cinematics_pilot.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402
from convert import cutscenes  # noqa: E402

REPORT = PROJECT / "work/build_report.json"


def replacements() -> list[tuple[str, str]]:
    scripted = json.loads(REPORT.read_text())["scripted"]
    ebora = scripted["actors"]["Ebora"]
    dust16 = ", ".join(map(str, scripted["points"]["DustObject16"]))
    sprite = "local function sprite(cog, shown) evt.SetSprite(cog, shown) end\n"
    out = [
        (sprite, sprite + "\n".join(convert.quakes_lua()) + "\n"),
        ('    open("BarWall0")\n    dust({-1972, 1027, 1075}, 1.5)\n',
         '    open("BarWall0")\n    dust({-1972, 1027, 1075}, 1.5)\n    quake("DBQuakeObject5")\n'),
        ('    open("BarWall1")\n    dust({3, 4055, 108}, 1.5)\n',
         '    open("BarWall1")\n    dust({3, 4055, 108}, 1.5)\n    quake("DBQuakeObject4")\n'),
        ('    open("ABDoorBoards0")\n    dust({10639, -14925, -1590}, 1.5)\n',
         '    open("ABDoorBoards0")\n    dust({10639, -14925, -1590}, 1.5)\n    quake("DBQuakeObject1")\n'),
        ("    evt.StartTimer(202, seconds(3))\n", f'    MM9Cinematic.start("{convert.CINEMA_ID}")\n'),
        ('    open("Stalagtite")\n',
         '    open("Stalagtite")\n    quake("TunnelQuake2")   -- the Stalagtite door\'s OpenTrigger: TunnelQuake2 On\n'),
        ('    if b == "DB_Barrel7" then open("ABMineBoards2") end\n',
         f'    if b == "DB_Barrel7" then open("ABMineBoards2") quake("DBQuakeObject3") dust({{{dust16}}}, 1.5) end'
         '   -- DBEffectsTrigger3\n'),
        ('        open("ABMineBoards0")\n        dust({12216, -13309, -1316}, 1.5)\n',
         '        open("ABMineBoards0")\n        dust({12216, -13309, -1316}, 1.5)\n'
         '        quake("DBQuakeObject0")   -- DBEffectsTrigger0\n'),
        ('    open("FallingBoard0")\n    dust({6579, -14838, -1452}, 1)\n',
         '    open("FallingBoard0")\n    dust({6579, -14838, -1452}, 1)\n    quake("DBQuakeObject2")\n'),
        (f'    if var("EboraFree") >= 3 then MM9.removeActor({ebora}) end\n',
         f'    if var("EboraFree") == 1 or var("EboraFree") == 2 then MM9Cinematic.finish("{convert.CINEMA_ID}") end\n'
         f'    if var("EboraFree") >= 3 then MM9.removeActor({ebora}) end\n'
         f'    evt.StartTimer({convert.T_QUAKE}, seconds(evt.RandomBetween(300, 600)))\n'),
        ('RegisterMapTimerEvent(202, seconds(3), handlers[202], "Ebora", "", seconds(3))\n',
         f'RegisterMapTimerEvent({convert.T_QUAKE}, seconds(3), handlers[{convert.T_QUAKE}], "Quake", "", seconds(3))\n'),
    ]
    # The old timer handler (EboraMines.scr's steps on timer 202) is gone: the cinematic's steps run them.
    text = (cutscenes.INSTALLED / "worlds/mm9/events/maps/thjoradmine.lua").read_text(encoding="latin-1")
    start = text.index("-- EboraMines.scr :FreeAtLast (also on damage)")
    end = text.index("-- The cave-in (Trigger7")
    out.append((text[start:end],
                "-- EboraMines.scr :FreeAtLast (also on damage): the cinematic ebora_free (thjoradmine.cinematics.yml): the\n"
                "-- camera on her, she taunts and vanishes in a column of fire; its gameplay steps are events 36001-36002.\n"
                "\n"))
    return out


def main() -> int:
    ebora = json.loads(REPORT.read_text())["scripted"]["actors"]["Ebora"]
    scenes = convert.ebora_scenes(ebora)
    target = cutscenes.pilot(convert.STEM, scenes, replacements())
    print(f"wrote {target} and {convert.STEM}.cinematics.yml ({', '.join(s.id for s in scenes)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
