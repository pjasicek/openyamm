#!/usr/bin/env python3
"""Acceptance sheets for the hands, from full-size viewer shots: one sheet per tier, Standing, a raised-arm clip and a hand-low clip, front, side and quarter, focus arms.
Usage (repo root): arm_accept.py <project> <token> <out prefix> <tier ...>"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
proj, tok, pre = sys.argv[1:4]
tiers = sys.argv[4:]
poses = (('Standing', 0.5, 'standing'), ('Running', 0.08, 'raised'), ('Walking', 0.25, 'low'))
views = ('front', 'left', 'quarter')
for t in tiers:
    spec = [f'ac_{t}_{p}_{v}:{c}:{tm}:{v}:arms' for c, tm, p in poses for v in views]
    subprocess.run(['python3', 'tools/run_creature_review.py', '--project', proj, '--token', tok, '--tier', t, 'shots', *spec], check=True, stdout=subprocess.DEVNULL)
    W, H = 690, 508
    S = Image.new('RGB', (W * 3, H * 3))
    d = ImageDraw.Draw(S)
    for r, (c, tm, p) in enumerate(poses):
        for k, v in enumerate(views):
            im = Image.open(Path(proj) / f'review/shots/ac_{t}_{p}_{v}.png').convert('RGB').resize((W, H), Image.LANCZOS)
            S.paste(im, (k * W, r * H))
            d.text((k * W + 6, r * H + 4), f'{t} {c} {tm} {v}', fill=(255, 255, 120))
    S.save(f'{pre}_{t}.png')
    print('ACCEPT', t)
