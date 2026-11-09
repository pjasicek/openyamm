#!/usr/bin/env python3
"""The closed mouth's slot in paint (orchestrator review 2026-11-02, "a pale band between the lips"): after the loose lip
piece was dropped and the pocket closed (mouth_close_pm3.py, mouth_hole_fan.py) a shallow recess remains between the lips;
its walls carried pale paint (the inside of Meshy's mouth). Head texels in the mouth box lying more than 1.5 mm behind the
lips' front surface (the frontmost texel within 2 mm in x and 2.5 mm in z) take a dark lip-shadow tone (the tier's lip colour
x 0.45), feathered, so the recess reads as the line where closed lips meet. Usage: mouth_slot_paint.py <glb> <prefix> [...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
pos, cov = texel_positions(glb, 'PeasantM3Head', N)
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - 0.855
box = cov & (np.abs(bx + 0.003) < 0.025) & (bz > 0.740) & (bz < 0.758) & (by < -0.03)
iy, ix = np.nonzero(box)
# the lips' front per texel: minimum depth over a 0.5 mm (x, z) grid, then a minimum filter of +-2 mm x, +-2.5 mm z
# (bounded memory: the grid is ~120 x 50 cells)
C = 0.0005
gx = ((bx[box] + 0.04) / C).astype(int); gz = ((bz[box] - 0.73) / C).astype(int)
grid = np.full((gx.max() + 1, gz.max() + 1), np.inf)
np.minimum.at(grid, (gx, gz), by[box])
front = ndimage.minimum_filter(grid, size=(5, 7), mode="nearest")[gx, gz]   # +-1 mm x, +-1.5 mm z: walls only
# r2c: the lips stand 2-4 mm proud of the moustache skin, so depth alone took that skin too: the slot is deeper than 6 mm,
# or deeper than 2 mm on a surface that does not face forward (|n_y| < 0.6; normals from the raster's position gradients)
P3 = np.stack([bx, by, bz], -1)
nrm = np.cross(np.gradient(P3, axis=1), np.gradient(P3, axis=0))
nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-12)
dep = by[box] - front
deep = (dep > 0.006) | ((dep > 0.002) & (np.abs(nrm[box][:, 1]) < 0.6))
# r4: the shallow groove left where the mouth is closed (mouth_v13: interior 1.5 mm behind the lips) is the meeting line
groove_t = np.zeros_like(deep)   # r4: off (curvature put lip and moustache surfaces in the band too)
slot = np.zeros_like(box); slot[iy[deep], ix[deep]] = True
soft = ndimage.gaussian_filter(slot.astype(float), 1.8) * cov
lipzone = box & ~slot & (np.abs(bx + 0.003) < 0.02)
for p in prefixes:
    f = Path(f'textures/{p}_head_basecolor.png')
    img = np.asarray(Image.open(f).convert('RGB'), float)
    lips = img[lipzone]
    lip = np.median(lips[(lips[:, 0] > lips[:, 1] * 1.25)], 0) if (lips[:, 0] > lips[:, 1] * 1.25).any() else np.median(lips, 0)
    # r3: the walls read as lip turning into the mouth: lip colour where the wall is shallow, darkening to x0.55 only on the
    # deepest part (a thin meeting line), so the lips look closed rather than parted round a dark gap
    lipm = lip * 0.85 + np.array([lip.mean()] * 3) * 0.15
    dd = np.zeros(img.shape[:2]); dd[iy, ix] = dep
    kd = np.clip((dd - 0.006) / 0.010, 0, 1)[..., None]
    wall = lipm * (1 - 0.2 * kd)      # r3b: the recess's own shading darkens it already
    out = img * (1 - soft[..., None]) + wall * soft[..., None]
    gm = np.zeros(img.shape[:2]); gm[iy[groove_t], ix[groove_t]] = 1.0
    gs = np.clip(ndimage.gaussian_filter(gm, 1.2) * 1.3, 0, 1)[..., None] * cov[..., None]
    out = out * (1 - gs) + (lipm * 0.62) * gs
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f)
    print('MOUTHSLOT', p, 'slot texels', int(slot.sum()), 'lip', lip.round())
