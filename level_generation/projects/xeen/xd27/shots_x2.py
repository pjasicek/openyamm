# After the dressing moves (lane A8, 2026-11-20): the rooms whose props moved.
import math
P = math.pi
K = 'actor kill 20000'
S = [
    ('01-mouth-to-gate', [0, 300, 0], P / 2, 0.0, [K]),
    ('02-mouth-southwest', [0, 700, 0], -2.4, -0.05, [K]),
    ('03-mouth-east', [-200, 500, 0], -0.4, -0.05, [K]),
    ('04-midden-fissure', [-900, 544, 0], P, 0.0, [K]),
    ('05-midden-bend', [-1600, 820, 90], 1.4, 0.0, [K]),
    ('06-bone-den-east', [-2400, 2500, 192], -0.3, -0.05, [K]),
    ('07-feast-northeast', [-200, 3500, 0], 0.5, -0.1, [K]),
    ('08-feast-southwest', [-500, 3000, 0], -2.3, -0.1, [K]),
    ('09-chief-seat', [-2752, 3620, 32], P / 2, -0.05, [K]),
    ('10-larder-from-door', [-3250, 3776, 32], P, -0.1, [K, 'item give 12170', 'event 15'], 4.0),
    ('11-larder-north', [-3600, 3700, 32], 1.9, -0.1, [K]),
    ('12-ramp', [-192, 4150, 0], P / 2, 0.08, [K]),
]
