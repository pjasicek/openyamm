"""Put every dorsal blade exactly on the midline plane (Blender, in place on work/v3/uv_master.blend after the UV
restore). scripts/v3/add_spines.py took each blade's up vector from the surface normal at its root, which leans a
few degrees sideways on the cdr1 back; here each blade (13-vertex component: 6 root lens, 6 mid lens, tip) is turned rigidly so its lateral axis is +X and its up axis lies in the x = 0 plane, root centre on x = 0.
Topology, UVs and weights are unchanged (the retexture stays mapped)."""
import bpy, numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
P = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
o = bpy.data.objects['Body']; me = o.data
part = np.array([d.value for d in me.attributes['v3part'].data])
E = np.array([e.vertices[:] for e in me.edges]); sp = part == 3
parent = {i: i for i in np.where(sp)[0]}
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
for a_, b_ in E:
    if sp[a_] and sp[b_]: parent[find(a_)] = find(b_)
blades = {}
for i in parent: blades.setdefault(find(i), []).append(i)
assert all(len(v) == 13 for v in blades.values()), sorted(len(v) for v in blades.values())
worst = 0.
for vids in blades.values():
    vs = [me.vertices[int(i)] for i in vids]; P_ = np.array([v.co[:] for v in vs]); m = P_.mean(0)
    tip = P_[np.argmax(np.linalg.norm(P_ - m, axis=1))]
    base = P_[np.argsort(-np.linalg.norm(P_ - tip, axis=1))[:6]]; c = Vector(base.mean(0))
    _, _, vt = np.linalg.svd(base - base.mean(0)); side = Vector(vt[1])       # root lens: long axis vt[0], across vt[1], normal vt[2]
    up = Vector(tip) - c; up = (up - up.dot(side) * side).normalized(); t = side.cross(up).normalized()
    side2 = Vector((1, 0, 0)) if side.x > 0 else Vector((-1, 0, 0))
    up2 = Vector((0, up.y, up.z)).normalized(); t2 = side2.cross(up2).normalized()
    M0 = Matrix((t, up, side)).transposed(); M1 = Matrix((t2, up2, side2)).transposed(); R = M1 @ M0.inverted()
    c2 = Vector((0, c.y, c.z))
    for v in vs:
        new = c2 + R @ (v.co - c); worst = max(worst, (new - v.co).length); v.co = new
me.update()
print('SYM_SPINES blades', len(blades), 'max move mm', round(worst * 1000, 2))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/v3/uv_master.blend'))
