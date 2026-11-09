"""A disc across the inside of each forearm tube just behind the cuff (HOF2 see-through after the stub trims: the view into
the cuff met the culled inside of the sleeve). Per side, rest pose: at S (m along forearm -> hand from the hand joint,
negative = up the forearm) a ring of N points at K x the forearm surface's radius there (ray from the axis to the body
faces of that arm), fanned to the axis, facing the hand. Weights: each ring point takes the weights of the nearest
forearm vertex, the centre their mean; UVs (every layer) the UVs of the hit surface point (the sleeve's own paint).
Faces only added. Args: <in blend> <out blend> [s -0.022] [k 0.92] [n 16]"""
import bpy, bmesh, sys, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
a = sys.argv[sys.argv.index('--') + 1:]
S = float(a[2]) if len(a) > 2 else -0.022; K = float(a[3]) if len(a) > 3 else 0.92; N = int(a[4]) if len(a) > 4 else 16
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
uvl = list(bm.loops.layers.uv.values()); dl = bm.verts.layers.deform.verify()
names = {g.index: g.name for g in ob.vertex_groups}
rep = {}
for tok in ('L', 'R'):
    gid = {g.index for g in ob.vertex_groups if g.name in (f'Bip01 {tok} Forearm', f'Bip01 {tok} Hand', f'Bip01 {tok} UpperArm')}
    faces = [f for f in bm.faces if f[lh] == 0 and f[lk] == 0 and
             np.mean([sum(w for g, w in v[dl].items() if g in gid) for v in f.verts]) > 0.5]
    tris = []; tf = []
    for f in faces:
        vs = f.verts
        for i in range(1, len(vs) - 1):
            tris.append([mw @ vs[0].co, mw @ vs[i].co, mw @ vs[i + 1].co]); tf.append((f, 0, i, i + 1))
    sub = bmesh.new()
    for t in tris:
        vv = [sub.verts.new(p) for p in t]; sub.faces.new(vv)
    sub.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(sub)
    a0 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local
    a1 = rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local
    ax = (a1 - a0).normalized(); C = a1 + ax * S
    # the forearm mesh centre at S (the fitted joint axis runs up to 3 cm off it)
    band = [mw @ v.co for f in faces for v in f.verts if abs(((mw @ v.co) - a1).dot(ax) - S) < 0.008 and ((mw @ v.co) - C).length < 0.09]
    if band:
        bb = np.array([tuple(p) for p in band]); C = Vector((0.5 * (bb.min(0) + bb.max(0))).tolist())
    u = ax.orthogonal().normalized(); w_ = ax.cross(u)
    ring = []; uvs = []
    for k in range(N):
        t = 2 * math.pi * k / N; d = u * math.cos(t) + w_ * math.sin(t)
        o_ = C.copy(); hit = (None,)
        for _ in range(6):                       # skip anything nearer than RMIN to the axis (the stub's remains)
            hit = bvh.ray_cast(o_, d, 0.12)
            if hit[0] is None or (hit[0] - C).length > 0.015: break
            o_ = hit[0] + d * 1e-4
        if hit[0] is None or (hit[0] - C).length > 0.08: continue
        f, i0, i1, i2 = tf[hit[2]]
        lp = f.loops
        tri_v = [mw @ lp[j].vert.co for j in (i0, i1, i2)]
        uvk = []
        for U in uvl:
            tu = [Vector((lp[j][U].uv.x, lp[j][U].uv.y, 0)) for j in (i0, i1, i2)]
            q = barycentric_transform(hit[0], *tri_v, *tu); uvk.append((q.x, q.y))
        ring.append(C + (hit[0] - C) * K); uvs.append(uvk)
    if len(ring) < 8:
        hit0 = bvh.ray_cast(C, u, 0.2)
        rep[tok] = {'too few hits': len(ring), 'faces': len(faces), 'C': [round(x, 3) for x in C], 'probe': None if hit0[0] is None else round((hit0[0] - C).length, 3)}; continue
    fv = [v for f in faces for v in f.verts]
    def nearest(p): return min(fv, key=lambda v: ((mw @ v.co) - p).length)
    nr = [bm.verts.new(mwi @ p) for p in ring]; cen = bm.verts.new(mwi @ C)
    acc = {}
    for v, p in zip(nr, ring):
        for g, wt in nearest(p)[dl].items():
            v[dl][g] = wt; acc[g] = acc.get(g, 0) + wt / len(nr)
    for g, wt in acc.items(): cen[dl][g] = wt
    made = 0
    for k in range(len(nr)):
        j = (k + 1) % len(nr)
        f = bm.faces.new([cen, nr[k], nr[j]]); f[lh] = 0; f[lk] = 0; f.smooth = True
        f.material_index = faces[0].material_index
        for lp in f.loops:
            src = uvs[k] if lp.vert is nr[k] or lp.vert is cen else uvs[j]
            for U, uv in zip(uvl, src): lp[U].uv = uv
        f.normal_update()
        if f.normal.dot(ax) < 0: f.normal_flip()
        made += 1
    rep[tok] = {'ring': len(nr), 'faces': made, 'radius_mm': round(float(np.mean([(p - C).length for p in ring])) * 1000, 1)}
bm.to_mesh(ob.data); ob.data.update()
print('CUFF_DISC', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
