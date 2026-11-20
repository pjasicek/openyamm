"""Close the lips' slit (face lesson: no parted mouth, no pale band between the lips). Meshy's head shell folds the lips
inward into a 1-2 mm open slit whose up/down-facing inner walls are painted pale. Vertices of the slit (|x| < XW, z within
the mouth band, behind the lips' front, normal facing up/down |n.z| > 0.5 or backward n.y > 0.2) are moved to the slit's
mid-line height (per 4 mm x bin, the median z of the slit vertices), so the walls meet and the lips close with one line.
Positions only (UVs, weights, topology kept). Args: <in blend> <out blend> [z0 0.727] [z1 0.742] [xw 0.032] [yfront -0.034]"""
import bpy, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z0 = float(a[2]) if len(a) > 2 else 0.727; Z1 = float(a[3]) if len(a) > 3 else 0.742
XW = float(a[4]) if len(a) > 4 else 0.032; YF = float(a[5]) if len(a) > 5 else -0.034
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; mw = ob.matrix_world; mwi = mw.inverted()
rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
sel = []
for v in me.vertices:
    c = mw @ v.co; n = (mw.to_3x3() @ v.normal).normalized()
    if abs(c.x) < XW and Z0 < c.z < Z1 and c.y > YF + 0.003 and c.y < YF + 0.03 and (abs(n.z) > 0.5 or n.y > 0.2):
        sel.append((v.index, c.copy()))
xs = np.array([c.x for _, c in sel]); zs = np.array([c.z for _, c in sel])
moved = 0; mx = 0.0
for i, c in sel:
    m = np.abs(xs - c.x) < 0.004
    zm = float(np.median(zs[m]))
    d = zm - c.z
    if abs(d) > 1e-5:
        me.vertices[i].co = mwi @ Vector((c.x, c.y, zm)); moved += 1; mx = max(mx, abs(d))
me.update()
print('MOUTHCLOSE slit vertices', len(sel), 'moved', moved, 'max mm', round(mx * 1000, 2))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
