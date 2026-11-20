"""Dagger clearance per clip: blade and guard samples (Dagger bone space, the male dagger's 0.325 m length) against
the posed body surface (unsigned: skirt, sleeves and hair are open shells, so no inside test). Reports the minimum
distance (cm) per clip, its frame and the body piece touched. Args: -- <blend> [action ...]"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); acts = a[1:] or ['Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects['Body']
pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
samples = [Vector((0, y, 0)) for y in np.linspace(0.06, 0.325, 12)]
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    worst = (1e9, None)
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        # exclude the right hand and forearm (the dagger is held there)
        faces = [p.vertices[:] for p in me.polygons if pv[p.vertices[0]] not in (4,)]
        fpiece = [int(pv[p.vertices[0]]) for p in me.polygons if pv[p.vertices[0]] not in (4,)]
        tree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], faces); ev.to_mesh_clear()
        M = rig.matrix_world @ rig.pose.bones['Dagger'].matrix
        for s in samples:
            p = M @ s; loc, nrm, i, d = tree.find_nearest(p)
            if d < worst[0]: worst = (d, f, fpiece[i])
    print('DAGGERCLEAR', name, 'min distance cm', round(worst[0] * 100, 2), 'frame', worst[1], 'piece', worst[2])
