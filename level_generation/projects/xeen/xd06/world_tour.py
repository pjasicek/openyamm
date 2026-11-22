# The move into the world (2026-11-20): the temple's monsters as Xeen rows where they spawn, and the rooms. tour.py list.
import math
N, S_, E, W = math.pi / 2, -math.pi / 2, 0.0, math.pi
S = [
 ('01-arrival-porch', [0, 300, 0], N, 0.0, []),
 ('02-nave-from-arch', [0, 1900, 0], N, 0.1, ['event 39'], 3.0),
 ('03-nave-priests', [-300, 2600, 0], 1.3, 0.0, []),
 ('04-west-chapel-clerics', [-1000, 4224, 0], W, 0.0, []),
 ('05-east-chapel-vestry', [1000, 4224, 0], E, 0.0, []),
 ('06-vestry-elder', [2400, 3800, 0], 0.8, 0.0, []),
 ('07-library', [2450, 2650, 0], 0.6, 0.05, []),
 ('08-refectory', [-2450, 3800, 0], 2.4, 0.0, []),
 ('08b-refectory-from-stair', [-3040, 5150, 0], -1.9, -0.05, []),
 ('08c-dormitory', [-2624, 2560, 0], 2.0, -0.05, []),
 ('08d-chapel-w-altar', [-1760, 4600, 0], S_, -0.05, []),
 ('09-crypt-skeletons', [-2300, 7050, -768], 2.4, 0.0, []),
 ('10-ossuary', [-2450, 8700, -768], 2.4, 0.0, []),
 ('11-near-bank-pool', [-1900, 9696, -768], E, -0.15, []),
 ('12-causeway-raised', [-1750, 9696, -768], E, -0.12, ['event 10', 'event 12'], 4.0),
 ('13-far-bank', [-50, 9500, -768], 0.6, 0.0, []),
 ('14-lich-crypt-ghouls', [1650, 9450, -768], 0.4, 0.0, []),
 ('15-sanctum-doors', [512, 10800, -768], N, 0.05, []),
 ('16-sanctum-master', [512, 11500, -768], N, 0.05, ['event 34'], 3.0),
 ('17-altar-master-close', [512, 12200, -768], N, 0.0, []),
 ('18-master-cell', [1500, 12480, -768], E, -0.05, ['event 25'], 3.0),
]
