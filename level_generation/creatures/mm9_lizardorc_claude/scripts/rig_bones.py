"""Rig tables, glTF frame. Names are MM9's. MM9's joints (bind symmetric, mesh fitted onto them), hands ours: Finger1-3 chains of 3 bones, thumb Finger0, 01, 02; jaw hinge and tongue ours."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import mm9_joints
C = ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head']
TAIL = ['Box03', 'Box04', 'Box05']
TONGUE = ['Bone02', 'Bone03', 'Bone04', 'Bone05']
FN = ['Finger1', 'Finger2', 'Finger3', 'Finger0']
def fk(f, k): return f'{f}{k}' if k else f          # Finger1, Finger11, Finger12
X = np.array([-1, 1, 1.])
def joints():
    W, par, _ = mm9_joints.rest()
    P = {n: W[n][:3, 3].copy() for n in W}
    Q = {n: v.copy() for n, v in P.items()}
    fg = json.load(open(HERE / 'work/fingers.json'))
    for f in FN:
        for k in range(3):
            Q[f'Bip01 L {fk(f, k)}'] = np.array(fg[f][k], float); Q[f'Bip01 R {fk(f, k)}'] = np.array(fg[f][k], float) * X
    tips = {f: np.array(fg[f][3], float) for f in FN}
    # hinge pivots toward the outside of the bend
    def out(a, b, c): d = (b - a) / np.linalg.norm(b - a) + (b - c) / np.linalg.norm(b - c); return d / np.linalg.norm(d)
    for s, m in (('L', 1), ('R', 1)):
        p = f'Bip01 {s} '
    import headfr as H
    Q['Box01'] = H.HINGE.copy(); hb = np.load(HERE / 'work/head1.npz')['tongue']
    for n, p in zip(TONGUE, hb): Q[n] = p.copy()
    hp = HERE / 'work/hand_poses.json'
    if hp.exists(): Q['Bone07'] = np.array(json.load(open(hp))['G'], float)
    return Q, tips
def table():
    P, tips = joints(); T = {}
    for a, b in zip(C, C[1:]): T[a] = (None if a == C[0] else C[C.index(a) - 1], P[a], P[b])
    T['Bip01 Head'] = ('Bip01 Neck', P['Bip01 Head'], P['Bip01 Head'] + np.array([0, .05, .3]))
    tt = [P[n] for n in TAIL] + [np.array([0, -.30, -.62])]
    for i, a in enumerate(TAIL): T[a] = ('Bip01 Pelvis' if i == 0 else TAIL[i - 1], tt[i], tt[i + 1])
    for s, m in (('L', np.array([1, 1, 1.])), ('R', X)):
        pre = f'Bip01 {s} '
        T[pre + 'Clavicle'] = ('Bip01 Neck', P[pre + 'Clavicle'], P[pre + 'UpperArm'])
        T[pre + 'UpperArm'] = (pre + 'Clavicle', P[pre + 'UpperArm'], P[pre + 'Forearm'])
        T[pre + 'Forearm'] = (pre + 'UpperArm', P[pre + 'Forearm'], P[pre + 'Hand'])
        T[pre + 'Hand'] = (pre + 'Forearm', P[pre + 'Hand'], P[pre + 'Finger2'])
        T[pre + 'Thigh'] = ('Bip01 Spine', P[pre + 'Thigh'], P[pre + 'Calf'])
        T[pre + 'Calf'] = (pre + 'Thigh', P[pre + 'Calf'], P[pre + 'Foot'])
        T[pre + 'Foot'] = (pre + 'Calf', P[pre + 'Foot'], P[pre + 'Foot'] + np.array([0, -.1, .2]))
        for f in FN:
            for k in range(3):
                n = pre + fk(f, k); nx = P[pre + fk(f, k + 1)] if k < 2 else tips[f] * m
                T[n] = (pre + 'Hand' if k == 0 else pre + fk(f, k - 1), P[n], nx)
    return T
def half_pairs():
    """(helper, child bone, helper's node parent, parent-side weight bones)"""
    out = []
    for s in 'LR':
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine3', 'Bip01 Spine2', 'Bip01 Neck')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
        out.append((pre + 'XhalfThigh', pre + 'Thigh', 'Bip01 Spine', ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1')))
        out.append((pre + 'XhalfCalf', pre + 'Calf', pre + 'Thigh', (pre + 'Thigh',)))
    out.append(('XhalfJaw', 'Box01', 'Bip01 Head', ('Bip01 Head',)))
    import os
    if os.environ.get('NECKHALF', '0') == '1':      # run 2: the neck band folded in Death and Hit2 (head 104, torso 56 faces, all neck): half rotations at both neck joints
        out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck', 'Bip01 Spine3')))     # the band runs Spine3 -> Head (Neck ~0); MM9 bends only at Head (32 deg Standing, 85 Death)
    out.append(('XhalfBox03', 'Box03', 'Bip01 Pelvis', ('Bip01 Pelvis', 'Bip01 Spine')))
    out.append(('XhalfBox04', 'Box04', 'Box03', ('Box03',)))
    return out
if __name__ == '__main__':
    for k, v in table().items(): print(k, v[0], np.round(v[1], 3).tolist(), np.round(v[2], 3).tolist())
