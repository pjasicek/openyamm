"""Weight the Dwarf to the MM9 skeleton by structure (rules of mm9_guard_claude/scripts/rig_guard.py and mm9_thrall_claude): torso bands between the spine bones, arm bands along the arm, head above a chin-nape plane,
leg bands, garments copied from or rigid on the skin under them. Tunic skirt on eight hinge bones `Skirt_*` at the belt, children of Bip01 Spine, keyed by skirt_keys.py. Exactly symmetric by construction.
Hinge pivots: knee and hip toward the inside of the bend, elbow toward the outside (Thrall, Mummy: cuts the folds).
Args: <graft blend> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
FIT, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
for o in list(bpy.data.objects):
    if o not in (arm, body): bpy.data.objects.remove(o)
B = 'Bip01 '
PIV = {'L Calf': (0, 0.025, 0), 'R Calf': (0, 0.025, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.02, 0), 'R Thigh': (0, -0.02, 0)}
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
for k, d in PIV.items(): J[B + k] = J[B + k] + np.array(d)
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
vp = np.zeros(n, int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
sk = np.nonzero(vp == 7)[0]
ztop = P[sk, 2].max(); ring = sk[P[sk, 2] > ztop - 0.06]
HZ = ztop - 0.04
cx, cy = 0.0, 0.5 * (P[ring, 1].min() + P[ring, 1].max()); rx, ry = 0.5 * np.ptp(P[ring, 0]), 0.5 * np.ptp(P[ring, 1])
ANG = np.radians([-112.5, -67.5, -22.5, 22.5, 67.5, 112.5, 157.5, -157.5])
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SFL', 'Skirt_SBL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SBR', 'Skirt_SFR']
HINGES = {nm: np.array([cx + rx * 0.9 * np.cos(a), cy + ry * 0.9 * np.sin(a), HZ]) for nm, a in zip(RING, ANG)}
print('RIG skirt top', round(ztop, 3), 'hinge z', round(HZ, 3), 'centre y', round(cy, 3), 'radii', round(rx, 3), round(ry, 3), 'bottom', round(P[sk, 2].min(), 3))
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
for k, d in PIV.items():
    e = eb[B + k]; v = Mi.to_3x3() @ Vector(d); e.head += v; e.tail += v
sp = eb[B + 'Spine']; Rt = sp.matrix.to_3x3()
for nm, h in HINGES.items():
    b = eb.new(nm); hp = Mi @ Vector(h)
    b.head = hp; b.tail = hp + Rt.col[1] * 0.08; b.align_roll(Rt.col[2]); b.parent = sp; b.use_connect = False; b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in arm.data.bones]; bidx = {b: i for i, b in enumerate(bones)}
for nm, h in HINGES.items(): J[nm] = np.array(h)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
W = np.zeros((n, len(bones)))


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def poly_param(Q, pts):
    best = np.full(len(Q), 1e9); s = np.zeros(len(Q)); L0 = 0.0
    for k, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        ab = b - a; L = np.linalg.norm(ab)
        t = (Q - a) @ ab / (L * L)
        tc = np.clip(t, 0, 1)
        if k == 0: tc = np.minimum(t, 1)
        if k == len(pts) - 2: tc = np.maximum(tc, 0) if k else t
        d = np.linalg.norm(Q - a - np.outer(tc, ab), axis=1)
        m = d < best
        best[m] = d[m]; s[m] = L0 + tc[m] * L
        L0 += L
    return s, best


def add(ids, name, w):
    W[ids, bidx[name]] += w


# spine hats: Spine, Spine1, and MM9's "Neck" node, which carries the shoulders: it is the upper chest
Z0, Z1, Z2 = 0.02, 0.15, 0.29
def torso(ids):
    z = P[ids, 2]
    a = 1 - sstep(z, Z0, Z1); c = sstep(z, Z1, Z2); b = 1 - a - c
    add(ids, B + 'Spine', a); add(ids, B + 'Spine1', b); add(ids, B + 'Neck', c)


ids = np.nonzero(vp == 1)[0]
torso(ids)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd = [J[f'{B}{s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & (vp == 1))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua)
    # across the armpit: the arm starts where the point lies outside a plane through the shoulder, down the torso's flank
    wa = sstep(t, -0.05, 0.07) * sstep(np.abs(P[q, 0]), 0.17, 0.235)
    we = sstep(t, Lu - 0.06, Lu + 0.06)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa * (1 - we)); add(q, f'{B}{s} Forearm', wa * we)
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    add(q, f'{B}{s} Hand', 1.0)
# shoulder plates and trims: the torso's bands, their outer corners take a share of the arm so that a raised arm does not run through them
ids = np.nonzero(vp == 12)[0]
torso(ids)
for s, sx in (('R', -1), ('L', 1)):
    q = ids[np.sign(P[ids, 0]) == sx]
    wa = 0.5 * sstep(np.abs(P[q, 0]), 0.17, 0.26)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa)
# head: rigid helm, horns, eyes, face with beard; the neck tube runs from the head into the chest
q = np.nonzero(np.isin(vp, [20, 21, 22, 23]))[0]; add(q, B + 'Head', 1.0)
q = np.nonzero(vp == 24)[0]
wh = sstep(P[q, 2], 0.335, 0.40)
add(q, B + 'Head', wh); add(q, B + 'Neck', 1 - wh)
# belt: spine block
q = np.nonzero(vp == 9)[0]; add(q, B + 'Spine', 1.0)
# skirt: hinges round the ring, by height
q = np.nonzero(vp == 7)[0]
ang = np.arctan2(P[q, 1] - cy, P[q, 0] - cx)
r = sstep(HZ + 0.015 - P[q, 2], 0.0, 0.09)
A = np.sort(ANG); order = np.argsort(ANG)
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
A2 = np.r_[A, A[0] + 2 * np.pi]
sw = np.zeros((len(q), 8))
for k in range(8):
    mm = (aa >= A2[k]) & (aa < A2[k + 1])
    u = sstep((aa[mm] - A2[k]) / (A2[k + 1] - A2[k]), 0, 1)
    sw[mm, k] = 1 - u; sw[mm, (k + 1) % 8] = u
for k in range(8):
    add(q, RING[order[k]], sw[:, k] * r)
add(q, B + 'Spine', 1 - r)
# legs
for s, sx in (('R', -1), ('L', 1)):
    th, ca, fo, to = [J[f'{B}{s} {x}'] for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
    q = np.nonzero((vp == 5) & ((np.sign(P[:, 0]) == sx) | (P[:, 0] == 0)))[0]
    t, d = poly_param(P[q], [th, ca, fo])
    Lt = np.linalg.norm(ca - th)
    wt = sstep(t, -0.07, 0.05) * sstep(np.abs(P[q, 0]), 0.0, 0.03)
    wk = sstep(t, Lt - 0.06, Lt + 0.06)
    if s == 'R': W[q] = 0
    else: W[q[P[q, 0] > 0]] = 0
    m = P[q, 0] == 0
    add(q, f'{B}{s} Thigh', wt * (1 - wk)); add(q, f'{B}{s} Calf', wt * wk)
    add(q[~m], B + 'Spine', (1 - wt)[~m])
    if s == 'R': add(q[m], B + 'Spine', (1 - wt)[m])
    q = np.nonzero((vp == 6) & (np.sign(P[:, 0]) == sx))[0]
    z = P[q, 2]
    wf = 1 - sstep(z, fo[2] - 0.03, fo[2] + 0.05)
    # the toe hinge: across the ball, along our foot
    fd = to[:2] - fo[:2]; fd = fd / np.linalg.norm(fd)
    al = (P[q, :2] - to[:2]) @ fd
    wy = sstep(al, -0.02, 0.03) * (1 - sstep(z, to[2] + 0.03, to[2] + 0.07))
    add(q, f'{B}{s} Calf', 1 - wf); add(q, f'{B}{s} Foot', wf * (1 - wy)); add(q, f'{B}{s} Toe0', wf * wy)
    q = np.nonzero((vp == 11) & (np.sign(P[:, 0]) == sx))[0]; add(q, f'{B}{s} Calf', 1.0)
# soften the bands inside each garment (2 passes)
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [4, 9, 11, 20, 21, 22, 23])
    new[keep] = W[keep]
    W = new
order_ = np.argsort(-W, axis=1)
for i in range(n):
    keep = order_[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for b in bones: body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = arm; body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
rep = dict(verts=n, tris=len(me.polygons), usage={bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0.5).any()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep)[:700])
