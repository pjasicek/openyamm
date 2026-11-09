"""Head mesh audit on the UV master: boundary loops, non-manifold edges, faces whose normal points to the head centre. Args: blend"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
h = bpy.data.objects['Head']
bm = bmesh.new(); bm.from_mesh(h.data); bm.edges.ensure_lookup_table()
b = [e for e in bm.edges if e.is_boundary]
nm = [e for e in bm.edges if len(e.link_faces) > 2]
print('BOUND', len(b), 'NONMAN', len(nm), 'VERTS', len(bm.verts), 'FACES', len(bm.faces))
left = set(b); loops = []
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
for l in sorted(loops, key=len, reverse=True)[:12]:
    p = np.array([v.co[:] for e in l for v in e.verts])
    print('LOOP', len(l), p.mean(0).round(3), (p.max(0) - p.min(0)).round(3))
c = np.array([v.co[:] for v in bm.verts]); cen = 0.5 * (c.min(0) + c.max(0))
inw = [f for f in bm.faces if np.dot(np.array(f.normal[:]), np.array(f.calc_center_median()[:]) - cen) < 0]
print('INWARD faces', len(inw))
small = [f for f in bm.faces if f.calc_area() < 1e-8]
print('TINY', len(small))
