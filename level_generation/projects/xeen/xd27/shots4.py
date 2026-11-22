import math
P = math.pi
K = 'actor kill 30000'
S = [
    ('01-gate-yard-bar', [420, 1560, 0], -2.3, 0.0, [K, K], 2.5),
    ('02-gate-yard-bar-lifted', [420, 1560, 0], -2.3, 0.0, [K, 'event 11', 'event 12'], 4.0),
    ('03-gate-open-from-mouth', [0, 640, 0], P / 2, 0.0, [K], 2.0),
    ('04-chief-seat-wide', [-2100, 3700, 32], 2.9, -0.05, [K], 2.0),
]
