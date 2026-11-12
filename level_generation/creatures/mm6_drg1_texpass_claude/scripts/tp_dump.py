"""Dumps the LOD0 primitives of the new atlas (texpass.json atlas_prims) from work/before_texpass/<stem>.glb into
work/lod0_before.npz: positions, normals, old UVs, joints, weights, triangles (global vertex ids, primitives
concatenated in atlas_prims order), primitive per triangle and vertex, vertex offsets, welded ids (exact positions,
within a primitive), head faces (head-bone weight of the corners averaged > 0.5) and group weights.
Usage: tp_dump.py"""
import re

import numpy as np

import tp_common as C

cfg = C.config()
g = C.Glb(C.before_glb(cfg))
doc = g.doc
mesh = doc['meshes'][C.lod0_mesh_index(doc, cfg['node'])]
names = C.joint_names(doc)
cols = {k: [] for k in ('pos', 'nrm', 'uv', 'joints', 'weights', 'vprim', 'weld')}
tris, tprim, offsets = [], [], []
offset = weld_offset = 0
for pi in cfg['atlas_prims']:
    pr = mesh['primitives'][pi]
    at = pr['attributes']
    pos = g.accessor(at['POSITION']).astype(np.float64)
    cols['pos'].append(pos)
    cols['nrm'].append(g.accessor(at['NORMAL']).astype(np.float64))
    cols['uv'].append(g.accessor(at['TEXCOORD_0']).astype(np.float64))
    cols['joints'].append(g.accessor(at['JOINTS_0']).astype(np.int64))
    w = g.accessor(at['WEIGHTS_0']).astype(np.float64)
    if w.max() > 1.5:
        w = w / 255.0 if w.max() <= 255 else w / 65535.0
    cols['weights'].append(w)
    cols['vprim'].append(np.full(len(pos), pi))
    _, weld = np.unique(pos.round(7), axis=0, return_inverse=True)
    cols['weld'].append(weld.ravel() + weld_offset)
    weld_offset += int(weld.max()) + 1
    t = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
    tris.append(t + offset)
    tprim.append(np.full(len(t), pi))
    offsets.append(offset)
    offset += len(pos)
data = {k: np.concatenate(v) for k, v in cols.items()}
tri = np.concatenate(tris)
head_v = C.bone_weight(data['joints'], data['weights'], names, cfg['head_bones'])
head_face = head_v[tri].mean(1) > 0.5
if 'head_uv_min_u' in cfg:          # the approved head set is a part of the old atlas (body | head sets side by side)
    head_face = data['uv'][tri, 0].mean(1) > cfg['head_uv_min_u']
extra = {}
for name, (pattern, _factor) in cfg.get('group_factors', {}).items():
    extra['g_' + name] = C.bone_weight(data['joints'], data['weights'], names, [pattern])
np.savez(C.lod0_path(), tri=tri, prim=np.concatenate(tprim), offsets=np.array(offsets),
         head_face=head_face, joint_names=np.array(names), **data, **extra)
area = C.tri_area3(data['pos'][tri])
print('verts', len(data['pos']), 'welded', weld_offset, 'tris', len(tri),
      'per prim', {int(p): int((np.concatenate(tprim) == p).sum()) for p in cfg['atlas_prims']},
      'head faces', int(head_face.sum()), f'head surface {area[head_face].sum() / area.sum():.1%}',
      {k: f'{(v > 0.5).mean():.1%} verts' for k, v in extra.items()})
