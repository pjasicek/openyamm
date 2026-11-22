#!/usr/bin/env python3
"""A5 (2026-11-20): tours of X1 and X2 in the Xeen world (the dressing rule, the new people and signs). Writes
output/studio_cal/x2/world_tour/tour_<map>.yml; heights from each build's export.json."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
import math
import os
R = _REPO_ROOT
OUT = R + '/output/studio_cal/x2/world_tour'
MAPS = {
    'x2': ('output/studio_cal/x2/build_w/export.json', [
        ('tavern_barrels', (65.6, 46.6), 200, (65.6, 43.2), 60), ('bank_door_square', (61.0, 46.4), 220, (62.8, 44.0), 100),
        ('south_quay_strongbox', (74.0, 55.9), 200, (71.0, 56.4), 60), ('north_quay_props', (58.0, 50.0), 200, (54.8, 50.2), 40),
        ('dock_props', (74.6, 55.6), 200, (77.0, 56.5), 40), ('danulf', (58.6, 80.4), 200, (56.8, 82.6), 120),
        ('ligono', (29.6, 100.2), 220, (27.0, 102.0), 120), ('west_road_end', (24.0, 40.0), 220, (20.6, 39.1), 100),
        ('north_road_end', (66.5, 24.0), 220, (67.1, 20.6), 100), ('town_air', (64, 70), 1800, (64, 50), 0),
        ('mirror_square', (64, 48.5), 200, (62.0, 46.9), 100), ('south_street', (58, 61.4), 220, (70, 61), 80)]),
    'x1': ('output/studio_cal/x1/build_rb/export.json', [
        ('inn_front', (44.6, 46.6), 600, (43.75, 45.0), 100), ('joes_yard', (60.0, 61.2), 500, (61.6, 59.4), 40),
        ('stables_barrels', (62.6, 50.0), 500, (64.0, 48.2), 40), ('temple_back', (56.3, 51.2), 500, (57.5, 49.3), 40),
        ('alchemist_barrels', (50.6, 47.6), 500, (49.5, 46.2), 40), ('derek_camp', (44.5, 76.0), 300, (42.0, 78.0), 80)]),
}
for key, (exp, shots) in MAPS.items():
    m = json.load(open(os.path.join(R, exp)))['map']
    hm = m['terrain']['height_map']
    def h(cx, cy):
        i, j = max(0, min(127, int(round(cx)))), max(0, min(127, int(round(cy))))
        return hm[j * 128 + i] * 32
    lines = ['output_dir: "%s/%s"' % (OUT, key), 'exit: true', 'settle_seconds: 2.5', 'shots:']
    for name, (cx, cy), eh, (tx, ty), th in shots:
        ex, ey = (cx - 64) * 512, (64 - cy) * 512
        gx, gy = (tx - 64) * 512, (64 - ty) * 512
        ez, tz = h(cx, cy) + eh, h(tx, ty) + th
        yaw = math.atan2(gy - ey, gx - ex)
        pitch = math.atan2(tz - ez, math.hypot(gx - ex, gy - ey))
        lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, time: "12:00", commands: '
                     '["render hud off", "sky weather 0", "weather clear"]}' % (name, ex, ey, ez, yaw, pitch))
    open('%s/tour_%s.yml' % (OUT, key), 'w').write('\n'.join(lines) + '\n')
    print(key, len(shots))
