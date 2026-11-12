# Medusa m282 Attack v3 (attacks-2, 2026-11-11). Faces +Z, +Y up, left +X. Native m282aa-ah: reach over the shoulder
# for an arrow, raise it, nock, draw (held 375 ms), loose, recover; the rattle tail stays raised. The installed clip
# carries the arms, bow and arrow; this layers the body: she leans back as she reaches overhead, then leans and
# glides 0.16 m into the draw, recoils at the loose (1.0 s, kept) with the head snapping back, and the long tail sweeps
# with the draw and shakes its rattle after the shot. Arrow (keyed under Rig) follows the chest. Length 1.5 s kept.
CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
COLUMN = {f'Col_{i:02d}': 1.0 for i in range(1, 8)}
COLUMN['Spine1'] = 0.8
FOLLOW = {'Arrow': 'Spine2'}
TAIL = [[f'Tail_{i:02d}' for i in range(a, b)] for a, b in ((1, 9), (9, 17), (17, 24), (24, 31))]


def tail_wave(axis, keys, groups, delay):
    out = []
    for k, (joints, weight) in enumerate(groups):
        out.append({'joints': {j: weight for j in joints}, 'axis': axis,
                    'keys': [(t + (delay * k if 0 < t < keys[-1][0] else 0), v) for t, v in keys]})
    return out


RATTLE = [(0, 0), (0.9, 0)] + [(0.94 + 0.04 * k, 5.0 * (-1) ** k * (1 - k / 11)) for k in range(11)] + [(1.5, 0)]

LAYERS = [
    {'joints': COLUMN, 'axis': X,
     'keys': [(0, 0), (0.35, -1.3), (0.6, 0.4), (0.92, 1.9), (1.0, 1.9), (1.07, -1.4), (1.2, -0.9), (1.42, 0),
              (1.5, 0)]},
    {'joints': {'Neck': 1.0, 'Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.35, -3), (0.6, 0), (0.98, 1), (1.06, -6), (1.25, -2), (1.5, 0)]},
    {'joints': {f'Tail_{i:02d}': 1.0 for i in range(25, 31)}, 'axis': Y, 'keys': RATTLE},
] + tail_wave(Y, [(0, 0), (0.35, 1.3), (0.9, -1.4), (1.05, -1.7), (1.3, 0.4), (1.5, 0)],
              [(TAIL[0], 0.7), (TAIL[1], 1.0), (TAIL[2], 1.2), (TAIL[3], 1.2)], 0.05) \
  + tail_wave(X, [(0, 0), (0.5, 2.5), (1.0, 3.0), (1.3, 2.0), (1.5, 0)], [(TAIL[2], 0.5), (TAIL[3], 1.5)], 0.04)

MOVES = [
    {'joint': 'Root', 'keys': [(0, [0, 0, 0]), (0.35, [0, 0, -0.04]), (0.92, [0, 0, 0.16]), (1.0, [0, 0, 0.16]),
                               (1.08, [0, 0, -0.06]), (1.3, [0, 0, -0.01]), (1.5, [0, 0, 0])]},
]
FLOOR = {'joint': 'Root', 'min': 0.0}
