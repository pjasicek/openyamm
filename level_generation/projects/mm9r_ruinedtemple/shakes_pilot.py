#!/usr/bin/env python3
"""
The temple's quakes and dust without a conversion (MM9_CUTSCENES.md section 5; README "Camera shake"): the installed
ruinedtemple.lua with the text convert.py now generates for them (effects_lua, the crypt, the cave-ins and the
TriggerHostile0 volume), written into the scratch root output/mm9_rework/cinematics_pilot_root after a syntax check.
No cinematics file: the temple has no cutscene.

    python3 level_generation/projects/mm9r_ruinedtemple/shakes_pilot.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
import convert  # noqa: E402

STEM = "ruinedtemple"


def replacements() -> list[tuple[str, str]]:
    objects = cutscenes.Objects.load(STEM)
    frame = cutscenes.Frame(PROJECT)
    block = "\n".join(convert.effects_lua(lambda name: objects.named(name)["values"], frame.point))
    cave = ('local function caveIn(left, right, timerLeft, timerRight)\n'
            '    evt.PlaySoundName("sounds/weapons/eqhammerimpact.wav", 0, 0, 0)\n'
            '    arm(timerLeft, 0.5); arm(timerRight, 1)\nend')
    return [
        ("    return MM9.giveItem(raw, source)\nend\n", "    return MM9.giveItem(raw, source)\nend\n" + block + "\n"),
        ('    openG("DB_Crypt0")\n    set("CryptOpen", 1)',
         '    openG("DB_Crypt0")\n    hostile0()   -- DB_Crypt0\'s death triggers TriggerHostile0\n'
         '    set("CryptOpen", 1)'),
        ("-- shatter into the same floor (not built: overrides.yml).\n" + cave,
         "-- shatter into the same floor (not built: overrides.yml). The trigger shakes its QuakeObject; each broken\n"
         "-- rail or ceiling brush sends its DBEffectsTrigger (dust and a quake).\n"
         'local function caveIn(left, right, timerLeft, timerRight, quakeName)\n'
         '    evt.PlaySoundName("sounds/weapons/eqhammerimpact.wav", 0, 0, 0)\n'
         '    quake(quakeName)\n'
         '    arm(timerLeft, 0.5); arm(timerRight, 1)\nend'),
        ('openG("DB_RailLeft"); openG("CaveInLeft")', 'openG("DB_RailLeft"); dbEffects(1); openG("CaveInLeft")'),
        ('openG("DB_RailRight"); openG("CaveInRight")', 'openG("DB_RailRight"); dbEffects(1); openG("CaveInRight")'),
        ('openG("DB_CeilingLeft"); openG("CaveInLeftB")',
         'openG("DB_CeilingLeft"); dbEffects(2); openG("CaveInLeftB")'),
        ('openG("DB_CeilingRight"); openG("CaveInRightB")',
         'openG("DB_CeilingRight"); dbEffects(2); openG("CaveInRightB")'),
        ('caveIn("Left", "Right", 405, 406)', 'caveIn("Left", "Right", 405, 406, "QuakeObject0")'),
        ('caveIn("LeftB", "RightB", 407, 408)', 'caveIn("LeftB", "RightB", 407, 408, "QuakeObject2")'),
        ('run = function() set("ShaftBottomReached", 1) end', 'run = function() set("ShaftBottomReached", 1); hostile0() end'),
    ]


def main() -> int:
    relative = Path(f"worlds/mm9/events/maps/{STEM}.lua")
    text = (cutscenes.INSTALLED / relative).read_text(encoding="latin-1")
    for old, new in replacements():
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"replacement text occurs {count} times: {old[:80]!r}")
        text = text.replace(old, new)
    cutscenes.syntax_check(text)
    target = cutscenes.PILOT_ROOT / relative
    if target.exists():
        target.unlink()   # a hard link of assets_dev's: replace, never write through
    target.write_text(text, encoding="latin-1")
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
