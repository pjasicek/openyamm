"""Whole-body renders of a viewer GLB in clip poses (Attack impact, Walking mid, Death mid, Hit), front and side.
Usage: blender -b -P pose_views.py -- <glb> <label> -> review/pose/<label>_<clip>_<view>.png"""
import bpy, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 420; sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review', 'pose'), exist_ok=True)
for clip, frac in [('Standing', 0.0), ('Attack', 0.5), ('Walking', 0.25), ('Death', 0.4), ('Hit', 0.3)]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; sc.frame_set(int(f0 + (f1 - f0) * frac))
    c = Vector((0, 0, 0.8))
    for view, dv in [('front', Vector((1, 0, .1))), ('side', Vector((0, -1, .1)))]:
        dv.normalize(); cam.location = c + dv * 5; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = 2.1
        sc.render.filepath = os.path.join(HERE, 'review', 'pose', f'{label}_{clip}_{view}.png'); bpy.ops.render.render(write_still=True)
