"""List (and optionally delete) loose parts of Body: face count, centroid, distance to the nearest hand joint.
Args: in.blend [out.blend max_faces hand_dist]  (delete parts with <= max_faces faces within hand_dist m of a hand joint)"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
H = [np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones if b.name.endswith(' Hand')]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen = set(); parts = []
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; comp = []; seen.add(f.index)
    while st:
        g = st.pop(); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: seen.add(h.index); st.append(h)
    c = np.mean([np.array(v.co) for g in comp for v in g.verts], 0)
    parts.append((len(comp), c, min(np.linalg.norm(c - h) for h in H), comp))
parts.sort(key=lambda p: -p[0])
for n, c, d, _ in parts:
    print('PART', n, np.round(c, 3).tolist(), 'hand dist', round(float(d), 3))
if len(a) > 1:
    mx, hd = int(a[2]), float(a[3])
    dele = [g for n, c, d, comp in parts if n <= mx and d < hd for g in comp]
    bmesh.ops.delete(bm, geom=dele, context='FACES')
    bm.to_mesh(me); bpy.ops.wm.save_as_mainfile(filepath=a[1])
    print('DELETED faces', len(dele))
