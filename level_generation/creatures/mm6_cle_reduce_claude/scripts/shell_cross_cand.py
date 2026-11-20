"""Cloak shell crossing audit (../mm6_cle_claude/scripts/shell_cross.py) for the source Body and every Cand_* in a
ladder blend. Faces take the cloak/inner labels of the nearest rig_v4 face centroid at rest
(work/cloak_side_labels.npz). Each inner vertex is tied at rest to its nearest outer-face point; per frame an inner
vertex whose offset along that face's normal turns positive by more than 2 mm crosses.
Usage: blender -b -P shell_cross_cand.py -- <ladder blend> [clips...]; prints SHELL <mesh> <clip> {...}."""
import bpy, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, args[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
L = np.load(os.path.join(HERE, 'work', 'cloak_side_labels.npz'))
tree0 = kdtree.KDTree(len(L['cen']))
for i, c in enumerate(L['cen']):
    tree0.insert(c, i)
tree0.balance()
TOL, RIM = 0.002, 0.004
clips = args[1:] or ['Standing', 'Walking', 'Attack', 'Cast', 'Hit', 'Fidget', 'Death', 'Dead']


def positions(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = [o.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear(); return P


def rest():
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.update()


meshes = ['Body'] + sorted(o.name for o in bpy.data.objects if o.name.startswith('Cand_'))
setup = {}
rest()
for name in meshes:
    o = bpy.data.objects[name]; me = o.data; me.calc_loop_triangles()
    for o2 in bpy.data.objects:
        if o2.type == 'MESH': o2.hide_viewport = o2.name not in meshes
    R = positions(o)
    cen = np.array([np.mean([R[i][:] for i in p.vertices], 0) for p in me.polygons])
    if name == 'Body':   # the source: its own rig_v4 face by centroid (exact)
        q0 = [tree0.find(c) for c in cen]; j = np.array([x[1] for x in q0]); dist = np.array([x[2] for x in q0])
        cloak, inner = L['cloak'][j], L['inner'][j]; src_lab = (cloak, inner)
        src_bvh = BVHTree.FromPolygons(R, [tuple(p.vertices) for p in me.polygons])
    else:   # candidates: the source face under each face centroid (centroids of large faces miss the rig_v4 ones)
        hits = [src_bvh.find_nearest(c) for c in cen]
        j = np.array([h[2] for h in hits]); dist = np.array([h[3] for h in hits])
        cloak, inner = src_lab[0][j], src_lab[1][j]
    otris = [t for t in me.loop_triangles if cloak[t.polygon_index] and not inner[t.polygon_index]]
    iverts = sorted({v for p in me.polygons if inner[p.index] for v in p.vertices} - {v for t in otris for v in t.vertices})
    bvh = BVHTree.FromPolygons(R, [tuple(t.vertices) for t in otris])
    ties = []
    for v in iverts:
        loc, nrm, fi, d = bvh.find_nearest(R[v])
        if fi is None or d > 0.05:
            continue
        a, b, c = (R[i] for i in otris[fi].vertices)
        off = (R[v] - loc).dot((b - a).cross(c - a).normalized())
        if off > -RIM:
            continue
        ties.append((v, fi, loc.copy()))
    setup[name] = (o, R, otris, ties)
    print('TIES', name, len(ties), 'of', len(iverts), 'label dist p99 mm', round(float(np.percentile(dist, 99)) * 1000, 1), 'inner faces', int(inner.sum()))
res = {}
spots = {}
for clip in clips:
    act = bpy.data.actions.get(clip)
    if act is None:
        continue
    rig.animation_data.action = act
    f0, f1 = (int(round(x)) for x in act.frame_range)
    acc = {n: [0, 0, 0.0, 0] for n in meshes}   # frames with, worst count, depth, worst frame
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for name in meshes:
            o, R, otris, ties = setup[name]; P = positions(o); n = 0; depth = 0.0
            for v, fi, rp in ties:
                ta, tb, tc = (R[i] for i in otris[fi].vertices); a, b, c = (P[i] for i in otris[fi].vertices)
                q = barycentric_transform(rp, ta, tb, tc, a, b, c)
                d = (P[v] - q).dot((b - a).cross(c - a).normalized())
                if d > TOL:
                    n += 1; depth = max(depth, d); spots.setdefault(name, set()).add(tuple(round(x, 2) for x in R[v]))
            s = acc[name]; s[0] += n > 0
            if n > s[1]: s[1], s[3] = n, f
            s[2] = max(s[2], depth)
    for name in meshes:
        s = acc[name]
        print('SHELL', name, clip, json.dumps({'frames_with': s[0], 'of': f1 - f0 + 1, 'worst': s[1], 'frame': s[3],
                                               'depth_mm': round(s[2] * 1000, 1)}))
for name, sp in spots.items():
    print('SPOTS', name, sorted(sp))
    np.save(os.path.join(HERE, 'work', f'shell_spots_{name}.npy'), np.array(sorted(sp)))
