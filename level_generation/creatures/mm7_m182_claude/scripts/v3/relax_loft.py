"""Move the lofted neck's intermediate rings to the linear blend (work/v3/graft.npz 'loft_linear'), in place on
work/v3/uv_master.blend after the UV restore: topology and UVs unchanged; the loft paint is rebuilt from 3D positions
by compose_v3 (rebake first). Loft vertices are found by their graft positions."""
import bpy, numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P = Path(__file__).resolve().parents[2]
g = np.load(P / 'work/v3/graft.npz'); old = g['co'][g['orig'] == 2]; new = g['loft_linear']
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
me = bpy.data.objects['Body'].data
kd = KDTree(len(me.vertices))
for v in me.vertices: kd.insert(v.co, v.index)
kd.balance(); moved = 0; worst = 0.
for a, b in zip(old, new):
    co, i, d = kd.find(Vector(a)); assert d < 1e-5, d
    worst = max(worst, (Vector(b) - me.vertices[i].co).length); me.vertices[i].co = Vector(b); moved += 1
me.update(); print('RELAX_LOFT moved', moved, 'max mm', round(worst * 1000, 1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
