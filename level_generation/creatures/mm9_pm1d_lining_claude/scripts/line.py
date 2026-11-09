#!/usr/bin/env python3
"""GLB-level linings for the installed (reduced) PeasantM1d (2026-11-05, LINING_BRIEF_20261105.md). PeasantDM2's
rim_lining.py and neck_cap.py, rewritten on the GLB's own LOD0 arrays so the reduction and the approved clips are kept:
every existing vertex row (position, normal, UV, joints, weights) and every existing triangle stays byte-identical; new
vertices and triangles are appended to the end of each primitive. Old LOD/shadow meshes are dropped (build_lods.py
rebuilds them); skin, nodes, clips, materials, variants and images are untouched.

Ops (a JSON list, applied in order; faces lined by an earlier op are left out of later bands, as in rim_lining.py):
  band: the band of faces reachable from the selected open loops (welded by position) through edge-adjacent faces of the
        same piece(s) whose vertices all lie within `depth` m of the loop vertices (and, with `bones`, whose vertices'
        dominant joints contain one of those keywords) is duplicated `offset` behind itself along the area-weighted vertex
        normal, reversed, with the source vertex's joints and weights, so the inside follows the outside under any pose.
        Vertices of inner-layer faces (facing the dominant bone's axis: Meshy folds) move only `inner_offset`, and those
        faces' twins keep the face's own UVs (rim_lining.py's rule); `skip_inner` leaves them out instead. Every
        vertex stays behind any cloth its offset direction meets within 2 cm (at most 40 % of that distance). The loop
        edges are joined to their twins by a rim strip facing out of the opening. Lining and strip take one dark texel of
        the band's own paint: the roughest face among the darkest `dark_pct` % of band faces whose region label
        (material region mask, RGBA or n = none) is `region`, at a texel whose 5x5 mask neighbourhood is that label only.
  cap:  a triangle fan from the loop's centroid (weights: the rim's mean, four largest kept) closes an open tube end
        (neck_cap.py's technique), facing away from the piece's centroid (`facing: in` reverses it), on the dark texel
        of `texel_from` (an earlier band op's name) or of its own piece (`region`).
Loops are chosen by `loops`: a list of [x, y, z] GLB-space centres (the nearest loop centre within 3 cm; rims.py lists
them). Usage: line.py <in glb> <out glb> <ops json> <report json>"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
import glbpack as G  # noqa: E402

src, dst, opsf, repf = sys.argv[1:5]
OPS = json.load(open(opsf))
doc, binary, nd, prims, jn = C.load(src)
binary = bytearray(binary)
HEAD, TAIL = C.joint_segments(doc, binary, nd)
mat = {m['name']: m for m in doc['materials']}

# all original LOD0 triangles (both primitives) for the offset collision test
ALL_TRI = np.concatenate([d['P'][d['T']] for d in prims.values()])
ALL_CEN = ALL_TRI.mean(1); ALL_KD = cKDTree(ALL_CEN)


def ray_hits(o, d, maxd):
    """distance to the nearest original triangle along the ray (inf if none within maxd)"""
    ids = ALL_KD.query_ball_point(o, maxd + 0.03)
    if not ids:
        return np.inf
    tr = ALL_TRI[ids]; e1 = tr[:, 1] - tr[:, 0]; e2 = tr[:, 2] - tr[:, 0]
    pv = np.cross(d, e2); det = (e1 * pv).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - tr[:, 0]
    u = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); v = (qv * d).sum(1) * inv; t = (e2 * qv).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < maxd)
    return t[hit].min() if hit.any() else np.inf


class Prim:
    def __init__(self, name):
        d = prims[name]; self.name = name; self.d = d
        self.P, self.N, self.UV, self.J, self.W, self.T = d['P'], d['N'], d['UV'], d['J'], d['W'], d['T']
        self.inv = C.weld(self.P); self.nw = self.inv.max() + 1
        self.TT = self.inv[self.T]
        self.piece = C.pieces(self.TT, self.nw); self.fpiece = self.piece[self.TT[:, 0]]
        self.rep = np.zeros(self.nw, np.int64); self.rep[self.inv] = np.arange(len(self.P))   # one GLB vertex per welded id
        self.WP = self.P[self.rep]
        self.loops, self.bnd, self.ec = C.boundary_loops(self.TT)
        self.dj = self.J[np.arange(len(self.J)), self.W.argmax(1)]
        self.wdj = self.dj[self.rep]
        m = mat[name]
        self.mask = C.image(doc, binary, m['extras']['openyamm_region_mask']['index'])
        self.col = C.image(doc, binary, m['pbrMetallicRoughness']['baseColorTexture']['index'])
        self.orm = C.image(doc, binary, m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])
        a, b, c = (self.P[self.T[:, k]] for k in range(3))
        self.fn = np.cross(b - a, c - a); self.farea = np.linalg.norm(self.fn, axis=1) / 2
        self.fn = self.fn / np.maximum(np.linalg.norm(self.fn, axis=1, keepdims=True), 1e-15)
        self.fcen = (a + b + c) / 3
        self.lined = np.zeros(len(self.T), bool)
        self.strip_ids = set()  # new triangles that are rim strips (the cloth's edge, meant to show)
        self.vtag = []          # per new vertex: (op, role, source pieces) for lining_gate.py
        self.newv = []          # (P, N, UV, J row index to copy joints/weights from | (J, W) arrays)
        self.newt = []
        self.uvc = self.UV[self.T].mean(1)
        lab = C.texel(self.mask, self.uvc); self.flabel = np.where(lab.max(1) > 0.3, lab.argmax(1), 4)

    def add_vertex(self, p, n, uv, jw, role='rim'):
        self.newv.append((np.asarray(p, float), np.asarray(n, float), np.asarray(uv, float), jw))
        self.vtag.append((CUR['op'], role, CUR['pieces']))
        return len(self.P) + len(self.newv) - 1

    def loop_near(self, c):
        best = min(self.loops, key=lambda lp: np.linalg.norm(self.WP[lp].mean(0) - c))
        d = np.linalg.norm(self.WP[best].mean(0) - c)
        assert d < 0.03, (self.name, c, d)
        return best

    def label_ok(self, uv, k):
        h, w = self.mask.shape[:2]; y, x = int(uv[1] % 1 * h), int(uv[0] % 1 * w)
        nb = self.mask[max(0, y - 2):y + 3, max(0, x - 2):x + 3].reshape(-1, 4)
        labs = np.where(nb.max(1) > 0.3, nb.argmax(1), 4)
        return (labs == k).all()

    def patch(self, uv, r=6):
        h, w = self.col.shape[:2]; y, x = int(uv[1] % 1 * h), int(uv[0] % 1 * w)
        nb = self.col[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1, :3].reshape(-1, 3) @ np.array([0.299, 0.587, 0.114])
        return nb.mean(), nb.std()

    def dark_uv(self, faces, region, dark_pct):
        """the darkest 13x13-texel patch mean among the band faces' centre texels of that region (uniform: std < 0.03, its
        5x5 mask neighbourhood one label), so the lining keeps its colour down the mip chain; the roughest of the darkest
        dark_pct % wins (a smooth texel shines grey inside a sleeve)"""
        k = 'RGBAn'.index(region)
        cand = [f for f in faces if self.flabel[f] == k and self.label_ok(self.uvc[f], k)] or list(faces)
        st = np.array([self.patch(self.uvc[f]) for f in cand])
        ok = st[:, 1] < 0.03
        if ok.sum() == 0:
            ok = st[:, 1] <= np.percentile(st[:, 1], 25)
        idx = np.where(ok)[0]
        order = idx[np.argsort(st[idx, 0])][:max(1, int(len(idx) * dark_pct / 100))]
        rough = C.texel(self.orm, self.uvc[np.array(cand)[order]])[:, 1]
        f = cand[int(order[np.argmax(rough)])]; uv = self.uvc[f]
        return uv, f, C.texel(self.col, uv)[0, :3]

    def inner_face(self, f):
        js = self.dj[self.T[f]]; vals, cnt = np.unique(js, return_counts=True); j = vals[cnt.argmax()]
        a0, a1 = HEAD[j], TAIL[j]; c = self.fcen[f]; dd = a1 - a0
        t = np.clip((c - a0) @ dd / max(dd @ dd, 1e-12), 0, 1); out = c - (a0 + dd * t)
        return self.fn[f] @ (out / max(np.linalg.norm(out), 1e-12)) < -0.2


CUR = {'op': '', 'pieces': ()}
PR = {n: Prim(n) for n in prims}
REPORT = []
DARK = {}


def jw_of(pr, gi):
    return ('copy', gi)


def mean_jw(pr, verts):
    """mean joint weights of GLB vertices, four largest renormalised"""
    acc = defaultdict(float)
    for v in verts:
        for j, w in zip(pr.J[v], pr.W[v]):
            if w > 0:
                acc[int(j)] += float(w) / len(verts)
    top = sorted(acc.items(), key=lambda x: -x[1])[:4]
    s = sum(w for _, w in top); J = np.zeros(4, np.int64); W = np.zeros(4)
    for i, (j, w) in enumerate(top):
        J[i] = j; W[i] = w / s
    return ('jw', J, W)


KINDS = {n: [] for n in PR}           # per new triangle: the op kind (band, cap, fill, backface)


def tag_kinds(kind):
    for n, q in PR.items():
        KINDS[n] += [kind] * (len(q.newt) - len(KINDS[n]))


for op in OPS:
    tag_kinds(OPS[OPS.index(op) - 1]['op'] if OPS.index(op) else 'none')
    pr = PR[op.get('prim', 'PM1d_C')]
    CUR['op'] = op['name']; CUR['pieces'] = ()
    if op['op'] == 'backface':
        # reversed exact copies (own UVs, negated normals, the vertex's own joints/weights) of single-sided sheets whose back the
        # gate shows as holes: faces with >= min_px hole pixels in a hole_faces.py map, grown `dilate` edge rings within the
        # same piece, limited to pieces whose faces carry region label `region` (hair cards: R of the head mask)
        hm = np.load(op['holes'])[pr.name]
        sel = set(np.where(hm >= op.get('min_px', 1))[0])
        if 'region' in op:
            k = 'RGBAn'.index(op['region']); sel = {f for f in sel if pr.flabel[f] == k}
        if 'pieces' in op:
            sel = {f for f in sel if pr.fpiece[f] in set(op['pieces'])}
        fadj = defaultdict(list)
        for e, fs in pr.ec.items():
            for f in fs:
                fadj[f] += [g for g in fs if g != f]
        for _ in range(op.get('dilate', 0)):
            sel |= {g for f in sel for g in fadj[f] if pr.fpiece[g] == pr.fpiece[f]}
        sel = sorted(f for f in sel if not pr.lined[f])
        own = {}
        for f in sel:
            vs = []
            for g in pr.T[f]:
                if g not in own:
                    own[g] = pr.add_vertex(pr.P[g], -pr.N[g], pr.UV[g], ('copy', g), 'back')
                vs.append(own[g])
            pr.newt.append((vs[0], vs[2], vs[1]))
        pr.lined[sel] = True
        REPORT.append(dict(op=op['name'], kind='backface', prim=pr.name, faces=len(sel),
                           pieces=sorted({int(pr.fpiece[f]) for f in sel})))
        continue
    lps = [pr.loop_near(np.array(c)) for c in op['loops']]
    lpv = sorted({v for lp in lps for v in lp})
    if op['op'] == 'band':
        depth = op['depth']; offset = op.get('offset', 0.003); inner_off = op.get('inner_offset', 0.0005)
        kd = cKDTree(pr.WP[lpv])
        pieces = set(op.get('pieces') or {pr.piece[v] for v in lpv})
        CUR['pieces'] = tuple(int(x) for x in pieces)
        bones = op.get('bones'); ymin, ymax = op.get('ymin', -9), op.get('ymax', 9)
        vdist = kd.query(pr.WP)[0]
        vbone = np.array([not bones or any(k in jn[j] for k in bones) for j in pr.wdj])
        vy = (pr.WP[:, 1] >= ymin) & (pr.WP[:, 1] <= ymax)
        fok = ((vdist[pr.TT] < depth) & vbone[pr.TT] & vy[pr.TT]).all(1) & np.isin(pr.fpiece, list(pieces)) & ~pr.lined
        # faces adjacent by welded edge
        fadj = defaultdict(list)
        for e, fs in pr.ec.items():
            for f in fs:
                fadj[f] += [g for g in fs if g != f]
        start = {pr.bnd[e] for e in pr.bnd if e[0] in set(lpv) and e[1] in set(lpv)}
        band, st = set(), [f for f in start if fok[f]]
        while st:
            f = st.pop()
            if f in band or not fok[f]:
                continue
            band.add(f); st += [g for g in fadj[f] if g not in band]
        band = sorted(band)
        inner = {f for f in band if pr.inner_face(f)}
        if op.get('skip_inner'):
            band = [f for f in band if f not in inner]; inner = set()
        if 'texel_from' in op:            # the same garment's dark texel as an earlier band (one lining colour per garment)
            assert DARK[op['texel_from']][0] == pr.name
            uv_dark = DARK[op['texel_from']][1]; rgb = C.texel(pr.col, uv_dark)[0, :3]
        else:
            # the darkest uniform patch of the garment's own paint: over every face of the band's pieces
            src_f = np.where(np.isin(pr.fpiece, list(pieces)))[0]
            uv_dark, fdark, rgb = pr.dark_uv(src_f, op.get('region', 'R'), op.get('dark_pct', 25))
        DARK[op['name']] = (pr.name, uv_dark)
        # welded vertex normals over the band
        wn = np.zeros((pr.nw, 3))
        for f in band:
            for w in pr.TT[f]:
                wn[w] += pr.fn[f] * pr.farea[f]
        bw = sorted({w for f in band for w in pr.TT[f]})
        near_inner = {w for f in inner for w in pr.TT[f]}
        target, capped = {}, 0
        for w in bw:
            n = wn[w] / max(np.linalg.norm(wn[w]), 1e-15); dirw = -n
            want = inner_off if w in near_inner else offset
            dist = ray_hits(pr.WP[w] + dirw * 1e-4, dirw, 0.02)
            if 0.4 * dist < want:
                want = 0.4 * dist; capped += 1
            target[w] = pr.WP[w] + dirw * want
        # twin vertices: dark ones per welded id; own-paint ones (twins of inner faces) per GLB vertex
        dark_v, own_v = {}, {}

        def twin_dark(w):
            if w not in dark_v:
                n = wn[w] / max(np.linalg.norm(wn[w]), 1e-15)
                dark_v[w] = pr.add_vertex(target[w], -n, uv_dark, ('copy', pr.rep[w]), 'twin')
            return dark_v[w]

        def twin_own(g):
            if g not in own_v:
                w = pr.inv[g]; n = wn[w] / max(np.linalg.norm(wn[w]), 1e-15)
                own_v[g] = pr.add_vertex(target[w], -n, pr.UV[g], ('copy', g), 'twin')
            return own_v[g]
        nl = 0
        for f in band:
            t = pr.T[f]
            if f in inner:
                a, b, c = (twin_own(g) for g in t)
            else:
                a, b, c = (twin_dark(pr.inv[g]) for g in t)
            pr.newt.append((a, c, b)); nl += 1
        bset = set(band)
        # rim strip between each selected loop edge of a band face and its twin, facing out of the opening
        rim_v, nr = {}, 0

        def rim_vertex(w, n):
            if w not in rim_v:
                rim_v[w] = pr.add_vertex(pr.WP[w], n, uv_dark, ('copy', pr.rep[w]))
            return rim_v[w]
        strips = []
        lset = set(lpv)
        for e, f0 in pr.bnd.items():
            if f0 not in bset or e[0] not in lset or e[1] not in lset:
                continue
            a, b = e; q = [pr.WP[a], pr.WP[b], target[b], target[a]]
            nrm = np.cross(q[1] - q[0], q[2] - q[0]); cen = np.mean(q, 0)
            flip = nrm @ (cen - pr.fcen[f0]) < 0
            strips.append((a, b, flip, nrm / max(np.linalg.norm(nrm), 1e-15) * (-1 if flip else 1)))
        sn = defaultdict(lambda: np.zeros(3))
        for a, b, flip, n in strips:
            sn[a] += n; sn[b] += n
        for a, b, flip, n in strips:
            na = sn[a] / max(np.linalg.norm(sn[a]), 1e-15); nb_ = sn[b] / max(np.linalg.norm(sn[b]), 1e-15)
            A, B = rim_vertex(a, na), rim_vertex(b, nb_)
            # the strip's inner corners share the twins' positions, on the strip's own vertices (strip normal)
            A2 = pr.add_vertex(target[a], na, uv_dark, ('copy', pr.rep[a]), 'twin')
            B2 = pr.add_vertex(target[b], nb_, uv_dark, ('copy', pr.rep[b]), 'twin')
            for tri in ((A, B, B2), (A, B2, A2)):
                pr.strip_ids.add(len(pr.newt)); pr.newt.append(tri[::-1] if flip else tri); nr += 1
        pr.lined[band] = True
        REPORT.append(dict(op=op['name'], kind='band', loops=[len(lp) for lp in lps], band_faces=len(band),
                           inner_twins_own_paint=len(inner), lining_faces=nl, rim_faces=nr, offset_capped=capped,
                           dark_uv=[round(float(x), 5) for x in uv_dark], dark_rgb=[round(float(x), 3) for x in rgb],
                           region=op.get('region', 'R'), pieces=sorted(int(p) for p in pieces),
                           band_regions={k: int(sum(pr.flabel[f] == i for f in band)) for i, k in enumerate('RGBAn')}))
    elif op['op'] == 'fill':
        # a real hole in the outer cloth (seen from outside): a fan in the cloth's own paint (neck_hole.py's idea): each fan
        # triangle takes the corner UVs of the boundary face on its rim edge, and its own centre vertex the UV of that face's
        # centroid (inside the same UV island, so the colour continues across the patch); normals = the rim's mean normal
        lp = lps[0]
        adj = defaultdict(list)
        for a, b in pr.bnd:
            if a in lp and b in lp:
                adj[a].append(b); adj[b].append(a)
        ring = [lp[0]]; prev = None
        while True:
            nxt = [x for x in adj[ring[-1]] if x != prev]
            if not nxt or nxt[0] == ring[0]:
                break
            prev = ring[-1]; ring.append(nxt[0])
        assert len(ring) == len(lp)
        c = pr.WP[ring].mean(0)
        nm = np.zeros(3)
        for w in ring:
            nm += pr.N[pr.inv == w].sum(0)
        nm /= np.linalg.norm(nm)
        cjw = mean_jw(pr, [pr.rep[w] for w in ring]); nf = 0
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            f0 = pr.bnd[tuple(sorted((a, b)))]
            ga = next(g for g in pr.T[f0] if pr.inv[g] == a); gb = next(g for g in pr.T[f0] if pr.inv[g] == b)
            cv = pr.add_vertex(c, nm, pr.uvc[f0], cjw, 'fill')
            va = pr.add_vertex(pr.P[ga], pr.N[ga], pr.UV[ga], ('copy', ga))
            vb = pr.add_vertex(pr.P[gb], pr.N[gb], pr.UV[gb], ('copy', gb))
            tri = (cv, va, vb)
            # the boundary face runs a -> b or b -> a; the fill runs the edge the other way (consistent winding)
            t = list(pr.T[f0]); ia, ib = t.index(ga), t.index(gb)
            if (ib - ia) % 3 == 1:          # face has a -> b: the fill needs b -> a
                tri = (cv, vb, va)
            pr.newt.append(tri); nf += 1
        REPORT.append(dict(op=op['name'], kind='fill', loop=len(lp), faces=nf, centre=[round(float(x), 4) for x in c]))
    elif op['op'] == 'cap':
        assert len(lps) == 1
        lp = lps[0]
        po = PR[op.get('out_prim', pr.name)]       # the cap may go into another primitive (a hand stub capped on the sleeve's paint)
        # order the loop
        adj = defaultdict(list)
        for a, b in pr.bnd:
            if a in lp and b in lp:
                adj[a].append(b); adj[b].append(a)
        ring = [lp[0]]; prev = None
        while True:
            nxt = [x for x in adj[ring[-1]] if x != prev]
            if not nxt or nxt[0] == ring[0]:
                break
            prev = ring[-1]; ring.append(nxt[0])
        assert len(ring) == len(lp), (len(ring), len(lp))
        if 'texel_from' in op:
            assert DARK[op['texel_from']][0] == po.name, (op['name'], DARK[op['texel_from']][0], po.name)
            uv = DARK[op['texel_from']][1]
        else:
            fs = np.where(np.isin(pr.fpiece, [pr.piece[lp[0]]]))[0]
            uv, _, _ = pr.dark_uv(fs, op.get('region', 'n'), op.get('dark_pct', 25))
        piece_c = pr.fcen[pr.fpiece == pr.piece[lp[0]]].mean(0)
        c = pr.WP[ring].mean(0)
        nrm = np.zeros(3)
        for i in range(len(ring)):
            nrm += np.cross(pr.WP[ring[i]] - c, pr.WP[ring[(i + 1) % len(ring)]] - c)
        nrm /= np.linalg.norm(nrm)
        out = c - piece_c
        flip = nrm @ out < 0
        if op.get('facing') == 'in':
            flip = not flip
        n_face = -nrm if flip else nrm
        CUR['pieces'] = (int(pr.piece[lp[0]]),)
        cv = po.add_vertex(c, n_face, uv, mean_jw(pr, [pr.rep[w] for w in ring]), 'centre')
        rv = [po.add_vertex(pr.WP[w], n_face, uv, ('copy', pr.rep[w]) if po is pr else
                            ('jw', pr.J[pr.rep[w]], pr.W[pr.rep[w]])) for w in ring]
        nf = 0
        for i in range(len(ring)):
            tri = (cv, rv[i], rv[(i + 1) % len(ring)])
            po.newt.append(tri[::-1] if flip else tri); nf += 1
        REPORT.append(dict(op=op['name'], kind='cap', prim=po.name, loop=len(lp), faces=nf, centre=[round(float(x), 4) for x in c],
                           uv=[round(float(x), 5) for x in uv], rgb=[round(float(x), 3) for x in C.texel(po.col, uv)[0, :3]]))

tag_kinds(OPS[-1]['op'])
# lining triangles' rest centres (GLB space) for the gates
lin_c, lin_p, lin_k = [], [], []
for name, pr in PR.items():
    if pr.newt:
        allP = np.vstack([pr.P, np.array([v[0] for v in pr.newv])])
        lin_c.append(allP[np.array(pr.newt)].mean(1)); lin_p += [name] * len(pr.newt)
        lin_k += ['rim' if i in pr.strip_ids else k for i, k in enumerate(KINDS[name])]
np.savez(str(Path(dst).with_suffix('')) + '_lining.npz', centre=np.vstack(lin_c) if lin_c else np.zeros((0, 3)),
         prim=np.array(lin_p), kind=np.array(lin_k),
         **{f'vtag_{n}': np.array([f'{a}|{b}|{",".join(map(str, c))}' for a, b, c in q.vtag]) for n, q in PR.items()},
         **{f'nvert_{n}': np.array(len(q.P)) for n, q in PR.items()},
         **{f'piece_{n}': q.piece[q.inv] for n, q in PR.items()})
# ---- write: append rows to each primitive's accessors (existing rows copied byte for byte)
mesh = doc['meshes'][nd['mesh']]
for p in mesh['primitives']:
    name = doc['materials'][p['material']]['name']; pr = PR[name]
    if not pr.newt:
        continue
    at = p['attributes']; nv = len(pr.newv)
    newP = np.array([v[0] for v in pr.newv], np.float32); newN = np.array([v[1] for v in pr.newv], np.float32)
    newN /= np.maximum(np.linalg.norm(newN, axis=1, keepdims=True), 1e-12)
    newUV = np.array([v[2] for v in pr.newv], np.float32)
    rawJ = G.raw_rows(doc, binary, at['JOINTS_0']); rawW = G.raw_rows(doc, binary, at['WEIGHTS_0'])
    jt = {5121: np.uint8, 5123: np.uint16}[doc['accessors'][at['JOINTS_0']]['componentType']]
    assert doc['accessors'][at['WEIGHTS_0']]['componentType'] == 5126
    newJ, newW = [], []
    for v in pr.newv:
        if v[3][0] == 'copy':
            newJ.append(rawJ[v[3][1]]); newW.append(rawW[v[3][1]])
        else:
            newJ.append(np.frombuffer(v[3][1].astype(jt).tobytes(), np.uint8))
            newW.append(np.frombuffer(v[3][2].astype(np.float32).tobytes(), np.uint8))
    rows = {'POSITION': newP.view(np.uint8).reshape(nv, -1), 'NORMAL': newN.view(np.uint8).reshape(nv, -1),
            'TEXCOORD_0': newUV.view(np.uint8).reshape(nv, -1), 'JOINTS_0': np.array(newJ), 'WEIGHTS_0': np.array(newW)}
    for sem, i in list(at.items()):
        old = G.raw_rows(doc, binary, i)
        at[sem] = G.append(doc, binary, doc['accessors'][i], np.vstack([old, rows[sem]]))
        G.set_minmax(doc, binary, at[sem])
    T0 = G.acc(doc, bytes(binary), p['indices']).reshape(-1).astype(np.int64)
    T = np.concatenate([T0, np.array(pr.newt, np.int64).reshape(-1)])
    ct = doc['accessors'][p['indices']]['componentType']; assert T.max() < 65536 or ct == 5125
    p['indices'] = G.append(doc, binary, {'componentType': ct, 'type': 'SCALAR'},
                            T.astype(np.uint16 if ct == 5123 else np.uint32).reshape(-1, 1))
    REPORT.append(dict(prim=name, new_vertices=nv, new_triangles=len(pr.newt), triangles=len(T) // 3))
mesh.pop('extras', None)
keep = sorted({n['mesh'] for n in doc['nodes'] if 'mesh' in n}); mmap = {o: k for k, o in enumerate(keep)}
doc['meshes'] = [doc['meshes'][i] for i in keep]
for n in doc['nodes']:
    if 'mesh' in n:
        n['mesh'] = mmap[n['mesh']]
doc, binary = G.compact(doc, binary)
G.write(dst, doc, binary)
json.dump(REPORT, open(repf, 'w'), indent=1)
for r in REPORT:
    print('LINE', json.dumps(r))
