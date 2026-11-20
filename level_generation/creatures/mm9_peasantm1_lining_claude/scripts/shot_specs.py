#!/usr/bin/env python3
"""viewer_shots.mjs specs (name:clip:time:view:body:camera:target, glTF metres) for the see-through gate's views: the posed
LOD0 bounding-box centre at clip/frame (30 fps) as the target, the camera along the gate's azimuth/elevation (az 0 = front,
+z; el = degrees down), at `dist` m, optionally aimed at an offset from the centre or at a fixed point.
Usage: shot_specs.py <glb> name:clip:frame30:az:el:dist[:dx,dy,dz | :@x,y,z bind anchor] ...  (prints the specs space-separated)"""
import math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(sys.argv[1])); out = []
for spec in sys.argv[2:]:
    f = spec.split(':'); name, clip, fr, az, el, dist = f[0], f[1], int(f[2]), float(f[3]), float(f[4]), float(f[5])
    t = fr / 30.0
    posed = m.skinned_positions(m.world(m.sample(clip, t)))
    P = posed[0][0]
    c = (P.min(0) + P.max(0)) / 2
    if len(f) > 6 and f[6].startswith('@'):          # a bind-space anchor: the posed position of the nearest LOD0 vertex
        q = np.array([float(x) for x in f[6][1:].split(',')]); best = None
        for k, prim in enumerate(m.primitives):
            i = np.linalg.norm(prim['positions'] - q, axis=1).argmin(); dd = np.linalg.norm(prim['positions'][i] - q)
            if best is None or dd < best[0]:
                best = (dd, posed[k][0][i])
        c = best[1]
    elif len(f) > 6:
        c = c + np.array([float(x) for x in f[6].split(',')])
    a, e = math.radians(az), math.radians(el)
    d = np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
    cam = c + d * dist
    out.append(f'{name}:{clip}:{t:.4f}:front:body:' + ','.join(f'{x:.4f}' for x in cam) + ':' + ','.join(f'{x:.4f}' for x in c))
print(' '.join(out))
