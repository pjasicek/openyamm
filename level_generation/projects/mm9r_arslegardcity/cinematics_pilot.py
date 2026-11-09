#!/usr/bin/env python3
"""
Arslegard City's cinematics without a conversion (README "Cinematics"): gate_fate and gate_writ from
gate_cinematics.scenes (the converter's code) into the scratch root output/mm9_rework/cinematics_pilot_root, with
the installed arslegardcity.lua changed as the converter now writes it (citylua.gate_lines and poll_lines in place of
the status-line scene) and the scenes' Lua appended (mm9r_common/cutscenes.py pilot). The scenes' voice wavs
(MM9 VOICES/CINEMA, imported as worlds/mm9/audio/voices/cinema/) are copied into the scratch root's audio where
missing.

    python3 level_generation/projects/mm9r_arslegardcity/cinematics_pilot.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import citylua  # noqa: E402
import cutscenes  # noqa: E402
import gate_cinematics  # noqa: E402


def section(text: str, start: str, end: str) -> str:
    """The installed text from `start` up to (not including) `end`."""
    first = text.index(start)
    return text[first:text.index(end, first)]


def main() -> int:
    movers, hanndl, arrival, experience = gate_cinematics.installed_inputs()
    scenes = gate_cinematics.scenes(movers, hanndl, arrival, experience)
    installed = (cutscenes.INSTALLED / f"worlds/mm9/events/maps/{gate_cinematics.STEM}.lua").read_text(
        encoding="latin-1")
    gate_old = section(installed, "-- The Great Gate scene (FateMan.scr, WritMan.scr", "\n\n-- BookLetter.scr letters")
    poll_old = section(installed, "-- The gate scene starts as MM9's does", "handlers[260] = poll")
    replacements = [(gate_old, "\n".join(citylua.gate_lines(arrival[4]))),
                    (poll_old, "\n".join(citylua.poll_lines()) + "\n")]
    target = cutscenes.pilot(gate_cinematics.STEM, scenes, replacements)
    copied = 0
    for scene in scenes:
        for cue in scene.cinema.cues:
            name = cue.get("sound", "")
            if not name.startswith("voices\\"):
                continue
            destination = cutscenes.PILOT_ROOT / "worlds/mm9/audio" / name.replace("\\", "/")
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(gate_cinematics.voice_path(name), destination)
                copied += 1
    for scene in scenes:
        print(f"{scene.id}: {scene.cinema.shots_seconds:.2f} s, {len(scene.cinema.shots)} shots, steps "
              f"{[event for _, _, event in scene.steps]}, done {scene.done_event}")
    print(f"wrote {target} and {gate_cinematics.STEM}.cinematics.yml; {copied} voice wavs copied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
