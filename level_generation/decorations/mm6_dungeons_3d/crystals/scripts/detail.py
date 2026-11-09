"""Close-up review renders of a tall model's ends (corinth capital and base) from the front and three-quarter view,
cropped bands of the model's height: review/<prop>/detail_<band>_y<yaw>.png.
Usage: blender --background --python detail.py -- <prop> <band low> <band high> [...] (fractions of the height)"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, bands = args[0], [(float(a), float(b)) for a, b in zip(args[1::2], args[2::2])]
out = os.path.join(cl.HERE, 'review', prop)
pl.reset()
bpy.ops.import_scene.gltf(filepath=os.path.join(cl.WORK, f'{prop}_export.glb'))
lod0 = min([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: len(o.name))
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not lod0:
        o.hide_render = True
for m in bpy.data.materials:
    if m.node_tree and m.get('openyamm_specular') is not None:
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Specular IOR Level'].default_value = 0.5 * float(m['openyamm_specular'])
scene = pl.setup_render((512, 512))
world = scene.world.node_tree.nodes
bg = next(n for n in world if n.type == 'BACKGROUND'); bg.inputs['Color'].default_value = (0.6, 0.6, 0.6, 1)
bpy.data.objects['Sun'].data.energy = 0.6
lo, hi = pl.bounds([lod0])
cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); scene.collection.objects.link(cam)
scene.camera = cam; cam.data.lens = 50
fov = 2 * math.atan(cam.data.sensor_width / 100)
for a, b in bands:
    z0, z1 = lo.z + (hi.z - lo.z) * a, lo.z + (hi.z - lo.z) * b
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (z0 + z1) / 2))
    radius = max(z1 - z0, hi.x - lo.x) * 0.6
    for yaw, elevation in ((0, 6), (40, 22)):
        y, e = math.radians(yaw), math.radians(elevation)
        d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
        cam.location = centre + d * radius / math.sin(fov / 2)
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(out, f'detail_{int(a * 100):02d}_y{yaw:03d}.png')
        bpy.ops.render.render(write_still=True)
