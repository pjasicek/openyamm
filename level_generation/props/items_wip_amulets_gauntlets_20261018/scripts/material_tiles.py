"""Split the retained Imagegen material painting; derive restrained, seam-safe PBR detail."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

P = Path(__file__).resolve().parents[1]
NAMES = ['gold', 'silver', 'bronze', 'steel', 'ivory', 'turquoise', 'jade', 'red',
         'purple', 'amber', 'sclera', 'leather', 'patina', 'blue', 'orange', 'dark']
METALS = {'gold', 'silver', 'bronze', 'steel', 'patina'}
GEMS = {'jade', 'red', 'purple', 'amber'}

raw = Image.open(P / 'textures/material_atlas_raw.png').convert('RGB')
assert raw.width == raw.height and raw.width >= 1024
for i, name in enumerate(NAMES):
    x, y = i % 4, i // 4
    # A small inset excludes generated tile boundary antialiasing.
    tile = raw.crop((round(x * raw.width / 4) + 5, round(y * raw.height / 4) + 5,
                     round((x + 1) * raw.width / 4) - 5, round((y + 1) * raw.height / 4) - 5))
    rgb = np.clip(np.asarray(tile.resize((256, 256)), dtype=np.float32) / 255, 30 / 255, 243 / 255)
    Image.fromarray(np.uint8(np.rint(rgb * 255))).save(P / f'textures/{name}_basecolor.png')
    lum = rgb @ np.array([.2126, .7152, .0722])
    height = (lum - gaussian_filter(lum, 2)) * (.08 if name in GEMS else .35)
    dy, dx = np.gradient(height)
    normal = np.stack([-dx * 3, dy * 3, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    assert np.isfinite(normal).all() and np.allclose(np.linalg.norm(normal, axis=-1), 1)
    Image.fromarray(np.uint8(np.rint((normal * .5 + .5) * 255))).save(P / f'textures/{name}_normal.png')
    rough = .19 if name in GEMS else .6 if name == 'leather' else .34
    mr = np.zeros_like(rgb)
    mr[..., 0], mr[..., 1], mr[..., 2] = 1, rough, float(name in METALS)
    Image.fromarray(np.uint8(np.rint(mr * 255))).save(P / f'textures/{name}_mr.png')
(P / 'receipts/materials.json').write_text(json.dumps({
    'source': 'textures/material_atlas_raw.png', 'albedo': 'Imagegen painted, cropped with five-pixel inset',
    'metallic': 'Binary declared material classes; never inferred from brightness',
    'roughness': 'Declared physical material values',
    'normal': 'OpenGL tangent detail derived from high-frequency painted luminance; gem strength reduced',
    'tiles': NAMES, 'tile_size': 256}, indent=2) + '\n')
print('16 Imagegen-painted PBR materials prepared')
