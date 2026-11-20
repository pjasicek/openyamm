"""After removing interior faces (|x|<0.6) and the tongue: dump the boundary loop(s) in the mouth box. Args: -- <blend> <npz>"""
import bpy, sys, os, bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = M.parts(bm); R = M.roles(bm, comp)
inside = {i for i in M.interior_faces(bm, comp, R['shell']) if abs(bm.faces[i].calc_center_median().x) < 0.6}
dele = [bm.faces[i] for i in inside] + [f for f in bm.faces if comp[f.verts[0].index] == R['tongue']]
bmesh.ops.delete(bm, geom=dele, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.edges.ensure_lookup_table()
cand = [e for e in bm.edges if e.is_boundary and all(M.in_box(v.co, ((-0.7, 0.7), (-5.3, -3.6), (14.6, 15.5))) for v in e.verts)]
left = set(cand); loops = []
while left:
    e = left.pop(); chain = [e.verts[0], e.verts[1]]
    for _ in range(2):
        while True:
            v = chain[-1]; nxt = [x for x in v.link_edges if x in left]
            if not nxt: break
            x = nxt[0]; left.discard(x); chain.append(x.other_vert(v))
        chain.reverse()
    loops.append(chain)
loops.sort(key=len, reverse=True)
for L in loops[:6]:
    P = np.array([tuple(v.co) for v in L])
    print('LOOP', len(L), 'closed', L[0] == L[-1], 'lo', P.min(0).round(3), 'hi', P.max(0).round(3))
np.savez(a[1], *[np.array([tuple(v.co) for v in L]) for L in loops[:4]])
