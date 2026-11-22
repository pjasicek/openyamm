"""Probe the fist: per finger, overlap pairs of its distal faces with the rest, for scaled FIST angles."""
import bpy, os, sys
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handpose as H
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
rig = bpy.data.objects['Hand_Rig']; mesh = bpy.data.objects['Hand']; me0 = mesh.data
dg = bpy.context.evaluated_depsgraph_get()
gname = {g.index: g.name for g in mesh.vertex_groups}
dom = [gname[max(v.groups, key=lambda e: e.weight).group] for v in me0.vertices]
tris = np.array([p.vertices[:] for p in me0.polygons])
fdom = [max(set(dom[i] for i in t), key=[dom[i] for i in t].count) for t in tris]
ORDER = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
DIST = {f: [k for k, d in enumerate(fdom) if d in (f + '_2', f + '_3')] for f in ORDER}
OTHER = {f: [k for k, d in enumerate(fdom) if not d.startswith(f)] for f in ORDER}
args = sys.argv[sys.argv.index('--') + 1:]
F = {'Thumb': (35, 35, 40), 'Index': (70, 85, 60)}
for spec in args:
    t1, t2, t3, f1, f2, f3 = map(float, spec.split(','))
    flex = {f: ((t1, t2, t3) if f == 'Thumb' else (f1, f2, f3)) for f in ORDER}
    H.reset(rig); H.hand(rig, flex, spread=-5)
    ev = mesh.evaluated_get(dg); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3); ev.to_mesh_clear()
    res = {}
    for f in ORDER:
        a = BVHTree.FromPolygons(co.tolist(), tris[DIST[f]].tolist())
        b = BVHTree.FromPolygons(co.tolist(), tris[OTHER[f]].tolist())
        pairs = a.overlap(b)
        vs = sorted({int(v) for k in DIST[f] for v in tris[k]})
        deep = []
        for v in vs:
            loc, nrm, idx, d = b.find_nearest(co[v].tolist())
            if loc is not None:
                sd = float(np.dot(co[v] - np.array(loc), np.array(nrm)))
                if sd < 0: deep.append((-sd, fdom[OTHER[f][idx]]))
        deep.sort(reverse=True)
        res[f] = (len(pairs), round(deep[0][0] * 100, 2) if deep else 0, deep[0][1] if deep else '',
                  round(np.percentile([d for d, _ in deep], 90) * 100, 2) if deep else 0)
    print('PROBE', spec, res)
