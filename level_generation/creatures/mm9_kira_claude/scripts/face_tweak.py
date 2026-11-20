"""Chin cleft and slivers on the face (viewer close-up r1-r4: a dark stroke under the lower lip and on the chin, dark nose tip): the
mirror bisect in clean_kira.py left vertices 1.6-3.9 mm off the midline 1-2 mm behind it, so thin triangles fold along the
midline and shade dark. Meshy's lower lip hangs into a cleft whose shadow drew the stroke, and two slivers speck the chin. Face-skin vertices (part 20) of the
chin between the lip (z 0.703, kept) and the jaw rim (z 0.674, kept), within 2.2 cm of the midline, take a Laplacian (6 passes, 0.5;
a y-only pass over the midline up to the brow notched the lips), midline vertices stay on the plane. Vertex moves only (UVs, weights and the paint
unchanged). Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
face_v = set()
for f in bm.faces:
    if fp[f.index] == 20: face_v.update(v.index for v in f.verts)
sel = [v for v in bm.verts if v.index in face_v and abs(v.co.x) < 0.022 and 0.674 < v.co.z < 0.703 and v.co.y < -0.05]
moved = 0.0
for _ in range(6):
    new = {}
    for v in sel:
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v).index in face_v]
        if len(nb) < 3: continue
        c = sum((n.co for n in nb), v.co * 0) / len(nb)
        new[v] = v.co * 0.5 + c * 0.5
    for v, c in new.items():
        if abs(v.co.x) < 1e-6: c.x = 0.0
        moved = max(moved, (v.co - c).length); v.co = c
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FACETWEAK', len(sel), 'max move mm', round(moved * 1000, 2))
