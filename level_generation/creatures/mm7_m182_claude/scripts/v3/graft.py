"""v3 head graft (system Python): the cdr1 body/wings (work/v3/src.npz, the installed MM6 cdr1 LOD0, welded) with the
v2 MM7 head (work/v3/v2_master.npz: the head texture-set piece, 1,808 triangles, its 22-vertex back ring) joined by
a lofted neck. Writes work/v3/graft.npz (co, tri, uv, uv_v2head, mat, W over the cdr1 bones, origin flags) and
work/v3/graft_report.json.

1. Head placement: p' = J_c + R (S (p - J_v)): the v2 jaw hinge J_v onto the cdr1 Jaw bone head J_c (so the cdr1 jaw
   rotation opens the new jaw about its own hinge), uniform scale s, muzzle (in front of the hinge) stretched by e
   along the head axis with a soft transition, optional pitch R. Keeps the head exactly mirror-symmetric.
2. cdr1 cut: plane through the neck centreline at cut_y, normal = centreline tangent; every neck/head face with a
   vertex beyond it and every separate piece (horns, teeth, spikes) whose centre lies beyond it is removed. The cut
   boundary vertices are projected onto the plane (clean planar ring).
3. Ring counts: the shorter of the two rings gets its longest edges split (adjacent triangle split, UV interpolated)
   until both rings have the same vertex count; the loft then joins them with quads only (matched counts at both
   seams, no zipper).
4. Loft: Hermite centreline (end tangents = cdr1 neck tangent and the head ring's axis), cross-sections interpolated
   per matched ring vertex in rotation-minimising frames, smoothstep blend; rings every loft_edge metres.
5. Weights: cdr1 kept vertices unchanged; head vertices take the v2 weights of the same-named bones (Head, Jaw, Neck*),
   renormalised; loft vertices blend the two ring weights; then a Laplacian smoothing band across both seams."""
import json, sys
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(P / 'scripts/v3'))
from meshutil import boundary_loops, components
from scipy.spatial import cKDTree
prm = json.loads((P / 'work/v3/graft_params.json').read_text())
A = np.load(P / 'work/v3/src.npz'); V = np.load(P / 'work/v3/v2_master.npz')
bonesA = [str(b) for b in A['bones']]; bonesV = [str(b) for b in V['bones']]
rep = {'params': prm}

# ---------------- 1. head piece ----------------
hv = V['pa_head']; ht = V['tri'][hv[V['tri']].all(1)]; huv = V['uv'][hv[V['tri']].all(1)]
used = np.unique(ht); remap = -np.ones(len(V['co']), int); remap[used] = np.arange(len(used))
Hco0 = V['co'][used].copy(); Htri = remap[ht]
# separate pieces of the head set: horns (v2 parts 3, 6) and cheek spikes grow about their roots (the native horns
# and spikes are longer than Meshy's); the degenerate 6-vertex piece (part 4, zero size) is dropped.
from scipy.spatial import cKDTree
hcomp = components(Htri, len(Hco0)); hmain = np.bincount(hcomp).argmax(); mtree = cKDTree(Hco0[hcomp == hmain])
hpart = V['pa_part'][used]; grown = {}; dropv = np.zeros(len(Hco0), bool)
for c in np.unique(hcomp):
    if c == hmain: continue
    vs = np.where(hcomp == c)[0]
    if np.ptp(Hco0[vs], 0).max() < 0.002: dropv[vs] = True; continue
    f = prm['horn_grow'] if set(hpart[vs]) & {3, 6} else prm['spike_grow']
    dd, _ = mtree.query(Hco0[vs]); root = Hco0[vs[np.argmin(dd)]]
    Hco0[vs] = root + f * (Hco0[vs] - root); grown[int(c)] = f
if dropv.any():
    keepT = ~dropv[Htri].any(1); Htri = Htri[keepT]; ht = ht[keepT]; huv = huv[keepT]
    k2 = np.unique(Htri); r2 = -np.ones(len(Hco0), int); r2[k2] = np.arange(len(k2))
    Hco0 = Hco0[k2]; Htri = r2[Htri]; used = used[k2]
rep_pieces = {'grown': len(grown), 'dropped_vertices': int(dropv.sum())}
# head piece class per vertex: 1 main head surface, 2 horns (v2 parts 3, 6), 3 other separate spikes
hcomp2 = components(Htri, len(Hco0)); hmain2 = np.bincount(hcomp2).argmax(); hp2 = V['pa_part'][used]
HPIECE = np.where(hcomp2 == hmain2, 1, np.where(np.isin(hp2, [3, 6]), 2, 3))
Huv = np.stack([(huv[..., 0] * 6208 - 2080) / 2048, huv[..., 1]], -1)       # v2 head 2K set coordinates
Jv = V['heads'][bonesV.index('Jaw')]; Jc = A['heads'][bonesA.index('Jaw')]
s, e = prm['scale'], prm['snout_stretch']; k = 0.004
q = (Hco0 - Jv)
yy = q[:, 1]; soft = -k * np.logaddexp(0, -yy / k)          # ~ yy for yy << 0 (muzzle), ~ 0 behind the hinge
q[:, 1] = yy + (e - 1) * soft
a = np.radians(prm['pitch_deg']); R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
Hco = Jc + (s * q) @ R.T
HW = np.zeros((len(used), len(bonesA)), np.float32)
for j, b in enumerate(bonesV):
    if b in bonesA: HW[:, bonesA.index(b)] = V['W'][used, j]
HW /= np.maximum(HW.sum(1, keepdims=True), 1e-9)
loopsH = boundary_loops(Htri); ringH = max(loopsH, key=len)
rep['head'] = {'pieces': rep_pieces, 'vertices': len(Hco), 'triangles': len(Htri), 'ring': len(ringH), 'other_loops': sorted(len(l) for l in loopsH if l is not ringH),
               'snout_tip': Hco[np.argmin(Hco[:, 1])].round(4).tolist(), 'size_m': np.ptp(Hco, 0).round(4).tolist()}

# ---------------- 2. cdr1 cut ----------------
# The plane comes from the neck centreline of the uncut mesh (mode "plane" writes work/v3/cut_plane.json); the cut
# itself is a Blender bisect (scripts/v3/cut_cdr1.py -> work/v3/cut.npz), so the ring is exactly planar.
def neck_plane():
    co = A['co']; tri = A['tri']; comp = components(tri, len(co)); main = np.bincount(comp).argmax()
    chain = np.array([A['heads'][bonesA.index(b)] for b in ('Spine2', 'Neck1', 'Neck2', 'Neck3', 'Head')])
    def chain_point(y):
        for i in range(len(chain) - 1):
            a_, b_ = chain[i], chain[i + 1]
            if (a_[1] - y) * (b_[1] - y) <= 0:
                f = (y - a_[1]) / (b_[1] - a_[1]); return a_ + f * (b_ - a_), (b_ - a_) / np.linalg.norm(b_ - a_)
    def centre_at(p, t, r=0.2, h=0.012):
        for _ in range(6):
            s_ = (comp == main) & (np.abs((co - p) @ t) < h) & (np.linalg.norm(co - p, axis=1) < r)
            c = co[s_].mean(0); c[0] = 0; p = c
        return p
    cl = np.array([centre_at(*chain_point(y)) for y in np.arange(-0.95, -1.27, -0.02)])
    ic = int(np.argmin(np.abs(cl[:, 1] - prm['cut_y'])))
    t = cl[min(ic + 1, len(cl) - 1)] - cl[max(ic - 1, 0)]; return cl[ic], t / np.linalg.norm(t), cl


if len(sys.argv) > 1 and sys.argv[1] == 'plane':
    c0, n0, cl = neck_plane()
    (P / 'work/v3/cut_plane.json').write_text(json.dumps({'centre': c0.tolist(), 'normal': n0.tolist(), 'centreline': cl.round(4).tolist()}, indent=1))
    print('PLANE', ','.join(f'{v:.6f}' for v in c0), ','.join(f'{v:.6f}' for v in n0)); sys.exit()
pl = json.loads((P / 'work/v3/cut_plane.json').read_text()); c0, n0 = np.array(pl['centre']), np.array(pl['normal'])
C = np.load(P / 'work/v3/cut.npz')
co = C['co']; tri = C['tri']; uv = C['uv']; mat = C['mat']; W = C['W']
assert [str(b) for b in C['bones']] == bonesA
keep_t = np.ones(len(tri), bool)
loops = boundary_loops(tri); onplane = [l for l in loops if np.abs((co[l] - c0) @ n0).max() < 1e-4 and len(l) > 4]
assert len(onplane) == 1, [len(l) for l in onplane]
ring0 = onplane[0]
rep['cut'] = {'centre': c0.round(4).tolist(), 'normal': n0.round(4).tolist(), 'triangles_after': len(tri), 'ring': len(ring0),
              'other_open_loops_gt4': sorted(len(l) for l in loops if l is not ring0 and len(l) > 4)}
# assemble kept cdr1 part
kv = np.unique(tri[keep_t]); mapA = -np.ones(len(co), int); mapA[kv] = np.arange(len(kv))
Aco = co[kv]; Atri = mapA[tri[keep_t]]; Auv = uv[keep_t]; Amat = mat[keep_t]; AW = W[kv]
ring0 = [mapA[v] for v in ring0]
nA = len(Aco)
Vco = np.vstack([Aco, Hco]); Tri = [Atri, Htri + nA]; UV = [Auv, np.zeros((len(Htri), 3, 2))]; UV2 = [np.full((len(Atri), 3, 2), -1.), Huv]
MAT = [Amat, np.ones(len(Htri), int)]; WW = np.vstack([AW, HW]); ORIG = np.r_[np.zeros(nA, int), np.ones(len(Hco), int)]; HP = np.r_[np.zeros(nA, int), HPIECE]
ring1 = [v + nA for v in ringH]
TRI = np.vstack(Tri); UVA = np.vstack(UV); UVB = np.vstack(UV2); MATA = np.concatenate(MAT)


# ---------------- 3. ring frames and matched counts ----------------
def frame(pts, axis):
    c = pts.mean(0); up = np.array([0, 0, 1.]) - axis * axis[2]; up /= np.linalg.norm(up); side = np.cross(axis, up)
    return c, up, side


def order_ring(ring, axis):
    c, up, side = frame(Vco[ring], axis)
    th = np.arctan2((Vco[ring] - c) @ side, (Vco[ring] - c) @ up)
    # loop order is cyclic; make it increasing in angle, starting at the top
    if np.sign(np.sum(np.sin(np.diff(np.unwrap(th))))) < 0: ring = ring[::-1]; th = th[::-1]
    i0 = int(np.argmin(np.abs(np.angle(np.exp(1j * th))))); return list(ring[i0:]) + list(ring[:i0])


c1 = Vco[ring1].mean(0); _, _, vt = np.linalg.svd(Vco[ring1] - c1); n1 = vt[2] * np.sign(vt[2] @ (Hco.mean(0) - c1))   # into the head
ring0 = order_ring(np.array(ring0), n0); ring1 = order_ring(np.array(ring1), n1)


def split_longest(ring, count):
    """Split the longest boundary edge of a ring (and its triangle) until the ring has `count` vertices."""
    global Vco, TRI, UVA, UVB, MATA, WW, ORIG, HP
    ring = list(ring)
    while len(ring) < count:
        L = [np.linalg.norm(Vco[ring[i]] - Vco[ring[(i + 1) % len(ring)]]) for i in range(len(ring))]
        i = int(np.argmax(L)); a_, b_ = ring[i], ring[(i + 1) % len(ring)]
        m = len(Vco); Vco = np.vstack([Vco, (Vco[a_] + Vco[b_]) / 2]); WW = np.vstack([WW, (WW[a_] + WW[b_]) / 2]); ORIG = np.r_[ORIG, ORIG[a_]]; HP = np.r_[HP, HP[a_]]
        f = int(np.where([(a_ in t) and (b_ in t) for t in TRI])[0][0]); t = list(TRI[f]); o = [x for x in t if x not in (a_, b_)][0]
        ia, ib, io = t.index(a_), t.index(b_), t.index(o)
        uvm = (UVA[f, ia] + UVA[f, ib]) / 2; uvm2 = (UVB[f, ia] + UVB[f, ib]) / 2
        # keep winding: replace the edge a-b in the triangle by a-m-b
        t1 = t.copy(); t1[ib] = m; u1 = UVA[f].copy(); u1[ib] = uvm; w1 = UVB[f].copy(); w1[ib] = uvm2
        t2 = t.copy(); t2[ia] = m; u2 = UVA[f].copy(); u2[ia] = uvm; w2 = UVB[f].copy(); w2[ia] = uvm2
        TRI[f] = t1; UVA[f] = u1; UVB[f] = w1
        TRI = np.vstack([TRI, t2]); UVA = np.concatenate([UVA, u2[None]]); UVB = np.concatenate([UVB, w2[None]]); MATA = np.r_[MATA, MATA[f]]
        ring.insert(i + 1, m)
    return ring


M = max(len(ring0), len(ring1)); ring0 = split_longest(ring0, M); ring1 = split_longest(ring1, M)
rep['rings_matched'] = M

# ---------------- 4. loft ----------------
p0, p1 = Vco[ring0].mean(0), Vco[ring1].mean(0); p0[0] = p1[0] = 0
dist = np.linalg.norm(p1 - p0); T0, T1 = n0 * dist * 1.0, n1 * dist * 1.0
K = max(3, int(np.ceil(dist / prm['loft_edge'])))
def herm(t):
    h00, h10, h01, h11 = 2 * t**3 - 3 * t**2 + 1, t**3 - 2 * t**2 + t, -2 * t**3 + 3 * t**2, t**3 - t**2
    return h00 * p0 + h10 * T0 + h01 * p1 + h11 * T1
def dherm(t):
    d = (6 * t**2 - 6 * t) * p0 + (3 * t**2 - 4 * t + 1) * T0 + (-6 * t**2 + 6 * t) * p1 + (3 * t**2 - 2 * t) * T1; return d / np.linalg.norm(d)
# rotation-minimising frames by double reflection, from the start frame
def rmf(ts):
    up = np.array([0, 0, 1.]) - n0 * n0[2]; up /= np.linalg.norm(up); F = [(herm(ts[0]), dherm(ts[0]), up)]
    for t in ts[1:]:
        x0, t0, r0 = F[-1]; x1, t1 = herm(t), dherm(t)
        v1 = x1 - x0; c1_ = v1 @ v1; rL = r0 - (2 / c1_) * (v1 @ r0) * v1; tL = t0 - (2 / c1_) * (v1 @ t0) * v1
        v2 = t1 - tL; c2 = v2 @ v2; r1 = rL - (2 / c2) * (v2 @ rL) * v2 if c2 > 1e-12 else rL; F.append((x1, t1, r1))
    return F
ts = np.linspace(0, 1, K + 1); F = rmf(ts)
# local 2D offsets of each ring vertex in its end frame
def local(ring, fr):
    x, t, u = fr; sdv = np.cross(t, u); d = Vco[ring] - x; return np.stack([d @ u, d @ sdv, d @ t], 1)
L0 = local(ring0, F[0]); L1 = local(ring1, F[-1])
twist_err = None
rings = [ring0]; LIN = []
for i in range(1, K):
    # the same ring with a linear blend (scripts/v3/relax_loft.py moves the loft there after the UV restore: the
    # smoothstep blend crowded the first rings at the flared nape and stretched them 3-6x in Attack)
    t = ts[i]; x, tt, u = F[i]; sdv = np.cross(tt, u); off = (1 - t) * L0 + t * L1
    LIN.append(x + off[:, :1] * u + off[:, 1:2] * sdv + off[:, 2:3] * tt)
    t = ts[i]; w = t * t * (3 - 2 * t); x, tt, u = F[i]; sdv = np.cross(tt, u)
    off = (1 - w) * L0 + w * L1          # includes the axial offset: the head ring is not planar (throat V)
    pts = x + off[:, :1] * u + off[:, 1:2] * sdv + off[:, 2:3] * tt
    idx = list(range(len(Vco), len(Vco) + M)); Vco = np.vstack([Vco, pts]); rings.append(idx)
    WW = np.vstack([WW, (1 - w) * WW[ring0] + w * WW[ring1]]); ORIG = np.r_[ORIG, np.full(M, 2)]; HP = np.r_[HP, np.zeros(M, int)]
rings.append(ring1)
# the end frame of the RMF may be rotated against ring1's own frame: report the residual (should be small)
x, tt, u = F[-1]; up1 = np.array([0, 0, 1.]) - n1 * n1[2]; up1 /= np.linalg.norm(up1); twist_err = float(np.degrees(np.arccos(np.clip(u @ up1, -1, 1))))
newT = []
for r in range(len(rings) - 1):
    a_, b_ = rings[r], rings[r + 1]
    for j in range(M):
        j1 = (j + 1) % M; A0, A1, B0, B1 = a_[j], a_[j1], b_[j], b_[j1]
        if np.linalg.norm(Vco[A0] - Vco[B1]) < np.linalg.norm(Vco[A1] - Vco[B0]): newT += [[A0, A1, B1], [A0, B1, B0]]
        else: newT += [[A0, A1, B0], [A1, B1, B0]]
newT = np.array(newT)
# outward winding: normal should point away from the centreline
cen = np.array([herm(np.clip(((Vco[t].mean(0) - p0) @ (p1 - p0)) / (dist**2), 0, 1)) for t in newT])
nrm = np.cross(Vco[newT[:, 1]] - Vco[newT[:, 0]], Vco[newT[:, 2]] - Vco[newT[:, 0]])
if np.mean(np.sum(nrm * (Vco[newT].mean(1) - cen), 1) > 0) < 0.5: newT = newT[:, ::-1]
TRI = np.vstack([TRI, newT]); UVA = np.concatenate([UVA, np.zeros((len(newT), 3, 2))]); UVB = np.concatenate([UVB, np.full((len(newT), 3, 2), -1.)])
MATA = np.r_[MATA, np.zeros(len(newT), int)]
rep['loft'] = {'rings_between': K - 1, 'length_m': round(float(dist), 4), 'triangles': len(newT), 'frame_twist_deg': round(twist_err, 2)}

# ---------------- 4b. wing roots (v3b) ----------------
# The installed cdr1 weights let the wing root lag: wing-material vertices 4-25 cm from the body carried only
# 0.16-0.75 wing weight and the body none, so the inner membrane stayed nearly static while the wing beat over it
# (hidden on cdr1 by its uniform paint, visible on v3a). Now the wing share rises from 0.3 at the junction (vertices
# shared by the body and wing materials) to 1 at ROOT metres along the wing, and body vertices within BODY metres
# of the junction take up to 0.3 of the wing so the shoulder skin follows the root instead of creasing. The wing
# bones keep their cdr1 proportions (Wing0 where cdr1 had none); the body bones keep theirs.
ROOT, BODY, WJ = prm.get('wing_root_m', .08), prm.get('wing_body_m', .05), prm.get('wing_junction_share', .3)
wingb = [i for i, n in enumerate(bonesA) if 'Wing' in n]; bodyb = [i for i in range(len(bonesA)) if i not in wingb]
vb = np.zeros(len(Vco), bool); vw = np.zeros(len(Vco), bool)
vb[np.unique(TRI[MATA == 0])] = True; vw[np.unique(TRI[MATA == 2])] = True
cdr = ORIG == 0; junc = vb & vw & cdr
jt = cKDTree(Vco[junc]); dj = jt.query(Vco)[0]
target = np.full(len(Vco), -1.)
wv = vw & cdr; target[wv] = WJ + (1 - WJ) * np.clip(dj[wv] / ROOT, 0, 1) ** 2 * (3 - 2 * np.clip(dj[wv] / ROOT, 0, 1))
bv_ = vb & ~vw & cdr & (dj < BODY) & (Vco[:, 2] > .55); target[bv_] = WJ * (1 - dj[bv_] / BODY) ** 2
changed = 0
for v in np.where(target >= 0)[0]:
    cur = WW[v, wingb].sum(); t = max(target[v], cur) if vw[v] else max(target[v], cur)
    if t <= cur + 1e-4: continue
    side = 'L' if Vco[v, 0] > 0 else 'R'
    if cur > .02: WW[v, wingb] *= t / cur
    else: WW[v, wingb] = 0; WW[v, bonesA.index(f'{side}Wing0')] = t
    bsum = WW[v, bodyb].sum()
    if bsum > 1e-6: WW[v, bodyb] *= (1 - t) / bsum
    changed += 1
rep['wing_root'] = {'root_m': ROOT, 'body_m': BODY, 'junction_share': WJ, 'junction_vertices': int(junc.sum()), 'reweighted_vertices': changed}

# ---------------- 5. weights smoothing across the seams ----------------
nbr = [set() for _ in range(len(Vco))]
for t in TRI:
    for i in range(3): nbr[t[i]].update((t[(i + 1) % 3], t[(i + 2) % 3]))
band = (ORIG == 2).copy()
for _ in range(prm.get('weight_band_rings', 3)):
    grow = band.copy()
    for v in np.where(band)[0]: grow[list(nbr[v])] = True
    band = grow
jaw = bonesA.index('Jaw')
band &= ~(WW[:, jaw] > 0.05)          # never smear the jaw ownership
for _ in range(prm['weight_smooth_iters']):
    Wn = WW.copy()
    for v in np.where(band)[0]:
        nb = list(nbr[v]); Wn[v] = 0.5 * WW[v] + 0.5 * WW[nb].mean(0)
    WW = Wn
# 4 influences
for v in range(len(WW)):
    o = np.argsort(WW[v])[::-1]; WW[v, o[4:]] = 0
WW /= np.maximum(WW.sum(1, keepdims=True), 1e-9)
rep['weights'] = {'smoothed_vertices': int(band.sum()), 'max_influences': int((WW > 0).sum(1).max())}
rep['totals'] = {'vertices': len(Vco), 'triangles': len(TRI), 'by_material': np.bincount(MATA, minlength=3).tolist()}
np.savez(P / 'work/v3/graft.npz', co=Vco, tri=TRI, uv=UVA, uv_v2head=UVB, mat=MATA, W=WW.astype(np.float32), orig=ORIG, pa_v3part=ORIG, pa_hpiece=HP, bones=np.array(bonesA),
         ring0=np.array(ring0), ring1=np.array(ring1), loft_linear=np.vstack(LIN))
(P / 'work/v3/graft_report.json').write_text(json.dumps(rep, indent=1) + '\n'); print('GRAFT', json.dumps(rep))
