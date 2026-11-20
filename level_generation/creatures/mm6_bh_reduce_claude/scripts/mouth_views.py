"""Textured mouth close-ups of a viewer GLB (Standing frame 0): front, three-quarter, from below and the left side
(the eye faces -Y after import). Usage: blender -b -P mouth_views.py -- <glb> <out prefix> [ortho size]"""
import os, sys, math, bpy
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[:2]; size = float(args[2]) if len(args) > 2 else .34
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions[os.environ.get('REA_CLIP', 'Standing')]; sc.frame_set(int(os.environ.get('REA_FRAME', '0')))
jaw = rig.matrix_world @ rig.pose.bones['Jaw'].head; eye = rig.matrix_world @ rig.pose.bones['EyeBall'].head
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Eye':
        o.hide_render = True
c = Vector((0, -.3, (eye.z + jaw.z) / 2 - .08))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = size
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(-20)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.45, .45, .48, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.render.engine = 'BLENDER_EEVEE'
for view, dv in {'front': (0, -1, .05), 'q34': (.6, -.75, .2), 'below': (0, -.6, -.8), 'left': (-1, -.25, .05)}.items():
    cam.location = c + Vector(dv).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Z').to_euler()
    sc.render.filepath = f'{out}_{view}.png'; bpy.ops.render.render(write_still=True)
