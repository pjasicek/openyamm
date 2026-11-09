"""Side/front X-ray: our raw mesh points (soles on MM9's floor) vs MM9's mesh and joints. Args: <raw npz> <mm9 glb> <mm9 npz> <out png> [Z0]"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from PIL import Image, ImageDraw
raw, mm9, mnpz, out = sys.argv[1:5]; Z0 = float(sys.argv[5]) if len(sys.argv) > 5 else -0.923
D = np.load(raw); co = D['co'] + [0, 0, Z0]; comp = D['comp']
M = np.load(mnpz); mc = M['co']
m = Model(Glb(mm9)); nn = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn)}
S = 450; W = 900; img = Image.new('RGB', (2 * W, W), 'white'); d = ImageDraw.Draw(img)
pal = [(31,119,180),(255,127,14),(44,160,44),(214,39,40),(148,103,189),(140,86,75),(227,119,194),(127,127,127),(188,189,34),(23,190,207)]
for k, (i, sgn) in enumerate(((1, -1), (0, 1))):
    ox = k * W + W / 2
    def P(p): return (ox + sgn * p[i] * S, W / 2 - p[2] * S)
    sl = np.abs(co[:, 0]) < 0.03 if i == 1 else np.ones(len(co), bool)
    for p, c in zip(co[sl], comp[sl]):
        x, y = P(p); d.point((x, y), fill=pal[c % 10])
    for p in mc[np.abs(mc[:, 0]) < 0.03] if i == 1 else mc:
        x, y = P(p); d.ellipse((x-1, y-1, x+1, y+1), fill='black')
    for n, p in MJ.items():
        if not (n.startswith('FHP') or n.startswith('Bip01')): continue
        x, y = P(p); d.ellipse((x-3, y-3, x+3, y+3), fill='red')
        if any(q in n for q in ('Spine', 'Neck', 'Head', 'Pelvis', 'UpperArm', 'Forearm', 'Hand', 'Calf', 'Foot')) and ' L ' not in n:
            d.text((x + 4, y - 4), n.replace('FHP ', '').replace('Bip01 ', ''), fill='red')
d.text((10, 10), 'mid slice |x|<3cm, side: front to the RIGHT', fill='black'); d.text((W + 10, 10), 'front view', fill='black')
img.save(out)
for n in ('FHP Pelvis', 'FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck', 'FHP Head', 'FHP R UpperArm', 'FHP R Forearm', 'FHP R Hand', 'FHP R Calf', 'FHP R Foot', 'XCOM_skirt'):
    if n in MJ: print(n, MJ[n].round(3))
