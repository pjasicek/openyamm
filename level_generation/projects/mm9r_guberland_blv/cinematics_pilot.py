#!/usr/bin/env python3
"""
The newgame_talk cinematic without a conversion (README "Cinematics"): writes guberland.cinematics.yml from
regionlua.scenes() and the installed guberland.lua as the changed regionlua.py now writes it into the scratch root
output/mm9_rework/cinematics_pilot_root (mm9r_common/cutscenes.py pilot):

    python3 level_generation/projects/mm9r_guberland_blv/cinematics_pilot.py

The replacements add what regionlua.py now adds: Scandlan's FoundPlayer event (56000 + his DAT index) starting the
cinematic, and its registration; the scene's block is appended as the map script's last hook. The actors are the
installed scene's (by their DAT object index), as the build's hooks.npc_actor names them.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import cutscenes  # noqa: E402
import regionlua  # noqa: E402

STEM = "guberland"
NAMES = ("Scandlan", "Broccan", "CommonerHalfOrcMaleA0")


def built() -> tuple[dict, dict, dict]:
    """The installed map's actor indices, floor points and DAT indices of NAMES."""
    objects = cutscenes.Objects.load(STEM)
    scene = yaml.load((cutscenes.INSTALLED / f"worlds/mm9/maps/{STEM}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    by_source = {a["mm9_source_object_index"]: a for a in scene["initial_state"]["actors"]
                 if "mm9_source_object_index" in a}
    dat = {name: objects.named(name)["index"] for name in NAMES}
    actors = {name: by_source[dat[name]]["actor_index"] for name in NAMES}
    points = {name: [by_source[dat[name]]["position"][k] for k in "xyz"] for name in NAMES}
    return actors, points, dat


def replacements(dat: dict) -> list[tuple[str, str]]:
    event = 56000 + dat["Scandlan"]
    handler = "\n".join(regionlua.talk_start_lua(event) + [""])
    visibility = "-- Visibility and the games on every load (the scripts' :Init).\n"
    alvar = "RegisterEvent(50345, \"Alvar the Clumsy\", handlers[50345])\n"
    return [(visibility, handler + visibility),
            (alvar, alvar + f"RegisterEvent({event}, \"Scandlan\", handlers[{event}])\n")]


def main() -> int:
    actors, points, dat = built()
    scenes = regionlua.scenes(actors, points["Broccan"], points["CommonerHalfOrcMaleA0"])
    target = cutscenes.pilot(STEM, scenes, replacements(dat))
    print(f"wrote {target} and {STEM}.cinematics.yml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
