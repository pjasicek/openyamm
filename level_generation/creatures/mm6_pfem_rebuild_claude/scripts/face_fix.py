#!/usr/bin/env python3
"""Follow-up 4 (2026-11-12): face defects of the installed runtime GLB, LOD0 head primitive only (body, clips, skin, the body's
images and the face paint itself are kept). Usage: face_fix.py <installed glb> <out glb> [--report work/followup4/face_fix.json]
The LODs are rebuilt after this by scripts/followup4_build.sh.

1. Holes. `prune_hidden.py` deleted v3 skin it judged hidden under the hair (rays hitting the hair's inside counted as cover, but the
   single-sided shell is culled from there): a quad in front of the right ear showed the background, the nostrils were open and the
   nape, seen from behind under the bob, looked through the head. Candidates: the pruned faces of `work/asm.npz` (and fan caps of
   the master's own open loops under 12 mm; the ear openings stay open: a flat fan sticks out of the curved temple). A software
   z-buffer (`soft_render.py`) from 156 directions keeps a candidate where it covers what a hole shows today (the background, or a
   surface 8 mm or more behind it), plus its one-ring; one that would mostly land within 8 mm over drawn skin or hair stays pruned,
   and so does the hairline notch above the forehead (y > 0.73: the decimated LOD1 fringe showed it as a skin wedge).
2. Paint for the new faces: small planar charts packed into free atlas space; each texel takes the colour and ORM of the nearest
   existing face-skin texel in 3D (nostril interiors x0.55, nape plates x0.85), flat normal map, 4 px gutters.
3. Midline needles and small mirror-seam charts (forehead, nose, chin; the symmetry snap): faces under 0.6 mm wide, or in charts under
   2 cm2, within 4-5 mm of the midline, take the UVs of the big face chart their corners belong to (new vertex entries, so their
   neighbours keep theirs; not the lips). They were one-texel strips in hair-brown texels or collapsed on texel (0, 0): the dark
   forehead "crack", the speck on the columella and the philtrum.
4. Normals: area-weighted per position over the face skin (positions shared with the body keep the installed normal, or take the
   body's), cancelling folds take their neighbours', then a bilateral smoothing (neighbour weight falls off with the angle between
   normals: sigma 32 deg under the chin and jaw, 20 deg elsewhere) on the jaw, chin, lower cheeks, face sides and nose-wing creases.
   Eyes, brows, nose bridge and lips keep theirs. Hair, braid and band keep their installed normals.
5. Hair shell front edge (temple to jaw, below the circlet): each boundary vertex moves onto the nearest face skin +0.8 mm (at most
   HAIR_MAX), three Laplacian passes along the edge re-seated on the skin, the next two rings at 50 % / 20 %, the inward back-face
   copies with their front vertices.
"""
import io, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from glbio import Glb  # noqa: E402
import soft_render as sr  # noqa: E402

IN, OUT = sys.argv[1], sys.argv[2]
REPORT = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else str(HERE / 'work/followup4/face_fix.json')
HAIR_MAX = 0.004                                     # metres: the edge tidy never moves a vertex further
rep = {}


def b2g(p):
    """Blender (assemble npz) -> runtime glTF frame of the installed GLB (mirrored to true handedness)"""
    return np.c_[-p[:, 0], p[:, 2], -p[:, 1]]


def weld(co, tol=1e-6):
    q = np.round(co / tol).astype(np.int64); _, inv = np.unique(q, axis=0, return_inverse=True); return inv.ravel()


def loops_of(edges):
    adj = defaultdict(list)
    for a, b in edges: adj[a].append(b)
    out, seen = [], set()
    for s in list(adj):
        if s in seen: continue
        L = [s]; seen.add(s); cur = s
        while True:
            nx = [x for x in adj[cur] if x not in seen]
            if not nx: break
            cur = nx[0]; seen.add(cur); L.append(cur)
        out.append(L)
    return out


g = Glb(IN)
H = g.prim(0, 1); B = g.prim(0, 0)
co, nr, uv, J, W, tri = H['POSITION'].astype(float), H['NORMAL'].astype(float), H['TEXCOORD_0'].astype(float), H['JOINTS_0'], H['WEIGHTS_0'], H['idx']
nv0, nt0 = len(co), len(tri)
D = np.load(HERE / 'work/uv_tex.npz'); NAMES = [str(x) for x in D['names']]
Pd = b2g(D['co']); Ud = D['uv'] * [1, -1] + [0, 1]
_, nn = cKDTree(np.c_[Pd, Ud * 0.05]).query(np.c_[co, uv * 0.05]); vcomp = D['comp'][nn]
fcomp = vcomp[tri[:, 0]]; HEAD, HAIR = NAMES.index('head'), NAMES.index('hair')
img_idx = {k: g.j['textures'][v['index']]['source'] for k, v in (('base', g.j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']),
                                                                ('orm', g.j['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']),
                                                                ('normal', g.j['materials'][0]['normalTexture']))}


def image(i):
    bv = g.j['bufferViews'][g.j['images'][i]['bufferView']]; o = bv.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(bytes(g.bin[o:o + bv['byteLength']]))).convert('RGB')).astype(np.float32)


TEX = {k: image(i) for k, i in img_idx.items()}; S = TEX['base'].shape[0]

# ---------------------------------------------------------------- 3. thin faces: UVs from the big chart next to them
# The symmetry snap left needle faces along the midline (forehead, nose, chin; under 0.6 mm wide). Some are UV-collapsed onto
# texel (0, 0), others are their own one-texel-wide charts sitting in hair-brown texels: either way they draw a dark line (the
# forehead "crack"). Each corner takes the UV its position has in the largest chart touching that position.
Ut = uv[tri]; span = (Ut.max(1) - Ut.min(1)).max(1)
inv = weld(co); fa3 = np.linalg.norm(np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]), axis=1)
emax = np.max([np.linalg.norm(co[tri[:, i]] - co[tri[:, (i + 1) % 3]], axis=1) for i in range(3)], 0)
height = fa3 / np.maximum(emax, 1e-12)
cx_ = np.abs(co[tri][:, :, 0]).max(1)
thin = (fcomp == HEAD) & ((height < 0.0006) | (span < 1e-4)) & (cx_ < 0.004)   # midline needles only (eyes and lips keep theirs)
uvk = np.c_[inv, np.round(uv / 1e-5)].astype(np.int64); _, cid0 = np.unique(uvk, axis=0, return_inverse=True); cid0 = cid0.ravel()
par0 = np.arange(cid0.max() + 1)


def fnd0(x):
    while par0[x] != x: par0[x] = par0[par0[x]]; x = par0[x]
    return x


for f in np.nonzero((fcomp == HEAD) & ~thin)[0]:
    r0 = fnd0(cid0[tri[f, 0]]); par0[fnd0(cid0[tri[f, 1]])] = r0; par0[fnd0(cid0[tri[f, 2]])] = r0
chart_area = defaultdict(float)
for f in np.nonzero((fcomp == HEAD) & ~thin)[0]: chart_area[fnd0(cid0[tri[f, 0]])] += fa3[f] / 2
pos_uv = defaultdict(dict)                              # welded position -> chart -> uv
for f in np.nonzero((fcomp == HEAD) & ~thin)[0]:
    ch = fnd0(cid0[tri[f, 0]])
    for v in tri[f]: pos_uv[inv[v]][ch] = uv[v].copy()
snapped = 0; snapped_faces = 0; dup = {}; tri = tri.copy()
# also the midline faces of small charts (< 2 cm2, the mirror seam's leftovers between the brows): only when the big chart has
# all three corners (no collapse for a face of real width)
fchart0 = np.array([fnd0(cid0[t_[0]]) for t_ in tri])
cy_ = co[tri][:, :, 1].mean(1)
mid_small = (fcomp == HEAD) & ~thin & (cx_ < 0.005) & np.array([chart_area.get(c, 0.0) < 2e-4 for c in fchart0]) \
    & ~((cy_ > 0.56) & (cy_ < 0.598))                      # not the lips (their own painted charts)
for f in np.nonzero(thin | mid_small)[0]:
    charts_ = defaultdict(int)
    for v in tri[f]:
        for ch in pos_uv[inv[v]]:
            if chart_area[ch] >= 5e-4: charts_[ch] += 1  # only into a real chart (5 cm2+), never another sliver chart
    if not charts_: continue
    ch = max(charts_, key=lambda c: (charts_[c], chart_area[c]))
    have = [v for v in tri[f] if ch in pos_uv[inv[v]]]
    if mid_small[f] and len(have) < 3: continue
    new_uv_ = {}
    for v in tri[f]:
        src = v if v in have else min(have, key=lambda h: np.linalg.norm(co[h] - co[v]))
        new_uv_[v] = pos_uv[inv[src]][ch]
    U3 = np.array([new_uv_[v] for v in tri[f]])
    if (U3.max(0) - U3.min(0)).max() > 0.1: continue     # stays local (a 4 cm needle at 2,321 px/m)
    snapped_faces += 1
    for k_ in range(3):
        v = tri[f, k_]
        if np.abs(uv[v] - new_uv_[v]).max() <= 1e-6: continue
        key_ = (int(v), tuple(np.round(new_uv_[v] / 1e-6).astype(int)))
        if key_ not in dup:                             # a new vertex entry: the old one stays with its other faces
            dup[key_] = len(co); co = np.vstack([co, co[v]]); nr = np.vstack([nr, nr[v]]); uv = np.vstack([uv, new_uv_[v]])
            J = np.vstack([J, J[v]]); W = np.vstack([W, W[v]]); vcomp = np.r_[vcomp, vcomp[v]]; snapped += 1
        tri[f, k_] = dup[key_]
rep['thin_faces_snapped'] = snapped_faces
rep['thin_faces'] = int(thin.sum()); rep['midline_small_chart_faces'] = int(mid_small.sum()); rep['thin_vertex_entries_added'] = snapped
nv0 = len(co)                                           # vertices before the hole fill (installed + thin-face copies)
NR0 = nr.copy()
span = (uv[tri].max(1) - uv[tri].min(1)).max(1)

# ---------------------------------------------------------------- 6. hair shell front edge tucked onto the skin
# The front edge of the hair shell hooks inward and stops 3-8 mm off the face (temple to jaw); from a three-quarter view the hook's
# inner side and the gap behind it read as angular flaps. Each front-edge vertex in the zone moves onto the nearest face skin
# (+0.8 mm along its normal), at most HAIR_MAX; the next two rings follow at 50 % and 20 %, the inward back-face copies with them.
fn_all = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
outw = ((co[tri].mean(1) - [0, 0.63, 0]) * fn_all).sum(1) > 0
hf = np.nonzero((fcomp == HAIR) & outw)[0]
winv = weld(co); tw = winv[tri[hf]]
e = np.stack([tw[:, [0, 1]], tw[:, [1, 2]], tw[:, [2, 0]]], 1).reshape(-1, 2)
es = np.sort(e, 1); ue, cnt = np.unique(es, axis=0, return_counts=True)
bw = np.unique(ue[cnt == 1])
Pw = np.zeros((winv.max() + 1, 3)); Pw[winv] = co
zone = (Pw[bw, 2] > -0.035) & (Pw[bw, 1] > 0.57) & (Pw[bw, 1] < 0.685) & (np.abs(Pw[bw, 0]) > 0.03)
bw = bw[zone]
skin_pos = set(winv[tri[fcomp == HEAD]].ravel()); bw = np.array([w_ for w_ in bw if w_ not in skin_pos], int)
skf = np.nonzero((fcomp == HEAD) & (fa3 > 0))[0]
rng = np.random.default_rng(0); nsm = 200000
pa_ = fa3[skf] / fa3[skf].sum(); kk = rng.choice(len(skf), nsm, p=pa_)
r1, r2 = rng.random(nsm), rng.random(nsm); sq = np.sqrt(r1); bc = np.c_[1 - sq, sq * (1 - r2), sq * r2]
spts = (co[tri[skf[kk]]] * bc[:, :, None]).sum(1); snrm = fn_all[skf[kk]] / np.maximum(np.linalg.norm(fn_all[skf[kk]], axis=1, keepdims=True), 1e-12)
kd_sk = cKDTree(spts)
dist_, ii_ = kd_sk.query(Pw[bw])
disp_w = {}
for w_, dd, i_ in zip(bw, dist_, ii_):
    if dd > 0.012: continue
    tgt = spts[i_] + snrm[i_] * 0.0008; d_ = tgt - Pw[w_]; ln_ = np.linalg.norm(d_)
    disp_w[w_] = d_ * min(1.0, HAIR_MAX / max(ln_, 1e-12))
hadj = defaultdict(set)
for f in hf:
    for a_ in winv[tri[f]]:
        for b_ in winv[tri[f]]:
            if a_ != b_: hadj[a_].add(b_)
ringd = [dict(disp_w)]
for frac in (0.5, 0.2):
    nxt = {}
    for w_ in ringd[-1]:
        for nb in hadj[w_]:
            if any(nb in r for r in ringd): continue
            nxt.setdefault(nb, []).append(ringd[-1][w_])
    ringd.append({k: np.mean(v, 0) * frac / (0.5 if frac == 0.2 else 1.0) for k, v in nxt.items()})
allw = {}
for r in ringd: allw.update(r)
moved = np.zeros(len(co), bool)
orig_co = co.copy()
for v in np.unique(tri[hf]):
    if winv[v] in allw: co[v] = co[v] + allw[winv[v]]; moved[v] = True
# the tucked edge itself: three Laplacian passes along the boundary (removes the zigzag), each re-seated 0.8 mm off the skin
bset_e = {tuple(x) for x in ue[cnt == 1]}; bnb = defaultdict(list)
for a_, b_ in bset_e:
    if a_ in disp_w and b_ in disp_w: bnb[a_].append(b_); bnb[b_].append(a_)
Pw = np.zeros((winv.max() + 1, 3)); Pw[winv] = co
for _ in range(3):
    Q = {w_: Pw[w_] + 0.5 * (np.mean([Pw[x] for x in bnb[w_]], 0) - Pw[w_]) for w_ in disp_w if len(bnb[w_]) == 2}
    if not Q: break
    ks = np.array(list(Q)); qp = np.array([Q[k] for k in ks]); _, ii2 = kd_sk.query(qp)
    qp = spts[ii2] + snrm[ii2] * 0.0008
    for k, p_ in zip(ks, qp): Pw[k] = p_
for v in np.unique(tri[hf]):
    if winv[v] in disp_w:
        d_ = Pw[winv[v]] - orig_co[v]; ln_ = np.linalg.norm(d_); co[v] = orig_co[v] + d_ * min(1.0, HAIR_MAX / max(ln_, 1e-12))
backs = np.unique(tri[(fcomp == HAIR) & ~outw]); fronts = np.unique(tri[hf])
kd_f = cKDTree(np.c_[orig_co[fronts], uv[fronts] * 0.02])
dd_, ii = kd_f.query(np.c_[orig_co[backs], uv[backs] * 0.02])
for b_, i_, dist2 in zip(backs, ii, dd_):
    fv = fronts[i_]
    if moved[fv] and dist2 < 0.004 and not moved[b_]: co[b_] = co[b_] + (co[fv] - orig_co[fv]); moved[b_] = True
rep['hair_edge_vertices_tucked'] = len(disp_w); rep['hair_vertices_moved'] = int(moved.sum())
rep['hair_max_move_mm'] = float(np.linalg.norm(co - orig_co, axis=1).max() * 1000)

# ---------------------------------------------------------------- 1. hole candidates
A = np.load(HERE / 'work/asm.npz'); A2 = np.load(HERE / 'work/asm2.npz'); an = [str(x) for x in A['names']]
fa = A['comp'][A['tri'][:, 0]] == an.index('head'); Ta = A['tri'][fa]; Pa = b2g(A['co'])
fb = A2['comp'][A2['tri'][:, 0]] == an.index('head'); cB = b2g(A2['co'])[A2['tri'][fb]].mean(1)
d, _ = cKDTree(cB).query(Pa[Ta].mean(1)); pruned = Ta[d > 1e-6][:, ::-1]           # mirrored frame: reverse the winding
cand = [Pa[pruned]]; kind = ['pruned'] * len(pruned)
# open loops of the master's head (with the pruned faces back): caps, not the neck
full = Ta[:, ::-1]; pinv = weld(Pa); tw = pinv[full]
e = np.stack([tw[:, [0, 1]], tw[:, [1, 2]], tw[:, [2, 0]]], 1).reshape(-1, 2)
es = np.sort(e, 1); ue, cnt = np.unique(es, axis=0, return_counts=True); bset = {tuple(x) for x in ue[cnt == 1]}
bed = [tuple(x) for x in e if tuple(sorted(x)) in bset]
Pw = np.zeros((pinv.max() + 1, 3)); Pw[pinv] = Pa
caps = []
for L in loops_of([(b, a) for a, b in bed]):                                          # reversed: caps face outwards
    c = Pw[L].mean(0)
    if c[1] < 0.57 and len(L) > 8: continue                                             # the neck opening
    if (Pw[L].max(0) - Pw[L].min(0)).max() > 0.012: continue                           # ear openings: a flat fan sticks out of the
                                                                                        # curved temple; they stay open under the hair
    for k in range(len(L)):
        caps.append([Pw[L[k]], Pw[L[(k + 1) % len(L)]], c])
rep['candidate_pruned'] = len(pruned); rep['candidate_caps'] = len(caps)
if caps: cand.append(np.array(caps)); kind += ['cap'] * len(caps)
CT = np.concatenate(cand); kind = np.array(kind)
# orientation check: outward from the head centre for skull faces (the nostril/mouth interiors are judged by the render)
nC = np.cross(CT[:, 1] - CT[:, 0], CT[:, 2] - CT[:, 0])

# ---------------------------------------------------------------- visibility selection (software z-buffer, bind pose)
prims = sr.load(g); prims[1] = (co, nr, uv, tri, prims[1][4])
ctex = np.full((4, 4, 3), 255, np.float32)
cprim = (CT.reshape(-1, 3), np.repeat(nC / np.maximum(np.linalg.norm(nC, axis=1, keepdims=True), 1e-12), 3, 0), np.zeros((len(CT) * 3, 2)),
         np.arange(len(CT) * 3).reshape(-1, 3), ctex)
allp = prims + [cprim]
fill = np.zeros(len(CT), int); over = np.zeros(len(CT), int)
VCACHE = HERE / 'work/followup4/visibility_cache.npz'
views = [(az, el) for el in (-55, -40, -25, -10, 5, 20, 35, 50) for az in range(0, 360, 20)]
views += [(az, el) for el in (-70, 70) for az in range(0, 360, 60)]
if VCACHE.exists() and np.load(VCACHE)['CT'].shape == CT.shape and np.allclose(np.load(VCACHE)['CT'], CT) and 'fill' in np.load(VCACHE) \
        and np.load(VCACHE)['co'].shape == co.shape and np.allclose(np.load(VCACHE)['co'], co):
    fill, over = np.load(VCACHE)['fill'], np.load(VCACHE)['over']
else:
    for az, el in views:
        _, ID0, Z0 = sr.render(prims, az, el, cen=(0.0, 0.63, 0.0), radius=0.13, size=520, shade=False, depth=True)
        _, ID, Z1 = sr.render(allp, az, el, cen=(0.0, 0.63, 0.0), radius=0.13, size=520, shade=False, depth=True)
        m = ID[..., 0] == len(prims); hole_ = (ID0[..., 0] < 0) | (Z0 - Z1 > 0.008)   # background, or a surface 8 mm+ behind
        if m.any():
            np.add.at(fill, ID[..., 1][m & hole_], 1); np.add.at(over, ID[..., 1][m & ~hole_], 1)
    np.savez(VCACHE, CT=CT, fill=fill, over=over, co=co)
# a candidate is needed where it covers what shows through a hole today: the background, or a surface 8 mm or more behind it
# (the far side of the head seen through the cheek). One that would mostly land within 8 mm over skin or hair drawn today
# duplicates the installed surface (the nape plates over the body's neck) and stays pruned
vis = (fill >= 3) & (over <= np.maximum(20, fill)) & (CT.mean(1)[:, 1] < 0.73)
# (not the hairline notch above the forehead: its few pixels sit under the fringe and the circlet, while the decimated LOD1
# fringe would show the restored skin as a wedge)
rep['candidates_overlapping_rejected'] = int(((fill >= 3) & ~vis).sum())
# one-ring among the candidates (shared positions)
ck = weld(CT.reshape(-1, 3)).reshape(-1, 3); vpos = set(ck[vis].ravel())
ring = np.array([bool(set(r) & vpos) for r in ck])
keep = (vis | ring) & (CT.mean(1)[:, 1] < 0.73)
rep['candidates_visible'] = int(vis.sum()); rep['candidates_kept'] = int(keep.sum())
rep['kept_by_kind'] = {k: int((keep & (kind == k)).sum()) for k in ('pruned', 'cap')}
NT = CT[keep]; nkind = kind[keep]
print('CANDIDATES', len(CT), 'visible', int(vis.sum()), 'kept', int(keep.sum()), rep['kept_by_kind'])

# ---------------------------------------------------------------- 2. charts for the new faces
nk = weld(NT.reshape(-1, 3)).reshape(-1, 3)
par = np.arange(nk.max() + 1)


def fnd(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x


for t_ in nk: r0 = fnd(t_[0]); par[fnd(t_[1])] = r0; par[fnd(t_[2])] = r0
groups = defaultdict(list)
for f, t_ in enumerate(nk): groups[fnd(t_[0])].append(f)
fn = np.cross(NT[:, 1] - NT[:, 0], NT[:, 2] - NT[:, 0]); fa_ = np.linalg.norm(fn, axis=1); fnu = fn / np.maximum(fa_[:, None], 1e-12)
charts = []
for fl_ in groups.values():                     # split each group into charts within a 60 deg normal cone (greedy region growing)
    left = set(fl_)
    adj = defaultdict(set)
    for f in fl_:
        for v in nk[f]: adj[v].add(f)
    while left:
        s = max(left, key=lambda f: fa_[f]); ch = [s]; left.discard(s); axis = fnu[s].copy(); frontier = [s]
        while frontier:
            f = frontier.pop()
            for v in nk[f]:
                for h in adj[v]:
                    if h in left and fnu[h] @ (axis / np.linalg.norm(axis)) > 0.5:
                        left.discard(h); ch.append(h); frontier.append(h); axis += fnu[h] * fa_[h]
        charts.append((ch, axis / np.linalg.norm(axis)))
# density: 2,000 px/m for the small faces on the face side (face skin 2,321); 900 px/m for the rest, 500 px/m for the 6-11 cm skull
# plates (under the hair: only a sliver of them shows, through a gap; free atlas space allows no more)
cen_n = NT.mean(1); lmax_n = np.max([np.linalg.norm(NT[:, i] - NT[:, (i + 1) % 3], axis=1) for i in range(3)], 0)
dens_f = np.where((cen_n[:, 2] > -0.01) & (lmax_n < 0.03), 2000.0, np.where(lmax_n < 0.06, 900.0, 500.0))
MAXPX = 44


def frame(ax):
    t1 = np.cross(ax, [0, 1.0, 0]) if abs(ax[1]) < 0.9 else np.cross(ax, [1.0, 0, 0]); t1 /= np.linalg.norm(t1); return t1, np.cross(ax, t1)


def split(ch, ax):
    """planar charts no larger than MAXPX: split at the median along the longer side until they fit"""
    t1, t2 = frame(ax); dn = dens_f[ch].max()
    P = NT[ch]; q = np.stack([P @ t1, P @ t2], -1) * dn
    ext = q.reshape(-1, 2).max(0) - q.reshape(-1, 2).min(0)
    if ext.max() <= MAXPX or len(ch) == 1: return [(ch, ax, dn)]
    k = int(np.argmax(ext)); c = q.mean(1)[:, k]; med = np.median(c)
    a_ = [f for f, x in zip(ch, c) if x <= med]; b_ = [f for f, x in zip(ch, c) if x > med]
    if not a_ or not b_: a_, b_ = ch[:len(ch) // 2], ch[len(ch) // 2:]
    return split(a_, ax) + split(b_, ax)


charts = [x for ch, ax in charts for x in split(ch, ax)]
occ = Image.new('L', (S, S)); dro = ImageDraw.Draw(occ)
for f in range(nt0):
    if span[f] >= 1e-4: dro.polygon([tuple(uv[v] * S) for v in tri[f]], fill=255, outline=255)
occ0 = np.asarray(occ) > 0                       # texels the existing charts use
occ_exist = ndimage.binary_dilation(occ0, iterations=3); occ = occ_exist.copy()
new_uv = np.zeros((len(NT), 3, 2)); placed = 0
for ch, ax, dn in sorted(charts, key=lambda c: -sum(fa_[f] for f in c[0]) * c[2] ** 2):
    t1, t2 = frame(ax)
    P = NT[ch].reshape(-1, 3); q = np.c_[P @ t1, P @ t2] * dn; q -= q.min(0); q += 4
    w, h = (np.ceil(q.max(0)) + 4).astype(int)
    mk = Image.new('L', (w, h)); dm = ImageDraw.Draw(mk)
    for k in range(len(ch)): dm.polygon([tuple(x) for x in q[3 * k:3 * k + 3]], fill=255, outline=255)
    mk = ndimage.binary_dilation(np.asarray(mk) > 0, iterations=3)
    best = None
    for y in range(0, S - h, 2):
        for x in range(0, S - w, 2):
            if not occ[y:y + h, x:x + w][mk].any(): best = (x, y); break
        if best: break
    if best is None: raise SystemExit(f'no atlas space for a chart of {w}x{h} px ({len(ch)} faces, {dn} px/m), {placed} placed')
    x, y = best; occ[y:y + h, x:x + w] |= mk; placed += 1
    new_uv[ch] = ((q + [x, y]) / S).reshape(-1, 3, 2)
rep['new_charts'] = placed
print('CHARTS', placed)

# ---------------------------------------------------------------- paint the new texels from the nearest existing face skin
def posmap(P3, UV, faces):
    Pm = np.full((S, S, 3), np.nan); Fm = -np.ones((S, S), int)
    for f in faces:
        t_ = UV[f] * S; x0, y0 = np.floor(t_.min(0)).astype(int); x1, y1 = np.ceil(t_.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, S - 1), min(y1, S - 1)
        if x1 < x0 or y1 < y0: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b_, c_ = t_; v0, v1 = b_ - a, c_ - a; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12: continue
        px_, py_ = xs - a[0], ys - a[1]
        l1 = (px_ * v1[1] - v1[0] * py_) / den; l2 = (v0[0] * py_ - px_ * v0[1]) / den; l0 = 1 - l1 - l2
        ins = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
        if not ins.any(): continue
        p = P3[f]; qq = l0[ins, None] * p[0] + l1[ins, None] * p[1] + l2[ins, None] * p[2]
        yy, xx = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int); Pm[yy, xx] = qq; Fm[yy, xx] = f
    return Pm, Fm


skin_f = np.nonzero((fcomp == HEAD) & (span >= 1e-4))[0]
PMs, FMs = posmap(co[tri], uv[tri], skin_f)
ok = FMs >= 0; ys_, xs_ = np.nonzero(ok); kd = cKDTree(PMs[ok])
PMn, FMn = posmap(NT, new_uv, range(len(NT)))
newpx = FMn >= 0
_, idx = kd.query(PMn[newpx])
for key in ('base', 'orm'):
    TEX[key][newpx] = TEX[key][ys_[idx], xs_[idx]]
# nostril interiors: the pruned faces inside the nose wings (behind the nostril opening) are shadowed
nos = (np.abs(NT.mean(1)[:, 0]) < 0.02) & (NT.mean(1)[:, 1] > 0.6) & (NT.mean(1)[:, 1] < 0.62) & (NT.mean(1)[:, 2] > 0.06)
dark = newpx.copy(); dark[newpx] = nos[FMn[newpx]]
TEX['base'][dark] *= 0.55
# behind the ear (the nape plates, seen only through the gap under the hair from behind): the nearest skin, a little shaded
# (the hair's own colour drew a black block there in the viewer: these faces point back and down, away from the lights)
backf = NT.mean(1)[:, 2] < -0.02
bpx = newpx.copy(); bpx[newpx] = backf[FMn[newpx]]
TEX['base'][bpx] *= 0.85
rep['nape_faces'] = int(backf.sum())
TEX['normal'][newpx] = [128, 128, 255]
# gutters around the new charts: dilate their colours outward 4 px (into texels no chart uses)
for key in ('base', 'orm', 'normal'):
    T_ = TEX[key]; filled = newpx.copy()
    for _ in range(4):
        ring_ = ndimage.binary_dilation(filled) & ~filled & ~occ_exist
        if not ring_.any(): break
        acc = np.zeros_like(T_); n_ = np.zeros(T_.shape[:2])
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            sh = np.roll(filled, (dy, dx), (0, 1)); val = np.roll(T_, (dy, dx), (0, 1))
            acc += val * sh[..., None]; n_ += sh
        upd = ring_ & (n_ > 0)
        T_[upd] = acc[upd] / n_[upd, None]; filled |= upd
rep['nostril_faces'] = int(nos.sum()); rep['new_texels'] = int(newpx.sum())


# ---------------------------------------------------------------- new vertices and faces
skin_v = np.unique(tri[fcomp == HEAD]); kd_sv = cKDTree(co[skin_v])
newP = NT.reshape(-1, 3); newU = new_uv.reshape(-1, 2)
key = np.c_[np.round(newP / 1e-6), np.round(newU / 1e-6)].astype(np.int64)
_, first, vinv = np.unique(key, axis=0, return_index=True, return_inverse=True); vinv = vinv.ravel()
addP, addU = newP[first], newU[first]
_, nnv = kd_sv.query(addP); addJ, addW = J[skin_v[nnv]], W[skin_v[nnv]]
co = np.vstack([co, addP]); uv = np.vstack([uv, addU]); J = np.vstack([J, addJ]); W = np.vstack([W, addW])
nr = np.vstack([nr, np.zeros_like(addP)])
tri = np.vstack([tri, vinv.reshape(-1, 3) + nv0]); fcomp = np.r_[fcomp, np.full(len(NT), HEAD)]
vcomp = np.r_[vcomp, np.full(len(addP), HEAD)]
rep['added_vertices'] = int(len(addP)); rep['added_faces'] = int(len(NT))

# ---------------------------------------------------------------- 5. normals
body_pos = {tuple(x) for x in np.round(B['POSITION'].astype(float) / 1e-6).astype(np.int64)}
winv = weld(co); nw = winv.max() + 1
fn_all = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
skinf = fcomp == HEAD
Ns = np.zeros((nw, 3)); Sa = np.zeros(nw)
for c_ in range(3):                                     # area-weighted, as build_glb.py (reproduces the installed normals)
    np.add.at(Ns, winv[tri[skinf, c_]], fn_all[skinf]); np.add.at(Sa, winv[tri[skinf, c_]], np.linalg.norm(fn_all[skinf], axis=1))
skin_w = np.zeros(nw, bool); skin_w[winv[tri[skinf]].ravel()] = True
frozen = np.zeros(nw, bool)
for v in range(len(co)):
    if tuple(np.round(co[v] / 1e-6).astype(np.int64)) in body_pos: frozen[winv[v]] = True
N0 = np.zeros((nw, 3)); N0[winv[:nv0]] = NR0
# a restored face can reach a neck position the head never had (the nape plates): it takes the body's normal there
bkey = {tuple(k): i for i, k in enumerate(np.round(B['POSITION'].astype(float) / 1e-6).astype(np.int64))}
for v in range(nv0, len(co)):
    if frozen[winv[v]] and np.linalg.norm(N0[winv[v]]) < 1e-6:
        N0[winv[v]] = B['NORMAL'][bkey[tuple(np.round(co[v] / 1e-6).astype(np.int64))]]
Nn = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-12)
Nn[frozen] = N0[frozen]
te = winv[tri[skinf]]; ed = np.vstack([te[:, [0, 1]], te[:, [1, 2]], te[:, [2, 0]]]); ed = np.vstack([ed, ed[:, ::-1]])
folded = skin_w & (np.linalg.norm(Ns, axis=1) < 0.35 * Sa) & ~frozen   # cancelling folds (nostril rims): neighbours' normals
for _ in range(4):
    acc = np.zeros((nw, 3)); np.add.at(acc, ed[:, 0], Nn[ed[:, 1]] * ~folded[ed[:, 1], None])
    okf = folded & (np.linalg.norm(acc, axis=1) > 1e-9); Nn[okf] = acc[okf] / np.linalg.norm(acc[okf], axis=1, keepdims=True)
rep['folded_positions'] = int(folded.sum())
# bilateral smoothing on the jaw, chin, lower cheeks, the face sides and the nose wings' creases (not the eyes, brows, nose
# bridge or lips): a neighbour's pull falls
# off with the angle between the normals (sigma 20 deg), so the jaw's low-angle facet steps blend and real edges stay
Pw2 = np.zeros((nw, 3)); Pw2[winv] = co
alar = (np.abs(Pw2[:, 0]) > 0.006) & (np.abs(Pw2[:, 0]) < 0.03) & (Pw2[:, 1] > 0.598) & (Pw2[:, 1] < 0.622) & (Pw2[:, 2] > 0.05)
reg = skin_w & ~frozen & ((Pw2[:, 1] < 0.597) | (np.abs(Pw2[:, 0]) > 0.045) | alar) \
    & ~((np.abs(Pw2[:, 0]) < 0.032) & (Pw2[:, 1] > 0.562) & (Pw2[:, 1] < 0.597) & (Pw2[:, 2] > 0.045))
SIG = np.where(Pw2[:, 1] < 0.565, np.radians(32.0), np.radians(20.0))   # chin and jaw underside: its facets step by 20-30 deg
for _ in range(4):
    cosd = (Nn[ed[:, 0]] * Nn[ed[:, 1]]).sum(1); w_ = np.exp(-(np.arccos(np.clip(cosd, -1, 1)) / SIG[ed[:, 0]]) ** 2)
    acc = np.zeros((nw, 3)); cntw = np.zeros(nw)
    np.add.at(acc, ed[:, 0], Nn[ed[:, 1]] * w_[:, None]); np.add.at(cntw, ed[:, 0], w_)
    tgt = acc / np.maximum(cntw[:, None], 1e-12)
    sm = Nn + 0.6 * (tgt - Nn); sm /= np.maximum(np.linalg.norm(sm, axis=1, keepdims=True), 1e-12)
    Nn[reg] = sm[reg]
rep['smoothed_positions'] = int(reg.sum())
# hair, braid and band vertices keep their installed normals (the tucked edge moves at most 4 mm; outer-hair normals on the
# hook's underside lit it white from below in the viewer, 2026-11-12)
newN = nr.copy(); newN[:nv0] = NR0
sv = np.nonzero(skin_w[winv] & (vcomp == HEAD))[0]; newN[sv] = Nn[winv[sv]]
ang_ch = np.degrees(np.arccos(np.clip((newN[:nv0] * NR0).sum(1), -1, 1)))
assert np.all(np.linalg.norm(newN, axis=1) > 0.5), 'zero normal'
rep['normal_change_deg_p50_p99_max'] = [float(np.percentile(ang_ch[sv[sv < nv0]], 50)), float(np.percentile(ang_ch[sv[sv < nv0]], 99)), float(ang_ch.max())]
rep['frozen_neck_positions'] = int(frozen.sum())

# ---------------------------------------------------------------- write
def put_image(i, arr):
    buf = io.BytesIO(); Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8)).save(buf, 'PNG', optimize=True)
    data = buf.getvalue()
    while len(g.bin) % 4: g.bin.append(0)
    off = len(g.bin); g.bin += data
    g.j['bufferViews'].append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data)})
    g.j['images'][i]['bufferView'] = len(g.j['bufferViews']) - 1


for k, i in img_idx.items(): put_image(i, TEX[k])
pr = g.j['meshes'][0]['primitives'][1]
pr['attributes'] = {'POSITION': g.add(co.astype(np.float32), 5126, 'VEC3', 34962),
                    'NORMAL': g.add(newN.astype(np.float32), 5126, 'VEC3', 34962),
                    'TEXCOORD_0': g.add(uv.astype(np.float32), 5126, 'VEC2', 34962),
                    'JOINTS_0': g.add(J.astype(np.uint16), 5123, 'VEC4', 34962),
                    'WEIGHTS_0': g.add(W.astype(np.float32), 5126, 'VEC4', 34962)}
pr['indices'] = g.add(tri.astype(np.uint32).ravel(), 5125, 'SCALAR', 34963)
g.compact(); g.save(OUT)
np.savez(HERE / 'work/followup4/face_fix_stage.npz', NT=NT, new_uv=new_uv, nkind=nkind, comp=vcomp)
json.dump(rep, open(REPORT, 'w'), indent=1)
print(json.dumps(rep))
