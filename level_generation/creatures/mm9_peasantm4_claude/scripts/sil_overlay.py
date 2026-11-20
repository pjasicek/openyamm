"""Silhouette overlay of two MM9 ABC meshes (bind pose) + per-vertex distance map of A to B.
Usage: sil_overlay.py <stemA> <stemB> <out.png>. Red = A only, green = B only, yellow = both.
Right panels: A's vertices coloured by distance to B's surface (0 .. 6 cm, blue->red), front and side."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import mm9_meshcmp as mc  # noqa
from scipy.spatial import cKDTree

a, b, out = sys.argv[1:4]
ma, pa, ra, ta = mc.load(a)
mb, pb, rb, tb = mc.load(b)
S = 900
lo = np.minimum(pa.min(0), pb.min(0)); hi = np.maximum(pa.max(0), pb.max(0))
# MM9: y up; x and z horizontal
span = (hi - lo).max() * 1.05
def proj(p, view):
    h = p[:, 0] if view == 'front' else p[:, 2]
    v = p[:, 1]
    return np.stack([(h - (lo[0] if view == 'front' else lo[2]) + (span - ((hi - lo)[0] if view == 'front' else (hi - lo)[2])) / 2) / span * S,
                     S - (v - lo[1] + (span - (hi - lo)[1]) / 2) / span * S], 1)
def mask(p, t, view):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im); q = proj(p, view)
    for tri in t:
        d.polygon([tuple(q[i]) for i in tri], fill=255)
    return np.asarray(im) > 0
tree = cKDTree(mc.surface_samples(pb, tb)); dist, _ = tree.query(pa)
panels = []
for view in ('front', 'side'):
    A = mask(pa, ta, view); B = mask(pb, tb, view)
    rgb = np.full((S, S, 3), 50, np.uint8)
    rgb[A & ~B] = (230, 40, 40); rgb[B & ~A] = (40, 200, 40); rgb[A & B] = (200, 200, 90)
    panels.append(Image.fromarray(rgb))
for view in ('front', 'side'):
    im = Image.new('RGB', (S, S), (50, 50, 50)); d = ImageDraw.Draw(im); q = proj(pa, view)
    order = np.argsort(dist)
    for i in order:
        t = min(dist[i] / 6.0, 1.0)
        c = (int(255 * t), int(80 * (1 - abs(t - 0.5) * 2)), int(255 * (1 - t)))
        d.ellipse([q[i, 0] - 3, q[i, 1] - 3, q[i, 0] + 3, q[i, 1] + 3], fill=c)
    panels.append(im)
sheet = Image.new('RGB', (S * 4, S)); [sheet.paste(p, (i * S, 0)) for i, p in enumerate(panels)]
ImageDraw.Draw(sheet).text((8, 8), f'red={a} only  green={b} only   dist {a}->{b} 0..6 cm (blue..red)', fill=(255, 255, 255))
sheet.save(out)
for r in mc.REGIONS:
    s = ra == r
    print(r, 'p50 %.1f p90 %.1f max %.1f' % (np.percentile(dist[s], 50), np.percentile(dist[s], 90), dist[s].max()))
