"""Clay and textured close-ups straight from GLBs (no weld, the file's own normals): head, hands, toes, torso, pack, shorts, corpse (Ogre Peasant spots).
Ground truth for normal checks; the welded source.blend changes custom normals (stored relative to the default
normals). Usage: blender -b -P glb_close.py -- <label=glb,...>  -> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
SPOTS = {'head_front': ('Standing', 0, 'B_Head', .32, (0, -1, .1)), 'head_side': ('Standing', 0, 'B_Head', .32, (1, -.2, .1)),
         'hand_l': ('Standing', 0, 'B_L_Finger21', .26, (.5, -.8, .1)), 'hand_r': ('Standing', 0, 'B_R_Finger21', .26, (-.5, -.8, .1)),
         'toes': ('Standing', 0, 'B_R_Toe0', .3, (0, -.3, 1)), 'feet_l': ('Standing', 0, 'B_L_Toe0', .3, (.5, -1, .6)),
         'torso': ('Standing', 0, 'B_Spine1', .8, (.3, -1, .1)), 'pack': ('Standing', 0, 'B_Spine2', .8, (-.4, 1, .2)),
         'shorts': ('Walking', 12, 'B_Pelvis', .7, (.2, -1, .1)), 'corpse': ('Dead', 0, 'B_Spine1', 1.9, (.7, -.7, .6))}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:  # only the skinned body (an add-on adds an icosphere to new scenes)
        if o.type == 'MESH' and not any(m.type == 'ARMATURE' for m in o.modifiers):
            o.hide_render = True
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
