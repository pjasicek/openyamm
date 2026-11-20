#!/usr/bin/env python3
"""Proportion guide images for the Codex HD-master brief (v2 masters).

The native x2 standing front (m286sa0) and right profile (m286sa2) are scaled onto the 1024x1536 master canvas so that
the hoof soles sit at y=1450 and the skull top at y=350 (H = 1100 px), with the measured landmark rows and width bars
from review/native_proportions.json drawn over them, plus the A-pose arm axes the masters should use.
Writes references_hd/guide_front.png and references_hd/guide_side.png.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[1]
X2 = P.parent / 'mm7_m286/aligned_2x'
W, HT = 1024, 1536
SOLE_Y, SKULL_Y = 1450, 350
STERNUM_X = 257.5


def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                 '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def place(frame, centre_x):
    nat = json.loads((P / 'review/native_proportions.json').read_text())
    rows = nat['landmark_rows_px']
    s = (SOLE_Y - SKULL_Y) / (rows['sole'] - rows['skull_top'])
    im = Image.open(X2 / frame).convert('RGBA')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    ox = 512 - centre_x * s
    oy = SOLE_Y - rows['sole'] * s
    canvas = Image.new('RGBA', (W, HT), (128, 128, 128, 255))
    canvas.alpha_composite(im, (round(ox), round(oy)))
    return canvas, nat, s, ox, oy


def label_rows(draw, nat, s, oy, names):
    f = font(22)
    rows = nat['landmark_rows_px']
    for key, text in names:
        y = rows[key] * s + oy
        draw.line([(0, y), (W, y)], fill=(255, 230, 0, 255), width=2)
        draw.text((8, y - 26), f'{text}  ({nat["landmark_heights_over_H"][key]:.2f} H)', fill=(255, 255, 0, 255),
                  font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))


def bar(draw, x0, x1, y, text, colour=(0, 220, 255, 255)):
    draw.line([(x0, y), (x1, y)], fill=colour, width=5)
    draw.line([(x0, y - 12), (x0, y + 12)], fill=colour, width=4)
    draw.line([(x1, y - 12), (x1, y + 12)], fill=colour, width=4)
    draw.text((x1 + 8, y - 12), text, fill=colour, font=font(20), stroke_width=2, stroke_fill=(0, 0, 0, 255))


def main():
    canvas, nat, s, ox, oy = place('m286sa0.png', STERNUM_X)
    d = ImageDraw.Draw(canvas)
    label_rows(d, nat, s, oy, [('horn_tip', 'HORN TIPS'), ('skull_top', 'SKULL TOP'), ('chin', 'CHIN'),
                               ('acromion', 'SHOULDER LINE'), ('armpit', 'ARMPIT'), ('waist', 'WAIST'),
                               ('kilt_hem', 'KILT HEM'), ('crotch', 'LEGS SEPARATE'), ('sole', 'HOOF SOLES')])
    widths = nat['widths_over_H']
    H = SOLE_Y - SKULL_Y
    rows = nat['landmark_rows_px']
    for key, row, text in [('shoulder_width', 'deltoid', 'SHOULDERS %.2f H'),
                           ('chest_width', 'armpit', 'CHEST %.2f H'),
                           ('waist_width', 'waist', 'WAIST %.2f H'),
                           ('kilt_hip_width', 'kilt_hip', 'KILT %.2f H'),
                           ('leg_outer_span_thigh', 'thigh', 'LEGS %.2f H')]:
        half = widths[key] * H / 2
        bar(d, 512 - half, 512 + half, rows[row] * s + oy + 14, text % widths[key])
    # A-pose arm axes: from the shoulder joint, 33 degrees from vertical, acromion-to-fingertip about 0.45 H.
    sh_y = (rows['acromion'] + 10) * s + oy
    sh_half = (widths['shoulder_width'] / 2 - 0.055) * H
    for side in (-1, 1):
        x0 = 512 + side * sh_half
        length = 0.45 * H
        a = math.radians(33)
        x1, y1 = x0 + side * length * math.sin(a), sh_y + length * math.cos(a)
        d.line([(x0, sh_y), (x1, y1)], fill=(255, 60, 200, 255), width=6)
    d.text((560, 1500), 'magenta = A-pose arm axes (33 deg)', fill=(255, 60, 200, 255), font=font(20),
           stroke_width=2, stroke_fill=(0, 0, 0, 255))
    canvas.convert('RGB').save(P / 'references_hd/guide_front.png')

    canvas, nat, s, ox, oy = place('m286sa2.png', 258.0)
    d = ImageDraw.Draw(canvas)
    label_rows(d, nat, s, oy, [('horn_tip', 'HORN TIP'), ('skull_top', 'SKULL TOP'), ('chin', 'CHIN'),
                               ('acromion', 'SHOULDER LINE'), ('armpit', 'ARMPIT'), ('kilt_hem', 'KILT HEM'),
                               ('knee', 'KNEE (forward)'), ('hock', 'HOCK (backward)'), ('sole', 'HOOF SOLES')])
    for key, row, text in [('chest_depth_side', 'armpit', 'CHEST DEPTH %.2f H'),
                           ('head_length_side', 'eyes', 'HEAD LENGTH %.2f H')]:
        x0 = {'chest_depth_side': 218.0, 'head_length_side': 235.0}[key]
        bar(d, (x0 - 258.0) * s + 512, (x0 - 258.0) * s + 512 + widths[key] * H, rows[row] * s + oy + 14,
            text % widths[key])
    canvas.convert('RGB').save(P / 'references_hd/guide_side.png')


if __name__ == '__main__':
    main()
