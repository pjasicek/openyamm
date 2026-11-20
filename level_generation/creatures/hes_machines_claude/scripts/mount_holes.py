"""List the open boundary loops of the turret's mount (part 0 of work/<name>_tex.blend, positions welded): size,
bounding box and mean normal of the faces along it. Args: -- <name>"""
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
bm = bmesh.new(); bm.from_mesh(bpy.data.objects[name].data)
layer = bm.faces.layers.int['part']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] != 0], context='FACES')
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
edges = {e for e in bm.edges if len(e.link_faces) == 1}
seen = set()
for e in edges:
    if e in seen:
        continue
    loop, stack = [], [e]
    seen.add(e)
    while stack:
        x = stack.pop(); loop.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y in edges and y not in seen:
                    seen.add(y); stack.append(y)
    pts = np.array([v.co[:] for x in loop for v in x.verts])
    n = np.mean([x.link_faces[0].normal[:] for x in loop], 0)
    print('LOOP', len(loop), 'lo', pts.min(0).round(3).tolist(), 'hi', pts.max(0).round(3).tolist(), 'n', n.round(2).tolist())
