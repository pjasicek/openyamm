"""Throat close-up specs with an open line of sight (run 2, third request): per clip the target is the throat under the jaw (mean of Bip01 Neck and the jaw
hinge Box01 posed), the cameras sit 0.45 m out along the head's own below, front, left and right axes (bind directions turned by the
head's skin rotation), so the view follows the head when it throws back. Prints name:clip:t:view:body:cam:target for vshots.sh.
Args: [prefix]"""
import sys
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
import numpy as np
pre = sys.argv[1] if len(sys.argv) > 1 else 'th'
m = Model(Glb('review/viewer/liz_a.glb')); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
DIRS = {'below': (0, -1, .35), 'front': (0, -.35, 1), 'left': (1, -.45, .2), 'right': (-1, -.45, .2)}
OFF = np.cumsum([0] + [len(p['positions']) for p in m.primitives])
TR = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
g = np.pi * (3 - 5 ** .5); kk = np.arange(400) + .5; zz = 1 - 2 * kk / 400; rr = np.sqrt(1 - zz ** 2); DIRS2 = np.c_[rr * np.cos(g * kk), zz, rr * np.sin(g * kk)]
def hits(o, d, A, E1, E2):
    h = np.cross(d, E2); det = (E1 * h).sum(1); s_ = o - A
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (s_ * h).sum(1) / det; q = np.cross(s_, E1); v = (q @ d) / det; t = (E2 * q).sum(1) / det
    ok = (np.abs(det) > 1e-12) & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & np.isfinite(t)
    return np.sort(t[ok])
out = []
for c, t in (('Standing', .3), ('Hit2', .5), ('Death2', .6), ('Dead', .5)):
    w = m.world(m.sample(c, float(t))); R = (w[names.index('Bip01 Head')] @ ibm['Bip01 Head'])[:3, :3]
    tg = .5 * (w[names.index('Bip01 Neck')][:3, 3] + w[names.index('Box01')][:3, 3]) + R @ np.array([0, -.03, .04])
    P = np.vstack([x[0] for x in m.skinned_positions(w)]); A = P[TR[:, 0]]; E1 = P[TR[:, 1]] - A; E2 = P[TR[:, 2]] - A
    for k, d in DIRS.items():
        d0 = R @ (np.array(d, float) / np.linalg.norm(d)); best = None
        for dd in DIRS2:                                # the most open direction within 50 deg of the wanted one: nothing between camera and throat
            if dd @ d0 < .64: continue
            cam = tg + dd * .45
            if cam[1] < .05: continue
            hh = hits(cam, -dd, A, E1, E2); fr = hh[0] if len(hh) else .45
            sc = min(fr, .45 - .02) + .05 * (dd @ d0)
            if best is None or sc > best[0]: best = (sc, cam)
        cam = best[1] if best else tg + d0 * .45
        out.append(f'{pre}_{c}_{k}:{c}:{t}:quarter:body:{cam[0]:.3f},{cam[1]:.3f},{cam[2]:.3f}:{tg[0]:.3f},{tg[1]:.3f},{tg[2]:.3f}')
print(' '.join(out))
