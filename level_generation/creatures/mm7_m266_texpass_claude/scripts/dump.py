"""Dumps the layout meshes of the installed GLB (texpass.json layout_meshes, LOD0 body first) into
work/lod0_before.npz: one triangle list over all their primitives with per-vertex positions, normals, old UVs,
joints, weights, a part id per triangle (index into `parts`), welded vertex ids (exact positions within one part),
the head weight per vertex (sum of weights on head_bones) and per-group weights (group_factors).
Usage: dump.py [glb, default work/before_texpass/<stem>.glb]"""
import sys

import numpy as np

import tp

path = sys.argv[1] if len(sys.argv) > 1 else tp.before_glb()
g = tp.Glb(path)
doc = g.doc
joint_names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
cols = {k: [] for k in ('pos', 'nrm', 'uv', 'joints', 'weights')}
tris, part_of_tri, part_of_vert, parts = [], [], [], []
offset = 0
for k, (mi, pi) in enumerate(tp.layout_prims(doc)):
    pr = doc['meshes'][mi]['primitives'][pi]
    at = pr['attributes']
    pos = g.accessor(at['POSITION']).astype(np.float64)
    cols['pos'].append(pos)
    cols['nrm'].append(g.accessor(at['NORMAL']).astype(np.float64))
    cols['uv'].append(g.accessor(at['TEXCOORD_0']).astype(np.float64))
    cols['joints'].append(g.accessor(at['JOINTS_0']).astype(np.int64))
    cols['weights'].append(tp.weights_float(g.accessor(at['WEIGHTS_0'])))
    tri = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
    tris.append(tri + offset)
    part_of_tri.append(np.full(len(tri), k))
    part_of_vert.append(np.full(len(pos), k))
    parts.append(f"{doc['meshes'][mi]['name']}#{pi}")
    offset += len(pos)
data = {k: np.concatenate(v) for k, v in cols.items()}
tri = np.concatenate(tris)
part = np.concatenate(part_of_tri)
pv = np.concatenate(part_of_vert)
key = np.concatenate([pv[:, None].astype(np.float64), data['pos'].round(7)], 1)
_, weld = np.unique(key, axis=0, return_inverse=True)
weld = weld.ravel()
if tp.CFG.get('weld_split_normals'):
    # double-sided sheets (fins, membranes): front and back share positions; keep vertices whose normals point
    # apart (dot < 0) in separate welded vertices, so each side is its own surface for the charts (Hydra fins
    # flipped inside merged charts and fell back to fragments)
    nrm = data['nrm'] / np.maximum(np.linalg.norm(data['nrm'], axis=1, keepdims=True), 1e-12)
    out = np.empty_like(weld)
    order = np.argsort(weld, kind='stable')
    bounds = np.flatnonzero(np.diff(weld[order])) + 1
    next_id = 0
    for group in np.split(order, bounds):
        reps = []
        for v in group:
            for rid, rn in reps:
                if nrm[v] @ rn > 0:
                    out[v] = rid
                    break
            else:
                reps.append((next_id, nrm[v]))
                out[v] = next_id
                next_id += 1
    weld = out


def group_weight(bones):
    ids = [i for i, n in enumerate(joint_names) if n in bones]
    missing = set(bones) - set(joint_names)
    assert not missing, ('unknown bones', missing)
    return np.where(np.isin(data['joints'], ids), data['weights'], 0).sum(1)


head_w = group_weight(tp.CFG['head_bones']) if tp.CFG.get('head_bones') else np.zeros(len(weld))
groups = {name: group_weight(bones) for name, (bones, _) in tp.CFG.get('group_factors', {}).items()}
np.savez(tp.HERE / 'work' / 'lod0_before.npz', tri=tri, part=part, weld=weld, head_w=head_w,
         joint_names=np.array(joint_names), parts=np.array(parts),
         group_names=np.array(list(groups)), group_w=np.array(list(groups.values())).reshape(len(groups), len(weld)),
         **data)
head_face = head_w[tri].mean(1) > 0.5
print('parts', parts, 'verts', len(weld), 'welded', weld.max() + 1, 'tris', len(tri),
      'head faces', int(head_face.sum()), 'groups', {k: int((v > 0.5).sum()) for k, v in groups.items()})
