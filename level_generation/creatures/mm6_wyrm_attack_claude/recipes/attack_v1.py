# Wyrm (DragonLand) mm6_wyrm Attack v1 (attacks-2, 2026-11-11). Faces +Z, +Y up. Native drr1at a-e (front view
# only): the head rears up, the jaws open wide, then it bites/breathes at the target (the flash) and settles. Layered
# over the installed clip (jaw and head keys kept): wind-up 0-0.45 s (the body sits back 3 cm, chest rises, the neck
# coils up and back, the tail lifts and curls), strike 0.45-0.62 s (the body lunges 5 cm forward and the chest drops,
# the neck shoots forward and down, the tail whips), contact 0.626 s (kept), recover by 1.0 s (length kept). The four
# paws stay where the installed clip puts them (two-bone IK).
CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
TAILS = [[f'Tail{i}' for i in range(a, b)] for a, b in ((1, 4), (4, 7), (7, 9), (9, 11))]
PLANT = [('Thigh_L', 'Shin_L', 'HindPaw_L'), ('Thigh_R', 'Shin_R', 'HindPaw_R'),
         ('UpperArm_L', 'ForeArm_L', 'FrontPaw_L'), ('UpperArm_R', 'ForeArm_R', 'FrontPaw_R')]


def tail_wave(axis, keys, groups, delay):
    out = []
    for k, (joints, weight) in enumerate(groups):
        out.append({'joints': {j: weight for j in joints}, 'axis': axis,
                    'keys': [(t + (delay * k if 0 < t < keys[-1][0] else 0), v) for t, v in keys]})
    return out


LAYERS = [
    {'joints': {'Spine1': 1.0, 'Spine2': 1.0, 'Spine3': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.25, -2), (0.45, -4), (0.5, -3.5), (0.62, 3.5), (0.7, 3.5), (0.85, 1.2), (1.0, 0)]},
    {'joints': {'Neck1': 1.0, 'Neck2': 1.0, 'Neck3': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.25, -6), (0.45, -11), (0.5, -10), (0.62, 9), (0.7, 9), (0.86, 3), (1.0, 0)]},
    {'joints': {'Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.45, -8), (0.62, 4), (0.75, 2), (1.0, 0)]},
] + tail_wave(Y, [(0, 0), (0.3, 2.5), (0.5, 4.0), (0.64, -4.0), (0.8, -1.5), (1.0, 0)],
              [(TAILS[0], 0.6), (TAILS[1], 1.0), (TAILS[2], 1.2), (TAILS[3], 1.2)], 0.03) \
  + tail_wave(X, [(0, 0), (0.4, -3.0), (0.6, -1.0), (0.8, -2.0), (1.0, 0)],
              [(TAILS[1], 0.6), (TAILS[2], 1.0), (TAILS[3], 1.2)], 0.03)

MOVES = [
    {'joint': 'Spine1', 'keys': [(0, [0, 0, 0]), (0.45, [0, 0.012, -0.03]), (0.5, [0, 0.01, -0.028]),
                                 (0.62, [0, -0.005, 0.05]), (0.7, [0, -0.005, 0.052]), (0.86, [0, 0, 0.02]),
                                 (1.0, [0, 0, 0])]},
]
