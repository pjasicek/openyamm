#!/usr/bin/env python3
"""
Door trap audit (DUNGEON_PLAYBOOK.md "Package change: a door that locks itself as it opens never auto-closes"): the
doorway doors of every built mm9r_* project that could shut a party into a room, for review by hand.

    python3 level_generation/projects/mm9r_common/door_trap_audit.py [mm9r_<map> ...]

It reads each project's last build (work/doors.json: groups, rooms, click events, mover auto-close; work/build_report.json:
the portals and the rooms they join) and MM9's DAT (each member's Locked, PushOpen; every message any object sends to
it). A room's portal count follows its name: a room with one portal is a dead end, and a dead end behind a flagged door
is where to look first. Two lists:

- **Shuts by itself**: a doorway group with an auto-close that the party may not reopen with a click: no click event,
  PushOpen 0, Locked in the DAT, or some object sends it Lock. A self-lock on open is fixed by the converter
  (movers.locks_itself); a Locked door the map's Lua keeps locked for good (a facade) is no trap.
- **Shut by another object**: a doorway group another object sends Close or Lock (trap rooms, ambushes, cells).

Every sender is listed with its class and message. What the map's Lua makes of them (keys kept or taken, unlock
variables, both-side buttons, timers) decides whether a flagged door is a trap: read its handler. The audit of
2026-11-09 found one (Thousand Terrors' MiddleDoor4/5, fixed).
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon.source import ROOT, Project, read_dat_world  # noqa: E402

PROJECTS = ROOT / "level_generation/projects"
LINKS = [(re.compile(r"(Open|Close)TriggerTarget(\d+)$"), lambda m: f"{m.group(1)}Trigger{m.group(2)}",
          lambda m: f"on-{m.group(1).lower()}"),
         (re.compile(r"TargetName(\d*)$"), lambda m: f"MessageName{m.group(1)}", lambda m: "trigger"),
         (re.compile(r"(Death|Damage)TriggerTarget$"), lambda m: f"{m.group(1)}TriggerMessage",
          lambda m: f"on-{m.group(1).lower()}")]


def senders_by_target(objects: list) -> dict:
    """Lower-case target name -> [(sender name, sender class, link kind, message)]."""
    out = defaultdict(list)
    for cls, props in objects:
        for key, value in props.items():
            if not isinstance(value, str) or not value.strip():
                continue
            for pattern, message_key, kind in LINKS:
                match = pattern.match(key)
                if match:
                    message = str(props.get(message_key(match), "") or "").strip().lower()
                    out[value.strip().lower()].append((str(props.get("Name")), cls, kind(match), message))
    return out


def audit(directory: Path) -> dict | None:
    work = directory / "work"
    if not (work / "doors.json").exists() or not (work / "build_report.json").exists():
        return None
    project = Project.load(directory)
    objects = [(o.name, {p.name: p.value for p in o.properties}) for o in read_dat_world(project.dat).objects]
    by_name = {str(p.get("Name", "")).lower(): p for _, p in objects}
    senders = senders_by_target(objects)
    degree = defaultdict(int)
    for portal in json.loads((work / "build_report.json").read_text()).get("portals", []):
        for room in portal["rooms"]:
            degree[room] += 1
    groups = defaultdict(list)
    for door in json.loads((work / "doors.json").read_text()):
        groups[door["group"]].append(door)
    # the auto-close the game runs: the installed scene's (a scratch rebuild installs it without touching work/)
    scene = ROOT / "assets_dev/worlds/mm9/maps" / f"{project.stem}.scene.yml"
    installed = {}
    if scene.exists():
        installed = {d["door_id"]: (d.get("mover") or {}).get("auto_close_seconds") or 0
                     for d in json.loads(scene.read_text())["initial_state"]["doors"]}
    shuts, shut = [], []
    for group, leaves in groups.items():
        if not any(d.get("doorway") for d in leaves):
            continue
        members = sorted({m for d in leaves for m in d.get("dat_models", [])})
        own = {m.lower() for m in members}
        props = [by_name.get(m.lower(), {}) for m in members]
        sent = sorted({s for m in members for s in senders.get(m.lower(), [])})
        rooms = sorted({leaves[0].get("room")} | {r for d in leaves for r in (d.get("extra_rooms") or [])} - {None})
        row = {"group": group, "rooms": {r: degree.get(r, 0) for r in rooms}, "senders": sent}
        auto = max(installed.get(d["door_id"], (d.get("mover") or {}).get("auto_close_seconds") or 0) for d in leaves)
        reasons = []
        if not max(d.get("event") or 0 for d in leaves):
            reasons.append("no click")
        if not all(int(float(p.get("PushOpen", 1) or 0)) for p in props):
            reasons.append("PushOpen 0")
        if any(int(float(p.get("Locked", 0) or 0)) for p in props):
            reasons.append("Locked")
        if any(s[3] == "lock" for s in sent):
            reasons.append("sent Lock")
        if auto and reasons:
            shuts.append(dict(row, auto_close=auto, reasons=reasons))
        if any(s[3] in ("close", "lock") and s[0].lower() not in own for s in sent):
            shut.append(row)
    return {"map": project.stem, "shuts": shuts, "shut": shut}


def rooms_text(rooms: dict) -> str:
    return ", ".join(f"{room} ({count} portal{'s' if count != 1 else ''})" for room, count in rooms.items())


def main() -> int:
    names = sys.argv[1:]
    directories = [PROJECTS / n for n in names] if names else sorted(
        p for p in PROJECTS.glob("mm9r_*") if p.name != "mm9r_common")
    for directory in directories:
        result = audit(directory)
        if result is None or not (result["shuts"] or result["shut"]):
            continue
        print(f"== {result['map']} ({directory.name})")
        for row in result["shuts"]:
            print(f"  shuts by itself: {row['group']} after {row['auto_close']:g} s ({', '.join(row['reasons'])}); "
                  f"{rooms_text(row['rooms'])}")
            for s in row["senders"]:
                print(f"      <- {s[0]} ({s[1]}, {s[2]}) {s[3]}")
        for row in result["shut"]:
            print(f"  shut by another object: {row['group']}; {rooms_text(row['rooms'])}")
            for s in row["senders"]:
                print(f"      <- {s[0]} ({s[1]}, {s[2]}) {s[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
