#!/usr/bin/env python3
"""roles_pg.json: the PeasantChildGirl library clips on the girl body (MM9 child girl skeleton, 60 joints, Bip01 names).
The MM9 roles plus the library clips the girls' scripts play: NPCbase.scr -> NPCBase.inc `Converse -1` (the library has one `conv`) and
BaseRun.inc `LoopAnim Cower`; YanmirChild.scr / NPC312.scr play none. Left out: hattack1 (peasants flee), cowerstart, cowerend.
ALL=1 adds them. Args: none (project folder)"""
import json, os
USED = dict(Standing=('stand', 1), Walking=('walk', 1), Running=('run', 1), Fidget=('fidget', 0), Talk=('conv', 0), Hit=('wince', 0),
            Death=('die1', 5), Cower=('cower', 1))
EXTRA = dict(Attack=('hattack1', 0), CowerStart=('cowerstart', 3), CowerEnd=('cowerend', 4))
ROLES = dict(USED, **EXTRA) if os.environ.get('ALL') else USED
roles = {}
for r, (c, k) in ROLES.items():
    d = dict(src='lib', clips=[c])
    if k == 1: d['loop'] = True
    elif k == 0: d['ease'] = 'both'
    elif k in (3, 5): d['ease'] = 'in'
    elif k == 4: d['ease'] = 'none'
    roles[r] = d
# five-finger hands from MM9's two two-bone chains: thumb from Finger0 / Finger01, the four fingers from Finger1 / Finger11
fa = {}
for s in 'LR':
    for f, src in (('Thumb', ('Finger0', 'Finger01', 'Finger01')), ('Index', ('Finger1', 'Finger11', 'Finger11')), ('Middle', ('Finger1', 'Finger11', 'Finger11')),
                   ('Ring', ('Finger1', 'Finger11', 'Finger11')), ('Pinky', ('Finger1', 'Finger11', 'Finger11'))):
        ks = (0.7, 0.5, 0.3) if f == 'Thumb' else (0.6, 0.6, 0.45)
        for k, (b, v) in enumerate(zip(src, ks), 1): fa[f'Bip01 {s} {f}{k}'] = [f'Bip01 {s} {b}', v, 'delta']
json.dump(dict(root='Bip01 Pelvis', root_nodes=['Bip01 Pelvis', 'Scene Root', 'Bip01 L Calf', 'Bip01 R Calf', 'Bip01 Spine'], foot='Bip01 L Toe0',
               sources={'lib': 'source/mm9_lib/pchildgirl/pchildgirl.glb'}, standing='Standing', dead_from='Death', lift_to_floor=True, thin_keys=True,
               root_lift={'Bip01 Pelvis': -0.10196},     # the library keys the pelvis relative (0 = standing); the bind has it 0.102 up
               roles=roles, finger_alias=fa), open(os.environ.get('OUT', 'scripts/roles_pg.json'), 'w'), indent=0)
print('ROLES', list(roles))
