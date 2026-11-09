"""Squash the prepared skull pile across (x, y) so its front silhouette matches the native sprite's width profile
(Meshy returned it 1.8 times as wide as tall; the sprite is 1.4): work/skullpile_uv.blend in place, then re-export the
retexture upload. Usage: blender --background ../work/skullpile_uv.blend --python squash_pile.py"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

SQUASH = 0.78
obj = bpy.data.objects['skullpile']
if not obj.get('squashed'):
    for v in obj.data.vertices:
        v.co.x *= SQUASH; v.co.y *= SQUASH
    obj['squashed'] = SQUASH
for p in obj.data.polygons:
    p.use_smooth = True
bpy.ops.wm.save_mainfile()
blib.export_neutral(obj, os.path.join(blib.HERE, 'texturing', 'skullpile_upload.glb'))
print('SQUASHED', [round(d, 3) for d in obj.dimensions])
