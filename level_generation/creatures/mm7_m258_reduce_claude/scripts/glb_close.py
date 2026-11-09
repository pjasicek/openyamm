"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, beak, crest, wings from
above and below, wing tip, talons, hind paw, tail tuft, flank. MM7 Griffin spots (LOD0 node M258, base material). Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Fly', 0, 'Head', .45, (0, -1, .15)), 'head_q34': ('Fly', 0, 'Head', .45, (-.7, -.7, .2)),
         'beak': ('Attack', 16, 'Head', .3, (-.8, -.6, -.1)), 'crest': ('Fly', 0, 'Neck2', .55, (0, .4, 1)),
         'wing_l_top': ('Fly', 0, 'Wing2_L', 1.9, (.2, .1, 1)), 'wing_r_under': ('Fly', 0, 'Wing2_R', 1.9, (-.3, .1, -1)),
         'wing_r_tip': ('Fly', 0, 'Wing3_R', .8, (-.3, -.6, .5)), 'talon_l': ('Fly', 0, 'FrontPaw_L', .45, (.5, -.8, .3)),
         'hpaw_r': ('Fly', 0, 'HindPaw_R', .5, (-.7, -.3, .2)), 'tail': ('Fly', 0, 'Tail4', 1.0, (.3, .3, 1)),
         'flank_r': ('Fly', 0, 'Spine2', 1.8, (-1, 0, .1)), 'death': ('Death', 30, 'Spine2', 3.2, (.6, -.6, .6))}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'M258':
            o.hide_render = True
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
