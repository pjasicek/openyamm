"""Textured rest-pose close-ups at given points (from candidate faces), camera along the face normal, for several
GLBs. Usage: blender -b -P spot_views.py -- <out dir> <points.json> <label=glb,...>  (points: [[name,[x,y,z],[nx,ny,nz]],...])"""
import json, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, a[0]); os.makedirs(out, exist_ok=True); pts = json.load(open(os.path.join(HERE, a[1])))
for item in a[2].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data_clear()
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = .14; cam.data.clip_end = 10
    sc.render.resolution_x = sc.render.resolution_y = 300; sc.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .5, .5, 1); sc.view_settings.view_transform = 'Standard'
    for name, p, n in pts:
        # glTF Y-up export: Blender import restores Z-up, matching the npz rest positions
        c = Vector(p); d = Vector(n).normalized()
        cam.location = c + d * .6; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{name}_tex.png'); bpy.ops.render.render(write_still=True)
print('SPOTS done')
