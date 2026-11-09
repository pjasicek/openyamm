"""Where a candidate misses the source at one frame: source vertices farther than REA_MM (default 6) from the posed
candidate, with their rest position and region label (work/groups.npy, 99 kept). Usage: blender -b -P probe_spot.py --
<ladder blend> <Cand_NN> <clip:frame>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand, cf = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); f = d['faces']; rest = d['verts']
g = np.load(os.path.join(HERE, 'work', 'groups.npy')); keep = np.load(os.path.join(HERE, os.environ.get('GE_KEEP', 'work/keep_base.npy')))
lab = np.where(keep, 99, g); vl = np.full(len(rest), -1)
for k in range(3):
    vl[f[:, k]] = np.maximum(vl[f[:, k]], lab)
clip, fr = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(fr))
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
dd = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
bad = np.where(dd > float(os.environ.get('REA_MM', '6')))[0]
print('SPOT', cf, len(bad), 'vertices over limit')
for i in bad[np.argsort(-dd[bad])][:25]:
    print('SPOT', round(dd[i], 1), 'mm rest', np.round(rest[i], 3), 'label', vl[i])
