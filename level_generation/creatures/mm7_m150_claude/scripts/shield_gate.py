"""Shield clearance gate: per frame of each clip, how far left-arm vertices (upper arm, forearm, hand, fingers weight >
0.5) poke through the heater shield. The shield sits rigidly on B_L_Forearm in the frame export_runtime.py builds
(origin at FOREARM_T of the forearm, +Y toward the hand, +Z laterally out of the back of the forearm at rest); its
back surface is a height map over (X, Y) from work/props.blend 'ShieldMesh' (prop space, 2 cm cells, min Z). A vertex
inside the outline whose Z exceeds the back height pokes through by that difference. Prints the worst depth and
frame per clip. Args: -- <blend> clip [clip ...]"""
import bpy, sys, os
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, clips = a[0], a[1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOREARM_T = float(os.environ.get('FOREARM_T', '0.55'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['ShieldMesh']
S = np.array([tuple(v.co) for v in dst.objects[0].data.vertices])
CELL = 0.02
ix = np.floor(S[:, 0] / CELL).astype(int); iy = np.floor(S[:, 1] / CELL).astype(int)
back = {}
for i, j, z in zip(ix, iy, S[:, 2]):
    back[(i, j)] = min(back.get((i, j), 9.0), z)
F0, F1 = rig.data.bones['B_L_Forearm'].head_local, rig.data.bones['B_L_Hand'].head_local
fy = (F1 - F0).normalized(); fz = Vector((1, 0, 0)); fz = (fz - fy * fz.dot(fy)).normalized(); fx = fy.cross(fz)
M0 = Matrix((fx, fy, fz)).transposed().to_4x4(); M0.translation = F0 + (F1 - F0) * FOREARM_T
FR = rig.data.bones['B_L_Forearm'].matrix_local
names = [g.name for g in body.vertex_groups]
arm = [i for i, n in enumerate(names) if n.startswith('B_L_') and any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger'))]
w = np.array([sum(e.weight for e in v.groups if e.group in arm) for v in me.vertices])
sel = np.where(w > 0.5)[0]


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


worst_all = 0.0
for c in clips:
    act = bpy.data.actions[c]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    worst = (0.0, None, 0)
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
        P = np.array([tuple(body.matrix_world @ m.vertices[i].co) for i in sel]); ev.to_mesh_clear()
        Mf = rig.matrix_world @ rig.pose.bones['B_L_Forearm'].matrix @ FR.inverted() @ M0
        Q = np.array(Mf.inverted()) @ np.column_stack([P, np.ones(len(P))]).T
        Q = Q[:3].T
        d, n = 0.0, 0
        for q in Q:
            b = back.get((int(np.floor(q[0] / CELL)), int(np.floor(q[1] / CELL))))
            if b is not None and q[2] > b:
                n += 1; d = max(d, q[2] - b)
        if d > worst[0]:
            worst = (d, f, n)
    worst_all = max(worst_all, worst[0])
    print('SHIELDGATE', c, 'worst poke cm', round(worst[0] * 100, 1), 'frame', worst[1], 'vertices', worst[2])
print('SHIELDGATE max cm', round(worst_all * 100, 1))
