"""Probe: open boundary loops near each wrist of a master (rest pose): s along forearm->hand from the hand joint, r from the
axis, edge count, whether its faces are lining faces. Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world
bm = bmesh.new(); bm.from_mesh(ob.data)
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
ll = bm.faces.layers.int.get('lined')
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    def sr(p):
        rel = np.array(p) - a1; s = rel @ ax; return s, np.linalg.norm(rel - s * ax)
    be = [e for e in bm.edges if e.is_boundary]
    seen = set()
    for e0 in be:
        if e0 in seen: continue
        comp = []; stack = [e0]; seen.add(e0)
        while stack:
            e = stack.pop(); comp.append(e)
            for v in e.verts:
                for e2 in v.link_edges:
                    if e2.is_boundary and e2 not in seen: seen.add(e2); stack.append(e2)
        P = np.array([tuple(mw @ v.co) for e in comp for v in e.verts])
        s, r = sr(P.mean(0))
        if -0.3 < s < 0.1 and r < 0.15:
            f = comp[0].link_faces[0]
            print('LOOP', tok, 'edges', len(comp), 's %.3f r %.3f' % (s, r), 'smin %.3f smax %.3f' % (min(sr(p)[0] for p in P), max(sr(p)[0] for p in P)),
                  'rmean %.3f' % np.mean([sr(p)[1] for p in P]), 'hand', f[lh], 'head', f[lk], 'lined', f[ll] if ll else None)
