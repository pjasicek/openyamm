#!/usr/bin/env python3
"""hkr armour v4 (bulky Trooper, 2026-10-22): v3's skinned shell route on the bulked caste body (bulk_body.py), with
a big rounded barrel cuirass standing further off, full thigh plates, two tassets riding their thighs (no central
tasset: it met the raised thigh plate in Running), larger caps and spikes. v3 notes follow. Writes
scripts/armour_trooper.json for
make_armour.py and skin_shell.py. The torso and limb plates are a SKINNED shell (spec key `shell`: skin_shell.py
transfers the body's weights to each piece, smooths them over the piece and blends them toward the piece's mean by
`rigid`, so a piece moves like armour and bending happens in the gaps between pieces); they stay in the Trooper caste
GLB's skinned mesh and the skin under each piece's interior is removed there. Rigid attachments remain only for the
small parts: pauldron caps + spikes (tier B: black carapace caps), crest, buckler, the swinging tasset (B_Groin) and
the carbine. Pieces (concept fam_troopers.png, 07_kreegan_castes.png):
- cuirass: chest plate (its upper left edge cut back for the supporting arm) and back plate, two abdomen lames and a
  lower back lame, belt;
- legs: a hip lame and a broad thigh plate over the front and sides, knee cap, shin greave to the ankle;
- arms: an upper-arm plate under the pauldron cap, a forearm guard (the right one with a front gap for the stock).
v2 (rigid plates, armour_spec_v2.py) and v3 (armour_spec_v3.py, the first shell) are history. Args: none"""
import json, math, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = ['B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand'] + \
       [f'B_{s}_Finger{a}{b}' for s in 'LR' for a in range(5) for b in ('', '1', '2')] + ['B_R_Finger0.001', 'B_R_Finger0.002']
HEAD = ['B_Head', 'Bone_025', 'headfront', 'B_Neck', 'Bone_041', 'Bone_036']
TAIL = ['Bone_020', 'Bone_019', 'Bone_018', 'Bone_017', 'Bone_016', 'Bone_015']
D = math.radians


def sym(tab):
    return [[v, -w] for v, w in tab], [[v, w] for v, w in tab]


def plane(name, bone, side, v, half, nu, nv, off, t, crown, glow=(), studs=(), lip=0.006, excl=(), half_l=None, **kw):
    kw.setdefault('shell', {'rigid': 1.0})
    lo, hi = sym(half)
    if half_l is not None:                      # the left (+x) edge's own half widths (cut back for the support arm)
        hi = [[v_, w] for v_, w in half_l]
    p = {'name': name, 'bone': bone, 'kind': 'plane', 'side': side, 'v': v, 'nu': nu, 'nv': nv, 'off': off, 't': t,
         'lip': lip, 'exclude_bones': list(excl), 'crown': crown, 'lo': lo, 'hi': hi}
    if glow: p['glow'] = glow
    if studs: p['studs'] = studs
    p.update(kw)
    return p


def mirror_angles(tab):
    """a left-limb angle table [[v, lo, hi]] -> the right limb's (u mirrored: -hi .. -lo)"""
    return [[v, -h, -l] for v, l, h in tab]


def cyl(name, bone, v, tab, nu, nv, off, t, include, ref=(0, -1, 0), **kw):
    p = {'name': name, 'bone': bone, 'kind': 'cyl', 'ref': list(ref), 'v': v, 'nu': nu, 'nv': nv, 'off': off, 't': t,
         'lip': kw.pop('lip', 0.005), 'include_bones': include,
         'lo': [[a, l] for a, l, h in tab], 'hi': [[a, h] for a, l, h in tab]}
    p.update(kw)
    return p


def cap(name, bone, centre, out, v, az, nu, nv, off, t, include, excl, hmax, **kw):
    p = {'name': name, 'bone': bone, 'kind': 'cap', 'centre': centre, 'out': out, 'v': v, 'nu': nu, 'nv': nv,
         'off': off, 't': t, 'lip': kw.pop('lip', 0.008), 'include_bones': include, 'win': [D(18), D(18)],
         'lo': [[a, -w] for a, w in az], 'hi': [[a, w] for a, w in az], 'hmax': hmax, 'exclude_bones': excl}
    p.update(kw)
    return p


TORSO_X = ARMS + HEAD
CUI = {'rigid': 1.0, 'bones': ['B_Spine2', 'B_Spine1']}
plates = [
    # the barrel cuirass: chest and back plates on one weight set (they move as one), the chest's lower edge rounded
    plane('chest', 'B_Spine2', 'front', [1.142, 1.445], [[1.142, 0.050], [1.165, 0.100], [1.21, 0.135], [1.26, 0.140],
          [1.36, 0.120], [1.42, 0.115], [1.445, 0.080]], 10, 9, 0.020, 0.018, 0.018,
          half_l=[[1.142, 0.050], [1.165, 0.075], [1.21, 0.075], [1.26, 0.074], [1.36, 0.076], [1.42, 0.100], [1.445, 0.072]],
          glow=[[[0.5, 0.06], [0.30, 0.50], [0.16, 0.92]], [[0.5, 0.06], [0.70, 0.50], [0.84, 0.92]], [[0.5, 0.06], [0.5, 0.62]]],
          studs=[[0.24, 0.80], [0.76, 0.80], [0.5, 0.80], [0.34, 0.30], [0.66, 0.30]], lip=0.008, excl=TORSO_X, stud_r=0.011,
          shell=dict(CUI, hide_pieces=[1])),   # P01: the demon's chest ornament, under the plate
    plane('back', 'B_Spine2', 'back', [1.17, 1.51], [[1.17, 0.12], [1.22, 0.16], [1.30, 0.185], [1.42, 0.185], [1.51, 0.13]],
          9, 7, 0.028, 0.018, 0.030, glow=[[[0.5, 0.08], [0.5, 0.92]], [[0.2, 0.55], [0.5, 0.75], [0.8, 0.55]]],
          studs=[[0.25, 0.75], [0.75, 0.75], [0.3, 0.3], [0.7, 0.3]], lip=0.008, excl=TORSO_X, shell=CUI),
    # an abdomen lame under the rounded lower edge, a lower back lame, the belt
    plane('abdomen_u', 'B_Spine', 'front', [1.06, 1.086], [[1.06, 0.068], [1.086, 0.072]], 7, 3, 0.020, 0.012, 0.010,
          glow=[[[0.08, 0.15], [0.92, 0.15]]], excl=TORSO_X, lip=0.004, shell={'rigid': 1.0, 'bones': ['B_Spine']}),
    # (no lower abdomen lame: the lowered gun's fist rests on the belly centre at the end of Fidget)
    plane('back_low', 'B_Spine', 'back', [1.03, 1.085], [[1.03, 0.12], [1.085, 0.13]], 7, 3, 0.024, 0.012, 0.012,
          excl=TORSO_X + TAIL, lip=0.004, paint_studs=[[0.3, 0.5], [0.7, 0.5]]),
    plane('belt', 'B_Pelvis', 'front', [0.972, 1.006], [[0.972, 0.068], [0.99, 0.090], [1.006, 0.100]], 8, 4, 0.022,
          0.012, 0.014, excl=ARMS + TAIL, lip=0.005, paint_studs=[[0.2, 0.5], [0.8, 0.5]],
          shell={'rigid': 1.0, 'bones': ['B_Pelvis', 'B_Spine']}, glow=[[[0.06, 0.82], [0.94, 0.82]]]),
]
# limbs (left tables; the right mirrored). Cyl u: 0 = front (ref -Y), positive toward the bone frame's s axis.
C0 = [0.21, -0.185, 1.37]                                 # the cap centre (left; x mirrored)
for s in 'LR':
    m = (lambda tab: tab) if s == 'L' else mirror_angles
    sx = 1 if s == 'L' else -1
    spike_bone = 'Bone_041' if s == 'L' else 'Bone_036'
    sh = lambda r, b=None: {'rigid': r, **({'bones': b} if b else {})}
    cap_az = [[-0.46, D(50)], [0.2, D(58)], [0.50, D(34)]]
    plates += [
        cap(f'pauldron_{s}', f'B_{s}_Pauldron', [C0[0] * sx, C0[1], C0[2]], [1.0 * sx, 0, 0.55], [-0.46, 0.50],
            cap_az, 9, 8, 0.075, 0.018, [f'B_{s}_Clavicle', f'B_{s}_UpperArm'],
            [spike_bone], 0.18, glow=[[[0.12, 0.16], [0.5, 0.08], [0.88, 0.16]]], studs=[[0.3, 0.45], [0.7, 0.45]]),
        # tier B: the black carapace replaces the ivory cap (same shape, a hair larger)
        cap(f'carapace_{s}', f'B_{s}_Carapace', [C0[0] * sx, C0[1], C0[2]], [1.0 * sx, 0, 0.55], [-0.46, 0.50],
            cap_az, 9, 8, 0.079, 0.018, [f'B_{s}_Clavicle', f'B_{s}_UpperArm'],
            [spike_bone], 0.18, style='carapace', tier='b', glow=[[[0.05, 0.12], [0.5, 0.05], [0.95, 0.12]]]),
        # the upper-arm plate under the cap (skinned: it follows the arm's twist)
        cyl(f'upperarm_{s}', f'B_{s}_UpperArm', [0.74, 0.88], m([[0.74, D(-165), D(-50)], [0.88, D(-165), D(-35)]]),
            6, 5, 0.012, 0.011, [f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist', f'B_{s}_Clavicle'], lip=0.005,
            glow=[[[0.5, 0.12], [0.5, 0.88]]], shell=sh(1.0, [f'B_{s}_UpperArm', f'B_{s}_UpperArmTwist'])),
        cyl(f'forearm_{s}', f'B_{s}_Forearm', [0.26, 0.76], m([[0.26, D(-185), D(5)], [0.76, D(-175), D(-5)]]) if s == 'L' else
            [[0.26, D(70), D(185)], [0.76, D(70), D(175)]],                  # right: a front gap for the carbine's stock
            7, 6, 0.018, 0.012, [f'B_{s}_Forearm', f'B_{s}_ForearmTwist', f'B_{s}_UpperArm'],
            exclude_pieces=[7, 8, 9, 10, 11, 12, 13, 16, 18],
            glow=[[[0.5, 0.10], [0.5, 0.90]]], studs=[[0.25, 0.5], [0.75, 0.5]], shell=sh(1.0, [f'B_{s}_Forearm'])),
        # the full thigh plate over the front and sides, under its own tasset
        cyl(f'thigh_{s}', f'B_{s}_Thigh', [0.38, 0.75], m([[0.38, D(-150), D(-10)], [0.55, D(-125), D(40)], [0.75, D(-95), D(35)]]),
            9, 7, 0.022, 0.012, [f'B_{s}_Thigh', f'B_{s}_Calf'], lip=0.006,
            glow=[[[0.40, 0.12], [0.42, 0.88]]], studs=[[0.72, 0.25], [0.72, 0.7]], shell=sh(1.0, [f'B_{s}_Thigh'])),
        cap(f'knee_{s}', f'B_{s}_Calf', [0.149 * sx, -0.216, 0.529], [0, -1.0, 0.15], [-0.65, -0.15],
            [[-0.65, D(50)], [-0.15, D(46)]], 6, 5, 0.030, 0.013, [f'B_{s}_Calf', f'B_{s}_Thigh'], [], 0.13, lip=0.006,
            win=[D(22), D(22)], studs=[[0.5, 0.5]], shell=sh(1.0, [f'B_{s}_Calf'])),
        cyl(f'shin_{s}', f'B_{s}_Calf', [0.16, 0.80], m([[0.16, D(-90), D(50)], [0.80, D(-80), D(20)]]),
            7, 6, 0.018, 0.012, [f'B_{s}_Calf', f'B_{s}_Foot'], lip=0.006,
            glow=[[[0.5, 0.15], [0.5, 0.85]]], studs=[[0.5, 0.06]], shell=sh(1.0, [f'B_{s}_Calf'])),
    ]
    # the tasset riding its thigh over the upper thigh front and side (rounded lower edge), layered above the thigh
    # plate's top; a hinged tasset was tried: the 68 deg knee drive raises the thigh's front through any hinge under the belt
    plates.append(cyl(f'tasset_{s}', f'B_{s}_Thigh', [0.14, 0.37], m([[0.14, D(-115), D(-25)], [0.22, D(-125), D(-15)],
                      [0.30, D(-110), D(-5)], [0.37, D(-80), D(-10)]]), 7, 6, 0.030, 0.012, [f'B_{s}_Thigh'], lip=0.006,
                      glow=[[[0.5, 0.15], [0.5, 0.85]]], studs=[[0.5, 0.82]], shell=sh(1.0, [f'B_{s}_Thigh'])))
props = [
    {'name': 'crest', 'bone': 'B_Head', 'kind': 'loft', 'ctrl': [[0, -0.345, 1.615], [0, -0.36, 1.67], [0, -0.345, 1.73], [0, -0.3, 1.79]],
     'r': [0.012, 0.03], 'nseg': 5, 'sides': 6, 'taper': 0.9, 'style': 'spike'},
    {'name': 'buckler', 'bone': 'B_L_Buckler', 'kind': 'disc', 'v': 0.34, 'normal': [0.75, 0.15, -0.25], 'R': 0.135,
     't': 0.032, 'gap': 0.065, 'seg': 14, 'frame_bone': 'B_L_Forearm'},
]
GROW = 1.12                                              # the spikes grow with the caps (from the cap centre)
for s in 'LR':
    sx = 1 if s == 'L' else -1
    cen = [C0[0] * sx, C0[1], C0[2]]
    g = lambda pts: [[c + (p - c) * GROW for p, c in zip(q, cen)] for q in pts]
    # two big spikes per cap, rooted inside its crown, rising up and out (concept); on B_<S>_Spikes (rides the cap)
    props.append({'name': f'pspike_{s}', 'bone': f'B_{s}_Spikes', 'kind': 'loft',
                  'ctrl': g([[0.29 * sx, -0.165, 1.555], [0.31 * sx, -0.165, 1.63], [0.34 * sx, -0.16, 1.70], [0.39 * sx, -0.14, 1.76]]),
                  'r': [0.030, 0.036], 'nseg': 5, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
    props.append({'name': f'pspike2_{s}', 'bone': f'B_{s}_Spikes', 'kind': 'loft',
                  'ctrl': g([[0.37 * sx, -0.15, 1.475], [0.42 * sx, -0.15, 1.52], [0.47 * sx, -0.145, 1.56], [0.52 * sx, -0.13, 1.585]]),
                  'r': [0.023, 0.028], 'nseg': 4, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
spec = {'atlas': 2048, 'texels_per_m': 900, 'exclude_bones_all': TAIL, 'plates': plates, 'props': props}
json.dump(spec, open(os.path.join(HERE, 'scripts', 'armour_trooper.json'), 'w'), indent=1)
print('SPEC plates', len(plates), 'props', len(props))
