#!/usr/bin/env python3
"""The staff stays above the floor in the falls (Giant die1/die2 retargeted: the right hand goes down with the staff rigid in it, and
its foot would pierce the floor by up to 1.25 m). Per key of the named clips the staff turns about its grip (the fist's hole, on the
shaft axis) about the horizontal axis across it by the least angle that keeps both its ends at least CLEAR above the floor: it tips
toward lying flat on the floor beside the body. The angle is low-passed (Gaussian, SIGMA keys) and only ever grows the clearance;
Ystaff's local rotation and translation keys take the turn, so the fist and the staff stay together at the grip.
Args: <in glb> <out glb> <clip> [clip ...]"""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix
IN, OUT = sys.argv[1:3]; CLIPS = sys.argv[3:]
CLEAR, SIGMA = 0.0, 2.0
m = Model(Glb(IN)); doc = m.glb.json
names = [n.get('name') for n in doc['nodes']]; S = names.index('Ystaff'); H = names.index('Bip01 R Hand')
jn = [names[j] for j in m.joints]
# the staff's own vertices in Ystaff's local frame (bind)
pr = m.primitives[0]; Vs = []
for pr in m.primitives:
    if not pr['skinned']: continue
    d = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
    Vs.append(pr['positions'][d == 'Ystaff'])
Vs = np.vstack(Vs)
ibm = m.inverse_binds[jn.index('Ystaff')]
L = (ibm @ np.c_[Vs, np.ones(len(Vs))].T).T[:, :3]           # Ystaff local
c_l = L.mean(0); ax_l = np.linalg.svd(L - c_l)[2][0]            # the shaft: the staff's long axis in the exported node frame
pr_ = (L - c_l) @ ax_l
ends_l = np.array([L[pr_.argmin()], L[pr_.argmax()]])
def rotm(axis, a):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
for clip in CLIPS:
    an = doc['animations'][m.clips[clip]]
    ch = {(c['target']['node'], c['target']['path']): c for c in an['channels']}
    rs = an['samplers'][ch[(S, 'rotation')]['sampler']]; ts_ = an['samplers'][ch[(S, 'translation')]['sampler']]
    times = m.glb.accessor(rs['input'])[:, 0]
    assert np.allclose(times, m.glb.accessor(ts_['input'])[:, 0])
    Q = m.glb.accessor(rs['output']).copy(); T = m.glb.accessor(ts_['output']).copy()
    ang = np.zeros(len(times)); axes = np.zeros((len(times), 3)); info = []
    for k, t in enumerate(times):
        W = m.world(m.sample(clip, float(t)))
        Ws = W[S]; R = Ws[:3, :3]
        c_w = R @ c_l + Ws[:3, 3]; a_w = R @ ax_l; G = c_w + a_w * ((W[H][:3, 3] - c_w) @ a_w)      # the grip: the wrist projected on the shaft
        e = (R @ ends_l.T).T + Ws[:3, 3]
        dirn = R @ ax_l; hor = np.cross(dirn, [0, 1.0, 0])
        if np.linalg.norm(hor) < 1e-6: hor = np.array([1.0, 0, 0])
        hor /= np.linalg.norm(hor); axes[k] = hor
        low = e[:, 1].min()
        if low >= CLEAR: continue
        # smallest |a| (either sense) with both ends >= CLEAR after turning about G
        best = None; top = (-1e9, 0.0)
        for a in np.radians(np.r_[np.arange(0, 91, 0.5), -np.arange(0.5, 91, 0.5)]):
            Rr = rotm(hor, a); ee = (Rr @ (e - G).T).T + G
            if ee[:, 1].min() >= CLEAR:
                best = a; break
            if ee[:, 1].min() > top[0]: top = (ee[:, 1].min(), a)
        ang[k] = best if best is not None else top[1]      # the grip itself on the floor: the staff as near flat as it gets
        info.append((round(float(t), 2), round(float(np.degrees(ang[k])), 1), round(float(low), 3)))
    if not ang.any():
        print('STAFFFLOOR', clip, 'clear'); continue
    # low-pass, never below the per-key need (in magnitude, per sign)
    sm = ndimage.gaussian_filter1d(ang, SIGMA, mode='nearest')
    ang = np.where(np.abs(sm) >= np.abs(ang), sm, ang)
    for k, t in enumerate(times):
        if abs(ang[k]) < 1e-6: continue
        W = m.world(m.sample(clip, float(t)))
        Wh = W[H]; Ws = W[S]
        c_w = Ws[:3, :3] @ c_l + Ws[:3, 3]; a_w = Ws[:3, :3] @ ax_l; G = c_w + a_w * ((Wh[:3, 3] - c_w) @ a_w)
        Rr = rotm(axes[k], ang[k])
        Rn = Rr @ Ws[:3, :3]; pn = Rr @ (Ws[:3, 3] - G) + G
        Ln = np.linalg.inv(Wh) @ np.r_[np.c_[Rn, pn], [[0, 0, 0, 1]]]
        Q[k] = matrix_quaternion(Ln[:3, :3]); T[k] = Ln[:3, 3]
    for k in range(1, len(Q)):
        if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
    rs['output'] = m.glb.append_accessor(Q, 'VEC4'); ts_['output'] = m.glb.append_accessor(T, 'VEC3')
    print('STAFFFLOOR', clip, 'keys turned', int((np.abs(ang) > 1e-6).sum()), 'max deg', round(float(np.degrees(np.abs(ang).max())), 1), info[-1] if info else '')
m.glb.write(OUT)
