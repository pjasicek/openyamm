"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): face front/side/three-quarter,
chest and right hand. Ground truth for normal checks; the welded source.blend changes custom normals (stored
relative to the default normals). Usage: blender -b -P glb_close.py -- <label=glb,...> [spot,...]  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'face_front': ('Standing', 0, 'B_Head', .26, (0, -1, .05)), 'face_side': ('Standing', 0, 'B_Head', .26, (1, 0, .05)),
         'face_q34': ('Standing', 0, 'B_Head', .26, (.7, -.7, .1)), 'chest': ('Standing', 0, 'B_Spine1', .5, (.2, -1, .1)),
         'hand_r': ('Attack', 24, 'B_R_Hand', .22, (-.3, -1, .4)), 'cuirass_mid': ('Standing', 0, 'B_Spine1', .22, (.2, -1, .1)),
         'cuirass_low': ('Standing', 0, 'B_Spine', .3, (0, -1, .1)), 'neck_back': ('Standing', 0, 'B_Neck', .3, (.4, 1, .3)),
         'sleeve_l': ('Standing', 0, 'B_L_Hand', .35, (.3, -1, .2)), 'robe_full': ('Standing', 0, 'B_Spine1', 1.25, (.3, -1, .05)),
         'robe_back': ('Standing', 0, 'B_Spine1', 1.25, (-.3, 1, .05))}
if len(sys.argv) > sys.argv.index('--') + 2:
    SPOTS = {k: SPOTS[k] for k in sys.argv[sys.argv.index('--') + 2].split(',')}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Necromancer':
            o.hide_render = True
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 20; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    acts = {a.name.rsplit('|', 1)[-1]: a for a in bpy.data.actions}
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = acts[act]
        if acts[act].slots:
            rig.animation_data.action_slot = acts[act].slots[0]
        sc.frame_set(frame); pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
