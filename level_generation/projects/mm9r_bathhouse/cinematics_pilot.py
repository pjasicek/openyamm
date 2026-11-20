#!/usr/bin/env python3
"""
The Bathhouse's cinematic and quake without a conversion (README "Cinematics"): bathhouse.cinematics.yml from
bath_cinematics.scenes and the installed bathhouse.lua with the changes convert.py now makes (the quake and its rumble
loops in the valve handler and the poll, Ebora's escape as the cinematic's start and steps), written into the scratch
root output/mm9_rework/cinematics_pilot_root.

    python3 level_generation/projects/mm9r_bathhouse/cinematics_pilot.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import bath_cinematics  # noqa: E402
import cutscenes  # noqa: E402  (bath_cinematics put mm9r_common on the path)

EBORA_ACTOR = 7          # the installed scene's Ebora (convert.py actor_index["Ebora"])


def replacements(text: str) -> list[tuple[str, str]]:
    start = text.index("local function escape()\n")
    end = text.index("handlers[97] = function(context)")
    return [
        ("    return math.abs(x - p[1]) < range and math.abs(y - p[2]) < range and math.abs(z - p[3]) < range\nend\n",
         "    return math.abs(x - p[1]) < range and math.abs(y - p[2]) < range and math.abs(z - p[3]) < range\nend\n"
         + bath_cinematics.RUMBLE_LOCAL + "\n"),
        ("        evt.PlaySoundName(\"sounds/weapons/eqhammerpostimpactloop.wav\", 0, 0, 0)\n",
         "\n".join(bath_cinematics.quake_lua()) + "\n"),
        (text[start:end], ""),
        ("    if dead >= 3 then escape() else",
         f"    if dead >= 3 then MM9Cinematic.start(\"{bath_cinematics.CINEMA_ID}\") else"),
        ("    -- the pistons pump while the valve is open",
         "\n".join(bath_cinematics.rumble_poll_lua()) + "\n    -- the pistons pump while the valve is open"),
    ]


def main() -> int:
    installed = (cutscenes.INSTALLED / f"worlds/mm9/events/maps/{bath_cinematics.STEM}.lua").read_text(
        encoding="latin-1")
    scenes = bath_cinematics.scenes(EBORA_ACTOR)
    target = cutscenes.pilot(bath_cinematics.STEM, scenes, replacements(installed))
    print(f"wrote {target} and {bath_cinematics.STEM}.cinematics.yml")
    print(cutscenes.yaml_text(bath_cinematics.STEM, scenes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
