"""Textured (Eevee) and clay close-ups straight from GLBs (their own normals, no weld) at Ebora's reduction spots:
legs/studs front and back, hips in Running, shoulders in Land, belt, back, hands, whole body. Variant via REA_VARIANT
(KHR_materials_variants index applied by swapping primitive materials on import is not supported, so the default
material = Ebora tier). Usage: blender -b -P close_glb.py -- <label=glb,...>  -> review/close/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'close'); os.makedirs(out, exist_ok=True)
F, B, L, R = (0, -1, .12), (0, 1, .15), (1, 0, .1), (-1, 0, .1)
SPOTS = {  # colloidal (2.01 m, faces -y; head dome 0.9 m wide, hands 0.5 m)
    'whole_front': ('Standing', 0, 'Bip01 Spine', 2.4, F), 'whole_back': ('Standing', 0, 'Bip01 Spine', 2.4, B),
    'whole_q34': ('Standing', 0, 'Bip01 Spine', 2.4, (.7, -.7, .2)), 'whole_side': ('Standing', 0, 'Bip01 Spine', 2.4, L),
    'legs_front': ('Standing', 0, 'Bip01 L Calf', 1.2, F), 'legs_back': ('Standing', 0, 'Bip01 L Calf', 1.2, B),
    'feet': ('Standing', 0, 'Bip01 L Foot', .8, (.4, -.8, .5)),
    'torso_front': ('Standing', 0, 'Bip01 Spine1', 1.0, F), 'torso_back': ('Standing', 0, 'Bip01 Spine2', 1.0, B),
    'torso_side': ('Standing', 0, 'Bip01 Spine1', 1.0, R),
    'hips_run': ('Running', 6, 'Bip01 Pelvis', .9, (.6, -.8, .1)),
    'armpit_atk': ('AttackMelee', 10, 'Bip01 R UpperArm', .7, (-.6, -.8, .2)), 'arms_cast': ('AttackRanged', 18, 'Bip01 Spine2', 1.4, F),
    'head_front': ('Standing', 0, 'Bip01 Head', .9, F), 'head_q34': ('Standing', 0, 'Bip01 Head', .9, (.7, -.7, .15)),
    'head_side': ('Standing', 0, 'Bip01 Head', 1.0, (1, 0, .1)), 'head_back': ('Standing', 0, 'Bip01 Head', 1.1, (0, 1, .3)),
    'head_low': ('Standing', 0, 'Bip01 Head', .9, (-.6, -.7, -.4)), 'head_qback': ('Standing', 0, 'Bip01 Head', 1.1, (-.7, .7, .3)),
    'head_fidget': ('Fidget', 40, 'Bip01 Head', 1.0, (.6, -.8, .1)),
    'hand_l': ('Standing', 0, 'Bip01 L Hand', .45, (.5, -.8, .1)), 'hand_r': ('Standing', 0, 'Bip01 R Hand', .45, (-.5, -.8, .1)),
    'hand_l_back': ('Standing', 0, 'Bip01 L Hand', .45, (.9, .3, .1)), 'hands_cast': ('AttackRanged', 18, 'Bip01 R Hand', .6, (0, -1, .2)),
    'fist_atk': ('AttackMelee', 10, 'Bip01 R Hand', .6, (-.4, -.9, .2)),
    'shoulder_hit2': ('Hit2', 4, 'Bip01 R UpperArm', .8, (-.6, -.8, .2)), 'shoulder_hit2_b': ('Hit2', 4, 'Bip01 R UpperArm', .8, (-.6, .8, .2)),
    'hips_cast': ('AttackRanged', 12, 'Bip01 Pelvis', 1.0, (.3, -.9, .1)),
    'death': ('Death', 30, 'Bip01 Pelvis', 2.2, (.5, -.5, .7)), 'death2': ('Death2', 25, 'Bip01 Pelvis', 2.2, (-.5, -.5, .7)),
}
only = os.environ.get('REA_SPOTS')
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb) if not glb.startswith('/') else glb)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 640
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, (act, frame, b, size, d) in SPOTS.items():
        if only and spot not in only.split(','):
            continue
        rig.animation_data.action = bpy.data.actions[act]
        if bpy.data.actions[act].slots:
            rig.animation_data.action_slot = bpy.data.actions[act].slots[0]
        sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size; cam.data.clip_end = 20
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('CLOSE done')
