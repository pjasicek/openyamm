"""Probe the sleeves of the Yrsa master: per side, the forearm axis (elbow -> wrist joint heads at rest) and the sleeve
vertices (loose part 5) binned along it: count, mean and max radius, and the cuff end. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
M = rig.matrix_world
for s in 'LR':
    e = M @ rig.data.bones[f'FHP {s} Forearm'].head_local; w = M @ rig.data.bones[f'FHP {s} Hand'].head_local
    print(s, 'elbow', np.round(e[:], 3), 'wrist', np.round(w[:], 3), 'len', round((w - e).length, 3))
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for ed in x.link_edges:
            y = ed.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
co = np.array([body.matrix_world @ v.co for v in bm.verts])
for s, sg in (('L', 1), ('R', -1)):
    e = np.array(M @ rig.data.bones[f'FHP {s} Forearm'].head_local); w = np.array(M @ rig.data.bones[f'FHP {s} Hand'].head_local)
    ax = (w - e) / np.linalg.norm(w - e)
    sel = np.where((comp == 5) & (np.sign(co[:, 0]) == np.sign(e[0])))[0]
    t = (co[sel] - e) @ ax; rad = co[sel] - e - np.outer(t, ax); r = np.linalg.norm(rad, axis=1)
    print(s, 'axis', np.round(ax, 3), 'sleeve verts', len(sel), 't range', round(t.min(), 3), round(t.max(), 3))
    for lo in np.arange(-0.05, t.max() + 0.02, 0.02):
        m = (t >= lo) & (t < lo + 0.02)
        if m.any(): print(f'   t {lo:+.2f} n {m.sum():3d} r mean {r[m].mean():.3f} max {r[m].max():.3f} min {r[m].min():.3f}')
