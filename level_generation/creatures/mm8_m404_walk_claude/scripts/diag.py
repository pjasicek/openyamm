"""Numeric gait diagnosis of a sampled Walking clip (from sample_clips.py)."""
import sys, numpy as np, json
from scipy.spatial.transform import Rotation as Rot
d = np.load(sys.argv[1]); clip = sys.argv[2] if len(sys.argv) > 2 else 'Walking'
names = list(d['names']); W = d[clip + '_world']; S = d['Standing_world'][0]; lows = d[clip + '_lows']; T = float(d[clip + '_duration'])
ix = {n: i for i, n in enumerate(names)}
def pos(b): return W[:, ix[b], :3, 3]
def rel_angles(b):
    # world rotation relative to the standing frame-0 world rotation, as yaw (Z), pitch (X), roll (Y) degrees
    R0 = S[ix[b], :3, :3]; out = []
    for M in W[:, ix[b], :3, :3]:
        out.append(Rot.from_matrix(M @ R0.T).as_euler('ZXY', degrees=True))
    return np.array(out)
rng = lambda a: float(a.max() - a.min())
rep = {'duration_s': T}
p = pos('B_Pelvis'); rep['pelvis_range_xyz_cm'] = [round(rng(p[:, k]) * 100, 2) for k in range(3)]
for b in ('B_Pelvis', 'B_Spine2', 'B_Neck', 'B_Head', 'B_L_Clavicle', 'B_R_Clavicle', 'B_R_Hand', 'Tail3', 'Tail6'):
    a = rel_angles(b); rep[b + '_rot_range_yaw_pitch_roll_deg'] = [round(rng(a[:, k]), 1) for k in range(3)]
for s in 'LR':
    f = pos(f'B_{s}_Foot'); h = pos(f'B_{s}_Thigh')
    rel = f - h
    rep[f'{s}_foot_fwd_range_cm'] = round(rng(rel[:, 1]) * 100, 1)
    rep[f'{s}_foot_lift_max_cm'] = round(float((lows[:, 'LR'.index(s)] - lows[:, 'LR'.index(s)].min()).max()) * 100, 1)
    a = rel_angles(f'B_{s}_Foot'); rep[f'{s}_foot_pitch_range_deg'] = round(rng(a[:, 1]), 1)
hand = pos('B_R_Hand'); rep['R_hand_range_xyz_cm'] = [round(rng(hand[:, k]) * 100, 1) for k in range(3)]
tail = pos('Tail6'); rep['tail_tip_range_xyz_cm'] = [round(rng(tail[:, k]) * 100, 1) for k in range(3)]
rep['lowest_body_mm'] = round(float(lows[:, 2].min()) * 1000, 1)
hip = pos('B_L_Thigh')[0]; ank = pos('B_L_Foot')[0]
print(json.dumps(rep, indent=1))
