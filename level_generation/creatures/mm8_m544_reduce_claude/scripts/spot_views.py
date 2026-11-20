"""Textured close-ups (rest pose, GLBs imported directly) at given model-space points, looking at each from outside
(horizontal direction away from the body axis, or from above/below for points near it). Usage:
blender -b -P spot_views.py -- <label=glb,...> <x,y,z;x,y,z;...> -> review/spots/<label>_<n>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
pts = [Vector([float(x) for x in p.split(',')]) for p in a[1].split(';')]
out = os.path.join(HERE, 'review', 'spots'); os.makedirs(out, exist_ok=True)
for item in a[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Unicorn':
            o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .12; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for n, p in enumerate(pts):
        d = Vector((p.x, 0, 0)) if abs(p.x) > .02 else Vector((0, 0, 1 if p.z > .35 else -1))
        if d.length < 1e-6:
            d = Vector((1, 0, 0))
        d = (d.normalized() + Vector((0, 0, .3))).normalized()
        cam.location = p + d * 2; cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{n}.png'); bpy.ops.render.render(write_still=True)
print('SPOTS', len(pts))
