"""Left (bow) hand orientation per clip in glTF space (+Y up): palm normal against the body's left direction and the
forward direction, thumb direction, forearm elevation. Usage: bow_hand_probe.py <glb> [clip ...]"""
import sys
import numpy as np
from gltf_fk import Gltf
g = Gltf(sys.argv[1]); N = g.names


def frame(clip, t, ov=None):
    P = lambda n: g.world(clip, N[n], t, ov)[:3, 3]
    left = P('B_L_UpperArm') - P('B_R_UpperArm'); left[1] = 0; left /= np.linalg.norm(left)
    fwd = np.cross(left, [0, 1, 0]); fwd = -fwd if np.dot(fwd, P('B_L_Toe0') - P('B_L_Foot')) < 0 else fwd
    h, idx, pky, mid = P('B_L_Hand'), P('B_L_Finger1'), P('B_L_Finger4'), P('B_L_Finger2')
    tip = np.mean([P(n) for n in ('B_L_Finger12', 'B_L_Finger22', 'B_L_Finger32', 'B_L_Finger42')], 0)
    n = np.cross(mid - h, idx - pky); n /= np.linalg.norm(n)
    if np.dot(n, tip - mid) < 0: n = -n
    thumb = P('B_L_Finger0') - P('B_L_Hand'); thumb -= np.dot(thumb, mid - h) / np.dot(mid - h, mid - h) * (mid - h)
    thumb /= np.linalg.norm(thumb)
    fa = P('B_L_Hand') - P('B_L_Forearm'); fa /= np.linalg.norm(fa)
    return dict(palm_out=float(n @ left), palm_fwd=float(n @ fwd), thumb_fwd=float(thumb @ fwd), thumb_out=float(thumb @ left),
                forearm_down=float(-fa[1]), left=left, fwd=fwd, n=n, fa=fa)


if __name__ == '__main__':
    for clip in sys.argv[2:] or list(g.anim):
        d = g.duration(clip); rows = [frame(clip, t) for t in np.linspace(0, d, 13)]
        print(f'{clip:9s}', ' '.join(f"{r['palm_out']:+.2f}/{r['palm_fwd']:+.2f}/{r['forearm_down']:+.2f}" for r in rows),
              ' thumb fwd/out', round(rows[0]['thumb_fwd'], 2), round(rows[0]['thumb_out'], 2))
