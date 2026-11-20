"""Render every mesh object of the open .blend from given yaws (studio light), for quick looks.
Usage: blender -b <file.blend> --python peek_render.py -- <out_prefix> <yaw> [<yaw> ...] [--elev E]"""
import math
import sys
import os
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
pl = dlib.pl
args = sys.argv[sys.argv.index('--') + 1:]
elev = 8
if '--elev' in args:
    i = args.index('--elev'); elev = float(args[i + 1]); args = args[:i] + args[i + 2:]
only = None
if '--only' in args:
    i = args.index('--only'); only = args[i + 1]; args = args[:i] + args[i + 2:]
prefix, yaws = args[0], [int(a) for a in args[1:]]
pl.setup_render((768, 768))
objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render and (only is None or o.name == only)]
os.makedirs(os.path.dirname(prefix), exist_ok=True)
pl.render_views(objs, os.path.dirname(prefix), os.path.basename(prefix), views=[(y, elev) for y in yaws])
