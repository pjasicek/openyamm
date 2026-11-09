"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals; after mm8_m492_reduce_claude):
face front/q34, eye, hand, torso, boots. Ground truth for normal checks: the welded source.blend changes custom normals
(stored relative to the default normals). A label ending in '~smooth' clears the file's normals first.
Usage: blender -b -P glb_close.py -- <label=glb,...> [spot,...]  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .5, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .5, (.7, -.7, .2)),
         'eye': ('Standing', 0, 'B_Head', .2, (0, -1, .05), (0, 0, .11)), 'rhand': ('Standing', 0, 'B_R_Hand', .35, (-.5, -1, .1)),
         'torso': ('Standing', 0, 'B_Spine2', .9, (.2, -1, .05)), 'boots': ('Standing', 0, 'B_L_Calf', .9, (.4, -1, .1)),
         'back': ('Standing', 0, 'B_Spine1', 1.0, (-.3, 1, .1)), 'scap': ('Standing', 0, 'B_Spine2', .45, (-.3, 1, .1), (0, 0, .05)), 'overhead': ('Attack', 22, 'B_Head', 1.3, (.6, -1, .2)),
         'death30': ('Death', 30, 'B_Spine', 1.8, (1, -.6, .6)), 'up_f': ('Standing', 0, 'B_Spine2', 1.1, (0, -1, 0.05)), 'lo_f': ('Standing', 0, 'B_Pelvis', 1.3, (0, -1, 0.05), (0, 0, -.45)),
         'up_b': ('Standing', 0, 'B_Spine2', 1.1, (0, 1, 0.05)), 'lo_b': ('Standing', 0, 'B_Pelvis', 1.3, (0, 1, 0.05), (0, 0, -.45)),
         'up_l': ('Standing', 0, 'B_Spine2', 1.1, (1, 0, 0.05)), 'lo_l': ('Standing', 0, 'B_Pelvis', 1.3, (1, 0, 0.05), (0, 0, -.45)),
         'up_r': ('Standing', 0, 'B_Spine2', 1.1, (-1, 0, 0.05)), 'lo_r': ('Standing', 0, 'B_Pelvis', 1.3, (-1, 0, 0.05), (0, 0, -.45)),
         'whole': ('Standing', 0, 'B_Spine', 2.6, (.6, -1, .15)),
         'lforearm_back': ('Standing', 0, 'B_L_Forearm', .45, (.3, 1, .1)), 'rhand_wrap': ('Standing', 0, 'B_R_Hand', .3, (-.5, -1, .1))}
if len(args) > 1:
    SPOTS = {k: SPOTS[k] for k in args[1].split(',')}
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    if label.endswith('~smooth'):
        for o in bpy.data.objects:
            if o.type == 'MESH':
                bpy.context.view_layer.objects.active = o; bpy.ops.mesh.customdata_custom_splitnormals_clear()
                for p in o.data.polygons:
                    p.use_smooth = True
        label = label[:-7] + '_smooth'
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 20; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, spec in SPOTS.items():
        act, frame, b, size, d = spec[:5]; off = Vector(spec[5]) if len(spec) > 5 else Vector()
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2) + off
        cam.location = c + Vector(d).normalized() * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
