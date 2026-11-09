"""Per-face Smart Topology piece and garment labels of the installed m362 LOD0. Two steps:
- in Blender (read-only on the production master ../mm7_m362_claude/work/rig_v6.blend, rest pose): per-vertex position,
  'piece' and 'garment' -> work/master_pieces.npz;
- with plain python3 (`python3 dump_pieces.py map`): each LOD0 face (work/lod0_before.npz) takes the majority label of
  its corners' nearest master vertices -> work/pieces.npz (piece, garment per face, max distance)."""
import os

import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys.argv[-1] == 'map':
    from scipy.spatial import cKDTree
    m = np.load(os.path.join(HERE, 'work', 'master_pieces.npz'))
    d = np.load(os.path.join(HERE, 'work', 'lod0_before.npz'))
    pos = d['pos']
    blender = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], 1)
    dist, idx = cKDTree(m['co']).query(blender)
    out = {}
    for name in ('piece', 'garment'):
        corner = m[name][idx][d['tri']]
        out[name] = np.array([np.bincount(r - r.min()).argmax() + r.min() for r in corner])
    np.savez(os.path.join(HERE, 'work', 'pieces.npz'), max_mm=dist.max() * 1000, **out)
    print('PIECES max distance mm', round(float(dist.max()) * 1000, 3), 'pieces', sorted(set(out['piece'].tolist())),
          'garments', sorted(set(out['garment'].tolist())))
    sys.exit()
import bpy  # noqa: E402
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm7_m362_claude', 'work', 'rig_v6.blend'))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
me = body.data
rig.animation_data_create()
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
labels = {}
for name in ('piece', 'garment'):
    a = np.zeros(len(me.vertices), np.int32)
    me.attributes[name].data.foreach_get('value', a)
    labels[name] = a
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), co=co, **labels)
print('MASTER', len(co))
