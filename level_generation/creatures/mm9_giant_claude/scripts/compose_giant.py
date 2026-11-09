#!/usr/bin/env python3
"""Runtime body maps from the one 4K Meshy paint: colour 2048 (Lanczos once), normal 1K, ORM 1K. Project folder."""
from pathlib import Path
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
J = Path('meshy/giant_retex_v1'); T = Path('textures')
ao = Image.open(T / 'gi_ao_4k.png').convert('L')
ao.resize((2048, 2048), Image.LANCZOS).save(T / 'gi_body_ao.png')
base = Image.open(J / 'texture_urls_0_base_color.png').convert('RGB'); print('BASE', base.size)
base.resize((2048, 2048), Image.LANCZOS).save(T / 'gi_body_raw.png')
Image.open(J / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'gi_body_normal.png')
r = np.asarray(Image.open(J / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
a = np.asarray(ao.resize((1024, 1024), Image.LANCZOS), np.float32) / 255
Image.fromarray((np.stack([a, np.maximum(r, 0.5), np.zeros_like(r)], -1) * 255 + .5).astype('u1')).save(T / 'gi_body_orm.png')
print('COMPOSE done')
