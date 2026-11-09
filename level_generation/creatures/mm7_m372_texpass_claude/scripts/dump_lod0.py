"""Dumps the LOD0 body primitive of the installed m372 GLB for the UV work: positions, normals, UVs, joints, weights,
triangles, welded vertex ids (exact positions), joint names, the approved head-set faces (right half of the
2080x1024 body | head atlas) and each face's approved region (mask sampled at the face's UV centre: 0 none/skin and
fittings, 1 gown, 2 veil + lining, 3 hair). Usage: dump_lod0.py <glb> <out npz>"""
import sys
import numpy as np
from glb import Glb

g = Glb(sys.argv[1])
doc = g.doc
mesh = next(m for m in doc['meshes'] if m['name'] == 'M372')
pr = mesh['primitives'][0]
at = pr['attributes']
pos = g.accessor(at['POSITION']).astype(np.float64)
uv = g.accessor(at['TEXCOORD_0']).astype(np.float64)
tri = g.accessor(pr['indices']).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(pos.round(7), axis=0, return_inverse=True)
weld = weld.ravel()
head_face = uv[tri, 0].mean(1) > 0.5
mat = doc['materials'][0]
mask = np.asarray(g.image(doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']).convert('RGBA'))
c = uv[tri].mean(1)
h, w = mask.shape[:2]
m = mask[np.clip((c[:, 1] * h).astype(int), 0, h - 1), np.clip((c[:, 0] * w).astype(int), 0, w - 1), :3]
region = np.where(m.max(1) > 127, m.argmax(1) + 1, 0)
joints = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
np.savez(sys.argv[2], pos=pos, nrm=g.accessor(at['NORMAL']), uv=uv, joints=g.accessor(at['JOINTS_0']),
         weights=g.accessor(at['WEIGHTS_0']), tri=tri, weld=weld, head_face=head_face, region=region,
         joint_names=np.array(joints))
print('verts', len(pos), 'welded', weld.max() + 1, 'tris', len(tri), 'head faces', int(head_face.sum()),
      'regions', np.bincount(region, minlength=4).tolist(),
      'head regions', np.bincount(region[head_face], minlength=4).tolist(),
      'y range', pos[:, 1].min(), pos[:, 1].max())
