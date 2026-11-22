import math
N, S_, E, W = math.pi / 2, -math.pi / 2, 0.0, math.pi
SW = -2.5
S = [
 ('01-lock-before', [4900, 1000, 0], SW, -0.25, []),
 ('02-lock-from-forge-door', [3350, -256, 0], 0.15, -0.12, []),
 ('03-golem-forge', [4550, -450, 0], -0.3, -0.12, []),
 ('04-bolt-n-close', [4600, 1150, 0], math.pi - 0.2, -0.45, []),
 ('05-bolt-s-and-lever', [4500, 100, 0], -2.0, -0.35, []),
 ('06-bolts-drawn', [4900, 1000, 0], SW, -0.25, ['event 36', 'event 37', 'event 38'], 4.0),
 ('07-bolt-n-drawn-close', [4600, 1150, 0], math.pi - 0.2, -0.45, []),
 ('08-lid-open', [4900, 1000, 0], SW, -0.3, ['lua evt.SetDoorState(20, DoorAction.Open)'], 8.0),
 ('09-lid-open-from-forge-door', [3350, -256, 0], 0.15, -0.12, []),
 ('10-exit-door-from-entry', [384, -1650, 0], S_, 0.12, []),
 ('11-exit-door-landing', [384, -2000, 192], S_, 0.0, []),
]
