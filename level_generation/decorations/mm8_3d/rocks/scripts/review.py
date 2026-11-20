"""Review renders of an exported (unlinked) GLB: LOD0 front (sprite-like, low elevation), three-quarter and side, and
every LOD from the three-quarter view, into review/<rock>/. The glTF importer multiplies base colours by COLOR_0,
as the engine does. Usage: blender --background --python review.py -- <rock> <export.glb> [yaw_deg] [elevation_deg]"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rocks_lib as rl  # noqa: E402

pl = rl.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop, glb = args[0], args[1]
yaw = int(args[2]) if len(args) > 2 else 0
elevation = int(args[3]) if len(args) > 3 else 8
out = os.path.join(rl.REVIEW, prop); os.makedirs(out, exist_ok=True)
for old in os.listdir(out):
    if old.startswith(('lod0_y', 'level', 'toplit')):
        os.remove(os.path.join(out, old))
pl.reset()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
objects = sorted([o for o in bpy.data.objects if o not in before and o.type == 'MESH'], key=lambda o: o.name)
for m in bpy.data.materials:                     # cull back faces as the engine does (single-sided materials)
    m.use_backface_culling = m.name != 'Plant'
for m in bpy.data.materials:                     # alpha-tested materials clip in Eevee too
    if m.blend_method != 'OPAQUE':
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            pass
scene = pl.setup_render((512, 512))
# neutral light (brief: compare under neutral light): white sky instead of the props library's blue one
bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.62, 0.62, 0.62, 1.0)
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((yaw, elevation), (yaw + 40, 22), (yaw + 90, 8)))
# top-lit check (the engine lights the baked shading again): sun near the zenith, same front camera
sun = next(o for o in bpy.data.objects if o.type == 'LIGHT')
saved = sun.rotation_euler.copy()
sun.rotation_euler = (math.radians(12), 0, math.radians(-35))
pl.render_views([lod0], out, 'toplit', views=((yaw, elevation),))
sun.rotation_euler = saved
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 40, 20),))
print('REVIEW', out, [o.name for o in objects])
