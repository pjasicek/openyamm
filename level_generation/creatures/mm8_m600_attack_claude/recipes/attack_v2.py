# Nightmare m600 Attack v2 (attacks-2, 2026-11-11). Faces +Z, +Y up. Native m600AA-Ah: the two jaw necks gape and
# spew a green cloud forward. The installed clip keeps its mouth gape and the user-approved subtle eye-stalk twitches
# (2026-10-18: larger eye motion was rejected), so the eye stalks are not touched. Added: the whole mass rears back
# and both jaw necks coil back (0-0.4 s), then the necks whip forward and down and the mass heaves forward 6 cm into
# the spew (contact 0.563 s, kept), a short shudder while it spews, recover by 1.0 s (length kept). FLOOR keeps the
# slime base on the ground when the mass pitches.
CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
NECKL = {f'NeckL_{i:02d}': 1.0 for i in range(0, 7)}
NECKR = {f'NeckR_{i:02d}': 1.0 for i in range(0, 8)}
NECKS = dict(NECKL, **NECKR)
SHUDDER = [(0.56, 0)] + [(0.6 + 0.04 * k, 1.2 * (-1) ** k * (1 - k / 5)) for k in range(5)] + [(0.82, 0)]

LAYERS = [
    {'joints': {'Body': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.36, -4), (0.42, -3.5), (0.56, 3.5), (0.64, 4), (0.8, 2), (1.0, 0)]},
    {'joints': NECKS, 'axis': X,
     'keys': [(0, 0), (0.36, -2.2), (0.42, -2.0), (0.56, 2.4), (0.64, 2.5), (0.82, 1.0), (1.0, 0)]},
    {'joints': NECKL, 'axis': Z,
     'keys': [(0, 0), (0.38, 1.5), (0.55, -1.0), (0.8, -0.5), (1.0, 0)]},
    {'joints': NECKR, 'axis': Z,
     'keys': [(0, 0), (0.38, -1.5), (0.55, 1.0), (0.8, 0.5), (1.0, 0)]},
    {'joints': {'Body': 1.0}, 'axis': Y, 'keys': [(0, 0)] + SHUDDER + [(1.0, 0)]},
]
MOVES = [
    {'joint': 'Root', 'keys': [(0, [0, 0, 0]), (0.38, [0, 0, -0.035]), (0.56, [0, 0, 0.06]), (0.64, [0, 0, 0.065]),
                               (0.8, [0, 0, 0.03]), (1.0, [0, 0, 0])]},
]
FLOOR = {'joint': 'Root', 'min': 0.0}
