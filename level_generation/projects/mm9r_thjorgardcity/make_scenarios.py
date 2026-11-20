#!/usr/bin/env python3
"""
Write the Thjorgard City scenarios from the built map (work/doors.json, work/build_report.json, the runtime scene,
props.json):

    scenario_doors_exits.yml   the general store's double door stops the party, opens on its click and the party
                               walks in; a facade door stays locked; the three exits (the docks and the west gate to
                               the Thjorgard wilderness, the east gate to the Arena) raise their transitions
    scenario_shops.yml         walk-in shops by real clicks: the magic shop (Geirrod A'Ghrie, RUDE 12) and Sitheag
                               A'Mor's shop (RUDE 10) open their dialogues and "Let us see what you have." opens the shop
    scenario_scripted.yml      the location key 1025, shop hours (5017), the town portal altar (5011), a letter, Sven's
                               clans (178) and Thjorad Mine reward (163), Harris Willington undamageable (233 never given), the bank orb

The city has no treasure chests (MM9 places none: README).

    scenario_thorolf.yml       NPC378.scr: nobody comes with key 106 alone or 83 with 84; with 83 Thorolf runs up
                               to the party he sees and opens RUDE 378 with no click, the other copy removed

    python3 level_generation/projects/mm9r_thjorgardcity/make_scenarios.py
    for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_thjorgardcity/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios, town_portal  # noqa: E402
from dungeon.source import SCALE, Project  # noqa: E402
import citylua  # noqa: E402

MAP = "thjorgardcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EXITS = {"Thjorgarddocks": (690, 270), "Arenaexit": (685, 0), "Thjorgardcityexit": (689, 180)}   # object, walk yaw


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.thjorgardcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


def choose(rude: int, node: int, label: str) -> dict:
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label)
    return {"select_topic": {"action_id": index, "match_label": label}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    everyone = [(p[0], p[1]) for p in actors.values()]
    events = citylua.prop_events(None)

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190, 240), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Thjorgard City (native BLV) - the general store's double door, a locked facade door, "
                                "the exits")
    steps = doc["steps"]
    store = door["StoredoorL"]
    # StoredoorL/R at LT x 736-800, z 3576 (the store's north wall, Storeportal): walk south from the street.
    sx, sy = 768 * SCALE, 3576 * SCALE
    z = floors.z(sx, sy + 300, 600)
    steps += [{"note": {"text": f"StoredoorL/R (door {store['door_id']}, event {store['event']}): shut, stops the "
                                "party, opens on its click; the party walks into the general store."}},
              {"assert": {"mechanism": {"id": store["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx, sy + 300, z + 1), 270, 0.8, (sx, sy + 40, z + 1), 60, 40),
              {"execute_event": {"id": store["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": store["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx, sy + 300, z + 1), 270, 0.8, (sx, sy - 300, z + 1), 140, 40)]
    facade = door["Door12"]
    steps += [{"note": {"text": "Door12 (a facade door, Locked, MoveDist 0): a click says it is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": facade["door_id"], "state": "closed"}}}]
    for name, (index, yaw) in EXITS.items():
        row = next(t for t in report["transitions"] if t["name"] == name and t["source"] == MAP)
        cx, cy, cz = (int(v) for v in row["centre"])
        back = {0: (-400, 0), 180: (400, 0), 270: (0, 400)}[yaw]
        ahead = {0: (200, 0), 180: (-200, 0), 270: (0, -200)}[yaw]
        start = (cx + back[0], cy + back[1])
        fz = floors.z(start[0], start[1], cz + 200)
        steps += [{"note": {"text": f"{name} (DAT object {index}) to {row.get('destination', '?')}."}},
                  scenarios.movement(MAP, (start[0], start[1], fz + 1), yaw, 0.9,
                                     (cx + ahead[0], cy + ahead[1], fz + 1), 400, 200),
                  {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": index}}},
                  {"load_map": {"map": MAP}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Thjorgard City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real clicks "
                          "and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("ShopkeeperElfFemaleB3", 12, "Let us see what you have."),
                              ("ShopkeeperElfFemaleB0", 10, "Let us see what you have.")):
        steps += [{"note": {"text": f"{name} (RUDE {rude}) in the shop: a click opens the dialogue; \"{label}\" opens "
                                    "the shop."}}]
        steps += talk(name, rude)
        steps += [choose(rude, rude, label),
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"dialog": {"active": True, "house_dialog": True}}},
                  {"press_action": {"action": "cancel_dialog"}}, {"press_action": {"action": "cancel_dialog"}},
                  {"advance_runtime": {"seconds": 0.5}}]
    scenarios.write(PROJECT / "scenario_shops.yml", doc, "make_scenarios.py")

    # --- scripted ---------------------------------------------------------------------------------------------------
    doc = header("scripted", "Thjorgard City (native BLV) - the location key, shop hours, the town portal altar, a "
                             "letter, Sven, Harris, the bank orb")
    steps = doc["steps"]
    a = scripted["actors"]
    steps += [
        {"note": {"text": "ForadWorld.scr: the location key 1025 on load; shops close (5017) from 20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(citylua.LOCATION_KEY)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": "BookLetter.scr: Prop3 (row 424) shows its text."}},
        {"execute_event": {"id": events["Prop3"]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "NPC3.scr: Sven's click with the five clans (82, 38, 51, 63, 74) gives 178 and opens RUDE 3; "
                          "his dialogue's close with Thjorad Mine done (32) pays 12 000 experience (key 163)."}},
        *[{"setup_shortcut": {"kind": "set_qbit", "id": key(k), "value": True}} for k in (*citylua.SVEN_CLAN_KEYS, 32)],
        {"interact_actor": {"actor_index": a["Sven"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 3}}},
        {"assert": {"qbit_set": [key(178)]}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(163)]}},
        {"note": {"text": "BankOrb.scr (Ragnar, RUDE 13): with the orb quest (322) and the orb row taken (330 set by "
                          "his click when the orb is carried; set here) and this bank's key 335, the close places the "
                          "orb: key 323."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(330), "value": True}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(335), "value": True}},
        {"interact_actor": {"actor_index": a["Ragnar"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 13}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(323)]}},
        {"assert": {"qbit_clear": [key(330)]}},
        {"note": {"text": "Harris Willington (DAT CanDamage 0, as in MM9): no damage reaches him, so NPC416.scr "
                          ":OnDeath's key 233 is never given (NPC3.scr :Lifesaver pays the same with or without it)."}},
        {"damage_actor": {"actor_index": a["Harris"], "amount": 100000}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_clear": [key(233)]}},
    ]
    doc["steps"] += town_portal.scenario_steps(PROJECT / "props.json", events, MAP)   # TownPortal.scr
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    # NPC378.scr: with key 83 Thorolf sees the party, runs over and talks (RUDE 378) with no click; nobody comes
    # with 106 alone or with 84 (dungeon/scenarios.py thorolf_document)
    doc = scenarios.thorolf_document(project, floors, MAP, header("thorolf", "Thorolf runs up and talks (NPC378.scr)"),
                                     scripted["actors"], actors, key)
    scenarios.write(PROJECT / "scenario_thorolf.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
