#!/usr/bin/env python3
"""
Write the Guberland City scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json):

    scenario_doors_exits.yml   the bank's double door stops the party, opens on its click and the party walks in; a
                               facade door stays locked; a quarter gate opens when the party walks up to it and the
                               party walks through; the exit raises its transition to the Guberland wilderness
    scenario_shops.yml         walk-in shops by real clicks: Skallagrim Hrafnssen (RUDE 135) and Trian A'Lyrae
                               (RUDE 137) open their dialogues and their service rows open the shops
    scenario_scripted.yml      the location key 1028, shop hours (5017), the town portal altar (5014), a letter,
                               Markel's clans (178) by his click and his Dook reward (168) on the close, the bank's
                               orb (326), the apothecary's potion (209 two hours after 208; 373 unlocks Nurtigan's
                               sickroom door), the tavern keeper's keg (306), Markel's awards (a Stuffed Dragon
                               taken only once he is dead, 40; with Yrsa's errand, 93, it gives 94)

The city has no chest (MM9 places no TreasureChest or TreasureBag here).

    scenario_thorolf.yml       NPC378.scr: nobody comes with key 106 alone or 83 with 84; with 83 Thorolf runs up
                               to the party he sees and opens RUDE 378 with no click, the other copy removed

    python3 level_generation/projects/mm9r_guberlandcity/make_scenarios.py
    for s in doors_exits shops scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_guberlandcity/scenario_$s.yml --scenario-no-color; done
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

MAP = "guberlandcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EXIT = 185                                   # DAT object index of ExitTrigger0


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.guberlandcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
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
    o = scripted["objects"]

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Guberland City (native BLV) - the bank's double door, a locked facade door, a quarter "
                                "gate, the exit")
    steps = doc["steps"]
    bank = door["BankL"]
    # BankL/R at LT x 264, z -1680/-1776 (the bank's west wall): walk east from the avenue into the bank.
    sx, sy = 264 * SCALE, -1728 * SCALE
    z = floors.z(sx - 300, sy, 400)
    steps += [{"note": {"text": f"BankL/R (doors {bank['door_id']}, event {bank['event']}): shut, stops the party, "
                                "opens on its click; the party walks into the bank."}},
              {"assert": {"mechanism": {"id": bank["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx - 40, sy, z + 1), 60, 40),
              {"execute_event": {"id": bank["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": bank["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx - 300, sy, z + 1), 0, 0.8, (sx + 300, sy, z + 1), 140, 40)]
    facade = door["Door2"]
    steps += [{"note": {"text": "Door2 (a facade door, Locked, MoveDist 0): a click says it is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": facade["door_id"], "state": "closed"}}}]
    # Gate6 (LT x -64, z -1728; leaves slide along z): from the north avenue into the east quarter. Its trigger box
    # spans LT x -192..64: the party steps into it, the poll opens the gate, the party walks through.
    gate = door["Gate6L"]
    gx, gy = -64 * SCALE, -1728 * SCALE
    gz = floors.z(gx - 300, gy, 400)
    steps += [{"note": {"text": f"Gate6L/R (doors {gate['door_id']}): shut; the party walks up to it (into "
                                "Gate6trigger's box), the gate opens, the party walks through into the east quarter."}},
              {"assert": {"mechanism": {"id": gate["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (gx - 300, gy, gz + 1), 0, 0.6, (gx - 40, gy, gz + 1), 300, 40),
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"mechanism": {"id": gate["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (gx - 300, gy, gz + 1), 0, 1.0, (gx + 400, gy, gz + 1), 200, 40)]
    row = next(t for t in report["transitions"] if t["name"] == "ExitTrigger0" and t["source"] == MAP)
    cx, cy, cz = (int(v) for v in row["centre"])
    a, b = (cx, cy - 450), (cx, cy + 200)
    fz = floors.z(a[0], a[1], cz + 200)
    steps += [{"note": {"text": f"ExitTrigger0 (DAT object {EXIT}): out of the city gate to the Guberland wilderness."}},
              scenarios.movement(MAP, (a[0], a[1], fz + 1), 90, 0.9, (b[0], b[1], fz + 1), 400, 200),
              {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT}}},
              {"load_map": {"map": MAP}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Guberland City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real "
                          "clicks and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("ShopkeeperHuman2MaleA5", 135, "We'd like to see your wares."),
                              ("ShopkeeperHuman2MaleA6", 137, "We'd like to see what you have.")):
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
    doc = header("scripted", "Guberland City (native BLV) - location key, shop hours, the altar, a letter, Markel, the "
                             "bank orb, the apothecary's potion and Nurtigan's door, the keg")
    steps = doc["steps"]
    a = scripted["actors"]
    sick = door[citylua.SICKROOM_DOOR]
    steps += [
        {"note": {"text": "ForadWorld.scr: the location key 1028 on load; shops close (5017) from 20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(citylua.LOCATION_KEY)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": "BookLetter.scr: Prop1 (row 569, the Guberland Players' bill) shows its text."}},
        {"execute_event": {"id": events["Prop1"]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "NPC127.scr: Markel's click with the five clans (82, 38, 51, 34, 74) gives 178 and opens "
                          "RUDE 127; his dialogue's close with the Dook beaten (66) pays 40 000 experience (key 168)."}},
        *[{"setup_shortcut": {"kind": "set_qbit", "id": key(k), "value": True}}
          for k in (*citylua.MARKEL_CLAN_KEYS, 66)],
        {"interact_actor": {"actor_index": a["MarkeltheGreat0"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 127}}},
        {"assert": {"qbit_set": [key(178)]}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(168)]}},
        {"note": {"text": "BankOrb.scr (Ottar, RUDE 140): with the orb row taken (330, set by his click when the orb is "
                          "carried; set here) and this bank's key 332, the close places the orb: key 326."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(330), "value": True}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(citylua.BANK_KEY), "value": True}},
        {"interact_actor": {"actor_index": a["ShopkeeperHuman2MaleA7"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 140}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(citylua.BANK_KEY2)]}},
        {"assert": {"qbit_clear": [key(330)]}},
        {"note": {"text": "NPC141.scr: the tavern keeper's close with the keg sold (304) gives 306."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(304), "value": True}},
        {"interact_actor": {"actor_index": a["ShopkeeperHalfOrcFemaleA"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 141}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(306)]}},
        {"note": {"text": f"{citylua.SICKROOM_DOOR} (Nurtigan's sickroom, Locked): a click says it is locked."}},
        {"execute_event": {"id": citylua.EV_SICKROOM}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"mechanism": {"id": sick["door_id"], "state": "closed"}}},
        {"note": {"text": "NPC142.scr (Skarphedinn, RUDE 142): the close with the potion ordered (208) starts the "
                          "two-hour wait: key 209 two game hours later; with 210 it hands over the potion (key 373), "
                          "which unlocks the sickroom: its click now opens it."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(208), "value": True}},
        {"interact_actor": {"actor_index": a["ShopkeeperHuman2MaleA8"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 142}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_clear": [key(209)]}},
        {"advance_game_time": {"hours": 2}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(209)]}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(210), "value": True}},
        {"interact_actor": {"actor_index": a["ShopkeeperHuman2MaleA8"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"press_action": {"action": "cancel_dialog"}},
        {"advance_runtime": {"seconds": 1}},
        {"assert": {"qbit_set": [key(373)]}},
        {"execute_event": {"id": citylua.EV_SICKROOM}},
        {"advance_runtime": {"seconds": 3}},
        {"assert": {"mechanism": {"id": sick["door_id"], "state": "open"}}},
        {"note": {"text": "Markel's awards (Prize0-5, world items, refused while Markel lives): with him dead (40) and "
                          "Yrsa's errand (93) one is taken: the Stuffed Dragon and key 94, the prize won."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(40), "value": True}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(93), "value": True}},
        {"advance_runtime": {"seconds": 0.2}},
        *scenarios.pick_up_steps(floors, MAP, scene, "Prize2", facing_degrees=180),   # the hall is south
        {"advance_runtime": {"seconds": 0.5}},
        {"assert": {"qbit_set": [key(94)]}},
        {"assert": {"inventory_any_member": [{"item_id": 10395, "count": 1}]}},
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
