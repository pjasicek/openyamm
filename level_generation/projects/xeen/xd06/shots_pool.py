import math
N, S_, E, W = math.pi / 2, -math.pi / 2, 0.0, math.pi
K = 'actor kill 40000'
S = [
 ('01-pool-down-from-edge', [-1420, 9696, -768], E, -0.6, [K]),
 ('02-pool-down-ne', [-1420, 9300, -768], 0.5, -0.5, []),
 ('03-pool-from-far', [-120, 9696, -768], W, -0.5, []),
 ('04-in-pool-west', [-400, 10200, -1088], W, 0.2, []),
 ('05-levers-1-2-3', [-1420, 9696, -768], E, -0.6, ['event 10', 'event 11', 'event 12'], 4.0),
 ('06-causeway-raised', [-1420, 9696, -768], E, -0.45, ['event 11'], 4.0),
 ('07-causeway-from-far', [-120, 9696, -768], W, -0.3, []),
 ('08-on-causeway', [-900, 9696, -768], E, -0.1, []),
]
