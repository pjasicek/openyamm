"""Where is the fist's real hole: circle fit to each finger's chain in the plane across the knuckle line, free radius there."""
import json, numpy as np
J = json.load(open('work/hands_v1.json'))['joints']['R']; Z = np.load('work/faces.npz')
P = np.unique(Z['bc'].reshape(-1, 3), axis=0); W = np.array(J['wrist'])
H = P[np.linalg.norm(P - (W + [-.05, -.1, -.15]), axis=1) < .24]
I, Pk = np.array(J['finger2-1']), np.array(J['finger5-1']); kn = (I - Pk) / np.linalg.norm(I - Pk)
mid = (I + Pk) / 2; e1 = np.cross(kn, np.array(J['finger3-1']) - W); e1 /= np.linalg.norm(e1); e2 = np.cross(kn, e1)
print('W', W.round(3), 'kn', kn.round(3), 'I', I.round(3), 'Pk', Pk.round(3))
q = lambda p: np.array([(p - mid) @ e1, (p - mid) @ e2])
C = []
for k, n in ((2, 'I'), (3, 'M'), (4, 'R'), (5, 'P')):
    pts = np.array([q(np.array(J[f'finger{k}-{j}'])) for j in (1, 2, 3)] + [q(np.array(J[f'finger{k}-3_tip']))])
    A = np.c_[2 * pts, np.ones(4)]; b = (pts ** 2).sum(1); s = np.linalg.lstsq(A, b, rcond=None)[0]; r = np.sqrt(s[2] + s[:2] @ s[:2]); C.append(s[:2])
    print(n, 'chain', pts.round(3).tolist(), 'centre', s[:2].round(3), 'r', round(float(r), 3))
c = np.mean(C, 0); G = mid + e1 * c[0] + e2 * c[1]
Q = np.c_[(H - mid) @ e1, (H - mid) @ e2]; ax = (H - mid) @ kn; m = np.abs(ax) < .07
best = (0, None)
for u in np.arange(c[0] - .05, c[0] + .05, .002):
    for v in np.arange(c[1] - .05, c[1] + .05, .002):
        d = np.hypot(Q[m, 0] - u, Q[m, 1] - v).min()
        if d > best[0]: best = (d, (u, v))
print('fit centre', G.round(3), 'free r at fit', round(float(np.hypot(*(Q[m] - c).T).min()), 4), 'best r', round(best[0], 4), 'at', np.round(mid + e1 * best[1][0] + e2 * best[1][1], 3), 'old G', json.load(open('scripts/grip.json'))['G'], 'hand verts', len(H))
