"""Textured close-ups for the retexture check, straight from GLBs (their own normals), with the base colour replaced by
a tier bake (work/retex/tier_<t>.png from tier_bake.py). Usage:
blender -b -P retex_views.py -- <label=glb,...> <tiers e.g. abc> [spot,...] -> review/retex/<label>_<tier>_<spot>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'retex'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
# (action, frame, bone, ortho size, view direction, offset); the cyclops faces -Y
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .42, (0, -1, .05), (0, 0, .05)),
         'face_q34': ('Standing', 0, 'B_Head', .42, (.7, -.7, .15), (0, 0, .05)),
         'face_side': ('Standing', 0, 'B_Head', .42, (1, 0, .05), (0, 0, .05)),
         'eye': ('Standing', 0, 'B_Head', .16, (0, -1, .05), (0, 0, .11)),
         'mouth': ('Standing', 0, 'B_Head', .2, (.25, -1, -.1), (0, -.02, -.02)),
         'neck_back': ('Standing', 0, 'B_Neck', .5, (-.3, 1, .25), (0, 0, .05)),
         'neck_side': ('Standing', 0, 'B_Neck', .5, (-1, .1, .1), (0, 0, .05)),
         'torso': ('Standing', 0, 'B_Spine2', .9, (.2, -1, .05), (0, 0, 0)),
         'back': ('Standing', 0, 'B_Spine1', 1.0, (-.3, 1, .1), (0, 0, 0)),
         'larm': ('Standing', 0, 'B_L_Forearm', .7, (1, -.2, .1), (0, 0, 0)),
         'rarm_back': ('Standing', 0, 'B_R_Forearm', .7, (-.6, 1, .1), (0, 0, 0)),
         'rhand': ('Standing', 0, 'B_R_Hand', .3, (-.5, -1, .1), (0, 0, 0)),
         'lhand': ('Standing', 0, 'B_L_Hand', .3, (.5, -1, .1), (0, 0, 0)),
         'loin_front': ('Standing', 0, 'B_Pelvis', .75, (0, -1, .05), (0, 0, -.12)),
         'loin_back': ('Standing', 0, 'B_Pelvis', .75, (0, 1, .05), (0, 0, -.12)),
         'boots': ('Standing', 0, 'B_L_Calf', .9, (.4, -1, .1), (0, 0, 0)),
         'boots_back': ('Standing', 0, 'B_R_Calf', .9, (-.4, 1, .1), (0, 0, 0)),
         'lupper_back': ('Standing', 0, 'B_L_UpperArm', .55, (.4, 1, .2), (0, 0, 0)),
         'rupper_back': ('Standing', 0, 'B_R_UpperArm', .55, (-.4, 1, .2), (0, 0, 0)),
         'lboot_out': ('Standing', 0, 'B_L_Calf', .6, (1, 0, .1), (0, 0, 0)),
         'rboot_out': ('Standing', 0, 'B_R_Calf', .6, (-1, 0, .1), (0, 0, 0)),
         'lforearm_back': ('Standing', 0, 'B_L_Forearm', .45, (.3, 1, .1), (0, 0, 0)),
         'rforearm_back': ('Standing', 0, 'B_R_Forearm', .45, (-.3, 1, .1), (0, 0, 0)),
         'lwrist': ('Standing', 0, 'B_L_Hand', .22, (.8, .2, .1), (0, 0, .06)),
         'rwrist': ('Standing', 0, 'B_R_Hand', .22, (-.8, .2, .1), (0, 0, .06)),
         'lwrist_f': ('Standing', 0, 'B_L_ForearmTwist', .3, (.2, -1, .05), (0, 0, 0)),
         'lwrist_b': ('Standing', 0, 'B_L_ForearmTwist', .3, (.2, 1, .05), (0, 0, 0)),
         'lwrist_s': ('Standing', 0, 'B_L_ForearmTwist', .3, (1, 0, .05), (0, 0, 0)),
         'rwrist_f': ('Standing', 0, 'B_R_ForearmTwist', .3, (-.2, -1, .05), (0, 0, 0)),
         'rwrist_b': ('Standing', 0, 'B_R_ForearmTwist', .3, (-.2, 1, .05), (0, 0, 0)),
         'rwrist_s': ('Standing', 0, 'B_R_ForearmTwist', .3, (-1, 0, .05), (0, 0, 0)),
         'armband': ('Standing', 0, 'B_R_UpperArm', .35, (-.7, -.7, .1), (0, 0, 0)),
         'discs': ('Standing', 0, 'B_Spine2', .45, (0, -1, .1), (0, 0, .12)),
         'belt_side': ('Standing', 0, 'B_Pelvis', .7, (1, 0, .05), (0, 0, 0))}
labels, tiers = args[0].split(','), args[1]
SUF = os.environ.get('RETEX_SUFFIX', '')  # tier bake suffix (tier_bake.py) for every label marked with '+'
if len(args) > 2:
    SPOTS = {k: SPOTS[k] for k in args[2].split(',')}
for item in labels:
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:
        if o.type == 'MESH' and 'oulder' in o.name:
            o.hide_render = True
    mat = bpy.data.materials['Cyclops_A']
    img_node = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and 'basecolor' in n.image.name)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.36, .36, .4, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.2
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.view_settings.view_transform = 'Standard'
    sc.render.engine = 'BLENDER_EEVEE'
    for t in tiers:
        img_node.image = bpy.data.images.load(os.path.join(HERE, 'work', 'retex', f'tier_{t}{SUF if label.endswith("+") else ""}.png'), check_existing=True)
        for spot, (act, frame, b, size, d, off) in SPOTS.items():
            rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2) + Vector(off)
            dv = Vector(d).normalized(); cam.location = c + dv * 4
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
            sun.rotation_euler = (c - (c + dv * 4 + Vector((1.5, 0, 2)))).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label.rstrip("+")}_{t}_{spot}.png'); bpy.ops.render.render(write_still=True)
print('RETEX_VIEWS done')
