"""Step 1 of the m414 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P12): no geometry edits needed.
P00 torso with neck and face, P01 both legs with greaves and sandals, P02/P03 right/left arm with vambrace and hand,
P04/P08/P09 the three skirt tiers (bottom, middle, top), P05 crest, P06 helmet dome, P07 cheek and neck guard, P10 belt,
P11/P12 eyes. Joins the parts into 'Body' with a 'piece' point
attribute (part index) and 'orig_co' (rest positions, for the nearest-vertex weight transfer from Meshy's rigged copy).
Args: -- <in blend> <out blend>"""
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
