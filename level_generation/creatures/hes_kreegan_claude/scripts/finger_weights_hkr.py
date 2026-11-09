"""hkr G4/G5: rebuild the demon's finger weights by connectivity (the installed Mixamo-style weights tore the knuckles
open as soon as a finger flexed: the demon's own clips never close the hands).
Per side: hand vertices = summed hand + finger weight > 0.5. A finger = the connected component (welded positions,
mesh edges) of the hand vertices beyond a threshold along the hand axis that holds that finger's tip, taken at the
lowest threshold before it merges with another finger's component (sweep in 2 mm steps from the tips to the wrist),
and limited to vertices beyond the finger's knuckle (projection onto its first segment > -ROOT_IN). Inside a finger:
nearest point on the chain polyline (knuckle -> joint 2 -> joint 3 -> tip); the segment's bone takes the weight,
blended linearly over +-BLEND at the two inner joints, and with the hand over [-ROOT_IN, +ROOT_OUT] around the
knuckle. Claw-material vertices are rigid on the distal bone. Palm vertices keep their weights with every finger
share moved to the hand bone. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
BLEND, ROOT_IN, ROOT_OUT = (float(os.environ.get(k, d)) for k, d in (('BLEND', '0.012'), ('ROOT_IN', '0.012'), ('ROOT_OUT', '0.018')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
CO = np.array([v.co[:] for v in me.vertices]); nv = len(CO)
gidx = {g.name: g.index for g in body.vertex_groups}
WT = np.zeros((nv, len(gidx)), np.float64)
for v in me.vertices:
    for g in v.groups: WT[v.index, g.group] = g.weight
claw = np.zeros(nv, bool)
for p in me.polygons:
    if body.material_slots[p.material_index].name.startswith('Demon_White_Claws'):
        claw[list(p.vertices)] = True
key = np.round(CO / 1e-5).astype(np.int64)
_, weld = np.unique(key, axis=0, return_inverse=True); weld = weld.ravel()
E = np.array([e.vertices[:] for e in me.edges])
rest = lambda n: np.array(rig.data.bones[n].head_local)


def chain(s, i):
    if s == 'R' and i == 0:
        return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
    return [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']


def components(mask):
    """connected components of the welded graph restricted to mask (vertex ids) -> label per vertex (-1 outside)"""
    wm = np.zeros(weld.max() + 1, bool); wm[weld[mask]] = True
    par = np.arange(len(wm))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    ee = weld[E]; ok = wm[ee[:, 0]] & wm[ee[:, 1]]
    for u, v in ee[ok]:
        ru, rv = find(u), find(v)
        if ru != rv: par[ru] = rv
    lab = np.full(nv, -1)
    idx = np.nonzero(mask)[0]
    lab[idx] = [find(weld[i]) for i in idx]
    return lab


report = {}
for s in 'LR':
    hand = f'B_{s}_Hand'; hb = [hand] + [b for i in range(5) for b in chain(s, i)]
    hsum = WT[:, [gidx[b] for b in hb]].sum(1)
    H = hsum > 0.5
    wr = rest(hand); f = rest(chain(s, 2)[0]) - wr; f /= np.linalg.norm(f)
    pts = {i: [rest(b) for b in chain(s, i)] + [np.array(rig.data.bones[chain(s, i)[2]].tail_local)] for i in range(5)}
    tipv = {}
    for i in range(5):
        d = np.linalg.norm(CO - pts[i][3], axis=1); d[~H] = 1e9; tipv[i] = int(np.argmin(d))
    fset = {}
    for i in range(5):
        p0 = pts[i][0]; di = pts[i][3] - p0; di /= np.linalg.norm(di)
        al = (CO - p0) @ di
        stop = -ROOT_IN
        res = None
        for t in np.arange(al[tipv[i]] - 0.002, stop - 1e-6, -0.002):
            lab = components(H & (al > t)); li = lab[tipv[i]]
            if li < 0: continue
            if any(lab[tipv[j]] == li for j in range(5) if j != i): break
            res = lab == li
        fset[i] = res if res is not None else np.zeros(nv, bool)
    overlap = sum(fset[i].astype(int) for i in range(5))
    fingers_all = np.zeros(nv, bool)
    newW = {}
    for i in range(5):
        m = fset[i] & (overlap == 1); fingers_all |= m
        P = pts[i]; bones = chain(s, i)
        idx = np.nonzero(m)[0]; X = CO[idx]
        # nearest point on the polyline: segment index and arclength
        best_d = np.full(len(X), 1e9); seg = np.zeros(len(X), int); tpar = np.zeros(len(X))
        for j in range(3):
            A, B = P[j], P[j + 1]; AB = B - A; L2 = AB @ AB
            t = np.clip(((X - A) @ AB) / L2, 0, 1); Q = A + np.outer(t, AB); dd = np.linalg.norm(X - Q, axis=1)
            upd = dd < best_d; best_d[upd] = dd[upd]; seg[upd] = j; tpar[upd] = t[upd]
        L = [np.linalg.norm(P[j + 1] - P[j]) for j in range(3)]
        raw_root = (X - P[0]) @ ((P[1] - P[0]) / L[0])          # signed distance past the knuckle
        for k_, vi in enumerate(idx):
            w = {}
            if claw[vi]:
                w[bones[2]] = 1.0
            else:
                j = seg[k_]; dist_in = tpar[k_] * L[j]; dist_out = (1 - tpar[k_]) * L[j]
                w[bones[j]] = 1.0
                if j < 2 and dist_out < BLEND:                    # near the next joint
                    x = 0.5 * (1 - dist_out / BLEND); w = {bones[j]: 1 - x, bones[j + 1]: x}
                if j > 0 and dist_in < BLEND:
                    x = 0.5 * (1 - dist_in / BLEND); w = {bones[j]: 1 - x, bones[j - 1]: x}
                if j == 0:
                    r = raw_root[k_]
                    if r < ROOT_OUT:
                        x = min(1.0, max(0.0, (r + ROOT_IN) / (ROOT_IN + ROOT_OUT)))
                        w = {bones[0]: x, hand: 1 - x}
            newW[vi] = (w, hsum[vi])
    # palm: finger shares -> hand
    palm = H & ~fingers_all
    for vi in np.nonzero(palm)[0]:
        fs = sum(WT[vi, gidx[b]] for b in hb if b != hand)
        newW[vi] = ({hand: WT[vi, gidx[hand]] + fs}, None)
    for vi, (w, hs) in newW.items():
        # keep the non-hand share (forearm blend) as it was; the hand+finger share is redistributed
        share = hsum[vi]
        for b in hb:
            WT[vi, gidx[b]] = 0.0
        tot = sum(w.values())
        for b, x in w.items():
            WT[vi, gidx[b]] = x / tot * share
    # smooth the hand/finger split across the welded mesh (the component cut can leave a palm vertex at 100 % hand next
    # to a finger vertex at 100 % on its second phalanx: 5x edge stretch once the fist closes); claws stay rigid
    cols = [gidx[b] for b in hb]
    sm = H & ~claw
    wn = WT[:, cols] / np.maximum(WT[:, cols].sum(1, keepdims=True), 1e-9)
    nb = [[] for _ in range(weld.max() + 1)]
    for u_, v_ in weld[E]:
        if u_ != v_: nb[u_].append(v_); nb[v_].append(u_)
    rep_of = {}
    for vi in range(nv): rep_of.setdefault(weld[vi], []).append(vi)
    for it in range(int(os.environ.get('SMOOTH', '4'))):
        wavg = np.zeros((weld.max() + 1, len(cols))); cnt = np.zeros(weld.max() + 1)
        np.add.at(wavg, weld, wn); np.add.at(cnt, weld, 1); wavg /= np.maximum(cnt, 1)[:, None]
        new = wn.copy()
        for vi in np.nonzero(sm)[0]:
            ns = nb[weld[vi]]
            if ns: new[vi] = 0.5 * wavg[weld[vi]] + 0.5 * wavg[ns].mean(0)
        wn = new
    WT[np.ix_(sm, cols)] = wn[sm] * hsum[sm, None]
    report[s] = {f'finger{i}': int((fset[i] & (overlap == 1)).sum()) for i in range(5)}
    report[s]['palm'] = int(palm.sum()); report[s]['overlap'] = int((overlap > 1).sum())
    print('FINGERW', s, json.dumps(report[s]))
for g in body.vertex_groups:
    col = WT[:, g.index]
    g.remove(list(range(nv)))
    nz = np.nonzero(col > 1e-5)[0]
    for vi in nz:
        g.add([int(vi)], float(col[vi]), 'REPLACE')
lab = np.zeros(nv, np.int32)
for s in 'LR':
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
