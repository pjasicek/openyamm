"""Rest-pose textured close-ups of given model-space points (Z up) from above and below, for flagged faces.
Usage: blender -b -P spot_views.py -- <label=glb,...> <x,y,z;...> <out dir>"""
import math, os, sys, bpy
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
items, pts, out = [a.split('=') for a in args[0].split(',')], [Vector([float(x) for x in p.split(',')]) for p in args[1].split(';')], args[2]
os.makedirs(out, exist_ok=True)
for label, glb in items:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_clear()
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .09; sc.render.resolution_x = sc.render.resolution_y = 360
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.6, .6, .62, 1)
    sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sun.data.energy = 3; sc.collection.objects.link(sun)
    sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for i, p in enumerate(pts):
        for side, d in (('top', (0.05, 0.05, 1)), ('bot', (0.05, 0.05, -1))):
            dv = Vector(d).normalized(); cam.location = p + dv * 2
            cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler(); sun.rotation_euler = cam.rotation_euler
            sc.render.filepath = os.path.join(out, f'{label}_p{i}_{side}.png'); bpy.ops.render.render(write_still=True)
print('SPOTS done')
