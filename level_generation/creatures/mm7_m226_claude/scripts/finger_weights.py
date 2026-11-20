"""G5: finger skin weights (Meshy's auto-rig has no finger bones; all hand skin sat on B_*_Hand).
Each finger chain is three joint heads plus a tip extrapolated by one more distal segment. A hand vertex belongs to
the finger whose chain (as line segments) is nearest, if that distance is < RADIUS and the vertex lies beyond the
knuckle (along the first segment); within the finger it goes to the nearest phalanx with a linear blend over
BLEND of the segment length on each side of the joints; at the knuckle it ramps from the hand into the proximal
phalanx. The palm and the back of the hand stay on B_*_Hand. Prints per-finger vertex counts and writes a debug
colour attribute 'finger' (0 hand, 1..5 thumb..pinky). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
SMOOTH_PASSES = int(__import__('os').environ.get('SMOOTH_PASSES', '3'))
RADIUS, BLEND = float(__import__('os').environ.get('FRADIUS', '0.022')), 0.25   # goblin fingers are thicker (bar1: 1.4 cm)
gi = {g.name: g for g in body.vertex_groups}
import json
FJ = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'finger_joints.json')))
FIT = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'fingers_fit.json')))


def weights(name):
    g = gi[name]; w = np.zeros(nv)
    for v in me.vertices:
        for e in v.groups:
            if e.group == g.index:
                w[v.index] = e.weight
    return w


def chain(side, f):
    names = [f'B_{side}_Finger{f}']
    while True:
        k = [b.name for b in rig.data.bones if b.parent and b.parent.name == names[-1]]
        if not k:
            break
        names.append(k[0])
    pts = [np.array(rig.data.bones[n].head_local) for n in names]
    # the measured fingertip (claw tip) lengthened 25 %: an extrapolated tip ended short of the goblin's claws, the
    # claw tips stayed on the hand bone and tore into spikes in the fist
    tip = np.array(FJ[side][names[-1] + '_tip'])
    pts.append(tip + (tip - pts[-1]) * 0.25)
    return names, np.array(pts)


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1), t


label = np.zeros(nv, np.int32)
EDGES = np.array([tuple(e.vertices) for e in me.edges])
for side in ('L', 'R'):
    hw = weights(f'B_{side}_Hand'); hw_all = hw
    ids = np.where(hw > 0.05)[0]
    P = co[ids]
    best = np.full(len(ids), 1e9); bf = np.full(len(ids), -1); bseg = np.zeros(len(ids), np.int32); bt = np.zeros(len(ids))
    chains = {f: chain(side, f) for f in range(5)}
    for f, (names, pts) in chains.items():
        for s in range(len(pts) - 1):
            d, t = seg_dist(P, pts[s], pts[s + 1])
            m = d < best
            best[m] = d[m]; bf[m] = f; bseg[m] = s; bt[m] = t[m]
    # vertices of a separated finger piece (fit_fingers.py) belong to that finger, whatever their distance to its chain
    # (claw tips, fat knuckles); outside the pieces only the knuckle/web ramp onto a proximal phalanx is allowed
    FN = ['thumb', 'index', 'middle', 'ring', 'pinky']
    piece_of = {}
    for f, n in enumerate(FN):
        for v in FIT[side]['verts'][n]:
            piece_of[v] = f
    # grow each piece through mesh edges: a connected vertex beyond its finger's knuckle (along the proximal phalanx
    # > 20 %) within 4 cm of that finger's chain joins it, unless another finger has it (claw tips 2 cm from the measured
    # tip were outside the cut pieces and stayed on the hand bone: 19x stretch)
    grown = 0
    for _ in range(40):
        add = {}
        for a_, b_ in EDGES:
            for x, y in ((a_, b_), (b_, a_)):
                if x in piece_of and y not in piece_of and y not in add and hw_all[y] > 0.05:
                    f = piece_of[x]; nm, pt = chains[f]
                    d0 = pt[1] - pt[0]; L0 = np.linalg.norm(d0)
                    if (co[y] - pt[0]) @ d0 / L0 / L0 > 0.2 and min(seg_dist(co[y:y + 1], pt[j], pt[j + 1])[0][0]
                                                                for j in range(len(pt) - 1)) < 0.04:
                        add[y] = f
        if not add:
            break
        piece_of.update(add); grown += len(add)
    print('FINGERPIECES', side, 'grown by', grown, 'vertices')
    for k, i in enumerate(ids):
        f = piece_of.get(int(i))
        if f is None:
            if bf[k] >= 0 and bseg[k] > 0:
                best[k] = 1e9                                               # off-piece: no mid/distal phalanx
            continue
        names_, pts_ = chains[f]; bb = (1e9, 0, 0.0)
        for s_ in range(len(pts_) - 1):
            d_, t_ = seg_dist(P[k:k + 1], pts_[s_], pts_[s_ + 1])
            if d_[0] < bb[0]:
                bb = (d_[0], s_, t_[0])
        bf[k], bseg[k], bt[k] = f, bb[1], bb[2]; best[k] = 0.0
    # beyond the knuckle: projection on the first segment from its base
    newW = {}
    counts = {}
    for k, i in enumerate(ids):
        f = bf[k]
        if f < 0 or best[k] > RADIUS:
            continue
        names, pts = chains[f]
        s, t = bseg[k], bt[k]
        a0 = pts[0]; d0 = (pts[1] - pts[0]); L0 = np.linalg.norm(d0)
        along = (co[i] - a0) @ d0 / L0 / L0
        if s == 0 and along < -BLEND and best[k] > 0:
            continue
        w = {}
        if s == 0:
            into = np.clip((along + BLEND) / (2 * BLEND), 0, 1)          # ramp hand -> proximal phalanx at the knuckle
            w[f'B_{side}_Hand'] = 1 - into; w[names[0]] = into
        else:
            w[names[s]] = 1.0
        # blend with the previous phalanx near the joint at the start of segment s (s >= 1)
        if s >= 1 and t < BLEND:
            b = 0.5 + 0.5 * t / BLEND
            prev = names[s - 1]; cur = names[s] if s < len(names) else names[-1]
            w = {cur: b, prev: 1 - b}
        if s == len(names):                                             # the extrapolated tip segment
            w = {names[-1]: 1.0}
        tot = hw[i]
        newW[i] = {n: x * tot for n, x in w.items()}
        counts[f] = counts.get(f, 0) + 1
        label[i] = f + 1
    for i, w in newW.items():
        gi[f'B_{side}_Hand'].remove([int(i)])
        for n, x in w.items():
            gi[n].add([int(i)], float(x), 'ADD')
    # knuckle band smoothing: the hand -> proximal phalanx ramp and the webs between fingers were one edge wide
    # (6-7x stretch where a hand-only vertex met an 80 % finger vertex). Vertices carrying hand or proximal-phalanx
    # weight that are not deeper than 60 % of the proximal phalanx get SMOOTH_PASSES of neighbour averaging over those
    # channels (their sum is kept); the mid and distal phalanges stay rigid.
    chan = [f'B_{side}_Hand'] + [chains[f][0][0] for f in range(5)]
    Wc = np.stack([weights(n) for n in chan], 1)
    deep = np.zeros(nv, bool)
    for f in range(5):
        nm, pt = chains[f]; d0 = pt[1] - pt[0]; L0 = np.linalg.norm(d0)
        along_all = (co - pt[0]) @ d0 / L0 / L0
        deep |= (np.array([piece_of.get(i) == f for i in range(nv)])) & (along_all > 0.6)
        for n2 in nm[1:]:
            deep |= weights(n2) > 0.05
    band = (Wc.sum(1) > 0.05) & ~deep & (Wc[:, 1:].sum(1) + (Wc[:, 0] > 0.05)) .astype(bool)
    nb = [[] for _ in range(nv)]
    for a_, b_ in EDGES:
        nb[a_].append(b_); nb[b_].append(a_)
    tot = Wc.sum(1)
    for _ in range(SMOOTH_PASSES):
        Wn = Wc.copy()
        for i in np.where(band)[0]:
            ns = [j for j in nb[i] if Wc[j].sum() > 0.05]
            if ns:
                m = 0.5 * Wc[i] + 0.5 * Wc[ns].mean(0)
                Wn[i] = m / max(m.sum(), 1e-9) * tot[i]
        Wc = Wn
    # m226: the averaging leaked a middle-finger share onto a pinky web vertex (one web edge 5.7x in the hit): a
    # vertex labelled to a finger keeps only the hand, its own and the ADJACENT fingers' proximal channels
    nonadj = 0
    for i in np.where(band & (label > 0))[0]:
        f = label[i] - 1
        far = [1 + g for g in range(5) if abs(g - f) > 1]
        if Wc[i, far].sum() > 1e-4:
            Wc[i, far] = 0; Wc[i] *= tot[i] / max(Wc[i].sum(), 1e-9); nonadj += 1
    print('FINGERSMOOTH', side, 'non-adjacent finger weight removed on', nonadj, 'vertices')
    for k, n in enumerate(chan):
        g = gi[n]
        for i in np.where(band)[0]:
            if Wc[i, k] > 1e-4:
                g.add([int(i)], float(Wc[i, k]), 'REPLACE')
            else:
                g.remove([int(i)])
    print('FINGERSMOOTH', side, 'band vertices', int(band.sum()), 'passes', SMOOTH_PASSES)
    print('FINGERS', side, {['thumb', 'index', 'middle', 'ring', 'pinky'][f]: c for f, c in sorted(counts.items())},
          'of', len(ids), 'hand vertices; palm/back stay on the hand')
a = me.attributes.get('finger') or me.attributes.new('finger', 'INT', 'POINT')
a.data.foreach_set('value', label.tolist())
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
