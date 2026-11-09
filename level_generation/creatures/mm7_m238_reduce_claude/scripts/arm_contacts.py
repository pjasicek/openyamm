"""G6-style contact check on a gate copy (gate_import.py blend): per clip and every 2nd frame, how deep the forearm and
hand vertices (weight > 0.5) of each arm go into the trunk (faces of the largest piece without weight on either arm;
the folded forearms touch each other by design, so the other arm is excluded too). Inside = behind the closest trunk
face within a 45 deg cone of its normal, within 5 cm (the shell is open, so a ray parity test is not usable). Args: -- <blend> clip [clip ...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
names = [g.name for g in body.vertex_groups]


def w(keys, side=None):
    idx = [i for i, n in enumerate(names) if any(k in n for k in keys) and (side is None or n.startswith(f'B_{side}_'))]
    return np.array([sum(e.weight for e in v.groups if e.group in idx) for v in me.vertices])


arm_any = w(('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))
trunk_faces = [tuple(p.vertices) for p in me.polygons if pv[p.vertices[0]] == 0 and all(arm_any[i] < 0.05 for i in p.vertices)]
probe = {s: np.where(w(('Forearm', 'Hand', 'Finger'), s) > 0.5)[0] for s in 'LR'}


def depth(tree, p):
    loc, nrm, idx, d = tree.find_nearest(p, 0.05)
    if loc is not None and (p - loc).dot(nrm) < -0.7 * d:
        return d
    return 0.0


for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = {s: (0.0, None) for s in 'LR'}
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        bpy.context.scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = [body.matrix_world @ v.co for v in m.vertices]; ev.to_mesh_clear()
        tree = BVHTree.FromPolygons(P, trunk_faces)
        for s in 'LR':
            for i in probe[s][::2]:
                d = depth(tree, P[i])
                if d > worst[s][0]:
                    worst[s] = (d, f)
    print('ARMCONTACT', c, {s: (round(v[0] * 100, 1), v[1]) for s, v in worst.items()}, '(cm, frame)')
