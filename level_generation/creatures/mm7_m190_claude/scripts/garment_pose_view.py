"""Posed render with vertices coloured by garment label (weights_fix.py) to locate a deforming piece.
Args: -- <blend> <action> <frame> <out prefix>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, an, fr, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cols = {0: (0.85, 0.7, 0.6), 1: (0.1, 0.9, 0.1), 2: (0.9, 0.1, 0.1), 3: (0.9, 0.8, 0.1), 4: (0.6, 0.2, 0.9), 5: (0.1, 0.4, 1),
        6: (1, 0.5, 0), 9: (0.2, 0.2, 0.2)}
ca = me.color_attributes.new('g', 'FLOAT_COLOR', 'POINT')
for i in range(len(gv)):
    c = cols.get(int(gv[i]), (1, 1, 1))
    if pv[i] == 0 and me.vertices[i].co.z > 1.0 and me.vertices[i].co.y > 0.05:
        c = (0, 1, 1)                                             # skin shell behind the upper back (hair)
    ca.data[i].color = (*c, 1)
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(fr))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
common.render_views(out, 1.0, 2.0, views=tuple(os.environ.get('VIEWS', 'front,right,left').split(',')), resolution=(500, 600))
