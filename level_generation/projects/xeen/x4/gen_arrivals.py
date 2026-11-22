#!/usr/bin/env python3
"""X4's arrivals check (A5, 2026-11-20): each DOORS.md arrival as a pose; after 3 s the party must still stand there
(within 300 across, its feet within the z band given): nothing buried, the ledge holds, the throne fall lands.
Writes output/studio_cal/x4/run/arrivals.yml."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
ARR = [  # name, x, y, z set, z_min, z_max, yaw (radians)
    ('x2_south_start', 16384, -22016, 1000, 960, 1060, 1.5708),
    ('x3_x36_arrival', -14336, -22016, 1000, 960, 1060, 1.5708),     # X3's north edge (the world's edge_spans)
    ('xd07_gate_outside', -1024, 6912, 1808, 1760, 1860, -1.5708),
    ('xd07_throne_fall', -4608, 9728, 2504, 1440, 1560, 0.0),
    ('xd07_postern_moat_bank', -5120, 8448, 1320, 1290, 1340, 3.1416),   # XD-07's postern: the rise's west foot
    ('xd25_stair_outside', -11520, -9448, 1060, 1030, 1100, -1.5708),
    ('xd26_mouth_outside', -9216, 11208, 1830, 1790, 1880, -1.5708),
    ('xd26_sky_crack_ledge', -7424, 14592, 3600, 3570, 3640, -1.5708),
    ('xd02_adit_outside', 20080, -16128, 1510, 1480, 1560, 3.1416),
    ('burlock_square', -1536, 3584, 1312, 1290, 1340, -1.5708),
    ('burlock_stables', 614, 4096, 1312, 1290, 1340, 3.1416),
    ('asp_travel_pit', -7168, -10240, 1056, 1030, 1090, 3.1416),
    ('asp_square', -12800, -11776, 1056, 1030, 1090, 1.5708),
    ('x4_river_landing', 9728, -18944, 740, 700, 790, 3.1416),
]
import yaml
steps = [{'new_game_flow': {'start_map': 'xeen_x4.odm'}}, {'setup_shortcut': {'kind': 'immortal', 'value': True}}]
for name, x, y, z, lo, hi, yaw in ARR:
    steps += [{'note': name}, {'set_pose': {'map': 'xeen_x4.odm', 'x': x, 'y': y, 'z': z, 'yaw': yaw, 'pitch': 0.0}},
              {'advance_runtime': {'seconds': 3.0}},
              {'assert': {'party_position': {'x': x, 'y': y, 'radius': 300, 'z_min': lo, 'z_max': hi}}}]
doc = {'id': 'xeen.x4.arrivals', 'title': "X4's arrivals hold the party", 'world': 'xeen', 'mode': 'faithful',
       'steps': steps}
open(_REPO_ROOT + '/output/studio_cal/x4/run/arrivals.yml', 'w').write(yaml.safe_dump(doc, sort_keys=False))
