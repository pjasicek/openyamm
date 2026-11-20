# Water Elemental m500 (= mm7_m210) Attack v4 (attacks-2, 2026-11-11). Faces +Z, +Y up, left +X. Native m500aa-ah:
# arms flare wide, the column rises back, then surges forward with both palms thrust out (the burst), tail fin lashing.
# Layers over the installed clip (its palms-forward push at 0.8 s kept): wind-up 0-0.62 s (column leans back 25°,
# arms flare up and out, head back, tail coils and the caudal fin rises), surge 0.66-0.875 s (column whips forward,
# lunge 0.3 m, palms driven forward), contact 0.875 s (kept), hold, recover by 1.375 s (length kept: regression).
CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
SPINE = {'Spine_01': 0.3, 'Spine_02': 0.9, 'Spine_03': 1.0, 'Spine_04': 1.0, 'Spine_05': 0.8, 'Spine_06': 0.6}
TAIL = [[f'Tail_{i:02d}' for i in range(a, b)] for a, b in ((0, 6), (6, 12), (12, 18), (18, 26))]


def tail_wave(axis, keys, groups, delay):
    out = []
    for k, (joints, weight) in enumerate(groups):
        out.append({'joints': {j: weight for j in joints}, 'axis': axis,
                    'keys': [(t + (delay * k if 0 < t < keys[-1][0] else 0), v) for t, v in keys]})
    return out


LAYERS = [
    {'joints': SPINE, 'axis': X,
     'keys': [(0, 0), (0.25, -2.0), (0.6, -5.0), (0.68, -4.5), (0.86, 6.5), (0.94, 7.0), (1.1, 4.5), (1.3, 1.0),
              (1.375, 0)]},
    {'joints': {'Neck': 1.0, 'Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.6, -7), (0.75, -4), (0.88, -3), (1.05, -2), (1.3, 0), (1.375, 0)]},
    {'joints': {'L_Arm': 1.0, 'R_Arm': -1.0}, 'axis': Z,
     'keys': [(0, 0), (0.3, 24), (0.55, 32), (0.7, 10), (0.86, -4), (1.05, -2), (1.3, 0), (1.375, 0)]},
    {'joints': {'L_Arm': 1.0, 'R_Arm': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.4, 8), (0.62, 14), (0.75, 0), (0.88, 0), (1.05, 0), (1.3, 0), (1.375, 0)]},
] + tail_wave(Y, [(0, 0), (0.3, 0.8), (0.62, 1.4), (0.86, -1.6), (1.02, -0.8), (1.25, 0.2), (1.375, 0)],
              [(TAIL[0], 0.5), (TAIL[1], 1.0), (TAIL[2], 1.2), (TAIL[3], 1.2)], 0.035) \
  + tail_wave(X, [(0, 0), (0.4, 1.5), (0.7, 2.6), (0.9, -0.5), (1.1, 0.8), (1.375, 0)],
              [(TAIL[1], 0.4), (TAIL[2], 1.0), (TAIL[3], 1.3)], 0.035)

MOVES = [
    {'joint': 'Root', 'keys': [(0, [0, 0, 0]), (0.6, [0, 0, -0.1]), (0.86, [0, 0.035, 0.28]), (0.96, [0, 0.035, 0.3]),
                               (1.15, [0, 0.015, 0.14]), (1.375, [0, 0, 0])]},
]
