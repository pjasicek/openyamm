"""Renders of review-viewer GLBs straight from file (own normals, baked tier colours): face, chest, back, mail kilt, hands
with the axe, legs, attack and corpse -> review/tiers/<label>_<spot>.png (Eevee) and <label>_<spot>_clay.png
(workbench, CLAY=1). Usage: blender -b -P viewer_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'tiers'); os.makedirs(out, exist_ok=True)
# The Minotaur faces -Y in Blender (glTF +Z forward); Attack impact 0.8167 s = frame 19.6 at 24 fps
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .5, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .5, (.7, -.7, .1)),
         'face_side': ('Standing', 0, 'B_Head', .5, (1, 0, .05)), 'head_back': ('Standing', 0, 'B_Head', .6, (-.3, 1, .4)),
         'chest': ('Standing', 0, 'B_Spine1', .8, (0, -1, .1)), 'back': ('Standing', 0, 'B_Spine1', .9, (0, 1, .1)),
         'kilt': ('Standing', 0, 'B_Pelvis', .7, (.5, -.85, .15)), 'kilt_back': ('Standing', 0, 'B_Pelvis', .7, (-.4, .9, .15)),
         'kilt_low': ('Standing', 0, 'B_Pelvis', .7, (.3, -.8, -.5)),
         'rhand': ('Standing', 0, 'B_R_Finger2', .35, (-.5, -.8, .2)), 'lhand': ('Standing', 0, 'B_L_Finger2', .35, (.5, -.8, .2)),
         'legs': ('Standing', 0, 'B_L_Calf', 1.0, (.3, -1, .05)), 'feet': ('Standing', 0, 'B_L_Foot', .5, (.4, -.9, .35)),
         'whole': ('Standing', 0, 'B_Spine', 2.4, (.6, -.8, .1)), 'windup': ('Attack', 10, 'B_Spine1', 2.6, (.7, -.7, .1)),
         'strike': ('Attack', 20, 'B_Spine1', 2.6, (-.6, -.8, .1)), 'dead': ('Dead', 0, 'B_Pelvis', 2.6, (.8, -.4, .6)),
         'grip': ('Attack', 20, 'B_R_Hand', .45, (-.6, -.8, .2))}
ONLY = os.environ.get('SPOTS')
if ONLY:
    SPOTS = {k: v for k, v in SPOTS.items() if k in ONLY.split(',')}
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
