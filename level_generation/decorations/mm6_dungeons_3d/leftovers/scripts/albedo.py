"""Albedo check: renders LOD0 of an exported GLB from the front with every material flat (emission of its base
colour times COLOR_0, no lighting) and prints the mean sRGB of the covered pixels: overall, and for each material
alone (the others held out). Compared with the native sprite's mean (sheet.py) this gives the COLOR_0 tint
(linear multiplier = linear(native) / linear(albedo)). Usage: blender --background --python albedo.py -- <glb> [yaw]"""
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll  # noqa: E402

pl = ll.pl
args = sys.argv[sys.argv.index('--') + 1:]
glb, yaw = args[0], int(args[1]) if len(args) > 1 else 0
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
lod0 = min(meshes, key=lambda o: len(o.name))
for o in meshes:
    if o is not lod0:
        bpy.data.objects.remove(o)
flat = {}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    emission = nt.nodes.new('ShaderNodeEmission')
    link = bsdf.inputs['Base Color'].links[0] if bsdf and bsdf.inputs['Base Color'].links else None
    if link:
        nt.links.new(link.from_socket, emission.inputs['Color'])
    else:
        emission.inputs['Color'].default_value = bsdf.inputs['Base Color'].default_value
    holdout = nt.nodes.new('ShaderNodeHoldout')
    flat[m.name] = (nt, out, emission, holdout)
scene = pl.setup_render((512, 512))
for o in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(o)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
path = os.path.join(ll.WORK, '_albedo.png')


def render(only=None):
    for name, (nt, out, emission, holdout) in flat.items():
        nt.links.new((emission if only in (None, name) else holdout).outputs[0], out.inputs['Surface'])
    pl.render_views([lod0], ll.WORK, '_albedo', views=((yaw, 4),))
    image = bpy.data.images.load(os.path.join(ll.WORK, f'_albedo_y{yaw:03d}.png'), check_existing=False)
    px = np.array(image.pixels[:]).reshape(-1, 4)
    bpy.data.images.remove(image)
    covered = px[:, 3] > 0.5
    return tuple(int(round(v * 255)) for v in px[covered, :3].mean(0)), int(covered.sum())


print('ALBEDO all', *render())
for name in flat:
    print('ALBEDO', name, *render(name))
os.remove(os.path.join(ll.WORK, f'_albedo_y{yaw:03d}.png'))
