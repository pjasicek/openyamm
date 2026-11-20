#!/usr/bin/env python3
"""Compare two builds of the keep (a runtime folder with its reports) so nothing is lost: the files byte for byte, the
scene section by section, the counts of decorations, pads, actors, chests, movers, lights and portals.

    python3 compare_builds.py <old dir> <new dir>      # each holds runtime/, content.json, doors.json, lights.json
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

old, new = Path(sys.argv[1]), Path(sys.argv[2])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12] if path.exists() else None


for name in ("anskramkeep.blv", "anskramkeep.doors.yml", "anskramkeep.faces.yml", "anskramkeep.lua"):
    a, b = digest(old / "runtime" / name), digest(new / "runtime" / name)
    print(f"{name}: {'identical' if a == b else 'DIFFERENT'} {a} {b}")

sa, sb = (json.loads((d / "runtime/anskramkeep.scene.yml").read_text()) for d in (old, new))
for key in sorted(set(sa) | set(sb)):
    if sa.get(key) != sb.get(key):
        print("scene key differs:", key)
for key in sorted(set(sa["initial_state"]) | set(sb["initial_state"])):
    if sa["initial_state"].get(key) != sb["initial_state"].get(key):
        print("initial_state differs:", key)
print("starts", [(s["position"], s["direction_degrees"]) for s in sa["party_start_points"]], "->",
      [(s["position"], s["direction_degrees"]) for s in sb["party_start_points"]])
actors_a, actors_b = sa["initial_state"]["actors"], sb["initial_state"]["actors"]
print("actors", len(actors_a), len(actors_b))
fields = Counter()
for a, b in zip(actors_a, actors_b):
    for key in a:
        if a[key] != b.get(key):
            fields[key] += 1
print("actor fields that differ:", dict(fields))
print("loot", len(sa["loot_containers"]), len(sb["loot_containers"]), sa["loot_containers"] == sb["loot_containers"])
print("doors", len(sa["initial_state"]["doors"]), len(sb["initial_state"]["doors"]))
ca, cb = (json.loads((d / "content.json").read_text()) for d in (old, new))
for key in ("decorations", "pads", "actors", "chests"):
    print(key, len(ca[key]), len(cb[key]), "same" if ca[key] == cb[key] else "differ")
    names = {e["anchor"] for e in ca[key]}, {e["anchor"] for e in cb[key]}
    if names[0] != names[1]:
        print("   lost:", sorted(names[0] - names[1]), "new:", sorted(names[1] - names[0]))
da, db = (json.loads((d / "doors.json").read_text()) for d in (old, new))
print("movers", len(da), len(db), "lost:", sorted({m["node"] for m in da} - {m["node"] for m in db}), "new:",
      sorted({m["node"] for m in db} - {m["node"] for m in da}))
la, lb = (json.loads((d / "lights.json").read_text()) for d in (old, new))
print("lights kept", sum(x["kept"] for x in la), sum(x["kept"] for x in lb), "total", len(la), len(lb))
