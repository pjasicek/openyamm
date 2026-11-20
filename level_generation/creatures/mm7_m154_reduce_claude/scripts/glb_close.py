"""Clay and textured close-ups straight from viewer GLBs (no weld, the file's own normals; bow and arrow attached as
children of their joints by viewer_attach.py): face, helmet and horns, tunic front (emblem) and back, quiver, the bow
grip (right fist) standing and at full draw, the draw pinch (left hand), boots, Attack and Death (MM7 Archer m154).
Usage: blender -b -P glb_close.py -- <label=glb,...> [spot,...]  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
DRAW = int(os.environ.get('DRAW_FRAME', '26'))  # Attack full draw (24 fps import; release 1.167 s = frame 28)
SPOTS = {'head_front': ('Standing', 0, 'B_Head', .34, (0, -1, .1)), 'head_q34': ('Standing', 0, 'B_Head', .34, (.7, -.7, .2)),
         'head_side': ('Standing', 0, 'B_Head', .36, (-1, 0, .1)), 'head_back': ('Standing', 0, 'B_Head', .42, (0, 1, .2)),
         'helmet_top': ('Standing', 0, 'B_Head', .36, (.4, -.6, 1)),
         'torso': ('Standing', 0, 'B_Spine1', .8, (0, -1, .05)), 'back': ('Standing', 0, 'B_Spine1', .9, (0, 1, .1)),
         'quiver': ('Standing', 0, 'B_Spine2', .55, (.5, 1, .4)),
         'hand_r': ('Standing', 0, 'B_R_Hand', .3, (-.4, -.8, .3)), 'hand_l': ('Standing', 0, 'B_L_Hand', .3, (.4, -.8, .3)),
         'grip_draw': ('Attack', DRAW, 'B_R_Hand', .32, (0, -1, .3)), 'pinch_draw': ('Attack', DRAW, 'B_L_Hand', .32, (.3, -1, .3)),
         'attack': ('Attack', DRAW, 'B_Spine1', 1.9, (.3, -1, .2)),
         'boots': ('Standing', 0, 'B_L_Calf', .8, (.5, -.8, .1)), 'boots_back': ('Standing', 0, 'B_R_Calf', .8, (-.4, .9, .1)),
         'death': ('Death', 48, 'B_Pelvis', 2.3, (1, -.3, .5)),
         'bow': ('Standing', 0, 'B_R_Hand', 1.45, (-1, -.25, .1)), 'bow_draw': ('Attack', DRAW, 'B_R_Hand', 1.45, (.15, -1, .1)),
         'arrow_draw': ('Attack', DRAW, 'B_Spine2', .9, (-.2, -.5, 1))}
args = sys.argv[sys.argv.index('--') + 1:]
if len(args) > 1:
    SPOTS = {k: SPOTS[k] for k in args[1].split(',')}
for item in args[0].split(','):
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
        a = bpy.data.actions[act]; rig.animation_data.action = a
        if a.slots:
            rig.animation_data.action_slot = a.slots[0]
        sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
