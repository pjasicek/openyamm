"""PeasantM5 body fit (2026-11-02, user via coordinator: "isnt there a disparity between the body size and head size?"): Markel's
body (ours) is wider than MM9's M5 along the torso sides, upper arms, shirt hem/hips and thighs, and deeper in belly and back,
while the heads match. Positions only (topology, UVs, weights unchanged; paid paints stay valid), bind pose, on the master
before the linings.
Field: every OUTER-layer vertex of ours (|signed distance| < 8 cm to MM9 M5's surface and its normal within 60 deg of the
nearest M5 normal) wants the move -d * n_M5 that puts it on M5's surface. The move applied at any vertex is the Gaussian
(SIGMA 2 cm, radius 5 cm) average of those wanted moves around its rest position, so inner layers (sleeve inside, the shirt
under the belt, linings later) move with the cloth over them; times a region weight by dominant-bone share: trunk, pelvis,
thighs, calves (boot shafts), clavicles and upper arms 1, forearms fading to 0 at the wrist; head, neck, hands, fingers and
feet 0 (pinned; the boot foot below the ankle 0). Then 8 mesh-edge smoothing passes of the move (pinned fixed), x GAIN.
Args: -- <in blend> <out blend> <m5 npz (co, tris; MM9 M5 in Blender bind space)> <report json> [gain 1.0]"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, M5, REP = a[:4]; GAIN = float(a[4]) if len(a) > 4 else 1.0
import os
SIGMA, RAD = float(os.environ.get('SIGMA', '0.02')), float(os.environ.get('RAD', '0.05'))
D = np.load(M5); C, T = D['co'].astype(float), D['tris']
A_, B_, C_ = C[T[:, 0]], C[T[:, 1]], C[T[:, 2]]
FN = np.cross(B_ - A_, C_ - A_); FN /= np.linalg.norm(FN, axis=1, keepdims=True) + 1e-12
P, N = [], []
for i in range(5):
    for j in range(5 - i):
        u, v = i / 4, j / 4
        P.append(A_ + u * (B_ - A_) + v * (C_ - A_)); N.append(FN)
P, N = np.concatenate(P), np.concatenate(N)
kt = KDTree(len(P))
for i, p in enumerate(P): kt.insert(Vector(p), i)
kt.balance()
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data; mw = np.array(o.matrix_world)
assert np.allclose(mw, np.eye(4), atol=1e-6), 'Body must have an identity matrix'
co = np.array([v.co[:] for v in me.vertices]); nr = np.array([v.normal[:] for v in me.vertices])
vg = {g.index: g.name for g in o.vertex_groups}
def rw(name):
    n = name.lower()
    if any(k in n for k in ('head', 'neck', 'hand', 'finger', 'thumb', 'index', 'middle', 'ring', 'pinky', 'foot', 'toe', 'eye', 'jaw', 'ponytail')):
        return 0.0
    if 'forearm' in n: return -1.0          # resolved per vertex below (fade to the wrist)
    if 'upperarm' in n: return -2.0         # v9: resolved per vertex (fade to 0 at the elbow: the elbow roll must keep covering the sleeve join)
    return 1.0
rig = o.parent
pass
hand = {s: np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local) for s in 'LR'}
elbow = {s: np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local) for s in 'LR'}
W = np.zeros(len(co))
for v in me.vertices:
    tot = sum(g.weight for g in v.groups)
    if tot <= 0: continue
    acc = 0.0
    for g in v.groups:
        r = rw(vg[g.group])
        if r == -2.0:
            s = 'L' if ' L ' in vg[g.group] else 'R'
            sh = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} UpperArm'].head_local)
            ax = elbow[s] - sh; t = np.clip(np.dot(co[v.index] - sh, ax) / np.dot(ax, ax), 0, 1)
            r = float(np.clip((float(os.environ.get('UA_END', '1.0')) - t) / 0.3, 0, 1))   # full near the shoulder, 0 from t = UA_END
        elif r < 0:
            s = 'L' if ' L ' in vg[g.group] else 'R'
            ax = hand[s] - elbow[s]; t = np.clip(np.dot(co[v.index] - elbow[s], ax) / np.dot(ax, ax), 0, 1)
            r = max(0.0, 1 - float(os.environ.get('FA_FADE', '2.5')) * t)   # v8: 0 from 40 % of the forearm on, so the cuffs and their linings stay as built (r6 opened the right cuff)
        acc += r * g.weight
    W[v.index] = acc / tot
import os
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromPolygons([Vector(x) for x in C], [list(map(int, t)) for t in T])
RAY = os.environ.get('RAY') == '1'
if os.environ.get('ARMPIT', '1') == '1':   # v10: the armpit folds (master x +-0.25, z 0.395) are left as built: moving them by
    # 1-2 cm folded Meshy's armpit web so the inner faces showed (see-through: torso 40 px, sleeve R 30 px)
    for sx in (1, -1):
        dd = np.linalg.norm(co - np.array([0.25 * sx, -0.005, 0.395]), axis=1)
        W *= np.clip((dd - 0.04) / 0.05, 0, 1)
if os.environ.get('BAND'):   # v7: the hip band is fitted by band_scale.py (all layers scaled together); excluded here
    zl, zh = (float(x) for x in os.environ['BAND'].split(','))
    W *= 1 - np.clip((co[:, 2] - (zl - 0.04)) / 0.04, 0, 1) * np.clip(((zh + 0.04) - co[:, 2]) / 0.04, 0, 1)
want = np.zeros_like(co); ok = np.zeros(len(co), bool); dist = np.zeros(len(co))
# outer layer only (v6, the hidden trouser top under the shirt skirt wanted to move OUT onto M5's surface while the skirt moved
# in: the trousers poked through): a source must see free air along its normal (no own face within 3 cm)
own = BVHTree.FromPolygons([Vector(x) for x in co], [list(p.vertices) for p in me.polygons])
outer = np.ones(len(co), bool)
if os.environ.get('OUTER', '1') == '1':
    for i in range(len(co)):
        n_ = Vector(nr[i])
        if n_.length < 0.5: continue
        hit = own.ray_cast(Vector(co[i]) + n_ * 0.001, n_, 0.03)
        if hit[0] is not None: outer[i] = False
for i, p in enumerate(co):
    if not outer[i]: continue
    q, k, _ = kt.find(Vector(p))
    n = N[k]; d = float(np.dot(p - np.array(q), n)); dist[i] = d
    if abs(d) < 0.08 and np.dot(nr[i], n) > 0.5:
        want[i] = -d * n; ok[i] = True
    elif RAY and W[i] > 0:
        # v3: along our own normal (the sleeve underside faces down; its nearest M5 point was the torso side)
        nv = Vector(nr[i]); best = None
        for sgn in (-1, 1):
            hit = bvh.ray_cast(Vector(p), nv * sgn, 0.08)
            if hit[0] is not None and hit[1].dot(nv) > 0.3 and (best is None or hit[3] < best[1]):
                best = (sgn, hit[3])
        if best is not None:
            want[i] = np.array(nv) * best[0] * best[1]; ok[i] = True; dist[i] = -best[0] * best[1]
        elif os.environ.get('WEB') == '1' and 0.005 < d < 0.05:
            # v4: cloth outside M5 with no surface along its own normal (the armpit web, a flared hem): to the nearest point
            want[i] = np.array(q) - p; ok[i] = True
src = np.where(ok)[0]
ks = KDTree(len(src))
for j, i in enumerate(src): ks.insert(Vector(co[i]), j)
ks.balance()
move = np.zeros_like(co)
for i in range(len(co)):
    if W[i] <= 0: continue
    hits = ks.find_range(Vector(co[i]), RAD)
    if not hits: continue
    idx = np.array([src[h[1]] for h in hits]); dd = np.array([h[2] for h in hits])
    g = np.exp(-0.5 * (dd / SIGMA) ** 2)
    move[i] = (want[idx] * g[:, None]).sum(0) / g.sum() * W[i]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nb = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
pin = W <= 0
for _ in range(8):
    nm = move.copy()
    for i, js in enumerate(nb):
        if pin[i] or not js: continue
        nm[i] = 0.5 * move[i] + 0.5 * move[js].mean(0)
    move = nm
move *= GAIN
for v in me.vertices: v.co = Vector(co[v.index] + move[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=OUT)
np.save(OUT.replace('.blend', '_move.npy'), np.concatenate([co, move], 1))
m = np.linalg.norm(move, axis=1)
r = dict(hidden_vertices=int((~outer).sum()), outer_sources=int(ok.sum()), moved=int((m > 1e-4).sum()), move_p50_mm=float(np.percentile(m[m > 1e-4], 50) * 1000),
         move_p90_mm=float(np.percentile(m[m > 1e-4], 90) * 1000), move_max_mm=float(m.max() * 1000), gain=GAIN,
         signed_before_outer_p50_mm=float(np.percentile(dist[ok], 50) * 1000), signed_before_outer_p90_mm=float(np.percentile(dist[ok], 90) * 1000))
json.dump(r, open(REP, 'w'), indent=1); print('FIT', r)
