"""Shared rig tables (Monk)."""
SIDES = ('L', 'R')
FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
def half_pairs():
    """Half-way helpers at the joints that fold: (helper, child bone, helper's node parent, weight bones of the parent side)."""
    out = []
    for s in SIDES:
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine3', 'Bip01 Spine2')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
    out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck',)))
    return out
