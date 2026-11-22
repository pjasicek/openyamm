#!/usr/bin/env python3
"""Into the world (lane A8, 2026-11-20): XD-12's tour from the installed map (assets_dev, --world xeen): the Well, the
works, the library and a trapdoor, Darzog's hall with Darzog and the clones, Crodo's cell, the roof, and the rooms whose
props moved (dressing). Writes xshots.yml; run with xshots.sh."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/xd12'
S = [
    ('01-gate-hall-arrival', [2752, 0, 160], P, 0.0),
    ('02-gate-hall-barrels', [2500, -700, 160], -1.2, -0.15),
    ('03-well-up-to-the-sky', [-500, -500, 160], 0.785, 1.1),
    ('04-well-foot-braziers', [0, -820, 160], P / 2, -0.12),
    ('05-hall-of-hands', [-384, 2000, 160], P / 2, -0.1),
    ('06-crypt', [-2080, 2080, 160], 2.36, -0.15),
    ('07-storeroom', [2150, -2150, 160], -0.785, -0.2),
    ('08-forge-anvils-lava', [-384, 2000, 930], P / 2, -0.15),
    ('09-forge-west', [300, 2300, 930], P, -0.12),
    ('10-scrap-hall', [-2100, 2100, 930], 2.36, -0.15),
    ('11-reading-room', [-384, 2000, 1696], P / 2, -0.12),
    ('12-reading-room-trapdoor', [1650, 2350, 1696], P, -0.3),
    ('13-great-library', [384, -2000, 1696], -P / 2, -0.12),
    ('14-study-of-the-arm', [2624, -2000, 1696], -1.75, -0.2),
    ('15-darzogs-hall', [-1650, 2496, 2464], 0.0, 0.0),
    ('16-darzogs-dais', [500, 2400, 2464], 0.1, 0.0),
    ('17-darzogs-study', [-2100, 2200, 2464], 2.5, -0.3),
    ('18-crodos-cell', [2700, 2650, 2464], 0.785, -0.1),
    ('19-clone-vats', [2048, -2048, 2464], -0.785, -0.25),
    ('20-portrait-hall', [1650, -2496, 2464], P, 0.0),
    ('21-roof-cloud-stair', [0, 1400, 3232], P / 2, 0.05),
    ('22-roof-down-the-well', [-950, 0, 3232], 0.0, -1.35),
    ('23-roof-over-the-lake', [0, -3240, 3232], -P / 2, -0.9),
]
doc = {'output_dir': X + '/xshots', 'settle_seconds': 2.0, 'exit': True,
       'shots': [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off']}
                 for n, p, y, pt in S]}
yaml.safe_dump(doc, open(X + '/xshots.yml', 'w'), sort_keys=False)
