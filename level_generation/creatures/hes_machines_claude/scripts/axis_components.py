"""List the connected components (positions welded) of work/<name>_tex.blend that sit on the yaw axis: bbox centre
within 0.15 m of x = y = 0. For picking the glowing core/node by geometry. Args: -- <name>"""
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
bm = bmesh.new(); bm.from_mesh(bpy.data.objects[name].data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
labels = mc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
for c in range(labels.max() + 1):
    p = co[labels == c]
    lo, hi = p.min(0), p.max(0); mid = (lo + hi) / 2
    if abs(mid[0]) < 0.15 and abs(mid[1]) < 0.15 and len(p) >= 8:
        print('AXIS', c, len(p), 'lo', lo.round(3).tolist(), 'hi', hi.round(3).tolist(),
              'radius', round(float(np.hypot(p[:, 0], p[:, 1]).max()), 3))
