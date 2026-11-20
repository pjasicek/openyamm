"""Tier check with the region ramps applied (review-viewer GLBs from viewer_variants.py, which bake the engine's ramp
rule into the base colour): Eevee renders of each given GLB, Standing rest and the Attack gape (frame 22), from the
front, three-quarter, back and above -> review/tiers/<label>_<pose>_<view>.png. Usage: blender -b -P tier_sheet.py -- <label=glb,...>"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'tiers'); os.makedirs(out, exist_ok=True)
VIEWS = {'front': (0, -1, .25), 'q34': (.7, -.7, .3), 'back': (0, 1, .25), 'top': (0, -.5, 1)}
POSES = {'rest': ('Standing', 0), 'gape': ('Attack', 22)}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.2; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for pose, (act, fr) in POSES.items():
        rig.animation_data.action = bpy.data.actions[act]
        if bpy.data.actions[act].slots:
            rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
        sc.frame_set(fr)
        for v, d in VIEWS.items():
            c = Vector((0, 0, .95)); cam.location = c + Vector(d).normalized() * 8
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label}_{pose}_{v}.png'); bpy.ops.render.render(write_still=True)
print('TIERS done')
