"""Neck pass probe: manifoldness of the body skin (part 0) and head shell (part 10), and which vertices of each lie inside the
other (ray parity). Args: <blend>"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(o.data); pl = bm.verts.layers.int['part']
for p in (0, 10):
    fs = [f for f in bm.faces if all(v[pl] == p for v in f.verts)]
    es = {e for f in fs for e in f.edges}
    bad = [e for e in es if len([f for f in e.link_faces if f in set(fs)]) != 2]
    print('PART', p, 'faces', len(fs), 'non-manifold/boundary edges', len(bad), [tuple(round(c, 2) for c in e.verts[0].co) for e in bad[:6]])
def tree_of(p):
    fs = [f for f in bm.faces if all(v[pl] == p for v in f.verts)]
    return BVHTree.FromPolygons([v.co[:] for v in bm.verts], [[v.index for v in f.verts] for f in fs])
def inside(tree, p):
    votes = 0
    for d in (Vector((1, 0, 0)), Vector((0, 0, -1)), Vector((0, 1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))):
        c = 0; o_ = p.copy()
        for _ in range(60):
            h = tree.ray_cast(o_, d)
            if h[0] is None: break
            c += 1; o_ = h[0] + d * 1e-5
        votes += c % 2
    return votes >= 3
ts, th = tree_of(0), tree_of(10)
H = [v for v in bm.verts if v[pl] == 10]; S = [v for v in bm.verts if v[pl] == 0]
hin = np.array([inside(ts, v.co) for v in H]); Ph = np.array([v.co[:] for v in H])
sin_ = np.array([inside(th, v.co) for v in S]); Ps = np.array([v.co[:] for v in S])
print('HEAD verts inside skin', hin.sum(), 'of', len(H))
for lo, hi in ((0, 0.1), (0.1, 0.17), (0.17, 0.25), (0.25, 0.6)):
    m = hin & (np.abs(Ph[:, 0]) >= lo) & (np.abs(Ph[:, 0]) < hi)
    if m.any(): print(f'  |x| {lo}-{hi}: {m.sum()} y {Ph[m,1].min():.2f}..{Ph[m,1].max():.2f} z {Ph[m,2].min():.2f}..{Ph[m,2].max():.2f}')
print('SKIN verts inside head', sin_.sum(), 'at', Ps[sin_].min(0).round(2) if sin_.any() else '', Ps[sin_].max(0).round(2) if sin_.any() else '')
