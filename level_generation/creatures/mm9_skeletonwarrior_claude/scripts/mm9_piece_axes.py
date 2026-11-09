import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
m = bpy.data.objects['MM9_Mesh']; rig = bpy.data.objects['MM9_Rig']
v = np.array([tuple(m.matrix_world @ x.co) for x in m.data.vertices])
gn = {g.index: g.name for g in m.vertex_groups}
lab = np.array([gn[max(x.groups, key=lambda g: g.weight).group] for x in m.data.vertices])
for n in ('Bip01 R Thigh', 'Bip01 R Calf', 'Bip01 R Foot', 'Bip01 R Toe0', 'Bip01 R UpperArm', 'Bip01 R Forearm', 'Bip01 R Hand', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head'):
    p = v[lab == n]; c = p.mean(0); u, s, vt = np.linalg.svd(p - c, full_matrices=False); a = vt[0]
    if a[2] < 0: a = -a
    print('AX', n, len(p), 'cen', np.round(c, 3), 'axis', np.round(a, 3), 'sv', np.round(s, 2), 'lo', np.round(p.min(0), 3), 'hi', np.round(p.max(0), 3))
