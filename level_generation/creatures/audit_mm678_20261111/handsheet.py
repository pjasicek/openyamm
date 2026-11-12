#!/usr/bin/env python3
"""Hand close-ups of every MM6-MM8 biped at the first Standing frame (audit 2026-11-11): left and right hand, front
three-quarter view facing the model (forward from the toes), flat shaded, bad triangles red.

    python3 handsheet.py <out_prefix> [--per 36] [--models a,b,...]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / 'claude_shared'))
import motion_audit  # noqa: E402
import motion_frames  # noqa: E402

CELL = 220


def hand_joint(names, side):
    for pattern in (f'B_{side}_Hand', f'mixamorig:{"Left" if side == "L" else "Right"}Hand',
                    f'{"Left" if side == "L" else "Right"}Hand', f'Hand_{side}', f'hand.{side.lower()}'):
        if pattern in names:
            return pattern
    for n in names:
        low = n.lower()
        if 'hand' in low and (('left' in low or f'_{side.lower()}' in low or low.startswith(side.lower())) if side == 'L'
                              else ('right' in low or f'_{side.lower()}' in low or low.startswith(side.lower()))):
            return n
    return None


def forward_yaw(a, world):
    toes = [i for i, n in enumerate(a.joint_names) if 'toe' in n.lower()]
    feet = [i for i, n in enumerate(a.joint_names) if 'foot' in n.lower() and 'toe' not in n.lower()]
    if toes and feet:
        d = np.mean([world[a.model.joints[t]][:3, 3] for t in toes], 0) - \
            np.mean([world[a.model.joints[f]][:3, 3] for f in feet], 0)
    else:
        d = np.array([0.0, 0.0, 1.0])
    # view() rotates by yaw about +Y and the camera looks along -Z: choose yaw so the forward points at +Z.
    return float(np.arctan2(-d[0], d[2])) if np.hypot(d[0], d[2]) > 1e-6 else 0.0


def cells(stem, path):
    a = motion_audit.Audit(path)
    clip = next((c for c in a.model.clips if c.lower() == 'standing'), None)
    t = a.model.clip_times(clip)[0] if clip else 0
    posed, scale, palette, world = a.pose(clip, t)
    s1, s2, fold, live = a.deformation(posed, scale, palette)
    bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
    base = forward_yaw(a, world)
    out = []
    for side, turn in (('R', -0.6), ('L', 0.6)):
        name = hand_joint(a.joint_names, side)
        rot = motion_frames.view(base + turn, 0.25)
        cam = posed @ rot.T
        if name is None:
            img = Image.new('RGB', (CELL, CELL), (220, 220, 220))
        else:
            j = a.model.joints[a.joint_names.index(name)]
            centre = (world[j][:3, 3] @ rot.T)[:2]
            # Centre a bit beyond the wrist toward the fingers: average of the hand-region vertices near the joint.
            region = a.vertex_region == motion_audit.REGIONS.index('hand')
            near = region & (np.linalg.norm(posed - world[j][:3, 3], axis=1) < 0.12 * a.height)
            if near.any():
                centre = (posed[near] @ rot.T)[:, :2].mean(0)
            img = motion_frames.draw(cam, a.tris, bad, centre, 0.17 * a.height, CELL)
        ImageDraw.Draw(img).text((3, 3), f'{stem[4:]} {side}', fill=(0, 0, 160))
        out.append(img)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('out')
    p.add_argument('--per', type=int, default=36)
    p.add_argument('--models')
    args = p.parse_args()
    table = json.loads((HERE / 'table.json').read_text())['models']
    stems = args.models.split(',') if args.models else sorted(
        s for s, r in table.items() if not r['mm9'] and r['body'] == 'biped')
    cols = 6
    for page in range(0, len(stems), args.per):
        chunk = stems[page:page + args.per]
        rows = (len(chunk) + cols // 2 - 1) // (cols // 2)
        sheet = Image.new('RGB', (CELL * cols, CELL * rows), 'white')
        for k, stem in enumerate(chunk):
            try:
                pair = cells(stem, HERE.parents[2] / 'assets_source' / table[stem]['path'])
            except Exception as error:  # noqa: BLE001
                print(stem, error)
                continue
            x, y = (k % (cols // 2)) * 2 * CELL, (k // (cols // 2)) * CELL
            sheet.paste(pair[0], (x, y))
            sheet.paste(pair[1], (x + CELL, y))
        name = f'{args.out}_{page // args.per + 1}.png'
        sheet.save(name)
        print(name)


if __name__ == '__main__':
    main()
