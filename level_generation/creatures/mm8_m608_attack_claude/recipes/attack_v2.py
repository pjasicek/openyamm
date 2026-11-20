# Juggernaut m608 Attack v2 (attacks-2, 2026-11-11). Faces +Z, +Y up; rollers on an X axle (radius 0.179). Native
# m608Aa-Ah: arms flung up and wide, flexed, brought together in front, the burst between the palms, recover. The
# installed clip carries the arms; this adds the body: the torso rears back and the rollers roll it back during the
# raise, then it pitches forward and lunges 0.13 m on its rollers into the palm strike (contact 1.0 s, kept), and
# rolls back by 1.25 s (length kept). Roller spin = travel / radius, so the rollers roll instead of sliding.
import numpy as np

CLIP = 'Attack'
SOURCE = 'Attack'
X, Y, Z = [1, 0, 0], [0, 1, 0], [0, 0, 1]
RADIUS = 0.179
TRAVEL = [(0, 0.0), (0.3, -0.03), (0.6, -0.045), (0.82, -0.02), (0.97, 0.12), (1.04, 0.13), (1.15, 0.06),
          (1.25, 0.0)]

LAYERS = [
    {'joints': {'Waist': 1.0, 'Chest': 1.4}, 'axis': X,
     'keys': [(0, 0), (0.3, -3), (0.6, -6), (0.8, -4), (0.97, 9), (1.05, 10), (1.16, 4), (1.25, 0)]},
    {'joints': {'Neck': 1.0, 'Head': 1.0}, 'axis': X,
     'keys': [(0, 0), (0.6, -4), (0.85, -2), (0.98, 5), (1.08, 4), (1.25, 0)]},
    {'joints': {'Waist': 1.0}, 'axis': Y,
     'keys': [(0, 0), (0.4, 6), (0.7, 4), (0.95, -4), (1.1, -2), (1.25, 0)]},
    {'joints': {'Roller_0': 1.0, 'Roller_1': 1.0, 'Roller_2': 1.0}, 'axis': X,
     'keys': [(t, float(np.degrees(d / RADIUS))) for t, d in TRAVEL]},
]
MOVES = [{'joint': 'Root', 'keys': [(t, [0, 0, d]) for t, d in TRAVEL]}]
FLOOR = {'joint': 'Root', 'min': 0.0}
