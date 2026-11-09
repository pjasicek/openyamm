"""Textured rest-pose close-ups straight from GLBs at given points (texture-drift suspects): each point is framed from its
face normal direction. Usage: blender -b -P spot_rest.py -- <label=glb,...> <x,y,z,nx,ny,nz,size;...>  -> review/spots/<label>_<k>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'spots'); os.makedirs(out, exist_ok=True)
items, pts = sys.argv[sys.argv.index('--') + 1:][:2]
pts = [[float(x) for x in p.split(',')] for p in pts.split(';')]
for item in items.split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420; cam.data.clip_start = 0.01
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    for k, (x, y, z, nx, ny, nz, size) in enumerate(pts):
        c = Vector((x, y, z)); cam.location = c + Vector((nx, ny, nz)).normalized() * 0.5
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(out, f'{label}_{k}.png'); bpy.ops.render.render(write_still=True)
print('SPOTS done')
