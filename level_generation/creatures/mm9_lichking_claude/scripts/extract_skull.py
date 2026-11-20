"""Lich skull (approved mm9_lich_claude, LichHead primitive of its runtime LOD0, bind space) -> work/lich_skull.npz:
co (Blender frame: x, -z, y), tri, uv (glTF v down), plus the head bone's bind position. Read-only on the lich project."""
import sys, numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = Glb('../mm9_lich_claude/export/mm9_lich_runtime_lod0.glb'); d = g.json
p = d['meshes'][0]['primitives'][1]
P = g.accessor(p['attributes']['POSITION']).astype(float); T = g.accessor(p['indices']).astype(int).reshape(-1, 3)
UV = g.accessor(p['attributes']['TEXCOORD_0']).astype(float)
m = Model(g); w = m.world({}); nn = [n['name'] for n in d['nodes']]
hb = w[nn.index('Bip01 Head')][:3, 3]; nb = w[nn.index('Bip01 Neck')][:3, 3]
co = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
print('skull bounds', co.min(0).round(3), co.max(0).round(3), 'tris', len(T), 'head bone', hb.round(3))
np.savez('work/lich_skull.npz', co=co, tri=T, uv=UV, head=np.r_[hb[0], -hb[2], hb[1]], neck=np.r_[nb[0], -nb[2], nb[1]])
