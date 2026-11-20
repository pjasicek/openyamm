#!/usr/bin/env python3
"""
Write The Arena's scenarios from the built map (work/doors.json, work/content.json, work/build_report.json, props.json):

    scenario_doors_exits.yml   the front door raises ExitTrigger0; the shut arena door stops the party, opens on a real
                               click and the party walks through; the pens open on their clicks
    scenario_fight.yml         a Page fight by real clicks on the Arena Master (RUDE 430): the opponents come out when
                               the party passes PlayerInTheHouse, the doors lock behind it, the last kill unlocks them,
                               "We won!" pays the purse and closes the arena for the day
    scenario_lord.yml          the third labor (key 214): a Lord fight won gives key 217
    scenario_bout.yml          a bet: the wager is taken, a real click on a betting slip picks the contestant, the bout
                               spawns, the other contestant dies, "We won!" pays the bet
    scenario_sven.yml          Jarl Sven's plot (key 230): the arena door brings Sven's double and Byri out; Byri's talk
                               (RUDE 245) gives key 231 and he runs off; the double's talk (RUDE 428) by a click

    python3 level_generation/projects/mm9r_thearena/make_scenarios.py
    for s in doors_exits fight lord bout sven; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \\
        --headless-run-scenario level_generation/projects/mm9r_thearena/scenario_$s.yml --scenario-no-color; done
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
from dungeon import scenarios  # noqa: E402
from dungeon.source import Project  # noqa: E402
import convert  # noqa: E402

MAP = "thearena.blv"
EXIT_OBJECT = 7                     # ExitTrigger0 (DAT object index; its map_transitions.txt row)
RUDE = PROJECT.parents[2] / "mm9/extracted/RUDE/RUDE"
FIRST_SPAWN = 5                     # the five placed NPCs come first; summoned monsters follow in order


def header(name: str, title: str) -> dict:
    return {"id": f"mm9r.thearena_{name}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}]}


def key(raw: int) -> int:
    return 90000 + raw


def choose(rude: int, node: int, label: str, slot: int | None = None) -> dict:
    """The dialogue row `label` of a RUDE node (its action id is the row's place in the file); `slot` picks one of
    two rows with the same label (430's two "We won!": slot 5 for a bet, 6 for a fight)."""
    with open(RUDE / f"NPC{rude}.rude", newline="", encoding="latin-1") as stream:
        rows = list(csv.reader(stream))
    index = next(k for k, row in enumerate(rows) if int(row[1]) == node and row[3] == label
                 and (slot is None or int(row[2]) == slot))
    return {"select_topic": {"action_id": index, "match_label": label}}


def var(name: str, value: int) -> dict:
    return {"assert": {"named_map_var_changed": {"name": name, "current": value}}}


def main() -> int:
    project = Project.load(PROJECT, install=False)
    floors = scenarios.Floors(project)
    movers = json.loads((PROJECT / "work/doors.json").read_text())
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    scene = json.loads((PROJECT / f"work/runtime/{project.stem}.scene.yml").read_text())
    props = {e["anchor"]: e for e in json.loads((PROJECT / "work/content.json").read_text())["decorations"]}
    door = {m["node"][5:]: m for m in movers}
    start = report["starts"][0]["position"]
    scripted = report["scripted"]
    P = scripted["points"]
    actors = {name: tuple(scene["initial_state"]["actors"][index]["position"][k] for k in "xyz")
              for name, index in scripted["actors"].items()}
    actor_index = scripted["actors"]
    master = actors["ShopkeeperElfMaleB0"]

    def talk_master() -> list:
        """A real click on the Arena Master across his counter (the bars are an untouchable cut-out)."""
        x, y, z = master
        return [{"set_pose": {"map": MAP, "x": x + 230, "y": y, "z": 1, "yaw": round(math.pi, 4), "pitch": -0.05}},
                {"advance_runtime": {"seconds": 0.2}},
                {"press_interact": {}},
                {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": 430}}}]

    def click(pose_xy, yaw, pitch=0.0, z=1) -> list:
        return [{"set_pose": {"map": MAP, "x": int(pose_xy[0]), "y": int(pose_xy[1]), "z": z, "yaw": round(yaw, 4),
                              "pitch": pitch}},
                {"advance_runtime": {"seconds": 0.2}},
                {"press_interact": {}}]

    arena = door["RotatingDoor0"]["door_id"], door["RotatingDoor1"]["door_id"]
    west, east = door["RotatingDoor2"]["door_id"], door["RotatingDoor4"]["door_id"]
    door_y = -1536                       # the arena doors at LT z -600
    enter = [scenarios.movement(MAP, (0, -2000, 1), 90, 0.9, (0, -1310, 1), 120, 20),
             {"advance_runtime": {"seconds": 1}}]

    # --- doors and exits ------------------------------------------------------------------------------------------
    doc = header("doors_exits", "The Arena (native BLV) - the front door, the arena door, the pens")
    steps = doc["steps"]
    steps += [{"note": {"text": "ExitTrigger0 (DAT object 7): the front door to Thjorgard City, just south of the start."}},
              scenarios.movement(MAP, start, 270, 0.8, (start[0], start[1] - 300, start[2]), 400, 200),
              {"assert": {"map_transition_requested": {"source_kind": "mm9_exit_trigger", "source_id": EXIT_OBJECT}}},
              {"load_map": {"map": MAP}},
              {"note": {"text": "The arena's double door (RotatingDoor0/1) is shut and stops the party; a real click opens "
                                "both leaves; the party walks into the arena."}},
              {"assert": {"mechanism": {"id": arena[0], "state": "closed"}}},
              scenarios.movement(MAP, (0, -2000, 1), 90, 0.9, (0, door_y - 60, 1), 80, 20),
              *click((0, door_y - 250), math.pi / 2),
              {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"mechanism": {"id": arena[0], "state": "open"}}},
              {"assert": {"mechanism": {"id": arena[1], "state": "open"}}},
              scenarios.movement(MAP, (0, -2000, 1), 90, 1.4, (0, -930, 1), 160, 20),
              {"note": {"text": "The pens (RotatingDoor2/3 west, 4/5 east): shut, a real click slides each pair apart."}},
              {"assert": {"mechanism": {"id": west, "state": "closed"}}},
              *click((-1200, 0), math.pi),
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": west, "state": "open"}}},
              *click((1200, 0), 0.0),
              {"advance_runtime": {"seconds": 3}},
              {"assert": {"mechanism": {"id": east, "state": "open"}}}]
    scenarios.write(PROJECT / "scenario_doors_exits.yml", doc, "make_scenarios.py")

    # --- a Page fight ---------------------------------------------------------------------------------------------
    doc = header("fight", "The Arena (native BLV) - a Page fight: RUDE 430 by clicks, the pens, the locks, the purse")
    steps = doc["steps"]
    steps += [{"console": {"line": "gold set 1000"}},
              *talk_master(),
              choose(430, 430, "We're here to fight."),
              choose(430, 1, "We'd like to fight at the Page level."),
              {"assert": {"qbit_set": [key(convert.KEY_PAGE)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"note": {"text": "Arena.scr :OnRude -> :FightCheck -> ArenaFight.scr :OnPage: opponents drawn, key 1011, the "
                                "party awaited (WaitingForPlayer)."}},
              var("Waiting", 1),
              {"assert": {"qbit_set": [key(convert.KEY_BOUT)]}},
              {"note": {"text": "Into the arena: the door opens on a click; past PlayerInTheHouse the doors shut and lock "
                                "behind the party and the pens open."}},
              *click((0, door_y - 250), math.pi / 2),
              {"advance_runtime": {"seconds": 2.5}},
              *enter,
              var("Waiting", 0),
              var("FightGroup", convert.GROUP_SPAWN_BASE + 1),
              {"assert": {"actor_visible": {"actor_index": FIRST_SPAWN, "hostile_to_party": True, "report_state": True}}},
              {"advance_runtime": {"seconds": 4}},
              {"assert": {"mechanism": {"id": arena[0], "state": "closed"}}},
              {"assert": {"mechanism": {"id": east, "state": "open"}}},
              {"assert": {"mechanism": {"id": west, "state": "open"}}},
              {"note": {"text": "The locked arena door does not open on a click from inside."}},
              *click((0, door_y + 250), -math.pi / 2),
              {"advance_runtime": {"seconds": 2}},
              {"assert": {"mechanism": {"id": arena[0], "state": "closed"}}},
              {"note": {"text": "Every opponent down (ArenaFight.scr :OnDead): key 1020, the door unlocked (one or two "
                                "opponents at Page: every living actor is hit; the NPCs are hidden)."}}]
    steps += [*[{"damage_actor": {"actor_index": FIRST_SPAWN + k, "amount": 100000, "skip_dead": True}} for k in range(5)],
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_FIGHT_WON)]}},
              var("FightGroup", 0),
              *click((0, door_y + 250), -math.pi / 2),
              {"advance_runtime": {"seconds": 2.5}},
              {"assert": {"mechanism": {"id": arena[0], "state": "open"}}},
              {"note": {"text": "\"We won!\" (row 430/6, needs 1020): Arena.scr :FightWin pays the purse, takes 1020, gives "
                                "1009 (no more fights today)."}},
              {"console": {"line": "gold set 0"}},
              *talk_master(),
              choose(430, 430, "We won!", 6),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_set": [key(convert.KEY_DONE_TODAY)]}},
              {"assert": {"qbit_clear": [key(convert.KEY_FIGHT_WON)]}},
              {"console": {"line": "gold get"}}]
    scenarios.write(PROJECT / "scenario_fight.yml", doc, "make_scenarios.py")

    # --- the Lord fight for the third labor -----------------------------------------------------------------------
    doc = header("lord", "The Arena (native BLV) - the third labor: a Lord fight won with key 214 gives key 217")
    steps = doc["steps"]
    steps += [{"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_LABOR), "value": True}},
              *talk_master(),
              choose(430, 430, "We're here to fight."),
              choose(430, 1, "We're the best there is!  Send us in at Lord!"),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              var("Lord", 1),
              *click((0, door_y - 250), math.pi / 2),
              {"advance_runtime": {"seconds": 2.5}},
              *enter,
              var("FightGroup", convert.GROUP_SPAWN_BASE + 1),
              *[{"damage_actor": {"actor_index": FIRST_SPAWN + k, "amount": 1000000, "skip_dead": True}} for k in range(5)],
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_FIGHT_WON)]}},
              *click((0, door_y + 250), -math.pi / 2),
              {"advance_runtime": {"seconds": 2.5}},
              *talk_master(),
              choose(430, 430, "We won!", 6),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_set": [key(convert.KEY_LABOR_DONE), key(convert.KEY_DONE_TODAY)]}}]
    scenarios.write(PROJECT / "scenario_lord.yml", doc, "make_scenarios.py")

    # --- a bet on a bout ------------------------------------------------------------------------------------------
    slip = props["BetSlipA"]["position"]
    doc = header("bout", "The Arena (native BLV) - a bet: the wager, a betting slip, the bout, the winnings")
    steps = doc["steps"]
    steps += [{"console": {"line": "gold set 1000"}},
              *talk_master(),
              choose(430, 430, "We'd like to place a bet."),
              choose(430, 10, "We'd like to wager 50 gold"),
              {"assert": {"qbit_set": [key(convert.KEY_BETTING), key(1012)]}},
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"note": {"text": "Arena.scr :OnBet2: the 50 gold are taken, the doors locked."}},
              {"assert": {"gold": 950}},
              var("BetAmount", 50),
              {"note": {"text": "A real click on the slip at Marker3 (ArenaMini.scr :OnUse): the bet is on monster A; after "
                                "3 s Arena.scr :OnWatch spawns A in the east pen and B in the west pen."}},
              *click((slip[0] + 120, slip[1]), math.pi, round(-math.atan2(161 - (slip[2] + 2), 120), 4)),
              {"assert": {"qbit_set": [key(convert.KEY_PICKED)]}},
              var("BetOn", 1),
              {"note": {"text": "Up to the stands to watch (\"Go up the stairs behind you to reach the viewing area\")."}},
              {"set_pose": {"map": MAP, "x": 410, "y": -2089, "z": 656, "yaw": round(math.pi / 2, 4), "pitch": -0.3}},
              {"advance_runtime": {"seconds": 9}},
              var("BoutGroupA", convert.GROUP_SPAWN_BASE + 1),
              var("BoutGroupB", convert.GROUP_SPAWN_BASE + 2),
              {"assert": {"actor_visible": {"actor_index": FIRST_SPAWN, "hostile_to_party": False, "report_state": True}}},
              {"assert": {"actor_visible": {"actor_index": FIRST_SPAWN + 1, "hostile_to_party": False,
                                            "report_state": True}}},
              {"assert": {"mechanism": {"id": east, "state": "open"}}},
              {"advance_runtime": {"seconds": 10}},
              {"assert": {"actor_visible": {"actor_index": FIRST_SPAWN, "report_state": True}}},
              {"assert": {"actor_visible": {"actor_index": FIRST_SPAWN + 1, "report_state": True}}},
              {"note": {"text": "B falls (here by a hit): A wins, the bet on A pays (key 1018); after 20 s the winner leaves "
                                "and the next pair is drawn."}},
              {"damage_actor": {"actor_index": FIRST_SPAWN + 1, "amount": 1000000}},
              {"advance_runtime": {"seconds": 1}},
              {"assert": {"qbit_set": [key(convert.KEY_WON_BET)]}},
              {"advance_runtime": {"seconds": 26}},
              var("Bouts", 2),
              {"assert": {"qbit_clear": [key(convert.KEY_BOUT), key(convert.KEY_WATCH)]}},
              *talk_master(),
              choose(430, 430, "We won!", 5),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_clear": [key(convert.KEY_WON_BET)]}},
              {"console": {"line": "gold get"}}]
    scenarios.write(PROJECT / "scenario_bout.yml", doc, "make_scenarios.py")

    # --- Jarl Sven's plot -----------------------------------------------------------------------------------------
    doc = header("sven", "The Arena (native BLV) - Sven's double, his soldiers and Byri the Scarred (keys 230 / 231)")
    steps = doc["steps"]
    byri = actor_index["CommonerHuman2MaleB0"]
    sven = actor_index["SvenArena"]
    steps += [{"assert": {"actor_visible": {"actor_index": byri, "hidden": True}}},
              {"assert": {"actor_visible": {"actor_index": sven, "hidden": True}}},
              {"setup_shortcut": {"kind": "set_qbit", "id": key(convert.KEY_SVEN_PLOT), "value": True}},
              {"note": {"text": "With Sven's plan (230) the Arena Master's fights are off (Arena.scr :OnRude :Reset)."}},
              *talk_master(),
              choose(430, 430, "We're here to fight."),
              choose(430, 1, "We'd like to fight at the Page level."),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_clear": [key(convert.KEY_PAGE)]}},
              var("Waiting", 0),
              {"note": {"text": "Opening the arena door (RotatingDoor0's OpenTrigger: SvenArena Walk): Sven's double and his "
                                "soldiers in the box, the east pen opens and Byri comes out to the middle."}},
              *click((0, door_y - 250), math.pi / 2),
              {"advance_runtime": {"seconds": 7}},
              {"assert": {"actor_visible": {"actor_index": sven, "hidden": False, "report_state": True,
                                            "near": {"x": P["Sven0"][0], "y": P["Sven0"][1], "max_distance": 120}}}},
              {"assert": {"actor_visible": {"actor_index": byri, "hidden": False, "report_state": True,
                                            "near": {"x": P["Marker2"][0], "y": P["Marker2"][1], "max_distance": 120}}}},
              {"assert": {"mechanism": {"id": east, "state": "open"}}},
              {"note": {"text": "Byri's talk (RUDE 245) by a click: the letter makes him talk; key 231; he runs off."}},
              *click((0, -260), math.pi / 2, -0.05),
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": 245}}},
              choose(245, 245, "We're not going to allow you to murder Sven."),
              choose(245, 1, "This letter."),
              choose(245, 202, "A dying messenger."),
              {"assert": {"qbit_set": [key(convert.KEY_SVEN_SAVED)]}},
              choose(245, 2, "I'm sure we could come to an arrangement."),
              choose(245, 3, "Who put you up to this?"),
              choose(245, 4, "Why did he want Sven dead?"),
              choose(245, 5, "Sven is going to find out about this.  We suggest leaving town."),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 5}},
              {"assert": {"actor_visible": {"actor_index": byri, "hidden": True}}},
              {"assert": {"mechanism": {"id": arena[0], "state": "open"}}},
              {"note": {"text": "Sven's double in the box (SvenArena.scr :OnUse key 1034, RUDE 428)."}},
              *click((P["Sven0"][0], P["Sven0"][1] - 230), math.pi / 2, -0.05, z=P["Sven0"][2]),
              {"assert": {"actor_dialog_started": {"kind": "mm9_rude", "source_id": 428}}},
              {"assert": {"qbit_set": [key(convert.KEY_DOUBLE)]}},
              choose(428, 428, "You're Sven's double?"),
              {"press_action": {"action": "cancel_dialog"}},
              {"advance_runtime": {"seconds": 0.5}},
              {"assert": {"qbit_clear": [key(convert.KEY_DOUBLE)]}}]
    scenarios.write(PROJECT / "scenario_sven.yml", doc, "make_scenarios.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
