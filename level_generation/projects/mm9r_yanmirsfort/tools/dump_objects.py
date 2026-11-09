#!/usr/bin/env python3
"""Dump Yanmir's Fort DAT objects (all but AIRail) with their properties: work/objects.txt."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS/YANMIRSFORT.dat")
skip = set(sys.argv[1:]) or {"AIRail"}
out = []
for i, o in enumerate(world.objects):
    if o.name in skip:
        continue
    props = {p.name: p.value for p in o.properties}
    out.append(f"[{i}] {o.name} {props.get('Name')}")
    for k, v in props.items():
        if k == "Name":
            continue
        if v in ("", None, 0, 0.0, False):
            continue
        out.append(f"    {k} = {v}")
print("\n".join(out))
