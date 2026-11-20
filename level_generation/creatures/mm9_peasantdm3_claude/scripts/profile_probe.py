import bpy, sys, os, bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
shell = L.find_part(lab, co, 0.266, 0.595); hair = L.find_part(lab, co, 0.393, 0.607)
s = co[lab == shell]; xc = (s[:, 0].min() + s[:, 0].max()) / 2
print('XC', xc)
mid = s[np.abs(s[:, 0] - xc) < 0.012]
for z0 in np.arange(0.27, 0.60, 0.01):
    q = mid[(mid[:, 2] >= z0) & (mid[:, 2] < z0 + 0.01)]
    if len(q): print(f'PROF z {z0:.2f} front y {q[:,1].min():+.3f} back y {q[:,1].max():+.3f}')
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
hv = set(np.where(lab == hair)[0].tolist())
bnd = [e for e in bm.edges if e.is_boundary and e.verts[0].index in hv]
print('HAIRBOUNDARY edges', len(bnd), 'z', sorted(round(co[e.verts[0].index, 2], 3) for e in bnd)[:5], '...')
sv = set(np.where(lab == shell)[0].tolist())
bnd = [e for e in bm.edges if e.is_boundary and e.verts[0].index in sv]
print('SHELLBOUNDARY edges', len(bnd), sorted(set(round(co[e.verts[0].index, 2], 2) for e in bnd)))
# vertex groups dominating hair and shell
vg = {g.index: g.name for g in body.vertex_groups}
from collections import Counter
for name, part in (('hair', hair), ('shell', shell)):
    c = Counter()
    for i in np.where(lab == part)[0]:
        ws = sorted(((g.weight, vg[g.group]) for g in body.data.vertices[i].groups), reverse=True)
        c[' '.join(f'{n}:{w:.1f}' for w, n in ws[:2])] += 1
    print('WEIGHTS', name, c.most_common(8))
