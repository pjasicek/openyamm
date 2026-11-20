"""Step 1 cleanup of the natm Smart Topology return (work/st_v1_parts.blend, loose parts P00..P438):
- the back loincloth panel (P10) hangs 6 cm to the right of the spine (native: centred): move it to x = 0 at its top;
- everything else is kept (feather cards, arm rings, beads, eye shells).
Joins the parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (positions before edits, for
the nearest-vertex weight transfer from Meshy's rigged copy). Args: -- <in blend> <out blend>"""
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
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
back = pv == 10
top = co[back][:, 2] > co[back][:, 2].max() - 0.03
dx = -float(co[back][top][:, 0].mean())
co[back, 0] += dx
me.vertices.foreach_set('co', co.ravel()); me.update()
# positions as uploaded to Meshy's auto-rig (after the edit), for the nearest-vertex weight transfer
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN back panel moved dx cm', round(dx * 100, 2), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
