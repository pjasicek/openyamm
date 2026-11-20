"""Step 1 of the m322 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P49, 1.75 m): P49 (a 1-tri sliver)
removed. P00 skin shell (body, head, the vest, trousers, bracers and boots all in one), P01 hair, P02/P03 hands (R -x /
L +x), P04/P05 eyes, P08/P09/P11 mouth bits, P06/P07/P10/P12 vest lacing, the rest small studs and trouser-lacing
grommets. Joins the parts into 'Body' with 'piece' and 'orig_co'. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
bpy.data.objects.remove(P.pop('P49'), do_unlink=True)
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
