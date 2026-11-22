#!/usr/bin/env python3
"""XD-10's tours: tour.py <set> <name> writes shots/<name>.yml. Sets: water (the moving-water check), rooms (every
room and interactive thing)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/xd10'
E = 160
OPEN_ALL = 'lua for _, d in ipairs({1,2,3,4,5,6,7,9,10,11}) do evt.SetDoorState(d, DoorAction.Open) end'
OPEN_WATER = 'lua evt.SetDoorState(10, DoorAction.Open)'
SETS = {
    'water': [
        ('01-rail-water-start', [2620, 5056, -640 + 190], 0.0, -0.3, None, []),
        ('02-sluice-window-start', [2620, 3072, 190], 0.0, -0.45, None, []),
        ('03-rail-water-1s', [2620, 5056, -640 + 190], 0.0, -0.3, 1.0, [OPEN_WATER]),
        ('04-rail-water-3s', [2620, 5056, -640 + 190], 0.0, -0.3, 2.0, []),
        ('05-rail-water-end', [2620, 5056, -640 + 190], 0.0, -0.3, 5.0, []),
        ('06-rail-wide-end', [2620, 5056, -640 + 190], 0.5, -0.25, None, []),
        ('07-sluice-window-end', [2620, 3072, 190], 0.0, -0.45, None, []),
        ('08-bed-from-floor', [3300, 3712, -1280 + E], 0.0, 0.05, None, []),
        ('09-mirage-cache-a', [-256, 9472, E], P, -0.05, 0.5, []),
        ('10-mirage-cache-b', [-256, 9472, E], P, -0.05, 0.7, []),
    ],
    'rooms': [
        ('01-north-mouth-arrival', [0, 9664, E], -P / 2, -0.05, None, []),
        ('02-north-mouth-exit-daylight', [0, 9300, E], P / 2, 0.05, None, []),
        ('03-north-mouth-west-mirage', [-200, 9472, E], P, -0.05, None, []),
        ('04-cache-chest', [-1000, 9400, E], P / 2 + 0.6, -0.2, None, []),
        ('05-phantom-safe-cave', [-1100, 8064, E], P + 0.4, -0.1, None, []),
        ('06-phantom-safe', [-1500, 7800, E], P + 0.5, -0.25, None, []),
        ('07-icicle-hall', [128, 8600, E], -P / 2, 0.15, None, []),
        ('08-icicle-hall-south', [300, 7200, E], P / 2 + 0.3, 0.1, None, []),
        ('09-hall-of-mirages', [256, 6500, E], -P / 2, 0.1, None, []),
        ('10-hall-of-mirages-ne-ice-stair', [600, 5200, E], 1.2, 0.05, None, []),
        ('11-frost-cavern', [256, 3900, E], -P / 2, 0.0, None, []),
        ('12-skull-alcoves', [-1150, 3200, E], P, -0.15, None, []),
        ('13-sluice-door', [900, 3072, E], 0.0, 0.0, None, []),
        ('14-sluice-plug', [1550, 2800, E], 0.35, -0.15, None, []),
        ('15-sluice-window', [2300, 3400, E], -0.3, -0.3, None, []),
        ('16-south-mouth', [64, 2000, E], -P / 2, 0.0, None, []),
        ('17-ice-stair-top', [1344, 6950, E], P / 2, -0.2, None, []),
        ('18-ice-stair-bend', [2300, 7296, -350], -P / 2, -0.25, None, []),
        ('19-ledge', [2400, 6100, -640 + E], -P / 2, -0.1, None, []),
        ('20-ledge-notice-gates', [2300, 4600, -640 + E], P, 0.0, None, []),
        ('21-ledge-water', [2620, 4600, -640 + 190], 0.3, -0.3, None, []),
        ('22-mirror-maze', [1500, 5300, -640 + E], P - 0.3, 0.0, None, []),
        ('23-maze-mirage', [704, 5900, -640 + E], P / 2, 0.0, None, []),
        ('24-deep-skulls-closed', [400, 5150, -640 + E], P / 2 + 0.3, 0.0, None, []),
        ('25-guardian-post', [-200, 5632, -640 + E], P, -0.1, None, []),
        ('26-echo-cave', [-576, 4500, -640 + E], -P / 2, -0.15, None, []),
        ('27-drowned-gate-from-ledge', [2100, 4352, -640 + E], P, 0.0, None, []),
        ('28-grotto-great-skull', [6500, 3328, -1280 + E], 0.0, -0.1, None, []),
        ('29-wreck', [1300, 1800, -1280 + E], -0.3, -0.15, None, []),
        ('30-sump', [700, 1800, -1280 + E], P + 0.6, -0.2, None, []),
        ('31-open-all-water-sinking', [2620, 4600, -640 + 190], 0.3, -0.3, 7.0, ['lua for _, d in ipairs({1,2,3,4,5,6,7,9,10,11}) do evt.SetDoorState(d, DoorAction.Open) end']),
        ('32-drowned-gallery-open', [1500, 4352, -640 + E], P, -0.05, None, []),
        ('33-steps-down', [2240, 3500, -640 + E], -P / 2, -0.3, None, []),
        ('34-reservoir-bed', [3100, 2496, -1280 + E], 0.3, 0.1, None, []),
        ('35-reservoir-bed-north', [4416, 2000, -1280 + E], P / 2, 0.15, None, []),
        ('36-reservoir-up-to-ledge', [3600, 5000, -1280 + E], P, 0.45, None, []),
        ('37-deep-skulls-open', [700, 6500, -640 + E], P / 2, -0.15, None, []),
        ('38-phantom-vault-open', [6784, 4400, -1280 + E], P / 2, -0.1, None, []),
        ('39-cache-from-safe-cave', [-1344, 8600, E], P / 2, 0.0, None, []),
        ('40-gallery-stair', [1408, 3300, -700], -P / 2, -0.3, None, []),
    ],
    'fix': [
        ('01-north-mouth-arrival', [0, 9664, E], -P / 2, 0.1, None, []),
        ('02-icicle-hall', [128, 8600, E], -P / 2, 0.2, None, []),
        ('03-phantom-safe', [-1500, 7800, E], P + 0.5, -0.25, None, []),
        ('04-ledge-notice', [2100, 5056, -640 + E], P, 0.0, None, []),
        ('05-mirror-maze', [1500, 5300, -640 + E], P - 0.3, 0.0, None, []),
        ('06-mirage-close-a', [-1344, 8700, E], P / 2, 0.0, 0.5, []),
        ('07-mirage-close-b', [-1344, 8700, E], P / 2, 0.0, 1.0, []),
        ('08-hall-ne-ice-stair', [600, 5200, E], 1.2, 0.05, None, []),
        ('09-open-all', [2620, 4600, -640 + 190], 0.3, -0.3, 7.0, [OPEN_ALL]),
        ('10-steps-from-ledge', [2240, 4000, -640 + E], -P / 2, -0.25, None, []),
        ('11-steps-mid', [2240, 3000, -820], -P / 2, -0.2, None, []),
        ('12-steps-bottom', [2500, 2496, -1280 + E], 0.0, 0.0, None, []),
    ],
}
s, name = sys.argv[1], sys.argv[2]
shots = []
for n, p, y, pt, settle, cmds in SETS[s]:
    d = {'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off'] + cmds}
    if settle:
        d['settle_seconds'] = settle
    shots.append(d)
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 2.0, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
