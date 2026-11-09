#!/usr/bin/env python3
"""
Write chests.yml: a headless scenario that stands in front of each converted MM9 chest, looks at its model and
presses interact, expecting that chest to open. Run it from output/mm9_rework/scenario_run (its settings.ini points
at the review root):

    python3 level_generation/projects/mm9r_isleofashes/make_chests_scenario.py
    cd output/mm9_rework/scenario_run && ../../../build/game/openyamm --world mm9 \\
        --headless-run-scenario ../../../level_generation/projects/mm9r_isleofashes/chests.yml --scenario-no-color
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))
import convert  # noqa: E402

EYE = 176
DISTANCE = 120


def main() -> int:
    native = convert.parse_odm_file(convert.review_root.mirror_path(Path("worlds/mm9/maps") / convert.MAP))["payload"]
    heights = np.array(native["height_map"], dtype=np.float64).reshape(convert.GRID, convert.GRID) * 32
    scene = json.loads((convert.SOURCE / f"{convert.STEM}.scene.yml").read_text())
    models = {b["name"]: b for b in native["bmodels"]}
    steps = [{"new_game_flow": {"start_map": convert.MAP}}]
    for record in scene["loot_containers"]:
        bmodel = models[f"BMODEL_chest_{record['source_object_index']}"]
        low, high = bmodel["bounds_min"], bmodel["bounds_max"]
        centre = np.array([(low[k] + high[k]) / 2 for k in ("x", "y", "z")])
        x, y = centre[0], centre[1] - DISTANCE                       # stand to the south, facing north
        z = convert.ground_at(heights, x, y)
        pitch = math.atan2(centre[2] - (z + EYE), DISTANCE)
        steps += [{"set_pose": {"map": convert.MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)),
                                "yaw": round(math.pi / 2, 4), "pitch": round(pitch, 4)}},
                  {"press_interact": {}},
                  {"assert": {"chest_opened": {"chest_id": record["container_id"]}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    document = {"id": "mm9r.isleofashes.chests", "world": "mm9", "mode": "faithful", "steps": steps}
    path = PROJECT / "chests.yml"
    path.write_text("# The converted MM9 chests open from in front of their models. Written by "
                    "make_chests_scenario.py.\n" + yaml.safe_dump(document, sort_keys=False))
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
