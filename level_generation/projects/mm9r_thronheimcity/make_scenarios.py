#!/usr/bin/env python3
"""
Write the Thronheim City scenarios from the built map (work/doors.json, work/content.json, work/build_report.json,
props.json):

    scenario_doors_exits.yml   the weapon shop's double door stops the party, opens on its click and the party walks
                               in; a facade door stays locked; both exits (the east gate, the docks) raise their
                               transitions to the Thronheim wilderness
    scenario_shops.yml         walk-in shops by real clicks: the weapon smith (William the Framish, RUDE 247) and the
                               apothecary (Thakkrad Kjarssen, RUDE 255) open their dialogues and their service rows open
                               the shops; a council Jarl (a posed RUDEProp) opens his dialogue by its click event
    scenario_chests.yml        the treasure chest in the loft opens; the loft's ladder (Ladder2) climbs to it
    scenario_scripted.yml      the location key 1030, shop hours (5017), the war council at Kira's door (keys 90 and 91
                               -> 40, 184, 85, 93), Ealusaid's Black Orb reward on her dialogue's close, Kira's Shield,
                               a letter, the Desert Terror's breakout when the party walks across the prison street
    scenario_thorolf.yml       NPC378.scr: nobody comes with key 106 alone or 83 with 84; with 83 Thorolf runs up
                               to the party he sees and opens RUDE 378 with no click, the other copy removed

    python3 level_generation/projects/mm9r_thronheimcity/make_scenarios.py
    for s in doors_exits shops chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_thronheimcity/scenario_$s.yml --scenario-no-color; done
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

MAP = "thronheimcity.blv"
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
EXIT_DOCK, EXIT_GATE = 136, 956            # DAT object indices of ExitTrigger0 and ExitTrigger1


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.thronheimcity_{name}", "title": title, "world": "mm9", "mode": "faithful",
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
    content = json.loads((PROJECT / "work/content.json").read_text())
    props = {e["source_name"]: e for e in json.loads((PROJECT / "props.json").read_text())}
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    door = {m["node"][5:]: m for m in movers}
    start = report["starts"][0]["position"]
    scripted = report["scripted"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    everyone = [(p[0], p[1]) for p in actors.values()]
    events = citylua.prop_events(None)

    def talk(name: str, rude: int) -> list:
        x, y, z = actors[name]
        return [scenarios.look_at(floors, MAP, (x, y, z), 0, distances=(140, 190), height=60,
                                  avoid=[a for a in everyone if a != (x, y)]),
                {"advance_runtime": {"seconds": 0.2}}, {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": rude}}},
                {"assert": {"dialog": {"active": True, "source_id": rude}}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "Thronheim City (native BLV) - a shop's double door, a locked facade door, the exits")
    steps = doc["steps"]
    shop = door["WeaponDoor1"]
    # WeaponDoor1/2 at LT x 856, z 1860-1948 (the weapon shop's east wall): walk west from the street into the shop.
    sx, sy = 856 * SCALE, 1904 * SCALE
    z = floors.z(sx + 300, sy, 3500)
    steps += [{"note": {"text": f"WeaponDoor1/2 (doors {shop['door_id']}, event {shop['event']}): shut, stops the "
                                "party, opens on its click; the party walks into William the Framish's shop."}},
              {"assert": {"mechanism": {"id": shop["door_id"], "state": "closed"}}},
              scenarios.movement(MAP, (sx + 300, sy, z + 1), 180, 0.8, (sx + 40, sy, z + 1), 60, 40),
              {"execute_event": {"id": shop["event"]}},
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": shop["door_id"], "state": "open"}}},
              scenarios.movement(MAP, (sx + 300, sy, z + 1), 180, 0.8, (sx - 300, sy, z + 1), 140, 40)]
    facade = door["Door1"]
    steps += [{"note": {"text": "Door1 (a facade door, Locked, MoveDist 0): a click says it is locked; it stays shut."}},
              {"execute_event": {"id": citylua.EV_LOCKED}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"mechanism": {"id": facade["door_id"], "state": "closed"}}}]
    for name, index, yaw, back in (("ExitTrigger1", EXIT_GATE, 0, -500), ("ExitTrigger0", EXIT_DOCK, 90, -500)):
        row = next(t for t in report["transitions"] if t["name"] == name and t["source"] == MAP)
        cx, cy, cz = (int(v) for v in row["centre"])
        if yaw == 0:
            a, b = (cx + back, cy), (cx + 200, cy)
        else:
            a, b = (cx, cy + back), (cx, cy + 200)
        fz = floors.z(a[0], a[1], cz + 200)
        steps += [{"note": {"text": f"{name} (DAT object {index}): out of the city to the Thronheim wilderness."}},
                  scenarios.movement(MAP, (a[0], a[1], fz + 1), yaw, 0.9, (b[0], b[1], fz + 1), 400, 200),
                  {"advance_runtime": {"seconds": 0.3}},
                  {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": index}}},
                  {"load_map": {"map": MAP}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- shops ------------------------------------------------------------------------------------------------------
    doc = header("shops", "Thronheim City (native BLV) - walk-in shops: the shopkeepers' dialogues open by real "
                          "clicks and their service rows open the shops")
    steps = doc["steps"]
    steps += [{"advance_runtime": {"seconds": 1.5}}]
    for name, rude, label in (("ShopkeeperHuman2MaleA0", 247, "We'd like to look at your wares."),
                              ("ShopkeeperHuman2MaleA4", 255, "We'd like to see your wares.")):
        steps += [{"note": {"text": f"{name} (RUDE {rude}) in the shop: a click opens the dialogue; \"{label}\" opens "
                                    "the shop."}}]
        steps += talk(name, rude)
        steps += [choose(rude, rude, label),
                  {"advance_runtime": {"seconds": 0.5}},
                  {"assert": {"dialog": {"active": True, "house_dialog": True}}},
                  {"press_action": {"action": "cancel_dialog"}}, {"press_action": {"action": "cancel_dialog"}},
                  {"advance_runtime": {"seconds": 0.5}}]
    steps += [{"note": {"text": "Bjarni (a council RUDEProp, RUDE 45: an actor seated on his HD model since 2026-11-08, "
                                "rude_props.py): with keys 90 and 91 the load shows the council; a click opens his "
                                "dialogue."}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(90), "value": True}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(91), "value": True}},
              {"execute_event": {"id": citylua.EV_LOAD}},
              {"interact_actor": {"actor_index": scripted["actors"]["BjarniProp"]}}, {"advance_runtime": {"seconds": 0.3}},
              {"assert": {"dialog": {"active": True, "source_id": 45}}},
              {"press_action": {"action": "cancel_dialog"}}]
    scenarios.write(PROJECT / "scenario_shops.yml", doc, "make_scenarios.py")

    # --- chests -----------------------------------------------------------------------------------------------------
    doc = header("chests", "Thronheim City (native BLV) - the treasure chest in the loft opens; its ladder climbs")
    steps = doc["steps"]
    for chest in content["chests"]:
        entry = props[chest["anchor"]]
        steps += [scenarios.look_at(floors, MAP, (entry["x"], entry["y"], entry["z"]), entry["yaw_degrees"],
                                    distances=(120, 160), max_drop=60),
                  {"press_interact": {}},
                  {"assert": {"chest_opened": {"chest_id": chest["container_id"]}}},
                  {"press_action": {"action": "cancel_dialog"}}]
    ladder = next(entry for entry in scene["ladders"] if entry["id"] == "Ladder2")
    bx, by, bz = ladder["bottom"]
    top = [int(round(v)) for v in ladder["top_exit"]]
    pose = {"map": MAP, "x": int(round(bx)), "y": int(round(by + 70)), "z": int(round(bz)) + 1,
            "yaw_degrees": 270, "pitch": 0}
    steps += [{"note": {"text": "Ladder2: from the room under the loft up to the chest (MM9's only way up); the party "
                                "climbs to the loft's floor and walks on into the loft (z is the check)."}},
              {"movement_segment": {"input": "forward", "seconds": 6.0, "actor_collision": False, "actor_ai": False,
                                    "start": pose, "expect_stop": dict(pose, x=top[0], y=top[1], z=top[2]),
                                    "loose_tolerance": True, "tolerance_xy": 2500, "tolerance_z": 60}}]
    scenarios.write(PROJECT / "scenario_chests.yml", doc, "make_scenarios.py")

    # --- scripted ---------------------------------------------------------------------------------------------------
    doc = header("scripted", "Thronheim City (native BLV) - location key, shop hours, the war council, Ealusaid, Kira's "
                             "Shield, a letter, the Desert Terror's breakout")
    steps = doc["steps"]
    kira_door = door["KiraDoor1"]
    steps += [
        {"note": {"text": "ForadWorld.scr: the location key 1030 on load; shops close (5017) from 20:00 to 06:00."}},
        {"advance_runtime": {"seconds": 1.5}},
        {"assert": {"qbit_set": [key(1030)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_set": [key(5017)]}},
        {"advance_game_time": {"hours": 12}}, {"advance_runtime": {"seconds": 2.5}},
        {"assert": {"qbit_clear": [key(5017)]}},
        {"note": {"text": "ARGUMENT.scr: with both signatures (keys 90, 91) opening Kira's council door runs the "
                          "council's reward: keys 184, 40, 85, 93."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(90), "value": True}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(91), "value": True}},
        {"execute_event": {"id": citylua.EV_KIRA_DOOR}},
        # the reward runs inside the cinematic council_argument (167 s); a skip runs its remaining steps
        {"advance_runtime": {"seconds": 1}},
        {"lua_event": {"source": "evt.SkipCinematic()"}},
        {"advance_runtime": {"seconds": 3}},
        {"assert": {"qbit_set": [key(40), key(184), key(85), key(93)]}},
        {"assert": {"mechanism": {"id": kira_door["door_id"], "state": "open"}}},
        {"note": {"text": "NPC241.scr: Ealusaid with the Black Orb's inventor found (314): her dialogue's close gives "
                          "315 (50 000 experience, 10 000 gold)."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(314), "value": True}},
        {"interact_actor": {"actor_index": scripted["actors"]["Ealusaid"]}}, {"advance_runtime": {"seconds": 0.3}},
        {"assert": {"dialog": {"active": True, "source_id": 241}}},
        {"press_action": {"action": "cancel_dialog"}}, {"advance_runtime": {"seconds": 0.5}},
        {"assert": {"qbit_set": [key(315)]}},
        {"note": {"text": "KiraShield.scr: Kira's Shield, a world item, is taken only with the labours (214); picked up it "
                          "gives key 216."}},
        {"setup_shortcut": {"kind": "set_qbit", "id": key(214), "value": True}},
        {"advance_runtime": {"seconds": 0.2}},
        *scenarios.pick_up_steps(floors, MAP, scene, "Shield", distances=(90, 120, 160, 200)),
        {"assert": {"qbit_set": [key(216)]}},
        {"assert": {"inventory_any_member": [{"item_id": 10375, "count": 1}]}},
        {"note": {"text": "BookLetter.scr: Prop21, the letter to Wahng (row 469), shows its text."}},
        {"execute_event": {"id": events["Prop21"]}},
        {"assert": {"dialog": {"active": True}}},
        {"press_action": {"action": "cancel_dialog"}},
        {"note": {"text": "Thronheimcity_BadAss.scr: walking west across BadAssTrigger (LT x 4312) breaks the Desert "
                          "Terror out: it walks to the cell's back wall and breaks it, runs to Shmoe and kills him, and "
                          "is loose (BadAssStage 3) within the breakout's time limit."}},
    ]
    px, py = 4312 * SCALE, 96 * SCALE
    pz = floors.z(px + 400, py, 3500)
    steps += [scenarios.movement(MAP, (px + 400, py, pz + 1), 180, 2.0, (px - 1100, py, pz + 1), 800, 80),
              {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"named_map_var_changed": {"name": "BadAssOut", "current": 1}}},
              # the Terror's own walks, not the time limit's fallback (which frees it where it stands): it is loose
              # by Shmoe well before the limit; a caged actor the party cannot see still runs its script's walks
              {"advance_runtime": {"seconds": citylua.BREAKOUT_TIMEOUT - 4}},
              {"assert": {"named_map_var_changed": {"name": "BadAssStage", "current": 3}}},
              {"assert": {"actor_visible": {"actor_index": scripted["actors"]["Shmoe"], "dead": True}}},
              {"assert": {"actor_visible": {"actor_index": scripted["actors"]["BadAss"], "far": {
                  "x": actors["BadAss"][0], "y": actors["BadAss"][1], "min_distance": 300}}}},
              {"note": {"text": "Out of its cell (the wall's doorway portal) it is the town's monster: it walks "
                                "(BaseInit lifts its placement's stillness), and 6 s on the extra guard comes from "
                                "GuardSpawn1 and runs for it."}},
              {"advance_runtime": {"seconds": 12}},
              {"assert": {"actor_visible": {"actor_index": scripted["actors"]["ExtraGuard"], "far": {
                  "x": actors["ExtraGuard"][0], "y": actors["ExtraGuard"][1], "min_distance": 300}}}},
              {"note": {"text": "Thronheimcity_Guard.scr :OnDeath: the guard stream goes on after the Terror's death "
                                "(the dying guard's OnDeath fires; GuardSpawn0 is no AI): Guard1 killed after the "
                                "Terror sends a new guard from GuardSpawn0."}},
              {"damage_actor": {"actor_index": scripted["actors"]["BadAss"], "amount": 100000000}},
              {"advance_runtime": {"seconds": 1.0}},
              {"assert": {"named_map_var_changed": {"name": "BadAssDead", "current": 1}}},
              {"damage_actor": {"actor_index": scripted["actors"]["Guard1"], "amount": 100000000}},
              {"advance_runtime": {"seconds": 1.0}},
              {"assert": {"named_map_var_changed": {"name": "GuardsSent", "current": 1}}}]
    doc["steps"] += town_portal.scenario_steps(PROJECT / "props.json", events, MAP)   # TownPortal.scr
    scenarios.write(PROJECT / "scenario_scripted.yml", doc, "make_scenarios.py")
    # NPC378.scr: with key 83 Thorolf sees the party, runs over and talks (RUDE 378) with no click; nobody comes
    # with 106 alone or with 84 (dungeon/scenarios.py thorolf_document)
    # with key 83 Thorolf0 waits at NPC378.scr's Thronheim spot (citylua.THOROLF0_TARGET_LT, on the floor)
    sx, sy, sz = project.native(citylua.THOROLF0_TARGET_LT)
    start = (sx, sy, floors.z(sx, sy, sz + 40))
    doc = scenarios.thorolf_document(project, floors, MAP, header("thorolf", "Thorolf runs up and talks (NPC378.scr)"),
                                     scripted["actors"], actors, key, start)
    scenarios.write(PROJECT / "scenario_thorolf.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
