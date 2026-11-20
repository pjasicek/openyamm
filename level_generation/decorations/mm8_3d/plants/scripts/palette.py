"""Print each sprite's mean colour and its main colour clusters (sRGB 0-255, k-means): python3 palette.py ids..."""
import sys
import numpy as np
from PIL import Image
from scipy.cluster.vq import kmeans2
ROOT = __import__('pathlib').Path(__file__).resolve().parents[5]
for sid in sys.argv[1:]:
    im = np.asarray(Image.open(ROOT / f'assets_dev/engine/decorations_x2/{sid}_p335.png').convert('RGBA')).astype(np.float32)
    px = im[im[..., 3] > 128][:, :3]
    np.random.seed(1)
    c, lab = kmeans2(px, 7, minit='++', seed=1)
    order = np.argsort(-np.bincount(lab, minlength=7))
    print(sid, 'mean', px.mean(0).round().astype(int).tolist(), ' '.join(
        f'{c[k].round().astype(int).tolist()}:{(lab == k).mean():.2f}' for k in order))
