"""Review renders of an exported (unlinked) GLB: LOD0 front (sprite-like, low elevation), three-quarter and side, and
every LOD from the three-quarter view, into review/<prop>/. Flipbook materials show their first frame emissive.
The glTF importer multiplies base colours by COLOR_0, as the engine does.
Usage: blender --background --python review.py -- <prop> <export.glb> <yaw_deg> [elevation_deg]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll  # noqa: E402

pl = ll.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, glb, yaw = args[0], args[1], int(args[2])
elevation = int(args[3]) if len(args) > 3 else 6
out = os.path.join(ll.REVIEW, prop); os.makedirs(out, exist_ok=True)
for old in os.listdir(out):
    if old.startswith(('lod0_y', 'level')):
        os.remove(os.path.join(out, old))
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
for m in bpy.data.materials:
    flip = m.get('openyamm_flipbook')
    if flip is not None and m.node_tree:
        nt = m.node_tree
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
pl.setup_render((512, 512))
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((yaw, elevation), (yaw + 40, 22), (yaw + 90, 8)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 40, 20),))
print('REVIEW', out, [o.name for o in objects])
