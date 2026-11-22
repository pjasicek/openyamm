#!/usr/bin/env python3
"""DD-03's tours: tour.py <name> writes shots/<name>.yml: every room and interactive thing, doors before and after.
Door numbers are ids.lock.yml's (1 armory, 2 banquet, 4 bedchamber, 6 cells, 7 closet, 8 cloud, 9 dstair, 11 kennel,
12 portcullis, 13 sleeping, 14 throne, 16 upper, 17 vault_secret, 18 vaults, 20 yard)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/dd03'
E = 160
G, F2, F3, D, K = E, 640 + E, 1280 + E, -640 + E, -1152 + E


def door(n):
    return f'lua evt.SetDoorState({n}, DoorAction.Open)'


SHOTS = [
    ('01-gate-arrival', [-1750, 0, G], 0.0, 0.0, []),
    ('02-gate-exit', [-1250, 0, G], P, 0.0, []),
    ('03-gate-crest', [-1536, -150, G], P / 2, 0.15, []),
    ('04-entrance-from-gate', [-800, 0, G], 0.0, 0.0, [door(12)]),
    ('05-entrance-yard-wall', [64, 500, G], -P / 2, 0.0, []),
    ('06-entrance-west', [800, 0, G], P, 0.1, []),
    ('07-throne-doors-closed', [500, 0, G], 0.0, 0.0, []),
    ('08-throne-from-doors', [1250, 0, G], 0.0, 0.05, [door(14)]),
    ('09-throne-close', [2350, 0, G], 0.0, 0.0, []),
    ('10-throne-safes', [1728, 250, G], P / 2, -0.2, []),
    ('11-throne-west', [2600, 0, G], P, 0.05, []),
    ('12-north-wing', [-750, 1216, G], 0.0, 0.0, []),
    ('13-cloud-foot', [-1536, 1150, G], P / 2, 0.05, []),
    ('14-banquet-doors', [768, 1150, G], P / 2, 0.0, []),
    ('15-banquet', [768, 1700, G], P / 2, 0.0, [door(2)]),
    ('16-kitchen', [1800, 1250, G], 0.5, 0.0, []),
    ('17-kitchen-passage', [2304, 1600, G], -P / 2, -0.05, []),
    ('18-south-wing', [1250, -1216, G], 0.0, 0.0, []),
    ('19-closet', [3150, 640, G], 0.0, 0.0, [door(7)]),
    ('19b-closet-door', [2600, 640, G], 0.0, 0.0, []),
    ('20-armory', [3850, 0, G], -0.4, -0.05, []),
    ('21-armory-safe', [4100, -500, G], -2.6, -0.3, []),
    ('22-dstair-head', [5200, -1216, G], -P / 2 + 0.3, 0.0, []),
    ('23-yard-from-entrance', [64, -650, G], -P / 2, 0.1, [door(20)]),
    ('24-yard-stables', [-700, -2100, G], P, 0.05, []),
    ('25-yard-mirror', [-128, -2450, G], -P / 2, 0.05, []),
    ('26-yard-sky', [-300, -1500, G], -P / 2, 0.9, []),
    ('27-cloud-flight', [-1536, 1500, G], P / 2, 0.25, [door(8)]),
    ('28-l2-landing', [-1950, 3200, F2], 0.0, 0.0, []),
    ('29-upper-foot', [-300, 3050, F2], P / 2, 0.05, []),
    ('30-residences', [450, 3136, F2], 0.0, 0.0, []),
    ('31-sleeping-door', [1152, 3050, F2], -P / 2, 0.0, []),
    ('32-sleeping', [1152, 2650, F2], -P / 2, -0.1, [door(13)]),
    ('33-phase-gallery', [2304, 2700, F2], -P / 2, 0.0, []),
    ('34-vault-doors', [2300, 1856, F2], 0.0, 0.0, []),
    ('35-vaults', [2850, 1856, F2], 0.0, 0.0, [door(18)]),
    ('36-upper-flight', [-384, 3350, F2], P / 2, 0.3, [door(16)]),
    ('37-l3-landing', [-750, 4992, F3], 0.0, 0.0, []),
    ('38-queens-gallery', [500, 5100, F3], 0.0, 0.0, []),
    ('39-gallery-north', [1408, 4800, F3], P / 2, 0.05, []),
    ('40-bedchamber-doors', [2250, 5120, F3], 0.0, 0.0, []),
    ('41-bedchamber', [2700, 4750, F3], 0.7, 0.0, [door(4)]),
    ('42-bedchamber-mirror', [2880, 5100, F3], P / 2, 0.0, []),
    ('43-court', [1408, 4400, F3], -P / 2, 0.0, []),
    ('44-court-east', [800, 3800, F3], 0.0, 0.0, []),
    ('45-court-west', [2000, 3800, F3], P, 0.0, []),
    ('46-bell-tower', [-1150, 4992, F3], P, 0.4, []),
    ('47-attic', [-1728, 4100, F3], -P / 2, 0.0, []),
    ('48-attic-arm', [-1750, 3264, F3], 0.0, 0.0, []),
    ('49-dstair-down', [5376, -1300, G], -P / 2, -0.35, [door(9)]),
    ('50-guardroom', [5300, -2800, D], -P / 2, 0.0, []),
    ('51-guard-desk', [5350, -3328, D], 0.0, -0.1, []),
    ('52-well-mouth', [4928, -3550, D], -P / 2, 0.0, []),
    ('53-well', [4480, -4150, D], -P / 2, 0.2, []),
    ('54-cells', [4500, -3264, D], P, 0.0, [door(6)]),
    ('55-cells-bays', [3500, -3550, D], P / 2, 0.0, []),
    ('56-maxsec', [2200, -3200, D], P, 0.0, []),
    ('57-maxsec-kennel', [1800, -3700, D], -P / 2, 0.0, []),
    ('58-kennel-stair', [1600, -4250, D], -P / 2, -0.3, [door(11)]),
    ('59-kennel', [1856, -5950, K], -P / 2, 0.1, []),
    ('60-kennel-hoard', [2200, -6600, K], -0.6, -0.15, []),
    ('61-vault-secret', [2150, -4160, D], 0.0, 0.0, [door(17)]),
    ('62-vault', [3550, -4480, D], P, 0.0, []),
]
name = sys.argv[1]
only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
shots = [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off'] + c}
         for n, p, y, pt, c in SHOTS if not only or n[:2] in only or any(x.startswith('door') for x in [])]
yaml.safe_dump({'output_dir': f'{X}/shots/{name}', 'settle_seconds': 1.5, 'exit': True, 'shots': shots},
               open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False, width=120)
print(len(shots), 'shots')
