"""Shared rig tables, Lich King (from the Evil Sorcerer's). MM9's LICHKING skeleton has no left Hand bone: L Finger0 is the left wrist (it carries
the palm in MM9). The right hand is Bip01 R Hand (the staff bone Bone01 hangs under it). Our five-finger chains hang under the wrist bone of each side."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
def wrist(s): return 'Bip01 L Finger0' if s == 'L' else 'Bip01 R Hand'
# front panel (tabard): hinge heights (Blender z) of the link bones, top link first; chained under the Pelvis
PANELS = {'F': (0.90, 0.74, 0.58, 0.44)}
def panel_bones(k): return [f'XPanel{k}{i + 1}' for i in range(len(PANELS[k]))]
# coat: hinge sectors round the body (azimuth in degrees from the back, +x = 90), two links each (belt, knee)
COAT = {'SFR': 135.0, 'SR': 90.0, 'BR': 40.0, 'B': 0.0, 'BL': -40.0, 'SL': -90.0, 'SFL': -135.0}
COAT_Z = (0.93, 0.52)
def coat_bones(k): return [f'XCoat{k}1', f'XCoat{k}2']
def bone_table(J, F):
    """name -> (parent, head, tail) in the Blender frame, deforming bones of the body."""
    B = {}
    chain = ['Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head']
    for a, b in zip(chain, chain[1:]): B[a] = (None if a == chain[0] else chain[chain.index(a) - 1], J[a], J[b])
    h = J['Bip01 Head']; B['Bip01 Head'] = ('Bip01 Neck', h, [h[0], h[1], h[2] + 0.2])
    for s in SIDES:
        pre = f'Bip01 {s} '
        mir = -1 if s == 'L' else 1
        wr = wrist(s)
        B[pre + 'Clavicle'] = ('Bip01 Neck', J[pre + 'Clavicle'], J[pre + 'UpperArm'])
        B[pre + 'UpperArm'] = (pre + 'Clavicle', J[pre + 'UpperArm'], J[pre + 'Forearm'])
        B[pre + 'Forearm'] = (pre + 'UpperArm', J[pre + 'Forearm'], J[pre + 'Hand'])
        m = F['Middle'][0]
        B[wr] = (pre + 'Forearm', J[pre + 'Hand'], [m[0] * mir, m[1], m[2]])
        B[pre + 'Thigh'] = ('Bip01 Spine', J[pre + 'Thigh'], J[pre + 'Calf'])
        B[pre + 'Calf'] = (pre + 'Thigh', J[pre + 'Calf'], J[pre + 'Foot'])
        t = J[pre + 'Toe0']
        B[pre + 'Foot'] = (pre + 'Calf', J[pre + 'Foot'], t)
        for f in FINGERS:
            P = [[p[0] * mir, p[1], p[2]] for p in F[f]]
            for k in range(3):
                B[f'{pre}{f}{k + 1}'] = (wr if k == 0 else f'{pre}{f}{k}', P[k], P[k + 1])
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
