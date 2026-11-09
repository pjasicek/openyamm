"""March along limbs by plane sections from a mid-limb seed. Args: <npz> <out npz>"""
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section, nearest_loop
npz, out = sys.argv[1:3]
D = np.load(npz); co, tri = D['co'], D['tri']


def march(p, d, step=0.01, nmax=120, jump=1.6):
    pts = []; p = np.array(p, float); d = d / np.linalg.norm(d); last = None
    for i in range(nmax):
        l = nearest_loop(section(co, tri, p, d), p)
        if l is None or np.linalg.norm(l['c'] - p) > 0.05: break
        if last is not None and l['per'] > last * jump: pts.append((*l['c'], l['per'])); break
        c = l['c']; pts.append((*c, l['per']))
        last = l['per'] if last is None else 0.7 * last + 0.3 * l['per']
        if len(pts) > 4:
            nd = np.array(pts[-1][:3]) - np.array(pts[-5][:3]); nd /= np.linalg.norm(nd); d = 0.6 * d + 0.4 * nd; d /= np.linalg.norm(d)
        p = c + d * step
    return np.array(pts)


seeds = {'armL': ((-.39, .08, 1.35), (-1, -.2, -.05)), 'armR': ((.40, .1, 1.48), (1, -.2, -.05)), 'legL': ((-.16, .04, .55), (-.2, .03, -1)), 'legR': ((.20, .01, .57), (.2, .0, -1))}
res = {}
for k, (p, d) in seeds.items():
    d = np.array(d, float)
    out1 = march(p, d, jump=2.2); in1 = march(p, -d)
    res[k] = np.vstack([in1[::-1], out1])
    print(k, len(in1), len(out1))
    a = res[k]
    for r in a[::5]: print('  ', r.round(3).tolist())
    print('  end', a[0].round(3), a[-1].round(3))
np.savez(out, **res)
