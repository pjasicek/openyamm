"""Count folded rest faces (weight_refine.folded_faces: normal against the smoothed neighbourhood normal) of 'Body'
in a blend, per chain region. Args: <blend> [rings]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weight_refine as R
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
me.calc_loop_triangles()
tris = np.array([tuple(t.vertices) for t in me.loop_triangles])
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
t = tris[(piece[tris] == 0).all(1)]
bad = R.folded_faces(co, t, int(argv[1]) if len(argv) > 1 else 6)
ch = chain[t[:, 0]]
print('FOLDS total %d of %d' % (bad.sum(), len(t)), {int(c): int((bad & (ch == c)).sum()) for c in range(-1, 5)})
c = co[t[bad]].mean(1)
if bad.any():
    H, e = np.histogramdd(c[:, 1:], bins=(8, 6))
    print('FOLDS y-bins', np.round(e[0], 2).tolist()); print('FOLDS z-bins', np.round(e[1], 2).tolist())
    print(H.astype(int))
