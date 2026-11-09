"""Textured rest-pose close-ups at work/escape_spots.json (escape_spots.py) for each <label>=<glb>; Eevee, ortho 0.18 m, camera
along the spot's normal. Usage: blender -b -P escape_close.py -- <label=glb,...> -> review/escape_close/<label>_<k>.png"""
import json, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'escape_close'); os.makedirs(out, exist_ok=True)
spots = json.load(open(os.path.join(HERE, 'work', 'escape_spots.json')))
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for a in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
        if a.animation_data:
            a.animation_data.action = None
        for b in a.pose.bones:
            b.matrix_basis.identity()
    body = bpy.data.objects['Wmut']; bpy.context.view_layer.update()
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.18; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sun.data.energy = 3.0; sc.collection.objects.link(sun)
    sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'
    for k, s in enumerate(spots):
        p = body.matrix_world @ Vector(s['p']); n = (body.matrix_world.to_3x3() @ Vector(s['n'])).normalized()
        cam.location = p + n * 2.0; cam.rotation_euler = (-n).to_track_quat('-Z', 'Y').to_euler()
        sun.rotation_euler = cam.rotation_euler
        sc.render.filepath = os.path.join(out, f'{label}_{k:02d}.png'); bpy.ops.render.render(write_still=True)
print('ESCAPECLOSE done')
