"""Compare the clips of two GLBs channel by channel (by node name): max rotation angle (deg) and max translation
difference (mm) per animation, sampled at the reference's key times. Usage: compare_clips.py <reference glb> <other glb>"""
import sys
import numpy as np
from glbio import read, clips
A = clips(*read(sys.argv[1])); B = clips(*read(sys.argv[2]))
for name in sorted(A):
    if name not in B:
        print(f'{name}: missing in other'); continue
    worst_r, worst_t, wr, n_missing = 0.0, 0.0, '', 0
    for key, (ta, va) in A[name].items():
        if key not in B[name]:
            n_missing += 1; continue
        tb, vb = B[name][key]
        vbi = np.stack([np.interp(ta, tb, vb[:, k]) for k in range(vb.shape[1])], 1)
        if key[1] == 'rotation':
            qa = va / np.linalg.norm(va, axis=1, keepdims=True); qb = vbi / np.linalg.norm(vbi, axis=1, keepdims=True)
            d = np.degrees(2 * np.arccos(np.clip(np.abs((qa * qb).sum(1)), 0, 1))).max()
            if d > worst_r:
                worst_r, wr = d, key[0]
        elif key[1] == 'translation':
            worst_t = max(worst_t, np.abs(va - vbi).max() * 1000)
    durs = (max(t[-1] for t, _ in A[name].values()), max(t[-1] for t, _ in B[name].values()))
    print(f'{name}: max rot {worst_r:.2f} deg ({wr}), max transl {worst_t:.2f} mm, duration {durs[0]:.3f} / {durs[1]:.3f} s,'
          f' channels missing {n_missing}')
