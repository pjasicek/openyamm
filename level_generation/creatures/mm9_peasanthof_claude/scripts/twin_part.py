"""Back-side twin of one single-sided loose part (HOF2's kerchief: from the front its inside at the sides of the face was
culled and showed the background). The loose part whose bounding box is widest in x among parts with at least MINV
vertices whose median height is above ZMIN (MM9 frame) is duplicated OFFSET behind itself along the area-weighted vertex
normal, flipped, with its own UVs (every layer), face attributes and weights; the open rim is joined to its twin by a rim
strip. Faces only added. Args: <in blend> <out blend> [zmin 0.6] [offset 0.0015] [minv 300] [ratio 1.0: collapse-decimate the twin layer]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
ZMIN = float(a[2]) if len(a) > 2 else 0.6
OFF = float(a[3]) if len(a) > 3 else 0.0015
MINV = int(a[4]) if len(a) > 4 else 300
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; mw = ob.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), int); parts = []
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = len(parts); cur = []
    while st:
        x = st.pop(); cur.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = len(parts); st.append(o)
    parts.append(cur)
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
best = None
for k, p in enumerate(parts):
    if len(p) < MINV or np.median(CO[p, 2]) < ZMIN: continue
    w = CO[p, 0].max() - CO[p, 0].min()
    if best is None or w > best[0]: best = (w, k)
k = best[1]; vset = set(parts[k])
faces = [f for f in bm.faces if f.verts[0].index in vset]
print('TWIN part', len(parts[k]), 'verts', len(faces), 'faces, width', round(best[0], 3))
bm.normal_update()
dl = bm.verts.layers.deform.verify()
uvl = list(bm.loops.layers.uv.values())
ints = list(bm.faces.layers.int.values())
vmap = {}
orig = {i: bm.verts[i] for i in vset}
for i in vset:
    v = orig[i]
    n = v.normal
    nv = bm.verts.new(v.co - n * OFF)
    for g, w in v[dl].items(): nv[dl][g] = w
    vmap[i] = nv
new = []
for f in faces:
    nf = bm.faces.new([vmap[v.index] for v in reversed(f.verts)])
    nf.material_index = f.material_index; nf.smooth = f.smooth
    for L in ints: nf[L] = f[L]
    src = list(reversed(f.loops))
    for lp, sp in zip(nf.loops, src):
        for U in uvl: lp[U].uv = sp[U].uv
    new.append(nf)
# rim strip: each boundary edge of the part joined to its twin edge, facing out of the cloth
rim = 0
for f in faces:
    for lp in f.loops:
        e = lp.edge
        if not e.is_boundary: continue
        v0, v1 = lp.vert, lp.link_loop_next.vert
        try:
            nf = bm.faces.new([v1, v0, vmap[v0.index], vmap[v1.index]])
        except ValueError:
            continue
        nf.material_index = f.material_index; nf.smooth = True
        for L in ints: nf[L] = f[L]
        uvs = {lp.vert.index: [lp[U].uv.copy() for U in uvl], lp.link_loop_next.vert.index: [lp.link_loop_next[U].uv.copy() for U in uvl]}
        for q in nf.loops:
            key = q.vert.index if q.vert.index in uvs else next(i for i, nv in vmap.items() if nv is q.vert)
            for U, uv in zip(uvl, uvs[key]): q[U].uv = uv
        rim += 1
twin_ids = [v for v in vmap.values()]
bm.verts.index_update()
tid = [v.index for v in twin_ids]
bm.to_mesh(me); me.update()
RATIO = float(a[5]) if len(a) > 5 else 1.0
if RATIO < 1.0:          # the inner layer only, collapse-decimated (LOD0 budget); weights and UVs interpolate
    vg = ob.vertex_groups.new(name='_twin')
    vg.add(tid, 1.0, 'REPLACE')
    mod = ob.modifiers.new('dec', 'DECIMATE'); mod.ratio = RATIO; mod.vertex_group = '_twin'; mod.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = ob
    arm_mods = [m for m in ob.modifiers if m.type == 'ARMATURE']
    for m in arm_mods: m.show_viewport = False
    bpy.ops.object.modifier_apply(modifier='dec')
    for m in arm_mods: m.show_viewport = True
    ob.vertex_groups.remove(ob.vertex_groups['_twin'])
print('TWIN_PART faces', len(new), 'rim', rim, 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
