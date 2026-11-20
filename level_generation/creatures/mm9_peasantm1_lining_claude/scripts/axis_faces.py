#!/usr/bin/env python3
"""Installed sleeve faces that pass through the forearm (within `r` m of the posed forearm->hand axis, between 5 cm past the
elbow and 3 cm past the wrist: sleeve_poke_gate.py's candidate range) in any frame of any clip at `fps`: faces folded into the
wrist, hidden inside the arm. Their lining twins sit on the other side of the axis and read as skin through the sleeve in
the poke gate, so the cuff bands leave them out (line.py band `exclude`). Usage: axis_faces.py <installed glb> [r 0.006] [fps 24]"""
import sys
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
glb = sys.argv[1]; R = float(sys.argv[2]) if len(sys.argv) > 2 else 0.006; FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 24
g = Glb(Path(glb)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
pr = m.primitives[0]; T = pr['triangles']; dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
idx = {n: i for i, n in enumerate(names)}; out = {}
BARY = np.array([(i / 4, j / 4, 1 - i / 4 - j / 4) for i in range(5) for j in range(5 - i)])
for tok in ('L', 'R'):
    arm = [j for j in jn if f' {tok} ' in j and any(k in j for k in ('UpperArm', 'Forearm', 'Hand'))]
    sf = np.where(np.isin(dom, arm)[T].sum(1) >= 2)[0]; fa, hd = idx[f'Bip01 {tok} Forearm'], idx[f'Bip01 {tok} Hand']
    hit = {}
    for clip in m.clips:
        t1 = m.clip_times(clip)[-1]
        for t in np.append(np.arange(0, t1, 1 / FPS), t1):
            W = m.world(m.sample(clip, float(t))); X = m.skinned_positions(W)[0][0]
            a0, a1 = W[fa][:3, 3], W[hd][:3, 3]; L = np.linalg.norm(a1 - a0); ax = (a1 - a0) / L
            V = X[T[sf]]; Q = np.einsum('kb,fbc->fkc', BARY, V)          # 15 sample points per face
            s = (Q - a0) @ ax; d = np.linalg.norm(np.cross(Q - a0, ax), axis=2)
            for f in sf[((d < R) & (s > 0.05) & (s < L + 0.03)).any(1)]:
                hit.setdefault(int(f), (clip, round(float(t), 3)))
    out[tok] = hit
    print(tok, len(hit), 'faces:', sorted(hit), {f: hit[f] for f in sorted(hit)[:8]})
