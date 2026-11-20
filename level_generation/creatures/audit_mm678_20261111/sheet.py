#!/usr/bin/env python3
"""Contact sheet of flagged moments (audit 2026-11-11): one row per (model, clip, time, joint), three frames around the
time, whole body and zoomed on the joint, bad triangles red (motion_audit thresholds).

    python3 sheet.py <out.png> <stem>|<clip>|<time>[|<joint>[|<yaw>]] ...
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / 'claude_shared'))
import motion_audit  # noqa: E402
import motion_frames  # noqa: E402

CELL = 210


def row(spec):
    parts = spec.split('|')
    stem, clip, time = parts[0], parts[1], float(parts[2])
    joint = parts[3] if len(parts) > 3 and parts[3] else None
    yaw = float(parts[4]) if len(parts) > 4 else 0.5
    table = json.loads((HERE / 'table.json').read_text())['models']
    a = motion_audit.Audit(HERE.parents[2] / 'assets_source' / table[stem]['path'])
    times = a.model.clip_times(clip)
    t0, t1 = times[0], times[-1]
    picks = [min(max(t, t0), t1) for t in (time - 0.12, time, time + 0.12)]
    rot = motion_frames.view(yaw, 0.15)
    cells = []
    for k, t in enumerate(picks):
        posed, scale, palette, world = a.pose(clip, t)
        s1, s2, fold, live = a.deformation(posed, scale, palette)
        bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
        cam = posed @ rot.T
        lo, hi = cam.min(axis=0), cam.max(axis=0)
        if k == 1:
            cells.append(motion_frames.draw(cam, a.tris, bad, (lo[:2] + hi[:2]) / 2,
                                            max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05, CELL))
        if joint:
            j = a.model.joints[a.joint_names.index(joint)]
            centre = (world[j][:3, 3] @ rot.T)[:2]
            cells.append(motion_frames.draw(cam, a.tris, bad, centre, 0.3 * a.height, CELL))
    img = Image.new('RGB', (CELL * 4 + 170, CELL), (255, 255, 255))
    ImageDraw.Draw(img).text((4, 8), f'{stem}\n{clip} @{time:.2f}s\n{joint or ""}', fill=(0, 0, 0))
    for i, c in enumerate(cells):
        img.paste(c, (170 + i * CELL, 0))
    return img


rows = [row(s) for s in sys.argv[2:]]
sheet = Image.new('RGB', (rows[0].width, CELL * len(rows)), (255, 255, 255))
for i, r in enumerate(rows):
    sheet.paste(r, (0, i * CELL))
sheet.save(sys.argv[1])
print(sys.argv[1])
