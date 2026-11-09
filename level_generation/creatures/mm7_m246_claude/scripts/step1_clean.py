"""Step 1 cleanup of the m246 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P97): nothing removed.
P00 skin body (head, torso, arms, trousers, boots), P01 crest, P02 hair, P03 vest, P04/P05 hands (right -x / left +x,
separate fingers), P06 helmet, P07/P08 forearm bracers (left/right), P09 belt, P10 pauldron (left), P11 left upper-arm
plate, P12/P13 eyes, P14 strap, P15/P16/P18/P19/P24-P29 hip panels, P17/P21 shin guards, P20/P23 cheek pieces,
P22 goatee, P30-P32 crest base, the rest spikes and studs (<= 40 triangles). Joins the parts into 'Body' with 'piece' and 'orig_co' point attributes.
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
