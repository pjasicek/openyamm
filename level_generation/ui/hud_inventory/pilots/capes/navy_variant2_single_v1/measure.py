"""Measure actual contour extrema and fold cross-sections; this does not approve artwork."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d, binary_erosion
from scipy.signal import find_peaks
P = Path(__file__).resolve().parent
HUD = P.parents[2]
sys.path.insert(0, str(HUD))
from freeze_targets import rendered
from finalize_classification import ROOT, digest
native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/6cape2v2a.bmp'), 'item').resize(
    (262, 500), Image.Resampling.NEAREST)
restored = Image.open(P / '6cape2v2a.png').convert('RGBA')
results = []
proof = Image.new('RGB', (1048, 430), '#333333')
draw = ImageDraw.Draw(proof)
for i, im in enumerate([native, restored]):
    a = np.asarray(im)
    mask = a[:, :, 3] >= 128
    ys, xs = np.where(mask)
    extrema = dict(apex=[float(np.median(xs[ys == ys.min()])), int(ys.min())],
                   lowest=[float(np.median(xs[ys == ys.max()])), int(ys.max())])
    left_top = np.where(mask[:, :120])[0].min()
    extrema['left_collar_apex'] = [float(np.median(np.where(mask[left_top, :120])[0])), int(left_top)]
    lum = a[:, :, :3] @ [.2126, .7152, .0722]
    rows = {}
    for y in [340, 380, 420]:
        line = gaussian_filter1d(lum[y-2:y+3].mean(axis=0), 2)
        peaks, _ = find_peaks(line, prominence=1.5, distance=8)
        rows[y] = [[int(x), round(float(line[x]), 3)] for x in peaks if 60 < x < 200]
    edge = (a[:, :, 3] > 0) & ~binary_erosion(mask, iterations=4)
    rgb = a[:, :, :3].astype(float)
    excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
    results.append(dict(label=['native', 'restored'][i], extrema=extrema, fold_peaks=rows,
                        contour_magenta_max=float(excess[edge].max()),
                        contour_pixels_above2=int(((excess > 2) & edge).sum())))
    tile = Image.new('RGBA', im.size, '#333333')
    tile.alpha_composite(im)
    proof.paste(tile.crop((0, 300, 262, 500)).resize((524, 400)), (i * 524, 24))
    draw.text((i * 524, 4), ['native lower folds', 'restored lower folds'][i], fill='white')
proof.save(P / 'lower-fold-comparison.png')
record = dict(artifact_sha256=digest(P / '6cape2v2a.png'), script_sha256=digest(Path(__file__)),
              method='Alpha128 contour extrema; five-row luminance mean with Gaussian sigma2, peak prominence1.5.',
              measurements=results)
(P / 'feature-measurements.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
