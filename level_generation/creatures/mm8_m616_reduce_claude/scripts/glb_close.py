"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, torso, hands and cuffs, back, tail coil (MM8 Naga).
Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Fly', 0, 'Head', .16, (0, -1, .15)), 'head_q34': ('Fly', 0, 'Head', .16, (.7, -.7, .2)),
         'head_side': ('Fly', 0, 'Head', .16, (-1, 0, .1)), 'jaw_open': ('Attack', 20, 'Head', .2, (.6, -.7, -.1)),
         'ribs_side': ('Fly', 0, 'Chest', .32, (-1, 0, .1)), 'ribs_front': ('Fly', 0, 'Chest', .32, (.3, -1, -.2)),
         'spine_top': ('Fly', 0, 'Chest', .5, (0, .2, 1)),
         'wing_l': ('Fly', 0, 'LWingFore', .62, (.1, -1, .3)), 'wing_r': ('Fly', 0, 'RWingFore', .62, (-.1, -1, .3)),
         'wing_l_back': ('Fly', 0, 'LWingFore', .62, (.1, 1, .4)),
         'fore_claw': ('Fly', 0, 'LForeFoot', .12, (.5, -.8, .1)), 'hind_claw': ('Fly', 0, 'RHindFoot', .14, (-.5, -.8, .1)),
         'tail': ('Fly', 0, 'Tail5', .5, (1, -.2, .6)), 'tail_tip': ('Fly', 0, 'Tail10', .16, (.6, -.3, .7)),
         'attack': ('Attack', 24, 'Chest', 1.3, (.3, -1, .2)), 'death': ('Death', 18, 'Chest', 1.3, (1, -.3, .5))}
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
