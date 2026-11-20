"""Render every candidate Poly Haven scan (outdoor rock sources, read only) from eight yaws at a low elevation, for
picking each sprite's source and yaw. Writes work/rocks/survey/<scan>_<yaw>.png.
Usage: blender --background --python rock_survey.py"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll  # noqa: E402
import rock_common as rc  # noqa: E402

pl = ll.pl
out = os.path.join(ll.WORK, 'rocks', 'survey')
for scan, path in rc.SCANS.items():
    pl.reset()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    pl.setup_render((256, 256))
    for yaw in range(0, 360, 45):
        pl.render_views(objs, out, scan, views=((yaw, 8),))
    print('SURVEY', scan)
