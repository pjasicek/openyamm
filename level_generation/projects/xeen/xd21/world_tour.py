# The move into the world (2026-11-20): the robbers as Xeen rows where they stand, and the rooms. tour.py list.
K = 'actor kill 30000'
P = 3.14159
S = [
 ('01-arrival', [-2560, 320, 0], 1.5708, 0.0, []),
 ('02-crawl-open', [-2560, 640, 0], 1.5708, 0.0, ['event 22'], 3.0),
 ('03-dicing-rogues', [-2560, 3650, 0], 1.9, -0.05, ['event 14'], 2.5),
 ('04-west-bank-rangers', [-2000, 4224, 0], 0.1, -0.05, []),
 ('05-east-bank-rogues', [-1100, 3968, 0], 0.25, -0.05, []),
 ('06-bunks-rogues', [-2432, 4800, 0], 1.9, -0.05, ['event 8'], 2.5),
 ('07-catwalk-rangers', [-1850, 5632, 0], 0.0, -0.05, ['event 23'], 2.5),
 ('08-fence-rogues', [650, 5632, 0], 0.0, -0.05, ['event 18'], 2.5),
 ('09-stair-rangers', [1000, 3968, 0], 0.0, 0.0, []),
 ('10-boss-door', [2750, 3968, 256], 0.0, -0.05, ['event 3'], 2.5),
 ('11-boss-and-guards', [3250, 3968, 256], 0.0, -0.1, ['event 3'], 1.5),
 ('12-race', [0, 3968, 0], -1.5708, -0.35, [K, 'event 30'], 7.0),
 ('13-boss-room', [3350, 4400, 256], -0.6, -0.05, [K]),
 ('14-vault', [3904, 6250, 256], 1.5708, -0.1, [K, 'event 9', 'event 29'], 4.0),
 ('15-river-grate', [0, 5600, 0], 1.5708, 0.15, [K]),
]
