#!/usr/bin/env python3
"""
SixFires.inc :Guilt (afterworld_guilt) without a map conversion: writes afterworld.cinematics.yml and the installed
afterworld.lua with Skraelos' :Guilt branch as the changed converter writes it (regionlua.py GUILT_LINES) and the
cutscene block appended, into the scratch root output/mm9_rework/cinematics_pilot_root (cutscenes.pilot).

    python3 level_generation/projects/mm9r_afterworld_blv/cinematics_pilot.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import cutscenes  # noqa: E402

spec = importlib.util.spec_from_file_location("regionlua_afterworld", PROJECT / "regionlua.py")
regionlua = importlib.util.module_from_spec(spec)
spec.loader.exec_module(regionlua)

OLD_GUILT = """    if has(380) and not has(381) then   -- :Guilt; the camera's "Done" (:OnDone), then :FadeIn2's greeting
        quest(); MM9.giveKey(381)
        MM9.giveKey(379); MM9.openRude(336); MM9.playSound("voices/npc/npc_336.wav")
        return
    end
"""


def main() -> int:
    scenes = regionlua.scenes()
    path = cutscenes.pilot("afterworld", scenes, [(OLD_GUILT, "\n".join(regionlua.GUILT_LINES) + "\n")])
    cinema = scenes[0].cinema
    print(f"{path}\n{cinema.id}: {cinema.shots_seconds:.2f} s, {len(cinema.shots)} shots, "
          f"steps {[(name, event) for name, _, event in scenes[0].steps]}")
    for cue in sorted(cinema.cues, key=lambda c: c["at"]):
        print(f"  {cue['at']:7.3f} {cue.get('note', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
