#!/usr/bin/env python3
"""Grip gate, every clip, from mm9_highwayman_claude/scripts/grip_gate.py for a rigid fist: fingers classified by the solved chains (work/fist.json). Skinned positions at 5 times: per digit, verts inside the handle (depth), wrap in deg round the axis (verts within 4 cm of the axis, 15 deg bins); palm too; Yclub against Hand, rigid in deg. Copy of ../mm9_trellborg_claude/scripts/grip_gate.py run from that folder (reads its work/fist.json); writes argv[2]. Args: <glb> <out.txt>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
Pr = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
dom = np.concatenate([np.array([jn[j] for j in p['joints'][np.arange(len(p['joints'])), p['weights'].argmax(1)]]) for p in Pr]).astype(str)
def X(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(Pr))])
w0 = m.world({}); rest = X(w0)
F = json.load(open('work/fist.json'))['R']; b2g = lambda v: np.array([v[0], v[2] + LIFT, -v[1]])
yi = nm.index('Yclub'); ji = jn.index('Yclub'); hi = nm.index('Bip01 R Hand')
hv = np.char.find(dom, 'R Hand') >= 0
LIFT = w0[yi][1, 3] - F['G'][2]
G0 = b2g(F['G']); U0 = b2g(F['kn']) - np.array([0, LIFT, 0]); U0 /= np.linalg.norm(U0); RC = 0.0255
ch = {f: np.array([b2g(p) for p in c]) for f, c in F['posed'].items()}
ids = np.nonzero(hv)[0]; Q = rest[ids]
def dc(Q, c):
    best = np.full(len(Q), 9.0)
    for a, b in zip(c[:-1], c[1:]):
        ab = b - a; t = np.clip((Q - a) @ ab / (ab @ ab), 0, 1); best = np.minimum(best, np.linalg.norm(Q - a - np.outer(t, ab), axis=1))
    return best
nmf = list(ch); DD = np.array([dc(Q, ch[f]) for f in nmf]); own = DD.argmin(0); own[DD.min(0) > 0.045] = len(nmf); nmf2 = nmf + ['Palm']
e1 = np.cross(U0, [0.3, 0.9, 0.2]); e1 /= np.linalg.norm(e1); e2 = np.cross(U0, e1)
out = []; WR = {}
for clip in [a['name'] for a in m.glb.json['animations']]:
    d = m.clip_times(clip)[-1]; ins = 0; nin = 0; lock = []; wrap = {}
    for t in np.linspace(0, d, 5):
        wc = m.world(m.sample(clip, float(t))); Y = X(wc); Sk = wc[yi] @ m.inverse_binds[ji]
        G = (Sk @ np.r_[G0, 1])[:3]; U = Sk[:3, :3] @ U0
        for i, f in enumerate(nmf2):
            v = Y[ids[own == i]] - G; a_ = v @ U; pr = v - np.outer(a_, U); r = np.linalg.norm(pr, axis=1); on = np.abs(a_) < 0.085
            if on.any(): ins = max(ins, float((RC - r[on]).max())); nin += int((r[on] < RC - 0.002).sum())
            k = on & (r < 0.062)
            wrap.setdefault(f, []).append(len(np.unique((np.degrees(np.arctan2(pr[k] @ e2, pr[k] @ e1)) // 15).astype(int))) * 15 if k.sum() > 2 else 0)
        lock.append(np.linalg.inv(wc[hi]) @ wc[yi])
    dl = max(float(np.degrees(np.arccos(np.clip((np.trace(l[:3, :3].T @ lock[0][:3, :3]) - 1) / 2, -1, 1)))) for l in lock)
    out.append(f"{clip:13s} inside {ins * 100:4.1f} cm, {nin:4d} vs | wrap " + ' '.join(f'{f} {int(np.median(v))}' for f, v in wrap.items()) + f' | rigid {dl:.1f}')
    print(out[-1], flush=True)
Path(sys.argv[2]).write_text('\n'.join(out) + '\n')
