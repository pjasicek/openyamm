"""Render scans (each set piece alone) from eight yaws at a low elevation for picking sources and yaws:
work/survey/<key>_y<yaw>.png. Usage: blender --background --python survey.py -- [key...]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rocks_lib as rl  # noqa: E402

pl = rl.pl
keys = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = os.path.join(rl.WORK, 'survey'); os.makedirs(out, exist_ok=True)
for key in keys or list(rl.SCANS):
    pl.reset()
    objs = rl.import_scan(key)
    for o in objs:
        o.parent = None
    pl.setup_render((200, 200))
    bpy.context.scene.eevee.taa_render_samples = 8
    pl.render_views(objs, out, key, views=[(y, 8) for y in range(0, 360, 45)])
    print('SURVEY', key)
