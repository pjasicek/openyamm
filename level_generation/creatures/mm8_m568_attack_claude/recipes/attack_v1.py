# Salamander m568 Attack v1 (attacks-2, 2026-11-11). Faces +Z, +Y up, left +X. The installed clip already carries the
# native action (gather the polearm overhead 0-0.8 s, chop forward-down at 1.0 s, recover); this layers the body on
# it: the column leans back and winds to its right during the gather, the tail tip lifts and curls, then the whole
# column whips forward and down with the chop, lunging 0.25 m, unwinding to its left; recover by 1.333 s (length and
# the 1.0 s contact kept). The Polearm node (animated under Root) follows the chest as in the installed clip.
CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
COLUMN = {f'Serpent_{i:02d}': 1.0 for i in range(0, 9)}
COLUMN.update({'B_Spine': 1.0, 'B_Spine1': 1.0})
TWIST = {f'Serpent_{i:02d}': 1.0 for i in range(0, 7)}
TWIST.update({'B_Spine': 1.0, 'B_Spine1': 1.0, 'B_Spine2': 1.0})
TAIL = [[f'Serpent_{i:02d}' for i in range(a, b)] for a, b in ((14, 17), (17, 20), (20, 23), (23, 26))]
FOLLOW = {'Polearm': 'B_Spine2'}


def tail_wave(axis, keys, groups, delay):
    out = []
    for k, (joints, weight) in enumerate(groups):
        out.append({'joints': {j: weight for j in joints}, 'axis': axis,
                    'keys': [(t + (delay * k if 0 < t < keys[-1][0] else 0), v) for t, v in keys]})
    return out


LAYERS = [
    {'joints': COLUMN, 'axis': X,
     'keys': [(0, 0), (0.3, -1.0), (0.75, -1.7), (0.84, -1.5), (1.0, 3.0), (1.08, 3.2), (1.2, 1.8), (1.333, 0)]},
    {'joints': TWIST, 'axis': Y,
     'keys': [(0, 0), (0.4, -1.8), (0.8, -2.4), (1.0, 1.1), (1.15, 0.6), (1.333, 0)]},
    {'joints': {'B_Neck': 1.0, 'B_Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.75, 7), (0.9, 4), (1.0, -12), (1.15, -9), (1.333, 0)]},
] + tail_wave(Y, [(0, 0), (0.4, 1.5), (0.8, 2.5), (1.0, -2.5), (1.15, -1.0), (1.333, 0)],
              [(TAIL[0], 0.6), (TAIL[1], 1.0), (TAIL[2], 1.2), (TAIL[3], 1.2)], 0.03) \
  + tail_wave(X, [(0, 0), (0.5, 2.0), (0.85, 3.0), (1.0, 0.0), (1.2, 1.0), (1.333, 0)],
              [(TAIL[1], 0.5), (TAIL[2], 1.0), (TAIL[3], 1.4)], 0.03)

MOVES = [
    {'joint': 'Root', 'keys': [(0, [0, 0, 0]), (0.75, [0, 0, -0.08]), (0.98, [0, 0, 0.25]), (1.1, [0, 0, 0.27]),
                               (1.25, [0, 0, 0.09]), (1.333, [0, 0, 0])]},
]
