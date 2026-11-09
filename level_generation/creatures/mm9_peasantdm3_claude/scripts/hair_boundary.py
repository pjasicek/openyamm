import bpy, bmesh, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = L.rest_coords(body); lab = L.loose_parts(body.data)
hair = lab[np.argmax(co[:, 2])]
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
be = [e for e in bm.edges if e.is_boundary and lab[e.verts[0].index] == hair]
# loops
adj = {}
for e in be:
    a, b = e.verts[0].index, e.verts[1].index
    adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
seen = set(); loops = []
for s in adj:
    if s in seen: continue
    loop = [s]; seen.add(s); cur = s
    while True:
        nx = [n for n in adj[cur] if n not in seen]
        if not nx: break
        cur = nx[0]; seen.add(cur); loop.append(cur)
    loops.append(loop)
xc = -0.0101
for l in loops:
    p = co[l]
    print('LOOP n', len(l), 'z', p[:, 2].min().round(3), p[:, 2].max().round(3), 'y', p[:, 1].min().round(3), p[:, 1].max().round(3), 'lat', np.abs(p[:, 0] - xc).min().round(3), np.abs(p[:, 0] - xc).max().round(3))
    for i in l[::max(1, len(l) // 12)]:
        print('   ', np.round(co[i], 3).tolist())
