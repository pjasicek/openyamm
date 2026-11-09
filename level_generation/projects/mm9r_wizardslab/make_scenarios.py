#!/usr/bin/env python3
"""Wizard's Lab scenarios from the built map's Lua (the review root's events/maps/wizardslab.lua, written by
convert.py through citylua.py): rerun after every conversion.

  scenario_teleporters.yml  every TeleporterSwitch.scr crystal sets its station's destination and lights for 4 s;
                            the party dropped on the station takes the trip (TeleporterMulti.scr :ResetDestination
                            clears it); every destination is floor the party stands on; the closet teleporters see
                            the party.
  scenario_ritual.yml       the first arrival at DestinationPurple starts the summoning: the six apprentices in
                            chain order, the master, the Greater Demon; six apprentices dying (the demon's doing)
                            make the master banish it.

Same-map moves are applied by the frame loop, not in a headless run, so a trip is proved by its consumed
destination (Dest<station> back to 0) and each destination separately by a drop test.

    python3 level_generation/projects/mm9r_wizardslab/make_scenarios.py
    for s in teleporters ritual; do ./build/game/openyamm --asset-root output/mm9_rework/assets_dev \\
        --headless-run-scenario level_generation/projects/mm9r_wizardslab/scenario_$s.yml --scenario-no-color; done
"""
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LUA = ROOT / "output/mm9_rework/assets_dev/worlds/mm9/events/maps/wizardslab.lua"
MAP = "wizardslab.blv"
ROW_DEMON = 9242
CONJURE_SECONDS, FADE_SECONDS, BANISH_SECONDS, LIGHT_SECONDS = 2.5, 2.0, 6.0, 4.0
NEUTRAL = "DestinationWhite"        # a floor point inside no Teleporter or Trigger box
POINT = r"\{(-?\d+), (-?\d+), (-?\d+)\}"
# closet teleporter -> (its doors' click event, a door id, the doors' plane y, +1/-1: the closet's inside lies
# towards +y / -y) from work/doors.json and the DAT's Closet<k>Door models
CLOSET_DOORS = {"Teleporter1": (101, 15, 11913, -1), "Teleporter2": (102, 17, 13360, 1)}


def table(text: str, name: str) -> str:
    match = re.search(rf"^local {name} = \{{\n(.*?)^\}}", text, re.S | re.M)
    if match is None:
        sys.exit(f"{LUA}: no table {name}")
    return match.group(1)


def points(text: str) -> list:
    return [[int(v) for v in m] for m in re.findall(POINT, text)]


def read_map() -> dict:
    text = LUA.read_text()
    stations = []
    for line in table(text, "STATIONS").splitlines():
        name = re.search(r'name = "(\w+)"', line).group(1)
        low, high, at = points(line)
        stations.append({"name": name, "box": (low, high), "at": at})
    destinations = []
    for line in table(text, "DESTINATIONS").splitlines():
        name = re.search(r'name = "(\w+)"', line).group(1)
        destinations.append({"name": name, "at": points(line)[0], "yaw": int(re.search(r"yaw = (\d+)", line)[1])})
    crystal = r'\[(\d+)\] = \{name = "(\w+)", station = (\d+), dest = (\d+)'
    crystals = [{"event": int(m[0]), "name": m[1], "station": int(m[2]), "dest": int(m[3])}
                for m in re.findall(crystal, table(text, "CRYSTALS"))]
    closets = []
    for line in table(text, "CLOSETS").splitlines():
        name = re.search(r'name = "(\w+)"', line).group(1)
        low, high, at = points(line)
        closets.append({"name": name, "box": (low, high), "at": at})
    summoners = [int(v) for v in re.search(r"^local SUMMONERS = \{([\d, ]+)\}", text, re.M)[1].split(",")]
    master = int(re.search(r"^local MASTER = (\d+)", text, re.M)[1])
    return {"stations": stations, "destinations": destinations, "crystals": crystals, "closets": closets,
            "summoners": summoners, "master": master}


def pose(at, yaw=0.0) -> dict:
    return {"set_pose": {"map": MAP, "x": at[0], "y": at[1], "z": at[2], "yaw": yaw, "pitch": 0.0}}


def wait(seconds) -> dict:
    return {"advance_runtime": {"seconds": seconds}}


def var(name, value) -> dict:
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def note(text) -> dict:
    return {"note": {"text": text}}


def scenario(identifier, title, steps) -> dict:
    return {"id": f"mm9r.wizardslab_{identifier}", "title": title, "world": "mm9", "mode": "faithful",
            "tags": ["mm9", "mm9_rework", "draft"], "steps": [{"load_map": {"map": MAP}}] + steps}


def teleporters(m) -> dict:
    neutral = next(d for d in m["destinations"] if d["name"] == NEUTRAL)["at"]
    steps = []
    for c in m["crystals"]:
        s = m["stations"][c["station"] - 1]
        d = m["destinations"][c["dest"] - 1]
        k = c["station"]
        steps += [note(f"Crystal {c['name']} (event {c['event']}): {s['name']} -> {d['name']}."),
                  pose(neutral), wait(0.5),
                  {"execute_event": {"id": c["event"]}}, wait(0.1),
                  var(f"Dest{k}", c["dest"]), var(f"CrystalBusy{k}", 1),
                  pose([s["at"][0], s["at"][1], s["at"][2]]), wait(1.0),
                  var(f"Dest{k}", 0),
                  wait(LIGHT_SECONDS - 0.6), var(f"CrystalBusy{k}", 0)]
    for d in m["destinations"]:
        steps += [note(f"{d['name']}: the party arriving stands on floor (TeleporterMulti.scr's destination)."),
                  {"movement_segment": {"input": "none", "seconds": 1.0, "actor_collision": False, "actor_ai": False,
                                        "start": {"map": MAP, "x": d["at"][0], "y": d["at"][1], "z": d["at"][2],
                                                  "yaw_degrees": d["yaw"] * 360 / 2048, "pitch": 0},
                                        "expect_stop": {"map": MAP, "x": d["at"][0], "y": d["at"][1],
                                                        "z": d["at"][2], "yaw_degrees": d["yaw"] * 360 / 2048,
                                                        "pitch": 0},
                                        "loose_tolerance": True, "tolerance_xy": 16, "tolerance_z": 24}}]
    # MM9 StartOpen: Closet2's leaves begin open (their click would shut them)
    initial = {d["door_id"]: d["initial_state"] for d in json.loads((HERE / "work/doors.json").read_text())}
    for c in m["closets"]:
        low, high = c["box"]
        event, door, door_y, inward = CLOSET_DOORS[c["name"]]
        x = (low[0] + high[0]) // 2
        start = {"map": MAP, "x": x, "y": door_y - inward * 150, "z": 40, "yaw_degrees": 90 * inward, "pitch": 0}
        starts_open = initial[door] == "open"
        opening = [] if starts_open else [{"execute_event": {"id": event}}, wait(2.0)]
        how = "standing open (MM9 StartOpen)" if starts_open else f"opened (event {event})"
        steps += [note(f"{c['name']} (always on, a plain Teleporter, behind its closet's doors): the closet {how}, "
                       f"the party walks in and touches the volume."),
                  pose(neutral), wait(0.5), pose([start["x"], start["y"], start["z"]], inward * 1.5708), wait(0.5),
                  *opening,
                  {"assert": {"mechanism": {"id": door, "state": "open"}}},
                  {"movement_segment": {"input": "forward", "seconds": 2.0, "actor_collision": False,
                                        "actor_ai": False, "start": start,
                                        # touching the volume sends the party on (a walk applies the move)
                                        "expect_stop": dict(start, x=c["at"][0], y=c["at"][1], z=c["at"][2]),
                                        # the walk goes on after the jump: near the arrival, thousands of units
                                        # from the closet, proves the trip
                                        "loose_tolerance": True, "tolerance_xy": 1500, "tolerance_z": 200}}]
    return scenario("teleporters", "Wizard's Lab (native BLV): the six colour teleporters, their 30 crystals, the "
                    "destinations and the closet teleporters", steps)


def ritual(m) -> dict:
    purple = next(d for d in m["destinations"] if d["name"] == "DestinationPurple")
    steps = [note("The first arrival at DestinationPurple (the tower top) starts the summoning (WizardLabCamera.scr; "
                  "the cinematic summoning runs its ticks)."),
             pose(purple["at"], purple["yaw"] * 6.283185 / 2048), wait(0.5), var("RitualStep", 1),
             wait(FADE_SECONDS), var("RitualStep", 2)]
    for step in range(3, 8):
        steps += [wait(CONJURE_SECONDS), var("RitualStep", step)]
    steps += [note("The master conjures (meteor, town portal, column of fire), then summons the Greater Demon."),
              wait(CONJURE_SECONDS), var("RitualStep", 8),
              wait(CONJURE_SECONDS), var("RitualStep", 9), var("DemonUp", 1),
              {"assert": {"actor_count": {"monster_id": ROW_DEMON, "min": 1}}},
              note("The demon kills the six apprentices (any hit now counts as its): each dying apprentice tells the "
                   "master; at six he banishes the demon (WizardMaster.scr :BanishDemon), then passes out.")]
    for actor in m["summoners"]:        # the demon kills some meanwhile (MM9's fight): each dies once, and one it
        # has already killed is no failure (Finished counts all six below)
        steps += [{"damage_actor": {"actor_index": actor, "amount": 50, "skip_dead": True}}, wait(0.5)]
    steps += [var("Finished", len(m["summoners"])), var("Banishing", 1), wait(BANISH_SECONDS + 0.5),
              var("DemonGone", 1), var("Betrayed", 0)]
    return scenario("ritual", "Wizard's Lab (native BLV): the summoning in the tower top", steps)


def main() -> int:
    m = read_map()
    print(len(m["stations"]), "stations,", len(m["destinations"]), "destinations,", len(m["crystals"]), "crystals,",
          len(m["closets"]), "closets,", len(m["summoners"]), "summoners")
    for name, data in (("teleporters", teleporters(m)), ("ritual", ritual(m))):
        path = HERE / f"scenario_{name}.yml"
        path.write_text("# Written by make_scenarios.py from the built map; rerun it after convert.py.\n"
                        + yaml.safe_dump(data, sort_keys=False, width=120))
        print("wrote", path.name, len(data["steps"]), "steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
