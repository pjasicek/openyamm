"""Sheets for the close-up and dress fixes (2026-11-01), from review-viewer shots at identical cameras.
closeups <out png> <skins...>: per skin two rows (texture pass r1, r2), columns eyes front/3/4, mouth front/3/4,
  nose front/3/4 (shots cu_<skin>_<tag>_{ef,eq,mf,mq,nf,nq}.png).
dress <out png>: rows HD master, installed r1, r2; columns front, left, 3/4 Standing, then the same views mid-walk
  for r1 and r2 (shots dr_<tag>_<view>_<clip>.png)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
S = HERE / 'review' / 'shots'
REF = HERE / 'references_hd'
mode, out = sys.argv[1], sys.argv[2]


def cell(path, size, box=None):
    im = Image.open(path).convert('RGB')
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    im.thumbnail(size, Image.Resampling.LANCZOS)
    return im


def grid(rows, labels, size, out_path):
    W, H = size
    sheet = Image.new('RGB', (150 + W * max(len(r) for r in rows), H * len(rows)), (24, 26, 30))
    d = ImageDraw.Draw(sheet)
    for r, (row, label) in enumerate(zip(rows, labels)):
        d.text((6, r * H + H // 2 - 8), label, fill=(235, 235, 235))
        for c, im in enumerate(row):
            if im is not None:
                sheet.paste(im, (150 + c * W + (W - im.width) // 2, r * H + (H - im.height) // 2))
    sheet.save(out_path)
    print('SHEET', out_path, sheet.size)


if mode == 'closeups':
    rows, labels = [], []
    for skin in sys.argv[3:]:
        for tag, name in (('tp', 'pass r1'), ('fix', 'r2 close-up fix')):
            rows.append([cell(S / f'cu_{skin}_{tag}_{v}.png', (340, 250), (0.12, 0.05, 0.88, 0.95))
                         for v in ('ef', 'eq', 'mf', 'mq', 'nf', 'nq')])
            labels.append(f'm342_{skin}\n{name}')
    grid(rows, labels, (344, 254), out)
else:
    views = ('front', 'left', 'quarter')
    refs = {'front': '01_front.png', 'left': '03_left.png', 'quarter': '00_three_quarter.png'}
    rows = [[cell(REF / refs[v], (330, 420)) for v in views] + [None] * 3]
    labels = ['HD master']
    for tag, name in (('tp', 'installed r1'), ('fix', 'r2 dress fix')):
        rows.append([cell(S / f'dr_{tag}_{v}_{c}.png', (330, 420), (0.22, 0.0, 0.78, 1.0))
                     for c in ('stand', 'walk') for v in views])
        labels.append(f'{name}\nStanding | mid-walk')
    grid(rows, labels, (334, 424), out)
