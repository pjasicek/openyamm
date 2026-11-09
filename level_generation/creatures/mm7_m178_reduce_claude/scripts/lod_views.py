"""Whole-body renders of the per-LOD GLBs written by lod_check.py (work/lodcheck_<label>_<level>.glb): Standing frame
0 three-quarter, Attack side view, head and right hand close-ups -> review/lods/<label>_<level>_<view>.png. Usage: blender -b -P lod_views.py -- <label,...>"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'lods'); os.makedirs(out, exist_ok=True)
for label in sys.argv[sys.argv.index('--') + 1].split(','):
    for level in range(4):
        bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
        bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{level}.glb'))
        rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('LOD_SCALE', '2.0'))
        sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
        sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.collection.objects.link(sun)
        w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
        sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x = sc.render.resolution_y = 400
        S = float(os.environ.get('LOD_SCALE', '2.0')); CZ = float(os.environ.get('LOD_CZ', '.85'))
        for view, act, frame, d, c, scale in (('q34', 'Standing', 0, (.75, -.75, .35), (0, 0, CZ), S),
                                              ('attack', 'Attack', int(os.environ.get('LOD_ATTACK_F', '30')), (1, -.2, .15), (0, 0, CZ), S),
                                              ('head', 'Standing', 0, (-.6, -.8, .15), (0, -.15, 1.5), .6),   # m178: face, horns, spikes
                                              ('hand', 'Standing', 0, (-.6, -.8, .15), (-.5, -.05, .5), .6)):
            rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame); cam.data.ortho_scale = scale
            c = Vector(c); cam.location = c + Vector(d).normalized() * 3
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out, f'{label}_{level}_{view}.png'); bpy.ops.render.render(write_still=True)
print('LODVIEWS done')
