"""Clip measures for the binding (work/anim_v1.blend):
- stride: Walking / Running are in place; the planted (lowest) sole slides back at the walking speed. stride = mean
  backward speed of the planted ankle over the frames it is down x cycle length (one full cycle);
- impact: the Attack's blow lands when both hands' centre reaches 95 % of its drop from the wind-up's highest point
  to its lowest after it (the claws slam down at the party);
- standing height: the top of the dome over Standing (model metres), its median and range;
- the gem socket's height in Standing frame 0.
Writes work/measure.json."""
import bpy, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']; sc = bpy.context.scene
gi = {g.index: g.name for g in mesh.vertex_groups}
VB = np.array([gi[v.groups[0].group] for v in mesh.data.vertices]); V0 = np.array([v.co[:] for v in mesh.data.vertices])
RINV = {b: np.array(rig.data.bones[b].matrix_local.inverted()) for b in set(VB)}


def use(name):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    return [int(round(x)) for x in act.frame_range]


def pts(b):
    m = np.array(rig.pose.bones[b].matrix) @ RINV[b]; P = V0[VB == b]
    return P @ m[:3, :3].T + m[:3, 3]


out = {}
for clip in ('Walking', 'Running'):
    f0, f1 = use(clip); n = f1 - f0
    ank = {s: [] for s in 'LR'}; low = {s: [] for s in 'LR'}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for s in 'LR':
            ank[s].append(np.array(rig.pose.bones[f'B_{s}_Foot'].head)); low[s].append(pts(f'B_{s}_Foot')[:, 2].min())
    speeds = []
    for f in range(n):
        s = 'L' if low['L'][f] < low['R'][f] else 'R'
        if min(low['L'][f], low['R'][f]) < 0.02:
            speeds.append((ank[s][f + 1][1] - ank[s][f][1]) * 30)    # +Y is backward
    v = float(np.mean(speeds)) if speeds else 0.0
    out[clip] = {'seconds': n / 30, 'planted_speed_mps': round(v, 3), 'stride_m': round(v * n / 30, 3),
                 'planted_frames': len(speeds)}
f0, f1 = use('Attack')
hz = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    c = (pts('B_L_Hand').mean(0) + pts('B_R_Hand').mean(0)) / 2; hz.append(c)
hz = np.array(hz); z = hz[:, 2]
top = int(z.argmax()); bot = top + int(z[top:].argmin())
thr = z[top] - 0.95 * (z[top] - z[bot])
hit = next(f for f in range(top, bot + 1) if z[f] <= thr)
out['Attack'] = {'seconds': (f1 - f0) / 30, 'windup_top_s': round(top / 30, 3), 'lowest_s': round(bot / 30, 3),
                 'impact_s': round(hit / 30, 3), 'hands_drop_m': round(float(z[top] - z[bot]), 3),
                 'hands_forward_at_impact_m': round(float(-hz[hit, 1]), 3)}
f0, f1 = use('Standing')
tops = []
for f in range(f0, f1 + 1):
    sc.frame_set(f); tops.append(max(pts(b)[:, 2].max() for b in set(VB)))
sc.frame_set(f0)
g = rig.matrix_world @ rig.pose.bones['Socket_Gem'].head
out['Standing'] = {'top_m_median': round(float(np.median(tops)), 4), 'top_m_range': [round(min(tops), 4), round(max(tops), 4)],
                   'gem_socket': [round(x, 3) for x in g]}
json.dump(out, open(os.path.join(HERE, 'work', 'measure.json'), 'w'), indent=1)
print('MEASURE', json.dumps(out))
