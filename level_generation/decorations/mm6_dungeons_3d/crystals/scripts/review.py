"""Review renders of a prop's exported (unlinked) GLB: LOD0 front (sprite-like, low elevation), three-quarter and
side, and every LOD from the three-quarter view, under a grey ambient (0.35), a key light (0.55) and a small
torch-like point light beside the camera (dungeon light: gloss shows as highlights). The glTF importer multiplies base colours by COLOR_0 as the
engine does; flipbook materials show their first frame; emission is set from finish.py's FINISH table. Also a dim-dungeon view
(dim_y*.png). Prints the mean
colour of the LOD0 front render for comparison with the native sprite. Then sheet.py builds the sheet.
Usage: blender --background --python review.py -- <prop> <yaw_deg>"""
import math
import os
import sys

import bpy
import importlib.util

import mathutils
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
# This batch's finish.py by path (the project's scripts/ folder, also on sys.path, has its own finish.py).
_spec = importlib.util.spec_from_file_location(
    'crystals_finish', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finish.py'))
finish = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(finish)
prop, yaw = sys.argv[sys.argv.index('--') + 1:]
yaw = int(yaw)
out = os.path.join(cl.HERE, 'review', prop)
os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=os.path.join(cl.WORK, f'{prop}_export.glb'))
objects = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
spec = finish.FINISH[prop]['materials']
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    flip = m.get('openyamm_flipbook')
    if flip is not None:
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    if m.get('openyamm_specular') is not None:
        bsdf.inputs['Specular IOR Level'].default_value = 0.5 * float(m['openyamm_specular'])
    settings = spec.get(m.name, {})
    if settings.get('emissive'):
        bsdf.inputs['Emission Color'].default_value = tuple(settings['emissive']) + (1.0,)
        bsdf.inputs['Emission Strength'].default_value = 1.0
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.eevee.taa_render_samples = 32
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('World'); scene.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
# Dungeon-like light: a grey ambient, a soft key from above the camera side and a small torch-like point light that
# shows gloss as highlights (the engine's indoor decorations get ambient, key and point lights).
AMBIENT, KEY, TORCH = 0.35, 0.55, 60.0
bg.inputs['Color'].default_value = (AMBIENT, AMBIENT, AMBIENT, 1.0); bg.inputs['Strength'].default_value = 1.0
sun = bpy.data.lights.new('Key', 'SUN'); sun.energy = KEY; sun.angle = math.radians(8)
key = bpy.data.objects.new('Key', sun); scene.collection.objects.link(key)
key.rotation_euler = (math.radians(55), 0, math.radians(yaw - 25))
lamp = bpy.data.lights.new('Torch', 'POINT'); lamp.energy = TORCH; lamp.color = (1.0, 0.92, 0.8)
lamp.shadow_soft_size = 0.05
torch = bpy.data.objects.new('Torch', lamp); scene.collection.objects.link(torch)
lod0 = min(objects, key=lambda o: len(o.name))
lo, hi = pl.bounds([lod0])
size = (hi - lo).length
y = math.radians(yaw)
torch.location = (lo + hi) / 2 + mathutils.Vector((-math.sin(y + 0.6) * size, -math.cos(y + 0.6) * size, size * 0.6))
lamp.energy = TORCH * size * size
paths = pl.render_views([lod0], out, 'lod0', views=((yaw, 6), (yaw + 40, 22), (yaw + 90, 8)))
image = bpy.data.images.load(paths[0])
pixels = np.empty(len(image.pixels), np.float32); image.pixels.foreach_get(pixels)
pixels = pixels.reshape(-1, 4); opaque = pixels[pixels[:, 3] > 0.9][:, :3]
print('RENDER MEAN', prop, (opaque.mean(0) * 255).round(1))
# Dim dungeon light (ambient 0.08, key 0.15, the torch): the glow and the gloss must not turn the crystal grey.
bg.inputs['Color'].default_value = (0.08, 0.08, 0.08, 1.0)
sun.energy = 0.15
pl.render_views([lod0], out, 'dim', views=((yaw + 20, 12),))
bg.inputs['Color'].default_value = (AMBIENT, AMBIENT, AMBIENT, 1.0)
sun.energy = KEY
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 40, 20),))
print('REVIEW', out, [o.name for o in objects])
