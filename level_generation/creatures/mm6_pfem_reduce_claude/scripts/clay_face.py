"""Clay (workbench, cavity) close-ups of a master's face in rest pose: front, three-quarter, side.
Usage: blender -b <master.blend> -P clay_face.py -- <out prefix>"""
import sys, math, bpy, json
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene; rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
eyes = json.loads(sc['pfem_eyes']); c = (Vector(eyes['EyeLeft']['centre']) + Vector(eyes['EyeRight']['centre'])) / 2
c.z -= 0.025
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.24
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.show_cavity = True
sc.display.shading.color_type = 'SINGLE'; sc.render.resolution_x = sc.render.resolution_y = 600
for name, d in {'front': (0, -1, .05), 'q34': (.6, -.8, .1), 'side': (1, -.05, .05)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 2
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
