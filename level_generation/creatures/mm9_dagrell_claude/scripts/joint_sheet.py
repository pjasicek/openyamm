#!/usr/bin/env python3
"""Joint-fix review sheets (2026-10-30): MM9 original | ours before | ours after, one row per pose, from the renders of
render_frames.py, with the before/after worst joint opening of that clip (joint_gaps.py JSON) in the row label.
Usage: joint_sheet.py <frames dir> <plan.json> <gaps_before.json> <gaps_after.json> <out prefix>"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

F, PLAN, GB, GA, OUT = sys.argv[1:6]
F = Path(F)
plan = json.load(open(PLAN))['frames']
gb = json.load(open(GB))['clips']; ga = json.load(open(GA))['clips']
S = 300
COLS = [('mm9', 'MM9 original'), ('before', 'ours before'), ('after', 'ours after')]


def tile(path):
    im = Image.open(path).convert('RGB')
    return im.resize((S, S), Image.LANCZOS)


def sheet(sub, rows, out):
    W = 230 + S * len(COLS) * (2 if sub == 'both' else 1)
    H = 30 + S * len(rows)
    im = Image.new('RGB', (W, H), (30, 31, 34)); dr = ImageDraw.Draw(im)
    dirs = ['frames', 'frames_side'] if sub == 'both' else [sub]
    x = 230
    for d in dirs:
        for _, name in COLS:
            dr.text((x + 8, 8), f'{name} ({"3/4" if d == "frames" else "side"})', fill=(230, 230, 230)); x += S
    for r, (i, rec) in enumerate(rows):
        y = 30 + r * S
        clip = rec['label'].split(' ')[0]
        lines = [rec['label'], f"MM9: {rec['mm9']}"]
        if clip in gb:
            lines += [f"worst joint opening", f"  before {gb[clip]['worst_m'] * 100:.0f} cm", f"  after  {ga[clip]['worst_m'] * 100:.1f} cm"]
        dr.multiline_text((8, y + 10), '\n'.join(lines), fill=(235, 235, 200), spacing=4)
        x = 230
        for d in dirs:
            for key, _ in COLS:
                im.paste(tile(F.parent / d / f'{key}_{i:02d}.png'), (x, y)); x += S
    im.save(out)
    print(out)


rows = [(i, r) for i, r in enumerate(plan)]
sheet('both', rows[:10], f'{OUT}_poses_1.png')
sheet('both', rows[10:], f'{OUT}_poses_2.png')
