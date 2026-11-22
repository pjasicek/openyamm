#!/usr/bin/env python3
"""Rebase (A5, 2026-11-20): a tour of what the rebase added or changed (shots into output/studio_cal/x1/rebase/tour)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import contextlib
import io
import math
import os
import sys
sys.argv = [sys.argv[0], '/tmp/x1_unused']
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import gen
OUT = _REPO_ROOT + '/output/studio_cal/x1/rebase/tour'
SHOTS = [  # name, camera cell, eye height over the land, target cell, target height over the land
    ('mirror_square', (54, 50.5), 220, (56.5, 48.3), 120), ('hunters_camp', (19, 66), 260, (23.5, 62), 80),
    ('ruined_shrine', (36, 102), 300, (30.5, 97.5), 150), ('ruined_cottage', (59, 80), 260, (55.5, 83), 80),
    ('grave_field', (56, 94), 260, (60.5, 98), 60), ('watchtower', (91, 43), 260, (97.5, 39.5), 300),
    ('stone_ring', (76, 55), 260, (80.6, 58.2), 60), ('rim_lookout', (97, 51), 260, (106, 54), -300),
    ('south_meadow_air', (58, 66), 1600, (52, 92), 0), ('east_meadow', (78, 50), 400, (96, 60), 0),
    ('west_meadow_air', (42, 54), 900, (28, 66), 0), ('dead_forest', (46, 76), 300, (32, 92), 100),
    ('toad_marsh', (78, 79), 350, (90, 92), 0), ('hills_air', (42, 42), 1800, (32, 27), 0),
    ('crodo_bottle', (28.5, 46.8), 200, (26, 48.8), 40), ('fisher_shelter', (67, 52.5), 260, (71, 56), 100),
    ('sheepfold', (54, 71.5), 260, (50.5, 74.5), 40), ('square_air', (55, 55), 1300, (55, 45), 0),
    ('outpost_west', (34, 34), 400, (30, 29), 80), ('road_camp_west', (16, 46.8), 900, (11.5, 41.8), 60)]
lines = ['output_dir: "%s"' % OUT, 'exit: true', 'settle_seconds: 2.5', 'shots:']
for name, (cx, cy), eh, (tx, ty), th in SHOTS:
    ex, ey = (cx - 64) * 512, (64 - cy) * 512
    gx, gy = (tx - 64) * 512, (64 - ty) * 512
    ez = gen.height(cx, cy) + eh
    tz = gen.height(tx, ty) + th
    yaw = math.atan2(gy - ey, gx - ex)
    pitch = math.atan2(tz - ez, math.hypot(gx - ex, gy - ey))
    lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                 % (name, ex, ey, ez, yaw, pitch))
open(os.path.join(os.path.dirname(OUT), 'tour.yml'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
