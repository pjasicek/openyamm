"""Rig tables of the Troglodyte, glTF frame. Names are MM9's (mixed Bip01/Bip02). Deforming bones; positions: fit.json targets on the left, mirrored right, MM9's own for the centre."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import mm9_joints
C = ['Bip01 Pelvis', 'Bip02 Spine', 'Bip01 Spine1', 'Bip02 Spine2', 'Bip02 Spine3', 'Bip02 Neck', 'Bip01 Head']
TAIL = ['Box01', 'Box02', 'Box03', 'Box04']
FN = ['Finger1', 'Finger2', 'Finger3']
def fk(f, k): return f'{f}{k}' if k else f          # Finger1, Finger11, Finger12
def joints():
    """name -> position, every bone the rig has (left and right)"""
    J, W, par = mm9_joints.sym()
    fit = json.load(open(HERE / 'work/fit.json'))['tgt']
    fg = json.load(open(HERE / 'work/fingers.json'))
    P = {n: J[n].copy() for n in C + TAIL + ['Box05', 'Box06']}
    L = {'Clavicle': J['Bip02 L Clavicle'], 'UpperArm': np.array(fit['sh']), 'Forearm': np.array(fit['el']), 'Hand': np.array(fit['wr']), 'Thigh': np.array(fit['hip']), 'Calf': np.array(fit['kn']), 'Foot': np.array(fit['an']), 'Toe0': np.array(fit['ball'])}
    for f in FN:
        for k in range(3): L[fk(f, k)] = np.array(fg[f][k], float)
    X = np.array([-1, 1, 1.])
    # hinge pivots toward the outside of the bend: the skin on the inside compresses less (Mummy, 2026-10-31)
    def out(a, b, c): d = (b - a) / np.linalg.norm(b - a) + (b - c) / np.linalg.norm(b - c); return d / np.linalg.norm(d)
    L['Calf'] = L['Calf'] + out(L['Thigh'], L['Calf'], L['Foot']) * .03
    L['Forearm'] = L['Forearm'] + out(L['UpperArm'], L['Forearm'], L['Hand']) * .012
    for k, v in L.items():
        P[f'Bip02 L {k}'] = v.copy(); P[f'Bip02 R {k}'] = v * X
    tips = {f: np.array(fg[f][3], float) for f in FN}
    return P, tips
def table():
    """name -> (parent, head, tail) for heat weights"""
    P, tips = joints(); T = {}
    for a, b in zip(C, C[1:]): T[a] = (None if a == C[0] else C[C.index(a) - 1], P[a], P[b])
    T['Bip01 Head'] = ('Bip02 Neck', P['Bip01 Head'], P['Bip01 Head'] + np.array([0, -.03, .3]))
    T['Box05'] = ('Bip01 Head', P['Box05'], P['Box06'])
    for a, b in zip(TAIL, TAIL[1:]): T[a] = ('Bip01 Pelvis' if a == TAIL[0] else TAIL[TAIL.index(a) - 1], P[a], P[b])
    X = np.array([-1, 1, 1.])
    for s, m in (('L', np.array([1, 1, 1.])), ('R', X)):
        pre = f'Bip02 {s} '
        T[pre + 'Clavicle'] = ('Bip02 Neck', P[pre + 'Clavicle'], P[pre + 'UpperArm'])
        T[pre + 'UpperArm'] = (pre + 'Clavicle', P[pre + 'UpperArm'], P[pre + 'Forearm'])
        T[pre + 'Forearm'] = (pre + 'UpperArm', P[pre + 'Forearm'], P[pre + 'Hand'])
        T[pre + 'Hand'] = (pre + 'Forearm', P[pre + 'Hand'], P[pre + 'Finger2'])
        T[pre + 'Thigh'] = ('Bip02 Spine', P[pre + 'Thigh'], P[pre + 'Calf'])
        T[pre + 'Calf'] = (pre + 'Thigh', P[pre + 'Calf'], P[pre + 'Foot'])
        T[pre + 'Foot'] = (pre + 'Calf', P[pre + 'Foot'], P[pre + 'Toe0'])
        t = P[pre + 'Toe0']; T[pre + 'Toe0'] = (pre + 'Foot', t, t + (P[pre + 'Toe0'] - P[pre + 'Foot']) * 1.3)
        for f in FN:
            for k in range(3):
                n = pre + fk(f, k); nx = P[pre + fk(f, k + 1)] if k < 2 else tips[f] * m
                T[n] = (pre + 'Hand' if k == 0 else pre + fk(f, k - 1), P[n], nx)
    return T
def half_pairs():
    """(helper, child bone, helper's node parent, parent-side weight bones)"""
    out = []
    for s in 'LR':
        pre = f'Bip02 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip02 Spine3', 'Bip02 Spine2', 'Bip02 Neck')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
        out.append((pre + 'XhalfThigh', pre + 'Thigh', 'Bip02 Spine', ('Bip01 Pelvis', 'Bip02 Spine', 'Bip01 Spine1')))
        out.append((pre + 'XhalfCalf', pre + 'Calf', pre + 'Thigh', (pre + 'Thigh',)))
    out.append(('XhalfJaw', 'Box05', 'Bip01 Head', ('Bip01 Head',)))
    out.append(('XhalfBox01', 'Box01', 'Bip01 Pelvis', ('Bip01 Pelvis', 'Bip02 Spine')))
    out.append(('XhalfBox02', 'Box02', 'Box01', ('Box01',)))
    out.append(('XhalfBox03', 'Box03', 'Box02', ('Box02',)))
    return out
if __name__ == '__main__':
    for k, v in table().items(): print(k, v[0], np.round(v[1], 3).tolist(), np.round(v[2], 3).tolist())
