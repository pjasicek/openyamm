"""G5 check: the rest hand coloured by finger label (finger_weights.py attribute 'finger': grey hand, red thumb,
orange index, yellow middle, green ring) with the finger joint heads; palm/back/sides. Args: -- <blend> <side> <out>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, side, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
lab = np.zeros(len(me.vertices), np.int32); me.attributes['finger'].data.foreach_get('value', lab)
COL = np.array([(0.6, 0.6, 0.6, 1), (0.9, 0.1, 0.1, 1), (1, 0.5, 0, 1), (0.95, 0.85, 0.1, 1), (0.1, 0.75, 0.2, 1), (0.1, 0.4, 0.9, 1)])
ca = me.color_attributes.new('lab', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', COL[lab].ravel())
me.color_attributes.active_color = ca
for n in [b.name for b in rig.data.bones if f'B_{side}_Finger' in b.name]:
    m = bpy.data.meshes.new('b'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.004)
    bm.to_mesh(m); bm.free(); o = bpy.data.objects.new('b', m); bpy.context.scene.collection.objects.link(o)
    o.location = rig.data.bones[n].head_local
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
scene.display.shading.show_xray = True; scene.display.shading.xray_alpha = 0.85
h = rig.data.bones[f'B_{side}_Hand'].head_local; t = rig.data.bones[f'B_{side}_Finger2'].head_local
c = h + (t - h) * 1.3
for v in ('front', 'left', 'back', 'right'):
    common.render_views(f'{out}_{v}', c.z, 0.3, views=(v,), resolution=(360, 360), target=(c.x, c.y))
