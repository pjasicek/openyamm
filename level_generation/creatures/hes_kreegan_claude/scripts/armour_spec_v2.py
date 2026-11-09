#!/usr/bin/env python3
"""hkr armour v2 (armour pass 2026-10-22; user: the Trooper read as the bare Demon with a few accessories): writes
scripts/armour_trooper.json for make_armour.py, the concept's heavily plated soldier (fam_troopers.png,
07_kreegan_castes.png) on the same per-bone rigid attachments:
- cuirass: a big chest plate (B_Spine2) from the upper stomach to the collar with a V of glowing seams (its upper left
  edge cut back 1.5 cm: the supporting left arm crosses it in Running), a matching back plate; two segmented abdomen lames (B_Spine1, B_Spine) with glow between them, a lower back lame (B_Spine);
- belt (B_Pelvis) and a long pointed front tasset (B_Groin, which swings with the more raised thigh);
- layered pauldrons (main cap on B_<S>_Pauldron + a lower lame over the top of the upper arm on B_<S>_Pauldron2,
  which follows the arm's swing; it replaces v1's upper-arm plate, which lay under it and cut both caps) with big
  spikes (the demon's own shoulder spikes still pierce them), larger forearm guards, the buckler emitter larger;
- broad thigh plates over the front and outer side of the thighs, knee caps and shin greaves down to the ankle
  (B_<S>_Calf), tier B's black carapace pauldrons rescaled over the new pauldrons and nested outside the lame (it
  turns with the arm under them).
The skin exclusions are those of v1 (the arms and fingers for torso plates, the tail everywhere). Args: none"""
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
plates = [
    # cuirass front: z 1.17 (upper stomach) .. 1.48 (collar), widest over the ribs; a V of seams to a glowing sternum
    plane('chest', 'B_Spine2', 'front', [1.175, 1.47], [[1.175, 0.100], [1.23, 0.104], [1.30, 0.108], [1.38, 0.124],
          [1.44, 0.126], [1.47, 0.090]], 9, 7, 0.012, 0.016, 0.006,
          half_l=[[1.175, 0.100], [1.23, 0.100], [1.30, 0.092], [1.38, 0.102], [1.44, 0.118], [1.47, 0.088]],
          glow=[[[0.5, 0.06], [0.30, 0.50], [0.16, 0.92]], [[0.5, 0.06], [0.70, 0.50], [0.84, 0.92]], [[0.5, 0.06], [0.5, 0.62]]],
          studs=[[0.24, 0.80], [0.76, 0.80], [0.5, 0.80], [0.34, 0.30], [0.66, 0.30]], lip=0.007, excl=TORSO_X, stud_r=0.010),
    plane('back', 'B_Spine2', 'back', [1.20, 1.50], [[1.20, 0.13], [1.25, 0.16], [1.38, 0.17], [1.46, 0.16], [1.50, 0.11]],
          8, 6, 0.022, 0.016, 0.020, glow=[[[0.5, 0.08], [0.5, 0.92]], [[0.2, 0.55], [0.5, 0.75], [0.8, 0.55]]],
          studs=[[0.25, 0.75], [0.75, 0.75], [0.3, 0.3], [0.7, 0.3]], lip=0.007, excl=TORSO_X),
    # abdomen lames: the upper on B_Spine1, the lower on B_Spine; 1 cm apart, glowing seams along their edges
    plane('abdomen_u', 'B_Spine', 'front', [1.106, 1.136], [[1.106, 0.098], [1.136, 0.100]], 7, 3, 0.016, 0.012, 0.008,
          glow=[[[0.08, 0.15], [0.92, 0.15]]], excl=TORSO_X, lip=0.004),
    plane('abdomen_l', 'B_Spine', 'front', [1.066, 1.094], [[1.066, 0.098], [1.094, 0.098]], 7, 3, 0.016, 0.012, 0.008,
          glow=[[[0.08, 0.15], [0.92, 0.15]]], excl=TORSO_X, lip=0.004),
    plane('back_low', 'B_Spine', 'back', [1.06, 1.125], [[1.06, 0.11], [1.125, 0.115]], 7, 3, 0.022, 0.012, 0.012,
          excl=TORSO_X + TAIL, lip=0.004, paint_studs=[[0.3, 0.5], [0.7, 0.5]]),
    plane('belt', 'B_Pelvis', 'front', [0.955, 1.016], [[0.955, 0.115], [0.98, 0.140], [1.0, 0.150], [1.016, 0.144]], 9, 4, 0.022,
          0.012, 0.014, excl=ARMS + TAIL, lip=0.005, paint_studs=[[0.2, 0.5], [0.8, 0.5]],
          glow=[[[0.06, 0.82], [0.94, 0.82]]]),
    # the long front tasset: from under the belt to the knees, pointed (concept)
    plane('groin', 'B_Groin', 'front', [0.665, 0.885], [[0.665, 0.016], [0.72, 0.038], [0.80, 0.052], [0.885, 0.068]],
          5, 7, 0.039, 0.010, 0.012, excl=ARMS + TAIL, lip=0.005, smooth=14, flat_rows=True,
          glow=[[[0.5, 0.12], [0.5, 0.88]]], studs=[[0.5, 0.82]]),
]
# limbs (left tables; the right mirrored). Cyl u: 0 = front (ref -Y), positive toward the bone frame's s axis.
for s in 'LR':
    m = (lambda tab: tab) if s == 'L' else mirror_angles
    sx = 1 if s == 'L' else -1
    spike_bone = 'Bone_041' if s == 'L' else 'Bone_036'
    plates += [
        cap(f'pauldron_{s}', f'B_{s}_Pauldron', [0.21 * sx, -0.185, 1.37], [1.0 * sx, 0, 0.55], [-0.60, 0.72],
            [[-0.60, D(54)], [0.3, D(68)], [0.72, D(44)]], 8, 7, 0.058, 0.016, [f'B_{s}_Clavicle', f'B_{s}_UpperArm'],
            [spike_bone], 0.16, glow=[[[0.12, 0.16], [0.5, 0.08], [0.88, 0.16]]], studs=[[0.3, 0.45], [0.7, 0.45]]),
        cap(f'pauldron2_{s}', f'B_{s}_Pauldron2', [0.21 * sx, -0.185, 1.37], [1.0 * sx, 0, 0.55], [-0.98, -0.62],
            [[-0.98, D(55)], [-0.62, D(60)]], 7, 3, 0.088, 0.012, [f'B_{s}_Clavicle', f'B_{s}_UpperArm'],
            [spike_bone], 0.18, lip=0.005, glow=[[[0.1, 0.8], [0.9, 0.8]]]),
        cyl(f'forearm_{s}', f'B_{s}_Forearm', [0.30, 0.68], m([[0.30, D(-185), D(5)], [0.68, D(-175), D(-5)]]) if s == 'L' else
            [[0.30, D(40), D(185)], [0.68, D(40), D(175)]],                  # right: a front gap for the carbine's stock
            7, 6, 0.016, 0.011, [f'B_{s}_Forearm', f'B_{s}_UpperArm'], exclude_pieces=[7, 8, 9, 10, 11, 12, 13, 16, 18],
            glow=[[[0.5, 0.10], [0.5, 0.90]]], studs=[[0.25, 0.5], [0.75, 0.5]]),
        cyl(f'thigh_{s}', f'B_{s}_Thigh', [0.28, 0.70], m([[0.28, D(-115), D(-50)], [0.45, D(-135), D(-15)], [0.55, D(-125), D(-12)], [0.70, D(-105), D(-25)]]),
            7, 6, 0.020, 0.012, [f'B_{s}_Thigh', f'B_{s}_Calf'], lip=0.006,
            glow=[[[0.42, 0.12], [0.44, 0.88]]], studs=[[0.72, 0.25], [0.72, 0.7]]),
        cap(f'knee_{s}', f'B_{s}_Calf', [0.149 * sx, -0.216, 0.529], [0, -1.0, 0.15], [-0.65, 0.0],
            [[-0.65, D(48)], [0.0, D(44)]], 6, 5, 0.030, 0.012, [f'B_{s}_Calf', f'B_{s}_Thigh'], [], 0.12, lip=0.006,
            win=[D(22), D(22)], studs=[[0.5, 0.5]]),
        cyl(f'shin_{s}', f'B_{s}_Calf', [0.18, 0.84], m([[0.18, D(-80), D(80)], [0.84, D(-70), D(70)]]),
            7, 6, 0.016, 0.011, [f'B_{s}_Calf'], lip=0.006,
            glow=[[[0.5, 0.15], [0.5, 0.85]]], studs=[[0.5, 0.06]]),
        # tier B: the black carapace replaces the ivory cap (same shape, a hair larger; the lame turns under both)
        cap(f'carapace_{s}', f'B_{s}_Carapace', [0.21 * sx, -0.185, 1.37], [1.0 * sx, 0, 0.55], [-0.60, 0.72],
            [[-0.60, D(54)], [0.3, D(68)], [0.72, D(44)]], 8, 7, 0.062, 0.016, [f'B_{s}_Clavicle', f'B_{s}_UpperArm'],
            [spike_bone], 0.18, style='carapace', tier='b', glow=[[[0.05, 0.12], [0.5, 0.05], [0.95, 0.12]]]),
    ]
props = [
    {'name': 'crest', 'bone': 'B_Head', 'kind': 'loft', 'ctrl': [[0, -0.345, 1.615], [0, -0.36, 1.67], [0, -0.345, 1.73], [0, -0.3, 1.79]],
     'r': [0.012, 0.03], 'nseg': 5, 'sides': 6, 'taper': 0.9, 'style': 'spike'},
    {'name': 'buckler', 'bone': 'B_L_Buckler', 'kind': 'disc', 'v': 0.34, 'normal': [0.75, 0.15, -0.25], 'R': 0.13,
     't': 0.032, 'gap': 0.06, 'seg': 14, 'frame_bone': 'B_L_Forearm'},
]
for s in 'LR':
    sx = 1 if s == 'L' else -1
    # two big spikes per pauldron, rooted inside its crown, rising up and out (concept); on B_<S>_Spikes (rides the
    # pauldron) so tier B keeps them over its carapace
    props.append({'name': f'pspike_{s}', 'bone': f'B_{s}_Spikes', 'kind': 'loft',
                  'ctrl': [[0.29 * sx, -0.165, 1.555], [0.31 * sx, -0.165, 1.63], [0.34 * sx, -0.16, 1.70], [0.39 * sx, -0.14, 1.76]],
                  'r': [0.026, 0.032], 'nseg': 5, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
    props.append({'name': f'pspike2_{s}', 'bone': f'B_{s}_Spikes', 'kind': 'loft',
                  'ctrl': [[0.37 * sx, -0.15, 1.475], [0.42 * sx, -0.15, 1.52], [0.47 * sx, -0.145, 1.56], [0.52 * sx, -0.13, 1.585]],
                  'r': [0.020, 0.024], 'nseg': 4, 'sides': 6, 'taper': 1.0, 'style': 'spike'})
spec = {'atlas': 2048, 'texels_per_m': 900, 'exclude_bones_all': TAIL, 'plates': plates, 'props': props}
json.dump(spec, open(os.path.join(HERE, 'scripts', 'armour_trooper.json'), 'w'), indent=1)
print('SPEC plates', len(plates), 'props', len(props))
