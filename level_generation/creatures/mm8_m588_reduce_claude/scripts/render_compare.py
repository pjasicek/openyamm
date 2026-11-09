"""Textured renders (Workbench, flat texture colour plus studio light, no sampling noise) of review-viewer GLBs at
every 3rd frame of every clip from six directions (front, three-quarter, side, back, top-front, below-front) ->
review/compare/<label>/<clip>_<frame>_<view>.png, for pixel comparison of an exact geometry cull.
Usage: blender -b -P render_compare.py -- <label=glb,...>"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {'front': (0, -1, .25), 'q34': (.7, -.7, .3), 'side': (1, 0, .2), 'back': (0, 1, .25), 'top': (0, -.5, 1),
         'below': (.2, -1, -.35)}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    out = os.path.join(HERE, 'review', 'compare', label); os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.6; sc.render.resolution_x = sc.render.resolution_y = 300
    sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
    for act in bpy.data.actions:
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        a, b = (int(x) for x in act.frame_range)
        for fr in range(a, b + 1, 3):
            sc.frame_set(fr)
            for v, d in VIEWS.items():
                c = Vector((0, 0, .95)); cam.location = c + Vector(d).normalized() * 8
                cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
                sc.render.filepath = os.path.join(out, f'{act.name.split("|")[-1]}_{fr:03d}_{v}.png')
                bpy.ops.render.render(write_still=True)
print('COMPARE done')
