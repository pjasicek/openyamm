"""Step 1 of the m190 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P28): P26-P28 are three
slivers (1-4 tris) beside the left braid: removed. Kept: P00 torso/head/beard/hair/collar (one shell), P01/P02 boots,
P03 ragged green skirt, P04/P05 hands (L/R), P06 bare legs (down into the boots), P07 mail skirt, P08 helmet, P09/P10 braids, P11/P12 bracers, P13/P14
shoulder guards, P15/P16 bare upper arms + elbows, P17/P18 horns, P19/P20 shoulder-guard rims, P21/P22 braid ends,
P23 buckle, P24/P25 eyes. Joins the parts into 'Body' with a 'piece' point
attribute (part index) and 'orig_co' (rest positions, for the nearest-vertex weight transfer from Meshy's rigged copy).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in ('P26', 'P27', 'P28'):
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
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
