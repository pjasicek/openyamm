"""Print face/helmet/coif landmarks of st1 parts (P03 face, P06 helmet, P02 coif, P08 nasal)."""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from mathutils.bvhtree import BVHTree
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_parts.blend'))
O = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
def tree(o):
    return BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])
T = {k: tree(O[k]) for k in ('P02', 'P03', 'P06', 'P08')}
for x in (0.0, 0.02, 0.033, 0.045, 0.06):
    row = []
    for z in np.arange(1.30, 1.53, 0.01):
        r = []
        for k in ('P03', 'P02', 'P06'):
            loc, n, i, d = T[k].ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
            r.append(f'{loc.y:+.3f}' if loc else '  --  ')
        row.append(f'z{z:.2f} face {r[0]} coif {r[1]} helm {r[2]}')
    print('X', x); print('\n'.join(row))
for k in ('P02', 'P03', 'P06', 'P08'):
    c = np.array([tuple(v.co) for v in O[k].data.vertices])
    print(k, 'lo', c.min(0).round(3), 'hi', c.max(0).round(3))
h = np.array([tuple(v.co) for v in O['P06'].data.vertices])
for ang in range(0, 360, 45):
    a = np.radians(ang); d = np.array([np.sin(a), -np.cos(a)])
    sel = (h[:, :2] - [-0.007, 0.055]) @ d > 0.06
    print('helmet rim min z dir', ang, round(float(h[sel, 2].min()), 3))
