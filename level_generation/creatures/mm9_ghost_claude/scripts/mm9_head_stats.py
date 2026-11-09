"""From the MM9 model: the head's back and width profile (work/mm9_head_profile.npz, in the master's bind frame) and the skin's hair colour per tier: the texels the back half of head1 maps to (work/mm9_hair.json).
Answers whether MM9's heads have hair: they do, on all three skins. Run from the project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
out = {}
for k in (1, 2, 3):
    g = Glb(f'source/tier{k}/ghost{k}.glb')
    doc = g.json
    m = next(x for x in doc['meshes'] if x['name'] == 'head1')['primitives'][0]
    P = g.accessor(m['attributes']['POSITION']).astype(np.float64)
    T = g.accessor(m['indices']).astype(int).reshape(-1, 3) if 'indices' in m else np.arange(len(P)).reshape(-1, 3)
    UV = g.accessor(m['attributes']['TEXCOORD_0']).astype(np.float64)
    # glTF (x, y up, z forward) -> the master's Blender frame (x, -z, y): the head faces -y
    B = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
    if k == 1:
        rng = np.random.default_rng(1)
        w = rng.dirichlet((1, 1, 1), 400)
        S = np.einsum('fvc,sv->fsc', B[T], w).reshape(-1, 3)
        zs = np.linspace(0.495, 0.725, 12)
        ymax = np.array([S[np.abs(S[:, 2] - z) < 0.016, 1].max() for z in zs])
        xmax = np.array([np.abs(S[(np.abs(S[:, 2] - z) < 0.016) & (S[:, 1] > -0.16), 0]).max() if ((np.abs(S[:, 2] - z) < 0.016) & (S[:, 1] > -0.16)).any() else np.abs(S[np.abs(S[:, 2] - z) < 0.016, 0]).max() for z in zs])
        np.savez('work/mm9_head_profile.npz', z=zs, ymax=ymax, xmax=xmax)
    im = Image.new('L', (256, 256), 0); dr = ImageDraw.Draw(im)
    back = B[T].mean(1)[:, 1] > -0.17
    for t in UV[T[back]]:
        dr.polygon([(float(u) * 256, float(v) * 256) for u, v in t], fill=255)
    mask = np.asarray(im) > 0
    skin = np.asarray(Image.open(f'source/tier{k}/skins/ghost{k}.png').convert('RGB'), np.float64) / 255
    px = skin[mask]
    L = px @ np.array([0.3, 0.59, 0.11])
    hs = float(((px.max(1) - px.min(1)) / np.maximum(px.max(1), 1e-3)).mean())
    # strand contrast: luminance against its blur
    from scipy import ndimage
    Lf = skin @ np.array([0.3, 0.59, 0.11]); fine = Lf - ndimage.gaussian_filter(Lf, 3)
    out[str(k)] = {'rgb': px.mean(0).round(4).tolist(), 'lum': round(float(L.mean()), 4), 'std': round(float(L.std()), 4), 'strand_std': round(float(fine[mask].std()), 4), 'sat': round(hs, 3), 'texels': int(mask.sum())}
    print('MM9 hair tier', k, out[str(k)])
json.dump(out, open('work/mm9_hair.json', 'w'), indent=1)
