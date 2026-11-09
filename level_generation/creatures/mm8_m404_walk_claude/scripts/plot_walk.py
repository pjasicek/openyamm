"""Plot pelvis / chest / head height and world yaw, and the lowest sole points, over one Walking cycle, installed
(dashed) vs new (solid), from sample_clips.py data. PIL only. Usage: plot_walk.py <installed.npz> <new.npz> <out.png>"""
import sys, numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation as R

a, b, out = sys.argv[1:4]
W_, H_, PAD = 1100, 300, 60
img = Image.new('RGB', (W_, 3 * H_ + 40), (250, 250, 250)); dr = ImageDraw.Draw(img)
COL = {'B_Pelvis': (31, 119, 180), 'B_Spine2': (44, 160, 44), 'B_Head': (214, 39, 40),
       'L sole': (148, 103, 189), 'R sole': (255, 127, 14)}
series = {0: [], 1: [], 2: []}
for path, dashed, lab in ((a, True, 'installed'), (b, False, 'new')):
    d = np.load(path); n = list(d['names']); ix = {x: i for i, x in enumerate(n)}; Wm = d['Walking_world']
    f = np.arange(len(Wm)) / (len(Wm) - 1) * 38.4
    for bone in ('B_Pelvis', 'B_Spine2', 'B_Head'):
        z = Wm[:, ix[bone], 2, 3]; series[0].append((f, (z - z.mean()) * 100, COL[bone], dashed, f'{lab} {bone}'))
        Rs = R.from_matrix(Wm[:, ix[bone], :3, :3]); e = (Rs * Rs.mean().inv()).as_euler('ZXY', degrees=True)
        series[1].append((f, e[:, 0], COL[bone], dashed, f'{lab} {bone}'))
    lows = d['Walking_lows']
    series[2].append((f, lows[:, 0] * 100, COL['L sole'], dashed, f'{lab} left sole'))
    series[2].append((f, lows[:, 1] * 100, COL['R sole'], dashed, f'{lab} right sole'))
titles = ['height about cycle mean (cm)', 'world yaw about cycle mean (deg)', 'lowest sole point (cm)']
for p in range(3):
    y0 = 30 + p * H_; top, bot = y0 + 22, y0 + H_ - 30
    lo = min(s[1].min() for s in series[p]); hi = max(s[1].max() for s in series[p]); span = (hi - lo) or 1
    lo -= span * .08; hi += span * .08
    X = lambda fr: PAD + (W_ - PAD - 20) * fr / 38.4
    Y = lambda v: bot - (bot - top) * (v - lo) / (hi - lo)
    dr.rectangle([PAD, top, W_ - 20, bot], outline=(160, 160, 160))
    for k in range(0, 39, 4):
        dr.line([X(k), bot, X(k), bot + 4], fill=(90, 90, 90)); dr.text((X(k) - 6, bot + 6), str(k), fill=(60, 60, 60))
    for v in np.linspace(lo, hi, 5):
        dr.text((6, Y(v) - 6), f'{v:5.1f}', fill=(60, 60, 60)); dr.line([PAD, Y(v), W_ - 20, Y(v)], fill=(228, 228, 228))
    if lo < 0 < hi:
        dr.line([PAD, Y(0), W_ - 20, Y(0)], fill=(180, 180, 180))
    dr.text((PAD, y0 + 4), titles[p], fill=(0, 0, 0))
    lx = PAD + 330
    for j, (fx, fy, c, dashed, lab) in enumerate(series[p]):
        pts = [(X(x), Y(y)) for x, y in zip(fx, fy)]
        for i in range(len(pts) - 1):
            if dashed and (i // 3) % 2:
                continue
            dr.line([pts[i], pts[i + 1]], fill=c, width=1 if dashed else 2)
        dr.text((lx + (j % 3) * 230, y0 + 4 + (j // 3) * 0), '', fill=c)
    for j, (fx, fy, c, dashed, lab) in enumerate(series[p]):
        dr.text((lx + (j % 3) * 230 - 300 * 0, top + 4 + (j // 3) * 12), ('- - ' if dashed else '___ ') + lab, fill=c)
dr.text((PAD, 3 * H_ + 14), 'MM8 Lizardman Warrior Walking (0.8 s): installed dashed, new solid. x = viewer frame (48 fps).',
        fill=(0, 0, 0))
img.save(out)
