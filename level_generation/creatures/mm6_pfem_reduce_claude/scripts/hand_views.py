"""Clasped-hands close-ups of a viewer GLB (Standing frame 0): top, front, three-quarter.
Usage: blender -b -P hand_views.py -- <glb> <label> [clip] -> review/hands/<label>_<view>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[0], a[1]; clip = a[2] if len(a) > 2 else 'Standing'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; sc.render.fps = 24
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(0)
pb = rig.pose.bones
c = (rig.matrix_world @ pb['mixamorig:LeftHand'].head + rig.matrix_world @ pb['mixamorig:RightHand'].head) / 2
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .3
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(30), 0, math.radians(-20)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600; sc.render.engine = 'BLENDER_EEVEE'
out = os.path.join(HERE, 'review', 'hands'); os.makedirs(out, exist_ok=True)
for view, d in {'top': (0.05, -0.35, 1), 'front': (0, -1, .2), 'q34': (.6, -.8, .5), 'below': (0, -.6, -.5)}.items():
    dv = Vector(d).normalized(); cam.location = c + dv * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
