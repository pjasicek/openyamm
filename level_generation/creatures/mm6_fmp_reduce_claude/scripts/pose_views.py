"""Posed whole-body renders of a viewer GLB at given clip frames (the ladder's worst frames), textured, framed on the
posed mesh. Usage: blender -b -P pose_views.py -- <glb> <label> <clip:frame,...> -> review/pose/<label>_<clip><frame>_<view>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label, frames = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600
sc.render.engine = 'BLENDER_EEVEE'
os.makedirs(os.path.join(HERE, 'review/pose'), exist_ok=True)
for cf in frames.split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    pts = [body.matrix_world @ v.co for v in ev.vertices]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    c = (lo + hi) / 2; size = max(hi - lo) * 1.1
    for view, d in {'q34': (.7, -.7, .35), 'side': (1, 0, .15), 'back': (-.6, .8, .3)}.items():
        dv = Vector((-d[1], d[0], d[2])).normalized()
        cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(HERE, 'review/pose', f'{label}_{clip}{f}_{view}.png'); bpy.ops.render.render(write_still=True)
