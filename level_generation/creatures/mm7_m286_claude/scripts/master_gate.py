#!/usr/bin/env python3
"""Proportion gate of an HD master (or any front/side silhouette) against review/native_proportions.json.

Landmark rows are given by hand (picked on a gridded view, `--grid` writes one) as key=y pairs; widths are measured
from the alpha runs at those rows: the outer extent for the shoulders, the run containing the body centre for the
chest/waist/kilt (in the A-pose the arms are clear of the torso below the armpit), the two leg runs at the thigh and
shin rows, and the arm run crossing a row, corrected by the arm's angle from vertical for its thickness.
Writes review/master_gate/<name>.json and <name>_overlay.png (native x2 frame scaled to the same skull top and sole:
red = native only, cyan = master only, white = both).

Usage: master_gate.py <image> <front|side|tq> name skull_top=.. chin=.. acromion=.. deltoid=.. armpit=.. waist=..
       kilt_hip=.. kilt_hem=.. crotch=.. thigh=.. shin=.. sole=.. [arm_row=..] [horn_tip=..] [cx=..]
       master_gate.py --grid <image> <out.png>
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
X2 = P.parent / 'mm7_m286/aligned_2x'


def runs(alpha, y):
    row = np.r_[0, (alpha[int(y)] > 100).astype(int), 0]
    xs = np.flatnonzero(np.diff(row))
    return [(int(a), int(b) - 1) for a, b in zip(xs[::2], xs[1::2])]


def grid(img, out):
    im = Image.open(img).convert('RGBA')
    bg = Image.new('RGBA', im.size, (110, 110, 110, 255))
    bg.alpha_composite(im)
    d = ImageDraw.Draw(bg)
    for y in range(0, im.height, 20):
        d.line([(0, y), (im.width, y)], fill=(255, 0, 0, 255) if y % 100 == 0 else (255, 255, 0, 120), width=1)
        if y % 40 == 0:
            d.text((2, y + 1), str(y), fill=(255, 255, 255, 255))
    for x in range(0, im.width, 50):
        d.line([(x, 0), (x, im.height)], fill=(0, 255, 255, 90), width=1)
        if x % 100 == 0:
            d.text((x + 2, 2), str(x), fill=(0, 255, 255, 255))
    bg.convert('RGB').save(out)


def main():
    if sys.argv[1] == '--grid':
        grid(sys.argv[2], sys.argv[3])
        return
    img, view, name = sys.argv[1:4]
    lm = {k: float(v) for k, v in (a.split('=') for a in sys.argv[4:])}
    nat = json.loads((P / 'review/native_proportions.json').read_text())
    G = nat['gate_ratios']
    alpha = np.array(Image.open(img).convert('RGBA'))[..., 3]
    H = lm['sole'] - lm['skull_top']
    cx = lm.get('cx')
    if cx is None:
        ys, xs = np.nonzero(alpha[int(lm['waist']):int(lm['kilt_hem'])] > 100)
        cx = float(np.median(xs))
    got = {}
    if view == 'front':
        got['head_height'] = (lm['chin'] - lm['skull_top']) / H
        got['skull_top_to_acromion'] = (lm['acromion'] - lm['skull_top']) / H
        r = runs(alpha, lm['deltoid'])
        got['shoulder_width'] = (r[-1][1] - r[0][0] + 1) / H

        def central(y):
            for a, b in runs(alpha, y):
                if a <= cx <= b:
                    return b - a + 1
            return float('nan')
        got['chest_width'] = central(lm['armpit']) / H
        got['waist_width'] = central(lm['waist']) / H
        got['kilt_hip_width'] = central(lm['kilt_hip']) / H
        got['leg_crotch_height'] = (lm['sole'] - lm['crotch']) / H
        legs = [s for s in runs(alpha, lm['thigh']) if s[1] - s[0] > 0.04 * H and abs((s[0] + s[1]) / 2 - cx) < 0.3 * H]
        got['leg_outer_span_thigh'] = (legs[-1][1] - legs[0][0] + 1) / H
        got['thigh_width_single'] = float(np.mean([b - a + 1 for a, b in legs[-2:]])) / H
        shins = [s for s in runs(alpha, lm['shin']) if s[1] - s[0] > 0.02 * H and abs((s[0] + s[1]) / 2 - cx) < 0.3 * H]
        got['shin_width_single'] = float(np.mean([b - a + 1 for a, b in shins[-2:]])) / H
        if 'arm_row' in lm:
            # the arm runs are the outermost runs; angle from the run centres 0.05 H apart
            y0, y1 = lm['arm_row'], lm['arm_row'] + 0.05 * H
            ra, rb = runs(alpha, y0), runs(alpha, y1)
            ws = []
            for side in (0, -1):
                a0, a1 = ra[side], rb[side]
                c0, c1 = (a0[0] + a0[1]) / 2, (a1[0] + a1[1]) / 2
                ang = np.arctan2(abs(c1 - c0), y1 - y0)
                ws.append((a0[1] - a0[0] + 1) * np.cos(ang))
            got['upper_arm_width'] = float(np.mean(ws)) / H
        if 'forearm_row' in lm:
            y0, y1 = lm['forearm_row'], lm['forearm_row'] + 0.03 * H
            ra, rb = runs(alpha, y0), runs(alpha, y1)
            ws = []
            for side in (0, -1):
                a0, a1 = ra[side], rb[side]
                ang = np.arctan2(abs((a1[0] + a1[1]) / 2 - (a0[0] + a0[1]) / 2), y1 - y0)
                ws.append((a0[1] - a0[0] + 1) * np.cos(ang))
            got['forearm_band_width'] = float(np.mean(ws)) / H
        if 'head_row' in lm:
            for a, b in runs(alpha, lm['head_row']):
                if a <= cx <= b:
                    got['head_width_no_ears'] = (b - a + 1) / H
        if 'horn_tip' in lm:
            got['horn_rise'] = (lm['skull_top'] - lm['horn_tip']) / H
        native_frame, ncx = 'm286sa0.png', 257.5
    else:
        got['head_height'] = (lm['chin'] - lm['skull_top']) / H
        got['skull_top_to_acromion'] = (lm['acromion'] - lm['skull_top']) / H
        if 'chest_front' in lm and 'chest_back' in lm:
            got['chest_depth_side'] = abs(lm['chest_front'] - lm['chest_back']) / H
        if 'snout' in lm and 'occiput' in lm:
            got['head_length_side'] = abs(lm['snout'] - lm['occiput']) / H
        if 'horn_tip' in lm:
            got['horn_rise'] = (lm['skull_top'] - lm['horn_tip']) / H
        native_frame, ncx = ('m286sa2.png', 258.0) if view == 'side' else ('m286sa1.png', 262.0)
    table = {}
    for k, v in got.items():
        if k in G and np.isfinite(v):
            table[k] = {'native': G[k], 'master': round(float(v), 4), 'dev_pct': round(100 * (v / G[k] - 1), 1)}
    # overlay: native frame scaled to the same skull top / sole, aligned on the body centre
    rows = nat['landmark_rows_px']
    s = H / (rows['sole'] - rows['skull_top'])
    nim = Image.open(X2 / native_frame).convert('RGBA')
    nim = nim.resize((round(nim.width * s), round(nim.height * s)), Image.LANCZOS)
    na = np.zeros(alpha.shape, bool)
    ox, oy = round(cx - ncx * s), round(lm['sole'] - rows['sole'] * s)
    arr = np.array(nim)[..., 3] > 100
    y0, x0 = max(oy, 0), max(ox, 0)
    y1, x1 = min(oy + arr.shape[0], alpha.shape[0]), min(ox + arr.shape[1], alpha.shape[1])
    na[y0:y1, x0:x1] = arr[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
    ma = alpha > 100
    iou = float((na & ma).sum() / max((na | ma).sum(), 1))
    ov = np.zeros(alpha.shape + (3,), np.uint8) + 40
    ov[na & ~ma] = (230, 40, 40)
    ov[ma & ~na] = (40, 210, 230)
    ov[na & ma] = (235, 235, 235)
    im = Image.fromarray(ov)
    d = ImageDraw.Draw(im)
    for k in ('skull_top', 'chin', 'acromion', 'armpit', 'waist', 'kilt_hem', 'crotch', 'sole'):
        if k in lm:
            y = lm[k]
            d.line([(0, y), (im.width, y)], fill=(255, 220, 0), width=1)
            yn = (rows[k] - rows['sole']) * s + lm['sole']
            d.line([(0, yn), (60, yn)], fill=(255, 80, 80), width=3)
            d.text((64, yn - 6), k, fill=(255, 120, 120))
    out_dir = P / 'review/master_gate'
    out_dir.mkdir(parents=True, exist_ok=True)
    im.save(out_dir / f'{name}_overlay.png')
    worst = max((abs(v['dev_pct']) for v in table.values()), default=0)
    res = {'image': str(Path(img).resolve().relative_to(P)), 'view': view, 'landmarks_px': lm, 'H_px': H,
           'ratios': table, 'overlay_iou_vs_native_pose': round(iou, 3), 'worst_dev_pct': worst,
           'note': 'IoU is against the native POSE (arms down, axe); the master is in an A-pose, so arms lower it.'}
    (out_dir / f'{name}.json').write_text(json.dumps(res, indent=1) + '\n')
    for k, v in table.items():
        flag = '' if abs(v['dev_pct']) <= 10 else '  <-- off'
        print(f"{k:28s} native {v['native']:.3f}  master {v['master']:.3f}  {v['dev_pct']:+6.1f} %{flag}")
    print('IoU vs native pose', round(iou, 3), 'worst', worst)


if __name__ == '__main__':
    main()
