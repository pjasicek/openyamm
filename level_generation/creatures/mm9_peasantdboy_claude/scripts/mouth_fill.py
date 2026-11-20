"""Close the mouth pocket (low 3/4 views read the dwarf boy's mouth as parted: the head shell folds about 1 cm inward
between the lips, rest z 0.324-0.338, and that pocket, painted as dark lip, faces a camera below the face).
Head-shell vertices in the mouth box (|x| < XW, Z0 < z < Z1, front) lying more than 1.5 mm behind the lips move forward
onto the straight line between the upper and the lower lip's front at their x (front-most shell vertex in the bands just
above and below the box, within 3 mm in x), minus 0.6 mm; a one-ring blend softens the rim. Positions only (UVs, weights
and paints unchanged: the dark pocket paint shrinks to the line where the lips meet). Symmetric (|x|).
Args (Blender): <in blend> <out blend> [xw 0.024] [z0 0.324] [z1 0.338]"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
XW = float(a[2]) if len(a) > 2 else 0.024
Z0 = float(a[3]) if len(a) > 3 else 0.324
Z1 = float(a[4]) if len(a) > 4 else 0.338
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']; hn = bm.faces.layers.int['hand']
headv = sorted({v.index for f in bm.faces if f[hl] and not f[hn] for v in f.verts})
co = np.array([bm.verts[i].co[:] for i in headv])
front = co[:, 1] < -0.05
def band_front(x, zlo, zhi):
    m = front & (np.abs(np.abs(co[:, 0]) - abs(x)) < 0.003) & (co[:, 2] > zlo) & (co[:, 2] < zhi)
    return co[m, 1].min() if m.any() else None
moved = 0; mx = 0.0
for k, i in enumerate(headv):
    x, y, z = co[k]
    if abs(x) >= XW or not (Z0 < z < Z1) or y > -0.04:
        continue
    up, lo = band_front(x, Z1, Z1 + 0.006), band_front(x, Z0 - 0.006, Z0)
    if up is None or lo is None:
        continue
    t = (z - Z0) / (Z1 - Z0)
    target = lo * (1 - t) + up * t + 0.0006
    if y > target + 0.0015:
        bm.verts[i].co.y = target; moved += 1; mx = max(mx, y - target)
bm.to_mesh(me); bm.free()
print('MOUTH_FILL', {'moved': moved, 'max_forward_mm': round(mx * 1000, 1)})
bpy.ops.wm.save_as_mainfile(filepath=a[1])
