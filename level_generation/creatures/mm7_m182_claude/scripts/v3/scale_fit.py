"""Binding scale from silhouettes: model renders (motion_render_v3.py at REF native px/m) vs the restored MM7 x2
frames of the same native frame and view. (1) area: sqrt(native area / model area) over all frames/views;
(2) IoU: best uniform zoom of the model silhouettes (with the best translation per image) maximising mean IoU.
Binding scale = native px per m x 5.0 (tier-A frame scale). Usage: scale_fit.py <render_dir> <ref px/m> [out.json]"""
import json, sys
import numpy as np
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[2]; NAT = P.parent / 'mm7_m182/aligned_2x'
R = Path(sys.argv[1]); REF = float(sys.argv[2]); S = 768
NOWING = '--nowing' in sys.argv; sys.argv = [x for x in sys.argv if x != '--nowing']; MASK = P.parent / 'mm7_m182/masks_2x'
index = json.loads((R / 'index.json').read_text())


def pad(a):
    c = np.zeros((S, S), bool); h, w = a.shape; c[(S - h) // 2:(S - h) // 2 + h, (S - w) // 2:(S - w) // 2 + w] = a; return c


def iou_best(m, n):
    F = np.fft.rfft2(n.astype(float)); G = np.fft.rfft2(m.astype(float)); c = np.fft.irfft2(F * np.conj(G), s=n.shape)
    iy, ix = np.unravel_index(np.argmax(c), c.shape); mm = np.roll(np.roll(m, iy, 0), ix, 1)
    return float((mm & n).sum() / max((mm | n).sum(), 1))


pairs = []
for e in index:
    n = np.asarray(Image.open(NAT / f"m182{e['frame']}{e['view']}.png").convert('RGBA'))[..., 3] > 127
    if NOWING:   # drop the native membranes (restored region mask G = membranes and spines)
        g = np.asarray(Image.open(MASK / f"m182{e['frame']}{e['view']}.png").convert('RGB'))[..., 1] > 127
        n = n & ~g
    m = Image.open(R / f"{e['clip']}_{e['frame']}{e['view']}_sil.png").convert('RGBA').getchannel('A')
    pairs.append((e, pad(n), m))
area = np.sqrt(sum(p[1].sum() for p in pairs) / sum((np.asarray(p[2]) > 127).sum() for p in pairs))
best = None; curve = {}
for f in np.arange(area * .8, area * 1.2, area * .02):
    ious = []
    for e, n, m in pairs:
        w = max(1, int(round(m.size[0] * f))); mm = pad(np.asarray(m.resize((w, w), Image.BILINEAR)) > 127) if w <= S else None
        ious.append(iou_best(mm, n) if mm is not None else 0)
    curve[round(float(f), 4)] = round(float(np.mean(ious)), 4)
    if best is None or np.mean(ious) > best[1]: best = (f, float(np.mean(ious)))
doc = {'ref_native_px_per_m': REF, 'area_factor': float(area), 'area_native_px_per_m': float(area * REF), 'area_binding': float(area * REF * 5),
       'iou_factor': float(best[0]), 'iou_native_px_per_m': float(best[0] * REF), 'iou_binding': float(best[0] * REF * 5), 'iou_mean': best[1],
       'curve': curve, 'frames': len(pairs)}
print(json.dumps({k: v for k, v in doc.items() if k != 'curve'}))
if len(sys.argv) > 3: Path(sys.argv[3]).write_text(json.dumps(doc, indent=1) + '\n')
