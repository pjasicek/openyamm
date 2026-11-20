#!/usr/bin/env python3
"""
Writes the yanmir_death scenarios (cutscene.py; README "Cinematics"):

- cinematic_yanmir_death_play.yml: the cinematic from the console: key 173 and the experience at
  once, the floor at 3.5 s, Yanmir removed at 6.3 s, a save refused while it plays and allowed after the 9.3 s.
- cinematic_yanmir_death_skip.yml: the same, skipped at 1 s: every step still runs.
- cinematic_yanmir_death_trigger.yml: the real trigger. Yanmir woken (SquishTrigger0), seen from the trap hall's north
  end; the party then waits beyond the hall's south door (DPortal20), off the AIRails tagged 555, so Yanmir crosses
  TriggerYanmirTrap chasing it: the cinematic started (its map var), the steps all ran.
- cinematic_yanmir_death_watch.yml: the same with the party in the hall (on a 555 rail): no cinematic, the same steps
  on the T_FALL timer.

The moment Yanmir's chase brings him onto the trap varies by a few frames between runs (about 11 s after the party
reaches the south door), so the timeline checks use the console start and the trigger checks the end state.

    python3 level_generation/projects/mm9r_yanmirsfort/make_cinematic_scenarios.py
"""

from __future__ import annotations

from pathlib import Path

import json

import yaml

PROJECT = Path(__file__).resolve().parent
YANMIR, KEY_FREE_QBIT = 71, 90173
# the trap's first floor and plank movers (work/doors.json: their ids move when the movers before them change)
_DOORS = json.loads((Path(__file__).resolve().parent / "work/doors.json").read_text())
FLOOR_DOOR = next(m["door_id"] for m in _DOORS if m["group"] == "TrapFloor")
PLANKS_DOOR = next(m["door_id"] for m in _DOORS if m["group"] == "TrapPlanks")
NORTH = 1.5707963267948966


def pose(x, y, z=1, yaw=NORTH):
    return {"set_pose": {"map": "yanmirsfort.blv", "x": x, "y": y, "z": z, "yaw": yaw, "pitch": 0}}


def adv(seconds):
    return {"advance_runtime": {"seconds": round(seconds, 3)}}


def var(name, value):
    return {"assert": {"state_dump_named_map_var": {"name": name, "value": value}}}


def note(text):
    return {"note": {"text": text}}


def lure(final_y: int) -> list:
    steps = [{"load_map": {"map": "yanmirsfort.blv"}}, note("YanmirTrap.scr: the six supports broken arm the trap")]
    steps += [{"execute_event": {"id": 200 + k}} for k in range(6)]
    steps += [adv(0.5), var("TrapArmed", 1), note("SquishTrigger0 wakes Yanmir")]
    steps += [pose(-4455, -2458, 1, 0.0), adv(0.5), pose(-4055, -2458, 1, 0.0), adv(0.5), var("YanmirAwake", 1)]
    steps += [note("Yanmir sees the party, which backs into the trap hall's north end"),
              pose(-1792, -2304, 1, 3.141592653589793), adv(3), {"execute_event": {"id": 112}}, pose(0, -3840),
              adv(4), pose(492, -4864), adv(4), pose(492, -6144), adv(4)]
    steps += [note(f"the party waits at y {final_y}: Yanmir chases it over the trap"), {"execute_event": {"id": 113}},
              adv(1), pose(492, final_y), adv(0.25)]
    return steps


def scenario(name: str, title: str, steps: list) -> None:
    body = {"id": f"mm9r.yanmirsfort.cinematic_yanmir_death_{name}", "title": title, "world": "mm9",
            "mode": "faithful", "tags": ["mm9", "mm9_rework", "cinematic"], "steps": steps}
    path = PROJECT / f"cinematic_yanmir_death_{name}.yml"
    path.write_text("# Written by make_cinematic_scenarios.py (yanmir_death, cutscene.py).\n"
                    + yaml.safe_dump(body, sort_keys=False, width=120))
    print(path)


def console_start() -> list:
    """The cinematic from the console: a fixed timeline to check against (Yanmir glides from his bed to YanmirPathA4
    in the first 2 s, as the console start has him elsewhere). The supports stay whole: with the trap armed, Yanmir
    standing on it would start the cinematic again through trapFires (TrapFired is 0 without the real trigger)."""
    steps = [{"load_map": {"map": "yanmirsfort.blv"}}, pose(492, -11700), adv(0.5), var("TrapArmed", 0),
             {"console": {"line": "cinematic play yanmir_death 36000"}}]
    return steps


def main() -> None:
    play = console_start() + [
        adv(0.5), note("0.5 s: playing; :GiveEeps ran at 0 s (key 173 without the quest's key 68); the floor is up"),
        {"console": {"line": "cinematic list", "expect_contains": "playing yanmir_death"}},
        {"assert": {"qbit_set": [KEY_FREE_QBIT]}}, {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "closed"}}},
        {"save_game": {"name": "mid_cinematic", "expect_failure": True}},
        adv(4.2), note("4.7 s: startDie's DestroyFloor key (3.5 s) brought the floor down; Yanmir falls"),
        {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "open"}}}, var("YanmirGone", 0),
        {"assert": {"actor_visible": {"actor_index": YANMIR, "hidden": False}}},
        {"console": {"line": "cinematic list", "expect_contains": "playing yanmir_death"}},
        adv(2.0), note("6.7 s: the end of the world has removed him (6.3 s)"), var("YanmirGone", 1),
        {"assert": {"actor_visible": {"actor_index": YANMIR, "hidden": True}}},
        adv(3.0), note("9.7 s: the camera is off (9.3 s): saving works again"),
        {"save_game": {"name": "after_cinematic"}},
    ]
    scenario("play", "Yanmir's Fort - yanmir_death played (console start, fixed timeline)", play)
    skip = console_start() + [
        adv(1.0), {"console": {"line": "cinematic list", "expect_contains": "playing yanmir_death"}},
        {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "closed"}}}, var("YanmirGone", 0),
        {"console": {"line": "cinematic skip", "expect_contains": "Skipping"}},
        adv(0.5), note("skipped at 1 s: the floor, the planks and the removal ran at once"),
        var("YanmirGone", 1), {"assert": {"qbit_set": [KEY_FREE_QBIT]}},
        {"assert": {"actor_visible": {"actor_index": YANMIR, "hidden": True}}},
        adv(2.0), {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "open"}}},
        {"assert": {"mechanism": {"id": PLANKS_DOOR, "state": "open"}}},
        {"save_game": {"name": "after_skip"}},
    ]
    scenario("skip", "Yanmir's Fort - yanmir_death skipped", skip)
    trigger = lure(-11700) + [
        adv(30.0), note("Yanmir has crossed TriggerYanmirTrap (about 11 s): the cinematic started and ran out"),
        var("TrapFired", 1), var("Cinema.yanmir_death.started", 1), var("YanmirGone", 1),
        {"assert": {"qbit_set": [KEY_FREE_QBIT]}}, {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "open"}}},
        {"assert": {"actor_visible": {"actor_index": YANMIR, "hidden": True}}},
        {"save_game": {"name": "after_trap"}},
    ]
    scenario("trigger", "Yanmir's Fort - yanmir_death through its trigger (the party off the 555 rails)", trigger)
    watch = lure(-10829) + [
        adv(30.0), note("the party on AITrk97 (UserData 555) saw the hall: no camera, the steps on T_FALL"),
        var("TrapFired", 1), var("Cinema.yanmir_death.started", 0), var("FallStage", 4), var("YanmirGone", 1),
        {"assert": {"qbit_set": [KEY_FREE_QBIT]}}, {"assert": {"mechanism": {"id": FLOOR_DOOR, "state": "open"}}},
        {"assert": {"actor_visible": {"actor_index": YANMIR, "hidden": True}}},
    ]
    scenario("watch", "Yanmir's Fort - yanmir_death watched from the hall (no camera)", watch)


if __name__ == "__main__":
    main()
