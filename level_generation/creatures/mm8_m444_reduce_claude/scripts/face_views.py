"""Textured face close-ups straight from GLBs (viewer tier files): front, three-quarter, side and back of the head,
Standing frame 0 -> review/face/<label>_<view>.png. Usage: blender -b -P face_views.py -- <label=glb,...>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'face'); os.makedirs(out, exist_ok=True)
VIEWS = {'front': (0, -1, .05), 'q34': (-.7, -.7, .1), 'side': (-1, 0, .05), 'back': (.3, 1, .25)}
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == 'Standing' or a.name == 'Standing')
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(0)
    pb = rig.pose.bones['B_Head']; c = rig.matrix_world @ ((pb.head + pb.tail) / 2) + Vector((0, 0, -.03))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .34; sc.render.resolution_x = sc.render.resolution_y = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for view, d in VIEWS.items():
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{view}.png'); bpy.ops.render.render(write_still=True)
print('FACEVIEWS done')
