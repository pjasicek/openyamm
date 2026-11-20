"""Step 1 of the m302 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P18, 1.35 m): removed P10 (a ball
on the cap brim) and P11-P18 (eight 31-44-tri belt rivets; the retexture paints them). Kept: P00 skin shell (torso,
arms, hands, neck, face), P01 vest (with its fleece trim), P02 beard, P03 trousers (belt included), P04 cap,
P05 hair (nape), P06 left boot (+x), P07 right boot, P08/P09 eyes. Joins the parts into 'Body' with a 'piece' point
attribute (part index) and 'orig_co' (rest positions, for the nearest-vertex weight transfer from Meshy's rigged copy).
Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
for n in ['P10'] + [f'P{i}' for i in range(11, 19)]:
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
