"""Hair faces whose UV triangle covers cap-blue or light texels (blue: b > r + 0.08 and b > 0.25; light: max > 0.45),
sampled densely including the edges. Compares a ladder mesh with the source hair. Usage: hair_blue.py <mesh npz> [group]"""
import sys, numpy as np
from PIL import Image
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
w = np.array([(a, b, 1 - a - b) for a in np.linspace(0, 1, 9) for b in np.linspace(0, 1, 9) if a + b <= 1])


def bad(uv):
    p = np.einsum('kj,fjc->fkc', w, uv) % 1.0
    x = np.clip((p[..., 0] * W).astype(int), 0, W - 1); y = np.clip(((1 - p[..., 1]) * H).astype(int), 0, H - 1)
    c = img[y, x]; blue = (c[..., 2] > c[..., 0] + .08) & (c[..., 2] > .25); light = c.max(-1) > .45
    return (blue | light).mean(1)


if __name__ == '__main__':
    src = np.load('work/mesh_in.npz'); comp = np.load('work/comp.npy')
    s = np.isin(comp, [11, 12, 16]); bs = bad(src['wuv'].reshape(-1, 3, 2)[s])
    print('source hair faces', s.sum(), 'with >10% bad texels', (bs > .1).sum())
    d = np.load(sys.argv[1]); g = d['group'] == int(sys.argv[2] if len(sys.argv) > 2 else 1)
    uv = d['wuv'].reshape(-1, 3, 2); c = d['verts'][d['faces']].mean(1)
    bd = bad(uv[g]); idx = np.where(g)[0]
    print('candidate group faces', g.sum(), 'with >10% bad texels', (bd > .1).sum())
    for i in np.argsort(-bd)[:12]:
        print(idx[i], round(float(bd[i]), 2), c[idx[i]].round(3))
