"""Bat wings on MM9's wing chain (raw ABC space, Blender frame: faces -Y, z up, figure's L wing at -x).

MM9 deforms its wing rigidly per vertex: every outline point sits at a bone head and the faces interpolate. We keep
that motion and draw it finer:
- Spars (tubes): arm root (buried in the back) -> Bone49 -> wrist Bone50; from the wrist three fingers
  (Bone53 -> Bone54 -> tip, Bone62 -> tip, Bone58 -> tip) and a short thumb claw. Each segment is rigid on the bone
  whose frame holds both its ends, with smooth blends at the joints; the buried root takes the body's own weights and
  blends into Bone48 as it leaves the back.
- Membrane: three Coons fans round the wrist (leading finger | finger 2 | finger 3 | arm), scalloped trailing edges,
  the inner panel's edge running tip3 -> Bone69 -> Bone66 -> the back. Weights are harmonic between the spar and edge
  weights (positive, exact on the outline), so it moves as MM9's faces do. Solidified to a thin closed shell.
- UV: membrane planar in the bind plane of each panel set (one chart per wing side, both layers share it); spars a
  cylinder strip each. Everything in the 'wing' material (own texture).

Args: <rig json> <body npz (co, tri, weights)> <out npz>. rig json: {"joints": {name: [x,y,z]}} with the wing bones,
Bip01 Spine2 and the body weights npz arrays (W, names) for anchor weights.
"""
import json, sys
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

CFG = dict(rows=11, cols=8, scallop=0.11, thick=0.007, sides=5, root_depth=0.07, joint_blend=0.05,
           arm_r=(0.028, 0.022, 0.017), lead_r=(0.016, 0.012, 0.008, 0.004), fing_r=(0.011, 0.007, 0.003),
           claw=0.10)
LEFT = dict(root='Bone48', arm='Bone49', wrist='Bone50', l1='Bone53', l2='Bone54', l3='Bone55', f2='Bone62',
            f2b='Bone63', f3='Bone58', f3b='Bone59', e1='Bone69', e2='Bone66')
MIRROR = {'Bone48': 'Bone13', 'Bone49': 'Bone14', 'Bone50': 'Bone15', 'Bone53': 'Bone18', 'Bone54': 'Bone19',
          'Bone55': 'Bone20', 'Bone58': 'Bone26', 'Bone59': 'Bone27', 'Bone62': 'Bone10', 'Bone63': 'Bone11',
          'Bone66': 'Bone46', 'Bone69': 'Bone34'}


UX, UZ0, UZ = 1.66, 0.36, 1.07          # membrane chart: u = |x| / UX, v = (z - UZ0) / UZ (1536x1024 paint, unit square UV)


def proj(p):
    return np.array([abs(p[0]) / UX, (p[2] - UZ0) / UZ])


def unit(v):
    return v / np.linalg.norm(v)


class Poly:
    """Polyline with a carrier bone per segment; sample(t) by arc length -> point, {bone: w}."""

    def __init__(self, pts, bones, blend):
        self.p = np.array(pts, float); self.b = bones; self.blend = blend
        seg = np.linalg.norm(np.diff(self.p, axis=0), axis=1); self.s = np.r_[0, np.cumsum(seg)]; self.L = self.s[-1]

    def point(self, t):
        s = np.clip(t, 0, 1) * self.L
        i = min(np.searchsorted(self.s, s, side='right') - 1, len(self.p) - 2)
        u = (s - self.s[i]) / max(self.s[i + 1] - self.s[i], 1e-9)
        return self.p[i] + (self.p[i + 1] - self.p[i]) * u, i, s

    def weights(self, t):
        _, i, s = self.point(t)
        w = {}
        def add(b, x):
            if isinstance(b, dict):
                for k, v in b.items(): w[k] = w.get(k, 0) + v * x
            else:
                w[b] = w.get(b, 0) + x
        # blend with the neighbour segment near an inner joint
        a = 1.0
        if i > 0 and s - self.s[i] < self.blend:
            u = 0.5 + 0.5 * (s - self.s[i]) / self.blend; u = u * u * (3 - 2 * u); add(self.b[i - 1], 1 - u); a = u
        elif i < len(self.b) - 1 and self.s[i + 1] - s < self.blend:
            u = 0.5 + 0.5 * (self.s[i + 1] - s) / self.blend; u = u * u * (3 - 2 * u); add(self.b[i + 1], 1 - u); a = u
        add(self.b[i], a)
        return w


def lerpw(a, b, u):
    w = {}
    for k, v in a.items(): w[k] = w.get(k, 0) + v * (1 - u)
    for k, v in b.items(): w[k] = w.get(k, 0) + v * u
    return w


def build_side(J, body, cfg, side_map, pleat_prefix):
    B = {k: side_map[v] for k, v in LEFT.items()}
    P = {k: np.array(J[v]) for k, v in B.items()}
    tip = lambda b: P[b]              # outline points sit at the last bone's head (MM9)
    # anchor on the back: the body surface point nearest the root bone, then root_depth inside
    kd = cKDTree(body['co'])
    d, ia = kd.query(P['root'])
    surf = body['co'][ia]; inward = unit(np.array([0.0, -1.0, 0.0]) + 0.6 * unit(np.r_[-surf[0], 0, 0]) * (abs(surf[0]) > 0.02))
    anchor = surf + inward * cfg['root_depth']
    body_w = body['wfun'](ia)
    # outline points
    W, A, E1, E2 = P['wrist'], P['arm'], P['e1'], P['e2']
    # inner edge meets the back below the root: body point nearest the MM9 web point (between Bone66 and the root)
    web = P['root'] + np.array([np.sign(P['arm'][0]) * 0.10, 0.02, -0.03])
    d2, ib = kd.query(web); back_in = body['co'][ib] + inward * 0.012; back_w = body['wfun'](ib)
    root_out = surf + (P['root'] - surf) * 0.0     # where the arm leaves the back
    # spars (wrist -> tip); carrier = bone whose frame holds both ends
    lead = Poly([W, P['l1'], P['l2'], tip('l3')], [B['wrist'], B['l1'], B['l2']], cfg['joint_blend'])
    f2 = Poly([W, P['f2'], tip('f2b')], [B['wrist'], B['f2']], cfg['joint_blend'])
    f3 = Poly([W, P['f3'], tip('f3b')], [B['wrist'], B['f3']], cfg['joint_blend'])
    arm = Poly([W, A, surf], [B['arm'], B['root']], cfg['joint_blend'])
    # trailing edges (u from S1 tip to S2 end)
    def edge_scallop(a, b, depth, toward):
        def f(u):
            p = a + (b - a) * u
            return p + unit(toward - (a + b) / 2) * depth * np.linalg.norm(b - a) * np.sin(np.pi * u)
        return f
    tL, t2, t3 = tip('l3'), tip('f2b'), tip('f3b')
    e_a = edge_scallop(tL, t2, cfg['scallop'], W)
    e_b = edge_scallop(t2, t3, cfg['scallop'], W)
    inner_pts = [t3, E1, E2, back_in, surf]
    # the web along the back moves with the wing root as MM9's does (Bone48 weights): tied to the body it stretched into a
    # sail between the waist and the elbow when the clips swing the wing arm up 70 deg
    inner_w = [{B['f3']: 1.0}, {B['arm']: 1.0}, {B['arm']: 1.0}, {B['root']: 1.0}, {B['root']: 1.0}]
    ip = Poly(inner_pts, [0, 1, 2, 3], 0.0)
    def e_c(u):
        p, i, s = ip.point(u)
        if i in (0, 1):      # scallop the two free edges
            a, b = ip.p[i], ip.p[i + 1]; uu = (s - ip.s[i]) / (ip.s[i + 1] - ip.s[i])
            p = p + unit(W - (a + b) / 2) * 0.08 * np.linalg.norm(b - a) * np.sin(np.pi * uu)
        return p
    def e_c_w(u):
        _, i, s = ip.point(u); uu = (s - ip.s[i]) / max(ip.s[i + 1] - ip.s[i], 1e-9)
        return lerpw(inner_w[i], inner_w[i + 1], uu)
    panels = [(lead, f2, e_a, lambda u: lerpw({B['l2']: 1.0}, {B['f2']: 1.0}, u)),
              (f2, f3, e_b, lambda u: lerpw({B['f2']: 1.0}, {B['f3']: 1.0}, u)),
              (f3, arm, e_c, e_c_w)]
    N, M = cfg['rows'], cfg['cols']
    verts = [W.copy()]; vw = [{B['wrist']: 1.0}]; fixed = [True]; vpan = [-1]; vu = [0.0]
    spar_rows = {}
    def spar_vert(poly, i):
        key = (id(poly), i)
        if key not in spar_rows:
            t = i / N; p, _, _ = poly.point(t)
            spar_rows[key] = len(verts); verts.append(p); vw.append(poly.weights(t)); fixed.append(True); vpan.append(-1); vu.append(0.0)
        return spar_rows[key]
    tris = []; panel_of = []
    edge_ids = []
    for pi, (S1, S2, E, EW) in enumerate(panels):
        rows = [[0]]
        for i in range(1, N + 1):
            t = i / N
            c = max(1, int(round(M * t * (1.6 if pi == 2 else 1.0))))
            row = []
            p1 = S1.point(t)[0]; p2 = S2.point(t)[0]
            e0, e1 = E(0.0), E(1.0)
            for j in range(c + 1):
                u = j / c
                if j == 0: row.append(spar_vert(S1, i)); continue
                if j == c: row.append(spar_vert(S2, i)); continue
                tp = t ** 1.5
                p = (1 - u) * p1 + u * p2 + tp * (E(u) - ((1 - u) * e0 + u * e1))
                verts.append(p); vw.append(EW(u) if i == N else None); fixed.append(i == N); row.append(len(verts) - 1); vpan.append(pi); vu.append(u)
            rows.append(row)
            if i == N: edge_ids += row
        for i in range(1, N + 1):
            a, b = rows[i - 1], rows[i]
            ja = jb = 0
            while ja < len(a) - 1 or jb < len(b) - 1:
                ua = ja / max(len(a) - 1, 1); ub = jb / max(len(b) - 1, 1)
                if jb < len(b) - 1 and (ja >= len(a) - 1 or (jb + 1) / (len(b) - 1) <= (ja + 1) / max(len(a) - 1, 1)):
                    tris.append((a[ja], b[jb], b[jb + 1])); jb += 1
                else:
                    tris.append((a[ja], b[jb], a[ja + 1])); ja += 1
                panel_of.append(pi)
    V = np.array(verts); T = np.array(tris)
    # harmonic weights for free vertices
    bones = sorted({k for w in vw if w for k in w})
    bi = {b: i for i, b in enumerate(bones)}
    n = len(V); Wm = np.zeros((n, len(bones)))
    fx = np.array(fixed)
    for i, w in enumerate(vw):
        if w:
            for k, v in w.items(): Wm[i, bi[k]] = v
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); e = np.unique(np.sort(e, 1), axis=0)
    L = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    deg = np.asarray(L.sum(1)).ravel()
    free = np.where(~fx)[0]; fixd = np.where(fx)[0]
    Lap = (csr_matrix((deg, (np.arange(n), np.arange(n))), shape=(n, n)) - L).tocsr()
    A_ = Lap[free][:, free]; Bm = -Lap[free][:, fixd] @ Wm[fixd]
    Wm[free] = np.column_stack([spsolve(A_.tocsc(), Bm[:, k]) for k in range(len(bones))])
    Wm = np.clip(Wm, 0, None); Wm /= Wm.sum(1, keepdims=True)
    # pleat: a tent across each panel blends into the panel's pleat bone (pleat_keys.py turns it out of plane as the fan
    # closes, so each half keeps its rest opening); not on points that carry body weights
    bodyshare = Wm[:, [k for k, b_ in enumerate(bones) if not b_.startswith('Bone')]].sum(1) if any(not b_.startswith('Bone') for b_ in bones) else np.zeros(len(Wm))
    vpan_a = np.array(vpan); vu_a = np.array(vu)
    tau = np.where(vpan_a >= 0, 1 - np.abs(2 * vu_a - 1), 0.0) * (1 - np.clip(bodyshare * 3, 0, 1))
    pnames = [f'{pleat_prefix}{k + 1}' for k in range(3)]
    Wm = np.c_[Wm * (1 - tau)[:, None], np.zeros((len(Wm), 3))]
    for k in range(3): Wm[vpan_a == k, len(bones) + k] = tau[vpan_a == k]
    bones = bones + pnames
    # orientation: membrane normal pointing back (+y) consistently
    fnrm = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    if fnrm[:, 1].sum() < 0: T = T[:, ::-1]
    mem = dict(co=V, tri=T, W=Wm, bones=bones, panel=np.array(panel_of))
    # spars
    def tube(poly, radii, nseg, close_start=True, start_extra=None):
        pts = []; ws = []
        ts = np.linspace(0, 1, nseg + 1)
        rr = np.interp(ts, np.linspace(0, 1, len(radii)), radii)
        frames = []
        for t in ts:
            p, _, _ = poly.point(t); pts.append(p); ws.append(poly.weights(t))
        pts = np.array(pts)
        tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
        ref = np.array([0, 1.0, 0])
        cv = []; ct = []; cw = []; cuv = []
        S = cfg['sides']
        p2 = np.array([proj(p) for p in pts]); d2 = np.gradient(p2, axis=0); d2 /= np.maximum(np.linalg.norm(d2, axis=1, keepdims=True), 1e-9)
        perp2 = np.c_[-d2[:, 1], d2[:, 0]]
        for k, (p, tg, r, w) in enumerate(zip(pts, tang, rr, ws)):
            a = unit(np.cross(tg, ref) if abs(tg @ ref) < 0.95 else np.cross(tg, [1.0, 0, 0])); b = np.cross(tg, a)
            for s in range(S):
                ang = 2 * np.pi * s / S
                cv.append(p + r * (np.cos(ang) * a + np.sin(ang) * b)); cw.append(w)
                cuv.append(p2[k] + perp2[k] * np.cos(ang) * max(r, 0.004) / UX)
        for k in range(len(pts) - 1):
            for s in range(S):
                a0 = k * S + s; a1 = k * S + (s + 1) % S; b0 = a0 + S; b1 = a1 + S
                ct += [(a0, a1, b1), (a0, b1, b0)]
        # caps: centre points
        c0 = len(cv); cv.append(pts[0] - tang[0] * rr[0] * 0.5); cw.append(ws[0]); cuv.append(p2[0])
        for s in range(S): ct.append((c0, (s + 1) % S, s))
        c1 = len(cv); cv.append(pts[-1] + tang[-1] * max(rr[-1], 0.004) * 1.5); cw.append(ws[-1]); cuv.append(p2[-1])
        base = (len(pts) - 1) * S
        for s in range(S): ct.append((c1, base + s, base + (s + 1) % S))
        return np.array(cv), np.array(ct), cw, np.clip(np.array(cuv), 0.002, 0.998)
    sp = []
    sp.append(tube(lead, cfg['lead_r'], 11))
    sp.append(tube(f2, cfg['fing_r'], 7))
    sp.append(tube(f3, cfg['fing_r'], 6))
    # arm: from inside the back (anchor, body weights) through the root to the wrist
    arm_full = Poly([anchor, surf, A, W], [body_w, B['root'], B['arm']], cfg['joint_blend'] * 1.5)
    sp.append(tube(arm_full, cfg['arm_r'][::-1] if False else (0.022, cfg['arm_r'][0], cfg['arm_r'][1], cfg['arm_r'][2]), 10))
    # thumb claw at the wrist, pointing along the MM9 spike (inward, up)
    cl_dir = unit(np.r_[-np.sign(W[0]) * 1.0, -0.2, 0.15]); cl = Poly([W, W + cl_dir * cfg['claw']], [B['wrist']], 0.0)
    sp.append(tube(cl, (0.012, 0.001), 3))
    return mem, sp, dict(anchor=anchor.tolist(), surf=surf.tolist(), back_in=back_in.tolist(), depth=float(d))


def solidify(mem, thick):
    V, T = mem['co'], mem['tri']
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for c in range(3): np.add.at(N, T[:, c], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    n = len(V)
    V2 = np.vstack([V + N * thick / 2, V - N * thick / 2])
    T2 = np.vstack([T, T[:, ::-1] + n])
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    key = np.sort(e, 1); u, c = np.unique(key, axis=0, return_counts=True)
    bset = {tuple(k) for k in u[c == 1]}
    rim = []
    for a, b in e:
        if tuple(sorted((a, b))) in bset:
            rim += [(b, a, a + n), (b, a + n, b + n)]
    T2 = np.vstack([T2, np.array(rim)])
    side = np.r_[np.zeros(n), np.ones(n)]
    return V2, T2, np.vstack([mem['W'], mem['W']]), side, N


def main():
    rig_p, body_p, out_p = sys.argv[1:4]
    R = json.load(open(rig_p)); J = R['joints']
    BD = np.load(body_p); bw = BD['W']; bnames = [str(x) for x in BD['names']]
    body = dict(co=BD['co'], wfun=lambda i: {bnames[k]: float(bw[i, k]) for k in np.nonzero(bw[i] > 1e-3)[0]})
    allv = []; allt = []; allw = []; part = []; uvs = []; rep = {}
    names = sorted({*bnames, *LEFT.values(), *MIRROR.values(), *[f'XPleat{a}{k}' for a in 'AB' for k in (1, 2, 3)]})
    ni = {n: i for i, n in enumerate(names)}
    off = 0
    for side, smap in (('L', {v: v for v in LEFT.values()}), ('R', MIRROR)):
        mem, sp, info = build_side(J, body, CFG, smap, 'XPleatA' if side == 'L' else 'XPleatB')
        rep[side] = info
        V2, T2, W2, lay, N = solidify(mem, CFG['thick'])
        # planar UV: project on the membrane's best plane (front view x-z is close), normalised later
        uv = np.clip(np.array([proj(p) for p in V2]), 0.002, 0.998)
        Wf = np.zeros((len(V2), len(names)))
        for k, b in enumerate(mem['bones']): Wf[:, ni[b]] = W2[:, k]
        allv.append(V2); allt.append(T2 + off); allw.append(Wf); part.append(np.zeros(len(V2), int) + (0 if side == 'L' else 1)); uvs.append(uv)
        off += len(V2)
        for k, (cv, ct, cw, cuv) in enumerate(sp):
            Wt = np.zeros((len(cv), len(names)))
            for i, w in enumerate(cw):
                for b, v in w.items(): Wt[i, ni[b]] += v
            Wt /= Wt.sum(1, keepdims=True)
            S = CFG['sides']
            ring = np.arange(len(cv)) // S; ang = (np.arange(len(cv)) % S) / S
            allv.append(cv); allt.append(ct + off); allw.append(Wt); part.append(np.zeros(len(cv), int) + (2 if side == 'L' else 3)); uvs.append(cuv)
            off += len(cv)
    V = np.vstack(allv); T = np.vstack(allt); W = np.vstack(allw); P = np.concatenate(part); UV = np.vstack(uvs)
    np.savez(out_p, co=V, tri=T, W=W, names=np.array(names), part=P, uv=UV)
    print('WINGS', len(V), len(T), json.dumps(rep))


if __name__ == '__main__':
    main()
