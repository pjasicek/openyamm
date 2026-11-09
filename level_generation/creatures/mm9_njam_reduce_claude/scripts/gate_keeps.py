#!/usr/bin/env python3
"""Extra exact faces that hold two of the Nobleman's gates at the installed values (per GLB LOD0 face, glb_parts order):
- shoulder skin (SHOULDER=1): every face with a vertex whose dominant joint is a Clavicle or UpperArm, the vertex set the
  jitter gate's shoulder-skin term reads (its 95th percentile moved with the sample: AttackMelee2 R 3.84 -> 4.27 mm/f2 at a55;
  Colloidal Warrior / Ebora lesson); the vertices themselves never move under mpqem, so keeping them keeps the term;
- hand contact (CONTACT=1): faces within R m of the other hand's posed vertices in CLIPS (default Fidget: the hands-together
  gesture, R hand into the L hand 1.6 -> 1.9 cm at a55), any part except the reaching hand's own arm, mirrored.
Usage: gate_keeps.py <in set tag> <out set tag>   (env SHOULDER, CONTACT, R, CLIPS) -> work/glb_sets_<out>.npz"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
src, dst = sys.argv[1:3]
S = dict(np.load(HERE / 'work' / f'glb_sets_{src}.npz'))
m = Model(Glb(str(HERE / 'before' / 'mm9_njam.glb')))
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
PR = m.primitives; nf = [len(p['triangles']) for p in PR]; off = np.cumsum([0] + nf)
dom = [np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in PR]
extra = np.zeros(off[-1], bool)
if E('SHOULDER', '1') == '1':
    for k, p in enumerate(PR):
        sv = np.array([d.endswith('Clavicle') or d.endswith('UpperArm') for d in dom[k]])
        hit = sv[p['triangles']].any(1); extra[off[k]:off[k + 1]] |= hit
    print('SHOULDER faces', int(extra.sum()))
if E('CONTACT', '1') == '1':
    R = float(E('R', '0.03')); clips = E('CLIPS', 'Fidget').split(','); hit = np.zeros(off[-1], bool)
    arm = lambda side: [np.array([(f' {side} ' in d) and any(d.endswith(b) for b in ('Hand', 'Forearm', 'UpperArm', 'Clavicle')) or
                                  (f' {side} ' in d and ('Finger' in d or 'Thumb' in d or 'Index' in d or 'Middle' in d or 'Ring' in d or 'Pinky' in d))
                                  for d in dk]) for dk in dom]
    armL, armR = arm('L'), arm('R')
    handv = lambda side: [np.array([f' {side} ' in d and not d.endswith('Forearm') and not d.endswith('UpperArm') and not d.endswith('Clavicle')
                                    and ('Hand' in d or 'Finger' in d or 'Thumb' in d) for d in dk]) for dk in dom]
    hL, hR = handv('L'), handv('R')
    for c in clips:
        for t in m.clip_times(c)[::2]:
            P = [x[0] for x in m.skinned_positions(m.world(m.sample(c, t)))]
            for hand, own in ((hR, armR), (hL, armL)):
                H = np.vstack([P[k][hand[k]] for k in range(len(PR))])
                tree = cKDTree(H)
                for k, p in enumerate(PR):
                    T = p['triangles']; d, _ = tree.query(P[k][T].mean(1), distance_upper_bound=R)
                    hit[off[k]:off[k + 1]] |= (d < R) & ~own[k][T].all(1)
    cen = np.vstack([PR[k]['positions'][PR[k]['triangles']].mean(1) for k in range(len(PR))])
    mir = cKDTree(cen).query(cen[hit] * [-1, 1, 1])
    hit[mir[1][mir[0] < 0.004]] = True
    print('CONTACT faces', int(hit.sum()), 'per prim', [int(hit[off[k]:off[k + 1]].sum()) for k in range(len(PR))])
    extra |= hit
new = extra & ~S['keep'] & ~S['lining']
S['keep'] = S['keep'] | (extra & ~S['lining']); S['group'] = np.where(S['keep'], 0, S['group'])
np.savez(HERE / 'work' / f'glb_sets_{dst}.npz', **S)
print('SET', dst, 'keep', int(S['keep'].sum()), f'(+{int(new.sum())})', 'groups', {int(g): int((S['group'][~S['keep']] == g).sum()) for g in np.unique(S['group'][~S['keep']])})
