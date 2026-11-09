"""PeasantM2 (from mm9_njam_claude/scripts/rig_nj.py): Meshy head kept (face shell 20 with the chest V skin, hair 21 hanging to the
shoulder blades: Head above the ear line, then Neck/Spine3 so the long hair follows the back); bell sleeves weighted along the arm out
to 17 cm from the arm line on the forearm; belt strap end (9) and buckle (10) on the Spine; trousers 5 and boots 6 as the hose/boots.
Njam (from mm9_nobleman_claude/scripts/rig_nb.py). Changes: no fur mantle part (paint); hair helmet (21) rigid on the Head (MM9's
Bip01 Ponytail1 swings up to 75 deg in wince2 on a short bob: not used); skirt hinges are NJAM.abc's first segments (re-parented to
the Spine by reparent_skirt.py; the second segments Bone07/23/15/11/03/19 never move in any clip and carry nothing); arm bands also
limited by distance from the arm line (the A-pose arm passes the coat waist); tall boots take the leg bands down to the ankle.
Weight the Nobleman to the MM9 skeleton by structure (mm9_highwayman_claude/scripts/rig_hw.py): torso bands between the spine bones, arm bands along the arm, head above a chin-nape plane, leg bands.
Doublet skirt on MM9's own six hinge bones (Bone06/14/18/02/10/22, moved onto our ring at the belt, rest rotations kept), keyed by skirt_keys.py. Exactly symmetric by construction.
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
PIV = {'L Calf': (0, 0.05, 0), 'R Calf': (0, 0.05, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.025, 0), 'R Thigh': (0, -0.025, 0)}
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
ANG = np.radians([-90.0, -45.0, 50.0, 90.0, 130.0, -135.0])   # NJAM.abc's hinge directions
RING = ['Bone06', 'Bone14', 'Bone18', 'Bone02', 'Bone10', 'Bone22']          # front centre, then round by the figure's left
HINGES = {nm: np.array([cx + rx * 0.9 * np.cos(a), cy + ry * 0.9 * np.sin(a), HZ]) for nm, a in zip(RING, ANG)}
print('RIG skirt top', round(ztop, 3), 'hinge z', round(HZ, 3), 'centre y', round(cy, 3), 'radii', round(rx, 3), round(ry, 3), 'bottom', round(P[sk, 2].min(), 3))
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
for k, d in PIV.items():
    e = eb[B + k]; v = Mi.to_3x3() @ Vector(d); e.head += v; e.tail += v
for nm, h in HINGES.items():
    e = eb[nm]; v = Mi @ Vector(h) - e.head; e.head += v; e.tail += v
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


# spine hats centred on each bone's middle
SP = [('Spine', 0.15), ('Spine1', 0.30), ('Spine2', 0.43), ('Spine3', 0.55)]
def torso(ids):
    z = P[ids, 2]; ax = np.abs(P[ids, 0])
    W_ = np.zeros((len(ids), 4))
    hs = [h for _, h in SP]
    W_[:, 0] = 1 - sstep(z, hs[0], hs[1])
    W_[:, 1] = sstep(z, hs[0], hs[1]) * (1 - sstep(z, hs[1], hs[2]))
    W_[:, 2] = sstep(z, hs[1], hs[2]) * (1 - sstep(z, hs[2], hs[3]))
    W_[:, 3] = sstep(z, hs[2], hs[3])
    wc = W_[:, 3] * sstep(ax, 0.09, 0.19) * sstep(z, 0.50, 0.58)
    for k, (nm, _) in enumerate(SP):
        add(ids, B + nm, W_[:, k] - (wc if k == 3 else 0))
    for s, sx in (('R', -1), ('L', 1)):
        m = np.sign(P[ids, 0]) == sx
        W[ids[m], bidx[f'{B}{s} Clavicle']] += wc[m]


ids = np.nonzero(vp == 1)[0]
torso(ids)
for s, sx in (('R', -1), ('L', 1)):
    ua, fa, hd, cl = [J[f'{B}{s} {x}'] for x in ('UpperArm', 'Forearm', 'Hand', 'Clavicle')]
    q = np.nonzero((np.sign(P[:, 0]) == sx) & (vp == 1))[0]
    t, d = poly_param(P[q], [ua, fa, hd])
    Lu = np.linalg.norm(fa - ua)
    zz = sstep(P[q, 2], 0.45, 0.56)
    dl = np.where(t > 0.5 * Lu, 0.17, 0.11)   # bell sleeve: wide past the elbow
    wa = sstep(t, -0.10, 0.10) * sstep(np.abs(P[q, 0]), 0.150 - 0.030 * zz, 0.175 + 0.045 * zz) * (1 - sstep(d, dl - 0.035, dl))   # sleeve's inner wall wholly on the arm past the armpit crease (|x| 0.16 = torso flank)
    wa = np.maximum(wa, sstep(np.abs(P[q, 0]), 0.205, 0.225) * (1 - sstep(P[q, 2], 0.40, 0.46)) * sstep(t, 0.0, 0.08))   # the bell cuff beyond the torso's width: all arm
    we = sstep(t, Lu - 0.075, Lu + 0.075)
    W[q] *= (1 - wa)[:, None]
    add(q, f'{B}{s} UpperArm', wa * (1 - we)); add(q, f'{B}{s} Forearm', wa * we)
    q = np.nonzero((vp == 4) & (np.sign(P[:, 0]) == sx))[0]
    hd_ = (hd - fa) / np.linalg.norm(hd - fa); wh_ = sstep((P[q] - hd) @ hd_, -0.025, 0.015)   # Meshy's hand piece runs up into the sleeve: forearm part on the Forearm
    add(q, f'{B}{s} Hand', wh_); add(q, f'{B}{s} Forearm', 1 - wh_)
# standing collar: its top follows the neck a little
q = np.nonzero((vp == 1) & (P[:, 2] > 0.60) & (np.abs(P[:, 0]) < 0.125))[0]
wn = 0.45 * sstep(P[q, 2], 0.62, 0.67)
W[q] *= (1 - wn)[:, None]; add(q, B + 'Neck', wn)
# head: the face shell below a chin-nape plane has the neck bands (and the chest V skin the spine); the hair is Head above the ears and
# follows the neck and upper back below, where it hangs over the shoulders
q = np.nonzero(vp == 20)[0]
a, b = np.array([0, -0.06, 0.672]), np.array([0, 0.09, 0.71])
tv = (b - a) / np.linalg.norm(b - a); nrm = np.cross(tv, [1, 0, 0]); nrm *= np.sign(nrm[2])
wh = sstep((P[q] - a) @ nrm, -0.03, 0.03)
rn = np.hypot(P[q, 0] / 0.06, (P[q, 1] - 0.02) / 0.07)
wh = np.where(P[q, 2] > 0.72, np.maximum(wh, sstep(rn, 0.95, 1.08)), wh)
add(q, B + 'Head', wh)
wb = (1 - wh) * (1 - sstep(P[q, 2], 0.585, 0.65))
add(q, B + 'Spine3', wb); add(q, B + 'Neck', 1 - wh - wb)
q = np.nonzero(vp == 21)[0]
wh = sstep(P[q, 2], 0.60, 0.70); ws = (1 - wh) * (1 - sstep(P[q, 2], 0.58, 0.66))
add(q, B + 'Head', wh); add(q, B + 'Spine3', ws); add(q, B + 'Neck', 1 - wh - ws)
# belt, buckle: spine block
q = np.nonzero(np.isin(vp, (9, 10)))[0]; add(q, B + 'Spine', 1.0)
# skirt: hinges round the ring, by height
q = np.nonzero(vp == 7)[0]
ang = np.arctan2(P[q, 1] - cy, P[q, 0] - cx)
r = sstep(HZ + 0.015 - P[q, 2], 0.0, 0.11)
A = np.sort(ANG); order = np.argsort(ANG)
aa = np.where(ang < A[0], ang + 2 * np.pi, ang)
A2 = np.r_[A, A[0] + 2 * np.pi]
sw = np.zeros((len(q), 6))
for k in range(6):
    mm = (aa >= A2[k]) & (aa < A2[k + 1])
    u = sstep((aa[mm] - A2[k]) / (A2[k + 1] - A2[k]), 0, 1)
    sw[mm, k] = 1 - u; sw[mm, (k + 1) % 6] = u
for k in range(6):
    add(q, RING[order[k]], sw[:, k] * r)
add(q, B + 'Spine', 1 - r)
# legs
for s, sx in (('R', -1), ('L', 1)):
    th, ca, fo, to = [J[f'{B}{s} {x}'] for x in ('Thigh', 'Calf', 'Foot', 'Toe0')]
    q = np.nonzero(((vp == 5) | ((vp == 6) & (P[:, 2] > fo[2] + 0.05))) & ((np.sign(P[:, 0]) == sx) | (P[:, 0] == 0)))[0]
    t, d = poly_param(P[q], [th, ca, fo])
    Lt = np.linalg.norm(ca - th)
    wt = sstep(t, -0.15, 0.09) * sstep(np.abs(P[q, 0]), 0.0, 0.03)
    wk = sstep(t, Lt - 0.085, Lt + 0.085)
    if s == 'R': W[q] = 0
    else: W[q[P[q, 0] > 0]] = 0
    m = P[q, 0] == 0
    add(q, f'{B}{s} Thigh', wt * (1 - wk)); add(q, f'{B}{s} Calf', wt * wk)
    add(q[~m], B + 'Spine', (1 - wt)[~m])
    if s == 'R': add(q[m], B + 'Spine', (1 - wt)[m])
    q = np.nonzero((vp == 6) & (np.sign(P[:, 0]) == sx) & (P[:, 2] <= fo[2] + 0.05))[0]
    z = P[q, 2]; y = P[q, 1]
    wf = 1 - sstep(z, fo[2] - 0.03, fo[2] + 0.05)
    # the toe hinge: across the ball, along our foot
    fd = to[:2] - fo[:2]; fd = fd / np.linalg.norm(fd)
    al = (P[q, :2] - to[:2]) @ fd
    wy = sstep(al, -0.02, 0.03) * (1 - sstep(z, to[2] + 0.03, to[2] + 0.07))
    add(q, f'{B}{s} Calf', 1 - wf); add(q, f'{B}{s} Foot', wf * (1 - wy)); add(q, f'{B}{s} Toe0', wf * wy)
# soften the bands inside each garment (2 passes)
for it in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    new = 0.6 * W + 0.4 * avg
    keep = np.isin(vp, [4, 9, 10])
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
