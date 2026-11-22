import math
SW = -2.5
S = [
 ('01-lock-before', [4900, 1000, 0], SW, -0.25, []),
 ('02-lock-from-forge-door', [3350, -256, 0], 0.15, -0.12, []),
 ('03-bolt-n-end', [4380, 700, 0], 2.06, -0.40, []),
 ('04-bolt-n-close', [4600, 1150, 0], math.pi - 0.2, -0.45, []),
 ('05-bolt-e-close', [4700, 650, 0], -2.31, -0.42, []),
 ('06-bolt-s-and-lever', [4500, 100, 0], -2.0, -0.35, []),
 ('07-bolt-s-end', [4330, -60, 0], -2.19, -0.45, []),
 ('07b-bolt-e-end', [4250, 600, 0], -0.93, -0.40, []),
 ('08-lid-top', [4700, 376, 0], math.pi, -0.65, []),
 ('09-bolts-drawn', [4900, 1000, 0], SW, -0.25, ['event 36', 'event 37', 'event 38'], 4.0),
 ('10-bolt-n-drawn-close', [4600, 1150, 0], math.pi - 0.2, -0.45, []),
 ('11-lid-open', [4900, 1000, 0], SW, -0.3, ['lua evt.SetDoorState(20, DoorAction.Open)'], 8.0),
 ('12-lid-open-from-forge-door', [3350, -256, 0], 0.15, -0.12, []),
]
