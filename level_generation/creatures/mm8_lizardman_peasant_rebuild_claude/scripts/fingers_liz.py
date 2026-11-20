"""Finger chains for the lizardman's four-digit hands (three clawed fingers and a thumb, as the masters), by
connectivity (lizardorc fingers.py logic, per side because our mesh is not mirrored): geodesic distance from the
wrist ring over the hand; the thumb is the first piece to split off, the three fingers the next split. Each digit:
joints at 4 / 36 / 66 % of its geodesic length (ring centres), tip at the far end.
Bones (MM9 names, so the lizardorc roles' finger_alias drives them from MM9's mitten curl): thumb Finger0 > Finger01 >
Finger02, fingers Finger1 > Finger11 > Finger12 (inner), Finger2.., Finger3.. (outer). Existing MM9 finger bones are
moved to our joints; new ones are added; all keep MM9's rest frame of Finger1 (fingers) / Finger0 (thumb), translated
only. Weights: each digit vertex by its geodesic position, bands of 20 % of the digit length at each joint; palm stays
on the hand. Args: <rig blend> <out blend> <report json>"""
import bpy, sys, json, heapq
import numpy as np
from mathutils import Vector
SRC, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']; body = bpy.data.objects['Body']; me = body.data
P = np.array([tuple(v.co) for v in me.vertices]); n = len(P)
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
gi = {g.name: g.index for g in body.vertex_groups}
def wget(name):
    w = np.zeros(n)
    if name not in gi: return w
    for v in me.vertices:
        for g in v.groups:
            if g.group == gi[name]: w[v.index] = g.weight
    return w
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; L = float(np.linalg.norm(P[a] - P[b])); nbr[a].append((b, L)); nbr[b].append((a, L))
def dijkstra(seeds, allowed):
    d = np.full(n, np.inf); h = []
    for s in seeds: d[s] = 0; heapq.heappush(h, (0.0, s))
    while h:
        dd, u = heapq.heappop(h)
        if dd > d[u]: continue
        for v, L in nbr[u]:
            if allowed[v] and dd + L < d[v]: d[v] = dd + L; heapq.heappush(h, (d[v], v))
    return d
def comps(mask):
    lab = -np.ones(n, int); c = 0
    for i in np.nonzero(mask)[0]:
        if lab[i] >= 0: continue
        st = [i]; lab[i] = c
        while st:
            u = st.pop()
            for v, _ in nbr[u]:
                if mask[v] and lab[v] < 0: lab[v] = c; st.append(v)
        c += 1
    return lab, c
rep = {}; chains = {}; labels = {}
for S in 'LR':
    h = J[f'Bip01 {S} Hand']; f = J[f'Bip01 {S} Forearm']; ax = (h - f) / np.linalg.norm(h - f)
    hw = wget(f'Bip01 {S} Hand')
    hand = (hw > 0.5) & (((P - h) @ ax) > -0.015) & (np.linalg.norm(P - h, axis=1) < 0.35)
    seeds = np.nonzero(hand & (np.abs((P - h) @ ax) < 0.015))[0]
    d = dijkstra(seeds, hand)
    fin = np.isfinite(d) & hand
    # the four digits: the first level with four pieces; each piece grown back towards the palm along its own axis
    # first split -> the smaller piece and the rest; the rest splits again into the other three (lizardorc logic)
    first = None
    for lev in np.arange(0.02, 0.30, 0.002):
        lab, c = comps(fin & (d > lev)); sizes = np.bincount(lab[lab >= 0], minlength=c); big = np.nonzero(sizes >= 8)[0]
        if len(big) >= 2:
            first = np.nonzero(lab == big[np.argmin(sizes[big])])[0]; lev1 = lev; break
    ex = np.zeros(n, bool); ex[first] = True
    for lev in np.arange(lev1, 0.30, 0.002):
        lab, c = comps(fin & (d > lev) & ~ex); sizes = np.bincount(lab[lab >= 0], minlength=c); big = np.nonzero(sizes >= 8)[0]
        if len(big) == 3:
            pieces = [first] + [np.nonzero(lab == b)[0] for b in big]; rep[f'{S}_split'] = [round(float(lev1), 3), round(float(lev), 3)]; break
    def axis_of(vs):
        dv = d[vs]; base = P[vs[dv < dv.min() + 0.008]].mean(0); tip = P[vs[np.argmax(dv)]]
        return base, tip
    ax_ = [axis_of(v) for v in pieces]
    # grow: palm vertices within GROW_R of a digit axis extended GROW_BACK towards the wrist join that digit
    GROW_R, GROW_BACK = 0.03, 0.05
    own = -np.ones(n, int)
    for k, v in enumerate(pieces): own[v] = k
    cand = np.nonzero(fin & (own < 0))[0]
    for i in cand:
        best, bd = -1, GROW_R
        for k, (b, t) in enumerate(ax_):
            u = (t - b) / np.linalg.norm(t - b); a0 = b - u * GROW_BACK
            tt = np.clip((P[i] - a0) @ u, 0, np.linalg.norm(t - a0)); dd = np.linalg.norm(P[i] - a0 - u * tt)
            if dd < bd and (P[i] - a0) @ u > 0: best, bd = k, dd
        if best >= 0: own[i] = best
    pieces = [np.nonzero(own == k)[0] for k in range(4)]
    def info(vs, k):
        b, t = ax_[k]; u = (t - b) / np.linalg.norm(t - b); a0 = b - u * GROW_BACK * 0.6
        dv = (P[vs] - a0) @ u; a, bb = 0.0, float(dv.max()); L = bb - a
        def ring(tq):
            m = np.abs(dv - (a + L * tq)) < max(0.006, L * 0.07)
            return P[vs[m]].mean(0) if m.any() else a0 + u * (a + L * tq)
        return dict(vs=vs, dv=dv, a=a, L=L, j=[ring(0.04), ring(0.36), ring(0.66), t])
    infos = [info(v, k) for k, v in enumerate(pieces)]
    # thumb: the digit whose base sits closest to the wrist (geodesic); fingers inner -> outer from the thumb
    dmins = [float(d[pieces[k]].min()) for k in range(4)]
    tk = int(np.argmin(dmins)); th = infos[tk]
    fi = [infos[k] for k in range(4) if k != tk]
    fi.sort(key=lambda q: np.linalg.norm(q['j'][0] - th['j'][0]))
    rep[f'{S}_dmin'] = [round(x, 3) for x in dmins]
    chains[S] = {'Finger0': th}
    for k, q in enumerate(fi, 1): chains[S][f'Finger{k}'] = q
    rep[S] = {k: {'len': round(float(q['L']), 3), 'verts': int(len(q['vs']))} for k, q in chains[S].items()}
# ---- bones
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones; Mi = arm.matrix_world.inverted()
names = {}
for S in 'LR':
    for fname, q in chains[S].items():
        k = fname[-1]
        tmpl = eb[f'Bip01 {S} Finger0' if k == '0' else f'Bip01 {S} Finger1']
        Rt = tmpl.matrix.to_3x3().copy(); roll_axis = Rt.col[2].copy()
        bn = [f'Bip01 {S} Finger{k}', f'Bip01 {S} Finger{k}1', f'Bip01 {S} Finger{k}2']
        par = f'Bip01 {S} Hand'
        for j, b in enumerate(bn):
            e = eb.get(b) or eb.new(b)
            hp = Mi @ Vector(q['j'][j]); ln = max(float(np.linalg.norm(q['j'][j + 1] - q['j'][j])), 0.01)
            e.head = hp; e.tail = hp + Rt.col[1] * ln; e.align_roll(roll_axis)
            e.parent = eb[par]; e.use_connect = False; e.use_deform = True; par = b
            names.setdefault(S, []).append(b)
bpy.ops.object.mode_set(mode='OBJECT')
# ---- weights on the digits
for S in 'LR':
    hand = f'Bip01 {S} Hand'
    for fname, q in chains[S].items():
        k = fname[-1]; bn = [f'Bip01 {S} Finger{k}', f'Bip01 {S} Finger{k}1', f'Bip01 {S} Finger{k}2']
        for b in bn:
            if b not in body.vertex_groups: body.vertex_groups.new(name=b)
        t = (q['dv'] - q['a']) / q['L']   # projection along the digit axis, 0 at the grown base
        def ss(x, a, b):
            y = np.clip((x - a) / (b - a), 0, 1); return y * y * (3 - 2 * y)
        w1 = ss(t, -0.10, 0.10); w2 = ss(t, 0.26, 0.46); w3 = ss(t, 0.56, 0.76)
        W = np.stack([1 - w1, w1 * (1 - w2), w2 * (1 - w3), w3], 1)       # hand, mcp, pip, dip
        for i, v in enumerate(q['vs']):
            for g in list(me.vertices[v].groups):
                body.vertex_groups[g.group].remove([int(v)])
            for gname, x in zip([hand] + bn, W[i]):
                if x > 0.01: body.vertex_groups[gname].add([int(v)], float(x), 'REPLACE')
json.dump({S: {k: [p.tolist() for p in q['j']] for k, q in chains[S].items()} for S in chains}, open(OUT + '.fingers.json', 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FINGERS ' + json.dumps(rep))
