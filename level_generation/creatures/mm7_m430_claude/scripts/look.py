"""Clay look at a blend's 'Body' (rest pose, piece colours): -- <blend> <out prefix> <centre z> <height> [views...]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, cz, h = a[0], a[1], float(a[2]), float(a[3])
views = tuple(a[4:]) or ('front', 'three_quarter', 'left', 'back')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects.get('Rig')
if rig and rig.animation_data:
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cols = [(0.9,0.3,0.3),(0.3,0.8,0.3),(0.3,0.5,0.95),(0.95,0.8,0.2),(0.8,0.3,0.9),(0.2,0.85,0.85),(0.95,0.55,0.2),(0.6,0.6,0.6)]
ca = me.color_attributes.new('pcol', 'FLOAT_COLOR', 'POINT')
for i, p in enumerate(pv):
    ca.data[i].color = (*cols[p % len(cols)], 1)
for o in bpy.data.objects:
    o.hide_render = o.type != 'MESH'
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.abspath(out), cz, h, views=views, resolution=(600, int(600 * 1.0)), distance=20)
