"""Small pieces of the reduced candidate (work/ladder.blend, REA_CAND default Cand_55): per piece faces, base point
on the body skin, tip (farthest vertex from the base), length, base radius, dominant bone.
Writes work/parts_probe.json. Usage: blender -b -P parts_probe.py"""
import json, os, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
c = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]; me = c.data
co = np.array([v.co[:] for v in me.vertices]); n = len(co)
ed = np.array([e.vertices[:] for e in me.edges])


def components(n, ed):
    """connected component label per vertex (union-find; Blender's Python has no scipy)"""
    parent = np.arange(n)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for a, b in ed:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    return np.unique(roots, return_inverse=True)[1]


lab = components(n, ed)
polys = [p.vertices[:] for p in me.polygons]; plab = np.array([lab[p[0]] for p in polys])
sizes = np.bincount(plab, minlength=lab.max() + 1); body = int(sizes.argmax())
bp = [p for p, l in zip(polys, plab) if l == body]
tree = BVHTree.FromPolygons([tuple(x) for x in co], bp)
gname = {g.index: g.name for g in c.vertex_groups}
out = []
for piece in np.argsort(-sizes):
    if piece == body or sizes[piece] > 400 or sizes[piece] == 0:
        continue
    ids = np.flatnonzero(lab == piece); p = co[ids]
    dist = np.array([tree.find_nearest(Vector(x))[3] for x in p])
    near = dist < max(dist.min() + 0.0015, 0.0008)
    base = p[near].mean(0); tip = p[np.argmax(np.linalg.norm(p - base, axis=1))]
    hit = tree.find_nearest(Vector(base)); nrm = np.array(hit[1])
    bones = {}
    for i in ids:
        for g in me.vertices[int(i)].groups:
            bones[gname[g.group]] = bones.get(gname[g.group], 0) + g.weight
    out.append({'piece': int(piece), 'faces': int(sizes[piece]), 'centre': p.mean(0).round(4).tolist(),
                'base': base.round(4).tolist(), 'tip': tip.round(4).tolist(), 'skin': np.array(hit[0]).round(4).tolist(),
                'skin_normal': nrm.round(3).tolist(), 'length': round(float(np.linalg.norm(tip - base)), 4),
                'base_radius': round(float(np.linalg.norm(p[near] - base, axis=1).mean()), 4),
                'min_skin_dist': round(float(dist.min()), 4), 'extent': (p.max(0) - p.min(0)).round(4).tolist(),
                'bone': max(bones, key=bones.get)})
json.dump(out, open(os.path.join(HERE, 'work', 'parts_probe.json'), 'w'), indent=1)
for o in out:
    print('PIECE', o['piece'], o['faces'], o['centre'], 'len', o['length'], 'r', o['base_radius'], 'skin', o['min_skin_dist'], o['bone'])
