"""Folded triangles on the chin and in the lower lip's cleft (user review 2026-11-02: "a dark smudge on the chin below
the lower lip" and specks at the chin). After clean_kira.py's mirror and face_tweak.py, four triangles per side at the
chin's lower rim (x 0.5-0.8 cm, z 0.683-0.685) are folded back over their neighbours (dihedrals 150-163 deg: two dark
and light specks under any light) and the lower lip's centre (z 0.705-0.714) keeps a cleft of 47-125 deg edges and
midline slivers (their UVs on the atlas corner: uv_slivers.py). B0: pockets (below); B: remaining inverted faces move
their vertices to their sound neighbours' mean; C: face-skin vertices below the lips (z < LIP_Z) and the cleft under the lower lip's centre (|x| < 1.2 cm, z 0.690-LIP_Z) (part 20) of the chin and lower-lip region
on an edge sharper than DIH deg, plus their one-ring, take a Laplacian (PASSES x 0.5, face-skin neighbours only);
midline vertices stay on the plane. Vertex moves and the deleted inverted faces only (UVs of every other face, weights and the paint unchanged). Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, math
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
DIH, PASSES, RIM_Z, LIP_Z = 45.0, 8, 0.695, 0.703     # LIP_Z: the lips keep their shape (smoothing them closed the mouth line)
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
lp = bm.faces.layers.int['part']
inreg = lambda c: c.y < -0.04 and 0.665 < c.z < 0.72 and abs(c.x) < 0.04
def sharp():
    bm.normal_update(); out = []
    for e in bm.edges:
        fs = e.link_faces
        if len(fs) == 2 and all(f[lp] == 20 for f in fs) and inreg((e.verts[0].co + e.verts[1].co) / 2):
            d = math.degrees(fs[0].normal.angle(fs[1].normal, 0.0))
            if d > DIH: out.append((e, d))
    return out
before = sharp(); worst0 = max((d for _, d in before), default=0)
# A. unwelded midline twins (clean_kira.py's mirror left coincident vertex pairs on x = 0; the slivers between them open
#    a slit that reads as a dark notch under the lower lip): weld face-skin vertices of the region closer than 0.1 mm
#    (loop UVs are per corner and stay; the slivers between the twins collapse and go)
nv0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if inreg(v.co) and any(f[lp] == 20 for f in v.link_faces)], dist=1e-4)
welded = nv0 - len(bm.verts)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# B0. pockets: faces facing into the head (normal against the skin's within 6 mm) around an apex shared by two of them
#     (Meshy's chin rim at x +/-6 mm: a doubled fan under a neighbour triangle). The inverted faces go (the triangle
#     over them covers their area) and the apex moves onto that triangle's plane so the rest of its fan meets it flush.
#     No UV of any remaining face changes.
def inverted():
    bm.normal_update()
    reg = [f for f in bm.faces if f[lp] == 20 and inreg(f.calc_center_median())]
    cen = {f: f.calc_center_median() for f in reg}
    out = []
    rim = [f for f in reg if cen[f].z < RIM_Z]       # the chin rim only: the lips' own crease faces down legitimately
    for f in rim:
        ref = sum((g.normal * g.calc_area() for g in reg if g is not f and (cen[g] - cen[f]).length < 0.006), f.normal * 0)
        if ref.length > 0 and f.normal.dot(ref.normalized()) < 0: out.append(f)
    return out
inv0 = inverted()
cnt = {}
for f in inv0:
    for v in f.verts: cnt[v] = cnt.get(v, 0) + 1
apex = [v for v, k in cnt.items() if k >= 2]
pockets = len(apex)
for v in apex:
    # the face that overlaps the fan: a region face not around the apex whose plane the apex sits behind/above
    cover = min((f for f in bm.faces if f[lp] == 20 and v not in f.verts and f not in inv0 and inreg(f.calc_center_median())
                 and (f.calc_center_median() - v.co).length < 0.006), key=lambda f: abs((v.co - f.verts[0].co).dot(f.normal)))
    v.co = v.co - cover.normal * (v.co - cover.verts[0].co).dot(cover.normal)
bmesh.ops.delete(bm, geom=inv0, context='FACES_ONLY')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# B. folded triangles: a face whose normal opposes the area-weighted normal of the face skin within 6 mm is inverted;
#    its vertices move to the mean of their neighbours that are not on an inverted face (10 rounds)
face_v = {v for f in bm.faces if f[lp] == 20 for v in f.verts}
unfold = 0
for _ in range(10):
    bm.normal_update()
    reg = [f for f in bm.faces if f[lp] == 20 and inreg(f.calc_center_median())]
    cen = {f: f.calc_center_median() for f in reg}
    bad = []
    for f in [f for f in reg if cen[f].z < RIM_Z]:
        ref = sum((g.normal * g.calc_area() for g in reg if g is not f and (cen[g] - cen[f]).length < 0.006), f.normal * 0)
        if ref.length > 0 and f.normal.dot(ref.normalized()) < 0: bad.append(f)
    if not bad: break
    bv = {v for f in bad for v in f.verts}
    for v in bv:
        anc = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) not in bv and e.other_vert(v) in face_v]
        if len(anc) >= 2:
            c = sum((a.co for a in anc), v.co * 0) / len(anc)
            if abs(v.co.x) < 1e-6: c.x = 0.0
            v.co = c; unfold += 1
mid = sharp()
sel = {v for e, _ in mid for v in e.verts if v.co.z < LIP_Z}
sel |= {e.other_vert(v) for v in list(sel) for e in v.link_edges if e.other_vert(v) in face_v and inreg(e.other_vert(v).co) and e.other_vert(v).co.z < LIP_Z}
# and the cleft under the lower lip's centre (the dimple whose fold drew the 'goatee' shadow)
sel |= {v for v in face_v if abs(v.co.x) < 0.012 and 0.690 < v.co.z < LIP_Z and v.co.y < -0.06}
moved = 0.0
for _ in range(PASSES):
    new = {}
    for v in sel:
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in face_v]
        if len(nb) < 3: continue
        c = sum((n.co for n in nb), v.co * 0) / len(nb)
        new[v] = v.co * 0.5 + c * 0.5
    for v, c in new.items():
        if abs(v.co.x) < 1e-6: c.x = 0.0
        moved = max(moved, (v.co - c).length); v.co = c
after = sharp()
for e, d in after: print('CHINFOLD_EDGE', round(d), [round(x, 4) for x in (e.verts[0].co + e.verts[1].co) / 2], round(e.calc_length() * 1000, 2), [round(f.calc_area() * 1e6, 2) for f in e.link_faces])
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CHINFOLD ' + json.dumps(dict(welded=welded, inverted_faces_deleted=len(inv0), pocket_apexes=pockets, unfold_moves=unfold, verts=len(sel), sharp_edges_before=len(before), worst_before=round(worst0), sharp_edges_after=len(after),
                                    worst_after=round(max((d for _, d in after), default=0)), max_step_mm=round(moved * 1000, 2))))
