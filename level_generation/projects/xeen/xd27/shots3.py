import math
P = math.pi
K = 'actor kill 20000'
S = [
    ('01-ledge-gorge-view', [2400, 6176, 128], 0.0, -0.05, [K]),
    ('02-ledge-rack-heap', [2752, 6280, 128], -P / 2, -0.1, [K]),
    ('03-over-the-parapet', [3060, 6176, 128], 0.0, -0.6, [K]),
    ('04-ledge-north-view', [2380, 6880, 128], -0.55, 0.0, [K]),
    ('05-rack-heap-gone', [2752, 6280, 128], -P / 2, -0.1, [K, 'event 18'], 5.0),
    ('06-chute-end', [1900, 6080, 160], 0.0, 0.0, [K]),
]
