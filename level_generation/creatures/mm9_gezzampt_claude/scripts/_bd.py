import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
print('LOOPS total verts', len(bm.verts))
bd = {e for e in bm.edges if e.is_boundary}
print('LOOPS boundary', len(bd), 'nonmanifold', sum(1 for e in bm.edges if not e.is_manifold), 'wire', sum(1 for e in bm.edges if e.is_wire))
out = []
while bd:
    e0 = bd.pop(); st = [e0]; cur = [e0]
    while st:
        e = st.pop()
        for v in e.verts:
            for f in v.link_edges:
                if f in bd: bd.remove(f); cur.append(f); st.append(f)
    q = np.array([v.co[:] for e in cur for v in e.verts]); out.append((len(cur), np.round(q.mean(0), 3).tolist(), np.round(np.ptp(q, 0), 3).tolist()))
out.sort(reverse=True)
print('LOOPS n', len(out))
for x in out[:40]: print('LOOPS', x)
