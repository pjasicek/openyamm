"""The conduit's glowing faces by geometry (its retexture painted the core copper): every polygon of the core tube
(the welded component on the axis spanning z 2.0-4.4 m) and of the crown node below the gold spike (the slim axis
component reaching the top, below NODE_TOP). Writes work/<name>_energy_geo.json (polygon indices of
work/<name>_tex.blend); compose.py repaints them violet-white and build_machine.py makes them the glow.
Args: -- <name>"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

NODE_TOP = 5.5
name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
me = bpy.data.objects[name].data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)   # same faces in the same order; welded positions only
labels = mc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
picked, comps = [], []
for c in range(labels.max() + 1):
    p = co[labels == c]
    lo, hi = p.min(0), p.max(0); mid = (lo + hi) / 2
    if abs(mid[0]) > 0.15 or abs(mid[1]) > 0.15:
        continue
    core = lo[2] > 1.95 and hi[2] < 4.45 and hi[2] - lo[2] > 1.5
    node = hi[2] > 5.8 and np.hypot(p[:, 0], p[:, 1]).max() < 0.2
    if core or node:
        comps.append(c)
        for f in bm.faces:
            if labels[f.verts[0].index] == c and (core or f.calc_center_median().z < NODE_TOP):
                picked.append(f.index)
assert len(bm.faces) == len(me.polygons)
json.dump(sorted(picked), open(os.path.join(HERE, 'work', f'{name}_energy_geo.json'), 'w'))
print('ENERGY_GEO components', comps, 'polygons', len(picked))
