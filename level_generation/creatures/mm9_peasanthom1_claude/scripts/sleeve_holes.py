"""Fill Meshy's holes in the sleeves (follow-up 2026-11-02: the "two dark triangles" on a sleeve were see-through holes;
four boundary loops of 4, 5, 18 and 19 edges on the forearms, 15 cm before the cuffs, present since the Smart Topology
mesh). Boundary loops of at most MAXE edges whose centre lies on an arm (|x| 0.45-0.8, z 0.25-0.6, i.e. not the cuffs,
eyes, mouth, neck or legs) are filled and triangulated; every new loop takes the UV (UVMap and HeadUV) its vertex has in
a rim face, so the patch continues the cloth's own paint (the rims lie inside one UV island each: checked, spread
printed); attributes from the largest rim face. Args (Blender): <in blend> <out blend> [max edges 24]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
MAXE = int(a[2]) if len(a) > 2 else 24
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
uvs = [bm.loops.layers.uv[n] for n in ('UVMap', 'HeadUV') if n in bm.loops.layers.uv]
ilayers = [bm.faces.layers.int[n] for n in ('head', 'hand') if n in bm.faces.layers.int]
seen = set(); loops = []
for e in bm.edges:
    if not e.is_boundary or e.index in seen:
        continue
    lp = [e]; seen.add(e.index); st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); lp.append(y); st.append(y)
    loops.append(lp)
rep = []
for lp in loops:
    c = np.mean([tuple(mw @ v.co) for x in lp for v in x.verts], 0)
    if len(lp) > MAXE or not (0.45 < abs(c[0]) < 0.8 and 0.25 < c[2] < 0.6):
        continue
    hl = bm.faces.layers.int['hand']
    rim_all = {x.link_faces[0] for x in lp}
    rim_faces = {f for f in rim_all if f[hl] == 0} or rim_all   # body cloth only: a hole beside the hand stub took
    # the stub's hand material and flat head-set UVs in the first try (head-set fragments 3.1 -> 5.0 %)
    vuv = {}
    for f in rim_faces:
        for l in f.loops:
            vuv.setdefault(l.vert, [tuple(l[u].uv) for u in uvs])
    spread = float(np.ptp(np.array([vuv[v][0] for x in lp for v in x.verts]), 0).max())
    ref = max(rim_faces, key=lambda f: f.calc_area())
    new = bmesh.ops.holes_fill(bm, edges=lp, sides=0)['faces']
    if not new:                                   # holes_fill refuses some loops: triangle_fill instead
        new = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=lp)['geom']
        new = [g for g in new if isinstance(g, bmesh.types.BMFace)]
    new = bmesh.ops.triangulate(bm, faces=new, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
    rc = {f: np.array(tuple(f.calc_center_median())) for f in rim_faces}
    for f in new:
        for il in ilayers:
            f[il] = 0                             # cloth patch: body material
        f.smooth = ref.smooth
        if all(l.vert in vuv for l in f.loops) and np.ptp(np.array([vuv[l.vert][0] for l in f.loops]), 0).max() <= 0.05:            # the face's corners lie in one UV island: continue the paint
            for l in f.loops:
                for k, u in enumerate(uvs):
                    l[u].uv = vuv[l.vert][k]
        else:                                     # across a seam: the nearest rim face's mean texel (flat patch)
            c0 = np.array(tuple(f.calc_center_median()))
            near = min(rim_faces, key=lambda g: np.linalg.norm(rc[g] - c0))
            for k, u in enumerate(uvs):
                m = tuple(np.mean([tuple(l[u].uv) for l in near.loops], 0))
                for l in f.loops:
                    l[u].uv = m
    rep.append({'edges': len(lp), 'centre': c.round(3).tolist(), 'faces': len(new), 'uv_spread': round(spread, 4)})
bm.normal_update()
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('SLEEVE_HOLES', json.dumps(rep))
