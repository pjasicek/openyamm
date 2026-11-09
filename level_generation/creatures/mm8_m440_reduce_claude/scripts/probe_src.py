"""Top source -> candidate distances at given frames with source vertex index, rest position, group and hidden flag.
Usage: REA_CAND=Cand_70 REA_FRAMES=Standing:0 blender -b -P probe_src.py"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[os.environ['REA_CAND']]
hid = np.load(os.path.join(HERE, 'work/hidden.npy')); w = np.load(os.path.join(HERE, 'work/weights.npz'))
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); rest = d['verts']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.verts.ensure_lookup_table(); return b
for clip, f in [(x.split(':')[0], int(x.split(':')[1])) for x in os.environ['REA_FRAMES'].split(',')]:
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(f)
    bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
    dist = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
    for i in np.argsort(-dist)[:int(os.environ.get('N', '8'))]:
        print('SRC', clip, f, i, f'{dist[i]*1000:.1f}mm rest', np.round(rest[i], 3), 'hidden', hid[i], 'dom', w['names'][w['dominant'][i]])
