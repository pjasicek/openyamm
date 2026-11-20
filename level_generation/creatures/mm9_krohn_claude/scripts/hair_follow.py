#!/usr/bin/env python3
"""Krohn's long hair hangs from the shoulders in the retargeted PeasantMale clips (Running, AttackMelee, Hit, Death).

KROHN.abc's hair chains (Xhairpiv*, children of the Head) keep their rest local rotation in the retargeted clips
(retarget_mm9.py: unmapped joints follow their parent), so every head pitch against the spine swings the hair tail through
the sword lying on the back (sword gate: Running 5.5 cm, Hit 5.8, AttackMelee 4.3, Death 3.4 cm). Here each hair pivot's
WORLD rotation follows Spine3 instead of the Head: its orientation relative to Spine3 is held at Standing's first key
(blend `k` of that, the rest stays the clip's own), per key, then written as the pivot's local rotation under the Head.
The scalp stays on the Head (head-weighted hair), the hanging hair rides with the back as the sword and cape do.
Usage: hair_follow.py in.glb out.glb k CLIP [CLIP ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion, slerp

src, dst, k, *clips = sys.argv[1:]
k = float(k)
g = Glb(Path(src)); m = Model(g)
names = [n.get('name') for n in g.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
import os
PIV = [idx[n] for n in os.environ.get('HAIR_PIVOTS', 'Xhairpiv,Xhairpiv01,Xhairpiv02').split(',')]   # HAIR_PIVOTS: a subset (mm9_krohn Death: the side strand only)
SP, HD = idx['Bip01 Spine3'], idx['Bip01 Head']
nrm = lambda M: M[:3, :3] / np.linalg.norm(M[:3, 0])
w0 = m.world(m.sample('Standing', 0.0))
K = {p: nrm(w0[SP]).T @ nrm(w0[p]) for p in PIV}
anims = {a['name']: a for a in g.json['animations']}
for clip in clips:
    a = anims[clip]
    for p in PIV:
        ch = next(c for c in a['channels'] if c['target']['node'] == p and c['target']['path'] == 'rotation')
        s = a['samplers'][ch['sampler']]
        times = g.accessor(s['input'])[:, 0]
        Q = g.accessor(s['output']).astype(np.float64)
        out = []
        for t, q in zip(times, Q):
            w = m.world(m.sample(clip, float(t)))
            want = nrm(w[HD]).T @ nrm(w[SP]) @ K[p]          # local under the Head that keeps Standing's hang off Spine3
            qn = matrix_quaternion(want)
            if qn @ q < 0:
                qn = -qn
            out.append(slerp(q, qn, k))
        s['output'] = g.append_accessor(np.array(out, np.float32), 'VEC4')
    m = Model(g)
    print('HAIRFOLLOW', clip, len(times), 'keys')
g.write(Path(dst))
