"""Removes the Mage's moustache piece from every LOD and shadow mesh of a texture-pass GLB (built by apply_layout.py
from a closeup_fix.py map set painted with moustache=flat or bare), user request 2026-11-01.

- The moustache is its own connected component under the nose in LOD0 (107 triangles), LOD1 (23) and LOD2 (4); LOD3
  has none. Each shadow mesh mirrors its LOD. The component is found per mesh by connectivity (welded by position) and
  its triangles are dropped.
- The face under it has one small opening (a 5-vertex loop, 5-7 mm, in LOD0 and LOD1). It is closed with a fan of
  triangles over the loop's own vertices, wound like the surrounding faces; the fill's corners copy the loop
  vertices' normal, joints and weights, and their UVs are a front projection into the painted hole-fill patch.
- LOD0 eyeballs take UVs in their own 64-px patches (planar along each eye's axis, frames from closeup_fix.py).
- LOD1 UVs are projected again per chart from the new LOD0 (as apply_layout.py), so nothing on LOD1 samples the
  removed moustache's texels; LOD2/LOD3 keep their UVs and their maps are transferred again from the new LOD0.
- Vertex buffers are rebuilt from the kept corners (unused vertices dropped); every other part of the GLB is carried
  over unchanged.

Usage: remove_moustache.py <in glb> <eyes json> <out glb> [report json]"""
import json
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parents[1]
CREATURES = HERE.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(CREATURES / 'claude_shared'))
from glb import Glb, png  # noqa: E402
import texture_quality as TQ  # noqa: E402
import apply_layout as AL  # noqa: E402
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(CREATURES / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

S = 2048
PATCHES = json.load(open(HERE / 'work' / 'nomoustache' / 'patches.json'))
FILL_BOX = (-0.0135, 0.0005, 1.4515, 1.4655)          # as closeup_fix.py


def welded(P):
    _, w = np.unique(P.round(5), axis=0, return_inverse=True)
    return w.ravel()


def components(F, w):
    W = w[F]
    n = int(w.max()) + 1
    _, part = connected_components(coo_matrix((np.ones(3 * len(F)), (W.ravel(), np.roll(W, 1, 1).ravel())),
                                              shape=(n, n)), directed=False)
    return part[W[:, 0]]


def moustache_faces(P, F):
    w = welded(P)
    fp = components(F, w)
    c = P[F].mean(1)
    out = np.zeros(len(F), bool)
    for k in np.unique(fp):
        s = fp == k
        m = c[s].mean(0)
        if 1.44 < m[1] < 1.47 and abs(m[0]) < 0.02 and m[2] > 0.11 and s.sum() < 200:
            out |= s
    return out


def eye_faces(P, F):
    w = welded(P)
    fp = components(F, w)
    c = P[F].mean(1)
    found = {}
    for k in np.unique(fp):
        s = fp == k
        m = c[s].mean(0)
        if 1.46 < m[1] < 1.52 and m[2] > 0.08 and 0.008 < abs(m[0]) < 0.03 and s.sum() <= 100:
            found['eye_left_x_neg' if m[0] < 0 else 'eye_right_x_pos'] = s
    return found


def fill_hole(P, F, keep):
    """Fan triangles closing the small boundary loop under the nose; returns (tri corner vertex ids (n,3))."""
    w = welded(P)
    Fk = F[keep]
    W = w[Fk]
    half = Counter()
    for t in W:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            half[(a, b)] += 1
    rev = {}
    for (a, b) in half:
        if (b, a) not in half:
            rev[b] = a                                   # fill edge b -> a reverses the boundary half-edge a -> b
    # one vertex entry per welded id, from the kept triangles
    rep = {}
    for t, f in zip(W, Fk):
        for wi, vi in zip(t, f):
            rep.setdefault(wi, vi)
    wpos = {wi: P[vi] for wi, vi in rep.items()}
    loops, seen = [], set()
    for v0 in rev:
        if v0 in seen:
            continue
        loop, v = [], v0
        while v not in seen and v in rev:
            seen.add(v)
            loop.append(v)
            v = rev[v]
        if v == v0 and 3 <= len(loop) <= 8:
            p = np.array([wpos[q] for q in loop])
            m = p.mean(0)
            if abs(m[0]) < 0.02 and 1.45 < m[1] < 1.465 and m[2] > 0.12 and np.ptp(p, 0).max() < 0.012:
                loops.append(loop)
    tris = []
    for loop in loops:
        for i in range(1, len(loop) - 1):
            tris.append([rep[loop[0]], rep[loop[i]], rep[loop[i + 1]]])
    return np.array(tris, np.int64).reshape(-1, 3), len(loops)


def fill_uv(points):
    x0, y0, side = PATCHES['hole_fill']
    u = (x0 + (points[..., 0] - FILL_BOX[0]) / (FILL_BOX[1] - FILL_BOX[0]) * side) / S
    v = (y0 + (FILL_BOX[3] - points[..., 1]) / (FILL_BOX[3] - FILL_BOX[2]) * side) / S
    return np.stack([u, v], -1)


def eye_uv(points, frame):
    c, R = np.array(frame['centre']), frame['radius']
    e1, e2 = np.array(frame['e1']), np.array(frame['e2'])
    x0, y0, side = frame['box']
    a = np.clip((points - c) @ e1 / R, -0.98, 0.98)
    b = np.clip((points - c) @ e2 / R, -0.98, 0.98)
    return np.stack([(x0 + (a * 0.5 + 0.5) * side) / S, (y0 + (0.5 - b * 0.5) * side) / S], -1)


def rebuild(g, mesh_index, corner_src, corner_uv):
    pr = g.doc['meshes'][mesh_index]['primitives'][0]
    srcv, uv, idx = AL.split_vertices(corner_src, corner_uv)
    for name, acc in pr['attributes'].items():
        data = g.accessor(acc)
        g.set_accessor(acc, uv if name == 'TEXCOORD_0' else data[srcv])
    g.set_accessor(pr['indices'], idx.reshape(-1))
    return len(srcv)


def main():
    src, eyes_path, dst = sys.argv[1:4]
    frames = {f['patch']: f for f in json.load(open(eyes_path))}
    g = Glb(src)
    doc = g.doc
    lod0 = doc['meshes'][0]
    lods = [0] + lod0['extras']['openyamm_lods']
    shadows = lod0['extras']['openyamm_shadow_lods']
    report = {}

    def prim(mi):
        pr = doc['meshes'][mi]['primitives'][0]
        return (g.accessor(pr['attributes']['POSITION']).astype(np.float64),
                g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64),
                g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64))

    # ---- LOD0 and its shadow: removal, fill, eye UVs
    new0 = None
    for mi in (0, shadows[0]):
        P, U, F = prim(mi)
        must = moustache_faces(P, F)
        keep = ~must
        fill, nloops = fill_hole(P, F, keep)
        corners = np.concatenate([F[keep], fill])
        cuv = np.concatenate([U[F[keep]], fill_uv(P[fill])])
        kept_ids = np.nonzero(keep)[0]
        for name, sel in eye_faces(P, F).items():
            rows = np.nonzero(sel[kept_ids])[0]
            cuv[rows] = eye_uv(P[F[kept_ids[rows]]], frames[name])
        if mi == 0:
            new0 = (P, corners, cuv)
        report[doc['meshes'][mi]['name']] = {'removed': int(must.sum()), 'fill_triangles': int(len(fill)),
                                              'fill_loops': nloops, 'triangles': int(len(corners))}
        report[doc['meshes'][mi]['name']]['vertices'] = rebuild(g, mi, corners, cuv)

    # ---- LOD1 and its shadow: removal, fill, UVs projected again from the new LOD0 (same triangle order in both)
    P0, F0, uv0 = new0
    chart = TQ.islands(uv0, P0[F0])
    P1, _, F1 = prim(lods[1])
    must1 = moustache_faces(P1, F1)
    fill1, nl1 = fill_hole(P1, F1, ~must1)
    corners1 = np.concatenate([F1[~must1], fill1])
    uv1, worst = AL.lod1_uvs(P0, F0, uv0, chart, P1, corners1, None)
    report['lod1_projection_worst_mm'] = round(worst * 1000, 2)
    Ps, _, Fs = prim(shadows[1])
    must_s = moustache_faces(Ps, Fs)
    assert (must_s == must1).all(), 'LOD1 shadow moustache triangles differ from LOD1'
    fill_s, nls = fill_hole(Ps, Fs, ~must_s)
    assert len(fill_s) == len(fill1)
    corners_s = np.concatenate([Fs[~must_s], fill_s])
    for mi, corners, n_removed, n_fill, nl in ((lods[1], corners1, must1.sum(), len(fill1), nl1),
                                              (shadows[1], corners_s, must_s.sum(), len(fill_s), nls)):
        report[doc['meshes'][mi]['name']] = {'removed': int(n_removed), 'fill_triangles': int(n_fill),
                                              'fill_loops': nl, 'triangles': int(len(corners)),
                                              'vertices': rebuild(g, mi, corners, uv1)}

    # ---- LOD2/LOD3 and shadows: removal only (no opening under the moustache there)
    for mi in (lods[2], lods[3], shadows[2], shadows[3]):
        P, U, F = prim(mi)
        must = moustache_faces(P, F)
        keep = ~must
        fill, nl = fill_hole(P, F, keep)
        assert len(fill) == 0, f'unexpected opening in {doc["meshes"][mi]["name"]}'
        report[doc['meshes'][mi]['name']] = {'removed': int(must.sum()), 'fill_triangles': 0, 'fill_loops': 0,
                                              'triangles': int(keep.sum()),
                                              'vertices': rebuild(g, mi, F[keep], U[F[keep]])}
    g.save(dst)

    # ---- far LODs: maps again from the new LOD0, on their own geometry and UVs
    g = Glb(dst)
    doc = g.doc
    for level in (2, 3):
        pr = doc['meshes'][lods[level]]['primitives'][0]
        corners = TT.source_faces(doc, g.bin, pr)
        uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
        mat = doc['materials'][pr['material']]
        kinds = TT.material_maps(mat)
        size = g.image(doc['textures'][kinds['basecolor']]['source']).size[0]
        maps, coverage = TT.transfer(doc, g.bin, doc['meshes'][0]['primitives'][0], pr, corners, uv[corners], size)
        report[f'LOD{level}_transfer_coverage'] = round(float(coverage), 3)
        for kind, picture in maps.items():
            g.set_image(doc['textures'][kinds[kind]]['source'], png(picture))
    g.save(dst)
    print('REMOVED', json.dumps(report))
    if len(sys.argv) > 4:
        json.dump(report, open(sys.argv[4], 'w'), indent=1)


if __name__ == '__main__':
    main()
