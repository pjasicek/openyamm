"""Fidget: blade samples against the closed left-hand skin (piece 3): signed distance (negative = inside) per frame;
reports the minimum. Args: -- <blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
act = bpy.data.actions['Fidget']; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
worst = (1e9, None); inside = 0
for f in range(0, 67):
    bpy.context.scene.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    tree = BVHTree.FromPolygons([body.matrix_world @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons if pv[p.vertices[0]] == 3])
    ev.to_mesh_clear(); M = rig.matrix_world @ rig.pose.bones['Dagger'].matrix
    for y in np.linspace(0.06, 0.325, 40):
        p = M @ Vector((0, y, 0)); loc, n, i, d = tree.find_nearest(p)
        sd = d if (p - loc).dot(n) >= 0 else -d
        inside += sd < 0
        if sd < worst[0]: worst = (sd, f)
print('FIDGETTOUCH min signed cm', round(worst[0] * 100, 2), 'frame', worst[1], 'samples inside', inside)
