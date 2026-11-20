"""Dump the creature project's final rest mesh (../mm9_dookmilitia_claude/work/final_v1.blend, Body) triangulated:
per triangle centroid, corners, material index and every int face attribute -> work/final_tris.npz."""
import bpy, bmesh, sys, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm9_dookmilitia_claude', 'work', 'final_v1.blend'))
body = bpy.data.objects['Body']; me = body.data
print('OBJ', [(o.name, o.type) for o in bpy.data.objects])
print('ATTR', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')])
print('MATS', [m.name if m else None for m in me.materials], 'mw', [list(r) for r in body.matrix_world])
bm = bmesh.new(); bm.from_mesh(me)
lays = {n: bm.faces.layers.int[n] for n in bm.faces.layers.int.keys()}
vf = bm.verts.layers.float['graft_s']; vi = bm.verts.layers.int['graft_side']
res = bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.faces.ensure_lookup_table()
mw = body.matrix_world
co = np.array([[(mw @ v.co)[:] for v in f.verts] for f in bm.faces])
out = dict(co=co, cen=co.mean(1), matidx=np.array([f.material_index for f in bm.faces]))
for n, l in lays.items(): out['a_' + n] = np.array([f[l] for f in bm.faces])
out['graft_s'] = np.array([[v[vf] for v in f.verts] for f in bm.faces]); out['graft_side'] = np.array([[v[vi] for v in f.verts] for f in bm.faces])
np.savez(os.path.join(HERE, 'work', 'final_tris.npz'), **out)
print('DUMP', len(bm.faces), {n: np.unique(out['a_' + n]).tolist()[:30] for n in lays})
