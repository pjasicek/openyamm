"""LOD0 budget (PF4, 2026-11-02): F1's skirt lining (hidden inside the skirt; seen only from below) decimated by Blender's collapse in the
asm, before any UVs (PF4 lays its own). Its faces are replaced by the decimated ones on NEW vertex rows appended to the asm (the collapse
moves vertices), the old lining rows stay unreferenced, so every other asm index (F1's tweak, weights and seam rules) is unchanged.
Vertices the lining shares (by position) with another part are held. Args: <asm in> <asm out> <part> <ratio>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
AIN, AOUT, PART, RATIO = a[0], a[1], a[2], float(a[3])
A = dict(np.load(AIN)); co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]
pi = names.index(PART); fs = np.where((comp[tri] == pi).all(1))[0]
verts, inv = np.unique(tri[fs], return_inverse=True); ft = inv.reshape(-1, 3)
key = np.round(co, 5); _, kinv = np.unique(key, axis=0, return_inverse=True); kinv = kinv.ravel()
other = np.zeros(kinv.max() + 1, bool); other[kinv[np.unique(tri[(comp[tri] != pi).any(1)])]] = True
shared = other[kinv[verts]]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new(PART); me.from_pydata(co[verts].tolist(), [], ft.tolist()); me.update()
ob = bpy.data.objects.new(PART, me); bpy.context.scene.collection.objects.link(ob)
vg = ob.vertex_groups.new(name='free'); vg.add(np.where(~shared)[0].tolist(), 1.0, 'REPLACE')
md = ob.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = RATIO; md.vertex_group = 'free'; md.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.modifier_apply(modifier='dec')
me = ob.data
P = np.array([v.co[:] for v in me.vertices]); T = np.array([[v for v in p.vertices] for p in me.polygons])
n0 = len(co)
A['co'] = np.vstack([co, P]); A['comp'] = np.r_[comp, np.full(len(P), pi)]
keep = np.ones(len(tri), bool); keep[fs] = False
A['tri'] = np.vstack([tri[keep], T + n0])
np.savez(AOUT, **A)
print('REDUCE', PART, len(fs), '->', len(T), 'held', int(shared.sum()), 'tris total', len(A['tri']))
