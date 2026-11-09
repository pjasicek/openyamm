"""Per-vertex weight sums by bone family of the welded rest source (work/source.blend, same vertex order as
dump_mesh.py) -> work/vweights.npz: arm_l/arm_r (UpperArm, Forearm, Hand, Finger), hand_l/hand_r (Hand, Finger),
dress (B_Pelvis and Dress_* chains), leg (Thigh, Calf, Foot, Toe), head (B_Head, B_Neck). Usage: blender -b -P dump_vweights.py"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; names = {g.index: g.name for g in o.vertex_groups}
fam = {'arm_l': lambda n: n.startswith('B_L_') and any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger')),
       'arm_r': lambda n: n.startswith('B_R_') and any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger')),
       'hand_l': lambda n: n.startswith('B_L_') and any(k in n for k in ('Hand', 'Finger')),
       'hand_r': lambda n: n.startswith('B_R_') and any(k in n for k in ('Hand', 'Finger')),
       'dress': lambda n: n == 'B_Pelvis' or n.startswith('Dress_'),
       'leg': lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')),
       'head': lambda n: n in ('B_Head', 'B_Neck')}
out = {k: np.zeros(len(me.vertices)) for k in fam}
for v in me.vertices:
    for g in v.groups:
        n = names[g.group]
        for k, f in fam.items():
            if f(n):
                out[k][v.index] += g.weight
np.savez(os.path.join(HERE, 'work', 'vweights.npz'), **out)
print('VWEIGHTS', {k: int((w > .5).sum()) for k, w in out.items()})
