"""Neck join fairing in the flight pose (2026-10-30, after graft_head.py; positions only, UVs and paints stay valid).

Args: <graft blend> <anim blend (for the Standing action)> <out blend> <report json> [t_min t_max]

The review viewer showed a waist where the neck meets the body: the loft is narrower than both the chest and the
head, with the chest standing proud of it (a recess at the throat, a ledge all round the join). The loft was built in
the bind pose, where the head looks down, and the bird is seen in flight, so the surface is faired in the fly pose:
every core vertex between t_min and t_max along the flight neck axis (Xneckpiv -> Xhead, in metres from Xneckpiv) is
solved as a biharmonic surface (uniform graph Laplacian, L^2 X = 0) with everything around it fixed, which removes the
ledge and the waist and keeps the tangents of the body and of the skull at the ends. Each solved position goes back
to the bind pose through the vertex's own skinning matrix, so with the unchanged weights the fly pose is exactly the
faired surface and the other clips bend it as before; the shading normals go the same way (see below). Loft vertices get piece = 1 (compose_crow.py repaints them).
"""
import bpy, sys, json
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
IN, ANIM, OUT, REP = a[:4]
PROBE = len(a) > 4 and a[4] == 'probe'
T_MIN = float(a[4]) if len(a) > 4 and not PROBE else 0.0
T_MAX = float(a[5]) if len(a) > 5 and not PROBE else 0.1

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
with bpy.data.libraries.load(ANIM) as (src, dst):
    dst.actions = ['Standing']
act = dst.actions[0]
rig.animation_data_create()
rig.animation_data.action = act
rig.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
bpy.context.view_layer.update()
M = {}
for pb in rig.pose.bones:
    M[pb.name] = np.array(rig.matrix_world @ pb.matrix @ rig.data.bones[pb.name].matrix_local.inverted())
n = len(me.vertices)
names = [g.name for g in body.vertex_groups]
P = np.array([tuple(v.co) for v in me.vertices])
PH = np.hstack([P, np.ones((n, 1))])
S = np.zeros((n, 4, 4))
for v in me.vertices:
    tot = sum(g.weight for g in v.groups)
    for g in v.groups:
        S[v.index] += M[names[g.group]] * g.weight / max(tot, 1e-9)
X = np.einsum('vij,vj->vi', S, PH)[:, :3]
chain = np.array([d.value for d in me.attributes['chain'].data])
piece = np.array([d.value for d in me.attributes['piece'].data])
kind = np.array([d.value for d in me.attributes['kind'].data])
o = np.array(rig.pose.bones['Xneckpiv'].head)
ax = np.array(rig.pose.bones['Xhead'].head) - o
ax /= np.linalg.norm(ax)
up = np.array([0, 0, 1.0]) - ax[2] * ax; up /= np.linalg.norm(up)
t = (X - o) @ ax
rel = (X - o) - np.outer(t, ax)
ru, rs = rel @ up, rel @ np.cross(ax, up)
core = (chain < 0) & (piece != 2)
rep = {'axis': ax.tolist()}
if PROBE:
    for tt in np.arange(-0.10, 0.22, 0.015):
        m = core & (np.abs(t - tt) < 0.008) & (np.hypot(ru, rs) < 0.14)
        if m.any():
            print(f'PROF t {tt:+.3f} n {m.sum():3d} top {ru[m].max():+.3f} bottom {ru[m].min():+.3f} '
                  f'halfwidth {np.abs(rs[m]).max():.3f} head {int((kind[m] > 0).sum())}')
    sys.exit(0)
zone = core & (t > T_MIN) & (t < T_MAX) & (np.hypot(ru, rs) < 0.14)
edges = np.array([e.vertices[:] for e in me.edges])
adj = [[] for _ in range(n)]
for x, y in edges:
    adj[x].append(y); adj[y].append(x)
# zone + two fixed rings around it
ids = set(np.nonzero(zone)[0].tolist())
ring = set(ids)
for _ in range(2):
    ring |= {j for i in ring for j in adj[i]}
order = sorted(ring)
idx = {v: i for i, v in enumerate(order)}
m_ = len(order)
L = np.zeros((m_, m_))
for v in order:
    i = idx[v]
    nb = [j for j in adj[v] if j in idx]
    L[i, i] = 1.0
    for j in nb:
        L[i, idx[j]] = -1.0 / len(nb)
A = L.T @ L
free = np.array([idx[v] for v in order if zone[v]])
fix = np.array([idx[v] for v in order if not zone[v]])
Xo = X[order]
sol = np.linalg.solve(A[np.ix_(free, free)] + 1e-9 * np.eye(len(free)), -A[np.ix_(free, fix)] @ Xo[fix])
Xn = X.copy()
Xn[np.array(order)[free]] = sol
Pn = P.copy()
zi = np.nonzero(zone)[0]
Pn[zi] = np.einsum('vij,vj->vi', np.linalg.inv(S[zi]), np.hstack([Xn[zi], np.ones((len(zi), 1))]))[:, :3]
for i in zi:
    me.vertices[int(i)].co = Vector(Pn[i])
# shading normals: the bind surface of the neck is bent and pinched (the head looks down), so normals computed there
# and carried by the skin point the wrong way in flight: they caught the viewer's lights from above as a pale collar
# and patch under the throat (the base colour there is dark). The normals are computed on the faired fly-pose surface
# and taken back through each vertex's skinning matrix, so S * n is the true flight normal in the review viewer.
tri = np.array([p_.vertices[:3] for p_ in me.polygons])
fn = np.cross(Xn[tri[:, 1]] - Xn[tri[:, 0]], Xn[tri[:, 2]] - Xn[tri[:, 0]])
Nf = np.zeros((n, 3))
for c in range(3):
    np.add.at(Nf, tri[:, c], fn)
Nf /= np.maximum(np.linalg.norm(Nf, axis=1, keepdims=True), 1e-12)
me.update()
Nb = np.array([tuple(x.vector) for x in me.vertex_normals])
chosen = np.array(order)
Nn = np.einsum('vij,vj->vi', np.linalg.inv(S[chosen][:, :3, :3]), Nf[chosen])
Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
Nb[chosen] = Nn
me.normals_split_custom_set_from_vertices([tuple(x) for x in Nb])
pa = me.attributes['piece'].data
for i in np.nonzero(kind == 4)[0]:
    pa[int(i)].value = 1
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.data.actions.remove(act)
d = np.linalg.norm(Xn[zi] - X[zi], axis=1)
rep.update({'t_range': [T_MIN, T_MAX], 'zone_verts': len(zi), 'fixed_verts': len(fix), 'max_move_fly_mm': float(d.max() * 1000),
            'mean_move_fly_mm': float(d.mean() * 1000), 'loft_verts': int((kind == 4).sum())})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('NECKFAIR ' + json.dumps(rep))
