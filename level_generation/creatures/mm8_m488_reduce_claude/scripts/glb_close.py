"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, torso, hands and cuffs, back, tail coil (MM8 Naga).
Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Standing', 0, 'B_Head', .5, (0, -1, .1)), 'head_q34': ('Standing', 0, 'B_Head', .5, (-.7, -.7, .2)),
         'head_side': ('Standing', 0, 'B_Head', .5, (1, 0, .1)), 'head_back': ('Standing', 0, 'B_Head', .55, (0, 1, .2)),
         'horns_top': ('Standing', 0, 'B_Head', .55, (0, -.3, 1)), 'muzzle': ('Standing', 0, 'B_Head', .28, (.3, -1, -.2)),
         'eye_r': ('Standing', 0, 'B_Head', .2, (-.6, -.8, .1)), 'head_right': ('Standing', 0, 'B_Head', .5, (-1, 0, .1)),
         'hand_r': ('Standing', 0, 'B_R_Hand', .3, (-.6, -.8, .2)), 'hand_l': ('Standing', 0, 'B_L_Hand', .3, (.6, -.8, .2)),
         'fist_attack': ('Attack', 24, 'B_R_Hand', .35, (-.3, -1, .2)),
         'torso': ('Standing', 0, 'B_Spine2', .9, (0, -1, .05)), 'wrap': ('Standing', 0, 'B_Pelvis', .8, (0, -1, .1)),
         'back': ('Standing', 0, 'B_Spine1', 1.1, (0, 1, .1)), 'legs': ('Standing', 0, 'B_L_Calf', 1.1, (.3, -1, .1)),
         'hooves': ('Standing', 0, 'B_R_Foot', .5, (-.6, -.8, .3)), 'run_knee': ('Running', 8, 'B_L_Calf', .9, (1, -.3, .1)),
         'arm_up': ('Fidget', 40, 'B_R_UpperArm', .9, (-.5, -1, .3)),
         'attack': ('Attack', 24, 'B_Spine2', 2.2, (.3, -1, .2)), 'death': ('Death', 36, 'B_Pelvis', 2.6, (1, -.3, .5)),
         'legs_back': ('Standing', 0, 'B_L_Calf', 1.1, (.2, 1, .1)),
         'atk56_side': ('Attack', 28, 'B_Spine2', 1.0, (1, -.2, .1)), 'atk56_top': ('Attack', 28, 'B_Spine2', 1.0, (.1, -.3, 1)),
         'atk50_front': ('Attack', 25, 'B_Spine2', 1.0, (.2, -1, .1)), 'atk62_front': ('Attack', 31, 'B_Spine2', 1.0, (.2, -1, .1))}
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
    for spot, (act, frame, b, size, d) in [(k, s) for k, s in SPOTS.items() if not os.environ.get('GLB_SPOTS') or k in os.environ['GLB_SPOTS'].split(',')]:
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
