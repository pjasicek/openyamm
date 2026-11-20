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
RADIUS, BLEND = 0.014, 0.25
gi = {g.name: g for g in body.vertex_groups}


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
    pts.append(pts[-1] + (pts[-1] - pts[-2]))
    return names, np.array(pts)


def seg_dist(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1), t


label = np.zeros(nv, np.int32)
for side in ('L', 'R'):
    hw = weights(f'B_{side}_Hand')
    ids = np.where(hw > 0.05)[0]
    P = co[ids]
    best = np.full(len(ids), 1e9); bf = np.full(len(ids), -1); bseg = np.zeros(len(ids), np.int32); bt = np.zeros(len(ids))
    chains = {f: chain(side, f) for f in range(5)}
    for f, (names, pts) in chains.items():
        for s in range(len(pts) - 1):
            d, t = seg_dist(P, pts[s], pts[s + 1])
            m = d < best
            best[m] = d[m]; bf[m] = f; bseg[m] = s; bt[m] = t[m]
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
        if s == 0 and along < -BLEND:
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
    print('FINGERS', side, {['thumb', 'index', 'middle', 'ring', 'pinky'][f]: c for f, c in sorted(counts.items())},
          'of', len(ids), 'hand vertices; palm/back stay on the hand')
a = me.attributes.get('finger') or me.attributes.new('finger', 'INT', 'POINT')
a.data.foreach_set('value', label.tolist())
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
