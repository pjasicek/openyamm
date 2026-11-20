import sys, numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
src = open('scripts/seam_fix.py').read()
exec(src[src.index('T = Path'):src.index('PT, CT = raster')])
PT, CT = raster(MAT == 1, 2048); PL, CL = raster(MAT == 0, 2048)
import json
sys.path.insert(0,'../claude_shared'); import tier_textures as TT
R = json.load(open(T / 'thrall_ramps.json')); e=R['materials'][0]
base = np.asarray(Image.open(T / 'thrall_limbs_final.png').convert('RGB'), np.float64) / 255
mask = np.stack([np.asarray(ch.resize((2048, 2048), Image.BILINEAR), np.float64) / 255 for ch in Image.open(T / 'thrall_region_mask.png').convert('RGBA').split()], -1)
L = np.clip(TT.apply(base, mask, e['ramps']['thrall_b']), 0, 1)
o, f = Z['Lu'], Z['Lf']; u = (f - o) / np.linalg.norm(f - o)
st = (PT - o) @ u; sl = (PL - o) @ u
A = np.asarray(Image.open(T/'thrall_torso_b_final.png').convert('RGB')).copy(); B=(L*255).astype('u1').copy()
mt = CT & (PT[..., 0] > 0) & (st > 0.0) & (st < 0.11) & (PT[...,2]>0.3); ml = CL & (PL[..., 0] > 0) & (sl < 0.16)&(PL[...,2]>0.3)
ys,xs=np.nonzero(mt); print('T bbox',xs.min(),xs.max(),ys.min(),ys.max())
ys2,xs2=np.nonzero(ml); print('L bbox',xs2.min(),xs2.max(),ys2.min(),ys2.max())
A[~mt] = A[~mt] // 5; B[~ml] = B[~ml] // 5
Image.fromarray(A).save('work/_sv_t.png'); Image.fromarray(B).save('work/_sv_l.png')
s=Image.new('RGB',(2000,1000)); s.paste(Image.fromarray(A).resize((1000,1000)),(0,0)); s.paste(Image.fromarray(B).resize((1000,1000)),(1000,0)); s.save('work/_sv.png')
