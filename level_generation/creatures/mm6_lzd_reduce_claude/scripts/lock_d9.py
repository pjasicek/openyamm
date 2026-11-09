"""Config d9 keep mask: d8 plus the gate-sensitive regions the d8 reduction moved (shared gate review/gates_nofix):
every source face with a vertex below REA_FOOT_Z (default 0.06 m: soles, toes and claws; foot yaw and sole height use
the lowest 5 mm of each foot) and every source face within REA_LOCK_R (0.04 m) of the LOD0 vertices of the given gate
edges (Hit arm_stretch_max). Usage: lock_d9.py <reduced glb> <base keep .npy> <out .npy> [v0,v1 ...]"""
import os, struct, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
glb, base, out, *edges = sys.argv[1:]
doc, b = read_glb(Path(glb))
node = next(n for n in doc['nodes'] if n.get('name') == 'Lizard')
pos = []
for p in doc['meshes'][node['mesh']]['primitives']:
    a = p['attributes']['POSITION']; n = doc['accessors'][a]['count']
    pos.append(np.array(struct.unpack(f'<{n * 3}f', accessor_bytes(doc, b, a))).reshape(-1, 3))
pos = np.concatenate(pos); pos = np.c_[pos[:, 0], -pos[:, 2], pos[:, 1]]  # glTF Y-up -> Z-up
d = np.load(HERE / 'work' / 'mesh_in.npz'); v, f = d['verts'], d['faces']
print('LOD0 -> source nearest (m):', cKDTree(v).query(pos)[0].max().round(4))
keep = np.load(base).copy(); n0 = int(keep.sum())
foot = (v[f][:, :, 2] < float(os.environ.get('REA_FOOT_Z', '0.06'))).any(1); keep |= foot
cen = v[f].mean(1); tree = cKDTree(cen)
for e in edges:
    for i in map(int, e.split(',')):
        keep[tree.query_ball_point(pos[i], float(os.environ.get('REA_LOCK_R', '0.04')))] = True
np.save(out, keep); print('feet', int(foot.sum()), 'faces; kept', n0, '->', int(keep.sum()))
