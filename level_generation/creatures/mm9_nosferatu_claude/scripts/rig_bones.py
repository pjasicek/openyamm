"""Shared rig tables (Nosferatu)."""
SIDES = ('L', 'R')
ROBE_ROWS = (0.88, 0.60, 0.30, 0.0)      # lattice rows, Blender z of the robe grid
ROBE_COLS = 12
def robe_bone(c, r): return f'XRobe{c:02d}_{r}'
def robe_names(): return [robe_bone(c, r) for c in range(ROBE_COLS) for r in range(len(ROBE_ROWS))]
def half_pairs():
    """(helper, child bone, helper's node parent, weight bones of the parent side)"""
    out = []
    for s in SIDES:
        pre = f'Bip01 {s} '
        out.append((pre + 'XhalfUpperArm', pre + 'UpperArm', pre + 'Clavicle', (pre + 'Clavicle', 'Bip01 Spine2')))
        out.append((pre + 'XhalfForearm', pre + 'Forearm', pre + 'UpperArm', (pre + 'UpperArm',)))
    out.append(('Bip01 XhalfHead', 'Bip01 Head', 'Bip01 Neck', ('Bip01 Neck',)))
    return out
