#!/usr/bin/env python3
"""Faces per sector of the compiled BLV with each sector's LT extents. Usage: tools/sectors.py"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from util.map_export import parse_blv_file  # noqa: E402
blv = parse_blv_file(Path(__file__).resolve().parents[1] / "work/runtime/inventastorca.blv")["payload"]
V = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float) if isinstance(blv["vertices"][0], dict) \
    else np.array(blv["vertices"], float)
c = Counter(f["room_number"] for f in blv["faces"] if not f["is_portal"])
for room, n in sorted(c.items(), key=lambda kv: -kv[1]):
    idx = [i for f in blv["faces"] if f["room_number"] == room and not f["is_portal"] for i in f["vertex_indices"]]
    p = V[idx] / 2.56
    print(room, n, "x", int(p[:, 0].min()), int(p[:, 0].max()), "z", int(p[:, 1].min()), int(p[:, 1].max()),
          "y", int(p[:, 2].min()), int(p[:, 2].max()))
