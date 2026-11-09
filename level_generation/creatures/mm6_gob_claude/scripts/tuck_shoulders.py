"""Keep shoulder skin well under the pauldrons/gorget so raised arms cannot push it through the plates.
Rest pose, Body vertices within 0.24 m of a shoulder joint: if the armour lies along the outward normal within 4 cm
(or just behind, skin already poking out) the vertex moves to GAP under the armour. Hidden skin only; topology,
UVs and weights are unchanged."""
import bpy, json, numpy as np
from mathutils.bvhtree import BVHTree
GAP = 0.018
m = bpy.data.objects['Peasant']; me = m.data
rig = bpy.data.objects['Peasant_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
heads = [rig.matrix_world @ rig.data.bones[f'mixamorig:{s}Arm'].head_local for s in ('Left', 'Right')]
inv = m.matrix_world.inverted()
heads = [inv @ h for h in heads]
moved = set()
for _ in range(3):
    me.update()
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices],
                                [tuple(p.vertices) for p in me.polygons if part[p.index] == PARTS.index('Armor')])
    for vi in {vi for p in me.polygons if part[p.index] == PARTS.index('Body') for vi in p.vertices}:
        v = me.vertices[vi]
        if min((v.co - h).length for h in heads) > 0.24:
            continue
        n = v.normal.copy()
        out = tree.ray_cast(v.co + n * 1e-5, n, 0.04)
        inn = tree.ray_cast(v.co - n * 1e-5, -n, 0.02)
        if out[0] is not None and out[3] < GAP:
            v.co = out[0] - n * GAP; moved.add(vi)
        elif out[0] is None and inn[0] is not None:
            v.co = inn[0] - n * GAP; moved.add(vi)
print('TUCKED shoulders', len(moved))
bpy.ops.wm.save_mainfile()
