"""Probe the Cast clip's left arm: per time, the local rotation angle of each arm joint vs Standing frame 0, the hand
position in the chest frame and the elbow angle."""
import sys, numpy as np
sys.path.insert(0, 'level_generation/creatures/claude_shared/floor')
import glb_pose as gp
g = gp.Glb(sys.argv[1]); m = gp.Model(g); clip = sys.argv[2] if len(sys.argv) > 2 else 'Cast'
side = sys.argv[3] if len(sys.argv) > 3 else 'Left'
names = [n.get('name') for n in g.json['nodes']]
J = {n: names.index(n) for n in ['Spine', 'Spine01', 'Spine02', f'{side}Shoulder', f'{side}Arm', f'{side}ForeArm', f'{side}Hand']}
st = m.sample('Standing', 0.0)
def ang(q1, q2):
    d = abs(float(np.dot(q1 / np.linalg.norm(q1), q2 / np.linalg.norm(q2)))); return np.degrees(2 * np.arccos(min(1, d)))
times = m.clip_times(clip)
for t in np.arange(0, times[-1] + 1e-6, 0.1):
    loc = m.sample(clip, t); w = m.world(loc)
    chest = w[J['Spine']]
    inv = np.linalg.inv(chest)
    hand = (inv @ w[J[f'{side}Hand']][:, 3])[:3]
    sh, el, wr = w[J[f'{side}Arm']][:3, 3], w[J[f'{side}ForeArm']][:3, 3], w[J[f'{side}Hand']][:3, 3]
    elbow = np.degrees(np.arccos(np.clip(np.dot((sh - el) / np.linalg.norm(sh - el), (wr - el) / np.linalg.norm(wr - el)), -1, 1)))
    row = [f'{t:4.2f}'] + [f"{k[len(side):] if k.startswith(side) else k}:{ang(loc.get(J[k], m.rest[J[k]])[1], st.get(J[k], m.rest[J[k]])[1]):5.1f}" for k in J]
    print(' '.join(row), 'hand_chest', np.round(hand, 3), f'elbow {elbow:5.1f}')
