"""Source faces that straddle a colour boundary on the torso: body-atlas faces (u < 0.5) whose base-colour samples
contain both skin and dark leather (the bodice neckline and armholes), or gold against anything (bracer rims). The collapse moves such a boundary into a
zigzag at any cut. -> work/edge_faces.npy (OR'd with the given keep set). Usage: edge_faces.py <keep in> <keep out>"""
import sys
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; w = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB')).astype(float) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 24)
uv = np.einsum('sk,fkc->fsc', B, w)
x = np.clip((uv[..., 0] * W).astype(int), 0, W - 1); y = np.clip(((1 - uv[..., 1]) * H).astype(int), 0, H - 1)
c = img[y, x]; r, g, b = c[..., 0], c[..., 1], c[..., 2]
skin = (r > .55) & (g > r * .58) & (g < r * .82) & (b > r * .4)  # not the orange studs
dark = (r + g + b) / 3 < .22
z = d['verts'][f].mean(1)[:, 2]
gold = (r > .6) & (g > .5) & (b < .35) & (g > r * .75)
body = (w.mean(1)[:, 0] < .5) & (z > .9) & (z < 1.45)
edge = body & (skin.mean(1) > .12) & (dark.mean(1) > .12)
armx = np.abs(d['verts'][f].mean(1)[:, 0]) > .2  # arms only: the bodice studs are gold dots on leather
rims = (w.mean(1)[:, 0] < .5) & (z > .8) & (z < 1.45) & armx & (gold.mean(1) > .12) & (gold.mean(1) < .88)  # bracer/armband rims: gold against leather or skin
print('RIMS', int((rims & ~edge).sum()))
edge |= rims
keep = np.load(sys.argv[1]) | edge
print('EDGE', int(edge.sum()), 'faces; keep', int(keep.sum())); np.save('work/edge_faces.npy', edge); np.save(sys.argv[2], keep)
