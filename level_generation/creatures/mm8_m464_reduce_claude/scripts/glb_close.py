"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head front/side, forefoot, flank.
MM8 Vampire female peasant spots. Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .26, (0, -1, .05)), 'face_q34': ('Standing', 0, 'B_Head', .26, (-.7, -.7, .1)),
         'rhand': ('Standing', 0, 'B_R_Hand', .18, (-.5, -.8, .2)), 'torso_front': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)),
         'torso_back': ('Standing', 0, 'B_Spine1', .6, (0, 1, .1)),
         'ear_r': ('Standing', 0, 'B_Head', .22, (-1, .3, .2)), 'ear_l': ('Standing', 0, 'B_Head', .22, (1, .3, .2)),
         'head_back': ('Standing', 0, 'B_Head', .3, (0, 1, .3)), 'lhand': ('Standing', 0, 'B_L_Hand', .18, (.5, -.8, .2)),
         'chest': ('Standing', 0, 'B_Spine2', .35, (.2, -1, .1)), 'neck': ('Standing', 0, 'B_Neck', .2, (.15, -1, .05)),
         'legs': ('Standing', 0, 'B_L_Calf', .8, (-.3, -1, .2))}
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
