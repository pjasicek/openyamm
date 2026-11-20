"""Reduce painted rigid parts of the UV mesh npz (LOD0 budget), keeping their UVs (decimate delimited by UV seams): each listed part
'name=target' is decimated as one object; every new vertex takes `orig` (and so its weights) from the nearest old vertex of the same part.
Parts reduced here must be rigid per piece (bone pieces, skulls), so the nearest-vertex weights are exact. Args: <in npz> <out npz> <part=target ...>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
D = dict(np.load(a[0])); OUT = a[1]; SPEC = {s.split('=')[0]: int(s.split('=')[1]) for s in a[2:]}
names = [str(x) for x in D['names']]; co, tri, uv, orig, comp, mat = D['co'], D['tri'], D['uv'], D['orig'], D['comp'], D['mat']
bpy.ops.wm.read_factory_settings(use_empty=True)
keep_f = np.ones(len(tri), bool); addP = []; addUV = []; addO = []; addC = []; addT = []; addM = []
base = len(co)
for part, target in SPEC.items():
    k = names.index(part); fi = np.where(comp[tri[:, 0]] == k)[0]
    if len(fi) <= target: print('KEEP', part, len(fi)); continue
    used, inv = np.unique(tri[fi], return_inverse=True)
    me = bpy.data.meshes.new(part); me.from_pydata(co[used].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    ul = me.uv_layers.new(name='UVMap')
    for p_, f in zip(me.polygons, tri[fi]):
        for li, vi in zip(p_.loop_indices, f): ul.data[li].uv = uv[vi]
    o = bpy.data.objects.new(part, me); bpy.context.scene.collection.objects.link(o)
    for x in bpy.data.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-6); bpy.ops.object.mode_set(mode='OBJECT')
    md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = target / len(fi); md.use_collapse_triangulate = True; md.delimit = {'UV'}
    bpy.ops.object.modifier_apply(modifier='d'); me = o.data; me.calc_loop_triangles(); uvd = me.uv_layers['UVMap'].data
    P = np.array([v.co[:] for v in me.vertices]); Cu = co[used]
    def nearest(p): return int(np.argmin(np.sum((Cu - p) ** 2, 1)))
    keys = {}; T = []
    for lt in me.loop_triangles:
        row = []
        for l in lt.loops:
            vi = me.loops[l].vertex_index; u_ = tuple(np.round(uvd[l].uv, 6))
            kk = (vi, u_)
            if kk not in keys:
                keys[kk] = base + len(addP); addP.append(P[vi]); addUV.append(u_); addO.append(orig[used[nearest(P[vi])]]); addC.append(k)
            row.append(keys[kk])
        T.append(row)
    addT += T; addM += [int(mat[fi[0]])] * len(T); keep_f[fi] = False
    print('REDUCE', part, len(fi), '->', len(T))
D['co'] = np.vstack([co, np.array(addP)]); D['uv'] = np.vstack([uv, np.array(addUV)]); D['orig'] = np.r_[orig, np.array(addO, int)]; D['comp'] = np.r_[comp, np.array(addC, int)]
D['tri'] = np.vstack([tri[keep_f], np.array(addT, int)]); D['mat'] = np.r_[mat[keep_f], np.array(addM, int)]
if 'inner' in D and len(D['inner']) == len(tri): D['inner'] = np.r_[D['inner'][keep_f], np.zeros(len(addT), bool)]
for key in ('hand_piece', 'head_label'):
    if key in D: D[key] = np.r_[D[key], np.full(len(addP), -1)]
np.savez(OUT, **D); print('SAVED', len(D['co']), len(D['tri']))
