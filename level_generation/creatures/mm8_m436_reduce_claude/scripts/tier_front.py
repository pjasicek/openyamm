"""Front and back textured renders (Eevee, Standing frame 0) straight from GLBs, e.g. the baked viewer tiers.
Usage: blender -b -P tier_front.py -- <label=glb,...> -> review/tiers/<label>_<view>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'tiers'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and not any(m.type == 'ARMATURE' for m in o.modifiers):
            o.hide_render = True
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0; sc.render.resolution_x = sc.render.resolution_y = 600
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    c = Vector((0, 0, .85))
    for view, d in (('front', (0, -1, .1)), ('back', (0, 1, .1))):
        cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
print('TIERS done')
