"""Boundary loops per part and outside visibility per face (rays from 600 directions on a sphere around the body)."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work/' + sys.argv[sys.argv.index('--') + 1] + '_parts.blend'))
objs = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
for o in objs:
    bm = bmesh.new(); bm.from_mesh(o.data)
    bverts = {v for e in bm.edges if e.is_boundary for v in e.verts}
    loops = []; seen = set()
    for v in bverts:
        if v in seen: continue
        st = [v]; seen.add(v); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                if e.is_boundary:
                    y = e.other_vert(x)
                    if y not in seen: seen.add(y); st.append(y)
        c = np.array([tuple(p.co) for p in comp])
        loops.append((len(comp), [round(float(t), 3) for t in c.mean(0)], round(float(np.ptp(c, 0).max()), 3)))
    print('LOOPS', o.name, loops)
    bm.free()
# visibility
verts = []; polys = []; owner = []
for o in objs:
    off = len(verts)
    verts += [o.matrix_world @ v.co for v in o.data.vertices]
    for p in o.data.polygons:
        polys.append([i + off for i in p.vertices]); owner.append((o.name, p.index))
tree = BVHTree.FromPolygons(verts, polys)
hit = np.zeros(len(polys), bool)
n = 1500; centre = Vector((0, 0, 0.8))
ga = math.pi * (3 - math.sqrt(5))
fc = np.array([sum((verts[i] for i in p), Vector()) / len(p) for p in polys])
for k in range(n):
    z = 1 - 2 * (k + 0.5) / n; r = math.sqrt(1 - z * z); d = Vector((math.cos(ga * k) * r, math.sin(ga * k) * r, z))
    # orthographic ray grid perpendicular to d
    u = d.orthogonal().normalized(); w = d.cross(u)
    for a in np.linspace(-0.55, 0.55, 45):
        for b in np.linspace(-0.85, 0.85, 70):
            org = centre + d * 3 + u * a + w * b
            loc, nor, idx, dist = tree.ray_cast(org, -d, 6)
            if idx is not None: hit[idx] = True
res = {}
for o in objs:
    idx = [i for i, ow in enumerate(owner) if ow[0] == o.name]
    res[o.name] = (len(idx), int(hit[idx].sum()))
    o['visible'] = [int(hit[i]) for i in idx]
print('VIS', res)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work/' + sys.argv[sys.argv.index('--') + 1] + '_vis.blend'))
