"""The wrap left a tunnel under the beard: the beard hangs 1-3 cm in front of the throat and the gap opens on both sides of the neck
(a see-through hole in the side view, a dark pit in the viewer). Throat vertices facing forward behind the beard are moved forward
along -y onto the beard's back surface (+4 mm into it), then their ring relaxed, so the gap closes; topology and UVs stay (the
paint belongs to work/uv_v1.blend). Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['part']
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
skinf = [f for f in bm.faces if all(v[pl] == 0 for v in f.verts)]
bvh = BVHTree.FromBMesh(bm)
moved = {}
for it in range(3):
    for v in bm.verts:
        if v[pl] != 0: continue
        p = v.co
        if not (abs(p.x) < 0.11 and 0.88 < p.z < 1.02 and -0.13 < p.y < 0.02): continue
        if v.normal.y > -0.25: continue                       # faces forward: the throat (or the beard's front: no hit behind it)
        hit = bvh.ray_cast(p + Vector((0, -0.002, 0)), Vector((0, -1, 0)), 0.06)
        if hit[0] is None: continue
        loc, nor, idx, dist = hit
        if nor.y < 0.2: continue                              # only a surface facing back (the beard's back)
        tgt = loc + Vector((0, -0.004, 0))
        moved[v.index] = (p.copy(), tgt)
        v.co = tgt
    bm.normal_update(); bvh = BVHTree.FromBMesh(bm)
    print('ROUND', it, len(moved))
ring = {e.other_vert(bm.verts[i]) for i in moved for e in bm.verts[i].link_edges} | {bm.verts[i] for i in moved}
for _ in range(3):
    nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)) for v in ring if v[pl] == 0]
    for v, c in nw: v.co = v.co * 0.6 + c * 0.4
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TUNNEL closed', len(moved), 'max move cm', round(max((b - a).length for a, b in moved.values()) * 100, 2) if moved else 0)
