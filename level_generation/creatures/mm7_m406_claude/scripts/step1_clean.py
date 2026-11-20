"""Step 1 cleanup of the m406 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P15): nothing removed.
P00 legs with plate, knee cops and sabatons, P01 torso and tabard (one shell), P02 head, P03 spiked helmet, P04/P05
hands (left/right, separate fingers), P06/P07 arms with vambraces, P08 mail coif, P09/P10 eyes, P11 belt buckle,
P12-P15 knee-cop studs. Joins the parts into 'Body' with 'piece' and 'orig_co' point attributes.
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
