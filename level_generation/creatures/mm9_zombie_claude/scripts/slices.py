import numpy as np
d = np.load('review/raw/fit_cmp.npz'); P = d['P']
print('ARMS: x | n | cy cz | wy wz')
for s in (1, -1):
    m = (s * P[:, 0] > 0.16) & (P[:, 2] > 0.2)
    Q = P[m]
    for x in np.arange(0.16, 0.72, 0.03):
        q = Q[np.abs(s * Q[:, 0] - x) < 0.0125]
        if len(q) < 3: continue
        print(s, round(x, 2), len(q), np.round(0.5 * (q[:, 1].min() + q[:, 1].max()), 3), np.round(0.5 * (q[:, 2].min() + q[:, 2].max()), 3), np.round(np.ptp(q[:, 1]), 3), np.round(np.ptp(q[:, 2]), 3))
print('LEGS: z | n | cx cy | wx wy')
for s in (1, -1):
    Q = P[(s * P[:, 0] > 0.0) & (P[:, 2] < 0.22)]
    for z in np.arange(0.2, -0.76, -0.05):
        q = Q[np.abs(Q[:, 2] - z) < 0.012]
        if len(q) < 3: continue
        print(s, round(z, 2), len(q), np.round(0.5 * (q[:, 0].min() + q[:, 0].max()), 3), np.round(0.5 * (q[:, 1].min() + q[:, 1].max()), 3), np.round(np.ptp(q[:, 0]), 3), np.round(np.ptp(q[:, 1]), 3))
