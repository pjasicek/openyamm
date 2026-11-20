"""(Werewolf copy of mm8_lizardman_peasant_rebuild_claude/scripts/rig_liz.py: no neck joint on BIGFOOT, toe joint.)
Structural weights for the fitted lizardman on the MM9 LIZARDORC skeleton (playbook: by structure, not by
distance; rules after mm6_gua_rebuild_claude/scripts/rig_gua.py). Bind = the posed mesh of fit_liz.py.
- limb membership by the nearest limb segment (transient-skin labels of the fit), smoothed over the mesh;
- arms: clavicle -> upper arm -> forearm -> hand bands by the position along the bent arm (shoulder band SH, elbow EL,
  wrist WR metres either side of the joint); legs: thigh -> calf -> foot bands (KN, AN);
- torso: Pelvis .. Spine3 by height between the joint heights; neck and head along the neck chain, everything above a
  plane through the head joint (normal = neck->head) on the head;
- skirt and apron (below the belt, off the leg axis): pelvis fading into the side's thigh towards the hem (SKIRT share);
- small pieces (fringe blades, collar teeth): rigid, the mean weights of the nearest other-piece vertices;
- four influences, normalised. Fingers: fingers_liz.py. Args: <fit blend> <out blend> <report json>"""
import bpy, sys, json, os
import numpy as np
from mathutils.kdtree import KDTree
FIT, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
SH, EL, WR, KN, AN = 0.05, 0.045, 0.03, 0.06, 0.04
SKIRT = 0.55; SMALL = 260; ARM_R, LEG_R = 0.11, 0.14
HN0, HN1 = 0.10, 0.04          # head ramp along neck->head (lizardorc: MM9 bends the neck only at Head)
HIP0, HIP1 = 0.06, 0.16        # hip band: pelvis above belt+HIP0, thigh below belt-HIP1
LEGCORE = 0.105                 # thigh skin within this of the leg axis is leg, not skirt
bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
JJ = json.load(open(FIT + '.joints.json'))
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
HAS = set(J)
NECK = 'Bip01 Neck' if 'Bip01 Neck' in HAS else 'Bip01 Spine3'
DEFORM = [b for b in ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head'] if b in HAS] + \
    [f'Bip01 {S} {b}' for S in 'LR' for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0') if f'Bip01 {S} {b}' in HAS]
bi = {b: i for i, b in enumerate(DEFORM)}
W = np.zeros((n, len(DEFORM)))
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
def smooth(A, it, k=0.5):
    for _ in range(it):
        A = (1 - k) * A + k * np.array([A[nb].mean(0) if nb else A[i] for i, nb in enumerate(nbr)])
    return A
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def seg_t(Q, a, b):
    ab = b - a; t = (Q - a) @ ab / (ab @ ab); tc = np.clip(t, 0, 1)
    return t, np.linalg.norm(Q - a - np.outer(tc, ab), axis=1)
cx = J['Bip01 Pelvis'][0]
side = np.where(P[:, 0] >= cx, 'L', 'R')
# ---- membership: nearest structure (torso chain, neck+head, arm incl. fingers, leg incl. toes)
belt = J['Bip01 Pelvis'][2] + 0.04
ext = {}
for S in 'LR':
    s = side == S
    h = J[f'Bip01 {S} Hand']; f = J[f'Bip01 {S} Forearm']; ax = (h - f) / np.linalg.norm(h - f)
    hs = s & (np.linalg.norm(P - h, axis=1) < 0.32) & (((P - h) @ ax) > 0)
    ext[f'tip{S}'] = P[hs][np.argmax(np.linalg.norm(P[hs] - h, axis=1))]
    fo = J[f'Bip01 {S} Foot']
    fs = s & (P[:, 2] < fo[2] + 0.03) & (np.linalg.norm((P - fo)[:, :2], axis=1) < 0.3)
    ext[f'toe{S}'] = P[fs][np.argmin(P[fs, 1])]
hp = J['Bip01 Head']; snout = P[np.argmin(P[:, 1])]
def dseg(a, b): return seg_t(P, a, b)[1]
D = {}
D['torso'] = np.min([dseg(J[a], J[b]) for a, b in (('Bip01 Pelvis', 'Bip01 Spine1'), ('Bip01 Spine1', 'Bip01 Spine3'))]
                    + ([dseg(J['Bip01 Spine3'], J[NECK])] if NECK != 'Bip01 Spine3' else []), 0) - 0.10
D['head'] = np.minimum(dseg(J[NECK], hp), dseg(hp, snout)) - 0.06
for S in 'LR':
    a = np.min([dseg(J[f'Bip01 {S} UpperArm'], J[f'Bip01 {S} Forearm']), dseg(J[f'Bip01 {S} Forearm'], J[f'Bip01 {S} Hand']),
                dseg(J[f'Bip01 {S} Hand'], ext[f'tip{S}'])], 0)
    l = np.min([dseg(J[f'Bip01 {S} Thigh'], J[f'Bip01 {S} Calf']), dseg(J[f'Bip01 {S} Calf'], J[f'Bip01 {S} Foot']),
                dseg(J[f'Bip01 {S} Foot'], ext[f'toe{S}'])], 0)
    D['arm' + S] = np.where(side == S, a, 9.0)
    D['leg' + S] = np.where((side == S) & (P[:, 2] < belt + 0.02), l, 9.0)
keys = list(D); M = np.stack([D[k] for k in keys], 1); lab = M.argmin(1)
isarm = np.isin(lab, [keys.index('armL'), keys.index('armR')])
isleg = np.isin(lab, [keys.index('legL'), keys.index('legR')])
dL = np.minimum(D['legL'], D['legR'])
legcore = isleg & (dL < LEGCORE)
mem = np.zeros((n, 3)); mem[isarm, 0] = 1; mem[isleg, 1] = 1; mem[~isarm & ~isleg, 2] = 1
mem = smooth(mem, 3, 0.5)
# ---- arm weights
WA = np.zeros((n, len(DEFORM)))
for S in 'LR':
    c, u, f, h = (J[f'Bip01 {S} {b}'] for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand'))
    # arc-length coordinate along the bent arm: nearest segment's parameter
    tu, du = seg_t(P, u, f); tf, df = seg_t(P, f, h)
    Lu, Lf = np.linalg.norm(f - u), np.linalg.norm(h - f)
    s_u = tu * Lu; s_f = Lu + tf * Lf
    th, dh_ = seg_t(P, h, ext[f'tip{S}'])
    sarc = np.where(du <= df, s_u, s_f)
    sarc = np.where((dh_ < np.minimum(du, df)) & (th > 0), Lu + Lf + WR + th * 0.01, sarc)
    w_u = sstep(sarc, -SH * 0.6, SH * 0.4)
    w_f = sstep(sarc, Lu - EL, Lu + EL)
    w_h = sstep(sarc, Lu + Lf - WR, Lu + Lf + WR * 0.6)
    s = side == S
    WA[s, bi[f'Bip01 {S} Clavicle']] = (1 - w_u)[s]
    WA[s, bi[f'Bip01 {S} UpperArm']] = (w_u * (1 - w_f))[s]
    WA[s, bi[f'Bip01 {S} Forearm']] = (w_f * (1 - w_h))[s]
    WA[s, bi[f'Bip01 {S} Hand']] = w_h[s]
# ---- leg weights
WL = np.zeros((n, len(DEFORM)))
for S in 'LR':
    t, c_, fo = (J[f'Bip01 {S} {b}'] for b in ('Thigh', 'Calf', 'Foot'))
    tt, dt = seg_t(P, t, c_); tc, dc = seg_t(P, c_, fo)
    Lt, Lc = np.linalg.norm(c_ - t), np.linalg.norm(fo - c_)
    sarc = np.where(dt <= dc, tt * Lt, Lt + tc * Lc)
    tz, dz = seg_t(P, fo, ext[f'toe{S}'])
    below_ankle = (P[:, 2] < fo[2] + 0.02) | ((dz < np.minimum(dt, dc)) & (tz > 0))
    sarc = np.where(below_ankle, np.maximum(sarc, Lt + Lc + AN), sarc)
    w_c = sstep(sarc, Lt - KN, Lt + KN); w_f = sstep(sarc, Lt + Lc - AN, Lt + Lc + AN * 0.5)
    w_t = sstep(P[:, 2], belt + HIP0, belt - HIP1)          # hip band: pelvis above, thigh below
    s = side == S
    WL[s, bi['Bip01 Pelvis']] = ((1 - w_t) * (1 - w_c))[s]
    WL[s, bi[f'Bip01 {S} Thigh']] = (w_t * (1 - w_c))[s]
    WL[s, bi[f'Bip01 {S} Calf']] = (w_c * (1 - w_f))[s]
    WL[s, bi[f'Bip01 {S} Foot']] = w_f[s]
    if f'Bip01 {S} Toe0' in bi:
        toe = J[f'Bip01 {S} Toe0']; tt0, _ = seg_t(P, fo, toe)
        wt = sstep(tt0, 0.75, 1.05) * below_ankle
        WL[s, bi[f'Bip01 {S} Toe0']] = (w_f * wt)[s]; WL[s, bi[f'Bip01 {S} Foot']] = (w_f * (1 - wt))[s]
# skirt (leg members off the leg core, above the knee): pelvis fading to the thigh by SKIRT at the hem
sk = isleg & ~legcore & (P[:, 2] > J['Bip01 L Calf'][2] - 0.05)
hem = P[sk, 2].min() if sk.any() else belt - 0.4
for S in 'LR':
    s = sk & (side == S)
    a = SKIRT * sstep(P[:, 2], belt, hem)
    WL[s] = 0; WL[s, bi['Bip01 Pelvis']] = (1 - a)[s]; WL[s, bi[f'Bip01 {S} Thigh']] = a[s]
# ---- body weights: torso by height, neck and head along the neck chain
WB = np.zeros((n, len(DEFORM)))
chain = [b for b in ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck'] if b in HAS]
zs = [J[b][2] for b in chain]
z = P[:, 2]
for k, b in enumerate(chain):
    lo = zs[k - 1] if k > 0 else -9; hi = zs[k + 1] if k + 1 < len(chain) else 9
    up = sstep(z, lo, zs[k]) if k > 0 else np.ones(n)
    dn = 1 - sstep(z, zs[k], hi) if k + 1 < len(chain) else np.ones(n)
    WB[:, bi[b]] = up * dn
hn = J['Bip01 Head'] - J[NECK]; hn /= np.linalg.norm(hn)
hd = (P - J['Bip01 Head']) @ hn
wh = np.maximum(sstep(hd, -HN0, HN1), sstep(P[:, 2], J['Bip01 Head'][2] - 0.01, J['Bip01 Head'][2] + 0.04))
WB *= (1 - wh)[:, None]; WB[:, bi['Bip01 Head']] += wh
# shoulders: body vertices near the clavicles (top of the chest, beside the neck) share the clavicle
for S in 'LR':
    c = J[f'Bip01 {S} Clavicle']; u = J[f'Bip01 {S} UpperArm']
    tt, d = seg_t(P, c, u)
    wcl = (1 - sstep(d, 0.06, 0.11)) * sstep(tt, 0.1, 0.6) * (side == S) * (1 - wh)
    WB *= (1 - 0.6 * wcl)[:, None]; WB[:, bi[f'Bip01 {S} Clavicle']] += 0.6 * wcl
W = mem[:, 0:1] * WA + mem[:, 1:2] * WL + mem[:, 2:3] * WB
W = W / np.maximum(W.sum(1, keepdims=True), 1e-9)
W = smooth(W, 2, 0.3)
# ---- small pieces rigid
key = {}; vid = np.array([key.setdefault(tuple(np.round(c, 5)), len(key)) for c in P])
par = list(range(len(key)))
def find(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for p in me.polygons:
    vs = [vid[v] for v in p.vertices]
    for x in vs[1:]:
        ra, rb = find(vs[0]), find(x)
        if ra != rb: par[ra] = rb
comp = np.array([find(vid[i]) for i in range(n)])
ids, cnt = np.unique(comp, return_counts=True); size = dict(zip(ids, cnt))
bigi = np.nonzero(np.array([size[c] >= SMALL for c in comp]))[0]
kd = KDTree(len(bigi))
for k, i in enumerate(bigi): kd.insert(P[i], k)
kd.balance()
nsmall = 0
for c in ids:
    if size[c] >= SMALL: continue
    sel = np.nonzero(comp == c)[0]; nsmall += 1
    acc = np.zeros(len(DEFORM))
    for i in sel:
        for co, k, d in kd.find_n(P[i], 3): acc += W[bigi[k]]
    W[sel] = acc / acc.sum()
order = np.argsort(-W, axis=1)
for i in range(n):
    row = np.zeros(len(DEFORM)); k = order[i, :4]; row[k] = W[i, k]; row[row < 0.02] = 0
    W[i] = row / row.sum()
for g in list(body.vertex_groups): body.vertex_groups.remove(g)
for b in DEFORM: body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]: body.vertex_groups[DEFORM[j]].add([i], float(W[i, j]), 'REPLACE')
for b in arm.data.bones: b.use_deform = b.name in DEFORM
for m in list(body.modifiers): body.modifiers.remove(m)
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
np.save(OUT + '.W.npy', W)
rep = {'ext': {k: v.round(3).tolist() for k, v in ext.items()}, 'small_pieces': nsmall, 'arm_verts': int(isarm.sum()), 'leg_verts': int(isleg.sum()), 'skirt_verts': int(sk.sum()),
       'dominant': {DEFORM[j]: int((W.argmax(1) == j).sum()) for j in range(len(DEFORM))}}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(rep))
