#!/usr/bin/env python3
"""roles_mk.json: all of MM9's clips. Args: none (project folder)"""
import json
ROLES = dict(Standing=('stand', 1), Walking=('walk', 1), Running=('run', 1), Backpedal=('Backpedal', 1), BackpedalRun=('BackpedalRun', 1),
  Fidget=('fidget1', 0), Fidget2=('fidget2', 0), Pray=('pray', 2), Aware=('aware', 0), Taunt=('Taunt', 0), CowerStart=('cowerstart', 3), Cower=('cower', 2), CowerEnd=('cowerend', 4),
  AttackMelee=('Hattack1', 0), AttackRanged=('castspell1', 0), AttackRanged2=('castspell2', 0), AttackRanged3=('castspell3', 0), Hit=('wince1', 0), Hit2=('wince2', 0), Death=('die1', 5), Death2=('die2', 5),
  Play=('play', 2), HoeWait=('hoewait', 2), Hoe=('hoe', 2), HoeFidget=('hoefidget', 2), SweepWait=('sweepwait', 2), Sweep=('sweep', 2), SweepFidget=('sweepfidget', 2), HammerWait=('hammerwait', 2), Hammer=('hammer', 2), HammerFidget=('hammerfidget', 2), WashWait=('washwait', 2), Wash=('wash', 2), WashFidget=('washfidget', 2))
roles = {}
for r, (c, k) in ROLES.items():
    d = dict(src='own', clips=[c])
    if k == 1: d['loop'] = True
    elif k == 0: d['ease'] = 'both'
    elif k == 3: d['ease'] = 'in'
    elif k == 4: d['ease'] = 'none'
    elif k == 5: d['ease'] = 'in'
    else: d['loop'] = True      # work and prayer loops: MM9 plays them in place; the seam residual is spread
    roles[r] = d
X = [f'X{a}' for a in ('main', 'Bbase', 'Ba', 'Bc', 'Bd', 'Fbase', 'Fpiv', 'Fa', 'Fb', 'Fd', 'Rbase', 'Rpiv', 'Rb', 'Rd', 'BRbase', 'BRpiv', 'BRa', 'BRc', 'BRd', 'FRpiv', 'FRa', 'FRb', 'FRc', 'FRd')]
for b in ('XRbase', 'XRpiv', 'XRb', 'XRd', 'XBRbase', 'XBRpiv', 'XBRa', 'XBRc', 'XBRd', 'XFRpiv', 'XFRa', 'XFRb', 'XFRc', 'XFRd'): X.append(b + '01')
fa = {}
for s in 'LR':
    for f, (a, b, c), src in (('Thumb', (0.7, 0.4, 0.2), 'Finger0'), ('Index', (0.6, 0.5, 0.35), 'Finger1'), ('Middle', (0.6, 0.5, 0.35), 'Finger1'), ('Ring', (0.6, 0.5, 0.35), 'Finger1'), ('Pinky', (0.6, 0.5, 0.35), 'Finger1')):
        for k, v in zip((1, 2, 3), (a, b, c)): fa[f'Bip01 {s} {f}{k}'] = [f'Bip01 {s} {src}', v, 'delta']
json.dump(dict(root='Bip01 Spine', root_nodes=['Bip01 Spine', 'Scene Root', 'Bip01 L Calf', 'Bip01 R Calf'] + X, foot='Bip01 L Toe0', sources={'own': 'source/mk1/mk1.glb'}, standing='Standing', dead_from='Death', lift_to_floor=True, thin_keys=True, roles=roles, finger_alias=fa), open('scripts/roles_mk.json', 'w'), indent=0)
