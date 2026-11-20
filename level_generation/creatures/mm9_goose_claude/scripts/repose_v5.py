"""Feet and bill repair on the UV-mapped goose (same topology and UVs, so the retexture stays valid).

Args: <in blend (uv_v4)> <mm9 rig blend> <out blend> <report json>

Feet: MM9's bind holds the feet tilted 17-21 deg; its clips flatten them (stand: 3-6 deg, toes splayed to -111 / -69
deg). Our Meshy feet were flat in the bind, so the clips tilted them. Per foot: in MM9's `stand` pose, the rotation
about the ankle that takes our toes' plane normal and toe yaw onto MM9's; every vertex is moved there in the stand
pose (scaled by its foot + toe weight) and pulled back to the bind by the inverse of its own skinning matrix. In
Standing the foot is then as MM9's, and every other clip follows MM9's bones from the right bind.

Bill: Meshy thinned the master's bill to a wader's: about 1.6 x the skull's depth long, needle tip. A real goose has a
bill shorter than its head, deep at the base with a blunt tip. Vertices ahead of the bill base scale along the bill
axis by BILL_LEN and away from it by 1 + BILL_THICK * u (u = 0 base, 1 tip), so the base seam does not move.
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Matrix, Quaternion, Vector
argv = sys.argv[sys.argv.index('--') + 1:]
IN, SRC, OUT, REP = argv
BILL_LEN = float(os.environ.get('BILL_LEN', '0.76'))
BILL_THICK = float(os.environ.get('BILL_THICK', '0.5'))
bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
with bpy.data.libraries.load(SRC) as (s_, d_):
    d_.objects = ['goose.mesh']
mm9 = d_.objects[0]
rig.animation_data_create()
act = bpy.data.actions['stand']
rig.animation_data.action = act
try:
    rig.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(0)
bpy.context.view_layer.update()
bones = [b.name for b in rig.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
Sm = np.array([np.array(rig.pose.bones[b].matrix @ rig.data.bones[b].matrix_local.inverted()) for b in bones])
n = len(me.vertices)
W = np.zeros((n, len(bones)))
gn = {g.index: g.name for g in body.vertex_groups}
for v in me.vertices:
    for g in v.groups:
        W[v.index, bidx[gn[g.group]]] = g.weight
P = np.array([tuple(v.co) for v in me.vertices])
Ph = np.hstack([P, np.ones((n, 1))])
Mi = np.einsum('ib,bjk->ijk', W, Sm)
Ps = np.einsum('ijk,ik->ij', Mi, Ph)[:, :3]
mg = {g.index: g.name for g in mm9.vertex_groups}
Q = np.array([tuple(mm9.matrix_world @ v.co) + (1.0,) for v in mm9.data.vertices])
QL = np.array([mg[max(v.groups, key=lambda g: g.weight).group] for v in mm9.data.vertices])
Qs = np.array([Sm[bidx[l]] @ q for q, l in zip(Q, QL)])[:, :3]
rep = {}


def plane_normal(X):
    c = X.mean(0)
    vt = np.linalg.svd(X - c)[2]
    nrm = vt[2]
    return nrm if nrm[2] > 0 else -nrm


Pnew = Ps.copy()
for foot, toes in (('Xfoot', ['Xtoea', 'Xtoeb', 'Xtoec']), ('Xfoot01', ['Xtoea01', 'Xtoeb01', 'Xtoec01'])):
    A = np.array(rig.pose.bones[foot].head)
    tw = W[:, [bidx[t] for t in toes]].sum(1)
    ours = tw > 0.5
    m9 = np.isin(QL, toes)
    n_o, n_m = plane_normal(Ps[ours]), plane_normal(Qs[m9])
    q1 = Vector(n_o).rotation_difference(Vector(n_m))
    Pt = (np.array(q1.to_matrix()) @ (Ps[ours] - A).T).T + A
    co, cm = Pt.mean(0) - A, Qs[m9].mean(0) - A
    dy = math.atan2(cm[1], cm[0]) - math.atan2(co[1], co[0])
    dy = (dy + math.pi) % (2 * math.pi) - math.pi
    q = Quaternion((0, 0, 1), dy) @ q1
    fw = W[:, [bidx[foot]] + [bidx[t] for t in toes]].sum(1)
    x = np.clip((fw - 0.3) / 0.6, 0, 1)
    g = x * x * (3 - 2 * x)
    for i in np.nonzero(g > 1e-3)[0]:
        qi = Quaternion().slerp(q, float(g[i]))
        Pnew[i] = np.array(qi.to_matrix()) @ (Ps[i] - A) + A
    rep[foot] = {'tilt_before_deg': math.degrees(math.acos(min(1, n_o[2]))), 'tilt_mm9_deg': math.degrees(math.acos(min(1, n_m[2]))),
                 'turn_deg': math.degrees(q.angle), 'yaw_delta_deg': math.degrees(dy), 'verts': int((g > 1e-3).sum())}
moved = np.linalg.norm(Pnew - Ps, axis=1) > 1e-7
for i in np.nonzero(moved)[0]:
    P[i] = (np.linalg.inv(Mi[i]) @ np.append(Pnew[i], 1))[:3]

# ---------------- bill
piece = np.array([d.value for d in me.attributes['piece'].data])
img = bpy.data.images.load(os.path.join(os.path.dirname(OUT), '..', 'textures', 'goose_basecolor.png'))
w_, h_ = img.size
px = np.array(img.pixels[:], np.float32).reshape(h_, w_, 4)
uvl = me.uv_layers.active.data
col = np.zeros((n, 3)); cnt = np.zeros(n)
for lo in me.loops:
    u, v = uvl[lo.index].uv
    col[lo.vertex_index] += px[min(h_ - 1, int(v * h_)), min(w_ - 1, int(u * w_)), :3]
    cnt[lo.vertex_index] += 1
col /= np.maximum(cnt, 1)[:, None]
orange = (col[:, 0] > col[:, 2] * 1.6) & (col[:, 0] > 0.35)
tip = P[np.argmin(np.where(piece == 0, P[:, 1], 9))]
eyes = P[piece == 2].mean(0)
head = (np.linalg.norm(P - eyes, axis=1) < 0.2) & (piece == 0)
d0 = (tip - eyes) / np.linalg.norm(tip - eyes)
tt = (P - eyes) @ d0
bo = head & orange & (np.abs(P[:, 0]) < 0.06) & (tt > 0)
t0 = float(np.percentile(tt[bo], 3))
base = P[bo & (tt < t0 + 0.012)].mean(0); base[0] = 0.0
ax = tip - base; L = float(np.linalg.norm(ax)); ax /= L
uu = (P - base) @ ax / L
sel = head & (uu > 0)
rad = (P - base) - (uu[:, None] * L) * ax
newp = P.copy()
for i in np.nonzero(sel)[0]:
    newp[i] = base + ax * L * BILL_LEN * uu[i] + rad[i] * (1 + BILL_THICK * min(1.0, uu[i]))
rep['bill'] = {'len_before': L, 'len_after': L * BILL_LEN, 'verts': int(sel.sum()), 'base': base.tolist(), 'tip': tip.tolist()}
P = newp
for v, p in zip(me.vertices, P):
    v.co = Vector(p)
me.update()
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REPOSE ' + json.dumps(rep))
