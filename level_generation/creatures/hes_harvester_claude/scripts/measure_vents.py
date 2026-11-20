"""The heat-vent frames (components 2, 44 of the raw return): the 2D convex hull (x, z) of each frame's front ring,
and the depth of the surface inside the frame (rays along +y from the front through the frame's centre region)."""
import os
import sys

import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvester_common as tc  # noqa: E402


def hull2d(points):
    """Convex hull (monotone chain), counter-clockwise."""
    pts = sorted(map(tuple, points))
    def half(seq):
        out = []
        for q in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (q[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(q)
        return out
    lower, upper = half(pts), half(pts[::-1])
    return np.array(lower[:-1] + upper[:-1])

obj = tc.import_raw()
bm = bmesh.new(); bm.from_mesh(obj.data)
labels = tc.component_labels(bm)
co = np.array([v.co[:] for v in bm.verts])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
frame_faces = [f for f in bm.faces if labels[f.verts[0].index] in (2, 44)]
others = bmesh.new()
bvh_all = BVHTree.FromBMesh(bm)
np.set_printoptions(precision=3, suppress=True)
for c in (2, 44):
    p = co[labels == c]
    front = p[p[:, 1] < p[:, 1].min() + float(os.environ.get("FRONT", 0.12))]
    print("  front pts y,z", np.unique(np.round(front[:, [0, 1, 2]], 2), axis=0).tolist())
    pts = hull2d(front[:, [0, 2]])
    print('FRAME', c, 'front y', front[:, 1].min(), front[:, 1].max(), 'hull', pts.round(3).tolist())
    cx, cz = pts.mean(0)
    for dx, dz in ((0, 0), (-0.2, 0), (0.2, 0), (0, -0.12), (0, 0.15)):
        loc, nrm, idx, dist = bvh_all.ray_cast(Vector((cx + dx, -4.0, cz + dz)), Vector((0, 1, 0)))
        hitc = labels[bm.faces[idx].verts[0].index] if idx is not None else None
        print('  ray', round(cx + dx, 3), round(cz + dz, 3), '-> y', None if loc is None else round(loc.y, 3), 'comp', hitc,
              'n', None if nrm is None else tuple(round(x, 2) for x in nrm))
