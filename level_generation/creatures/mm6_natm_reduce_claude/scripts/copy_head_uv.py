"""Keep the accepted head texture set: the head faces of a head-protected reduction (decimate_tex.py with
REA_PROTECT_ZMIN) are the installed head's own faces, so their HeadUV is copied from the installed master
(../mm6_natm_claude/work/rig_v6.blend, the UVs Meshy's head_retexture_v1 painted) by exact corner position.
Run after export_uploads.py (which gave the head faces a fresh Smart UV Project). Fails if any head face of either
mesh has no exact partner. Rewrites work/rig_v5h.blend."""
import bpy, os
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm6_natm_claude', 'work', 'rig_v6.blend'))
me = bpy.data.objects['Body'].data; uv = me.uv_layers['HeadUV'].data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
# per installed head face (quads in the master, triangles in the reduction): corner position -> UV, and a BVH to
# find the face that contains each reduced triangle
from mathutils.bvhtree import BVHTree
faces = [p for p in me.polygons if hd[p.index]]
src = [[(me.vertices[me.loops[li].vertex_index].co.copy(), tuple(uv[li].uv)) for li in p.loop_indices] for p in faces]
bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [list(p.vertices) for p in faces])
n_src = sum(len(p.vertices) - 2 for p in faces)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5h.blend'))
me = bpy.data.objects['Body'].data; uv = me.uv_layers['HeadUV'].data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
miss = 0; worst = 0.0
for p in me.polygons:
    if not hd[p.index]:
        continue
    loc, _, i, dist = bvh.find_nearest(p.center)
    # corners by distance (the reduction's source went through the glTF export: float noise ~1e-7)
    best = [min(src[i], key=lambda e: (e[0] - me.vertices[me.loops[li].vertex_index].co).length) for li in p.loop_indices]
    err = max((b[0] - me.vertices[me.loops[li].vertex_index].co).length for b, li in zip(best, p.loop_indices))
    worst = max(worst, err)
    if dist > 1e-4 or err > 1e-4:
        miss += 1; continue
    for li, b in zip(p.loop_indices, best):
        uv[li].uv = b[1]
print('HEADUV copied', int(hd.sum()) - miss, 'of', int(hd.sum()), 'head triangles; installed head triangles', n_src, 'missing', miss, 'worst corner mm', round(worst * 1000, 4))
assert miss == 0 and int(hd.sum()) == n_src, 'head faces differ from the installed head set'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5h.blend'))
