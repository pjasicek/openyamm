"""Review renders of a prop's exported (unlinked) GLB: LOD0 from the front at the sprite's elevation, three-quarter
and side/back, and every LOD from one view. Flipbook materials show their first frame, emissive like the engine's
unlit fire; unlit materials glow; the glTF importer multiplies base colours by COLOR_0, as the engine does.
Usage: blender --background --python review.py -- <prop> <export.glb> <yaw_deg> [elevation_deg]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, glb, yaw = args[0], args[1], int(args[2])
elevation = int(args[3]) if len(args) > 3 else 8
out = os.path.join(ml.HERE, 'review', prop); os.makedirs(out, exist_ok=True)
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
for m in bpy.data.materials:
    m.use_backface_culling = True            # as the engine draws single-sided materials
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    flip = m.get('openyamm_flipbook')
    if flip is not None and bsdf is not None:
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    if bsdf is None:          # KHR_materials_unlit imports as an emission/background mix: leave it
        continue
    if flip is not None or m.name in ('Glow', 'Brew', 'Embers'):
        base = bsdf.inputs['Base Color'].links
        if base:
            nt.links.new(base[0].from_socket, bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 1.0
pl.setup_render((512, 512))
bpy.context.scene.eevee.taa_render_samples = int(os.environ.get('REVIEW_SAMPLES', '8'))   # the GPU is shared
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((yaw, elevation), (yaw + 40, 24), (yaw + 90, 10), (yaw + 180, 14)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 30, 20),))
print('REVIEW', out, [o.name for o in objects])
