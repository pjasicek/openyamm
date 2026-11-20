"""Whole-body renders of review-viewer GLBs (body + merged sword), imported as is: Standing 0 and Attack at the impact
(1.283 s), three-quarter front -> review/viewer_views/<label>_<clip>.png. Usage: blender -b -P viewer_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'viewer_views'); os.makedirs(out, exist_ok=True)
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4; sc.render.resolution_x = sc.render.resolution_y = 520
    c = Vector((0, 0, .9)); cam.location = c + Vector((.6, -1, .25)).normalized() * 6
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for clip, t in (('Standing', 0), ('Attack', 1.283)):
        act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == clip or a.name == clip)
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        fr = act.frame_range[0] + t * 24; sc.frame_set(int(fr), subframe=fr - int(fr))
        sc.render.filepath = os.path.join(out, f'{label}_{clip}.png'); bpy.ops.render.render(write_still=True)
print('VIEWS done')
