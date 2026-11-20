"""Textured close-ups of flagged prop spots (flag_spots.py on the prop npz: glTF prop-space 'x,y,z/nx,ny,nz;...')
straight from forearm GLBs, along the spot normal and 45 deg beside it.
Usage: blender -b -P prop_spots.py -- <label=glb,...> <spots> <out dir>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
g2b = lambda v: Vector((v[0], -v[2], v[1]))
spots = []
for s in a[1].split(';'):
    p, n = s.split('/'); spots.append((g2b([float(x) for x in p.split(',')]), g2b([float(x) for x in n.split(',')]).normalized()))
out = os.path.join(HERE, a[2]); os.makedirs(out, exist_ok=True)
for item in a[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Sword':
            o.hide_render = True
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('SPOT_SIZE', '.08')); cam.data.clip_end = 5
    sc.render.resolution_x = sc.render.resolution_y = 300; sc.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.6, .6, .62, 1); sc.view_settings.view_transform = 'Standard'
    sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sun.data.energy = 3; sc.collection.objects.link(sun)
    for i, (p, n) in enumerate(spots):
        side = n.cross(Vector((0, 0, 1))); side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        for tag, d in (('out', n), ('side', (n + side).normalized())):
            cam.location = p + d * 1.5; cam.rotation_euler = (p - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sun.rotation_euler = cam.rotation_euler
            sc.render.filepath = os.path.join(out, f'{label}_p{i}_{tag}.png'); bpy.ops.render.render(write_still=True)
print('PROPSPOTS', len(spots))
