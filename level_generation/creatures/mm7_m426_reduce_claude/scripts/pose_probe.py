"""Worst source-vertex -> candidate distances at one frame, with rest positions and dominant bones.
Usage: blender -b -P pose_probe.py -- <ladder blend> <Cand_NN> <clip:frame>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand, cf = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
rest = np.array([v.co[:] for v in src.data.vertices])
clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
dd = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
for i in np.argsort(-dd)[:15]:
    v = src.data.vertices[int(i)]
    print('PROBE', round(float(dd[i]), 1), np.round(rest[i], 3).tolist(), sorted(((names[g.group], round(g.weight, 2)) for g in v.groups), key=lambda t: -t[1])[:3])
