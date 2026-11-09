"""Symmetric master-pose body: centre the torso on x, undo the yaw, turn the left arm (raw -x) into the masters' A pose, keep the -x half, mirror.
Args: <in blend> <out blend> <out npz> <report json>. The arm joints are from the plane-section survey (see README)."""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix
IN, OUT, NPZ, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
P = np.array([tuple(v.co) for v in me.vertices])
# centre and yaw
cx, cy = 0.046, 0.09
yaw = math.atan2(0.044, 0.428)     # the legs' centres differ by 4.4 cm in y over 42.8 cm
c, s = math.cos(yaw), math.sin(yaw)
Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
if Rz @ np.array([1, 0, 0]) @ np.array([0, 1, 0]) < 0: Rz = Rz.T
P = (P - [cx, cy, 0]) @ Rz.T
L = P[:, 0] < 0
# the left arm: sections at the old pose, transformed
def tr(q): return (np.array(q, float) - [cx, cy, 0]) @ Rz.T
Sh, El, Wr = tr((-.190, .120, 1.452)), tr((-.380, .107, 1.386)), tr((-.505, .027, 1.349))
def smooth(x, a, b):
    u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def rot_about(p, o, axis, ang, w):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    out = p.copy()
    d = p - o
    # by angle w*ang per vertex (Rodrigues), keeps limb thickness better than a matrix blend
    a = (w * ang)[:, None]
    out = o + d * np.cos(a) + np.cross(axis, d) * np.sin(a) + axis * (d @ axis)[:, None] * (1 - np.cos(a))
    return out
u0 = (El - Sh) / np.linalg.norm(El - Sh); f0 = (Wr - El) / np.linalg.norm(Wr - El)
# arm vertices: on the -x side, beyond the armpit plane
arm = L & (((P - Sh) @ u0) > -0.10) & (P[:, 2] > 1.2) & (np.abs(P[:, 0]) > 0.17)
print('ARM VERTS', arm.sum())
# forearm first: straighten the elbow to a small bend in the plane of the arm
target_f = u0 + 0.10 * np.array([0, -1, 0]); target_f /= np.linalg.norm(target_f)
ax = np.cross(f0, target_f); ang = math.atan2(np.linalg.norm(ax), f0 @ target_f)
Q = P.copy()
tt = (P - El) @ ((u0 + f0) / np.linalg.norm(u0 + f0))
w = np.where(arm, smooth(tt, -0.035, 0.035), 0.0)
idx = w > 0
Q[idx] = rot_about(P[idx], El, ax, ang, w[idx])
print('ELBOW deg', math.degrees(ang))
# whole arm: down to 40 deg below horizontal about the shoulder
target_u = np.array([-math.cos(math.radians(40)), -0.03, -math.sin(math.radians(40))]); target_u /= np.linalg.norm(target_u)
ax = np.cross(u0, target_u); ang = math.atan2(np.linalg.norm(ax), u0 @ target_u)
tt = (P - Sh) @ u0
w = np.where(arm, smooth(tt, -0.07, 0.05), 0.0)
idx = w > 0
Q[idx] = rot_about(Q[idx], Sh, ax, ang, w[idx])
print('SHOULDER deg', math.degrees(ang))
me.vertices.foreach_set('co', Q.ravel()); me.update()
# keep -x, mirror
bm = bmesh.new(); bm.from_mesh(me)
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
ret = bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
co = np.array([tuple(v.co) for v in me.vertices])
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.modifier_add(type='TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=ob.modifiers[-1].name)
T = np.zeros(len(me.polygons) * 3, np.int32); me.polygons.foreach_get('vertices', T)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
np.savez(NPZ, co=co, tri=T.reshape(-1, 3))
json.dump(dict(shoulder=(Sh).tolist(), elbow=El.tolist(), wrist=Wr.tolist()), open(REP, 'w'))
print('SYM', len(co), len(T) // 3, co.min(0), co.max(0))
