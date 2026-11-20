"""Renders of review-viewer GLBs straight from file (own normals, baked tier colours): face, chest, back, belt, hands
with the sword, legs, attack and corpse -> review/tiers/<label>_<spot>.png (Eevee) and <label>_<spot>_clay.png
(workbench, CLAY=1). Usage: blender -b -P viewer_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'tiers'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .32, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .32, (.7, -.7, .1)),
         'chest': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)), 'back': ('Standing', 0, 'B_Spine1', .7, (0, 1, .1)),
         'belt': ('Standing', 0, 'B_Pelvis', .45, (.5, -.85, .15)), 'rhand': ('Standing', 0, 'B_R_Finger2', .35, (-.5, -.8, .2)),
         'lhand': ('Standing', 0, 'B_L_Finger2', .3, (.5, -.8, .2)), 'legs': ('Standing', 0, 'B_L_Calf', .8, (.3, -1, .05)),
         'strike': ('Attack', 24, 'B_Spine1', 1.6, (-.6, -.8, .1)), 'windup': ('Attack', 12, 'B_Spine1', 1.6, (.7, -.7, .1)),
         'dead': ('Dead', 0, 'B_Pelvis', 1.8, (.8, -.4, .6))}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    acts = {a.name.rsplit('|', 1)[-1].split('_')[-1] if '|' in a.name else a.name: a for a in bpy.data.actions}
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 460
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = acts[act]
        if acts[act].slots:
            rig.animation_data.action_slot = acts[act].slots[0]
        sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size; cam.data.clip_end = 20
        sc.render.engine = 'BLENDER_EEVEE'; sc.render.filepath = os.path.join(out, f'{label}_{spot}.png'); bpy.ops.render.render(write_still=True)
        if os.environ.get('CLAY') == '1':
            sc.render.engine = 'BLENDER_WORKBENCH'; sc.render.filepath = os.path.join(out, f'{label}_{spot}_clay.png'); bpy.ops.render.render(write_still=True)
print('VIEWERVIEWS done')
