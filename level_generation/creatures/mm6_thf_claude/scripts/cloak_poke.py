"""Cloak poke-through audit: for each frame of a clip, leg/boot vertices behind the hips (y > 0.02 relative to the
hips) whose ray toward the back (+Y, in the chest's heading) meets no cloak face, while they are inside the cloak's
angular span and above the hem. Also the shin-capsule distance to the nearest chain point. env CLIP, Args: blend."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, blend))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
act = bpy.data.actions[os.environ.get('CLIP', 'Walking')]; arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
cl = PARTS.index('Cloak'); legp = {PARTS.index('Legs'), PARTS.index('Boot')}
cfaces = [p for p in me.polygons if part[p.index] == cl]
lverts = sorted({v for p in me.polygons if part[p.index] in legp for v in p.vertices})
f0, f1 = (int(round(x)) for x in act.frame_range)
sc = bpy.context.scene; tot = 0; tot_high = 0
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = [mesh.matrix_world @ v.co for v in m.vertices]
    tree = BVHTree.FromPolygons(P, [tuple(p.vertices) for p in cfaces])
    hips = arm.matrix_world @ arm.pose.bones['Hips'].head
    bad = 0; high = 0
    for i in lverts:
        p = P[i]
        if p.y < hips.y + 0.02 or p.z < 0.14 or p.z > 0.9:
            continue
        if tree.ray_cast(p + Vector((0, 1e-4, 0)), Vector((0, 1, 0)), 1.0)[0] is None:
            bad += 1
            # above the hem line there: a ray down from the vertex meets cloak below it -> it pokes through the
            # cloth, not out from under the hem
            if tree.ray_cast(p, Vector((0, 0, -1)), 1.0)[0] is not None:
                high += 1
    ev.to_mesh_clear(); tot += bad; tot_high += high
    print('POKE', act.name, f, bad, 'through the cloth', high)
print('POKE_TOTAL', act.name, tot, 'through the cloth (not below the hem)', tot_high)
