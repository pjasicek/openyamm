"""Source -> candidate distance per source vertex (max over every 6th frame of every clip), summarised per face group
(work/groups.npy, first group of the vertex's faces) for each candidate in work/<blend>. Hidden source vertices skipped.
Usage: blender -b -P region_error.py -- <blend> <Cand_70,...>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); g = np.load(os.path.join(HERE, 'work/groups.npy'))
hid = np.load(os.path.join(HERE, 'work/hidden.npy'))
vg = np.full(len(d['verts']), -1); vg[d['faces'][:, 0]] = g; vg[d['faces'][:, 1]] = g; vg[d['faces'][:, 2]] = g
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.verts.ensure_lookup_table(); return b
for cn in a[1].split(','):
    c = bpy.data.objects[cn]; mx = np.zeros(len(d['verts']))
    for act in bpy.data.actions:
        rig.animation_data.action = act
        for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 6):
            sc.frame_set(fr); bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
            mx = np.maximum(mx, [tc.find_nearest(v.co)[3] for v in bs.verts]); bs.free(); bc.free()
    mx *= 1000
    for k in np.unique(vg):
        s = (vg == k) & ~hid
        if s.any():
            print('REGION', cn, 'group', k, 'verts', int(s.sum()), 'p99', round(float(np.percentile(mx[s], 99)), 2), 'max', round(float(mx[s].max()), 2),
                  'at', np.round(d['verts'][np.where(s)[0][np.argmax(mx[s])]], 3))
