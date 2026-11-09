import json, numpy as np
Z = np.load('work/faces.npz'); B = Z['bc']; U = Z['bu']
J = json.load(open('work/hands_v1.json')); 
for S, sg in (('R', -1), ('L', 1)):
    Fr = J['frames'][S]; W = np.array(Fr['W']); d = np.array(Fr['d']); d /= np.linalg.norm(d)
    c = B.mean(1); al = (c - W) @ d; rad = np.linalg.norm(c - W - np.outer(al, d), axis=1)
    m = (np.sign(c[:, 0]) == sg) & (rad < .16)
    n = np.cross(B[:, 1] - B[:, 0], B[:, 2] - B[:, 0]); A = np.linalg.norm(n, axis=1) / 2; n /= np.maximum(2 * A, 1e-12)[:, None]
    out = c - W - np.outer(al, d); inward = ((n * out).sum(1) < 0)
    for a0, a1 in ((-.06, -.03), (-.03, -.0), (0, .012), (.012, .03), (.03, .05), (.05, .08)):
        k = m & (al >= a0) & (al < a1)
        e, f = U[k, 1] - U[k, 0], U[k, 2] - U[k, 0]; ua = np.abs(e[:, 0] * f[:, 1] - e[:, 1] * f[:, 0]) / 2 * 2048 ** 2
        print(S, a0, a1, 'faces', int(k.sum()), 'inward', int((inward & k).sum()), 'r med', round(float(np.median(rad[k])), 3) if k.any() else 0, 'r max', round(float(rad[k].max()), 3) if k.any() else 0, 'area cm2', round(float(A[k].sum() * 1e4), 1), 'texels', int(ua.sum()))
