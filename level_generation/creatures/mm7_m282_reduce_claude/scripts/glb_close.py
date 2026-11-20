"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, helmet, torso, shoulder, hands, arms, knees, boots, back, Attack and Death (spots for the MM7 Medusa).
Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {  # MM7 Medusa (m282): face front and both three-quarters (accepted twice by the user), hair, hands, serpent
    'head_front': ('Standing', 0, 'Head', .34, (0, -1, .1)), 'head_q34l': ('Standing', 0, 'Head', .34, (.7, -.7, .15)),
    'head_q34r': ('Standing', 0, 'Head', .34, (-.7, -.7, .15)), 'head_side': ('Standing', 0, 'Head', .45, (-1, 0, .1)),
    'head_back': ('Standing', 0, 'Head', .55, (0, 1, .2)), 'hair_top': ('Standing', 0, 'Head', .7, (.1, -.3, 1)),
    'hair_wide': ('Standing', 0, 'Head', .75, (.5, -.85, .2)), 'torso': ('Standing', 0, 'Spine2', .7, (0, -1, .05)),
    'back': ('Standing', 0, 'Spine2', .8, (0, 1, .1)), 'hand_l': ('Standing', 0, 'Hand_L', .26, (.4, -.8, .3)),
    'hand_r': ('Standing', 0, 'Hand_R', .26, (-.4, -.8, .3)), 'arm_l': ('Standing', 0, 'UpperArm_L', .6, (.9, -.4, .1)),
    'column': ('Standing', 0, 'Col_02', 1.0, (0, -1, .1)), 'coil': ('Standing', 0, 'Root', .9, (.5, -.8, .5)),
    'tail_side': ('Standing', 0, 'Tail_12', 2.4, (1, -.2, .5)), 'rattle': ('Standing', 0, 'Tail_29', .5, (.6, -.6, .5)),
    'attack': ('Attack', 24, 'Spine2', 1.6, (.3, -1, .2)), 'attack_hand': ('Attack', 24, 'Hand_R', .4, (.3, -1, .2)),
    'death': ('Death', 36, 'Col_04', 3.0, (1, -.3, .6)), 'death_coil': ('Death', 24, 'Root', 1.0, (.3, -1, .3)),
    'walk': ('Walking', 10, 'Col_03', 3.2, (1, -.6, .5)),
    'tail_top': ('Standing', 0, 'Tail_08', 1.3, (.2, -.1, 1)), 'tail_top2': ('Standing', 0, 'Tail_20', 1.3, (.2, -.1, 1)),
    'death_belly': ('Death', 36, 'Col_04', 1.4, (.2, -1, .3)), 'hair_side': ('Standing', 0, 'Head', .8, (1, -.1, .1)),
    'bust_l': ('Standing', 0, 'Spine2', .55, (1, -.3, .1)), 'bust_r': ('Standing', 0, 'Spine2', .55, (-1, -.3, .1)),
    'lower_back': ('Standing', 0, 'Pelvis', .9, (0, 1, .1)), 'flank_r': ('Standing', 0, 'Col_02', 1.2, (-1, 0, .2))}
if len(sys.argv) > sys.argv.index('--') + 2:
    SPOTS = {k: SPOTS[k] for k in sys.argv[sys.argv.index('--') + 2].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
