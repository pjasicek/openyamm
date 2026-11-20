"""Rest render with the coat faces whose normal points toward the body axis painted red (inner layer / turned faces).
Args: -- <blend> <out prefix> <zc> <size> <views>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, zc, size, views = a[1], float(a[2]), float(a[3]), a[4].split(',')
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
gv = np.array([x.value for x in me.attributes['garment'].data])
pel = np.array(rig.data.bones['B_Pelvis'].head_local)
grey = bpy.data.materials.new('g'); grey.diffuse_color = (0.7, 0.7, 0.7, 1)
red = bpy.data.materials.new('r'); red.diffuse_color = (0.9, 0.1, 0.1, 1)
blue = bpy.data.materials.new('b'); blue.diffuse_color = (0.2, 0.3, 0.9, 1)
me.materials.clear(); me.materials.append(grey); me.materials.append(red); me.materials.append(blue)
n_red = 0
for p in me.polygons:
    g = gv[p.vertices[0]]; c = np.array(p.center); r = c - pel; r[2] = 0
    if g in (1, 2) and np.linalg.norm(r) > 1e-4 and np.array(p.normal) @ (r / np.linalg.norm(r)) < -0.2:
        p.material_index = 1; n_red += 1
    elif g == 7:
        p.material_index = 2
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_backface_culling = True
for v in views:
    common.render_views(out, zc, size, views=(v,), resolution=(700, 700))
print('INNERMARK red faces', n_red)
