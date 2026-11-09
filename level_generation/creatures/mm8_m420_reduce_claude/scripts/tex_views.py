"""Retexture check renders: textured close-ups of the review-viewer GLBs (tier colours baked) for each tier and
model tag -> review/retex/<tier>_<tag>_<spot>.png. Usage: blender -b -P tex_views.py -- <tier,...> <tag,...>"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tiers, tags = (a.split(',') for a in sys.argv[sys.argv.index('--') + 1:][:2])
# (action, frame, bone, ortho size, view direction); the model faces -Y
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .26, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .26, (.7, -.7, .1)),
         'face_side': ('Standing', 0, 'B_Head', .26, (1, 0, .05)), 'neck_side': ('Standing', 0, 'B_Neck', .32, (-1, -.3, .1)),
         'neck_back': ('Standing', 0, 'B_Neck', .32, (.2, 1, .2)), 'hand_r': ('Attack', 24, 'B_R_Hand', .22, (-.3, -1, .4)),
         'hand_l': ('Attack', 24, 'B_L_Hand', .22, (.3, -1, .4)), 'robe_front': ('Standing', 0, 'B_Spine1', 1.25, (0, -1, .05)),
         'robe_back': ('Standing', 0, 'B_Spine1', 1.25, (0, 1, .05)), 'cuirass_front': ('Standing', 0, 'B_Spine1', .5, (.2, -1, .1)),
         'cuirass_back': ('Standing', 0, 'B_Spine1', .5, (-.2, 1, .1)), 'waist_back': ('Standing', 0, 'B_Spine1', .35, (.2, 1, -.15)),
         'robe_side': ('Standing', 0, 'B_Spine1', 1.25, (1, 0, .05)), 'sleeve_up': ('Attack', 24, 'B_Spine1', 1.0, (-.4, -1, -.4))}
out = os.path.join(HERE, 'review', 'retex'); os.makedirs(out, exist_ok=True)
for tier in tiers:
    for tag in tags:
        bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
        bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'review', 'viewer', f'mm8_necromancer_{tier}_{tag}.glb'))
        rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'; cam.data.clip_end = 20
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
        sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
        w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (.45, .45, .48, 1)
        sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x = sc.render.resolution_y = 480
        acts = {a.name.rsplit('|', 1)[-1]: a for a in bpy.data.actions}
        for spot, (act, frame, b, size, d) in SPOTS.items():
            rig.animation_data.action = acts[act]
            if acts[act].slots:
                rig.animation_data.action_slot = acts[act].slots[0]
            sc.frame_set(frame); pb = rig.pose.bones[b]
            c = rig.matrix_world @ ((pb.head + pb.tail) / 2); dv = Vector(d).normalized()
            cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = size
            sc.render.filepath = os.path.join(out, f'{tier}_{tag}_{spot}.png'); bpy.ops.render.render(write_still=True)
print('TEXVIEWS done')
