"""Per-vertex weight sums of bone groups (work/source.blend Body) -> work/weights.npz: head (B_Head, B_Neck, B_Jaw, eyes),
hand_L/hand_R (B_*_Hand and its fingers), finger (the fingers alone), tip (distal finger bones), toe, foot (B_*_Foot, B_*_Toe*), plus the dominant bone per vertex."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data
names = [g.name for g in src.vertex_groups]
print('GROUPS', names)
sel = {'head': ('B_Head', 'B_Jaw', 'Socket_Eye'), 'hand_L': ('B_L_Hand', 'B_L_Finger'), 'hand_R': ('B_R_Hand', 'B_R_Finger'),
       'foot': ('B_L_Foot', 'B_R_Foot', 'B_L_Toe', 'B_R_Toe'), 'finger': ('B_L_Finger', 'B_R_Finger')}
out = {k: np.zeros(len(me.vertices)) for k in list(sel) + ['tip', 'toe']}
dom = np.zeros(len(me.vertices), np.int32)
for v in me.vertices:
    best = (0, -1)
    for g in v.groups:
        n = names[g.group]
        for k, pre in sel.items():
            if n.startswith(pre):
                out[k][v.index] += g.weight
        if n.startswith(('B_L_Toe', 'B_R_Toe')):
            out['toe'][v.index] += g.weight
        if n.startswith(('B_L_Finger', 'B_R_Finger')) and (n.endswith('2') or n.endswith('.002')):
            out['tip'][v.index] += g.weight
        best = max(best, (g.weight, g.group))
    dom[v.index] = best[1]
np.savez(os.path.join(HERE, 'work', 'weights.npz'), names=np.array(names), dominant=dom, **out)
