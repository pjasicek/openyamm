"""Textured temple close-ups (right and left, just above and in front of each ear) of the per-LOD GLBs written by
lod_check.py (work/lodcheck_<label>_<level>.glb), Standing frame 0, straight from the GLB (own normals).
Usage: blender -b -P temple_views.py -- <label,...> [levels, default 0123] -> review/temple/<label>_<level>_<side>.png"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, 'review', 'temple'); os.makedirs(out, exist_ok=True)
levels = [int(c) for c in (args[1] if len(args) > 1 else '0123')]
# (rest-pose look-at point relative to B_Head, view direction, ortho size); the Pirate faces -Y, his right is -X
VIEWS = {'right': ((-0.07, -0.03, 0.0), (-1, -.45, .15), .13), 'left': ((0.06, -0.03, 0.0), (1, -.45, .15), .13),
         'right_wide': ((-0.05, -0.0, 0.0), (-1, -.2, .2), .26), 'left_wide': ((0.05, -0.0, 0.0), (1, -.2, .2), .26)}
for label in args[0].split(','):
    for level in levels:
        bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
        bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{level}.glb'))
        rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
        sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
        w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
        sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x = sc.render.resolution_y = 500
        pb = rig.pose.bones['B_Head']; head = rig.matrix_world @ pb.head
        for view, (off, d, size) in VIEWS.items():
            c = head + Vector(off) + Vector((0, 0, 0.07)); cam.data.ortho_scale = size
            cam.location = c + Vector(d).normalized() * 2; cam.data.clip_start = 1.5
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label}_{level}_{view}.png'); bpy.ops.render.render(write_still=True)
print('TEMPLE done')
