#!/usr/bin/env python3
"""Linings for Sven's installed GLB, written at the GLB level (2026-11-05, LINING_BRIEF_20261105.md): faces are added only;
every existing vertex, UV, normal, weight, image, clip and the shadow meshes stay byte-identical (new vertices and triangles
are appended to the primitives they line). The same rules run on LOD0 and on each existing LOD1-3 mesh (their own
geometry), so no LOD is rebuilt.

Technique (PeasantDM2's rim_lining.py / neck_cap.py, re-expressed on welded GLB geometry):
  band   faces of one welded piece reachable from a selected open rim loop under the rule's limits;
  lining the band duplicated `off` behind itself along the area-weighted welded normal and flipped; each lining vertex
         copies the raw JOINTS_0/WEIGHTS_0 bytes of the outer vertex it lines; the offset is capped at 40 % of the distance
         to the piece's own cloth along the inward ray (2 cm reach: folds), as rim_lining.py does;
  paint  `dark`: one texel of the garment's own paint (the darkest point of the 24-texel blurred base colour inside the
         band's charts eroded by 12 texels, so every mip level reads the same colour), on lining, rim strip and cap;
         `own`: the twin keeps its outer vertex's UV (hair: the underside reads as hair);
  rim    `dark` rules join each rim edge to its lining edge by a strip (the cloth's thickness), facing out of the edge;
  cap    optional: the lining's inner end (the band's cut edges) fanned to its centroid (mean weights of the loop's top four
         joints), facing the opening: a closed cup, so a view into the opening never reaches the unlined interior.
Rules (Sven, GLB rest space, Y up):
  vest   body prim; rim = open loop with r > 0.15 m and centre y < 0.95 (the coat's hem, skirt bones); band = vest faces
         with every vertex below y_cut; cap at the cut (inside the belt, above the trousers' open top at y 1.027);
  bracer body prim; rim = open loops >= 60 % Forearm-dominant with r < 0.06 (cuff_trim's wrist ring); band = forearm-
         dominant faces whose vertices lie within `depth` of the rim's plane (towards the elbow) and 1.6 r of its axis;
         cap at the band's inner end (beyond the hand stub's open end, 7.4 cm in);
  hair   head prim; rim = open loops of the hair shell (most Ponytail-weighted piece) with >= MIN_HAIR_EDGES edges and
         r > 0.1 (the two side curtains' free edges); band = hair faces with every vertex within `reach` of a rim vertex;
         own-UV twins at 1.5 mm, no strip, no cap.
Usage: glb_lining.py <in glb> <out glb> <report json> [key=value: lods 0,1,2,3 rules vest,bracer,hair y_cut 1.045
       vest_off 0.003 bracer_depth 0.09 bracer_off 0.002 hair_reach 0.06 hair_off 0.0015]"""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbpack  # noqa: E402
from bglbio import acc  # noqa: E402

IN, OUT, REP = sys.argv[1:4]
opt = dict(x.split('=', 1) for x in sys.argv[4:])
LODS = [int(x) for x in opt.get('lods', '0,1,2,3').split(',')]
RULES = opt.get('rules', 'vest,bracer,hair,braids,shells').split(',')
Y_CUT = float(opt.get('y_cut', 1.16))
VEST_OFF = float(opt.get('vest_off', 0.003))
BR_DEPTH = float(opt.get('bracer_depth', 0.03))
BR_OFF = float(opt.get('bracer_off', 0.002))
HAIR_REACH = float(opt.get('hair_reach', 0.015))
HAIR_OFF = float(opt.get('hair_off', 0.0015))
MIN_HAIR_EDGES = int(opt.get('min_hair_edges', 12))
BRAID_OFF = float(opt.get('braid_off', 0.001))
RING = int(opt.get('ring', 0))
HAIR_HITS = set()
if opt.get('hair_hits'):
    _g = json.load(open(opt['hair_hits']))
    _nb = int(opt.get('hits_body_faces', 3244))    # Blender polygon order: body faces, then head faces
    HAIR_HITS = {int(k) - _nb for k, v in _g['hole_faces'].items() if _g['face_material'][int(k)] == 1
                 and v >= int(opt.get('hit_min', 10))}   # faces whose underside showed in >= hit_min hole pixels in all
HAIR_SEL0 = []

doc, binary = glbpack.read(IN)
B = bytes(binary)
node = next(n for n in doc['nodes'] if n.get('name') == 'Sven' and 'mesh' in n)
jn = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
lod_meshes = [node['mesh']] + doc['meshes'][node['mesh']]['extras']['openyamm_lods']


def image_of(mat, key):
    pbr = doc['materials'][mat]['pbrMetallicRoughness']
    tex = doc['textures'][pbr[key]['index']]
    im = doc['images'][tex['source']]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return np.asarray(Image.open(io.BytesIO(B[o:o + v['byteLength']])).convert('RGB'), np.float64) / 255.0


def weld(P):
    _, inv = np.unique(P.round(6), axis=0, return_inverse=True)
    return inv.ravel()


class Prim:
    def __init__(self, p):
        a = p['attributes']; self.p = p
        self.P = acc(doc, B, a['POSITION']).astype(np.float64)
        self.N = acc(doc, B, a['NORMAL']).astype(np.float64)
        self.UV = acc(doc, B, a['TEXCOORD_0']).astype(np.float64)
        self.J = acc(doc, B, a['JOINTS_0']).astype(np.int64)
        self.W = acc(doc, B, a['WEIGHTS_0']).astype(np.float64)
        self.T = acc(doc, B, p['indices']).reshape(-1, 3).astype(np.int64)
        self.inv = weld(self.P); self.TT = self.inv[self.T]; n = self.inv.max() + 1
        self.Pw = np.zeros((n, 3)); self.Pw[self.inv] = self.P
        self.rep = np.zeros(n, np.int64); self.rep[self.inv[::-1]] = np.arange(len(self.P))[::-1]
        self.dom = np.array([jn[j] for j in self.J[np.arange(len(self.J)), self.W.argmax(1)]])
        self.domw = self.dom[self.rep]
        e = np.concatenate([self.TT[:, [0, 1]], self.TT[:, [1, 2]], self.TT[:, [2, 0]]])
        _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
        self.piece = lab[self.TT[:, 0]]
        self.ec = Counter()
        self.edge_faces = defaultdict(list)
        for fi, t in enumerate(self.TT):
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = (min(a_, b_), max(a_, b_)); self.ec[k] += 1; self.edge_faces[k].append(fi)
        self.vf = defaultdict(list)
        for fi, t in enumerate(self.TT):
            for v in t:
                self.vf[v].append(fi)
        # new geometry
        self.newP, self.newN, self.newUV, self.newJW, self.newT = [], [], [], [], []
        self.src, self.kind = [], []   # per new vertex: GLB vertex it lines (-1 cap centre); kind 1 twin, 2 rim copy, 3 cap centre, 4 plug deep ring
        self.nv = len(self.P)
        self.Jraw = glbpack.raw_rows(doc, B, a['JOINTS_0']); self.Wraw = glbpack.raw_rows(doc, B, a['WEIGHTS_0'])

    def loops(self):
        bnd = [e for e, c in self.ec.items() if c == 1]
        adj = defaultdict(list)
        for a_, b_ in bnd:
            adj[a_].append(b_); adj[b_].append(a_)
        seen, out = set(), []
        for v in adj:
            if v in seen:
                continue
            st, comp = [v], []; seen.add(v)
            while st:
                x = st.pop(); comp.append(x)
                for y in adj[x]:
                    if y not in seen:
                        seen.add(y); st.append(y)
            cs = set(comp)
            out.append((comp, [e for e in bnd if e[0] in cs]))
        return out

    def add_vertex(self, pos, nrm, uv, jw_raw, src=-1, kind=0):
        self.src.append(src); self.kind.append(kind)
        self.newP.append(pos); self.newN.append(nrm); self.newUV.append(uv); self.newJW.append(jw_raw)
        self.nv += 1
        return self.nv - 1

    def grow(self, seeds, ok):
        band, st = set(), list(seeds)
        while st:
            f = st.pop()
            if f in band or not ok(f):
                continue
            band.add(f)
            t = self.TT[f]
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                st += [g for g in self.edge_faces[(min(a_, b_), max(a_, b_))] if g not in band]
        return sorted(band)


def ray_hits(O, D, tri, reach):
    """first hit distance (inf if none) of rays O + t D, 0 < t < reach, against triangles tri (m,3,3)"""
    out = np.full(len(O), np.inf)
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    for i in range(len(O)):
        h = np.cross(D[i], e2); a_ = (e1 * h).sum(1)
        ok = np.abs(a_) > 1e-12
        f = np.zeros_like(a_); f[ok] = 1.0 / a_[ok]
        s = O[i] - v0; u = f * (s * h).sum(1)
        q = np.cross(s, e1); v = f * (q @ D[i]); t = f * (e2 * q).sum(1)
        m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & (t < reach)
        if m.any():
            out[i] = t[m].min()
    return out


def dark_uv(pr, band, img, erode=12, blur=24, grey=False):
    """darkest point of the blurred base colour inside the band's charts (eroded), as a UV"""
    H, W = img.shape[:2]
    mask = Image.new('L', (W, H), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(mask)
    for f in band:
        uv = pr.UV[pr.T[f]]
        d.polygon([(float(u * W), float(v * H)) for u, v in uv], fill=255)
    m = ndimage.binary_erosion(np.asarray(mask) > 0, iterations=erode)
    lum = ndimage.uniform_filter(img @ np.array([0.299, 0.587, 0.114]), blur)
    if grey:   # steel: only unsaturated paint (not the skin or fur charts next to it)
        bl = np.stack([ndimage.uniform_filter(img[..., c], 9) for c in range(3)], -1)
        m &= (bl.max(-1) - bl.min(-1)) < 0.08
    if not m.any():
        m = np.asarray(mask) > 0
    idx = np.flatnonzero(m.ravel())
    k = idx[np.argmin(lum.ravel()[idx])]
    y, x = divmod(int(k), W)
    return np.array([(x + 0.5) / W, (y + 0.5) / H]), img[y, x].round(3).tolist(), float(lum.ravel()[k])


def line(pr, band, rims, off, mode, uv_dark=None, cap=False, cap_toward=None):
    """add a lining of `band` (face indices); rims = boundary edges (welded) to join by a strip (dark mode)"""
    if not len(band):
        return dict(band=0, lining=0, strip=0, cap=0, capped_offsets=0)
    band = np.asarray(band)
    bw = np.unique(pr.TT[band])
    tri = pr.Pw[pr.TT[band]]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])   # area-weighted
    nw = np.zeros((pr.Pw.shape[0], 3))
    for c in range(3):
        np.add.at(nw, pr.TT[band, c], fn)
    nrm = nw[bw] / np.maximum(np.linalg.norm(nw[bw], axis=1, keepdims=True), 1e-12)
    # folds and creases (adjacent band faces far apart in direction): the offset direction that keeps the twin behind
    # every adjacent face plane (max over candidates of the min dot); at a fold sharper than that allows, 0.3 mm only
    fu = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
    vfaces = defaultdict(list)
    for i, f in enumerate(band):
        for v in pr.TT[f]:
            vfaces[int(v)].append(i)
    fold_cap = np.full(len(bw), np.inf); folds = 0
    for k, w in enumerate(bw):
        Ni = fu[vfaces[int(w)]]
        if (Ni @ nrm[k]).min() >= 0.3:
            continue
        cand = [nrm[k]] + list(Ni) + [a_ + b_ for i_, a_ in enumerate(Ni) for b_ in Ni[i_ + 1:]]
        cand = [c / np.linalg.norm(c) for c in cand if np.linalg.norm(c) > 1e-9]
        best = max(cand, key=lambda c: (Ni @ c).min())
        nrm[k] = best; folds += 1
        if (Ni @ best).min() < 0.3:
            fold_cap[k] = 0.0003
    piece_faces = np.flatnonzero(pr.piece == pr.piece[band[0]])
    ptri = pr.Pw[pr.TT[piece_faces]]
    O = pr.Pw[bw] - nrm * 1e-4
    hit = ray_hits(O, -nrm, ptri, 0.02)
    offs = np.minimum(np.minimum(off, 0.4 * hit), fold_cap)
    capped = int((offs < off).sum())
    tw_pos = {int(w): pr.Pw[w] - n * o for w, n, o in zip(bw, nrm, offs)}
    tw_nrm = {int(w): -n for w, n in zip(bw, nrm)}
    new_t = []
    if mode == 'dark':
        twin = {}
        for w in bw:
            r = pr.rep[w]
            twin[int(w)] = pr.add_vertex(tw_pos[int(w)], tw_nrm[int(w)], uv_dark, (pr.Jraw[r], pr.Wraw[r]), r, 1)
        for f in band:
            a_, b_, c_ = pr.TT[f]
            new_t.append((twin[a_], twin[c_], twin[b_]))
        # rim strip: outer face edge a->b (its winding) -> triangles (b, a, a'), (b, a', b') on dark copies of a, b
        strip = 0
        bset = set(band.tolist())
        rimcopy = {}
        for e in rims:
            fs = [f for f in pr.edge_faces[e] if f in bset]
            if not fs:
                continue
            t = list(pr.TT[fs[0]])
            i = t.index(e[0])
            a_, b_ = (e[0], e[1]) if t[(i + 1) % 3] == e[1] else (e[1], e[0])
            for v in (a_, b_):
                if v not in rimcopy:
                    r = pr.rep[v]
                    rimcopy[v] = pr.add_vertex(pr.Pw[v], -tw_nrm[int(v)], uv_dark, (pr.Jraw[r], pr.Wraw[r]), r, 2)
            new_t += [(rimcopy[b_], rimcopy[a_], twin[a_]), (rimcopy[b_], twin[a_], twin[b_])]
            strip += 2
        ncap = 0
        capinfo = []
        if cap:
            # cut edges: band edges used once in the band, twice in the mesh, not on the rim
            cnt = Counter()
            for f in band:
                t = pr.TT[f]
                for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    cnt[(min(a_, b_), max(a_, b_))] += 1
            cut = [e for e, c in cnt.items() if c == 1 and pr.ec[e] == 2]
            # components of the cut edges
            adj = defaultdict(list)
            for a_, b_ in cut:
                adj[a_].append(b_); adj[b_].append(a_)
            seen = set()
            for v0 in list(adj):
                if v0 in seen:
                    continue
                st, comp = [v0], []; seen.add(v0)
                while st:
                    x = st.pop(); comp.append(x)
                    for y in adj[x]:
                        if y not in seen:
                            seen.add(y); st.append(y)
                if len(comp) < 4:
                    continue
                cs = set(comp)
                ce = [e for e in cut if e[0] in cs]
                cpos = np.mean([tw_pos[int(v)] for v in comp], 0)
                wsum = defaultdict(float)
                for v in comp:
                    r = pr.rep[v]
                    for j, wt in zip(pr.J[r], pr.W[r]):
                        if wt > 0:
                            wsum[int(j)] += wt
                top = sorted(wsum.items(), key=lambda kv: -kv[1])[:4]
                tot = sum(w for _, w in top)
                jr = np.zeros(4, np.uint8); wr = np.zeros(4, np.float32)
                for k, (j, w) in enumerate(top):
                    jr[k] = j; wr[k] = w / tot
                cn = cap_toward(cpos)
                c = pr.add_vertex(cpos, cn, uv_dark, (jr.view(np.uint8), wr.view(np.uint8)), -1, 3)
                capinfo.append(dict(centre=cpos.round(3).tolist(), loop=len(comp), y=[round(float(pr.Pw[comp, 1].min()), 3), round(float(pr.Pw[comp, 1].max()), 3)]))
                for e in ce:
                    f = [g for g in pr.edge_faces[e] if g in bset][0]
                    t = list(pr.TT[f]); i = t.index(e[0])
                    a_, b_ = (e[0], e[1]) if t[(i + 1) % 3] == e[1] else (e[1], e[0])
                    # lining has b'->a'; the cap triangle continues it with a'->b'
                    tri_ = (twin[a_], twin[b_], c)
                    new_t.append(tri_); ncap += 1
        pr.newT += new_t
        return dict(band=len(band), lining=len(band), strip=strip, cap=ncap, capped_offsets=capped, folds=folds, caps=capinfo)
    # own-UV twins per GLB vertex
    gv = np.unique(pr.T[band])
    twin = {}
    for v in gv:
        w = int(pr.inv[v])
        twin[int(v)] = pr.add_vertex(tw_pos[w], -pr.N[v], pr.UV[v], (pr.Jraw[v], pr.Wraw[v]), int(v), 1)
    for f in band:
        a_, b_, c_ = pr.T[f]
        new_t.append((twin[a_], twin[c_], twin[b_]))
    pr.newT += new_t
    return dict(band=len(band), lining=len(band), strip=0, cap=0, capped_offsets=capped, folds=folds)


def cap_loop(pr, edges, uvd):
    """fan cap of one open loop on copies of its vertices (dark UV) and a centre (mean weights, top four joints),
    consistent with the piece: boundary edge a->b of a face -> cap triangle (b, a, centre)"""
    vs = sorted({v for e in edges for v in e})
    cpos = pr.Pw[vs].mean(0)
    copy = {}
    wsum = defaultdict(float)
    for v in vs:
        r = pr.rep[v]
        copy[v] = pr.add_vertex(pr.Pw[v], np.zeros(3), uvd, (pr.Jraw[r], pr.Wraw[r]), int(r), 2)
        for j, wt in zip(pr.J[r], pr.W[r]):
            if wt > 0:
                wsum[int(j)] += wt
    top = sorted(wsum.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
    jr = np.zeros(4, np.uint8); wr = np.zeros(4, np.float32)
    for k, (j, w) in enumerate(top):
        jr[k] = j; wr[k] = w / tot
    c = pr.add_vertex(cpos, np.zeros(3), uvd, (jr.view(np.uint8), wr.view(np.uint8)), -1, 3)
    tris = []
    for e in edges:
        f = pr.edge_faces[e][0]
        t = list(pr.TT[f]); i = t.index(e[0])
        a_, b_ = (e[0], e[1]) if t[(i + 1) % 3] == e[1] else (e[1], e[0])
        tris.append((copy[b_], copy[a_], c))
    # vertex normals of the copies and the centre: the cap's area-weighted face normal
    P = {copy[v]: pr.Pw[v] for v in vs}; P[c] = cpos
    n = sum(np.cross(P[t[1]] - P[t[0]], P[t[2]] - P[t[0]]) for t in tris)
    n = n / max(np.linalg.norm(n), 1e-12)
    for i in list(copy.values()) + [c]:
        pr.newN[i - (pr.nv - len(pr.newN))] = n
    pr.newT += tris
    return dict(cap=len(tris))


def plug(pr, comp, edges, ax, cen, uvd, off, depth):
    """rim strip -> ring `off` inside the rim (radially) -> tube `depth` along ax -> fan cap; orientation continues the
    outer cloth across each rim edge (outer a->b: strip (b, a, a1), (b, a1, b1); tube (b1, a1, a2), (b1, a2, b2); cap
    (b2, a2, centre)), so the plug's front faces look into the opening"""
    vs = sorted(set(comp))
    rad = {}
    for v in vs:
        x = pr.Pw[v] - cen; u = x - (x @ ax) * ax; rad[v] = u / max(np.linalg.norm(u), 1e-12)
    # the deep ring follows the wall: from the axis point `depth` in, a radial ray per rim vertex finds the wall
    pf = np.flatnonzero(pr.piece == pr.piece[pr.edge_faces[edges[0]][0]])
    Dd = np.array([rad[v] for v in vs])
    for dep in (depth, depth / 2, depth / 4):
        axc = cen + ax * (((pr.Pw[vs] - cen) @ ax).mean() + dep)
        wall = ray_hits(np.repeat(axc[None], len(vs), 0), Dd, pr.Pw[pr.TT[pf]], 0.08)
        if np.isfinite(wall).all():
            break
    else:
        # a coarse LOD tube: accept the full depth when 60 % of the walls are found; the rest take the narrowest found wall
        axc = cen + ax * (((pr.Pw[vs] - cen) @ ax).mean() + depth)
        wall = ray_hits(np.repeat(axc[None], len(vs), 0), Dd, pr.Pw[pr.TT[pf]], 0.08)
        dep = depth
        if np.isfinite(wall).mean() < 0.6:
            return dict(skipped='walls found for under 60 % of the rim at depth/1, /2, /4 (a coarse LOD tube)')
    depth = dep
    rimc, r1, r2 = {}, {}, {}
    for k, v in enumerate(vs):
        rr = pr.rep[v]; jw = (pr.Jraw[rr], pr.Wraw[rr])
        rimc[v] = pr.add_vertex(pr.Pw[v], -ax, uvd, jw, int(rr), 2)
        p1 = pr.Pw[v] - rad[v] * off
        r1[v] = pr.add_vertex(p1, -rad[v], uvd, jw, int(rr), 1)
        rw = wall[k] - off if np.isfinite(wall[k]) else wall[np.isfinite(wall)].min() - off   # unfound: the narrowest wall
        r2[v] = pr.add_vertex(axc + rad[v] * rw, -rad[v], uvd, jw, int(rr), 4)
    wsum = defaultdict(float)
    for v in vs:
        rr = pr.rep[v]
        for j, wt in zip(pr.J[rr], pr.W[rr]):
            if wt > 0:
                wsum[int(j)] += wt
    top = sorted(wsum.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
    jr = np.zeros(4, np.uint8); wr = np.zeros(4, np.float32)
    for k, (j, w) in enumerate(top):
        jr[k] = j; wr[k] = w / tot
    cpos = axc
    c = pr.add_vertex(cpos, -ax, uvd, (jr.view(np.uint8), wr.view(np.uint8)), -1, 3)
    tris = []
    for e in edges:
        f = pr.edge_faces[e][0]
        t = list(pr.TT[f]); i = t.index(e[0])
        a_, b_ = (e[0], e[1]) if t[(i + 1) % 3] == e[1] else (e[1], e[0])
        tris += [(rimc[b_], rimc[a_], r1[a_]), (rimc[b_], r1[a_], r1[b_]),
                 (r1[b_], r1[a_], r2[a_]), (r1[b_], r2[a_], r2[b_]),
                 (r2[b_], r2[a_], c)]
    pr.newT += tris
    # rest check: every deep-ring vertex inside the piece's wall (an outward radial ray meets the wall within 2 cm)
    O = np.array([pr.newP[r2[v] - (pr.nv - len(pr.newP))] for v in vs]); Dd = np.array([rad[v] for v in vs])
    hit = ray_hits(O, Dd, pr.Pw[pr.TT[pf]], 0.02)
    return dict(strip=2 * len(edges), tube=2 * len(edges), cap=len(edges), depth=depth,
                deep_ring_inside=int(np.isfinite(hit).sum()), deep_ring=len(vs), wall_found=int(np.isfinite(wall).sum()),
                deep_ring_clearance_mm=[round(float(np.min(hit)) * 1000, 2), round(float(np.max(hit)) * 1000, 2)])


report = {'lods': {}}
tw = {}
REF_PIECES = {'braids': [], 'shells': []}   # LOD0 centres; a LOD's piece must lie within 2 cm of one


def matches(rule, c):
    if lod == 0:
        REF_PIECES[rule].append(c); return True
    return any(np.linalg.norm(c - r) < 0.02 for r in REF_PIECES[rule])


uv_cache = {}
for lod in LODS:
    mi = lod_meshes[lod]
    prims = doc['meshes'][mi]['primitives']
    body, head = Prim(prims[0]), Prim(prims[1])
    rl = report['lods'][lod] = {'mesh': doc['meshes'][mi]['name'], 'rules': {}}
    img = image_of(prims[0]['material'], 'baseColorTexture')
    for rule in RULES:
        if rule == 'vest':
            pr = body
            for comp, edges in pr.loops():
                q = pr.Pw[comp]; cen = q.mean(0); r = np.linalg.norm(q - cen, axis=1).mean()
                if not (r > 0.15 and cen[1] < 0.95):
                    continue
                pc = pr.piece[pr.edge_faces[edges[0]][0]]
                seeds = [pr.edge_faces[e][0] for e in edges]
                band = pr.grow(seeds, lambda f: pr.piece[f] == pc and pr.Pw[pr.TT[f], 1].mean() < Y_CUT)
                if 'vest' not in uv_cache:
                    uv_cache['vest'] = dark_uv(pr, [f for f in band if pr.Pw[pr.TT[f], 1].mean() < 1.0], img)   # the skirt's own red paint (not the belt strap painted under the belt)
                uvd = uv_cache['vest'][0]
                hem_c = cen.copy()

                def toward(cp, hem_c=hem_c):
                    d = hem_c - cp; return d / np.linalg.norm(d)
                res = line(pr, band, edges, VEST_OFF, 'dark', uvd, cap=True, cap_toward=toward)
                res.update(rim_edges=len(edges), rim_centre=cen.round(3).tolist(), texel=uv_cache['vest'][1],
                           uv=uvd.round(5).tolist())
                rl['rules'].setdefault('vest', []).append(res)
        elif rule == 'bracer':
            # the bracers' wrist rings (cuff_trim's cut): the arm mesh is coarse here (faces along the bracer up to 15 cm
            # long), so a band lining would end in a ragged cut; instead a plug built from the rim loop itself: the rim
            # joined by a strip to a ring 2 mm inside it, a tube from that ring BRACER_DEPTH up the bracer, and a fan cap,
            # every vertex with its rim vertex's weights (the bracer is rigid on the forearm, bracer_rigid.py)
            pr = body
            found = []
            for comp, edges in pr.loops():
                q = pr.Pw[comp]; cen = q.mean(0); r = np.linalg.norm(q - cen, axis=1).mean()
                fore = np.mean(['Forearm' in d for d in pr.domw[comp]])
                if not (fore >= 0.6 and r < 0.06):
                    continue
                side = ' L ' if np.mean([' L ' in d for d in pr.domw[comp]]) > 0.5 else ' R '
                pc = pr.piece[pr.edge_faces[edges[0]][0]]
                # the forearm's axis: main principal axis of this arm's forearm-dominant vertices within 15 cm of the rim
                # (the rim is cut slanted, so its own plane normal is not the bracer's axis)
                fv = np.flatnonzero((pr.domw == f'Bip01{side}Forearm') & (np.linalg.norm(pr.Pw - cen, axis=1) < 0.15))
                X = pr.Pw[fv] - pr.Pw[fv].mean(0)
                ax = np.linalg.svd(X, full_matrices=False)[2][0]
                if ((pr.Pw[fv] - cen) @ ax).mean() < 0:
                    ax = -ax            # towards the elbow
                found.append((comp, edges, ax, side, cen, r, pc))
            if 'bracer' not in uv_cache:
                steel = [f for f in range(len(pr.TT)) if all('Forearm' in d for d in pr.domw[pr.TT[f]])
                         and (np.abs(pr.Pw[pr.TT[f], 0]) > 0.53).all()]
                uv_cache['bracer'] = dark_uv(pr, steel, img, erode=3, blur=3, grey=True)
            uvd = uv_cache['bracer'][0]
            for comp, edges, ax, side, cen, r, pc in found:
                res = plug(pr, comp, edges, ax, cen, uvd, BR_OFF, BR_DEPTH)
                res.update(side=side.strip(), rim_edges=len(edges), rim_centre=cen.round(3).tolist(), radius=round(float(r), 3),
                           texel=uv_cache['bracer'][1], uv=uvd.round(5).tolist())
                rl['rules'].setdefault('bracer', []).append(res)
        elif rule == 'hair':
            # the hair shell: faces whose underside the see-through gate saw (HAIR_HITS: hole_faces of the installed GLB,
            # every clip at step 4 from 16 views) plus their RING-ring neighbours, united with the band within HAIR_REACH of
            # the shell's free edges (every open loop of >= MIN_HAIR_EDGES edges); a LOD takes its hair faces within
            # 1.2 cm of a LOD0 selection (LOD1; LOD2/3 the free-edge band only); lined once with own-UV twins
            from scipy.spatial import cKDTree
            pr = head
            pony = Counter(pr.piece[f] for f in range(len(pr.TT))
                           if sum('Ponytail' in d for d in pr.domw[pr.TT[f]]) >= 2)
            hp = pony.most_common(1)[0][0]
            lps = [(c, e) for c, e in pr.loops() if pr.piece[pr.edge_faces[e[0]][0]] == hp and len(e) >= MIN_HAIR_EDGES]
            sel = set()
            if lps and HAIR_REACH > 0:
                kd = cKDTree(pr.Pw[[v for c, _ in lps for v in c]])
                seeds = [pr.edge_faces[x][0] for _, e in lps for x in e]
                sel |= set(pr.grow(seeds, lambda f: pr.piece[f] == hp and (kd.query(pr.Pw[pr.TT[f]])[0] < HAIR_REACH).all()))
            nhit = 0
            if HAIR_HITS:
                if lod == 0:
                    hits = {f for f in HAIR_HITS if f < len(pr.TT) and pr.piece[f] == hp}
                    nhit = len(hits)
                    for _ in range(RING):
                        hits |= {g for f in hits for v in pr.TT[f] for g in pr.vf[v] if pr.piece[g] == hp}
                    sel |= hits
                elif lod == 1:   # LOD1 only; LOD2/3 (far) keep the free-edge band alone
                    kd0 = cKDTree(np.array(HAIR_SEL0))
                    cen = pr.Pw[pr.TT].mean(1)
                    sel |= {f for f in np.flatnonzero(pr.piece == hp) if kd0.query(cen[f])[0] < 0.012}
            band = sorted(int(f) for f in sel)
            if lod == 0:
                HAIR_SEL0[:] = [pr.Pw[pr.TT[f]].mean(0) for f in band]
            res = line(pr, band, [], HAIR_OFF, 'own')
            res.update(loops=[len(e) for _, e in lps], gate_faces=nhit)
            rl['rules'].setdefault('hair', []).append(res)
        elif rule == 'braids':
            # the two side braids (open strips hanging from the temples: head pieces of 40-200 faces, >= 15 cm tall, whose
            # open loop has >= 25 % Neck-dominant vertices; not the eyes or lips): every face twinned with its own UVs
            pr = head
            for pc in np.unique(pr.piece):
                fs = np.flatnonzero(pr.piece == pc)
                vs = np.unique(pr.TT[fs])
                if not (40 <= len(fs) <= 200) or np.ptp(pr.Pw[vs, 1]) < 0.15:
                    continue
                lp = [(c, e) for c, e in pr.loops() if pr.piece[pr.edge_faces[e[0]][0]] == pc]
                if not lp or np.mean(['Neck' in d for d in pr.domw[lp[0][0]]]) < 0.25 or not matches('braids', pr.Pw[vs].mean(0)):
                    continue
                res = line(pr, list(fs), [], BRAID_OFF, 'own')
                res.update(piece_faces=len(fs), centre=pr.Pw[vs].mean(0).round(3).tolist())
                rl['rules'].setdefault('braids', []).append(res)
        elif rule == 'shells':
            # small open shells on the chest (brooches, necklace plaques, the belt buckle: body pieces under 100 faces with
            # one open loop of >= 10 edges): the loop capped by a fan on a dark texel of the piece's own paint, facing out
            # of the closed piece (towards the body)
            pr = body
            for pc in np.unique(pr.piece):
                fs = np.flatnonzero(pr.piece == pc)
                lp = [(c, e) for c, e in pr.loops() if pr.piece[pr.edge_faces[e[0]][0]] == pc]
                if len(fs) >= 100 or len(lp) != 1 or len(lp[0][1]) < 10:
                    continue
                comp, edges = lp[0]
                if not matches('shells', pr.Pw[np.unique(pr.TT[fs])].mean(0)):
                    continue
                uvd, tex, _ = dark_uv(pr, list(fs), img, erode=2, blur=3)
                res = cap_loop(pr, edges, uvd)
                res.update(piece_faces=len(fs), loop=len(edges), centre=pr.Pw[comp].mean(0).round(3).tolist(), texel=tex)
                rl['rules'].setdefault('shells', []).append(res)
    # write the primitives back (appended rows; existing rows copied as raw bytes)
    for pr in (body, head):
        if not pr.newT:
            continue
        p = pr.p; a = p['attributes']
        n_new = len(pr.newP)

        def ext(key, rows):
            old = glbpack.raw_rows(doc, binary, a[key])
            new = np.concatenate([old, rows], 0)
            i = glbpack.append(doc, binary, doc['accessors'][a[key]], new)
            glbpack.set_minmax(doc, binary, i)
            return i
        f32 = lambda x: np.asarray(x, np.float32).reshape(n_new, -1).view(np.uint8)  # noqa: E731
        na = {}
        na['POSITION'] = ext('POSITION', f32(pr.newP))
        nn = np.asarray(pr.newN, np.float64); nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
        na['NORMAL'] = ext('NORMAL', f32(nn))
        na['TEXCOORD_0'] = ext('TEXCOORD_0', f32(pr.newUV))
        na['JOINTS_0'] = ext('JOINTS_0', np.stack([np.asarray(j, np.uint8).ravel() for j, _ in pr.newJW]))
        na['WEIGHTS_0'] = ext('WEIGHTS_0', np.stack([np.asarray(w, np.uint8).ravel() for _, w in pr.newJW]))
        T = np.concatenate([pr.T, np.asarray(pr.newT, np.int64)], 0)
        assert T.max() < 65536
        ia = glbpack.append(doc, binary, doc['accessors'][p['indices']], T.astype(np.uint16).ravel().view(np.uint8).reshape(-1, 2),
                            count=T.size)
        for k in na:
            a[k] = na[k]
        p['indices'] = ia
        rl.setdefault('faces', {})[doc['materials'][p['material']]['name']] = [len(pr.T), int(len(T))]
        tw.setdefault(lod, {})[doc['materials'][p['material']]['name']] = dict(nv0=len(pr.P), nf0=len(pr.T), src=[int(x) for x in pr.src],
                                                                               kind=pr.kind)
    print('LINING lod', lod, json.dumps(rl))
doc, binary = glbpack.compact(doc, binary)
glbpack.write(OUT, doc, binary)
Path(REP).write_text(json.dumps(report, indent=1))
Path(OUT + '.twins.json').write_text(json.dumps(tw))
print('LINING done', OUT)
