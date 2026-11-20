"""Write scripts/retarget_pmale.json for GREENMAN: bone map (same Bip01 names), root bases, leg-length scale, and the
staff bone's (Bone01) transform in the R hand from GREENMAN's own stand clip, frame 0.
Usage (project dir): gltf_venv python scripts/retarget_setup.py"""
import json, sys
import numpy as np
sys.path.insert(0, 'scripts')
from retarget_mm9 import read, sample, rest, parents, qmul, qinv, qrot
from pygltflib import GLTF2
T = GLTF2().load('source/mm9/greenman.glb'); S = GLTF2().load('source/mm9_lib/pmale.glb')
tn = {n.name: i for i, n in enumerate(T.nodes)}; sn = {n.name: i for i, n in enumerate(S.nodes)}
tpar = parents(T)
def fk(g, par, anim, i, t=0.0):
    chain = [i]
    while chain[-1] in par:
        chain.append(par[chain[-1]])
    p = np.zeros(3); q = np.array([0, 0, 0, 1.0])
    for j in reversed(chain):
        tr = sample(g, anim, j, 'translation', np.array([t])) if anim else None
        ro = sample(g, anim, j, 'rotation', np.array([t])) if anim else None
        tr = tr[0] if tr is not None else rest(g.nodes[j], 'translation')
        ro = ro[0] if ro is not None else rest(g.nodes[j], 'rotation')
        p = p + qrot(q[None], tr[None])[0]; q = qmul(q[None], ro[None])[0]
    return p, q
stand = next(a for a in T.animations if a.name == 'stand')
hp, hq = fk(T, tpar, stand, tn['Bip01 R Hand']); sp, sq = fk(T, tpar, stand, tn['Bone01'])
rel_t = qrot(qinv(hq)[None], (sp - hp)[None])[0]; rel_q = qmul(qinv(hq)[None], sq[None])[0]
def leg(g, names):
    return sum(np.linalg.norm(rest(g.nodes[{n.name: i for i, n in enumerate(g.nodes)}[k]], 'translation')) for k in names)
lt = leg(T, ['Bip01 R Calf', 'Bip01 R Foot']); ls = leg(S, ['Bip01 R Calf', 'Bip01 R Foot'])
gm_root = sample(T, stand, tn['Bip01'], 'translation', np.array([0.0]))[0]
pm_stand = next(a for a in S.animations if a.name == 'stand1')
pm_root = sample(S, pm_stand, sn['Bip01 Spine'], 'translation', np.array([0.0]))[0]
bones = {n: n for n in tn if n.startswith('Bip01 ') and n in sn and n != 'Bip01 Pelvis'}
# PeasantMale has a thumb (Finger0/01) and one finger chain (Finger1/11): GREENMAN's other fingers follow that chain
for side in 'LR':
    bones[f'Bip01 {side} Finger02'] = f'Bip01 {side} Finger01'
    for k in '1234':
        bones[f'Bip01 {side} Finger{k}'] = f'Bip01 {side} Finger1'
        bones[f'Bip01 {side} Finger{k}1'] = f'Bip01 {side} Finger11'
        bones[f'Bip01 {side} Finger{k}2'] = f'Bip01 {side} Finger11'
cfg = {'clips': {'run': 'run', 'hattack1': 'hattack1', 'wince1': 'wince1', 'die1': 'die1'},
       'bones': bones, 'root': ['Bip01', 'Bip01 Spine'], 'fps': 30, 'root_scale': round(lt / ls, 4),
       'root_target_base': [round(float(x), 5) for x in gm_root], 'root_source_base': [round(float(x), 5) for x in pm_root],
       'follow': {'Bone01': ['Bip01 R Hand', [float(x) for x in rel_t], [float(x) for x in rel_q]]},
       '_note': 'GREENMAN.abc has only stand, fidget1, fidget2, walk; row 266 BaseName PeasantMale: run, hattack1, wince1, die1 '
                'from the PeasantMale library by world-rotation copy; leg length ratio %.3f / %.3f; staff bone rigid in the R hand '
                '(MM9 stand frame 0; MM9 own clips keep it within 0.9 deg).' % (lt, ls)}
json.dump(cfg, open('scripts/retarget_pmale.json', 'w'), indent=1)
print('legs', lt, ls, 'k', lt / ls, 'gm_root', gm_root, 'pm_root', pm_root, 'rel', rel_t, rel_q, 'bones', len(bones))
