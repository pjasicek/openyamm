"""Review renders of a model's exported (unlinked) GLB: LOD0 front (low elevation, as the sprite is drawn),
three-quarter and side, and every LOD from the three-quarter view. The glTF importer multiplies base colours by
COLOR_0, as the engine does. sheet.py then puts them beside the native sprite.
Usage: blender --background --python review.py -- <prop> <export.glb>"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import containers_lib as cl  # noqa: E402

pl = cl.pl
prop, glb = sys.argv[sys.argv.index('--') + 1:][:2]
out = os.path.join(cl.HERE, 'review', prop)
os.makedirs(out, exist_ok=True)
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
scene = pl.setup_render((512, 512))
# Neutral light (grey ambient, white key) so the render's mean colour compares with the sprite's.
background = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
background.inputs['Color'].default_value = (0.6, 0.6, 0.6, 1.0)
for m in bpy.data.materials:                # the engine's specular scale (openyamm_specular) in the preview
    if m.get('openyamm_specular') is not None and m.node_tree:
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Specular IOR Level'].default_value = 0.5 * float(m['openyamm_specular'])
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((0, 10), (40, 24), (90, 10)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((40, 20),))
print('REVIEW', out, [o.name for o in objects])
