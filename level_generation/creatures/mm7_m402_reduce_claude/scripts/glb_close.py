"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): face, fangs, eyes, knees, fringe, feet, abdomen, underside, corpse.
MM7 Spider spots. Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_q34': ('Standing', 0, 'Fang_R', .5, (-.7, -.7, .3)), 'face_side': ('Standing', 0, 'Fang_L', .5, (1, 0, .1)),
         'eyes': ('Standing', 0, 'Thorax', .55, (0, -.4, 1)), 'fangs_open': ('Attack', 16, 'Fang_R', .5, (-.4, -1, -.1)),
         'knees_r': ('Standing', 0, 'Thorax', 1.6, (-1, 0, .35)), 'fringe_r1': ('Standing', 0, 'Tibia_R1', .45, (-1, -.2, .1)),
         'feet_r': ('Standing', 0, 'Tarsus_R3', .4, (-.6, -.6, .3)), 'abdomen': ('Standing', 0, 'Abdomen', 1.1, (.6, .7, .6)),
         'under': ('Standing', 0, 'Thorax', 2.0, (.1, .1, -1)), 'dead': ('Dead', 0, 'Thorax', 2.4, (-.6, -.6, .5)), 'death9': ('Death', 9, 'Thorax', 2.6, (-.7, -.7, .4))}
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
