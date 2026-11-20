"""Fre pass 4: PeasantF2's braid has ~2,400 triangles; the Fre LOD0 budget (15k) needs about half. Blender collapse-decimate of the braid
faces only (the cap untouched), UVs kept (delimit on seams), then rows split by UV again; weights for new rows from the nearest original
row of the same part. Args: <hair npz> <out npz> [ratio]"""
import bpy, sys, bmesh
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]; H = dict(np.load(a[0])); R = float(a[2]) if len(a) > 2 else 0.5
co, tri, uv, braid = H['co'], H['tri'], H['uv'], H['braid']
# weld rows by position for a manifold mesh; UVs go on loops
key = np.round(co, 6); u, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
me = bpy.data.meshes.new('h'); me.from_pydata(u.tolist(), [], inv[tri].tolist()); me.update()
uvl = me.uv_layers.new(name='UVMap'); loops_uv = uv[tri].reshape(-1, 2); uvl.data.foreach_set('uv', loops_uv.ravel())
ob = bpy.data.objects.new('h', me); bpy.context.scene.collection.objects.link(ob); bpy.context.view_layer.objects.active = ob
bv = np.zeros(len(u), bool); bv[inv[braid]] = True
vg = ob.vertex_groups.new(name='braid'); vg.add(np.where(bv)[0].tolist(), 1.0, 'REPLACE')
mod = ob.modifiers.new('d', 'DECIMATE'); mod.ratio = R; mod.vertex_group = 'braid'; mod.delimit = {'SEAM', 'UV'}; mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
me = ob.data; bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
uvd = me.uv_layers['UVMap'].data
P = np.array([v.co[:] for v in me.vertices]); rows = {}; pos = []; uvs = []; T = []
for p in me.polygons:
    r = []
    for l in p.loop_indices:
        vi = me.loops[l].vertex_index; k = (vi, round(uvd[l].uv[0], 6), round(uvd[l].uv[1], 6))
        if k not in rows: rows[k] = len(pos); pos.append(P[vi]); uvs.append(uvd[l].uv[:])
        r.append(rows[k])
    T.append(r)
pos = np.array(pos); uvs = np.array(uvs); T = np.array(T)
# weights / braid flag from the nearest original row (braid rows only among braid rows)
d = ((pos[:, None, :] - co[None, ::1, :]) ** 2).sum(-1) if len(pos) * len(co) < 2e7 else None
import numpy.linalg as la
idx = np.array([np.argmin(((co - p) ** 2).sum(1)) for p in pos])
out = dict(H); out.update(co=pos, tri=T, uv=uvs, wj=H['wj'][idx], ww=H['ww'][idx], braid=H['braid'][idx], f2orig=H['f2orig'][idx])
np.savez(a[1], **out); print('DECIMATED', len(tri), '->', len(T), 'rows', len(pos))
