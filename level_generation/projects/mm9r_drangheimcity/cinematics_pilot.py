#!/usr/bin/env python3
"""
The dwarves_and_humans cinematic without a conversion (README "Cinematics"): writes drangheimcity.cinematics.yml from
citylua.scenes() and the installed drangheimcity.lua as the changed citylua.py now writes it into the scratch root
output/mm9_rework/cinematics_pilot_root (mm9r_common/cutscenes.py pilot):

    python3 level_generation/projects/mm9r_drangheimcity/cinematics_pilot.py

The replacements turn the installed Hrolf code (a 1-second proximity poll that gave key 5010 and moved Hrolf to his
marker at once) into citylua.py's: Hrolf's FoundPlayer event (56000 + his DAT index) starts the cinematic and the poll
no longer watches him; the scene's block and the fight's kill hook are appended as map_script appends them.
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

STEM = "drangheimcity"


def built() -> tuple[dict, dict, dict]:
    """The built map's actor indices and DAT indices by DAT name (work/build_report.json, convert.py's hooks.actor and
    hooks.objects) and the two actors' monster rows (the installed scene)."""
    scripted = json.loads((PROJECT / "work/build_report.json").read_text())["scripted"]
    import yaml
    scene = yaml.load((cutscenes.INSTALLED / f"worlds/mm9/maps/{STEM}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    monsters = {name: actors[scripted["actors"][name]]["monster_id"] for name in ("Hrolf", "Alfrigg")}
    return scripted["actors"], scripted["objects"], monsters


def replacements(actors: dict, objects: dict) -> list[tuple[str, str]]:
    hrolf, event = actors["Hrolf"], citylua.found_player_event(objects["Hrolf"])
    installed = (cutscenes.INSTALLED / f"worlds/mm9/events/maps/{STEM}.lua").read_text(encoding="latin-1")
    start = installed.index("-- NPC110.scr / NPC109.scr (Hrolf Anfarssen")
    end = installed.index("\n\n", start) + 1
    marker = next(line for line in installed[start:end].splitlines() if "evt.SetMapActorPosition" in line)
    point = [int(v) for v in marker.split("(", 1)[1].rstrip(")").split(",")[1:]]
    new_head = "\n".join(citylua.hrolf_lua(hrolf, point, event))
    keith = "RegisterEvent(50320, \"Keith Bloodaxe\", handlers[50320])\n"
    return [
        (installed[start:end], new_head),
        ("    hrolfWatch()\n    if var(\"HrolfAway\") == 1 then set(\"HrolfAway\", 0); hrolfAway() end\n", ""),
        (keith, keith + f"RegisterEvent({event}, \"Hrolf\", handlers[{event}])\n"),
    ]


def main() -> int:
    actors, objects, monsters = built()
    target = cutscenes.pilot(STEM, citylua.scenes(actors, monsters), replacements(actors, objects),
                             extra_lua=citylua.fight_over_lua(actors, monsters))
    print(f"wrote {target} and {STEM}.cinematics.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
