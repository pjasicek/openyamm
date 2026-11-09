"""Vertices only on the frozen mesh (UVs and paints stay). Each arm: the zipped wrist band, which folded inward to a groove, goes onto the tube between the bracer's end ring and the hand's ring, polar per angle; hand scaled 1.08 from the wrist. Each hand: fingers curled round a cylinder per finger on a grid (from finish_clan.py, here baked into the rest mesh by forward kinematics with soft joints, since the fists are rigid and have no finger bones), thumb over them. Right round the club's grip, left a closed fist. The grip centre lies in the cavity between palm face and fingers. Writes scripts/grip.json (G, kn), work/fist.json (posed chains). Args: <in blend> <out blend>"""
import bpy, sys, json, math
import numpy as np
from mathutils import Matrix, Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
HERE = '/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/'
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
P = np.array([v.co[:] for v in me.vertices]); n = len(P)
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
HJ = json.load(open(HERE + 'work/hands_v1.json'))
RG = {'R': 0.0255 + 0.002, 'L': 0.016}
MODE = open(HERE + 'scripts/fist_mode.txt').read().strip(); HS = 1.08 if MODE == 'r5' else 1.0      # r5 = the build left installed; r9 = taper, blend, weld, unsolved (README)
sst = lambda x, a, b: (lambda t: t * t * (3 - 2 * t))(np.clip((x - a) / (b - a), 0, 1))
unit = lambda v: v / np.linalg.norm(v)
def rot(ax, a): return np.array(Matrix.Rotation(a, 3, Vector(ax)))
out = {}
for S, sg in (('R', -1), ('L', 1)):
    Fr = HJ['frames'][S]; W = np.array(Fr['W']); d = unit(np.array(Fr['d']))
    al = (P - W) @ d; rv = P - W - np.outer(al, d); r = np.linalg.norm(rv, axis=1)
    arm = (np.sign(P[:, 0]) == sg) & (pa == 0) & (r < 0.2) & (al > -0.25)
    U = unit(np.cross(d, [0, 0, 1.0])); V_ = np.cross(d, U); th = np.arctan2(rv @ V_, rv @ U)
    # polar rings
    def ring(lo, hi):
        m = arm & (al > lo) & (al < hi) & (r < 0.11); o = np.argsort(th[m]); a_, r_ = th[m][o], r[m][o]
        bins = np.linspace(-np.pi, np.pi, 25); c = 0.5 * (bins[1:] + bins[:-1]); v = np.array([r_[(a_ >= bins[i]) & (a_ < bins[i + 1])].max() if ((a_ >= bins[i]) & (a_ < bins[i + 1])).any() else np.nan for i in range(24)])
        ok = ~np.isnan(v); return np.interp(c, c[ok], v[ok], period=2 * np.pi), c
    ra, c = ring(-0.03, -0.002); rb, _ = ring(0.05, 0.075)
    band = arm & (al > -0.002) & (al < 0.052)
    t = sst(al[band], -0.002, 0.052)
    tgt = np.interp(th[band], c, ra, period=2 * np.pi) * (1 - t) + np.interp(th[band], c, rb, period=2 * np.pi) * t
    q = W + np.outer(al[band], d) + (rv[band] / np.maximum(r[band, None], 1e-6)) * tgt[:, None]
    print('FIST band', S, int(band.sum()), 'groove', round(float(np.median(r[band])), 3), '->', round(float(np.median(tgt)), 3))
    P[band] = q
    # hand scale
    hand = arm & (al > 0.03); k = 1 + (HS - 1) * sst((P - W) @ d, 0.03, 0.09)
    P[hand] = W + (P[hand] - W) * k[hand, None]
    Jr = HJ['joints'][S]
    def sj(v):
        v = np.array(v); a_ = (v - W) @ d; return W + (v - W) * (1 + (HS - 1) * sst(np.array(a_), 0.03, 0.09))
    FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
    J = {f: np.array([sj(Jr[f'finger{k_}-{j}']) for j in (1, 2, 3)] + [sj(Jr[f'finger{k_}-3_tip'])]) for f, k_ in FN.items()}
    FG = ('Index', 'Middle', 'Ring', 'Pinky')
    kn = unit(J['Index'][0] - J['Pinky'][0]); mid = 0.5 * (J['Index'][0] + J['Pinky'][0])
    e1 = unit(np.cross(kn, J['Middle'][0] - W))
    if (J['Middle'][1] - J['Middle'][0]) @ e1 < 0: e1 = -e1
    e2 = np.cross(kn, e1)
    if (W - mid) @ e2 < 0: e2 = -e2
    flex = 1.0 if np.cross(e1, e2) @ kn > 0 else -1.0
    # classify
    ids = np.nonzero(arm & ((P - W) @ d > 0.04) & (np.linalg.norm(P - mid, axis=1) < 0.26))[0]; Q = P[ids]
    def dist_chain(Q, ch):
        best = np.full(len(Q), 9.0); seg = np.zeros(len(Q), int); tt = np.zeros(len(Q))
        for s in range(3):
            a, b = ch[s], ch[s + 1]; ab = b - a; L = ab @ ab; t_ = (Q - a) @ ab / L; c_ = np.clip(t_, 0, 1)
            dd = np.linalg.norm(Q - a - np.outer(c_, ab), axis=1); m = dd < best
            best[m] = dd[m]; seg[m] = s; tt[m] = (t_ * np.sqrt(L))[m]
        return best, seg, tt
    D = {f: dist_chain(Q, J[f]) for f in FN}
    names = list(FN); DD = np.array([D[f][0] for f in names]); own = DD.argmin(0); dmin = DD.min(0)
    finger = dmin < 0.042
    palmv = Q[~finger]
    ep = (palmv - mid) @ e1; ez = (palmv - mid) @ e2; ax_ = (palmv - mid) @ kn
    m = (np.abs(ax_) < 0.06) & (ez > 0.03) & (ez < 0.1)
    face = float(np.percentile(ep[m], 92)) if m.any() else 0.02
    H = {f: float(np.median(D[f][0][(own == i) & finger])) for i, f in enumerate(names)}
    R = RG[S]
    AX = kn * flex; R = RG[S]
    # palm's inner face in the section plane; the grip touches it and passes under the knuckles
    pv = Q[~finger]; pe1, pe2 = (pv - mid) @ e1, (pv - mid) @ e2; pax = (pv - mid) @ kn
    bins = np.arange(0.0, 0.14, 0.015); fx = []
    for z in bins:
        k_ = (np.abs(pax) < 0.07) & (np.abs(pe2 - z) < 0.012)
        fx.append(pe1[k_].max() if k_.any() else np.nan)
    fx = np.array(fx); ok = ~np.isnan(fx); A, B = np.polyfit(bins[ok], fx[ok], 1)     # e1 = A e2 + B
    nn = np.array([1, -A]) / np.hypot(1, A)                                       # away from the palm
    hf = float(np.mean([H[f] for f in FG])); mc = np.mean([[(J[f][0] - mid) @ e1, (J[f][0] - mid) @ e2] for f in FG], 0)
    isp = np.zeros(n, bool); isp[ids] = True; tv = np.array([p.vertices[:] for p in me.polygons]); tv = tv[isp[tv].all(1)]; TP = P[tv]
    ta = (TP - mid) @ kn; tg = np.abs(ta).max(1) < 0.075; T1 = ((TP - mid) @ e1)[tg]; T2 = ((TP - mid) @ e2)[tg]
    def face_at(z):
        fxs = []
        for k_ in range(3):
            l_ = (k_ + 1) % 3; c1 = (T2[:, k_] - z) * (T2[:, l_] - z) < 0; t_ = (z - T2[c1, k_]) / (T2[c1, l_] - T2[c1, k_]); fxs.append(T1[c1, k_] + (T1[c1, l_] - T1[c1, k_]) * t_)
        fxs = np.concatenate(fxs); return fxs.max() if len(fxs) else None
    zs = np.arange(0.09, 0.19, 0.01); fs = [face_at(z) for z in zs]; ok = [f_ is not None for f_ in fs]
    A2, B2 = np.polyfit(zs[ok], np.array([f_ for f_ in fs if f_ is not None]), 1); print('FIST face', S, round(A2, 2), round(B2, 3))
    best = None
    for z in np.arange(-0.03, 0.1, 0.002):
        g2 = np.array([A2 * z + B2 + R + 0.004, z]); e_ = abs(np.hypot(*(mc - g2)) - (R + hf + 0.012))
        if best is None or e_ < best[0]: best = (e_, g2)
    g2 = np.array([0.078, 0.02]) if S == 'R' else np.array([0.064, 0.02]); best = (0, g2); G = mid + e1 * g2[0] + e2 * g2[1]
    print('FIST frame', S, 'palm', round(A, 2), round(B, 3), 'G2', np.round(g2, 3).tolist(), 'miss', round(best[0], 3), 'G', np.round(G, 3).tolist())
    NQ = Q.copy(); wrap_deg = {}
    for i, f in enumerate(names):
        m = (own == i) & finger; j = J[f]; q = Q[m]
        d_, seg, tt = dist_chain(q, j); Ls = np.linalg.norm(np.diff(j, axis=0), axis=1); cum = np.r_[0, np.cumsum(Ls)]; L = cum[-1]
        s_ = np.clip(cum[seg] + tt, 0, L + 0.02); T_ = np.array([(j[k + 1] - j[k]) / Ls[k] for k in range(3)])[seg]
        c_ = j[seg] + T_ * tt[:, None]; o = q - c_; w = o @ kn; Nin = np.cross(AX, T_); Nin /= np.linalg.norm(Nin, axis=1, keepdims=True); u = (o * Nin).sum(1)
        j2 = np.array([(j[0] - mid) @ e1, (j[0] - mid) @ e2]) - g2
        a0 = np.arctan2(j2[1], j2[0]); r0 = np.hypot(*j2); ax0 = (j[0] - G) @ kn
        if f != 'Thumb':
            Rf = R + H[f] + 0.002; Atot = min(L / Rf, 3.6); th = a0 + s_ / L * Atot; rr = r0 + (Rf - r0) * sst(s_, 0.0, 0.03); ax = np.full(len(s_), ax0) * (1 - 0.15 * s_ / L); sg_ = 1.0
        else:
            Rf = R + 2 * hf + H['Thumb'] + 0.002; Atot = -min(L / Rf, 2.4); th = a0 + s_ / L * Atot; rr = r0 + (Rf - r0) * sst(s_, 0.0, 0.05); axm = (J['Middle'][0] - G) @ kn; ax = ax0 + (axm - ax0) * sst(s_, 0.0, L); sg_ = -1.0
        C_ = G + np.outer(rr * np.cos(th), e1) + np.outer(rr * np.sin(th), e2) + np.outer(ax, kn)
        toG = -(np.outer(np.cos(th), e1) + np.outer(np.sin(th), e2))
        tip = np.maximum(s_ - L, 0) * sg_
        tan = np.outer(-np.sin(th), e1) + np.outer(np.cos(th), e2)
        NP = C_ + toG * (u * sg_ if f != 'Thumb' else np.abs(u) * np.sign(u))[:, None] + np.outer(w, kn) + tan * tip[:, None]
        wb = sst(s_, 0.0, 0.025)[:, None]
        NQ[m] = q * (1 - wb) + NP * wb; wrap_deg[f] = round(float(np.degrees(abs(Atot))))
    # thumb: rigid swing from its base so the tip lies over the fingers at the grip's outer side; length kept, no arc
    ti = names.index('Thumb'); m = (own == ti) & finger; t0 = J['Thumb'][0]; tq = Q[m]; rho = np.linalg.norm(tq - t0, axis=1); tip = tq[np.argmax(rho)]
    dirt = np.cos(np.radians(25)) * e1 + np.sin(np.radians(25)) * e2
    tgt = G + dirt * (R + 2 * hf + H['Thumb'] * 0.6) + kn * ((J['Middle'][0] - G) @ kn)
    a_ = unit(tip - t0); b_ = unit(tgt - t0); v_ = np.cross(a_, b_); sn = np.linalg.norm(v_); an = math.atan2(sn, a_ @ b_)
    wt = sst(rho, 0.012, 0.05)
    NQ[m] = t0 + np.array([rot(v_ / sn, an * w_) @ (q_ - t0) for q_, w_ in zip(tq, wt)])
    print('FIST thumb', S, 'turn', round(math.degrees(an)), 'reach', round(float(np.linalg.norm(tip - t0)), 3), 'to target', round(float(np.linalg.norm(tgt - t0)), 3))
    print('FIST wrapdeg', S, wrap_deg)
    # web across the grip: skin between the fingers' roots and the palm runs through the handle; those root vertices go to the palm side of the cylinder
    Pn = P.copy(); Pn[ids] = NQ; inv = -np.ones(n, int); inv[ids] = np.arange(len(ids)); moved = 0
    for it in range(4):
        T_ = Pn[tv]; ce = T_.mean(1) - G; ac = ce @ kn; rc = np.linalg.norm(ce - np.outer(ac, kn), axis=1); bad = tv[(rc < R + 0.002) & (np.abs(ac) < 0.085)]
        vs = np.unique(bad)
        for vi in vs:
            q_ = Pn[vi] - G; a1_, a2_ = q_ @ e1, q_ @ e2; ax_ = q_ @ kn; ang_ = np.arctan2(a2_, a1_)
            if a2_ < 0.012 and abs(ax_) < 0.09:
                r_ = max(np.hypot(a1_, a2_), R + 0.004); an_ = np.pi * 0.97 if a1_ < 0.012 else ang_
                Pn[vi] = G + e1 * r_ * np.cos(an_) + e2 * r_ * np.sin(an_) + kn * ax_; moved += 1
        print('FIST web', S, it, len(bad), len(vs))
    NQ = Pn[ids]
    posed = {}
    for f in names:
        j = J[f]; L = np.linalg.norm(np.diff(j, axis=0), axis=1).sum(); j2 = np.array([(j[0] - mid) @ e1, (j[0] - mid) @ e2]) - g2
        posed[f] = j.tolist()
    P[ids] = NQ
    # nothing inside the handle
    q_ = P[ids] - G; ax_ = q_ @ kn; pr = q_ - np.outer(ax_, kn); r_ = np.linalg.norm(pr, axis=1); m = (r_ < R + 0.001) & (np.abs(ax_) < 0.09)
    P[ids[m]] = G + np.outer(ax_[m], kn) + pr[m] / np.maximum(r_[m, None], 1e-5) * (R + 0.002)
    out[S] = dict(G=G.tolist(), kn=kn.tolist(), posed=posed, half=H, R=R, own=None)
    if S == 'R': json.dump(dict(G=G.tolist(), kn=kn.tolist()), open(HERE + 'scripts/grip.json', 'w'))
    fv = ids[finger]; isf = np.zeros(n, bool); isf[fv] = True
    Eg = np.array([e.vertices[:] for e in me.edges]); deg = np.bincount(Eg.ravel(), minlength=n).astype(float)
    for _ in range(3):
        s2 = np.zeros_like(P); np.add.at(s2, Eg[:, 0], P[Eg[:, 1]]); np.add.at(s2, Eg[:, 1], P[Eg[:, 0]])
        P[fv] = 0.6 * P[fv] + 0.4 * (s2[fv] / deg[fv, None])
# one limb: the hand's top rim stood 2-3 cm proud of the wrist over 2 cm, and the bend lived in 5 cm. The heel of the hand now flares from the bracer's end ring over 13 cm, and the weight blend runs the same way
Eg = np.array([e.vertices[:] for e in me.edges]); deg = np.bincount(Eg.ravel(), minlength=n).astype(float)
gi = {g.name: g.index for g in body.vertex_groups}
TA, TB = -0.03, 0.13
for S, sg in (() if MODE == 'r5' else (('R', -1), ('L', 1))):
    Fr = HJ['frames'][S]; W = np.array(Fr['W']); d = unit(np.array(Fr['d']))
    al = (P - W) @ d; rv = P - W - np.outer(al, d); r = np.linalg.norm(rv, axis=1)
    arm = (np.sign(P[:, 0]) == sg) & (pa == 0) & (r < 0.24) & (al > -0.25)
    U = unit(np.cross(d, [0, 0, 1.0])); V_ = np.cross(d, U); th = np.arctan2(rv @ V_, rv @ U)
    bins = np.linspace(-np.pi, np.pi, 13); c = 0.5 * (bins[1:] + bins[:-1])
    def env(lo, hi):
        m = arm & (al > lo) & (al < hi); v = np.array([r[m & (th >= bins[i]) & (th < bins[i + 1])].max() if (m & (th >= bins[i]) & (th < bins[i + 1])).any() else np.nan for i in range(12)])
        ok = ~np.isnan(v); return np.interp(c, c[ok], v[ok], period=2 * np.pi)
    ra = env(-0.05, -0.006); rh = np.maximum(env(0.15, 0.2), ra)
    win = arm & (al > -0.004) & (al < 0.16); ai = al[win]; t = sst(ai, -0.004, 0.16)
    E_ = np.interp(th[win], c, ra, period=2 * np.pi) * (1 - t) + np.interp(th[win], c, rh, period=2 * np.pi) * t
    set_ = (ai < 0.09) | (r[win] > E_); idw = np.nonzero(win)[0][set_]
    P[idw] = W + np.outer(ai[set_], d) + rv[idw] / np.maximum(r[idw, None], 1e-5) * E_[set_, None]
    print('TAPER', S, 'moved', int(set_.sum()), 'of', int(win.sum()), 'ra', round(float(ra.mean()), 3), 'rh', round(float(rh.mean()), 3))
    al = (P - W) @ d
    B_ = f'Bip01 {S} '
    wv = np.nonzero(arm & (al > TA) & (al < 0.2))[0]; tt = sst(al[wv], TA, TB)
    F_, H_, Hh = gi[B_ + 'Forearm'], gi[B_ + 'Hand'], gi[B_ + 'Hand_h']; Fh = gi.get(B_ + 'Forearm_h')
    gs = body.vertex_groups
    for vi, t_ in zip(wv.tolist(), tt.tolist()):
        for nm_ in (B_ + 'Forearm', B_ + 'Hand', B_ + 'Hand_h'): gs[nm_].remove([vi])
        a_ = max(1 - 2 * t_, 0); b_ = 1 - abs(2 * t_ - 1); c_ = max(2 * t_ - 1, 0)
        rest_ = sum(g.weight for g in me.vertices[vi].groups)
        k_ = max(1 - rest_, 0)
        if a_ > 0.005: gs[B_ + 'Forearm'].add([vi], a_ * k_, 'REPLACE')
        if b_ > 0.005: gs[B_ + 'Hand_h'].add([vi], b_ * k_, 'REPLACE')
        if c_ > 0.005: gs[B_ + 'Hand'].add([vi], c_ * k_, 'REPLACE')
    print('BLEND', S, len(wv))
json.dump(out, open(HERE + 'work/fist.json', 'w'))
for v, q in zip(me.vertices, P): v.co = Vector(q)
me.update()
# the zip left open edges on the arm ring: boundary vertices in the wrist zones weld, what stays open is filled, new faces borrow UVs from their vertices
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
def zone_v(v):
    for S in 'RL':
        Fr = HJ['frames'][S]; W = np.array(Fr['W']); d = unit(np.array(Fr['d'])); a_ = (np.array(v.co[:]) - W) @ d
        if -0.03 < a_ < 0.06 and np.linalg.norm(np.array(v.co[:]) - W) < 0.16: return True
    return False
bd = [v for v in bm.verts if v.is_boundary and zone_v(v)] if MODE != 'r5' else []
n0 = len(bd); bmesh.ops.remove_doubles(bm, verts=bd, dist=0.006)
for it in range(0 if MODE == 'r5' else 4):
    bm.edges.ensure_lookup_table()
    for e in [e for e in bm.edges if len(e.link_faces) > 2 and zone_v(e.verts[0])]:
        if not e.is_valid: continue
        fs = sorted(e.link_faces, key=lambda f: f.calc_area())
        bmesh.ops.delete(bm, geom=fs[:len(fs) - 2], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    op = [e for e in bm.edges if e.is_boundary and zone_v(e.verts[0])]
    print('WELD round', it, 'open', len(op))
    if not op: break
    bmesh.ops.collapse(bm, edges=op[:1] if it else op)
bm.edges.ensure_lookup_table()
oe = [e for e in bm.edges if e.is_boundary and zone_v(e.verts[0])]
n1 = len(oe)
old = set(bm.faces)
if MODE != 'r5': bmesh.ops.holes_fill(bm, edges=oe, sides=64)
new = [f for f in bm.faces if f not in old]
bmesh.ops.triangulate(bm, faces=new)
new = [f for f in bm.faces if f not in old]
mt = bm.faces.layers.int.get('mat')
for nm_ in ('UVMap', 'HeadUV', 'PartUV'):
    ul = bm.loops.layers.uv.get(nm_)
    if ul is None: continue
    for f in new:
        for l in f.loops:
            src = next((x for x in l.vert.link_loops if x.face in old), None)
            if src is not None: l[ul].uv = src[ul].uv
for f in new:
    f.smooth = True
    if mt is not None: f[mt] = 0
bmesh.ops.recalc_face_normals(bm, faces=new + [g for f in new for e in f.edges for g in e.link_faces])
mf = [e for e in bm.edges if len(e.link_faces) > 2 and zone_v(e.verts[0])]
print('WELD boundary verts', n0, 'open after weld', n1, 'filled faces', len(new), 'multi', len(mf), 'open now', sum(1 for e in bm.edges if e.is_boundary and zone_v(e.verts[0])))
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FIST done')
