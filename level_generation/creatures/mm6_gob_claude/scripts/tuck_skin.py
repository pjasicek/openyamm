"""Keep Body skin at least 7 mm under the Tunic (collar/shoulder z-fighting and slight poke-through).
Along each skin vertex normal: tunic just outside (<7 mm) or just inside (<10 mm behind) -> move the vertex to
7 mm under the cloth. Rest pose; topology, UVs and weights unchanged."""
import bpy, json, numpy as np
from mathutils.bvhtree import BVHTree
GAP = 0.010
m = bpy.data.objects['Peasant']; me = m.data
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
moved = set()
for _ in range(3):
    me.update()
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices],
                                [tuple(p.vertices) for p in me.polygons if part[p.index] == PARTS.index('Tunic')])
    for vi in {vi for p in me.polygons if part[p.index] == PARTS.index('Body') for vi in p.vertices}:
        v = me.vertices[vi]
        if not (0.85 < v.co.z < 1.40):
            continue
        n = v.normal.copy()
        out = tree.ray_cast(v.co + n * 1e-5, n, GAP)
        inn = tree.ray_cast(v.co - n * 1e-5, -n, 0.020)
        if out[0] is not None:
            v.co = out[0] - n * GAP; moved.add(vi)
        elif inn[0] is not None:
            v.co = inn[0] - n * GAP; moved.add(vi)
print('TUCKED', len(moved))
bpy.ops.wm.save_mainfile()
