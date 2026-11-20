"""Sleeve and forearm-stub radii along each forearm of a dumped master (dump_mesh.py npz + bones json)."""
import numpy as np, json, sys
d = np.load(sys.argv[1], allow_pickle=True); B = json.load(open(sys.argv[1] + '.bones.json'))
P, L, ls, lt, W, Wi, vg = d['P'], d['L'], d['ls'], d['lt'], d['W'], d['Wi'], d['vg']
fv = [L[ls[i]:ls[i] + lt[i]] for i in range(len(ls))]
hand_v = set(np.concatenate([fv[i] for i in np.where(d['hand'])[0]]).tolist())
head_v = set(np.concatenate([fv[i] for i in np.where(d['head'])[0]]).tolist())
body_v = set(np.concatenate([fv[i] for i in np.where((d['hand'] == 0) & (d['head'] == 0))[0]]).tolist())
for s in 'LR':
    E = np.array(B[f'Bip01 {s} Forearm'][:3]); Wr = np.array(B[f'Bip01 {s} Hand'][:3]); ax = Wr - E; ln = np.linalg.norm(ax); ax /= ln
    names = {f'Bip01 {s} Forearm', f'Bip01 {s} Hand', f'Bip01 {s} UpperArm'}
    arm = np.array([vg[Wi[v, 0]] in names or any(vg[Wi[v, k]].startswith(f'Bip01 {s} ') and ('Finger' in vg[Wi[v, k]] or 'Thumb' in vg[Wi[v, k]]) for k in range(1)) for v in range(len(P))])
    rel = P - E; a = rel @ ax / ln; r = np.linalg.norm(rel - np.outer(rel @ ax, ax), axis=1)
    print(s, 'forearm length %.3f' % ln)
    for lo in np.arange(-0.2, 1.25, 0.1):
        m = arm & (a >= lo) & (a < lo + 0.1)
        sv = [v for v in np.where(m)[0] if v in body_v and v not in hand_v]
        hv = [v for v in np.where(m)[0] if v in hand_v]
        f = lambda vs: ('%3d r %.3f..%.3f' % (len(vs), r[vs].min(), r[vs].max())) if len(vs) else '  0'
        print(' a %.1f sleeve %s | stub/hand %s' % (lo, f(sv), f(hv)))
