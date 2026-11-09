#!/usr/bin/env python3
"""
Review of the rotating movers against MM9: the same views and the same motions in the native BLV and in the old
bmodel_world map (MM9's own geometry and rotating mechanisms), driven by the debug console in menu input tours.

    python3 level_generation/projects/mm9r_anskramkeep/review_movers.py tours      # review/movers_run.sh and its tours
    bash level_generation/projects/mm9r_anskramkeep/review/movers_run.sh
    python3 level_generation/projects/mm9r_anskramkeep/review_movers.py sheet      # review/movers_compare.jpg
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
REVIEW = PROJECT / "review"
SCALE = 2.56


def lt(x, z, y=-192.0):
    return [round(x * SCALE), round(z * SCALE), round(y * SCALE)]


def moves() -> dict:
    return {m["node"][5:]: m for m in json.loads((PROJECT / "work/doors.json").read_text())}


# One run per view: name, party position, yaw and pitch (degrees), the event key (door, lever, trap, hatch) or None,
# and the shots: (name, seconds to wait before it; None: before the event).
VIEWS = [("door", lt(0, 40), 90, 0, "door", [("door_shut", None), ("door_swinging", 0.45), ("door_open", 1.2)]),
         ("lever", lt(390, 3520), 180, 8, "lever", [("lever_shut", None), ("lever_moved", 2.2)]),
         ("trap", lt(1170, 700), 0, -10, "trap", [("trap_shut", None), ("trap_turning", 0.45), ("trap_open", 0.8)]),
         ("hatch", lt(1244, 704, -436), 180, 50, "hatch", [("hatch_shut", None), ("hatch_open", 2.0)]),
         ("pit", lt(1344, 590, -420), 90, -12, None, [("pit_spikes", None)]),
         # Beyond the mover review: the barred window from the airlock's east room and from the vestibule, the niche
         # behind trap 1 from inside, and the shut slabs over the Giant Imp's shaft.
         ("window", lt(420, 3592), 180, 0, None, [("window_room", None)]),
         ("windowback", lt(160, 3592), 0, 0, None, [("window_vestibule", None)]),
         ("niche", lt(1344, 560, -190), 270, 0, None, [("niche", None)]),
         ("ontrap", lt(1344, 708, -190), 180, 0, None, [("on_trap", None)]),
         ("onhatch", lt(1240, 704, -190), 0, 0, None, [("on_hatch", None)]),
         ("shaft", lt(0, 4760), 90, -18, None, [("shaft", None)])]
# The original map runs on the outdoor renderer, whose enclosed-map view distance fades far geometry: not MM9.
OVERRIDES = {"original": "--set video.view_distance=unlimited ", "native": ""}
EVENTS = {"original": {"door": 30715, "lever": 30750, "trap": 30029, "hatch": 30032},
          "native": {"door": "DoubleDoorL15", "lever": "SwitchLever0", "trap": "PivotWallTrap1",
                     "hatch": "TrapExitDoor1"}}


def tour(tag: str, event, shots: list) -> dict:
    steps = [{"wait": 2.0}]
    for shot, delay in shots:
        if delay is not None:
            if event is not None:
                steps.append({"console": f"event {event}"})
                event = None
            steps.append({"wait": delay})
        steps.append({"capture": shot})
    return {"output_dir": str(REVIEW / f"movers_{tag}"), "exit": True, "steps": steps}


def main() -> int:
    if sys.argv[1] == "tours":
        door = moves()
        script = [f"#!/bin/bash\ncd {ROOT}"]
        for tag, assets, game_map in (("native", "output/mm9_rework/assets_dev", "anskramkeep.blv"),
                                      ("original", "output/mm9_rework/assets_original", "anskramkeep.odm")):
            for name, position, yaw, pitch, key, shots in VIEWS:
                event = None
                if key is not None:
                    event = EVENTS[tag][key]
                    event = door[event]["event"] if tag == "native" else event
                path = REVIEW / f"movers_{tag}_{name}.tour.yml"
                path.write_text(yaml.safe_dump(tour(tag, event, shots), sort_keys=False))
                script.append(f"./tools/run_game.sh --isolated mv{tag}{name} --world mm9 --map {game_map} "
                              f"--assets $PWD/{assets} --position {position[0]} {position[1]} {position[2]} "
                              f"--yaw-radians {math.radians(yaw):.4f} --pitch-degrees {pitch} --warmup 3 --seconds 25 "
                              f"{OVERRIDES[tag]}--set debug.menu_input_tour_path={path} > /dev/null 2>&1 &")
        script.append("wait")
        (REVIEW / "movers_run.sh").write_text("\n".join(script) + "\n")
        print(REVIEW / "movers_run.sh")
        return 0
    names = [shot for view in VIEWS for shot, _ in view[5]]
    width, height = 640, 360
    sheet = Image.new("RGB", (width * 2, (height + 20) * len(names)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(names):
        for column, tag in enumerate(("original", "native")):
            path = REVIEW / f"movers_{tag}/{name}.png"
            if path.exists():
                sheet.paste(Image.open(path).convert("RGB").resize((width, height)),
                            (column * width, row * (height + 20) + 20))
            draw.text((column * width + 6, row * (height + 20) + 4), f"{tag}: {name}", fill=(235, 235, 235))
    sheet.save(REVIEW / "movers_compare.jpg", quality=85)
    print(REVIEW / "movers_compare.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
