import sys, numpy as np
from PIL import Image
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
from pygltflib import GLTF2
N = 1024
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2', N)
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
a_ = g.accessors[sk.inverseBindMatrices]; bv = g.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
J = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}
print('NECK', J['Bip01 Neck'], 'HEAD', J['Bip01 Head'], 'SPINE2', J['Bip01 Spine2'])
img = np.asarray(Image.open('textures/pdm2_tp_basecolor_graded.png').convert('RGB').resize((N, N)), float)
P = np.nan_to_num(pos); nk = J['Bip01 Neck']
rad = np.hypot(P[..., 0] - nk[0], P[..., 2] - nk[2]); y = P[..., 1]
lum = img @ [0.299, 0.587, 0.114]
for y0 in np.arange(0.80, 0.98, 0.02):
    for r0 in (0.06, 0.08, 0.10, 0.12, 0.14):
        m = cov & (y >= y0) & (y < y0 + 0.02) & (rad >= r0 - 0.02) & (rad < r0)
        if m.sum() > 20:
            print('y %.2f r<%.2f n %5d lum %5.1f rgb %s' % (y0, r0, m.sum(), np.median(lum[m]), np.median(img[m], 0).round()))
m = cov & (y > float(sys.argv[2])) & (rad < float(sys.argv[3]))
ys, xs = np.nonzero(m)
y0, y1, x0, x1 = max(ys.min() - 20, 0), min(ys.max() + 20, N), max(xs.min() - 20, 0), min(xs.max() + 20, N)
dbg = img.copy(); dbg[m] = dbg[m] * 0.5 + np.array([0, 255, 0]) * 0.5
s = np.concatenate([img[y0:y1, x0:x1], dbg[y0:y1, x0:x1]], 1)
Image.fromarray(np.uint8(s)).resize((s.shape[1] * 2, s.shape[0] * 2), Image.NEAREST).save('review/collar_probe.png')
print('BOX', y0, y1, x0, x1, int(m.sum()))
