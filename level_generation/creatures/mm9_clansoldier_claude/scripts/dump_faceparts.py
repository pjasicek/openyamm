import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Face']; P = np.array([v.co[:] for v in o.data.vertices])
for z in (-0.155, -0.15, -0.14, -0.13, -0.12, -0.11, -0.10, -0.09, -0.08, -0.06):
    m = np.abs(P[:, 2] - z) < 0.004
    r = P[m]
    if len(r) == 0: continue
    ys = np.sort(r[:, 1])
    gap = np.diff(ys); i = gap.argmax()
    print('DUMP', z, len(r), 'y', ys[0].round(3), ys[-1].round(3), 'x', r[:, 0].max().round(3), 'gap', gap[i].round(3), 'at', ys[i].round(3))
bm = bmesh.new(); bm.from_mesh(o.data)
seen = set(); 
for e0 in [e for e in bm.edges if e.is_boundary]:
    if e0 in seen: continue
    st = [e0]; seen.add(e0); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen: seen.add(y); st.append(y)
    q = np.array([v.co[:] for e in cur for v in e.verts])
    print('DUMP loop', len(cur), q.min(0).round(3), q.max(0).round(3))
