"""Apply the 2026-10-20 hood review fixes to the textured master in place (its topology and Meshy UVs stay): delete the
hidden nape fins (pieces in DROP of step1_clean.py) and flag the shreds that step1_clean.py now reclassifies as cloth
(RECLASS). robe_rig.py is then re-run on the result for the new hood weights. Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
DROP = {190, 202}
RECLASS = {193, 194, 196, 197, 207, 210}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
gone = [bm.verts[i] for i in np.where(np.isin(pv, list(DROP)))[0]]
nt = sum(len(f.verts) - 2 for f in {f for v in gone for f in v.link_faces})
bmesh.ops.delete(bm, geom=gone, context='VERTS'); bm.to_mesh(me); bm.free(); me.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
cl = np.zeros(len(me.vertices), np.int32); me.attributes['cloth'].data.foreach_get('value', cl)
cl[np.isin(pv, list(RECLASS))] = 1
me.attributes['cloth'].data.foreach_set('value', cl.tolist())
print('HOODFIX deleted pieces', sorted(DROP), nt, 'triangles; reclassified as cloth', sorted(RECLASS), int(np.isin(pv, list(RECLASS)).sum()), 'vertices;',
      'triangles now', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
