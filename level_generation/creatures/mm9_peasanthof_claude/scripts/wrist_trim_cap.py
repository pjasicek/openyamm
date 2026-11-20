"""HOF2 wrists (coordinator review 2026-11-02: right-hand flap over the cuff in Running/Death, left cuff ring see-through).
Per side, rest pose, axis forearm joint -> hand joint, s along it from the hand joint, r from the axis:
1. Trim: hand-graft faces (attribute hand) whose vertices all lie before the joint (s < S_TRIM) and whose centre is further
   than K_TRIM x the cuff ring's median radius from the axis are deleted (the toothed stub shards that rose over the cuff
   when the wrist bent). The stub keeps its inner part.
2. Cap: each open boundary loop of body faces (no head/hand) whose centre lies within -0.08..0.0 of the hand joint and within
   0.08 m of the axis (the cuff_trim ring) gets an annulus: a second ring at CAP x the loop's radius about the axis,
   joined to the loop, facing out of the sleeve (toward the hand); its UVs (both layers) are the loop's own (the ring
   collapses onto the cuff paint), its weights the loop vertices'. The view into the sleeve end meets the annulus, the stub
   passes through its hole.
Faces deleted/added only; existing UVs and weights unchanged. Args: <in blend> <out blend> [s_trim -0.004] [k_trim 0.85] [cap 0.45]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
S_TRIM = float(a[2]) if len(a) > 2 else -0.004
K_TRIM = float(a[3]) if len(a) > 3 else 0.85
CAP = float(a[4]) if len(a) > 4 else 0.45
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = ob.data; mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
uvl = list(bm.loops.layers.uv.values()); dl = bm.verts.layers.deform.verify()
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    def sr(p):
        rel = np.array(p) - a1; s = rel @ ax; return s, np.linalg.norm(rel - s * ax)
    # cuff ring radius: body vertices 1-4 cm before the joint
    rr = [sr(mw @ v.co)[1] for v in bm.verts if v.link_faces and all(f[lh] == 0 and f[lk] == 0 for f in v.link_faces)
          and -0.045 < sr(mw @ v.co)[0] < -0.01 and sr(mw @ v.co)[1] < 0.055]
    ring_r = float(np.median(rr)) if rr else 0.03
    dead = []
    for f in bm.faces:
        if f[lh] == 0: continue
        ss = [sr(mw @ v.co) for v in f.verts]
        if min(s for s, _ in ss) < -0.12 or max(r for _, r in ss) > 0.12: continue      # the other hand
        if all(s < S_TRIM for s, _ in ss) and np.mean([r for _, r in ss]) > K_TRIM * ring_r:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES_ONLY')
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    # cuff ring loops
    caps = 0
    bedges = [e for e in bm.edges if e.is_boundary and e.link_faces and e.link_faces[0][lh] == 0 and e.link_faces[0][lk] == 0]
    seen = set()
    for e0 in bedges:
        if e0 in seen: continue
        loop = [e0]; seen.add(e0); v = e0.verts[1]; start = e0.verts[0]
        while v is not start:
            nxt = [e for e in v.link_edges if e.is_boundary and e not in seen and e in set(bedges)]
            if not nxt: break
            e = nxt[0]; seen.add(e); loop.append(e); v = e.other_vert(v)
        vs = [loop[0].verts[0]] + [None] * 0
        order = [start]; cur = start
        for e in loop:
            cur = e.other_vert(cur); order.append(cur)
        order = order[:-1]
        P = [np.array(mw @ q.co) for q in order]
        c = np.mean(P, 0); s_c, r_c = sr(c)
        if not (-0.08 < s_c < 0.0 and r_c < 0.03 and len(order) >= 6): continue
        foot = a1 + s_c * ax
        inner = []
        for q, p in zip(order, P):
            d = p - (a1 + ((p - a1) @ ax) * ax)
            ni = bm.verts.new(mwi @ Vector((a1 + ((p - a1) @ ax) * ax + d * CAP).tolist()))
            for g, w in q[dl].items(): ni[dl][g] = w
            inner.append(ni)
        src_face = order[0].link_faces[0]
        for i in range(len(order)):
            j = (i + 1) % len(order)
            try:
                f = bm.faces.new([order[i], order[j], inner[j], inner[i]])
            except ValueError:
                continue
            f.material_index = src_face.material_index; f.smooth = True
            f[lh] = 0; f[lk] = 0
            for lp in f.loops:
                q = lp.vert if lp.vert in order else order[inner.index(lp.vert)]
                ref = next(l for l in q.link_loops if l.face is not f)
                for U in uvl: lp[U].uv = ref[U].uv
            f.normal_update()
            if f.normal.dot(Vector(ax.tolist())) < 0:
                f.normal_flip()
            caps += 1
    rep[tok] = {'ring_r_mm': round(ring_r * 1000, 1), 'trimmed_faces': len(dead), 'cap_faces': caps}
bm.to_mesh(me); me.update()
print('WRIST_TRIM_CAP', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
