#!/usr/bin/env python3
"""Linings behind open garment rims, added to an installed GLB without Blender (2026-11-05, MM9 lining batch,
devdocs/mm9_rework/overnight/LINING_BRIEF_20261105.md). PeasantDM2's rim_lining.py technique on the GLB's own meshes:

For every rim spec and every visual LOD mesh (the node's mesh and its openyamm_lods): the open boundary loops of the spec's
primitive (vertices welded by position) whose vertices are mostly (>= 60 %) weighted to one of `bones` and whose centre lies
in the spec's box are selected; loops that coincide with another primitive's open rim (the head/body seam) are skipped.
The band = faces of the loop's piece reachable from the loop through faces whose corners all lie within `depth` (m) of the
loop's vertices (and, with `band_bones`, are weighted mostly to those bones). The band's welded vertices are duplicated
`offset` behind themselves along the negated area-weighted band normal (at most 40 % of the distance to any other face that
direction meets within 2 cm), the band's triangles are copied onto them with reversed winding, and every selected loop
edge is joined to its twin by a two-triangle rim strip facing out of the garment. Lining and strip vertices copy the joints
and weights of the vertex they line (strip corners on the rim sit exactly on the original vertex), so the inside follows
the outside under every pose; their UV is one dark texel of the band's own paint (the darkest, flattest 16x16 window among
the band's face centres); normals are the negated original normals (strip: its face normal).

Only appended data: every existing vertex (position, normal, UV, joints, weights), triangle, image, material, skin and clip
keeps its bytes; the shadow meshes are left as they are (a lining adds nothing to a silhouette: DM2 dropped them there).
Usage: glb_lining.py <in glb> <out glb> <spec json> [report json]
spec: {"lods": [0, 1, 2, 3], "rims": [{"name", "prim", "bones": [...], "box": {"y": [lo, hi], "x": [lo, hi], ...} (glTF),
       "min_edges": [lod0, lod1, lod2, lod3], "depth", "band_bones": [...] (optional), "offset" 0.003, "skip_inner" false,
       "inner_offset" 0.0005, "texel_from": [u, v] (optional fixed texel), "lods": [...] (optional subset),
       "depth_by_bone": {"Head": 0.05} (optional: a shorter band where the vertex's dominant bone matches),
       "holes": {"gate": see_through json with face_holes, "counts": [faces per primitive of that GLB] (or "gates": a list of
                 such {"gate", "counts"}), "min_sum", "ring" 1,
                 "near_m" 0.006} (optional: LOD0 band limited to the faces the gate found holes on, grown by ring; a coarser
                 LOD's face joins when at least half of its area lies within near_m of that LOD0 band), "rim": true (false: no rim strips),
       "holes.mode": "limit" (band = depth band & hole faces) | "add" (depth band | hole faces within
       holes.depth of the rim), "flood": true (false: band faces need not connect to the rim), "texel_of": another spec's name (reuse its texel), "dark_pct" 15, "own_uv": false (true: the lining keeps the band's own UVs instead of one dark texel), "max_piece_share": 1.0 (loops of a piece holding a larger share of the primitive's faces are left out)}]}"""
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack  # noqa: E402
from bglbio import acc  # noqa: E402

IN, OUT, SPEC = sys.argv[1:4]
REP = sys.argv[4] if len(sys.argv) > 4 else None
spec = json.load(open(SPEC))
doc, binary = glbpack.read(IN)
node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
lod_meshes = [node['mesh']] + doc['meshes'][node['mesh']].get('extras', {}).get('openyamm_lods', [])
joints = doc['skins'][node['skin']]['joints']
bname = [doc['nodes'][j]['name'] for j in joints]


def image_of(material, key):
    m = doc['materials'][material]
    t = (m['pbrMetallicRoughness'] if key == 'baseColorTexture' else m)[key]['index']
    im = doc['images'][doc['textures'][t]['source']]
    v = doc['bufferViews'][im['bufferView']]
    raw = bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])
    return np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'), np.float32) / 255.0


def weld(P):
    _, inv = np.unique(np.round(P, 5), axis=0, return_inverse=True)
    return inv.ravel()


def boundary_loops(TW):
    cnt = defaultdict(int); owner = {}
    for fi, t in enumerate(TW):
        for i in range(3):
            e = (t[i], t[(i + 1) % 3])
            k = tuple(sorted(e)); cnt[k] += 1; owner[k] = (fi, e)
    bnd = [k for k, c in cnt.items() if c == 1]
    adj = defaultdict(list)
    for e in bnd:
        adj[e[0]].append(e); adj[e[1]].append(e)
    seen, loops = set(), []
    for e in bnd:
        if e in seen:
            continue
        st, lp = [e], []; seen.add(e)
        while st:
            x = st.pop(); lp.append(owner[x])
            for v in x:
                for y in adj[v]:
                    if y not in seen:
                        seen.add(y); st.append(y)
        loops.append(lp)          # [(face, (a, b) in the face's winding order)]
    return loops, {k for k in bnd}


def ray_hits(O, D, tri, maxd):
    """Nearest hit distance (inf if none within maxd) of rays O + t D against triangles tri (m, 3, 3)."""
    out = np.full(len(O), np.inf)
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    for i in range(len(O)):
        p = np.cross(D[i], e2); det = (e1 * p).sum(1); ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        s = O[i] - v0; u = (s * p).sum(1) * inv
        q = np.cross(s, e1); v = (D[i] * q).sum(1) * inv; t = (e2 * q).sum(1) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & (t < maxd)
        if h.any():
            out[i] = t[h].min()
    return out


def coverage(img, uv, T):
    from PIL import ImageDraw
    H, W = img.shape[:2]
    m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    for t in T:
        dr.polygon([(uv[i, 0] * W, uv[i, 1] * H) for i in t], fill=255, outline=255)
    return np.asarray(m) > 0


def pick_texel(img, uvs, cov, pct=15, half=4):
    """One texel for a band's lining: a flat 8x8 window on painted chart whose mean luminance is closest to the band's own
    dark tone (the pct-th percentile of its face-centre luminance, at least 0.03: never the black of an outline). A lining's
    UVs are one point, so the GPU samples mip 0 bilinearly there: only the window's few texels matter."""
    H, W = img.shape[:2]
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    cen = [lum[min(H - 1, int(v * H)), min(W - 1, int(u * W))] for u, v in uvs]
    target = max(0.03, float(np.percentile(cen, pct)))
    best, buv = 9.0, None
    for u, v in uvs:
        x, y = int(np.clip(u * W, half, W - half - 1)), int(np.clip(v * H, half, H - half - 1))   # glTF uv: v from the top row
        win = lum[y - half:y + half, x - half:x + half]
        if cov[y - half:y + half, x - half:x + half].mean() < 1.0:      # on painted chart only (the gutters are black)
            continue
        score = abs(win.mean() - target) + 2.0 * win.std()
        if score < best:
            best, buv = score, ((x + 0.5) / W, (y + 0.5) / H)
    x, y = int(buv[0] * W), int(buv[1] * H)
    return buv, img[y, x].tolist(), round(float(best), 4)


SEAM_M = 0.003     # a loop whose vertices mostly lie on another primitive (the head/body seam on the collar cloth) is closed
report = {'input': IN, 'lods': {}}
lod0_band, lod0_texel = {}, {}
_b = [(i / 4, j / 4) for i in range(5) for j in range(5 - i)]
BARY = np.array([(a, b, 1 - a - b) for a, b in _b])          # 15 barycentric samples per face
new_prims = {}
for li, mi in enumerate(lod_meshes):
    if li not in spec.get('lods', [0, 1, 2, 3]):
        continue
    prims = doc['meshes'][mi]['primitives']
    data = []
    for p in prims:
        a = p['attributes']
        P = acc(doc, binary, a['POSITION']).astype(np.float64)
        d = dict(P=P, N=acc(doc, binary, a['NORMAL']).astype(np.float64), J=acc(doc, binary, a['JOINTS_0']),
                 W=acc(doc, binary, a['WEIGHTS_0']), T=acc(doc, binary, p['indices']).reshape(-1, 3).astype(np.int64))
        d['w'] = weld(P); d['TW'] = d['w'][d['T']]
        n = d['w'].max() + 1
        d['rep'] = np.zeros(n, np.int64); d['rep'][d['w'][::-1]] = np.arange(len(P))[::-1]
        d['Pw'] = P[d['rep']]
        dom = d['J'][np.arange(len(P)), np.argmax(d['W'], 1)]
        d['dom'] = np.array([bname[j] for j in dom])[d['rep']]
        r = np.r_[d['TW'][:, 0], d['TW'][:, 1]]; c = np.r_[d['TW'][:, 1], d['TW'][:, 2]]
        d['comp'] = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1]
        d['loops'], _ = boundary_loops(d['TW'])
        d['img'] = image_of(p['material'], 'baseColorTexture')
        d['uv'] = acc(doc, binary, a['TEXCOORD_0']).astype(np.float64)
        d['new'] = dict(P=[], N=[], UV=[], J=[], W=[], T=[])
        data.append(d)
    allP = np.concatenate([d['P'] for d in data])
    allT = np.concatenate([d['T'] + sum(len(e['P']) for e in data[:k]) for k, d in enumerate(data)])
    alltri = allP[allT]
    rim_pts = {k: d['Pw'][np.unique(np.concatenate([[x[1][0], x[1][1]] for lp in d['loops'] for x in lp]))]
               for k, d in enumerate(data)}
    lrep = report['lods'][li] = {}
    for rs in spec['rims']:
        if li not in rs.get('lods', [0, 1, 2, 3]):
            continue
        k = rs['prim']; d = data[k]; nV = len(d['P'])
        min_edges = rs.get('min_edges', [4, 3, 3, 3])[li]
        others = [cKDTree(data[o]['Pw']) for o in range(len(data)) if o != k]
        sel = []
        for lp in d['loops']:
            vs = np.unique([v for _, e in lp for v in e])
            hits = sum(any(b in d['dom'][v] for b in rs['bones']) for v in vs)
            c = d['Pw'][vs].mean(0)
            box = rs.get('box', {})
            inbox = all(box[ax][0] <= c['xyz'.index(ax)] <= box[ax][1] for ax in box)
            seam = max([(t.query(d['Pw'][vs])[0] < SEAM_M).mean() for t in others] + [0]) > 0.6
            share = (d['comp'][d['TW'][:, 0]] == d['comp'][vs[0]]).mean()
            if hits >= 0.6 * len(vs) and inbox and len(lp) >= min_edges and not seam and share <= rs.get('max_piece_share', 1.0):
                sel.append(lp)
        if not sel:
            lrep[rs['name']] = {'loops': 0}
            continue
        loopv = np.unique([v for lp in sel for _, e in lp for v in e])
        kd = cKDTree(d['Pw'][loopv])
        dist = kd.query(d['Pw'])[0]
        dep = np.full(len(dist), rs['depth'])
        for b, dv in rs.get('depth_by_bone', {}).items():      # e.g. {"Head": 0.05}: the scalp only near the rim
            dep[np.array([b in x for x in d['dom']])] = dv
        ok_v = dist < dep
        if rs.get('band_bones'):
            ok_v &= np.array([any(b in x for b in rs['band_bones']) for x in d['dom']])
        comps = {d['comp'][v] for v in loopv}
        same = np.isin(d['comp'][d['TW'][:, 0]], list(comps))
        okf = ok_v[d['TW']].all(1) & same
        fcen = d['P'][d['T']].mean(1)
        hmode = rs.get('holes', {}).get('mode', 'limit')
        reach = (dist < rs.get('holes', {}).get('depth', 9.0))[d['TW']].all(1) & same
        if rs.get('holes') and li == 0:
            # only faces the see-through gate found holes on (summed hole pixels >= min_sum), grown by `ring` edge rings
            h = rs['holes']
            hot = np.zeros(len(d['T']), bool)
            # one or more gate runs (installed, earlier candidates): each run's face index = its GLB's primitive offset + face;
            # a candidate's faces past the input's own count are its linings and are ignored
            for g in h.get('gates', [{'gate': h.get('gate'), 'counts': h.get('counts')}]):
                off = sum(g['counts'][:k])
                for key, (sm, mx) in json.load(open(g['gate']))['face_holes'].items():
                    f = int(key) - off
                    if 0 <= f < len(d['T']) and f < g['counts'][k] and sm >= h['min_sum']:
                        hot[f] = True
            for _ in range(h.get('ring', 1)):
                vv = np.zeros(len(d['Pw']), bool); vv[d['TW'][hot].ravel()] = True
                hot |= vv[d['TW']].any(1)
            okf = okf & hot if hmode == 'limit' else okf | (hot & reach)     # add: the depth band plus hole faces further out
        if rs.get('holes') and li > 0:
            # a coarser LOD: faces near the LOD0 band (centroid within near_m of an LOD0 band face centroid)
            # a coarser LOD face takes the lining when at least half of its area lies within near_m of the LOD0 band
            # (samples on the face against samples on the LOD0 band faces): the same lined area at every LOD
            tri = d['P'][d['T']]
            samp = np.einsum('sk,fkc->fsc', BARY, tri)
            bp, bn = lod0_band.get(rs['name'], (np.zeros((1, 3)) + 99, np.zeros((1, 3))))
            dd, ii = cKDTree(bp).query(samp.reshape(-1, 3))
            fnl = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            fnl /= np.maximum(np.linalg.norm(fnl, axis=1, keepdims=True), 1e-12)
            agree = (bn[ii].reshape(len(tri), -1, 3) * fnl[:, None, :]).sum(2) > 0.5     # same side of the same layer
            nm = rs['holes'].get('near_m', 0.006)
            nm = nm[li] if isinstance(nm, list) else nm          # per LOD: coarser LODs sit further from the LOD0 surface
            near = ((dd.reshape(len(tri), -1) < nm) & agree).mean(1) >= 0.5
            okf = okf & near if hmode == 'limit' else okf | (near & reach)
        # flood from the loop faces through okf faces sharing an edge
        e2f = defaultdict(list)
        for fi, t in enumerate(d['TW']):
            for i in range(3):
                e2f[tuple(sorted((t[i], t[(i + 1) % 3])))].append(fi)
        band, st = set(), [f for lp in sel for f, _ in lp]
        if not rs.get('flood', True):
            band, st = set(np.nonzero(okf)[0].tolist()), []      # every band face, connected to a rim or not
        while st:
            f = st.pop()
            if f in band or not okf[f]:
                continue
            band.add(f)
            t = d['TW'][f]
            for i in range(3):
                st += e2f[tuple(sorted((t[i], t[(i + 1) % 3])))]
        band = np.array(sorted(band), dtype=np.int64)
        if not len(band):
            lrep[rs['name']] = {'loops': len(sel), 'band_faces': 0}
            continue
        if li == 0:
            bt = d['P'][d['T'][band]]
            bnl = np.cross(bt[:, 1] - bt[:, 0], bt[:, 2] - bt[:, 0])
            bnl /= np.maximum(np.linalg.norm(bnl, axis=1, keepdims=True), 1e-12)
            lod0_band[rs['name']] = (np.einsum('sk,fkc->fsc', BARY, bt).reshape(-1, 3), np.repeat(bnl, len(BARY), 0))
        BT = d['TW'][band]
        # area-weighted band normals per welded vertex
        tri = d['Pw'][BT]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nw = np.zeros((len(d['Pw']), 3))
        for i in range(3):
            np.add.at(nw, BT[:, i], fn)
        bv = np.unique(BT)
        nrm = nw[bv] / np.maximum(np.linalg.norm(nw[bv], axis=1, keepdims=True), 1e-12)
        offs = np.full(len(bv), rs.get('offset', 0.003))
        if rs.get('skip_inner'):
            pass        # not needed on this body (no inner cloth layer in the lined bands)
        # collision cap: another face along the inward direction within 2 cm -> at most 40 % of that distance
        own = np.zeros(len(allT), bool)
        base = sum(len(e['P']) for e in data[:k])
        vset = set(bv.tolist())
        # faces touching the vertex itself are not obstacles
        hitd = ray_hits(d['Pw'][bv] - nrm * 1e-4, -nrm, alltri, 0.02)
        capped = int((0.4 * hitd < offs).sum())
        offs = np.minimum(offs, 0.4 * hitd)
        twinP = d['Pw'][bv] - nrm * offs[:, None]
        # band paint texel
        fuv = d['uv'][d['T'][band]].mean(1)
        if li > 0 and rs['name'] in lod0_texel:
            tuv, trgb, tsc = lod0_texel[rs['name']]          # every LOD lines with the LOD0 texel (same image)
        elif rs.get('texel_of') in lod0_texel:
            tuv, trgb, tsc = lod0_texel[rs['texel_of']]      # the same garment on the other side: one lining colour
        elif rs.get('texel_from'):
            tuv = tuple(rs['texel_from']); trgb = d['img'][int(tuv[1] * d['img'].shape[0]), int(tuv[0] * d['img'].shape[1])].tolist(); tsc = None
        else:
            if 'cov' not in d:
                d['cov'] = coverage(d['img'], d['uv'], d['T'])
            tuv, trgb, tsc = pick_texel(d['img'], fuv, d['cov'], rs.get('dark_pct', 15))
        if li == 0:
            lod0_texel[rs['name']] = (tuv, trgb, tsc)
        new = d['new']; start = nV + len(new['P'])
        tw = {int(v): start + i for i, v in enumerate(bv)}
        for i, v in enumerate(bv):
            r0 = d['rep'][v]
            new['P'].append(twinP[i]); new['N'].append(-nrm[i]); new['UV'].append(tuv)
            new['J'].append(d['J'][r0]); new['W'].append(d['W'][r0])
        if rs.get('own_uv'):
            # own-UV twins (Sven's hair route): one twin per original split vertex of the band, at its welded vertex's
            # offset position, keeping that vertex's own UV, so the underside reads as the garment's own paint; the dark
            # per-welded-vertex twins above stay only as the strips' inner corners
            bpos = {int(v): i for i, v in enumerate(bv)}
            ot = {}
            for v in np.unique(d['T'][band]):
                i = bpos[int(d['w'][v])]
                ot[int(v)] = nV + len(new['P'])
                new['P'].append(twinP[i]); new['N'].append(-nrm[i]); new['UV'].append(tuple(d['uv'][v]))
                new['J'].append(d['J'][v]); new['W'].append(d['W'][v])
            for t in d['T'][band]:
                new['T'].append([ot[t[0]], ot[t[2]], ot[t[1]]]); new.setdefault('C', []).append('L')
        else:
            for t in BT:
                new['T'].append([tw[t[0]], tw[t[2]], tw[t[1]]]); new.setdefault('C', []).append('L')
        nlin = len(BT)
        # rim strips: loop edge (a, b) in its face's winding -> outward strip a, b, b' / a, b', a'  (reversed winding of the
        # face's own continuation: the strip faces away from the face across the edge)
        bset = set(band.tolist()) if rs.get('rim', True) else set(); nrim = 0
        for lp in sel:
            for f, (a, b) in lp:
                if f not in bset:
                    continue
                ia, ib = len(new['P']) + nV, len(new['P']) + nV + 1
                ra, rb = d['rep'][a], d['rep'][b]
                pa, pb = d['Pw'][a], d['Pw'][b]
                # strip normal: from the face centre across the edge
                fc = d['Pw'][d['TW'][f]].mean(0); mid = (pa + pb) / 2
                sn = mid - fc; sn -= np.dot(sn, pb - pa) / max(np.dot(pb - pa, pb - pa), 1e-12) * (pb - pa)
                sn /= max(np.linalg.norm(sn), 1e-12)
                for v, r in ((a, ra), (b, rb)):
                    new['P'].append(d['Pw'][v]); new['N'].append(sn); new['UV'].append(tuv)
                    new['J'].append(d['J'][r]); new['W'].append(d['W'][r])
                a2, b2 = tw[a], tw[b]
                for tri3 in ((ia, ib, b2), (ia, b2, a2)):
                    # orient: geometric normal along sn
                    q = [new['P'][x - nV] for x in tri3]
                    gn = np.cross(q[1] - q[0], q[2] - q[0])
                    new['T'].append(list(tri3) if np.dot(gn, sn) >= 0 else [tri3[0], tri3[2], tri3[1]])
                    new.setdefault('C', []).append('S')
                    nrim += 1
        lrep[rs['name']] = {'loops': len(sel), 'loop_edges': [len(lp) for lp in sel],
                            'loop_centres': [np.round(d['Pw'][np.unique([v for _, e in lp for v in e])].mean(0), 3).tolist()
                                             for lp in sel],
                            'band_faces': int(len(band)), 'lining_tris': nlin, 'rim_tris': nrim, 'offset_capped': capped,
                            'texel_uv': [round(x, 5) for x in tuv], 'texel_rgb': [round(x, 3) for x in trgb], 'texel_score': tsc}
    new_prims[mi] = data
    for k, d in enumerate(data):
        lrep.setdefault('_added', {})[k] = {'verts': len(d['new']['P']), 'tris': len(d['new']['T']),
                                            'classes': ''.join(d['new'].get('C', []))}   # per added triangle: L lining, S strip

# write: each changed primitive gets new accessors = original raw bytes + appended rows of the same component type
for mi, data in new_prims.items():
    for p, d in zip(doc['meshes'][mi]['primitives'], data):
        nw = d['new']
        if not nw['T']:
            continue
        a = p['attributes']
        vals = {'POSITION': np.array(nw['P'], np.float32), 'NORMAL': np.array(nw['N'], np.float32),
                'TEXCOORD_0': np.array(nw['UV'], np.float32), 'JOINTS_0': np.array(nw['J']), 'WEIGHTS_0': np.array(nw['W'])}
        for key, idx in list(a.items()):
            src = doc['accessors'][idx]
            old = glbpack.raw_rows(doc, binary, idx)
            dt = {5126: np.float32, 5121: np.uint8, 5123: np.uint16}[src['componentType']]
            if src.get('normalized'):
                raise ValueError('normalized attributes are not handled')
            add = np.ascontiguousarray(vals[key].astype(dt)).view(np.uint8).reshape(len(vals[key]), -1)
            a[key] = glbpack.append(doc, binary, src, np.concatenate([old, add]))
            glbpack.set_minmax(doc, binary, a[key])
        src = doc['accessors'][p['indices']]
        old = acc(doc, binary, p['indices']).ravel()
        idx = np.concatenate([old.astype(np.int64), np.array(nw['T'], np.int64).ravel()])
        dt = np.uint16 if idx.max() < 65535 else np.uint32
        tmpl = dict(src, componentType=5123 if dt is np.uint16 else 5125)
        p['indices'] = glbpack.append(doc, binary, tmpl, idx.astype(dt).view(np.uint8).reshape(len(idx), -1))
doc, binary = glbpack.compact(doc, binary)
glbpack.write(OUT, doc, binary)
tot = {li: sum(v['tris'] for v in r['_added'].values()) for li, r in report['lods'].items()}
report['added_tris'] = tot
print('LINING', json.dumps(tot))
for li, r in report['lods'].items():
    for n, x in r.items():
        if n != '_added':
            print(' LOD', li, n, json.dumps({k: x[k] for k in x if k in ('loops', 'loop_edges', 'band_faces', 'lining_tris',
                                                                           'rim_tris', 'offset_capped', 'texel_rgb')}))
if REP:
    json.dump(report, open(REP, 'w'), indent=1, default=lambda o: o.tolist() if hasattr(o, 'tolist') else int(o))
