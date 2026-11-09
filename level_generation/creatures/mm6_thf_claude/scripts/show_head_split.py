import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v3.blend'))
arm = bpy.data.objects['Thief_Rig']; arm.animation_data.action = None
for b in arm.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Thief'].data
h = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', h)
red = bpy.data.materials.new('h'); red.diffuse_color = (0.9, 0.3, 0.2, 1); grey = bpy.data.materials.new('g'); grey.diffuse_color = (0.7, 0.7, 0.7, 1)
me.materials.clear(); me.materials.append(grey); me.materials.append(red)
for p in me.polygons: p.material_index = int(h[p.index])
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, 'head_split'), 1.25, 0.8, views=('front', 'left', 'back'), resolution=(400, 400))
