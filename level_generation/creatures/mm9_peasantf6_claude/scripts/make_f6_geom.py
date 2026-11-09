"""PeasantF6 geometry = PeasantF5's approved final geometry (positions after F5's tweak_pf.py, read from F5's work/uv_tex2.npz via `orig`)
with the coif and the four brooches removed, F5's human ears pressed flat onto the skull, and three new parts, all numpy:
  hair  - a bob shell over the skull: the skull's hair-region faces offset outward along their normals by MM9 PeasantF6's own hair volume
          (ray from the head centre to MM9's head mesh, x HAIR_K), tapered to 6 mm at the face opening and thin round the ear roots, with a
          rim strip from the shell edge to 2 mm inside the skull (closed: no see-through under the bob);
  ears  - procedural cupped elf leaves (PeasantF8 / M7d / M2d generator), root inside the skull at the pressed human ear, tip from MM9's;
  braid - a tapered tube with alternating lobes from inside the hair at the nape down the back along MM9's braid line (kept off the dress).
Args: <f5 final asm npz> <mm9 f6 head npz> <out npz> [key=value ...]"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree

IN, MM9, OUT = sys.argv[1:4]
opt = dict(a.split('=', 1) for a in sys.argv[4:])
f3 = lambda s: np.array([float(x) for x in s.split(',')])
HAIR_K = float(opt.get('hair_k', '0.85'))
TMIN = float(opt.get('tmin', '0.006'))
EAR_ROOT = f3(opt.get('root', '0.066,0.008,0.668'))
EAR_TIP = f3(opt.get('tip', '0.128,0.042,0.760'))
EAR_W = float(opt.get('width', '0.044'))
FWD = float(opt.get('fwd', '0.45'))
REP = {}

S = np.load(IN); co, tri, comp = S['co'].copy(), S['tri'].copy(), S['comp'].copy(); names = [str(x) for x in S['names']]
extra = {k: S[k] for k in S.files if k not in ('co', 'tri', 'comp', 'names')}


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def vnormals(P, T):
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); N = np.zeros_like(P)
    for c in range(3): np.add.at(N, T[:, c], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


def edges_of(T):
    return np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1), axis=0)


def laplace(P, T, sel, passes, k=0.5, w=None, taubin=False):
    e = edges_of(T); P = P.copy(); w = np.ones(len(P)) if w is None else w
    for it in range(passes):
        kk = (k if it % 2 == 0 else -0.53) if taubin else k
        acc = np.zeros_like(P); deg = np.zeros(len(P))
        np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        L = acc / np.maximum(deg, 1)[:, None]
        P[sel] = P[sel] + (L[sel] - P[sel]) * (kk * w[sel])[:, None]
    return P


# ---- 1. drop the coif and the brooches
drop = [names.index('coif'), names.index('ornaments')]
keepv = ~np.isin(comp, drop); keept = keepv[tri].all(1)
idx = -np.ones(len(co), int); idx[keepv] = np.arange(keepv.sum())
co, comp, tri = co[keepv], comp[keepv], idx[tri[keept]]
newnames = [n for i, n in enumerate(names) if i not in drop]
comp = np.array([newnames.index(names[c]) for c in comp]); names = newnames
H = names.index('head'); hv = comp == H; htri = tri[comp[tri[:, 0]] == H]
REP['dropped'] = ['coif', 'ornaments']

# ---- 2. F5's human ears pressed onto the skull (else two ears per side): each head vertex in the ear box takes at most the cheek's distance
# from the midline at its height (+2 mm), faded over 1 cm at the box edges, then relaxed by Laplacian passes weighted by the press weight
PY0, PY1, PZ0, PZ1 = f3(opt.get('pressbox', '-0.040,0.045,0.615,0.775'))
Q = co.copy(); pw = np.zeros(len(co)); npress = 0
for vi in np.where(hv)[0]:
    x, y, z = co[vi]
    if not (PY0 <= y <= PY1 and PZ0 <= z <= PZ1): continue
    ref = hv & (np.sign(co[:, 0]) == np.sign(x)) & (np.abs(co[:, 2] - z) < 0.01) & (co[:, 1] > PY0 - 0.02) & (co[:, 1] < PY0)
    if not ref.any(): continue
    cap = np.abs(co[ref, 0]).max() + 0.002
    w = max(0.0, min(1.0, (y - PY0) / 0.01, (PY1 - y) / 0.01, (z - PZ0) / 0.01, (PZ1 - z) / 0.01)); pw[vi] = w
    if abs(x) > cap:
        Q[vi, 0] = np.sign(x) * (abs(x) + (cap - abs(x)) * w); npress += 1
co = laplace(Q, htri, hv & (pw > 0), int(opt.get('press_smooth', '25')), 0.5, pw)
REP['pressed_ear_vertices'] = npress
# F5's skull carries a midline crease on the forehead and crown (hidden by the coif until now): relaxed in place on the skull above the brows
cz = hv & (np.abs(co[:, 0]) < 0.03) & (co[:, 2] > float(opt.get('crease_z', '0.725')))
cw = ss(0.03 - np.abs(co[:, 0]), 0, 0.012) * ss(co[:, 2], float(opt.get('crease_z', '0.725')), float(opt.get('crease_z', '0.725')) + 0.012)
co = laplace(co, htri, cz, int(opt.get('crease_smooth', '20')), 0.5, cw, taubin=True)      # Taubin: no shrinking of the forehead

# ---- 3. hair region on the skull: above a hairline that depends on the azimuth round the head (0 = front)
C = np.array([0.0, -0.01, 0.69])
phi = np.degrees(np.arctan2(np.abs(co[:, 0]), -(co[:, 1] - C[1])))
HL = np.array([[0, 0.768], [25, 0.762], [45, 0.742], [58, 0.712], [68, 0.665], [78, 0.625], [92, 0.600], [130, 0.590], [180, 0.588]])
zline = np.interp(phi, HL[:, 0], HL[:, 1])
eyeball = np.zeros(len(co), bool)
# the eyeballs are separate closed pieces inside the head part: never hair
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ne = edges_of(htri); A = coo_matrix((np.ones(len(ne)), (ne[:, 0], ne[:, 1])), shape=(len(co), len(co)))
ncc, lab = connected_components(A, directed=False)
hl = lab[hv]; big = np.bincount(hl).argmax(); skull = hv & (lab == big)
hairv = skull & (co[:, 2] > zline)
hf = htri[hairv[htri].all(1)]
REP['hair_faces'] = int(len(hf))
# keep the largest edge-connected piece of the hair faces (stray specks at the hairline drop out)
fe = np.vstack([hf[:, [0, 1]], hf[:, [1, 2]], hf[:, [2, 0]]])
A2 = coo_matrix((np.ones(len(fe)), (fe[:, 0], fe[:, 1])), shape=(len(co), len(co)))
_, lab2 = connected_components(A2, directed=False); main = np.bincount(lab2[hf[:, 0]]).argmax(); hf = hf[lab2[hf[:, 0]] == main]

# ---- 4. thickness from MM9 PeasantF6's hair: ray from C through each hair vertex to MM9's head mesh
M = np.load(MM9); P6, T6, B6 = M['P6'], M['T6'], M['B6']
ht = T6[~(B6[T6] == 'FHP Ponytail11').any(1) & (P6[T6][:, :, 2].mean(1) > 0.57)]      # the head and hair (not the braid, not the shoulders)
a6, b6, c6 = P6[ht[:, 0]], P6[ht[:, 1]], P6[ht[:, 2]]


def ray_hit(o, d):
    e1, e2 = b6 - a6, c6 - a6; p = np.cross(d, e2); det = (e1 * p).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); s = o - a6; u = (s * p).sum(1) * inv; q = np.cross(s, e1); v = (d * q).sum(1) * inv
    t = (e2 * q).sum(1) * inv; good = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return t[good].max() if good.any() else np.nan


hverts = np.unique(hf)
N = vnormals(co, htri)
thick = np.zeros(len(co))
for vi in hverts:
    d = co[vi] - C; r = np.linalg.norm(d); s = ray_hit(C, d / r)
    thick[vi] = np.clip((s - r) * HAIR_K, float(opt.get('bulk', '0.014')), float(opt.get('tmax', '0.06'))) if np.isfinite(s) else TMIN
# taper toward the face opening and round the ear roots; smooth the field
facev = skull & ~hairv & (phi < float(opt.get('face_phi', '82'))) & (co[:, 2] > float(opt.get("face_z", "0.6")))      # the face opening only: the bob's lower edge keeps its thickness
fd = cKDTree(co[facev]).query(co[hverts])[0]
# taper distance: long over the forehead, short at the temples and sides (the bob stands out beside the face, as MM9's)
TAPER = np.interp(phi[hverts], [0, 40, 65], [float(opt.get('taper', '0.025')), float(opt.get('taper', '0.025')), float(opt.get('taper_side', '0.012'))])
thick[hverts] = TMIN + (thick[hverts] - TMIN) * ss(fd, 0.0, TAPER)
for sx in (1, -1):
    er = EAR_ROOT * [sx, 1, 1]; et = er + (EAR_TIP * [sx, 1, 1] - er) * 0.25
    seg = et - er; tt = np.clip(((co[hverts] - er) @ seg) / (seg @ seg), 0, 1); dd = np.linalg.norm(co[hverts] - (er + tt[:, None] * seg), axis=1)
    thick[hverts] = TMIN + (thick[hverts] - TMIN) * ss(dd, float(opt.get('ear_r0', '0.016')), float(opt.get('ear_r1', '0.034')))
eh = edges_of(hf)
for _ in range(6):
    acc = np.zeros(len(co)); deg = np.zeros(len(co))
    np.add.at(acc, eh[:, 0], thick[eh[:, 1]]); np.add.at(acc, eh[:, 1], thick[eh[:, 0]]); np.add.at(deg, eh[:, 0], 1); np.add.at(deg, eh[:, 1], 1)
    m = deg > 0; thick[m] = 0.5 * thick[m] + 0.5 * acc[m] / deg[m]
# the smoothing lifts the edge again: taper once more after it (the hairline itself is thin, as hair is)
thick[hverts] = TMIN + (thick[hverts] - TMIN) * ss(fd, 0.0, TAPER)
# cap mode (coordinator review 2026-11-02: the bob read as a flared bell; MM9's hair is a close cap pulled back behind the ears): the shell
# thins to RIM_T over RIM_W toward its whole boundary, so the lower edge tucks under onto the skull instead of ending in a hard step
if 'rim_w' in opt:
    _e = np.vstack([hf[:, [0, 1]], hf[:, [1, 2]], hf[:, [2, 0]]]); _u, _c = np.unique(np.sort(_e, axis=1), axis=0, return_counts=True)
    _bv = np.unique(_u[_c == 1]); _db = cKDTree(co[_bv]).query(co[hverts])[0]; RIMT = float(opt.get('rim_t', '0.0015'))
    thick[hverts] = RIMT + (thick[hverts] - RIMT) * ss(_db, 0.0, float(opt['rim_w']))
# hair normals: skull normals smoothed (the crumpled pressed ears must not spike the shell)
Nh = N.copy()
for _ in range(8):
    acc = np.zeros_like(Nh); deg = np.zeros(len(co))
    np.add.at(acc, eh[:, 0], Nh[eh[:, 1]]); np.add.at(acc, eh[:, 1], Nh[eh[:, 0]]); np.add.at(deg, eh[:, 0], 1); np.add.at(deg, eh[:, 1], 1)
    m = deg > 0; Nh[m] = 0.5 * Nh[m] + 0.5 * acc[m] / deg[m][:, None]
Nh /= np.maximum(np.linalg.norm(Nh, axis=1, keepdims=True), 1e-12)
REP['hair_thickness_mm'] = dict(p10=round(float(np.percentile(thick[hverts], 10)) * 1000, 1), p50=round(float(np.median(thick[hverts])) * 1000, 1),
                                max=round(float(thick[hverts].max()) * 1000, 1))

# shell vertices (new) + rim to 2 mm inside the skull along the boundary
base = len(co); remap = -np.ones(len(co), int); remap[hverts] = base + np.arange(len(hverts))
shell = co[hverts] + Nh[hverts] * thick[hverts, None]
shell_f = remap[hf]
# boundary edges of the hair patch, oriented as in their face
e_all = np.vstack([hf[:, [0, 1]], hf[:, [1, 2]], hf[:, [2, 0]]]); key = np.sort(e_all, axis=1)
uk, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
bnd = e_all[cnt[inv.ravel()] == 1]
bverts = np.unique(bnd); inner_idx = -np.ones(len(co), int)
inner_idx[bverts] = base + len(hverts) + np.arange(len(bverts))
inner = co[bverts] - N[bverts] * 0.002
rim = []
for a, b in bnd:            # shell face has a->b: the rim takes b->a
    A_, B_ = remap[a], remap[b]; a2, b2 = inner_idx[a], inner_idx[b]
    rim += [[B_, A_, a2], [B_, a2, b2]]
hair_co = np.vstack([shell, inner]); hair_tri = np.vstack([shell_f, np.array(rim)])
# relax the shell surface a little (keeps the volume, removes the skull's small creases)
Pall = np.vstack([co, hair_co]); sel = np.zeros(len(Pall), bool); sel[base:base + len(hverts)] = True
sel[remap[bverts]] = False
Pall = laplace(Pall, hair_tri, sel, int(opt.get('hair_smooth', '6')), 0.4)
hair_co = Pall[base:]
# the hairline follows the skull's triangle edges (a zigzag): relax the shell edge and the rim's inner edge along the boundary loop
nb = {}
for a, b in bnd: nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
bl = np.array(sorted(nb)); bpos = {v: i for i, v in enumerate(bl)}
for which in ('shell', 'inner'):
    ids = np.array([(remap[v] if which == 'shell' else inner_idx[v]) - base for v in bl])
    Pb = hair_co[ids].copy()
    for _ in range(int(opt.get('edge_smooth', '12'))):
        Pn = Pb.copy()
        for i, v in enumerate(bl):
            nn = [bpos[u] for u in nb[v]]
            Pn[i] = 0.5 * Pb[i] + 0.5 * Pb[nn].mean(0)
        Pb = Pn
    hair_co[ids] = Pb
REP['hair_boundary_edges'] = int(len(bnd))
# clearance (cap mode): the relaxation shrinks a thin shell into the skull (the skull's paint then showed through as a dark arc over the
# forehead); every shell vertex is pushed back out along its normal to at least min(its thickness, CLEAR) above its skull vertex
if 'clear' in opt:
    CL = float(opt['clear']); sh_ = hair_co[:len(hverts)]; base_ = co[hverts]; n_ = Nh[hverts]
    off = ((sh_ - base_) * n_).sum(1); need = np.maximum(np.minimum(thick[hverts], CL), float(opt.get('rim_t', '0.0015')))
    push = np.maximum(need - off, 0); hair_co[:len(hverts)] = sh_ + n_ * push[:, None]
    REP['clear_pushed'] = dict(n=int((push > 1e-5).sum()), max_mm=round(float(push.max()) * 1000, 2))


def append(P, T, name):
    global co, tri, comp, names
    off = len(co); co = np.vstack([co, P]); tri = np.vstack([tri, T + off])
    if name not in names: names.append(name)
    comp = np.r_[comp, np.full(len(P), names.index(name))]


# hair_tri indexes base.. (shell, inner) -> local
append(hair_co, hair_tri - base, 'hair')

# ---- 5. elf ears (cupped leaf with a rolled rim), +x then mirrored
NU, NV = 12, 7
eu = EAR_TIP - EAR_ROOT; EL = np.linalg.norm(eu); eu /= EL
en = np.array([1.0, -FWD, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)
ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
uu = np.linspace(0, 1, NU); vv = np.linspace(-1, 1, NV)
V = []
for sgn in (1, -1):
    for u in uu:
        wid = EAR_W * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
        th = 0.0055 * (1 - u) ** 0.7 + 0.0012
        for v in vv:
            cup = 0.006 * (1 - v * v) * np.sin(np.pi * min(u * 1.1, 1)) if sgn > 0 else 0.0
            rimh = 0.002 * np.exp(-((abs(v) - 1) / 0.3) ** 2) * (1 - u) if sgn > 0 else 0.0
            off = sgn * th * np.sqrt(max(1 - v * v, 0.0)) - cup + rimh
            V.append(EAR_ROOT + eu * (u * EL) + ev * (v * wid * 0.5) + en * off)
V = np.array(V); nf = NU * NV
tipp = V[(NU - 1) * NV:nf].mean(0)
T = []
for s in (0, 1):
    for i in range(NU - 1):
        for j in range(NV - 1):
            a = s * nf + i * NV + j; b = a + 1; c = a + NV; d = c + 1
            T += [[a, b, d], [a, d, c]] if s == 0 else [[a, d, b], [a, c, d]]
for i in range(NU - 1):
    for j in (0, NV - 1):
        a, c = i * NV + j, (i + 1) * NV + j; b, d = nf + a, nf + c
        T += [[a, c, d], [a, d, b]] if j == 0 else [[a, d, c], [a, b, d]]
T = np.array(T)
# merge the tip rows into one vertex (both sides)
tipi = nf + 0  # placeholder; rebuild arrays with a single tip vertex
mapv = np.arange(len(V)); tiprow = np.r_[np.arange((NU - 1) * NV, nf), nf + np.arange((NU - 1) * NV, nf)]
mapv[tiprow] = tiprow[0]; V[tiprow[0]] = tipp
T = mapv[T]; T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
# side strips also collapse at the root? root rows stay open inside the skull (hidden), as in F8/M7d
usedv = np.unique(T); m2 = -np.ones(len(V), int); m2[usedv] = np.arange(len(usedv)); V = V[usedv]; T = m2[T]
# orient outward: signed volume of the leaf about its centroid
cen = V.mean(0); vol = np.einsum('ij,ij->i', V[T[:, 0]] - cen, np.cross(V[T[:, 1]] - cen, V[T[:, 2]] - cen)).sum()
flipped = vol < 0
if flipped: T = T[:, ::-1]
REP['ear'] = dict(len_m=round(float(EL), 4), faces_per_ear=int(len(T)), flipped_to_outward=bool(flipped), root=EAR_ROOT.tolist(), tip=EAR_TIP.tolist())
VL = V * [-1, 1, 1]; TL = T[:, ::-1]
append(np.vstack([V, VL]), np.vstack([T, TL + len(V)]), 'ears')

# ---- 6. braid: tube along MM9's braid line, kept off our back
CP = np.array([f3(p) for p in opt.get('braid', '0,0.062,0.668;0,0.090,0.615;0,0.112,0.565;0,0.130,0.510;0,0.144,0.462;0,0.152,0.430').split(';')])
from scipy.interpolate import CubicSpline
sp = CubicSpline(np.r_[0, np.cumsum(np.linalg.norm(np.diff(CP, axis=0), axis=1))], CP)
L = float(sp.x[-1]); NR, NS = int(opt.get('braid_rings', '40')), 10
s_ = np.linspace(0, L, NR); cen = sp(s_); tan = sp(s_, 1); tan /= np.linalg.norm(tan, axis=1, keepdims=True)
side = np.array([1.0, 0, 0])
LOBE = float(opt.get('lobe', '0.026'))
R0 = np.interp(s_ / L, [0, 0.12, 0.8, 0.9, 0.93, 1.0], [float(x) for x in opt.get('braid_r', '0.025,0.021,0.013,0.008,0.010,0.002').split(',')])
ring = []
for k in range(NR):
    t_ = tan[k]; xa = side - t_ * (side @ t_); xa /= np.linalg.norm(xa); ya = np.cross(t_, xa)
    ph = s_[k] / LOBE * np.pi
    body = s_[k] / L < 0.88
    r = R0[k] * ((0.80 + 0.32 * abs(np.sin(ph))) if body else 1.0)
    shift = 0.0035 * np.sin(ph * 0.5 * 2) * (R0[k] / 0.017) if body else 0.0
    for j in range(NS):
        a = 2 * np.pi * j / NS
        ring.append(cen[k] + xa * (shift + r * np.cos(a)) + ya * r * 0.82 * np.sin(a))
BP = np.array(ring); BT = []
for k in range(NR - 1):
    for j in range(NS):
        a = k * NS + j; b = k * NS + (j + 1) % NS; c = a + NS; d = b + NS
        BT += [[a, c, d], [a, d, b]]
top = len(BP); BP = np.vstack([BP, cen[0] - tan[0] * 0.004]); bot = len(BP); BP = np.vstack([BP, cen[-1] + tan[-1] * 0.004])
for j in range(NS):
    BT += [[top, j, (j + 1) % NS]]; BT += [[bot, (NR - 1) * NS + (j + 1) % NS, (NR - 1) * NS + j]]
BT = np.array(BT)
cb = BP.mean(0); vol = np.einsum('ij,ij->i', BP[BT[:, 0]] - cb, np.cross(BP[BT[:, 1]] - cb, BP[BT[:, 2]] - cb)).sum()
if vol < 0: BT = BT[:, ::-1]
# clearance to the dress back (braid surface to the nearest dress vertex)
dv = co[comp == names.index('dress')]; dmin = cKDTree(dv).query(BP)[0].min()
REP['braid'] = dict(length_m=round(L, 3), faces=int(len(BT)), min_gap_to_dress_mm=round(float(dmin) * 1000, 1))
append(BP, BT, 'braid')

REP['parts'] = {n: int((comp[tri[:, 0]] == i).sum()) for i, n in enumerate(names)}
REP['triangles'] = int(len(tri))
np.savez(OUT, co=co, tri=tri, comp=comp, names=np.array(names), **extra)
print('F6GEOM', json.dumps(REP))
