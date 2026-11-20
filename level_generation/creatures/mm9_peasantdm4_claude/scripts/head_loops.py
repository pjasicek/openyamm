"""Diagnostic: boundary loops of the head-set faces of a master blend (head = 1, not hands): edge count, centre, bbox,
mean radius about the centre. Args (Blender): <blend>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; bm = bmesh.new(); bm.from_mesh(ob.data)
hl = bm.faces.layers.int.get('head'); hal = bm.faces.layers.int.get('hand')
bE = [e for e in bm.edges if e.is_boundary and e.link_faces[0][hl] == 1 and not (hal and e.link_faces[0][hal] == 1)]
seen = set()
for e0 in bE:
    if e0.index in seen: continue
    loop = []; stack = [e0]
    while stack:
        e = stack.pop()
        if e.index in seen: continue
        seen.add(e.index); loop.append(e)
        for v in e.verts:
            for e2 in v.link_edges:
                if e2.is_boundary and e2.index not in seen and e2 in bE: stack.append(e2)
    P = np.array([v.co[:] for e in loop for v in e.verts])
    c = P.mean(0)
    print('HLOOP', len(loop), np.round(c, 3).tolist(), 'lo', np.round(P.min(0), 3).tolist(), 'hi', np.round(P.max(0), 3).tolist(), 'r', round(float(np.linalg.norm(P - c, axis=1).mean()), 3))
