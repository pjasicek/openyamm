"""Front panel off the legs (user review 1: patches near the hips): the leg shell (piece 2) pokes through the top of
the bodysuit's front panel (piece 11) at rest, so skin showed through the leather. The panel's vertices move OFFSET
outward along their normals (in place on <blend>; topology, UVs and weights unchanged). Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
OFFSET = float(os.environ.get('PANEL_OFFSET', '0.008'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Body'].data
if me.get('panel_offset'):
    print('PANEL already offset', me['panel_offset']); sys.exit(0)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.normal_update()
moved = 0
for v in bm.verts:
    if pv[v.index] == 11:
        n = v.normal.copy()
        if n.y > 0:                        # the panel faces forward (-Y); a sheet's normals may point inward
            n = -n
        v.co += n * OFFSET; moved += 1
bm.to_mesh(me); bm.free(); me['panel_offset'] = OFFSET
bpy.ops.wm.save_mainfile()
print('PANEL offset', OFFSET, 'm, vertices', moved)
