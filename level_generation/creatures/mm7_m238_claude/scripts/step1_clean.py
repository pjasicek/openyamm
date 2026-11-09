"""Step 1 cleanup of the m238 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P09, normalised to 1.80 m
from the vortex tip to the ponytail top, facing -Y): nothing removed. P00 body (torso, arms, head, ponytail; the hips
continue as a core cone inside the vortex down to the tip), P01 the spiral vortex shell, P02 circlet, P03/P04 earrings,
P05/P06 eyes, P07/P09 forehead jewel, P08 lips/teeth sliver. Joins the parts into 'Body' with 'piece' and 'orig_co'
point attributes. Args: -- <in blend> <out blend>"""
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
