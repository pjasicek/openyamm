"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): the five heads, the head-to-neck
joints, back, flank and paws. MM7 Hydra spots (faces -y; heads 1..5 from -x to +x). Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'heads_front': ('Standing', 0, 'Head3', 2.0, (0, -1, .2)), 'h1_q34': ('Standing', 0, 'Head1', .6, (-.7, -.7, .3)),
         'h2_q34': ('Standing', 0, 'Head2', .6, (-.7, -.7, .3)), 'h3_front': ('Standing', 0, 'Head3', .6, (0, -1, .15)),
         'h4_q34': ('Standing', 0, 'Head4', .6, (.7, -.7, .3)), 'h5_q34': ('Standing', 0, 'Head5', .6, (.7, -.7, .3)),
         'necks_back': ('Standing', 0, 'Spine3', 1.6, (0, 1, .5)), 'flank_r': ('Standing', 0, 'Spine2', 1.8, (-1, 0, .1)),
         'back': ('Standing', 0, 'Spine2', 1.6, (.4, .3, 1)), 'fpaw_r': ('Standing', 0, 'FrontPaw_R', .4, (-.5, -.8, .3)),
         # head 5 review (horns -> eyes): front, both three-quarters, both eyes close; drawn in a +-0.35 m slab
         'h5r_front': ('Standing', 0, 'Head5', .55, (0, -1, .15)), 'h5r_q34r': ('Standing', 0, 'Head5', .55, (-.7, -.7, .25)),
         'h5r_q34l': ('Standing', 0, 'Head5', .55, (.7, -.7, .25)), 'h5r_eye_r': ('Standing', 0, 'Head5@0.683,-1.205,1.405', .2, (-.8, -.55, .2)),
         'h5r_eye_l': ('Standing', 0, 'Head5@0.915,-1.207,1.403', .2, (.8, -.6, .2)),
         'h5r_mouth_l': ('Standing', 0, 'Head5@0.850,-1.322,1.354', .2, (.8, -.6, .0))}
if os.environ.get('GLB_SPOTS'):
    SPOTS = {k: SPOTS[k] for k in os.environ['GLB_SPOTS'].split(',')}
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
        if '@' in b:  # a rest-space point carried by the bone (the eyes)
            b, p = b.split('@'); pb = rig.pose.bones[b]
            c = rig.matrix_world @ (pb.matrix @ pb.bone.matrix_local.inverted() @ (rig.matrix_world.inverted() @ Vector([float(x) for x in p.split(',')])))
        else:
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        cam.data.clip_start, cam.data.clip_end = (4 - .35, 4 + .35) if spot.startswith('h5r') else (.1, 10)
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
