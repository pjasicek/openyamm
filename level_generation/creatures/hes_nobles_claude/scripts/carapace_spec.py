#!/usr/bin/env python3
"""The Nobles' gilded carapace (fam_nobles.png; CODEX_BRIEF_NOBLES.md: grown chitin with bone-ceramic inserts,
black-violet resin joints, restrained conduit seams, fine gold edges; rib/leaf-shaped plates that leave the lean body
and the wing roots legible) on the winged Kreegan body, as the Trooper's route (hes_kreegan_claude/armour_spec_v4.py):
projected plates (make_carapace.py), skinned as a shell (skin_shell.py: each piece takes the mean of the body's weights
under it, `rigid` 1.0, so it moves like armour). Pieces:
- torso: a V breastplate over the chest (the charcoal abdomen stays bare), a narrow spine plate between the wing roots,
  the belt front and back;
- skirt: a long pointed front tabard and a back tabard (pelvis and both thighs averaged: they swing between the legs),
  a pointed leaf over each hip riding its thigh;
- legs: a thigh plate over the front, a knee cap, a greave;
- arms: a two-layer pauldron with two ivory spikes, an upper-arm plate, a bracer (the native forearm spurs pass
  through it, as the sheet's spiked bracers).
Writes scripts/carapace_noble.json. Args: none"""
import json, math, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = math.radians
FINGERS = [f'B_{s}_Finger{a}{b}' for s in 'LR' for a in range(6) for b in ('', '1', '2')] + ['B_R_Finger0.001', 'B_R_Finger0.002']
ARMS = [f'B_{s}_{b}' for s in 'LR' for b in ('UpperArm', 'UpperArmTwist', 'Forearm', 'ForearmTwist', 'Hand')] + FINGERS
HEAD = ['B_Head', 'B_Neck']
WINGS = [f'B_Wing_{s}_{b}' for s in 'LR' for b in ('Root', 'Arm', 'Finger1', 'Finger2', 'Finger3', 'Lead')]
LEGS = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')]


def sym(tab):
    return [[v, -w] for v, w in tab], [[v, w] for v, w in tab]


def plane(name, bone, side, v, half, nu, nv, off, t, crown, excl=(), **kw):
    kw.setdefault('shell', {'rigid': 1.0})
    lo, hi = sym(half)
    p = {'name': name, 'bone': bone, 'kind': 'plane', 'side': side, 'v': v, 'nu': nu, 'nv': nv, 'off': off, 't': t,
         'lip': kw.pop('lip', 0.005), 'exclude_bones': list(excl), 'crown': crown, 'lo': lo, 'hi': hi}
    p.update(kw)
    return p


def mirror_angles(tab):
    return [[v, -h, -l] for v, l, h in tab]


def cyl(name, bone, v, tab, nu, nv, off, t, include, ref=(0, -1, 0), **kw):
    p = {'name': name, 'bone': bone, 'kind': 'cyl', 'ref': list(ref), 'v': v, 'nu': nu, 'nv': nv, 'off': off, 't': t,
         'lip': kw.pop('lip', 0.005), 'include_bones': include,
         'lo': [[a, l] for a, l, h in tab], 'hi': [[a, h] for a, l, h in tab], 'hpct': 90}
    p.setdefault('shell', {'rigid': 1.0})
    p.update(kw)
    return p


def cap(name, bone, centre, out, v, az, nu, nv, off, t, include, hmax, **kw):
    p = {'name': name, 'bone': bone, 'kind': 'cap', 'centre': centre, 'out': out, 'v': v, 'nu': nu, 'nv': nv,
         'off': off, 't': t, 'lip': kw.pop('lip', 0.007), 'include_bones': include, 'win': [D(18), D(18)],
         'lo': [[a, -w] for a, w in az], 'hi': [[a, w] for a, w in az], 'hmax': hmax, 'hpct': 90}
    p.setdefault('shell', {'rigid': 1.0})
    p.update(kw)
    return p


TORSO_X = ARMS + HEAD + WINGS
SKIRT = {'rigid': 1.0, 'fixed': {'B_Pelvis': 0.6, 'B_L_Thigh': 0.2, 'B_R_Thigh': 0.2}}
plates = [
    # the V breastplate: from the collarbones to a point at the solar plexus, a keel down its middle
    plane('chest', 'B_Spine2', 'front', [0.935, 1.105],
          [[0.935, 0.010], [0.96, 0.045], [0.99, 0.085], [1.03, 0.118], [1.075, 0.130], [1.105, 0.095]], 9, 8,
          0.010, 0.010, 0.014, excl=TORSO_X + LEGS, lip=0.006,
          glow=[[[0.5, 0.05], [0.5, 0.55]], [[0.18, 0.80], [0.40, 0.55], [0.5, 0.40]], [[0.82, 0.80], [0.60, 0.55], [0.5, 0.40]]],
          shell={'rigid': 1.0, 'bones': ['B_Spine2', 'B_Spine1']}),
    # the spine plate between the wing roots
    plane('spine', 'B_Spine2', 'back', [0.90, 1.08], [[0.90, 0.015], [0.94, 0.045], [1.02, 0.055], [1.08, 0.040]], 5, 6,
          0.010, 0.010, 0.012, excl=TORSO_X + LEGS, lip=0.005, glow=[[[0.5, 0.1], [0.5, 0.9]]],
          shell={'rigid': 1.0, 'bones': ['B_Spine2', 'B_Spine1', 'B_Spine']}),
    plane('belt_f', 'B_Pelvis', 'front', [0.80, 0.84], [[0.80, 0.095], [0.82, 0.105], [0.84, 0.110]], 7, 3,
          0.012, 0.010, 0.010, excl=ARMS + WINGS, lip=0.004, paint_studs=[[0.5, 0.5]],
          shell={'rigid': 1.0, 'bones': ['B_Pelvis', 'B_Spine']}),
    plane('belt_b', 'B_Pelvis', 'back', [0.80, 0.84], [[0.80, 0.095], [0.82, 0.105], [0.84, 0.110]], 7, 3,
          0.012, 0.010, 0.010, excl=ARMS + WINGS, lip=0.004, shell={'rigid': 1.0, 'bones': ['B_Pelvis', 'B_Spine']}),
    # the long pointed tabards hang from the belt between the legs (pelvis and both thighs averaged)
    plane('tabard_f', 'B_Pelvis', 'front', [0.47, 0.805],
          [[0.47, 0.004], [0.53, 0.030], [0.62, 0.052], [0.72, 0.060], [0.805, 0.058]], 5, 8, 0.030, 0.010, 0.010,
          excl=ARMS + WINGS, lip=0.005, flat_rows=True, glow=[[[0.5, 0.12], [0.5, 0.9]]], shell=SKIRT),
    plane('tabard_b', 'B_Pelvis', 'back', [0.50, 0.805],
          [[0.50, 0.004], [0.56, 0.032], [0.65, 0.055], [0.74, 0.065], [0.805, 0.065]], 5, 8, 0.030, 0.010, 0.010,
          excl=ARMS + WINGS, lip=0.005, flat_rows=True, shell=SKIRT),
]
for s in 'LR':
    m = (lambda tab: tab) if s == 'L' else mirror_angles
    sx = 1 if s == 'L' else -1
    sh = lambda b: {'rigid': 1.0, 'bones': b}
    plates += [
        # a pointed leaf over the hip, riding its thigh (cyl u: 0 front, -90 lateral for the left limb)
        cyl(f'leaf_{s}', f'B_{s}_Thigh', [0.10, 0.74], m([[0.10, D(-135), D(-50)], [0.22, D(-135), D(-45)],
            [0.40, D(-128), D(-55)], [0.60, D(-112), D(-70)], [0.74, D(-92), D(-88)]]), 6, 8, 0.016, 0.010,
            [f'B_{s}_Thigh', 'B_Pelvis'], lip=0.005, glow=[[[0.5, 0.1], [0.5, 0.8]]], shell=sh([f'B_{s}_Thigh'])),
        cyl(f'thigh_{s}', f'B_{s}_Thigh', [0.42, 0.92], m([[0.42, D(-38), D(-30)], [0.56, D(-72), D(8)], [0.76, D(-82), D(18)], [0.92, D(-62), D(10)]]),
            6, 7, 0.012, 0.010, [f'B_{s}_Thigh'], lip=0.005, glow=[[[0.5, 0.15], [0.5, 0.85]]], shell=sh([f'B_{s}_Thigh'])),
        cap(f'knee_{s}', f'B_{s}_Calf', [0.105 * sx, -0.10, 0.52], [0, -1.0, 0.15], [-0.50, 0.50],
            [[-0.50, D(8)], [-0.22, D(38)], [0.25, D(44)], [0.50, D(30)]], 6, 6, 0.014, 0.012, [f'B_{s}_Calf', f'B_{s}_Thigh'], 0.12,
            win=[D(22), D(22)], studs=[[0.5, 0.5]], stud_r=0.010, insert=0.2, shell=sh([f'B_{s}_Calf'])),
        cyl(f'greave_{s}', f'B_{s}_Calf', [0.10, 0.84], m([[0.10, D(-12), D(12)], [0.26, D(-62), D(48)], [0.62, D(-52), D(38)], [0.84, D(-18), D(14)]]),
            6, 6, 0.010, 0.010, [f'B_{s}_Calf'], lip=0.005, glow=[[[0.5, 0.12], [0.5, 0.88]]], shell=sh([f'B_{s}_Calf'])),
        # the two-layer pauldron: a large lower cap over the shoulder and a smaller upper cap above it
        cap(f'pauldron_{s}', f'B_{s}_UpperArm', [0.17 * sx, -0.06, 1.05], [1.0 * sx, 0, 0.55], [-0.50, 1.05],
            [[-0.50, D(48)], [0.0, D(60)], [0.80, D(42)], [1.05, D(20)]], 8, 7, 0.022, 0.012, [f'B_{s}_Clavicle', f'B_{s}_UpperArm',
            f'B_{s}_UpperArmTwist'], 0.16, insert=0.4, glow=[[[0.10, 0.20], [0.5, 0.10], [0.90, 0.20]]],
            shell=sh([f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist', f'B_{s}_Clavicle'])),
        cyl(f'upperarm_{s}', f'B_{s}_UpperArm', [0.35, 0.85], m([[0.35, D(-150), D(-30)], [0.85, D(-140), D(-35)]]),
            5, 5, 0.010, 0.010, [f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist'], lip=0.005,
            glow=[[[0.5, 0.12], [0.5, 0.88]]], shell=sh([f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist'])),
        cyl(f'bracer_{s}', f'B_{s}_Forearm', [0.15, 0.85], m([[0.08, D(-75), D(-62)], [0.28, D(-150), D(22)], [0.60, D(-145), D(18)], [0.86, D(-120), D(4)]]),
            7, 7, 0.006, 0.009, [f'B_{s}_Forearm', f'B_{s}_ForearmTwist'], lip=0.005,
            glow=[[[0.5, 0.10], [0.5, 0.90]]], shell=sh([f'B_{s}_Forearm', f'B_{s}_ForearmTwist'])),
    ]
props = []
for s in 'LR':
    sx = 1 if s == 'L' else -1
    # two ivory spikes rising up and back out of the upper pauldron (fam_nobles.png)
    props.append({'name': f'pspike_{s}', 'bone': f'B_{s}_UpperArm', 'kind': 'loft',
                  'ctrl': [[0.19 * sx, -0.07, 1.09], [0.21 * sx, -0.07, 1.14], [0.235 * sx, -0.06, 1.19], [0.27 * sx, -0.04, 1.23]],
                  'r': [0.016, 0.020], 'nseg': 5, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
    props.append({'name': f'pspike2_{s}', 'bone': f'B_{s}_UpperArm', 'kind': 'loft',
                  'ctrl': [[0.24 * sx, -0.08, 1.04], [0.275 * sx, -0.08, 1.07], [0.30 * sx, -0.075, 1.10], [0.33 * sx, -0.06, 1.12]],
                  'r': [0.012, 0.015], 'nseg': 4, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
spec = {'atlas': 2048, 'texels_per_m': 1100, 'exclude_bones_all': WINGS, 'plates': plates, 'props': props}
json.dump(spec, open(os.path.join(HERE, 'scripts', 'carapace_noble.json'), 'w'), indent=1)
print('SPEC plates', len(plates), 'props', len(props))
