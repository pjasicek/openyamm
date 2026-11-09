"""Throat close-up specs (run 2, third request): per clip the target is the throat under the jaw (mean of Bip01 Neck and the jaw
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
out = []
for c, t in (('Standing', .3), ('Hit2', .5), ('Death2', .6), ('Dead', .5)):
    w = m.world(m.sample(c, float(t))); R = (w[names.index('Bip01 Head')] @ ibm['Bip01 Head'])[:3, :3]
    tg = .5 * (w[names.index('Bip01 Neck')][:3, 3] + w[names.index('Box01')][:3, 3]) + R @ np.array([0, -.03, .04])
    for k, d in DIRS.items():
        d = R @ (np.array(d, float) / np.linalg.norm(d)); cam = tg + d * .45
        if cam[1] < .05: cam[1] = .05
        out.append(f'{pre}_{c}_{k}:{c}:{t}:quarter:body:{cam[0]:.3f},{cam[1]:.3f},{cam[2]:.3f}:{tg[0]:.3f},{tg[1]:.3f},{tg[2]:.3f}')
print(' '.join(out))
