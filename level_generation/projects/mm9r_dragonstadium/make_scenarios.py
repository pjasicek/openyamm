#!/usr/bin/env python3
"""
Write the Dragon Stadium scenarios from the built map (work/content.json, work/build_report.json, props.json):

    scenario_doors_exits.yml   the exit to Lindisfarne (a walk from the start into ExitTrigger0); pillar p1 stops a walk,
                               a real click on its base breaks all seven levels and the party walks through where it
                               stood; a real click on p3's level 2 breaks levels 2-7 and leaves the base
    scenario_chests.yml        both chests open from in front of their models (interact)
    scenario_scripted.yml      Dragon.scr: the Dragon King is hidden until the party walks into DragonTrigger's box,
                               then shows and wakes; 45 s later two Winged Mutants appear (:SpawnMutants); killed, he
                               gives key 472 and item 577 and the spawns stop; he has not moved (immobile)

    python3 level_generation/projects/mm9r_dragonstadium/make_scenarios.py
    for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_dragonstadium/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import ROOT, SCALE, Project  # noqa: E402
import convert  # noqa: E402

MAP = "dragonstadium.blv"
EYE = 160
EXIT_OBJECT = 33                     # ExitTrigger0's DAT object index


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.dragonstadium_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def pose(x, y, z, yaw_radians, pitch=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": int(round(x)), "y": int(round(y)), "z": int(round(z)) + 1,
                         "yaw": round(yaw_radians, 4), "pitch": round(pitch, 4)}}


def click_pose(floors, target, outward_xy, distance) -> dict:
    """Stand `distance` out from a face centre (native) along its outward plan direction, looking at the centre."""
    x, y = target[0] + outward_xy[0] * distance, target[1] + outward_xy[1] * distance
    z = floors.z(x, y, target[2] + 200)
    return pose(x, y, z, math.atan2(target[1] - y, target[0] - x),
                math.atan2(target[2] - (z + EYE), math.dist((x, y), target[:2])))


def var(name: str, value: int) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    start = report["starts"][0]["position"]
    # ExitTrigger0's row in the review root's table (the build report lists only rows a run changed)
    table = (ROOT / "output/mm9_rework/assets_dev/worlds/mm9/data_tables/map_transitions.txt").read_text(encoding="latin-1")
    exit_row = next(line.split("\t") for line in table.splitlines() if line.startswith("mm9:transition/dragonstadium/33\t"))
    exit_centre = [float(v) for v in exit_row[6:9]]

    # --- the exit and the pillars ---------------------------------------------------------------------------------
    doc = header("doors_exits", "Dragon Stadium (native BLV) - the exit to Lindisfarne, the pillars break on a click")
    steps = doc["steps"]
    yaw = math.degrees(math.atan2(exit_centre[1] - start[1], exit_centre[0] - start[0])) % 360
    distance = math.dist(start[:2], exit_centre[:2])
    steps += [{"note": {"text": "ExitTrigger0 (to Lindisfarne, DragonStatiumExit; AskPlayer): a walk from the start "
                                f"down the tunnel into its volume (DAT object {EXIT_OBJECT})."}},
              scenarios.movement(MAP, start, yaw, round(distance / scenarios.WALK + 0.6, 2), exit_centre[:2] + [start[2]],
                                 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}}]
    # p1: level 1 is a rock mound (LT x -128..512, z -992..-128, y -64..128; 45-degree slopes the party walks up, a flat
    # top at LT y 128 = native 328); level 2 is the column on it (LT x 64..384, z -736..-384). The party stands on the
    # mound's west slope and walks east into the column's upright west face (native x 164; its south faces lean back
    # 15 degrees and let the party about 240 units into their foot: README, Checks).
    top_z = 128 * SCALE
    west = (40, -1430)
    floor_south = -992 * SCALE - 240             # the arena floor south of the mound
    x = 224 * SCALE
    z = floors.z(x, floor_south, 400)
    through = -300 * SCALE                       # north of where the column stood
    steps += [{"note": {"text": "Pillar p1 standing: a walk east on its mound stops at the column (p1 level 2)."}},
              var("Pillar0_1", 0),
              scenarios.movement(MAP, (west[0], west[1], top_z + 1), 0, 1.0, (127, west[1], top_z + 1), 60, 200),
              # the mound's south-west slope (BLV face centre (410, -2021, 164), plan normal (-0.6, -0.8))
              {"note": {"text": "A real click on the mound (p1 level 1) breaks it and every level over it "
                                "(DeathTriggerTarget chain)."}},
              click_pose(floors, (410, -2021, 164), (-0.6, -0.8), 330),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.5}},
              *[var(f"Pillar0_{k}", 1) for k in convert.LEVELS],
              {"note": {"text": "The same walk east now crosses where the column stood (its faces are untouchable)."}},
              scenarios.movement(MAP, (west[0], west[1], top_z + 1), 0, 1.0, (west[0] + 768, west[1], -163), 150, 400),
              {"note": {"text": "The party walks on the arena floor north through where the mound stood."}},
              scenarios.movement(MAP, (x, floor_south, z + 1), 90, round((through - floor_south) / scenarios.WALK, 2),
                                 (x, through, z + 1), 120, 80)]
    # p3 level 2 stands on p3's plinth (level 1: LT y -64..128, z 0..864): the party stands on the plinth's top, south
    # of level 2 (LT z 224 -> native y 573), and clicks it.
    x3 = (1728 + 2080) / 2 * SCALE
    y3 = 224 * SCALE - 220
    z3 = 128 * SCALE
    steps += [{"note": {"text": "A real click on p3 level 2 (from p3's plinth) breaks levels 2-7; the plinth stays."}},
              pose(x3, y3, z3, math.pi / 2, math.atan2(288 * SCALE - (z3 + EYE), 220)),
              {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}}, {"advance_runtime": {"seconds": 0.5}},
              var("Pillar2_1", 0), *[var(f"Pillar2_{k}", 1) for k in range(2, 8)],
              *[var(f"Pillar1_{k}", 0) for k in convert.LEVELS]]
    # p2 by damage (the scene destructibles: 200 hit points a level, level 7 TriggerDestroyOnly)
    p2 = [report["scripted"]["destructible_ids"][convert.pillar_name("p2", k)] for k in convert.LEVELS]
    steps += [{"note": {"text": "p2 by weapon damage: 199 leave level 1 standing; level 7 takes none (TriggerDestroyOnly "
                                "is broken only by the chain); one more point breaks level 1 and its death chain brings "
                                "down levels 2-7."}},
              {"console": {"line": f"destructible {p2[0]} damage 199", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 0.5}}, var("Pillar1_1", 0),
              {"console": {"line": f"destructible {p2[0]} damage 1", "expect_contains": "damage"}},
              {"advance_runtime": {"seconds": 1.0}}, *[var(f"Pillar1_{k}", 1) for k in convert.LEVELS]]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- chests ---------------------------------------------------------------------------------------------------
    doc = header("chests", "Dragon Stadium (native BLV) - both chests open from in front of them")
    doc["steps"] += scenarios.chest_steps(floors, MAP, content["chests"], props)
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- the Dragon King ------------------------------------------------------------------------------------------
    doc = header("scripted", "Dragon Stadium (native BLV) - Dragon.scr: hidden until the trigger, mutants, the reward")
    steps = doc["steps"]
    dragon = report["scripted"]["dragon_index"]
    box = report["scripted"]["trigger_box"]
    actor = next(a for a in json.loads((PROJECT / "work/runtime/dragonstadium.scene.yml").read_text())
                 ["initial_state"]["actors"] if a["actor_index"] == dragon)
    at = actor["position"]
    beyond = box[1][1] + 300                     # north of the box, in the arena's mouth
    zb = floors.z(start[0], beyond, 400)
    # out of the dragon's sight: up the side tunnel (LT 2 450, -2 900)
    hx, hy = 2450 * SCALE, -2900 * SCALE
    hz = floors.z(hx, hy, 900)
    steps += [{"note": {"text": "Dragon.scr ScriptParams 1 (:HideSetup): the Dragon King is not there until the trigger."}},
              {"assert": {"actor_visible": {"actor_index": dragon, "hidden": True}}},
              var("DragonAwake", 0),
              {"note": {"text": "The party walks from the start up the tunnel into DragonTrigger's box (polled)."}},
              scenarios.movement(MAP, start, 90, round((beyond - start[1]) / scenarios.WALK, 2),
                                 (start[0], beyond, zb + 1), 400, 200),
              {"advance_runtime": {"seconds": 0.6}},
              var("DragonAwake", 1),
              {"assert": {"actor_visible": {"actor_index": dragon, "hidden": False}}},
              {"note": {"text": ":SpawnMutants 45 s after :OnTrigger: two Winged Mutants at MutantMarker0/1 (the party "
                                "waits out of his sight in the side tunnel)."}},
              pose(hx, hy, hz, math.pi),
              {"advance_runtime": {"seconds": 40}},
              var("MutantsSpawned", 0),
              {"advance_runtime": {"seconds": 6}},
              var("MutantsSpawned", 2),
              {"assert": {"actor_count": {"monster_id": report["scripted"]["mutant_row"], "min": 2}}},
              {"note": {"text": "He has not left his place (immobile: no ground walk in MM9)."}},
              {"assert": {"actor_visible": {"actor_index": dragon, "near": {"x": at["x"], "y": at["y"], "max_distance": 32}}}},
              {"note": {"text": ":OnDeath: killed by the party, key 472 (QBit 90472) and item 577 (Super Guber Award)."}},
              {"damage_actor": {"actor_index": dragon, "amount": 10000000}},
              {"advance_runtime": {"seconds": 1}},
              var("DragonDead", 1),
              {"assert": {"qbit_set": [90000 + convert.KEY_DRAGON]}},
              {"assert": {"inventory_any_member": [{"item_id": 10000 + convert.ITEM_AWARD, "count": 1}]}},
              {"note": {"text": "A dead AI's Wait timers still fire (MM9): his :SpawnMutants goes on, the next "
                                "pair 90 s after the first."}},
              {"advance_runtime": {"seconds": 95}},
              var("MutantsSpawned", 4)]
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
