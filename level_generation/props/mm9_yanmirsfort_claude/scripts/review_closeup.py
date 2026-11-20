"""Blender: close-up review renders of the claw torch's orb and blue flame (side, front, three-quarter, above) and of
the hanging claw lamp's orb, with the isle's review setup (back faces culled) -> review/<prop>/closeup_*.png. Only the
vertices above `low` metres are kept for the framing (the torch's wall arm is cut away).
Usage: blender --background --python review_closeup.py"""
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts'))
import blib  # noqa: E402

blib.HERE, blib.WORK, blib.TEX = HERE, os.path.join(HERE, 'work'), os.path.join(HERE, 'textures')
SCRIPT = os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts', 'review.py')
ns = {'__file__': SCRIPT, '__name__': 'isle_review'}
source = open(SCRIPT).read()
exec(compile(source[:source.index('args = sys.argv')], SCRIPT, 'exec'), ns)

for prop, low, views in (('clawtorchr180', 0.55, (('side', 90, 0), ('front', 0, 4), ('threequarter', 35, 15),
                                                  ('above', 20, 55))),
                         ('clawlampp180', -1.0, (('side', 90, 0), ('below', 30, -35)))):
    blib.reset()
    blib.setup_render((500, 500))
    bpy.ops.import_scene.gltf(filepath=os.path.join(blib.WORK, f'mm9_deco_{prop}.glb'))
    ns['frame_fire']()
    base = [o for o in bpy.data.objects if o.type == 'MESH' and '_LOD' not in o.name]
    for o in base:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (o.matrix_world @ v.co).z < low], context='VERTS')
        bm.to_mesh(o.data)
        bm.free()
    out = os.path.join(HERE, 'review', prop)
    os.makedirs(out, exist_ok=True)
    for name, yaw, el in views:
        blib.render(base, os.path.join(out, f'closeup_{name}.png'), yaw, el)
    print('CLOSEUP', prop)
