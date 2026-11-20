"""Mouth proportions of 'Body' in the bind pose, seen from the front: rays along +y on a 0.25 mm grid give a depth map;
the hole = rays that travel more than 6 mm past the lips. Prints hole width/height, head width (max |x| * 2 over the head
slice), the lip ring (outer) width/height and the mouth centre. Args: <blend>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; me = b.data
pa = me.attributes['piece']
faces = [p for p in me.polygons if pa.data[p.index].value == 0]
verts = [v.co.copy() for v in me.vertices]
tree = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in faces])
P = np.array([tuple(v) for v in verts])
used = sorted({i for p in faces for i in p.vertices}); Q = P[used]
ymin = Q[:, 1].min()
head = Q[Q[:, 1] < ymin + 0.06]
hw = 2 * np.abs(head[:, 0]).max(); zc0 = (head[:, 2].min() + head[:, 2].max()) / 2
fr = Q[Q[:, 1] < ymin + 0.03]
res = 0.00025
xs = np.arange(-0.03, 0.03, res); zs = np.arange(fr[:, 2].min() - 0.002, fr[:, 2].max() + 0.002, res)
D = np.full((len(zs), len(xs)), np.nan)
for i, z in enumerate(zs):
    for j, x in enumerate(xs):
        h = tree.ray_cast(Vector((x, ymin - 0.05, z)), Vector((0, 1, 0)))
        if h[0] is not None:
            D[i, j] = h[0].y
# polar walk from the deepest point: along each ray the lip crest is the first minimum of the depth; the opening's edge
# is the last point inside it still 2 mm deeper than the crest
lips = Q[Q[:, 1] < ymin + 0.006]
cz = float((lips[:, 2].min() + lips[:, 2].max()) / 2)
edge = {}
for ang in np.radians(np.arange(0, 360, 5)):
    r = np.arange(0, 0.03, res)
    px = r * np.cos(ang); pz = cz + r * np.sin(ang)
    i = np.clip(((pz - zs[0]) / res).astype(int), 0, len(zs) - 1); j = np.clip(((px - xs[0]) / res).astype(int), 0, len(xs) - 1)
    d = D[i, j]
    ok = np.nan_to_num(d, nan=1e9)
    k = int(np.argmin(ok[: int(0.028 / res)]))
    crest = ok[k]
    inside = np.nonzero(ok[:k] > crest + 0.002)[0]
    edge[ang] = (r[inside[-1]] if len(inside) else 0.0, r[k])
pts = np.array([(v[0] * np.cos(a_), cz + v[0] * np.sin(a_), v[1] * np.cos(a_), cz + v[1] * np.sin(a_)) for a_, v in edge.items()])
w = pts[:, 0].max() - pts[:, 0].min(); h = pts[:, 1].max() - pts[:, 1].min()
wc = pts[:, 2].max() - pts[:, 2].min(); hc = pts[:, 3].max() - pts[:, 3].min()
rep = {'ymin': float(ymin), 'head_width': float(hw), 'hole_w': float(w), 'hole_h': float(h), 'w_over_head': float(w / hw),
       'h_over_w': float(h / w), 'crest_w': float(wc), 'crest_h': float(hc), 'crest_w_over_head': float(wc / hw),
       'z_axis': float(cz), 'z_hole_centre': float((pts[:, 1].max() + pts[:, 1].min()) / 2), 'depth_max': float(np.nanmax(D) - ymin)}
print('MOUTH ' + json.dumps(rep))
