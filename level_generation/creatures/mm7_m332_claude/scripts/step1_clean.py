"""Step 1 of the m332 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P31, 1.75 m): nothing removed.
P00 skin shell (body, head with the painted hair, shoes, bracers), P01 vest, P02/P03 hands (L +x / R), P04 ponytail,
P05 belt, P15 buckle, P06/P07/P08/P23/P25/P31 dagger and sheath fittings (his right hip), P09 right upper-arm band,
P10-P14/P16/P17/P19 vest studs, P18/P20-P22/P24/P26/P27/P30 lacing crosses, P28/P29 eyes. Joins the parts into 'Body'
with a 'piece' point attribute (part index) and 'orig_co'. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(P), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co),
      'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
