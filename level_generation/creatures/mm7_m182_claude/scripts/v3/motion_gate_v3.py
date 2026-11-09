"""v3 motion gate (copy of scripts/motion_gate.py; renders from scripts/v3/motion_render_v3.py: the cdr1 clips at the
MM7 native frame times mapped by scripts/v3/clipmap.py). Writes review/motion_gate.json (v2: review/motion_gate_v2.json).


Per native frame and view: silhouette IoU of the model render against the restored x2 frame (alpha > 0.5, both on a
576 px canvas, 1 x2 pixel per pixel), after the best integer translation (FFT correlation; the native sprites float
above their anchor while the model hangs from the actor origin). Sheets: review/motion_vs_native/<clip>.png, one row
per native frame, each view as x2 frame | model (textured, aligned). Writes review/motion_gate.json.
Usage: motion_gate.py <render_dir>"""
import json, sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[2]; NATIVE = P.parent / 'mm7_m182/aligned_2x'; OUT = P / 'review/motion_vs_native'; OUT.mkdir(parents=True, exist_ok=True)
R = Path(sys.argv[1]); index = json.loads((R / 'index.json').read_text()); S = 576


def native(frame, view):
    im = Image.open(NATIVE / f'm182{frame}{view}.png').convert('RGBA'); w, h = im.size
    canvas = Image.new('RGBA', (S, S), (0, 0, 0, 0)); canvas.paste(im, ((S - w) // 2, (S - h) // 2)); return canvas


def shift(model, nat):
    F = np.fft.rfft2(nat.astype(float)); G = np.fft.rfft2(model.astype(float)); c = np.fft.irfft2(F * np.conj(G), s=nat.shape)
    iy, ix = np.unravel_index(np.argmax(c), c.shape); return (iy - S if iy > S // 2 else iy), (ix - S if ix > S // 2 else ix)


rows = {}; gate = {}
for e in index:
    clip, frame, view = e['clip'], e['frame'], e['view']
    nat = native(frame, view); nm = np.asarray(nat)[..., 3] > 127
    sil = np.asarray(Image.open(R / f'{clip}_{frame}{view}_sil.png').convert('RGBA'))[..., 3] > 127
    dy, dx = shift(sil, nm); m = np.roll(np.roll(sil, dy, 0), dx, 1)
    iou = float((m & nm).sum() / max((m | nm).sum(), 1))
    gate.setdefault(clip, {}).setdefault(frame, {})[str(view)] = round(iou, 4)
    tex = Image.open(R / f'{clip}_{frame}{view}_tex.png').convert('RGBA')
    tex = Image.fromarray(np.roll(np.roll(np.asarray(tex), dy, 0), dx, 1))
    rows.setdefault(clip, {}).setdefault(frame, []).append((view, nat, tex, iou))
summary = {}
for clip, frames in gate.items():
    per_frame = {f: round(float(np.mean(list(v.values()))), 4) for f, v in frames.items()}
    summary[clip] = {'mean_iou': round(float(np.mean(list(per_frame.values()))), 4), 'min_frame_iou': min(per_frame.values()), 'per_frame_mean': per_frame,
                     'per_frame_per_view': frames}
v2 = json.loads((P / 'review/motion_gate_v2.json').read_text())['clips']
doc = {'v2_mean_iou': {k: v['mean_iou'] for k, v in v2.items()}, 'method': 'silhouette IoU vs restored x2 frames (alpha > 0.5, 576 px canvas, best translation), views 0-4 (death frames da-dd: view 0 only, as in game)',
       'renders': str(R), 'clips': summary}
(P / 'review/motion_gate.json').write_text(json.dumps(doc, indent=1) + '\n')
bg = (88, 88, 92)
for clip, frames in rows.items():
    cell = 192; cols = max(len(v) for v in frames.values())
    sheet = Image.new('RGB', (cols * 2 * cell, len(frames) * (cell + 18)), bg); d = ImageDraw.Draw(sheet)
    for r, (frame, items) in enumerate(frames.items()):
        for c, (view, nat, tex, iou) in enumerate(items):
            for k, im in enumerate((nat, tex)):
                b = Image.new('RGBA', (S, S), bg + (255,)); b.alpha_composite(im); b = b.convert('RGB').resize((cell, cell), Image.LANCZOS)
                sheet.paste(b, ((2 * c + k) * cell, r * (cell + 18) + 18))
            d.text((2 * c * cell + 4, r * (cell + 18) + 3), f'm182{frame}{view} | {clip} model   IoU {iou:.2f}', fill=(255, 255, 160))
    sheet.save(OUT / f'{clip}.png')
print('MOTION_GATE', {c: (v['mean_iou'], v['min_frame_iou']) for c, v in summary.items()})
