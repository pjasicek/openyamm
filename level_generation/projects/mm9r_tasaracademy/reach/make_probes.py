#!/usr/bin/env python3
"""Reach probes for the Ta'Sar Academy (README, "Can the monsters reach the party"): the store room's Dagrell
(Dagrell0, actor 24) behind SecretDoor0 comes out to a party in the east corridor, in sight and out of it; control: the
same Dagrell with the secret door shut stays in (MM9's door holds it). report_state every 2 s.

    python3 level_generation/projects/mm9r_tasaracademy/reach/make_probes.py && \\
        level_generation/projects/mm9r_tasaracademy/reach/run_probes.sh
"""
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
MAP = "tasaracademy.blv"
EV_SWITCH1 = 203
DAGRELL = 24


def probe(name, steps):
    doc = {"id": f"mm9r.ta_probe_{name}", "title": name, "world": "mm9", "mode": "faithful", "tags": ["mm9", "draft"],
           "steps": [{"load_map": {"map": MAP}}] + steps}
    (HERE / f"probe_{name}.yml").write_text(yaml.safe_dump(doc, sort_keys=False))


def watch(seconds, pose=None):
    out = []
    for _ in range(int(seconds / 2)):
        if pose:
            out.append({"set_pose": dict(pose)})
        out += [{"assert": {"actor_visible": {"actor_index": DAGRELL, "report_state": True}}},
                {"advance_runtime": {"seconds": 2}}]
    return out


# in the store room (LT 2700, -200), 300 LT from the Dagrell: in sight
SEEN = {"map": MAP, "x": 6912, "y": -512, "z": 1, "yaw": 0.6, "pitch": 0}
# outside, in the east corridor in front of SecretDoor0 (LT 1906, -552): out of the store room's sight
HIDDEN = {"map": MAP, "x": 4880, "y": -1413, "z": 1, "yaw": 0.0, "pitch": 0}
open_door = [{"execute_event": {"id": EV_SWITCH1}}, {"advance_runtime": {"seconds": 2}}]
probe("dagrell_seen", open_door + [{"set_pose": SEEN}] + watch(14, SEEN))
probe("dagrell_hidden", open_door + [{"set_pose": SEEN}, {"advance_runtime": {"seconds": 3}}, {"set_pose": HIDDEN}]
      + watch(14, HIDDEN))
probe("dagrell_door_shut", [{"set_pose": SEEN}, {"advance_runtime": {"seconds": 3}}, {"set_pose": HIDDEN}]
      + watch(16, HIDDEN))
