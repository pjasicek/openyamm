"""Rest-pose (geometry only) vs posed error per candidate in work/ladder.blend: p99/max of the two-way vertex->surface
distance with no action, and at REA_FRAMES. Separates decimation error from weight error. blender -b -P probe_rest.py"""
import os, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
def err(a, b):
    ba, bb = ev(a), ev(b); ta, tb = BVHTree.FromBMesh(ba), BVHTree.FromBMesh(bb)
    e = np.array([tb.find_nearest(v.co)[3] for v in ba.verts] + [ta.find_nearest(v.co)[3] for v in bb.verts]); ba.free(); bb.free()
    return f'p99 {np.percentile(e, 99)*1000:.2f} max {e.max()*1000:.2f}'
frames = [('rest', None)] + [(c.split(':')[0], int(c.split(':')[1])) for c in os.environ.get('REA_FRAMES', 'Running:0,Land:9').split(',')]
for clip, f in frames:
    if clip == 'rest':
        rig.animation_data.action = None
        for b in rig.pose.bones: b.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(f)
    for cn in sorted(o.name for o in bpy.data.objects if o.name.startswith('Cand_')):
        print('REST' if clip == 'rest' else 'POSE', clip, f, cn, err(bpy.data.objects[cn], src), flush=True)
