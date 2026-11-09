#!/usr/bin/env python3
"""Build the reduced school from decimated template fish (decimate_tex.py npz files): each template becomes glTF
vertices (one per position and UV wedge). Normals and skin weights come from the reference fish at the closest
surface point facing the same way (source triangles whose normal agrees with the vertex's own), interpolated from
the reference's welded vertices: the source's custom normals and its weights are continuous across its UV seams
(86 small charts, no hard edges), so every wedge copy of a vertex gets the same values and kept vertices their exact
source ones. A UV-chart lookup (the chart holding the wedge UV) only measures texture drift. The template is then copied to all twelve fish with their similarity transforms
(work/fish.npz) and joints offset by 5 per fish, and written into the four LOD primitives of a copy of the source
GLB; every other part of the file (rig, clips, materials, variants, LOD and shadow references) is unchanged, and
unreferenced buffer data is dropped.
Usage: fish_build.py <src glb> <out glb> <lod0 npz> <lod1 npz> <lod2 npz> <lod3 npz> [ref npz for lod1-3]
  LOD0's reference is the source fish; LOD1-3 use the reduced LOD0 template (work/tmpl_lod0.npz, written here)."""
import copy
import struct
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
INFLUENCES = 3                                    # as the source (max 3 nonzero)
UV_TOL = 5e-3                                     # 10 px at 2K: UV a collapse may drift across a seam


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p[:, None] - a[None]
    d00 = (v0 * v0).sum(-1); d01 = (v0 * v1).sum(-1); d11 = (v1 * v1).sum(-1)
    d20 = (v2 * v0).sum(-1); d21 = (v2 * v1).sum(-1); den = d00 * d11 - d01 * d01
    den = np.where(np.abs(den) < 1e-20, 1e-20, den)
    v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den
    return np.stack([1 - v - w, v, w], -1)


def closest_on_tris(p, a, b, c):
    """barycentric of the closest point on each triangle (a, b, c: T x 3) to each query p (Q x 3) -> Q x T x 3"""
    p = p[:, None]; ab, ac, ap = b - a, c - a, p - a
    d1 = (ab * ap).sum(-1); d2 = (ac * ap).sum(-1)
    bp = p - b; d3 = (ab * bp).sum(-1); d4 = (ac * bp).sum(-1)
    cp = p - c; d5 = (ab * cp).sum(-1); d6 = (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc); v = vb / den; w = vc / den
    out = np.stack([1 - v - w, v, w], -1)
    one = lambda *x: np.stack(x, -1) * np.ones_like(out)
    sel = lambda m, val: np.where(m[..., None], val, out)
    t_ab = d1 / np.where(np.abs(d1 - d3) < 1e-30, 1e-30, d1 - d3); t_ac = d2 / np.where(np.abs(d2 - d6) < 1e-30, 1e-30, d2 - d6)
    t_bc = (d4 - d3) / np.where(np.abs((d4 - d3) + (d5 - d6)) < 1e-30, 1e-30, (d4 - d3) + (d5 - d6))
    z = np.zeros_like(d1)
    out = sel((va <= 0) & (d4 - d3 >= 0) & (d5 - d6 >= 0), np.stack([z, 1 - t_bc, t_bc], -1))
    out = sel((vb <= 0) & (d2 >= 0) & (d6 <= 0), np.stack([1 - t_ac, z, t_ac], -1))
    out = sel((vc <= 0) & (d1 >= 0) & (d3 <= 0), np.stack([1 - t_ab, t_ab, z], -1))
    out = sel((d6 >= 0) & (d5 <= d6), one(z, z, z + 1))
    out = sel((d3 >= 0) & (d4 <= d3), one(z, z + 1, z))
    out = sel((d1 <= 0) & (d2 <= 0), one(z + 1, z, z))
    return out


def charts(ref):
    """UV chart of every reference triangle (glTF vertices are split at UV seams, so shared indices = one chart)"""
    import scipy.sparse as sp, scipy.sparse.csgraph as cg
    I = ref['I']; n = len(ref['P']); e = np.concatenate([I[:, [0, 1]], I[:, [1, 2]]])
    return cg.connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)[1][I[:, 0]]


def lookup(ref, pos, uv):
    """per query: (triangle, barycentric) of the reference surface point closest in 3D on the UV chart that holds the
    query's UV (the chart picks the side, fin and mirrored copy; 3D picks the point, so a vertex the collapse moved
    with a slightly drifted UV still takes the weights and normal of where it is). Also returns the UV distance from
    the chart (0 inside) and the UV drift: query UV minus the reference UV at the chosen point."""
    I = ref['I']; ua, ub, uc = (ref['UV'][I[:, k]].astype(np.float64) for k in range(3))
    B = bary(uv.astype(np.float64), ua, ub, uc)
    Bc = np.clip(B, 0, None); Bc /= Bc.sum(-1, keepdims=True)
    uv_err = np.linalg.norm(np.einsum('qtk,tkc->qtc', Bc, np.stack([ua, ub, uc], 1)) - uv[:, None], axis=-1)
    P3 = np.einsum('qtk,tkc->qtc', Bc, ref['P'][I].astype(np.float64))
    d3 = np.linalg.norm(P3 - pos[:, None], axis=-1)
    tu = np.where(uv_err < 1e-4, d3, 10 + uv_err * 100 + d3).argmin(1)
    # candidate charts: every chart with a triangle within UV_TOL of the query UV (else the nearest one)
    ch = charts(ref); nch = ch.max() + 1; q = np.arange(len(tu))
    cand = np.zeros((len(tu), nch), bool)
    for c in range(nch):
        cand[:, c] = (uv_err[:, ch == c] < UV_TOL).any(1)
    cand[q, ch[tu]] = True
    A, Bt, C = (ref['P'][I[:, k]].astype(np.float64) for k in range(3))
    Bp = closest_on_tris(pos.astype(np.float64), A, Bt, C)
    Pp = np.einsum('qtk,tkc->qtc', Bp, np.stack([A, Bt, C], 1)); dist = np.linalg.norm(Pp - pos[:, None], axis=-1)
    dist = np.where(cand[:, ch], dist, np.inf)
    t = dist.argmin(1); b = Bp[q, t]
    drift = np.linalg.norm(np.einsum('qk,qkc->qc', b, np.stack([ua, ub, uc], 1)[t]) - uv, axis=1)
    return t, b, uv_err[q, tu], dist[q, t], drift


def lookup3d(ref, pos, nrm):
    """per query: (triangle, barycentric) of the closest reference surface point among triangles facing the same
    way as the query normal (thin fins: never the other side)"""
    I = ref['I']; A, Bt, C = (ref['P'][I[:, k]].astype(np.float64) for k in range(3))
    fn = np.cross(Bt - A, C - A); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-20
    Bp = closest_on_tris(pos.astype(np.float64), A, Bt, C)
    Pp = np.einsum('qtk,tkc->qtc', Bp, np.stack([A, Bt, C], 1)); dist = np.linalg.norm(Pp - pos[:, None], axis=-1)
    dist = np.where(nrm @ fn.T > 0.2, dist, dist + 1.0)
    t = dist.argmin(1); q = np.arange(len(t))
    return t, Bp[q, t], dist[q, t]


def fix_inside_out(V, F, wuv):
    """reverse closed pieces whose signed volume is negative: MeshLab flattens a thin closed fin (9 cm^3, 11 cm)
    into an inside-out shell at 6-8 triangles in the LODs; the source pieces are all positive"""
    import scipy.sparse as sp, scipy.sparse.csgraph as cg
    e = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    _, lab = cg.connected_components(sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V),) * 2), directed=False)
    F, wuv = F.copy(), wuv.copy()
    for k in np.unique(lab[F[:, 0]]):
        s = lab[F[:, 0]] == k; f = F[s]
        _, cc = np.unique(np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), 1), axis=0, return_counts=True)
        if (cc == 2).all() and (np.cross(V[f[:, 0]], V[f[:, 1]]) * V[f[:, 2]]).sum() < 0:
            F[s] = F[s][:, ::-1]; wuv[s] = wuv[s][:, ::-1]
            print(f'  reversed an inside-out closed piece of {int(s.sum())} triangles')
    return F, wuv


def template(dec, ref):
    """decimated npz -> template glTF arrays with normals and weights from ref"""
    V, F, wuv = dec['verts'], dec['faces'], dec['wuv'].reshape(-1, 3, 2)
    F, wuv = fix_inside_out(V, F, wuv)
    key = {}; verts = []; idx = np.zeros(F.shape, np.int64)
    for i in range(len(F)):
        for k in range(3):
            kk = (int(F[i, k]), round(float(wuv[i, k, 0]), 6), round(float(wuv[i, k, 1]), 6))
            if kk not in key:
                key[kk] = len(verts); verts.append((F[i, k], wuv[i, k]))
            idx[i, k] = key[kk]
    P = V[[v for v, _ in verts]]; UV = np.array([u for _, u in verts])
    _, _, uerr, _, drift = lookup(ref, P, UV)
    # one normal and weight set per welded vertex, from the closest same-facing reference point
    vid = np.array([v for v, _ in verts]); uv_ids, first = np.unique(vid, return_index=True)
    fnr = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fnr)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-20
    t, B, d3 = lookup3d(ref, V[uv_ids], vn[uv_ids])
    I = ref['I'][t]
    Nw = np.einsum('qk,qkc->qc', B, ref['N'][I].astype(np.float64)); Nw /= np.linalg.norm(Nw, axis=1, keepdims=True)
    dense_w = np.zeros((len(uv_ids), 6))
    for k in range(3):
        for s_ in range(4):
            np.add.at(dense_w, (np.arange(len(uv_ids)), ref['J'][I[:, k], s_].astype(int)), B[:, k] * ref['W'][I[:, k], s_])
    pos_of = np.searchsorted(uv_ids, vid)
    N = Nw[pos_of]; dense = dense_w[pos_of]; d3 = d3[pos_of]
    J = np.argsort(-dense, 1)[:, :INFLUENCES]; Wt = np.take_along_axis(dense, J, 1)
    Wt[Wt < 1e-4] = 0; Wt /= Wt.sum(1, keepdims=True); J = np.where(Wt > 0, J, 0)
    J = np.pad(J, ((0, 0), (0, 4 - INFLUENCES))); Wt = np.pad(Wt, ((0, 0), (0, 4 - INFLUENCES)))
    print(f'  template {len(F)} tris {len(P)} verts; UV outside charts max {uerr.max():.1e}; off surface p99 '
          f'{np.percentile(d3, 99) * 1000:.2f} max {d3.max() * 1000:.2f} mm; UV drift p99 {np.percentile(drift, 99) * 2048:.1f} '
          f'max {drift.max() * 2048:.1f} px (2K)')
    return {'P': P.astype(np.float32), 'N': N.astype(np.float32), 'UV': UV.astype(np.float32), 'J': J.astype(np.uint8),
            'W': Wt.astype(np.float32), 'I': idx}


def school(t, fish):
    out = {k: [] for k in ('P', 'N', 'UV', 'J', 'W', 'I')}; n = len(t['P'])
    for k in range(len(fish['S'])):
        s, R, T = fish['S'][k], fish['R'][k], fish['T'][k]
        out['P'].append(s * t['P'] @ R + T); out['N'].append(t['N'] @ R); out['UV'].append(t['UV'])
        out['J'].append(np.where(t['W'] > 0, t['J'] + 5 * k, 0)); out['W'].append(t['W']); out['I'].append(t['I'] + k * n)
    return {k: np.concatenate(v) for k, v in out.items()}


def compact(doc, binary):
    """drop unreferenced accessors and buffer views; rebuild the binary in view order"""
    used_acc = set()
    for m in doc['meshes']:
        for p in m['primitives']:
            used_acc |= set(p['attributes'].values()) | ({p['indices']} if 'indices' in p else set())
            for tg in p.get('targets', []):
                used_acc |= set(tg.values())
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            used_acc.add(s['inverseBindMatrices'])
    for a in doc.get('animations', []):
        for s in a['samplers']:
            used_acc |= {s['input'], s['output']}
    amap = {o: n for n, o in enumerate(sorted(used_acc))}
    used_bv = sorted({doc['accessors'][i]['bufferView'] for i in used_acc} | {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
    bmap = {}; nb = bytearray(); views = []
    for o in used_bv:
        v = copy.deepcopy(doc['bufferViews'][o]); nb.extend(b'\0' * (-len(nb) % 4))
        off = v.get('byteOffset', 0); chunk = binary[off:off + v['byteLength']]
        v['byteOffset'] = len(nb); nb.extend(chunk); bmap[o] = len(views); views.append(v)
    accs = []
    for o in sorted(used_acc):
        a = copy.deepcopy(doc['accessors'][o]); a['bufferView'] = bmap[a['bufferView']]; accs.append(a)
    doc['accessors'], doc['bufferViews'] = accs, views
    for im in doc.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = bmap[im['bufferView']]
    for m in doc['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] = amap[p['indices']]
            if 'targets' in p:
                p['targets'] = [{k: amap[v] for k, v in tg.items()} for tg in p['targets']]
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
    for a in doc.get('animations', []):
        for s in a['samplers']:
            s['input'], s['output'] = amap[s['input']], amap[s['output']]
    return nb


def put(doc, binary, data, ctype, kind, target, minmax=False):
    binary.extend(b'\0' * (-len(binary) % 4))
    raw = data.tobytes(); doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(raw), 'target': target})
    binary.extend(raw)
    a = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': ctype, 'count': len(data), 'type': kind}
    if minmax:
        a['min'] = data.min(0).tolist(); a['max'] = data.max(0).tolist()
    doc['accessors'].append(a); return len(doc['accessors']) - 1


def write_school(src, dst, lods):
    doc, binary = read_glb(Path(src)); binary = bytearray(binary)
    meshes = [doc['nodes'][next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'School')]['mesh']]
    meshes += doc['meshes'][meshes[0]]['extras']['openyamm_lods']
    for mi, s in zip(meshes, lods):
        assert len(s['P']) < 65536
        p = doc['meshes'][mi]['primitives'][0]; at = p['attributes']
        at['POSITION'] = put(doc, binary, s['P'].astype(np.float32), 5126, 'VEC3', 34962, True)
        at['NORMAL'] = put(doc, binary, s['N'].astype(np.float32), 5126, 'VEC3', 34962)
        at['TEXCOORD_0'] = put(doc, binary, s['UV'].astype(np.float32), 5126, 'VEC2', 34962)
        at['JOINTS_0'] = put(doc, binary, s['J'].astype(np.uint8), 5121, 'VEC4', 34962)
        at['WEIGHTS_0'] = put(doc, binary, s['W'].astype(np.float32), 5126, 'VEC4', 34962)
        p['indices'] = put(doc, binary, s['I'].reshape(-1).astype(np.uint16), 5123, 'SCALAR', 34963)
    nb = compact(doc, binary); write_glb(Path(dst), doc, bytes(nb))
    print('WROTE', dst, [len(s['I']) for s in lods], 'tris;', len(nb) >> 10, 'KiB binary')


if __name__ == '__main__':
    src, dst, *npz = sys.argv[1:]
    fish = np.load(HERE / 'work' / 'fish.npz'); ref0 = {k: fish[k] for k in ('P', 'N', 'UV', 'J', 'W', 'I')}
    t0 = template(np.load(npz[0]), ref0); np.savez(HERE / 'work' / 'tmpl_lod0.npz', **t0)
    temps = [t0] + [template(np.load(n), t0) for n in npz[1:4]]
    write_school(src, dst, [school(t, fish) for t in temps])
