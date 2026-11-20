# Serpentmen m524 Attack v4 (attacks-2, 2026-11-11): native aa-ag rear-and-strike. Model faces +Z, +Y up, left +X.
# Wind-up 0-0.36 s: column leans back, arms spread wide, head back, jaw opens, tail curls; strike 0.38-0.56 s: column
# whips forward and down, lunges 0.3 m, arms reach; contact ~0.56 s; hold low; recover by 1.125 s (length kept).
CLIP = 'Attack'
SOURCE = 'Attack'

SPINE = {'Spine_01': 0.6, 'Spine_02': 1.0, 'Spine_03': 1.0, 'Spine_04': 1.0, 'Spine_05': 0.8, 'Spine_06': 0.6}
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]


def tail_wave(axis, keys, groups, delay):
    layers = []
    for k, (joints, weight) in enumerate(groups):
        layers.append({'joints': {j: weight for j in joints}, 'axis': axis,
                       'keys': [(t + (delay * k if 0 < t < keys[-1][0] else 0), v) for t, v in keys]})
    return layers


TAIL = [[f'Tail_{i:02d}' for i in range(a, b)] for a, b in ((0, 6), (6, 12), (12, 18), (18, 26))]

LAYERS = [
    {'joints': SPINE, 'axis': X,
     'keys': [(0, 0), (0.12, -1.5), (0.36, -6), (0.4, -5.5), (0.56, 7.5), (0.64, 8), (0.8, 5.5), (0.98, 1.5),
              (1.125, 0)]},
    {'joints': {'Neck': 1.0, 'Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.36, -9), (0.48, -8), (0.58, -7), (0.7, -5), (0.95, -1), (1.125, 0)]},
    {'joints': {'Jaw': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.24, 9), (0.4, 26), (0.56, 30), (0.72, 14), (0.92, 0), (1.125, 0)]},
    {'joints': {'L_Arm': 1.0, 'R_Arm': -1.0}, 'axis': Z,
     'keys': [(0, 0), (0.36, 32), (0.48, 14), (0.58, -6), (0.74, -4), (0.98, 0), (1.125, 0)]},
    {'joints': {'L_Arm': 1.0, 'R_Arm': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.36, 14), (0.48, -10), (0.58, -36), (0.74, -28), (0.98, -4), (1.125, 0)]},
    {'joints': {'L_Forearm': 1.0, 'R_Forearm': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.36, 10), (0.58, -18), (0.78, -10), (1.125, 0)]},
] + tail_wave(Y, [(0, 0), (0.2, 0.7), (0.36, 1.0), (0.54, -1.2), (0.68, -0.7), (0.88, 0.3), (1.125, 0)],
              [(TAIL[0], 0.6), (TAIL[1], 1.0), (TAIL[2], 1.2), (TAIL[3], 1.2)], 0.04) \
  + tail_wave(X, [(0, 0), (0.3, 1.5), (0.54, 0.3), (0.72, 1.2), (1.125, 0)],
              [(TAIL[2], 0.3), (TAIL[3], 1.0)], 0.05)

MOVES = [
    {'joint': 'Root', 'keys': [(0, [0, 0, 0]), (0.36, [0, 0, -0.1]), (0.54, [0, 0, 0.28]), (0.64, [0, 0, 0.3]),
                               (0.82, [0, 0, 0.2]), (1.0, [0, 0, 0.03]), (1.125, [0, 0, 0])]},
]
