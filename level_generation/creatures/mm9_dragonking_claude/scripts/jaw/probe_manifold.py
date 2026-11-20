"""Duplicate faces, non-manifold and boundary edges of the main shell near the mouth. Args: -- <blend>"""
import bpy, sys, os, bmesh
import numpy as np
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
comp = M.parts(bm); shell = np.bincount(comp).argmax()
box = ((-0.9, 0.9), (-5.4, -2.5), (14.4, 16.6))
keys = Counter(tuple(sorted(v.index for v in f.verts)) for f in bm.faces)
dups = [k for k, n in keys.items() if n > 1]
print('duplicate faces total', len(dups), 'in box', sum(1 for k in dups if M.in_box(bm.verts[k[0]].co, box)) if dups else 0)
nm = [e for e in bm.edges if comp[e.verts[0].index] == shell and len(e.link_faces) > 2 and all(M.in_box(v.co, box) for v in e.verts)]
bd = [e for e in bm.edges if comp[e.verts[0].index] == shell and e.is_boundary and all(M.in_box(v.co, box) for v in e.verts)]
print('non-manifold (>2 faces) edges in box', len(nm), 'boundary edges in box', len(bd))
for e in (nm + bd)[:40]:
    print(' ', 'NM' if e in nm else 'BD', [tuple(round(c, 3) for c in v.co) for v in e.verts])
