#!/usr/bin/env python3
"""Runtime body maps from the one 4K Meshy paint (mm9_bigfoot_claude/compose_bf.py): colour 2048 (Lanczos once), normal 1K,
ORM 1K (R baked AO, G Meshy roughness floored at 0.42, B Meshy metallic: the silver belt, plates, greaves and bracers). Project folder."""
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
J = Path('meshy/yan_retex_v1'); T = Path('textures')
ao = Image.open(T / 'yan_ao_4k.png').convert('L')
ao.resize((2048, 2048), Image.LANCZOS).save(T / 'yan_body_ao.png')
base = Image.open(J / 'texture_urls_0_base_color.png').convert('RGB'); print('BASE', base.size)
base.resize((2048, 2048), Image.LANCZOS).save(T / 'yan_body_raw.png')
Image.open(J / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'yan_body_normal.png')
r = np.asarray(Image.open(J / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
m = np.asarray(Image.open(J / 'texture_urls_0_metallic.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
a = np.asarray(ao.resize((1024, 1024), Image.LANCZOS), np.float32) / 255
Image.fromarray((np.stack([a, np.maximum(r, 0.42), m], -1) * 255 + .5).astype('u1')).save(T / 'yan_body_orm.png')
print('COMPOSE done', 'metal mean', round(float(m.mean()), 3), 'rough mean', round(float(r.mean()), 3))
