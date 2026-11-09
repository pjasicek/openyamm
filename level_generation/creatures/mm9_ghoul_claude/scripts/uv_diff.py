"""Per face: mean colour in the old layout (Meshy 2K grade) against the new one, and UV overlap in the new layout. Finds charts that landed on another chart's texels."""
import sys; sys.path.insert(0, 'scripts')
import numpy as np
from PIL import Image
import project_lib as PL
Fo = np.load('work/faces_oldlayout.npz'); R = np.load('work/repack.npz')
idx = R['body']; uvn = R['uvn']; uvo = Fo['uvb'][idx]; co = Fo['co'][idx]
S = 2048
a = np.asarray(Image.open('textures/old_layout/ghoul_basecolor_graded.png').convert('RGB'), np.float32) / 255
b = np.asarray(Image.open('textures/ghoul_basecolor_graded.png').convert('RGB'), np.float32) / 255
W = np.array([[.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [1 / 3, 1 / 3, 1 / 3]])
pa = (W[None] @ uvo)                                 # F,4,2
pb = (W[None] @ uvn)
ca = PL.sample(a, pa); cb = PL.sample(b, pb)
d = np.abs(ca - cb).sum(2).mean(1)
print('faces', len(d), 'colour diff p50 %.3f p99 %.3f' % (np.median(d), np.percentile(d, 99)), 'over .35:', int((d > 0.35).sum()))
bad = np.argsort(-d)[:14]
for f in bad: print(round(float(d[f]), 2), np.round(co[f].mean(0), 3).tolist(), 'part', int(Fo['part'][idx][f]))
# overlap: texels claimed by two faces
cnt = np.zeros((S, S), np.int32)
from PIL import ImageDraw
for f, u in enumerate(uvn):
    im = Image.new('1', (1, 1))
    x = u[:, 0] * S; y = (1 - u[:, 1]) * S
    x0, x1, y0, y1 = int(x.min()), int(x.max()) + 1, int(y.min()), int(y.max()) + 1
    gx, gy = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
    dd = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(dd) < 1e-9: continue
    a1 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / dd
    b1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / dd
    m = (a1 >= 0) & (b1 >= 0) & (a1 + b1 <= 1)
    cnt[np.clip(y0, 0, S - 1):np.clip(y1, 0, S), np.clip(x0, 0, S - 1):np.clip(x1, 0, S)] += m[:cnt[np.clip(y0, 0, S - 1):np.clip(y1, 0, S), np.clip(x0, 0, S - 1):np.clip(x1, 0, S)].shape[0], :cnt[np.clip(y0, 0, S - 1):np.clip(y1, 0, S), np.clip(x0, 0, S - 1):np.clip(x1, 0, S)].shape[1]].astype(np.int32)
print('texels used', int((cnt > 0).sum()), 'overlapped', int((cnt > 1).sum()), 'share %.4f' % ((cnt > 1).sum() / max((cnt > 0).sum(), 1)))
