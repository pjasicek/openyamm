"""PartUV study: PartField part tree once, then PartUV's recursive unwrap at several distortion thresholds, each
mapped back onto the input triangles (per-corner UVs + chart id) for our own density scaling and xatlas packing.

Runs in uv_research_20261111/partuv/venv with `python -I` (PartUV 0.1.2 wheel from PyPI, torch 2.7.1+cu128):
  partuv_run.py <mesh.npz from partuv_export_mesh.py> <out dir> <state dict .pt | bones> <threshold> [<threshold> ...]
'bones' builds the part tree from the skin weights (sklearn Ward clustering over adjacent faces) instead of PartField.
Writes <out>/partuv_t<thr>.npz (uv M x 3 x 2 unpacked, chart M, distortion per chart) and <out>/partuv_runs.json.
The PartField checkpoint is the plain state dict converted from model_objaverse.ckpt with torch weights_only=True
(no pickle code execution).
"""
import json
import os
import sys
import time

import numpy as np
import trimesh
import yaml
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

import torch
from preprocess_utils.manifold import split_nonmanifold_edges_as_seams
from preprocess_utils.partfield_official.run_PF import PFInferenceModel
import partuv

SRC, OUT, CKPT = sys.argv[1:4]
THRESHOLDS = [float(t) for t in sys.argv[4:]]
os.makedirs(OUT, exist_ok=True)
config_path = os.path.join(OUT, 'config.yaml')
with open(config_path, 'w') as f:      # PartUV defaults (config/config.yaml of the repo)
    yaml.safe_dump({'verbose': False, 'save_stuff': False, 'num_cuda_streams': 10,
                    'pipeline': {'threshold': 1.25, 'parallelDepth': 10, 'component_maxDepth': 10,
                                 'checkSelfIntersection': False, 'checkNon2Manifold': True, 'num_omp_threads': 8,
                                 'num_cuda_streams': 10},
                    'unwrap': {'method': 'abf', 'abf_iters': 5, 'agg_parts': 10, 'pamo': True,
                               'usePamoFaceThreshold': 1000}}, f)

data = np.load(SRC)
pos, tri = data['pos'], data['tri']
mesh = trimesh.Trimesh(vertices=pos, faces=tri, process=False)
fixed, nonmanifold = split_nonmanifold_edges_as_seams(mesh)
assert len(fixed.faces) == len(tri)          # face order is kept, only vertices are split
runs = {'input': SRC, 'triangles': int(len(tri)), 'nonmanifold_edges': int(nonmanifold)}
t0 = time.perf_counter()
if CKPT == 'bones':
    # licence-clean part tree without PartField (NVIDIA non-commercial licence): the same Ward agglomerative
    # clustering over edge-adjacent faces that PartField's tree uses, on per-face skin weights (+ a little position)
    from sklearn.cluster import AgglomerativeClustering
    from preprocess_utils.partfield_official.AgglomerativeClustering import construct_face_adjacency_matrix_naive
    t1 = time.perf_counter()
    w = data['weights'][tri].mean(1)
    w /= np.maximum(np.linalg.norm(w, axis=1, keepdims=True), 1e-9)
    centre = pos[tri].mean(1)
    centre = (centre - centre.mean(0)) / np.ptp(pos, 0).max()
    feat = np.concatenate([w, 0.5 * centre], 1)
    clustering = AgglomerativeClustering(connectivity=construct_face_adjacency_matrix_naive(fixed.faces),
                                         n_clusters=1).fit(feat)
    tree = {len(tri) + i: {'left': int(a), 'right': int(b)} for i, (a, b) in enumerate(clustering.children_)}
    runs['tree'] = 'bones'
else:
    model = PFInferenceModel(checkpoint_path=CKPT, device='cuda')
    t1 = time.perf_counter()
    tree, root, _ = model.process_face(None, output_path=None, mesh=fixed.copy(), device=model.device,
                                       sample_on_faces=10, sample_batch_size=100_000)
t2 = time.perf_counter()
runs['partfield_load_s'] = round(t1 - t0, 1)
runs['partfield_s'] = round(t2 - t1, 1)
V = np.asfortranarray(fixed.vertices, np.float64)
F = np.asfortranarray(fixed.faces, np.int32)
for thr in THRESHOLDS:
    t3 = time.perf_counter()
    final, parts = partuv.pipeline_numpy(V=V, F=F, tree_dict=tree, configPath=config_path, threshold=thr)
    elapsed = time.perf_counter() - t3
    uv = np.full((len(tri), 3, 2), np.nan)
    chart = np.full(len(tri), -1)
    whole = final.to_components()   # one mesh, vertices split per chart, each chart in its own unit square
    cf, cv, cuv = np.asarray(whole.F), np.asarray(whole.V), np.asarray(whole.UV)[:, :2]
    assert len(cf) == len(tri), (cf.shape, tri.shape)
    n_charts, label = connected_components(coo_matrix((np.ones(len(cf) * 3), (np.repeat(np.arange(len(cf)), 3),
                                                                             cf.ravel()))).tocsr() @
                                           coo_matrix((np.ones(len(cf) * 3), (cf.ravel(),
                                                                             np.repeat(np.arange(len(cf)), 3)))).tocsr(),
                                           directed=False)
    # PartUV reorders the faces: find each output face's input triangle by its corner positions
    lookup = {}
    for f, t in enumerate(F):
        lookup.setdefault(tuple(sorted(map(tuple, np.round(V[t], 6)))), []).append(f)
    for k, t in enumerate(cf):
        f = lookup[tuple(sorted(map(tuple, np.round(cv[t], 6))))].pop()
        src = V[F[f]]
        for j in range(3):
            uv[f, int(np.linalg.norm(src - cv[t[j]], axis=1).argmin())] = cuv[t[j]]
        chart[f] = label[k]
    dist = [float(c.distortion) for p in parts for c in p.components]
    assert (chart >= 0).all() and not np.isnan(uv).any(), 'unmapped faces'
    np.savez(os.path.join(OUT, f'partuv_t{thr:g}.npz'), uv=uv, chart=chart, distortion=np.array(dist))
    sizes = np.bincount(chart)
    runs[f't{thr:g}'] = {'charts': int(n_charts), 'part_charts': int(sum(p.num_components for p in parts)), 'parts': len(parts), 'distortion': float(final.distortion),
                         'charts_under_8': int((sizes < 8).sum()), 'seconds': round(elapsed, 1)}
    print('PARTUV', thr, runs[f't{thr:g}'], flush=True)
json.dump(runs, open(os.path.join(OUT, 'partuv_runs.json'), 'w'), indent=1)
