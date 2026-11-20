"""PartUV charts with a skin-weight part tree, for uv_atlas.py (charts='partuv'). Runs outside Blender in
claude_shared/partuv_venv (setup in TEXTURE_QUALITY_PASS.md):

    partuv_venv/bin/python -I partuv_charts.py <in.npz> <out.npz> [--threshold 1.25] [--no-pamo]

in.npz: pos (N x 3), tri (M x 3), weights (N x G skin weights; one column of ones when the mesh has none).
out.npz: uv (M x 3 x 2, each chart flattened on its own, unpacked) and chart (M), in the input face order.

PartUV (Wang et al., SIGGRAPH Asia 2025; pip partuv 0.1.2, Apache-2.0) splits a part hierarchy recursively until every
chart flattens (ABF) under the distortion threshold. Its default hierarchy comes from PartField, which is under NVIDIA's
non-commercial licence; this script never imports or runs it. The hierarchy here is Ward agglomerative clustering over
edge-adjacent faces (as PartField's tree is built) on per-face skin weights plus 0.5 x normalised position, so the
parts follow the rig. Only the compiled pipeline (`partuv/_core`) is loaded, by file path, so the package's own
`__init__` (which imports the PartField inference code and torch) never runs.

Non-manifold edges are cut as seams first (corners glued only across edges with exactly two faces), as PartUV's own
preprocessing does; face order is kept. PartUV reorders faces internally: each output face is matched back to its
input triangle by its corner positions. Research and numbers: uv_research_20261111/REPORT.md.
"""
import argparse
import glob
import importlib.machinery
import importlib.util
import os
import sys
import tempfile
from collections import defaultdict

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def load_core():
    spec = importlib.util.find_spec('partuv')
    if spec is None or not spec.submodule_search_locations:
        raise ImportError('partuv is not installed in this environment')
    found = glob.glob(os.path.join(list(spec.submodule_search_locations)[0], '_core*.so'))
    if not found:
        raise ImportError('partuv/_core extension not found')
    loader = importlib.machinery.ExtensionFileLoader('partuv._core', found[0])
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('partuv._core', loader))
    loader.exec_module(module)
    return module


def split_nonmanifold(pos, tri):
    """One vertex per group of corners glued across two-face edges: non-manifold edges become seams."""
    parent = list(range(3 * len(tri)))

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    edge = defaultdict(list)
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            edge[(min(a, b), max(a, b))].append(f)
    corner = [{int(v): k for k, v in enumerate(t)} for t in tri]
    nonmanifold = 0
    for (a, b), faces in edge.items():
        if len(faces) > 2:
            nonmanifold += 1
        if len(faces) != 2:
            continue
        f, g = faces
        for v in (a, b):
            parent[find(3 * f + corner[f][v])] = find(3 * g + corner[g][v])
    new_index, new_pos = {}, []
    new_tri = np.empty_like(tri)
    for f, t in enumerate(tri):
        for k, v in enumerate(t):
            root = find(3 * f + k)
            if root not in new_index:
                new_index[root] = len(new_pos)
                new_pos.append(pos[v])
            new_tri[f, k] = new_index[root]
    return np.array(new_pos), new_tri, nonmanifold


def face_adjacency(tri):
    edge = defaultdict(list)
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            edge[(min(a, b), max(a, b))].append(f)
    rows, cols = [], []
    for faces in edge.values():
        faces = sorted(set(faces))
        for i in range(len(faces)):
            for j in range(i + 1, len(faces)):
                rows += [faces[i], faces[j]]
                cols += [faces[j], faces[i]]
    n = len(tri)
    adj = coo_matrix((np.ones(len(rows), np.int8), (rows, cols)), shape=(n, n)).tocsr()
    count, labels = connected_components(adj, directed=False)
    if count > 1:      # Ward needs one connected graph: chain the pieces by their first faces
        reps = [int(np.nonzero(labels == c)[0][0]) for c in range(count)]
        r = reps[:-1] + reps[1:]
        c = reps[1:] + reps[:-1]
        adj = adj + coo_matrix((np.ones(len(r), np.int8), (r, c)), shape=(n, n)).tocsr()
    return adj


def skin_tree(pos, tri, weights):
    from sklearn.cluster import AgglomerativeClustering
    w = weights[tri].mean(1)
    w = w / np.maximum(np.linalg.norm(w, axis=1, keepdims=True), 1e-9)
    centre = pos[tri].mean(1)
    centre = (centre - centre.mean(0)) / max(float(np.ptp(pos, 0).max()), 1e-12)
    feat = np.concatenate([w, 0.5 * centre], 1)
    clustering = AgglomerativeClustering(connectivity=face_adjacency(tri), n_clusters=1).fit(feat)
    return {len(tri) + i: {'left': int(a), 'right': int(b)} for i, (a, b) in enumerate(clustering.children_)}


CONFIG = """verbose: false
save_stuff: false
num_cuda_streams: 10
pipeline:
  threshold: {threshold}
  parallelDepth: 10
  component_maxDepth: 10
  checkSelfIntersection: false
  checkNon2Manifold: true
  num_omp_threads: 8
  num_cuda_streams: 10
unwrap:
  method: abf
  abf_iters: 5
  agg_parts: 10
  pamo: {pamo}
  usePamoFaceThreshold: 1000
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--threshold', type=float, default=1.25)
    parser.add_argument('--no-pamo', action='store_true', help='CPU only (PAMO, the distortion-check simplifier, '
                                                                'uses CUDA)')
    args = parser.parse_args()
    data = np.load(args.src)
    pos, tri = data['pos'].astype(np.float64), data['tri'].astype(np.int64)
    weights = data['weights'].astype(np.float64) if 'weights' in data else np.ones((len(pos), 1))
    core = load_core()
    V, F, nonmanifold = split_nonmanifold(pos, tri)
    tree = skin_tree(V, F, weights[_source_vertex(pos, tri, V, F)])
    with tempfile.TemporaryDirectory() as tmp:
        config = os.path.join(tmp, 'config.yaml')
        with open(config, 'w') as f:
            f.write(CONFIG.format(threshold=args.threshold, pamo='false' if args.no_pamo else 'true'))
        final, parts = core.pipeline_numpy(V=np.asfortranarray(V), F=np.asfortranarray(F.astype(np.int32)),
                                           tree_dict=tree, configPath=config, threshold=args.threshold)
    whole = final.to_components()       # one mesh, vertices split per chart
    cf, cv, cuv = np.asarray(whole.F), np.asarray(whole.V), np.asarray(whole.UV)[:, :2]
    if len(cf) != len(tri):
        raise RuntimeError(f'PartUV returned {len(cf)} faces for {len(tri)}')
    rows = np.repeat(np.arange(len(cf)), 3)
    incidence = coo_matrix((np.ones(len(rows)), (rows, cf.ravel()))).tocsr()
    _, label = connected_components(incidence @ incidence.T, directed=False)
    lookup = defaultdict(list)
    for f, t in enumerate(F):
        lookup[tuple(sorted(map(tuple, np.round(V[t], 6))))].append(f)
    uv = np.full((len(tri), 3, 2), np.nan)
    chart = np.full(len(tri), -1)
    for k, t in enumerate(cf):
        f = lookup[tuple(sorted(map(tuple, np.round(cv[t], 6))))].pop()
        src = V[F[f]]
        for j in range(3):
            uv[f, int(np.linalg.norm(src - cv[t[j]], axis=1).argmin())] = cuv[t[j]]
        chart[f] = label[k]
    if (chart < 0).any() or np.isnan(uv).any():
        raise RuntimeError('PartUV left faces unmapped')
    np.savez(args.dst, uv=uv, chart=chart)
    sizes = np.bincount(chart)
    print(f'PARTUV threshold {args.threshold}: {len(sizes)} charts ({int((sizes < 8).sum())} under 8 triangles), '
          f'{len(parts)} parts, {nonmanifold} non-manifold edges cut, pamo {not args.no_pamo}', flush=True)


def _source_vertex(pos, tri, V, F):
    """Original vertex of every split vertex (for its skin weights)."""
    src = np.zeros(len(V), np.int64)
    src[F.ravel()] = tri.ravel()
    return src


if __name__ == '__main__':
    sys.exit(main())
