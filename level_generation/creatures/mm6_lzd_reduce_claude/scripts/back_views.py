"""Renders of a viewer GLB in one clip at given times, from behind, behind-right, front and front-right (sleeve check).
Usage: blender -b -P back_views.py -- <glb> <label> <clip> <t1,t2,...>"""
import math, os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label, clip, times = sys.argv[sys.argv.index('--') + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions[clip]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.1
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(155)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 500
sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review/back'), exist_ok=True)
for t in times.split(','):
    sc.frame_set(round(float(t) * sc.render.fps)); c = Vector((0, 0, 1.25))
    for view, d in {'back': (0, 1, .15), 'backr': (-.6, .8, .2), 'front': (0, -1, .15), 'frontr': (-.7, -.7, .2)}.items():
        cam.location = c + Vector(d).normalized() * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(HERE, 'review/back', f'{label}_{clip}_{t}_{view}.png'); bpy.ops.render.render(write_still=True)
