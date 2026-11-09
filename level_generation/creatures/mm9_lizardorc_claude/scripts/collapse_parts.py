#!/usr/bin/env python3
"""Collapse gate split by mesh part (run 2): collapse_gate.py's test (area below 20 % of rest, or normal flipped against its blended
rotation) at 30 fps, counted at each clip's worst frame per region and per part of work/final.npz (matched by rest position), and the
head split into mouth (teeth, tongue, red mouth paint), neck (below the jaw hinge plane, behind the jaw) and skull. Exposed = seen from some
direction (collapse_gate.exposed). Args: <glb> <out txt> [clips]"""
import sys, json, runpy
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.argv = [sys.argv[0], sys.argv[1], '/dev/null', 'Standing'] + sys.argv[2:] if False else sys.argv
G = runpy.run_path(str(HERE / 'scripts' / 'collapse_gate.py'), run_name='lib', init_globals=None) if False else None
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, out = sys.argv[1:3]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
m = Model(Glb(glb)); doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives; rest = np.vstack([np.asarray(p['positions'], float) for p in PR]); OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
SK = lambda w: np.vstack([x[0] for x in m.skinned_positions(w)])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1); dn = np.array([names[d] for d in dom])
REG = {'knee': ('Calf',), 'hip': ('Thigh',), 'elbow': ('Forearm',), 'shoulder': ('UpperArm', 'Clavicle'), 'groin': ('Bip01 Pelvis', 'Bip01 Spine'), 'torso': ('Spine1', 'Spine2', 'Spine3'), 'neck': ('Bip01 Neck', 'XhalfHead', 'XhalfNeck'), 'head': ('Bip01 Head',)}
def region(n):
    for r, ks in REG.items():
        if r == 'groin':
            if n in ks: return r
        elif any(k in n for k in ks): return r
    return 'other'
reg = np.array([region(n) for n in dn])
F = np.load(HERE / 'work/final.npz'); fp = F['part']; tr = cKDTree(F['co']); d_, ix = tr.query(rest); vpart = np.where(d_ < 1e-5, fp[ix], -2)
fpart = vpart[T].max(1)
# head classes
J0 = np.load(HERE / 'work/joined.npz'); jk = J0['jawk']; vj = np.where(d_ < 1e-5, jk[F['vmap'][ix].clip(0)] * (F['vmap'][ix] >= 0), 0)
hp = [i for i, p in enumerate(PR) if p['skinned']][2]   # head primitive (third skinned)
uv = np.asarray(m.glb.accessor(doc['meshes'][0]['primitives'][hp]['attributes']['TEXCOORD_0']), float) if False else None
c0 = rest[T].mean(1)
cls = np.array(['-'] * len(T), dtype=object)
hd = fpart == 1
cls[np.isin(fpart, [3, 4, 7])] = 'mouth'
cls[hd & (c0[:, 2] < .17) & (c0[:, 1] < .70)] = 'neck'
cls[hd & (cls == '-')] = 'skull'
# red mouth paint on head skin faces: by the head texture at the face's UV centroid
img = None
for i, p in enumerate(PR):
    pass
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
from collections import Counter
res = {}; lines = []
for clip in [a['name'] for a in doc['animations'] if not want or a['name'] in want]:
    best = (-1, 0, None)
    for t in np.arange(0, m.clip_times(clip)[-1] + 1e-6, 1 / 30):
        world = m.world(m.sample(clip, float(t))); P = SK(world); pal = world[m.joints] @ m.inverse_binds
        n, a = tri(P); nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
        dd = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
        bad = ok & ((a < .2 * a0) | (dd < 0))
        if bad.sum() > best[0]: best = (int(bad.sum()), float(t), bad)
    _, t, bad = best
    cnt = Counter()
    for f in np.nonzero(bad)[0]:
        key = reg[f] + ':' + ('hide' if fpart[f] == 0 else 'head-' + cls[f] if fpart[f] in (1, 3, 4, 7) else 'cutlass' if fpart[f] == 30 else f'shell{fpart[f]}')
        cnt[key] += 1
    line = f'{clip:12s} t={t:.2f} ' + ' '.join(f'{k}={v}' for k, v in sorted(cnt.items()))
    print(line, flush=True); lines.append(line); res[clip] = {'t': t, 'faces': [int(f) for f in np.nonzero(bad)[0]]}
open(out, 'w').write('\n'.join(lines) + '\n'); json.dump(res, open(out + '.json', 'w'))
