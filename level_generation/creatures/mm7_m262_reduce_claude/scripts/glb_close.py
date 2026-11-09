"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): MM7 Harpy spots (close_m262.py; source / reduced smooth / reduced flat side by side via pair_sheet.py). Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Walking', 0, 'B_Head', .5, (0, -1, .15)), 'face_q34': ('Walking', 0, 'B_Head', .5, (-.7, -.7, .2)),
         'face_r': ('Walking', 0, 'B_Head', .55, (-1, 0, .05)), 'hair_back': ('Walking', 0, 'B_Head', .8, (0, 1, .1)),
         'hand_r': ('Walking', 0, 'B_R_Hand', .4, (-.5, -.8, .3)), 'hand_l': ('Walking', 0, 'B_L_Hand', .4, (.5, -.8, .3)),
         'knife_atk': ('Attack', 24, 'B_R_Hand', .55, (-.4, -.8, .3)), 'chest': ('Walking', 0, 'B_Spine1', .9, (0, -1, .1)),
         'talon_r': ('Walking', 0, 'B_R_Foot', .45, (-.6, -.7, .1)), 'talon_l': ('Walking', 0, 'B_L_Foot', .45, (.6, -.7, .1)),
         'talon_atk': ('Attack', 24, 'B_R_Foot', .6, (0, -1, .2)), 'legs': ('Walking', 0, 'B_Pelvis', 1.0, (0, -1, 0)),
         'wings_front': ('Walking', 0, 'B_Spine2', 2.6, (0, -1, .15)), 'wings_back': ('Walking', 0, 'B_Spine2', 2.6, (0, 1, .3)),
         'tail': ('Walking', 0, 'B_Pelvis', 1.0, (.3, 1, -.1)), 'attack': ('Attack', 24, 'B_Spine1', 2.6, (-.7, -.7, .3)),
         'hit': ('Hit', 6, 'B_Spine1', 2.6, (0, -1, .2)), 'death': ('Death', 52, 'B_Pelvis', 2.8, (.6, -.6, .6))}
if os.environ.get('SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['SPOTS'].split(',')}
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
        cam.location = c + Vector(d).normalized() * 6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
