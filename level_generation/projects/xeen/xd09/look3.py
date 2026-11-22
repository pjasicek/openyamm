import math
N, S_, E, W = math.pi / 2, -math.pi / 2, 0.0, math.pi
SW = -2.5
S = [
 ('01-lock-before', [4900, 1000, 0], SW, -0.25, []),
 ('02-lever-s', [4224, -650, 0], S_, -0.1, []),
 ('03-lever-n-and-slot', [3850, 1700, 0], -1.2, -0.25, []),
 ('04-tumbler-e-lever', [5650, 500, 0], -2.4, -0.15, []),
 ('05-bolts-drawn', [4900, 1000, 0], SW, -0.25, ['event 36', 'event 37', 'event 38'], 4.0),
 ('06-lever-n-and-slot-after', [3850, 1700, 0], -1.2, -0.25, []),
]
