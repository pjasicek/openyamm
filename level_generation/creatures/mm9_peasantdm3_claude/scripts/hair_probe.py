import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
hair = L.find_part(lab, co, 0.393, 0.607); shell = L.find_part(lab, co, 0.266, 0.595)
print('PARTS hair', hair, (lab == hair).sum(), 'shell', shell, (lab == shell).sum())
h = co[lab == hair]
c = np.array([0, h[:, 1].mean(), 0])
for z0 in np.arange(0.39, 0.61, 0.02):
    s = (h[:, 2] >= z0) & (h[:, 2] < z0 + 0.02)
    if s.any():
        r = np.hypot(h[s, 0], h[s, 1] - c[1])
        print(f'HAIR z {z0:.2f} n {s.sum():3d} x {h[s,0].min():+.3f}..{h[s,0].max():+.3f} y {h[s,1].min():+.3f}..{h[s,1].max():+.3f} r {r.min():.3f}..{r.max():.3f}')
sh = co[lab == shell]
for z0 in np.arange(0.26, 0.60, 0.02):
    s = (sh[:, 2] >= z0) & (sh[:, 2] < z0 + 0.02)
    if s.any():
        print(f'SHELL z {z0:.2f} n {s.sum():3d} x {sh[s,0].min():+.3f}..{sh[s,0].max():+.3f} y {sh[s,1].min():+.3f}..{sh[s,1].max():+.3f}')
b = co[lab == 0]
for z0 in np.arange(0.20, 0.42, 0.02):
    s = (b[:, 2] >= z0) & (b[:, 2] < z0 + 0.02)
    if s.any():
        print(f'BODY z {z0:.2f} n {s.sum():3d} x {b[s,0].min():+.3f}..{b[s,0].max():+.3f} y {b[s,1].min():+.3f}..{b[s,1].max():+.3f}')
# small parts
for p in np.unique(lab):
    s = lab == p
    if s.sum() < 100:
        q = co[s]; print('SMALL', p, s.sum(), q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
