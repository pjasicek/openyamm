import math
P = math.pi
K = 'actor kill 20000'
S = [
    ('01-mouth-daylight-exit', [0, 820, 0], -P / 2, 0.0, []),
    ('02-chute-top', [900, 5920, 384], 0.0, -0.05, [K]),
    ('03-ledge-gorge-view', [2400, 6176, 128], 0.0, -0.05, [K]),
    ('04-ledge-rack-heap', [2752, 6280, 128], -P / 2, -0.1, [K]),
    ('05-over-the-parapet', [3060, 6176, 128], 0.0, -0.75, [K]),
    ('06-ledge-north-view', [2380, 6880, 128], -0.55, 0.0, [K]),
    ('07-ledge-south-view', [2700, 6900, 128], -1.3, 0.0, [K]),
    ('08-rack-heap-gone', [2752, 6280, 128], -P / 2, -0.1, [K, 'event 18'], 5.0),
    ('09-chief-den-sail', [-2000, 3800, 32], -1.9, 0.0, [K]),
    ('10-gate-from-mouth', [0, 760, 0], P / 2, 0.05, []),
]
