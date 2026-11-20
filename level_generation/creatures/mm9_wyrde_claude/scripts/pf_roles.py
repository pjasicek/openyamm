#!/usr/bin/env python3
"""roles_pf.json: the PeasantFemale library clips on the PeasantF1 body (MM9 human female skeleton, 73 joints).
Default (user decision for townsfolk, Annud 2026-10-31): the MM9 roles plus the library clips this body's scripts play.
ALL=1 writes every one of the library's 20 clips (for F1/F5 or a later script pass). Args: none (project folder)"""
import json, os
# role -> (library clip, kind): 1 loop, 0 one-shot eased both ways, 5 death (eased in)
USED = dict(Standing=('stand1', 1), Walking=('Walk', 1), Running=('run', 1), Fidget=('Fidget4', 0), Talk=('Conv2', 0), Conv1=('Conv1', 0),
            Conv3=('Conv3', 0), Hit=('Wince1', 0), Death=('Die1', 5), Cower=('cower', 1))
EXTRA = dict(Fidget2=('Fidget3', 0), Yawn=('Yawn', 0), Wash=('Wash', 1), WashFidget=('Washfidget', 0), Wipe=('wipe', 1), WipeFidget=('wipefidget', 0),
             Hit2=('Wince2', 0), Death2=('Die2', 5), CowerStart=('cowerstart', 3), CowerEnd=('cowerend', 4))
ROLES = dict(USED, **EXTRA) if os.environ.get('ALL') else USED
roles = {}
for r, (c, k) in ROLES.items():
    d = dict(src='lib', clips=[c])
    if k == 1: d['loop'] = True
    elif k == 0: d['ease'] = 'both'
    elif k in (3, 5): d['ease'] = 'in'
    elif k == 4: d['ease'] = 'none'
    roles[r] = d
fa = {}
for s in 'LR':
    for f, (a, b, c), src in (('Thumb', (0.7, 0.4, 0.2), 'Finger0'), ('Index', (0.6, 0.5, 0.35), 'Finger1'), ('Middle', (0.6, 0.5, 0.35), 'Finger1'),
                              ('Ring', (0.6, 0.5, 0.35), 'Finger1'), ('Pinky', (0.6, 0.5, 0.35), 'Finger1')):
        for k, v in zip((1, 2, 3), (a, b, c)): fa[f'FHP {s} {f}{k}'] = [f'FHP {s} {src}', v, 'delta']
json.dump(dict(root='FHP Pelvis', root_nodes=['FHP Pelvis', 'Scene Root', 'FHP L Calf', 'FHP R Calf', 'FHP Spine1'], foot='FHP L Toe0',
               sources={'lib': 'source/mm9_lib/pfemale.glb'}, standing='Standing', dead_from='Death', lift_to_floor=True, thin_keys=True,
               roles=roles, finger_alias=fa), open(os.environ.get('OUT', 'scripts/roles_pf.json'), 'w'), indent=0)
print('ROLES', list(roles))
