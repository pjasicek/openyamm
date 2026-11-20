"""Head-and-chest front renders of a viewer GLB in Standing frame 0, flat (texture only, no lighting) and lit studio
clay, to separate texture colour from shading. Usage: blender -b -P flat_views.py -- <glb> <label>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
head = rig.matrix_world @ next(b for n, b in rig.pose.bones.items() if n.lower().endswith('head')).head
c = head - Vector((0, 0, .12))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .55; cam.location = c + Vector((0, -4, .3))
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.resolution_x = sc.render.resolution_y = 500
sc.view_settings.view_transform = 'Standard'
for mode, light, ctype in [('flat', 'FLAT', 'TEXTURE'), ('litclay', 'STUDIO', 'SINGLE')]:
    sc.display.shading.light = light; sc.display.shading.color_type = ctype; sc.display.shading.single_color = (.8, .8, .8)
    sc.render.filepath = os.path.join(HERE, 'review/skin', f'{label}_{mode}.png'); bpy.ops.render.render(write_still=True)
