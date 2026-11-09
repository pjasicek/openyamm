#!/usr/bin/env python3
"""Torso part images, 1536 in TorsoUV, one per tier (the only per-tier images: bare chest / vest / mail).
A: tier A's paint moved from the body atlas (4K Meshy colour, graded like the body) into TorsoUV. B: Meshy's torso-only paint. C: the Codex masters projected, see project_tier.py.
Also fits the limb ramps of B and C: masters projected on the shared atlas against tier A's paint.
Args: none (project folder). Reads work/faces.npz."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
import project_lib as PL
F = np.load('work/faces.npz')
TX = Path('textures')
S = 1536
tors = F['torso'] > 0
uvt, co = F['uvt'][tors], F['co'][tors]
pos, nor, cov, bar, fid = PL.raster(uvt, co, S)
print('torso coverage %.3f' % cov.mean())
uvb = F['uvb'][tors]
# atlas uv per torso texel
auv = (bar[..., None] * uvb[fid]).sum(2)
Image.MAX_IMAGE_PIXELS = None
atlas = np.asarray(Image.open(TX / 'zombie4k_final.png').convert('RGB'), np.float32) / 255
A = PL.sample(atlas, auv)
def pad(img): 
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True); return img[iy, ix]
Image.fromarray((pad(A) * 255 + 0.5).astype('u1')).save(TX / 'zombie_torso_a.png')
Bim = Image.open(TX / 'zombie_torso_b_basecolor_final.png').convert('RGB')
if Bim.size != (S, S): Bim = Bim.resize((S, S), Image.LANCZOS)
Bim.save(TX / 'zombie_torso_b.png')
# C: masters
proj, have, rep = PL.project('references_tiers/c_', pos, nor, cov, F['co'], fine=True)
print('C', rep, 'unseen', int((cov & ~have).sum()))
_, (iy, ix) = ndimage.distance_transform_edt(~have, return_indices=True)
C = proj[iy, ix]
import soft_detail_tone as SD
C = SD.tone(C)
Image.fromarray((pad(C) * 255 + 0.5).astype('u1')).save(TX / 'zombie_torso_c_raw.png')
np.savez('work/torso_map.npz', pos=pos, cov=cov)
