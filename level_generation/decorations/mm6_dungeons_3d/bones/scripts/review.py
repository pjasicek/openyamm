"""Review renders of one exported (unlinked) GLB: LOD0 front 'flat' (each material's base colour times COLOR_0 as
emission, no lights: the colour a self-lit sprite replacement shows at light one), and LOD0 front, three-quarter
and side with a weak key light for shape; every LOD from the three-quarter view. Flipbook materials show their
first frame. Usage: blender --background --python review.py -- <prop> <export.glb>"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib as tlib  # noqa: E402

pl = tlib.pl
prop, glb = sys.argv[sys.argv.index("--") + 1:][:2]
SIDE = int(sys.argv[sys.argv.index("--") + 3]) if len(sys.argv) > sys.argv.index("--") + 3 else 90
out = os.path.join(tlib.HERE, 'review', prop); os.makedirs(out, exist_ok=True)
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
GLOWING = ('Flame', 'Fire', 'Embers', 'Coals')      # unlit in the engine
emissions = []
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        continue
    flip = m.get('openyamm_flipbook')
    if flip is not None:
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    links = bsdf.inputs['Base Color'].links
    if links:
        nt.links.new(links[0].from_socket, bsdf.inputs['Emission Color'])
    else:
        bsdf.inputs['Emission Color'].default_value = bsdf.inputs['Base Color'].default_value
    emissions.append((bsdf, flip is not None or m.name.split('.')[0] in GLOWING))
scene = pl.setup_render((512, 512))
sun = bpy.data.objects['Sun']
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')


def mode(flat):
    for bsdf, glow in emissions:
        bsdf.inputs['Emission Strength'].default_value = 1.0 if (flat or glow) else 0.75
    sun.hide_render = flat
    sun.data.energy = 1.6
    background.inputs['Strength'].default_value = 0.0 if flat else 0.25


lod0 = min(objects, key=lambda o: len(o.name))
mode(True)
for path in pl.render_views([lod0], out, 'flat', views=((0, 0),)):
    print('FLAT', path)
mode(False)
pl.render_views([lod0], out, 'lod0', views=((0, 6), (40, 22), (SIDE, 8)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((40, 20),))
print('REVIEW', out, [o.name for o in objects])
