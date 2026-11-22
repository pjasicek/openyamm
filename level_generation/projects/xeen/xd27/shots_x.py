# Into the world (lane A8, 2026-11-20): the Xeen rows standing where they spawn, the gorge, the exit picture, the larder.
import math
P = math.pi
K = 'actor kill 20000'
S = [
    ('01-arrival-mouth', [0, 300, 0], P / 2, 0.0, []),
    ('02-mouth-daylight-exit', [0, 820, 0], -P / 2, 0.0, []),
    ('03-midden-dogs', [-1450, 640, 70], 1.0, 0.0, []),
    ('04-bone-den-ogres', [-1856, 2000, 192], 2.2, 0.0, []),
    ('05-feast-from-terrace', [-1180, 2752, 192], 0.15, -0.22, []),
    ('06-feast-pit-brutes', [420, 2560, 0], 2.45, -0.12, []),
    ('07-gate-yard-dogs', [0, 2300, 0], -P / 2, -0.05, []),
    ('08-kennel-dogs', [640, 3168, 0], 0.0, 0.0, []),
    ('09-chief-den', [-1520, 3616, 32], P, -0.05, []),
    ('10-quarry-ogres', [-64, 5280, 384], P / 2, 0.0, []),
    ('11-ledge-chieftain', [2280, 6176, 128], 0.0, 0.0, []),
    ('12-ledge-gorge-view', [2400, 6176, 128], 0.0, -0.05, [K]),
    ('13-ledge-rack-heap', [2752, 6280, 128], -P / 2, -0.1, [K]),
    ('14-larder-inside', [-3330, 3800, 32], P, -0.1, [K, 'item give 12170', 'event 15'], 4.0),
]
