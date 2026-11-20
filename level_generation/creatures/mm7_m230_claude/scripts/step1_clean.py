"""Step 1 cleanup of the m230 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P37): the plate armour
comes back as separate segments (no skin under it): P00 thigh plates, P01 great helm, P02/P05 cuirass and tabard top,
P03/P04 gauntlets (left/right, separate fingers), P06/P07 greaves, P08 eagle crest, P09/P22/P24 pauldrons and upper
arms, P10 belt, P11/P12 sabatons, P13/P21 tabard skirts (back/front), P15/P16 knee cops, P17-P20/P32/P33 vambraces and
couters, P14/P23/P25/P26/P29-P31/P34-P36 plume strands, P27 gorget, P28 buckle. P37 (one degenerate triangle) removed.
P22 (left upper arm) carries a thin strand down to the belt: its vertices outside the mirrored extent of P24 (right
upper arm, +5 mm) are cut and loose fragments under 30 faces dropped (bar1's boot-strand rule).
Joins the parts into 'Body' with 'piece' and 'orig_co' point attributes. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
bpy.data.objects.remove(P.pop('P37'), do_unlink=True)
import bmesh
r = np.array([tuple(v.co) for v in P['P24'].data.vertices]); lo, hi = r.min(0), r.max(0)
mlo, mhi = np.array([-hi[0], lo[1], lo[2]]) - 0.005, np.array([-lo[0], hi[1], hi[2]]) + 0.005
bm = bmesh.new(); bm.from_mesh(P['P22'].data)
cut = [v for v in bm.verts if np.any(np.array(v.co) < mlo) or np.any(np.array(v.co) > mhi)]
bmesh.ops.delete(bm, geom=cut, context='VERTS')
seen, small = set(), []
for f in bm.faces:
    if f in seen:
        continue
    comp, st = [], [f]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); comp.append(x); st.extend(g for e in x.edges for g in e.link_faces)
    if len(comp) < 30:
        small += comp
bmesh.ops.delete(bm, geom=small, context='FACES')
print('CLEAN P22 strand: cut verts', len(cut), 'fragment faces removed', len(small))
bm.to_mesh(P['P22'].data); bm.free()
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
