"""Write the pilot's screenshot tour (Armory and tavern) into <output_dir>/tour.yml."""
import math
import sys

out = sys.argv[1]
d = math.radians
shots = [
    # Armory (BModel 51), the user's view 03 first.
    ('armory_v03', (-8892.189, -6804.438, 161), 0.567, d(-8.079)),
    ('armory_door', (-8820, -6352, 161), 0.0, d(2)),
    ('armory_nw', (-8700, -5700, 161), math.atan2(-750, 172), d(4)),
    ('armory_eave', (-8690, -6960, 161), math.atan2(160, 162), d(18)),
    ('armory_south', (-8100, -7020, 161), math.pi / 2, d(12)),
    ('armory_above', (-8900, -7300, 900), math.atan2(820, 692), d(-28)),
    # Tavern (BModels 80 front, 79 hall), the user's view 01 first.
    ('tavern_v01', (-9563.396, -8718.901, 161), 0.023, d(0.172)),
    ('tavern_porch', (-9150, -8690, 161), 0.0, d(8)),
    ('tavern_oblique', (-9250, -8150, 161), math.atan2(-540, 450), d(5)),
    ('tavern_door', (-8860, -8690, 193), 0.0, d(6)),
    ('tavern_hall_south', (-8100, -9800, 161), math.atan2(598, -348), d(22)),
    ('tavern_roof', (-9600, -9900, 1000), math.atan2(1210, 1664), d(-8)),
    # Bridge (BModel 20), the user's view 08 first.
    ('bridge_v08', (-19384.920, -11222.390, 658.781), 2.181, d(-40.050)),
    ('bridge_side', (-20216, -11250, 200), math.pi / 2, d(4)),
    ('bridge_oblique', (-19300, -11000, 300), math.atan2(496, -916), d(-3)),
    # Goblinwatch (BModels 70-72), the user's view 07 first.
    ('goblinwatch_v07', (-18421.469, -13917.778, 2338.048), 4.719, d(-22.775)),
    ('goblinwatch_front', (-18432, -14450, 1660), -math.pi / 2, d(10)),
    ('goblinwatch_oblique', (-17000, -14200, 2500), math.atan2(-1256, -1432), d(-10)),
]
lines = [f'output_dir: {out}', 'exit: true', 'settle_seconds: 3.0', 'shots:']
for name, p, yaw, pitch in shots:
    lines += [f'  - name: {name}', f'    position: [{p[0]}, {p[1]}, {p[2]}]', f'    yaw: {yaw:.4f}',
              f'    pitch: {pitch:.4f}']
open(out + '/tour.yml', 'w').write('\n'.join(lines) + '\n')
