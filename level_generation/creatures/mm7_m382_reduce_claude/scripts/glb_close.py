"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, muzzle, ears, bite, back, flank, paws, tail root.
MM7 rat spots (MM8 Wererat spots, sizes x CLOSE_K, default 2.2). Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Standing', 0, 'Head', .2, (0, -1, .15)), 'face_q34': ('Standing', 0, 'Head', .2, (-.7, -.7, .2)),
         'face_r': ('Standing', 0, 'Head', .22, (-1, 0, .05)), 'mouth_front': ('Standing', 0, 'Head', .09, (0, -1, .1)),
         'ears': ('Standing', 0, 'Head', .18, (0, .4, 1)), 'bite': ('Attack', 12, 'Head', .22, (-.7, -.7, 0)),
         'back': ('Standing', 0, 'Spine2', .55, (.4, .2, 1)), 'flank_r': ('Standing', 0, 'Spine2', .55, (-1, 0, .1)),
         'fpaw_r': ('Standing', 0, 'FrontPaw_R', .12, (-.5, -.8, .3)), 'hpaw_l': ('Standing', 0, 'HindPaw_L', .14, (.7, -.5, .3)),
         'tail_root': ('Standing', 0, 'Tail1', .3, (1, .3, .3))}
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
        size *= float(os.environ.get('CLOSE_K', '2.2'))
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
