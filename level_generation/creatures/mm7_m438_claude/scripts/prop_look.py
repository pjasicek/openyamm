"""Clay renders of work/props.blend's prop (cap faces red). Args: -- <out prefix> [object]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'props.blend'))
ob = bpy.data.objects[a[1] if len(a) > 1 else 'ForearmMesh']; me = ob.data
me.materials.clear()
for c in ((0.75, 0.75, 0.7, 1), (0.8, 0.1, 0.1, 1)):
    m = bpy.data.materials.new('m'); m.diffuse_color = c; me.materials.append(m)
if 'cap' in me.attributes:
    cv = np.zeros(len(me.polygons), bool); me.attributes['cap'].data.foreach_get('value', cv)
    for p in me.polygons: p.material_index = int(cv[p.index])
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
ob.rotation_euler = (-1.5708, 0, 0) if os.environ.get('CAP_VIEW') is None else (0, 0, 3.14159)   # CAP_VIEW: the cut end faces the front camera
bpy.context.view_layer.update()
if os.environ.get('CAP_VIEW'):
    ob.location = (0, 0.15, 0); bpy.context.view_layer.update()
    for m, c in zip(me.materials, ((0.75, 0.75, 0.7, 1), (0.8, 0.1, 0.1, 1))):
        m.diffuse_color = c
    if 'bonepart' in me.attributes:
        m2 = bpy.data.materials.new('b'); m2.diffuse_color = (0.95, 0.9, 0.7, 1); me.materials.append(m2)
        bv = np.zeros(len(me.polygons), bool); me.attributes['bonepart'].data.foreach_get('value', bv)
        for p in me.polygons:
            if bv[p.index]: p.material_index = 2
    common.render_views(a[0], 0.0, 0.16, views=('front', 'three_quarter', 'side60'), resolution=(400, 400))
else:
    common.render_views(a[0], 0.0, 0.5, views=('front', 'left', 'back', 'right'), resolution=(400, 400))
