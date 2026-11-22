"""Step 1 cleanup of the Killer Sprite Smart Topology return (work/st_v1_parts.blend, loose parts P00..; examine_parts.py).
Parts: P00 head + torso + dress (with the ragged hem) + arms + hands (one shell), P01 hair, P02 legs, P03/P04 eye balls,
P05/P06 two stray strands across the forehead, P07/P08/P11/P14/P15 loose wisps floating beside the body, P09/P10/P16-P24
small loose locks on the back of the hair, P12/P13 lash strips (micro triangles; the paint carries the lashes).
Kept: P00, P01, P02, P03, P04. Joins them into 'Body' with a 'piece' point attribute (part index) and 'orig_co'.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import os as _os; _os.chdir(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))  # project-relative paths
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
KEEP = {'P00', 'P01', 'P02', 'P03', 'P04'}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
DROP = sorted(set(P) - KEEP)
for n in DROP:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
print('DROPPED', len(DROP), DROP)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
for o in bpy.data.objects:
    o.select_set(o.name in P)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
body.data.materials.clear()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons))
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
