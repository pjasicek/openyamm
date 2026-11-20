"""Shade a prepared mesh smooth, save its .blend and re-export the retexture upload.
Usage: blender --background ../work/<name>_uv.blend --python smooth_export.py -- <name>"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

name = sys.argv[sys.argv.index('--') + 1]
obj = bpy.data.objects[name]
for p in obj.data.polygons:
    p.use_smooth = True
bpy.ops.wm.save_mainfile()
blib.export_neutral(obj, os.path.join(blib.HERE, 'texturing', f'{name}_upload.glb'))
print('SMOOTH', name, len(obj.data.polygons))
