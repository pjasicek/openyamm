"""Clay close renders of the left hand (rest pose) with the faces in an .npy list in red.
Usage: blender -b work/source.blend -P viz_faces.py -- <faces .npy> <label>"""
import os, sys, bpy, numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fl, label = sys.argv[sys.argv.index('--') + 1:][:2]
body = bpy.data.objects['Body']; me = body.data; sel = set(np.load(os.path.join(HERE, fl)).tolist())
attr = me.color_attributes.new('Sel', 'FLOAT_COLOR', 'CORNER')
for p in me.polygons:
    for li in p.loop_indices: attr.data[li].color = (.9, .1, .1, 1) if p.index in sel else (.65, .65, .65, 1)
me.color_attributes.active_color = attr
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.color_type = 'VERTEX'
sc.display.shading.light = 'STUDIO'; sc.display.shading.show_backface_culling = False
rig = bpy.data.objects['Rig']
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
c = Vector([float(x) for x in os.environ.get('REA_C', '0.425,-0.06,0.85').split(',')])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('REA_S', '.2')); sc.render.resolution_x = sc.render.resolution_y = 450
os.makedirs(os.path.join(HERE, 'review/hands'), exist_ok=True)
for view, d in {'front': (0, -1, .1), 'out': (1, 0, .1), 'in': (-1, -.15, .1), 'back': (0, 1, .1)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(HERE, 'review/hands', f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
