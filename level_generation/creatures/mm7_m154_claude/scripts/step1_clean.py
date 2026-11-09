"""Step 1 cleanup of the m154 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P24): nothing removed.
P00 tunic with gorget, pauldrons and upper sleeves, P01 legs and boots, P02 head, P03/P04 hands (left/right, separate
fingers), P05/P16 fur quiver, P06 helmet, P07 mail coif, P08/P09 mail forearms, P10 diagonal strap, P11/P12 eyes,
P13/P14 horns, P15 belt buckle, P17 helmet spike, P18-P24 arrows in the quiver. Joins the parts into 'Body' with 'piece' and 'orig_co' point attributes.
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
print('CLEAN parts', len(P), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
