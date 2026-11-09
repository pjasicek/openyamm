#!/usr/bin/env python3
"""Lowest and highest point (glTF y, mm) of every visual LOD in every clip (30 fps samples), as floor/height evidence that
the linings change no LOD's floor contact or height. Usage: lod_floor.py <glb> [fps 30]"""
import copy
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
path = sys.argv[1]; FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
base = Glb(path)
node = next(i for i, n in enumerate(base.json['nodes']) if 'mesh' in n and 'skin' in n)
mesh0 = base.json['nodes'][node]['mesh']
lods = [mesh0] + base.json['meshes'][mesh0]['extras']['openyamm_lods']
for li, mi in enumerate(lods):
    g = Glb(path); g.json['nodes'][node]['mesh'] = mi; g.json['meshes'][mi]['name'] = 'Visual'
    m = Model(g); out = []
    for clip in m.clips:
        t1 = m.clip_times(clip)[-1]; lo, hi = 9.0, -9.0
        for t in np.append(np.arange(0, t1, 1 / FPS), t1):
            for P, T in m.skinned_positions(m.world(m.sample(clip, t))):
                y = P[np.unique(T), 1]; lo = min(lo, y.min()); hi = max(hi, y.max())
        out.append(f'{clip} {lo * 1000:.2f}/{hi * 1000:.2f}')
    print(f'LOD{li} (mesh {mi}) lowest/highest mm: ' + ', '.join(out), flush=True)
