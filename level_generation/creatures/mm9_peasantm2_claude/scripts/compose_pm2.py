#!/usr/bin/env python3
"""PeasantM2 runtime maps from the 4K Meshy paints (from mm9_njam_claude/scripts/compose_nj.py). Project folder.
Body job pm2_retex_body on the one upload layout: torso square u 0..ST, limbs square u ST..1, both from v 0, crops resized once (Lanczos).
Head jobs pm2_retex_head_a / _b on the head upload (HeadUV 0..1): colour 4K -> 1792 once per tier, normal 1K per tier, ORM flat-ish from
Meshy's roughness. Writes textures/pm2_{torso,limbs}_raw.png, _normal.png, _orm.png, pm2_head_{t}_raw.png, pm2_head_{t}_normal.png, pm2_head_orm.png."""
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ST, SL = 0.55, 0.45
M = Path('meshy'); T = Path('textures'); T.mkdir(exist_ok=True)
def crop(im, part, size, resample=Image.LANCZOS):
    W, H = im.size
    box = (0, H * (1 - ST), W * ST, H) if part == 'torso' else (W * ST, H * (1 - SL), W, H)
    return im.resize((size, size), resample, box=box)
ao = Image.open(T / 'pm2_ao_4k.png').convert('L') if (T / 'pm2_ao_4k.png').exists() else None
if ao:
    crop(ao, 'torso', 2048).save(T / 'pm2_torso_ao.png'); crop(ao, 'limbs', 1792).save(T / 'pm2_limbs_ao.png')
j = M / 'pm2_retex_body'
base = Image.open(j / 'texture_urls_0_base_color.png').convert('RGB')
nrm = Image.open(j / 'texture_urls_0_normal.png').convert('RGB')
rough = Image.open(j / 'texture_urls_0_roughness.png').convert('L')
for part, size in (('torso', 2048), ('limbs', 1792)):
    crop(base, part, size).save(T / f'pm2_{part}_raw.png')
    a_ = np.array(crop(nrm, part, 1024)); a_[..., 1] = 255 - a_[..., 1]       # Meshy +y down -> glTF +y up
    Image.fromarray(a_).save(T / f'pm2_{part}_normal.png')
    r = np.asarray(crop(rough, part, 1024), np.float32) / 255
    a = np.asarray(crop(ao, part, 1024), np.float32) / 255 if ao else np.ones_like(r)
    orm = np.stack([a, np.maximum(r, 0.5), np.zeros_like(r)], -1)
    Image.fromarray((orm * 255 + .5).astype('u1')).save(T / f'pm2_{part}_orm.png')
for t in 'ab':
    j = M / f'pm2_retex_head_{t}'
    if not j.exists(): continue
    Image.open(j / 'texture_urls_0_base_color.png').convert('RGB').resize((1792, 1792), Image.LANCZOS).save(T / f'pm2_head_{t}_raw.png')
    a_ = np.array(Image.open(j / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS)); a_[..., 1] = 255 - a_[..., 1]
    Image.fromarray(a_).save(T / f'pm2_head_{t}_normal.png')
    if t == 'a':
        r = np.asarray(Image.open(j / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
        orm = np.stack([np.ones_like(r), np.maximum(r, 0.55), np.zeros_like(r)], -1)
        Image.fromarray((orm * 255 + .5).astype('u1')).save(T / 'pm2_head_orm.png')
print('COMPOSE done')
