"""Fit the cleaned Meshy body to the ORIGINAL MM9 Lich skeleton and weight it (Yrsa route, by parts: the Meshy return is
well separated). Bones are translated, never rotated, so MM9's local clip rotations play unchanged.

Args: <in blend: Body with face attr part> <mm9 glb> <out blend> <report json> <config json>

Joints: spine/neck/head stay at MM9's positions (the mesh is shifted in y to the belt); legs by boot and pants slices; arms
from the separate hand parts: geodesic level sets from the forearm end find the five fingers by connectivity (a finger =
the earliest component that never splits again), the wrist sits `palm` before the first split, the elbow keeps MM9's
forearm length along the measured forearm.
Fingers: three joints per finger on the mesh centreline: MM9's two (proximal, distal; rest frames unchanged) plus one new
(`Bip01 <S> Tip<n>`, rest frame = the distal's) driven by finger_alias from the distal curl. MM9's left pinky has no
proximal bone (socket LHand1 sits in its place): Finger41 is its proximal, `L Tip41`/`L Tip42` follow.
Weights: by part. Hands by connectivity, 2 cm blends at joints; legs by height; cloak and robe by MM9's rigid skin
(label transfer, diffusion), arm bands on the cloak's sleeves; head parts on Head, neck on Neck.
"""
import bpy, bmesh, sys, json, heapq
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, MM9, OUT, REP, CFG = argv
cfg = json.load(open(CFG))
rep = {}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [o for o in bpy.data.objects if o not in existing]
arm = next(o for o in new if o.type == 'ARMATURE')
arm.name = 'MM9_Rig'
if arm.animation_data:
    arm.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
mm9 = next(o for o in new if o.type == 'MESH' and 'd_lich' in o.name)
for o in [o for o in new if o is not arm and o is not mm9]:
    bpy.data.objects.remove(o)
mm9.name = 'MM9_Mesh'
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
names = list(J)

nf = len(me.polygons)
fpart = np.zeros(nf, np.int32); me.attributes['part'].data.foreach_get('value', fpart)
F = np.array([list(p.vertices) for p in me.polygons])
co = np.array([v.co for v in me.vertices]); nv = len(co)
vpart = np.zeros(nv, np.int32); vpart[F.ravel()] = np.repeat(fpart, 3)
co[:, 1] += cfg['y_shift']
for v, c in zip(me.vertices, co):
    v.co = Vector(c)
P = cfg['parts']
adj = [[] for _ in range(nv)]
for t in F:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        i, j = int(t[a]), int(t[b])
        w = float(np.linalg.norm(co[i] - co[j]))
        adj[i].append((j, w)); adj[j].append((i, w))
newJ = {n: J[n].copy() for n in names}


def geodesic(ids, seeds):
    D = {i: 1e9 for i in ids}; h = []
    for s in seeds:
        D[s] = 0.0; heapq.heappush(h, (0.0, s))
    while h:
        x, i = heapq.heappop(h)
        if x > D[i]:
            continue
        for j, w in adj[i]:
            if j in D and x + w < D[j]:
                D[j] = x + w; heapq.heappush(h, (D[j], j))
    return D


def components(keep):
    keep = set(keep); seen = set(); comps = []
    for i in keep:
        if i in seen:
            continue
        st = [i]; seen.add(i); c = []
        while st:
            x = st.pop(); c.append(x)
            for j, _ in adj[x]:
                if j in keep and j not in seen:
                    seen.add(j); st.append(j)
        comps.append(c)
    return comps


def fingers_of(ids, D):
    """Sweep t upward; a finger is the earliest component that never splits again."""
    dmax = max(D.values())
    active = [(0.0, list(ids), list(ids))]   # (birth t, verts at birth, current verts)
    done = []
    t = 0.05
    while t < dmax and active:
        nxt = []
        for birth, born, c in active:
            sub = components([i for i in c if D[i] > t])
            sub = [q for q in sub if max(D[i] for i in q) > t + 0.035]    # a bump, not a branch
            if len(sub) == 0:
                done.append((birth, born))
            elif len(sub) == 1:
                nxt.append((birth, born, sub[0]))
            else:
                nxt += [(t, q, q) for q in sub]
        active = nxt
        t += 0.004
    done += [(b, v) for b, v, _ in active]
    out = [{'birth': b, 'verts': c, 'len': max(D[i] for i in c) - b} for b, c in done]
    out.sort(key=lambda x: -x['len'])
    return out


def centreline(c, D, d0, d1, n=24):
    ds = np.array([D[i] for i in c]); P_ = co[c]
    edges = np.linspace(d0, d1, n + 1); pts = []; dv = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (ds >= a) & (ds < b + 1e-6)
        if m.sum():
            pts.append(P_[m].mean(0)); dv.append(ds[m].mean())
    return np.array(dv), np.array(pts)


hand_w = {}      # vert -> {bone: w}
tip_bones = {}   # new bone -> (parent, template, position)
fingers_rep = {}
for side in ('L', 'R'):
    S = side
    pid = P['hand'][side]
    ids = np.unique(F[fpart == pid]).tolist()
    idset = set(ids)
    zt = max(co[i, 2] for i in ids)
    ring = [i for i in ids if co[i, 2] > zt - 0.03]
    D = geodesic(ids, ring)
    fs = fingers_of(ids, D)[:5]
    first = min(f['birth'] for f in fs)
    wrist_d = first - cfg['palm']
    band = [i for i in ids if abs(D[i] - wrist_d) < 0.012]
    wrist = co[band].mean(0)
    ringc = co[ring].mean(0)
    fa = ringc - wrist; fa /= np.linalg.norm(fa)
    flen = np.linalg.norm(J[f'Bip01 {S} Hand'] - J[f'Bip01 {S} Forearm'])
    newJ[f'Bip01 {S} Hand'] = wrist
    newJ[f'Bip01 {S} Forearm'] = wrist + fa * flen
    # order the fingers by the MM9 thumb -> pinky direction across the hand
    mm9tips = [f'Bip01 {S} Finger{k}' for k in (0, 1, 2, 3)]
    across = J[f'Bip01 {S} Finger0'] - J[f'Bip01 {S} Finger3']; across /= np.linalg.norm(across)
    for f in fs:
        dm = min(D[i] for i in f['verts']); f['base'] = co[[i for i in f['verts'] if D[i] < dm + 0.012]].mean(0)
        f['x'] = float((f['base'] - wrist) @ across)
    fs.sort(key=lambda f: -f['x'])
    rep_side = []
    for k, f in enumerate(fs):
        d0 = f['birth'] - 0.012
        d1 = max(D[i] for i in f['verts'])
        # verts of the finger including the short stretch below the split
        below = [i for i in ids if f['birth'] - 0.012 < D[i] <= f['birth'] and
                 np.linalg.norm(co[i] - f['base']) < 0.02]
        vs = list(set(f['verts']) | set(below))
        dv, pts = centreline(vs, D, d0, d1)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]; L_ = s[-1]
        fr = cfg['thumb_fracs'] if k == 0 else cfg['finger_fracs']
        joints = [pts[np.searchsorted(s, q * L_).clip(0, len(pts) - 1)] for q in fr]
        ds = [dv[np.searchsorted(s, q * L_).clip(0, len(pts) - 1)] for q in fr]
        if side == 'L' and k == 4:
            # MM9's left pinky has no proximal bone (the socket LHand1 sits in its place) and Finger41 swings from the
            # hand; our pinky follows the ring finger's curl on its own chain (rest frames of Finger3 / Finger31)
            b0, b1, b2 = 'Bip01 L Pinky1', 'Bip01 L Pinky2', 'Bip01 L Tip4'
            tip_bones[b0] = ('Bip01 L Hand', 'Bip01 L Finger3', joints[0])
            tip_bones[b1] = (b0, 'Bip01 L Finger31', joints[1]); tip_bones[b2] = (b1, 'Bip01 L Finger31', joints[2])
        else:
            b0, b1 = f'Bip01 {S} Finger{k}', f'Bip01 {S} Finger{k}1'
            b2 = f'Bip01 {S} Tip{k}'
            newJ[b0] = joints[0]; newJ[b1] = joints[1]
            tip_bones[b2] = (b1, b1, joints[2])
        blend = 0.012
        chain = [(b0, ds[0]), (b1, ds[1]), (b2, ds[2])]
        for i in vs:
            d = D[i]
            w = {}
            if d < ds[0] - blend:
                w = {f'Bip01 {S} Hand': 1.0}
            elif d < ds[0] + blend:
                a = (d - (ds[0] - blend)) / (2 * blend); w = {f'Bip01 {S} Hand': 1 - a, b0: a}
            elif d < ds[1] - blend:
                w = {b0: 1.0}
            elif d < ds[1] + blend:
                a = (d - (ds[1] - blend)) / (2 * blend); w = {b0: 1 - a, b1: a}
            elif d < ds[2] - blend:
                w = {b1: 1.0}
            elif d < ds[2] + blend:
                a = (d - (ds[2] - blend)) / (2 * blend); w = {b1: 1 - a, b2: a}
            else:
                w = {b2: 1.0}
            hand_w[i] = w
        rep_side.append({'len': round(float(L_), 3), 'birth': round(float(f['birth']), 3),
                         'base': [round(float(x), 3) for x in f['base']]})
    fingers_rep[side] = rep_side
    # palm and forearm by geodesic distance
    for i in ids:
        if i in hand_w:
            continue
        d = D[i]
        a = np.clip((d - (wrist_d - 0.02)) / 0.04, 0, 1)
        hand_w[i] = {f'Bip01 {S} Forearm': 1 - a, f'Bip01 {S} Hand': a}
rep['fingers'] = fingers_rep

# legs: boots by slices, the thigh joint keeps MM9's height
for side, sx in (('L', -1), ('R', 1)):
    bid = P['boot'][side]
    q = co[np.unique(F[fpart == bid])]
    def cen(z, h=0.03):
        m = np.abs(q[:, 2] - z) < h
        p = q[m]
        return 0.5 * (p.min(0) + p.max(0))
    c = cen(J[f'Bip01 {side} Calf'][2], 0.03); a = cen(J[f'Bip01 {side} Foot'][2], 0.02)
    c[2] = J[f'Bip01 {side} Calf'][2]; a[2] = J[f'Bip01 {side} Foot'][2]
    newJ[f'Bip01 {side} Calf'] = c; newJ[f'Bip01 {side} Foot'] = a
    newJ[f'Bip01 {side} Toe0'] = a + (J[f'Bip01 {side} Toe0'] - J[f'Bip01 {side} Foot'])
    t = J[f'Bip01 {side} Thigh'].copy()
    pq = co[np.unique(F[fpart == P['pants']])]
    m = (np.abs(pq[:, 2] - cfg['thigh_slice']) < 0.03) & (np.sign(pq[:, 0]) == sx)
    t[1] = 0.5 * (pq[m, 1].min() + pq[m, 1].max()) if m.sum() > 3 else t[1]
    newJ[f'Bip01 {side} Thigh'] = t
# children without their own fit move with the nearest fitted ancestor
fitted = {k for k, v in newJ.items() if np.linalg.norm(v - J[k]) > 1e-9}
for n in names:
    if n in fitted:
        continue
    p = parent[n]
    while p is not None and p not in fitted:
        p = parent[p]
    if p is not None:
        newJ[n] = J[n] + (newJ[p] - J[p])
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in names}
for a, b in (('Thigh', 'Calf'), ('Calf', 'Foot'), ('UpperArm', 'Forearm'), ('Forearm', 'Hand')):
    for s in 'LR':
        u = J[f'Bip01 {s} {b}'] - J[f'Bip01 {s} {a}']; w = newJ[f'Bip01 {s} {b}'] - newJ[f'Bip01 {s} {a}']
        ang = np.degrees(np.arccos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
        rep.setdefault('bone_dir_change_deg', {})[f'{s} {a}'] = round(float(ang), 1)
        rep.setdefault('bone_len_ratio', {})[f'{s} {a}'] = round(float(np.linalg.norm(w) / np.linalg.norm(u)), 3)

bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mi = arm.matrix_world.inverted()
for eb in arm.data.edit_bones:
    d = Mi.to_3x3() @ Vector(newJ[eb.name] - J[eb.name])
    eb.head += d; eb.tail += d
for name, (par, tmpl, pos) in tip_bones.items():
    t = arm.data.edit_bones[tmpl]
    eb = arm.data.edit_bones.new(name)
    off = Mi @ Vector(pos) - t.head
    eb.head = t.head + off; eb.tail = t.tail + off; eb.roll = t.roll
    eb.parent = arm.data.edit_bones[par]
    eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for name, (par, tmpl, pos) in tip_bones.items():
    arm.pose.bones[name].rotation_mode = 'QUATERNION'
    newJ[name] = pos
bones = list(newJ)
bidx = {b: i for i, b in enumerate(bones)}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}

# ---- weights
mp = np.array([mm9.matrix_world @ v.co for v in mm9.data.vertices])
lab = []
for v in mm9.data.vertices:
    g = max(v.groups, key=lambda g: g.weight)
    lab.append(mm9.vertex_groups[g.group].name)
mp2 = np.array([mp[i] + (newJ[lab[i]] - J[lab[i]]) for i in range(len(lab))])
mf = [list(p.vertices) for p in mm9.data.polygons]
bvh = BVHTree.FromPolygons([Vector(x) for x in mp2], mf)
W = np.zeros((nv, len(bones)))
override = cfg.get('label_override', {})
cloak = np.isin(vpart, P['cloak']); robe = np.isin(vpart, P['robe'])
for i in np.nonzero(cloak | robe)[0]:
    loc, nrm, fi, dist = bvh.find_nearest(Vector(co[i]))
    fv = mf[fi]
    best = min(fv, key=lambda k: (mp2[k] - np.array(loc)) @ (mp2[k] - np.array(loc)))
    L = override.get(lab[best], lab[best])
    W[i, bidx[L]] = 1
nbr = [[j for j, _ in a] for a in adj]
for it in range(cfg.get('diffuse', 8)):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    m = cloak | robe
    W[m] = 0.5 * W[m] + 0.5 * avg[m]


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


for s, sx in (('L', -1), ('R', 1)):
    # legs: boots and pants by height along the leg
    th, ca, fo, to = (bidx[f'Bip01 {s} {b}'] for b in ('Thigh', 'Calf', 'Foot', 'Toe0'))
    zk, za = newJ[f'Bip01 {s} Calf'][2], newJ[f'Bip01 {s} Foot'][2]
    boot = vpart == P['boot'][s]
    z = co[:, 2]
    wc = sstep(z, zk - 0.06, zk + 0.06)        # 1 above the knee
    wa = sstep(z, za - 0.03, za + 0.03)
    tb = newJ[f'Bip01 {s} Toe0'][1]            # the ball of the foot, y
    wt = sstep(tb + 0.02 - co[:, 1], 0, 0.04) * (1 - sstep(z, 0.03, 0.09))
    W[boot, th] = wc[boot]
    W[boot, ca] = ((1 - wc) * wa)[boot]
    W[boot, fo] = ((1 - wa) * (1 - wt))[boot]
    W[boot, to] = ((1 - wa) * wt)[boot]
pants = vpart == P['pants']
pel = bidx['Bip01 Pelvis']
x = co[:, 0]; z = co[:, 2]
for s, sx in (('L', -1), ('R', 1)):
    th, ca = bidx[f'Bip01 {s} Thigh'], bidx[f'Bip01 {s} Calf']
    side = sstep(sx * x, -0.05, 0.05)
    up = sstep(z, 0.92, 1.05)                  # waist into the pelvis
    wc = sstep(z, newJ[f'Bip01 {s} Calf'][2] - 0.06, newJ[f'Bip01 {s} Calf'][2] + 0.06)
    W[pants, th] = (side * (1 - up) * wc)[pants]
    W[pants, ca] = (side * (1 - up) * (1 - wc))[pants]
W[pants, pel] = sstep(z, 0.92, 1.05)[pants]
# robe: a cloth on the pelvis with a smooth share of each thigh, one mix per height, top on the belt's spine bone
rb = robe
sp = bidx['Bip01 Spine']
W[rb] = 0
top = sstep(z, 0.98, 1.08)
W[rb, sp] = top[rb]
leg = (1 - top) * cfg['robe_leg'] * sstep(0.98 - z, 0, 0.42)
W[rb, pel] = (1 - top - leg)[rb]
for s, sx in (('L', -1), ('R', 1)):
    W[rb, bidx[f'Bip01 {s} Thigh']] = (leg * sstep(sx * x, -0.14, 0.14))[rb]
for pid, bone in cfg['rigid_parts'].items():
    m = vpart == int(pid)
    W[m] = 0; W[m, bidx[bone]] = 1
for i, w in hand_w.items():
    W[i] = 0
    for b, a in w.items():
        W[i, bidx[b]] = a
# sleeves: the cloak's arm bands along the fitted arm (the sleeve follows the arm; Box bones keep their share)
band = cfg['bands']
for s, sx in (('L', -1), ('R', 1)):
    ua, fa, hd = (f'Bip01 {s} {b}' for b in ('UpperArm', 'Forearm', 'Hand'))
    cl = f'Bip01 {s} Clavicle'
    idxs = [bidx[b] for b in (cl, ua, fa)]
    o = newJ[ua]; ax = newJ[hd] - o; L_ = np.linalg.norm(ax); ax /= L_
    t = (co - o) @ ax
    te = (newJ[fa] - o) @ ax
    share = W[:, idxs].sum(1)
    m = cloak & (share > 0.3) & (np.sign(co[:, 0]) == sx)
    wu = sstep(t, band['shoulder'][0], band['shoulder'][1])
    wf = sstep(t, te - band['elbow'], te + band['elbow'])
    nw = np.stack([1 - wu, wu * (1 - wf), wu * wf], 1)
    for i in np.nonzero(m)[0]:
        W[i, idxs] = nw[i] * share[i]
# the pendant lies on the cape: each of its vertices copies the nearest cape vertex
pend = np.nonzero(vpart == cfg['pendant'])[0]
capeidx = np.nonzero(cloak)[0]
for i in pend:
    W[i] = W[capeidx[np.argmin(np.linalg.norm(co[capeidx] - co[i], axis=1))]]

order = np.argsort(-W, axis=1)
for i in range(nv):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]; row[row < 0.02] = 0
    if row.sum() == 0:
        raise SystemExit(f'vertex {i} part {vpart[i]} has no weights')
    W[i] = row / row.sum()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(nv):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
bpy.data.objects.remove(mm9)
rep['verts'] = nv; rep['tris'] = nf
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT', json.dumps({k: rep[k] for k in ('fingers', 'bone_dir_change_deg', 'bone_len_ratio', 'tris')}))
