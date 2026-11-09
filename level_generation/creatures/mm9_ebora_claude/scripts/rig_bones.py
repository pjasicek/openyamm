"""Shared rig tables (Ebora; from mm9_evilsorcerer_claude/scripts/rig_bones.py, no panels)."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
WING_L = ['Bone48', 'Bone49', 'Bone50', 'Bone53', 'Bone54', 'Bone55', 'Bone58', 'Bone59', 'Bone62', 'Bone63', 'Bone66', 'Bone69']
WING_R = ['Bone13', 'Bone14', 'Bone15', 'Bone18', 'Bone19', 'Bone20', 'Bone26', 'Bone27', 'Bone10', 'Bone11', 'Bone46', 'Bone34']


def bone_table(J, F):
    """name -> (parent, head, tail) in the Blender frame, deforming bones of the body (heat weights)."""
    B = {}
    chain = ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head']
    for a, b in zip(chain, chain[1:]): B[a] = (None if a == chain[0] else chain[chain.index(a) - 1], J[a], J[b])
    h = J['Bip01 Head']; B['Bip01 Head'] = ('Bip01 Neck', h, [h[0], h[1], h[2] + 0.2])
    for s in SIDES:
        pre = f'Bip01 {s} '
        mir = -1 if s == 'L' else 1
        B[pre + 'Clavicle'] = ('Bip01 Neck', J[pre + 'Clavicle'], J[pre + 'UpperArm'])
        B[pre + 'UpperArm'] = (pre + 'Clavicle', J[pre + 'UpperArm'], J[pre + 'Forearm'])
        B[pre + 'Forearm'] = (pre + 'UpperArm', J[pre + 'Forearm'], J[pre + 'Hand'])
        m = F['Middle'][0]
        B[pre + 'Hand'] = (pre + 'Forearm', J[pre + 'Hand'], [m[0] * mir, m[1], m[2]])
        B[pre + 'Thigh'] = ('Bip01 Pelvis', J[pre + 'Thigh'], J[pre + 'Calf'])
        B[pre + 'Calf'] = (pre + 'Thigh', J[pre + 'Calf'], J[pre + 'Foot'])
        B[pre + 'Foot'] = (pre + 'Calf', J[pre + 'Foot'], J[pre + 'Toe0'])
        t = J[pre + 'Toe0']
        B[pre + 'Toe0'] = (pre + 'Foot', t, [t[0], t[1] - 0.08, t[2]])
        for f in FINGERS:
            P = [[p[0] * mir, p[1], p[2]] for p in F[f]]
            for k in range(3):
                B[f'{pre}{f}{k + 1}'] = (pre + 'Hand' if k == 0 else f'{pre}{f}{k}', P[k], P[k + 1])
    return B


def half_pairs():
    """Half-way helpers at the joints that fold: (helper, child bone, helper's node parent, weight bones of the parent side)."""
    out = []
    for s in SIDES:
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine3', 'Bip01 Spine2')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
        out.append((pre + 'XhalfThigh', pre + 'Thigh', 'Bip01 Spine', ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1')))
        out.append((pre + 'XhalfCalf', pre + 'Calf', pre + 'Thigh', (pre + 'Thigh',)))
    out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck',)))
    return out
