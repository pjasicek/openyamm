#!/usr/bin/env python3
"""Dump one of a model's own GLB clips as a library-style source loop (the npz of extract_source.py: canonical joint
names, world matrices per frame in glTF axes, toe ends, rest), so the composer can take the legs' rhythm from the
model's accepted motion (h08 did the same for the Troglodyte's Mutant Run through its FBX).

    glb_source.py <model.glb> <clip> <out.npz> [fps=30]

The toe end is the toe joint plus 0.6 x the ankle-to-toe vector (only facing and floor use it).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

glb_path, clip, out = sys.argv[1:4]
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
SET = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck',
       'B_Head': 'Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    SET.update({f'B_{s}_Thigh': f'{side}UpLeg', f'B_{s}_Calf': f'{side}Leg', f'B_{s}_Foot': f'{side}Foot',
                f'B_{s}_Toe0': f'{side}ToeBase', f'B_{s}_Clavicle': f'{side}Shoulder',
                f'B_{s}_UpperArm': f'{side}Arm', f'B_{s}_Forearm': f'{side}ForeArm', f'B_{s}_Hand': f'{side}Hand'})
glb = open_glb(glb_path)
model = glb_pose.Model(glb)
idx = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
ours = list(SET)
T = model.clip_times(clip)[-1]
n = int(round(T * fps))
times = np.arange(n + 1) / n * T
times[-1] = 0.0                       # the loop's last frame is its first
mats = np.zeros((n + 1, len(ours), 4, 4))
tails = np.zeros((n + 1, 2, 3))
for i, t in enumerate(times):
    W = model.world(model.sample(clip, float(t)))
    for j, name in enumerate(ours):
        mats[i, j] = W[idx[name]]
    for k, s in enumerate('LR'):
        foot, toe = W[idx[f'B_{s}_Foot'], :3, 3], W[idx[f'B_{s}_Toe0'], :3, 3]
        tails[i, k] = toe + 0.6 * (toe - foot)
W0 = model.world(model.sample('Standing', 0.0))
rest = np.stack([W0[idx[name]] for name in ours])
rest_tails = np.stack([W0[idx[f'B_{s}_Toe0'], :3, 3] + 0.6 * (W0[idx[f'B_{s}_Toe0'], :3, 3]
                                                                - W0[idx[f'B_{s}_Foot'], :3, 3]) for s in 'LR'])
np.savez(out, names=np.array([SET[n] for n in ours]), mats=mats, toe_tails=tails, fps=fps,
         frames=np.arange(n + 1), rest=rest, rest_toe_tails=rest_tails, source=f'{Path(glb_path).name}:{clip}')
print(f'GLB SOURCE {clip}: {n + 1} frames at {fps:g} fps -> {out}')
