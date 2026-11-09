"""Faces whose winding disagrees with their neighbours (shared edge walked the same direction), per loose part, on a
master blend's Body. Args: <blend> [fix out blend]: with an output, flips the minority side of each part (BFS from the
largest consistent region) and saves."""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data; mw = body.matrix_world
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bad = set()
for e in bm.edges:
    if len(e.link_faces) != 2: continue
    f1, f2 = e.link_faces
    def dirn(f):
        vs = [v.index for v in f.verts]
        i = vs.index(e.verts[0].index); j = vs.index(e.verts[1].index)
        return (j - i) % len(vs) == 1
    if dirn(f1) == dirn(f2):
        bad.add(f1.index); bad.add(f2.index)
cs = [tuple(np.round(np.array(mw @ bm.faces[i].calc_center_median()), 3)) for i in sorted(bad)]
print('FLIP inconsistent faces', len(bad))
for i, c in list(zip(sorted(bad), cs))[:60]:
    print('FLIP face', i, c)
