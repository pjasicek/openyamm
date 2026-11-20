"""Pack generated albedo for belt UV strips and book cover; no icon projections."""
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
TEXTURES = PROJECT / 'textures'
TEXTURES.mkdir(exist_ok=True)
source = Image.open(PROJECT / 'references/jewellery_leather.png').convert('L').resize((128, 128))
grain = np.asarray(source, np.float32) / 128
for name, colour in {
    'brown': (91, 55, 35), 'tan': (133, 92, 58), 'black': (40, 38, 42),
    'green': (44, 91, 47), 'red': (112, 32, 45), 'pink': (107, 55, 83), 'blue': (35, 47, 96),
}.items():
    rgb = np.clip(grain[..., None] * np.array(colour), 30, 243).astype(np.uint8)
    rgb = np.tile(rgb, (1, 8, 1))
    assert rgb.shape == (128, 1024, 3)
    Image.fromarray(rgb).save(TEXTURES / f'leather_{name}.png')
cover = np.asarray(Image.open(PROJECT / 'references/jewellery_item211_cover.png').convert('RGB').resize((1024, 1024)))
cover = np.clip(cover, 30, 243).astype(np.uint8)
Image.fromarray(cover).save(TEXTURES / 'jewellery_item211_cover.png')
maximum = cover.max(axis=2).astype(float)
minimum = cover.min(axis=2).astype(float)
saturation = (maximum - minimum) / np.maximum(maximum, 1)
gold = (cover[:, :, 0].astype(float) > cover[:, :, 2] * 1.3) & (maximum > 100)
silver = (saturation < .40) & (maximum > 100)
metal = gold | silver
mr = np.empty_like(cover)
mr[:, :, 0] = 255
mr[:, :, 1] = np.where(metal, 125, 200)
mr[:, :, 2] = metal * 255
assert set(np.unique(mr[:, :, 2])) == {0, 255}
Image.fromarray(mr).save(TEXTURES / 'jewellery_item211_mr.png')
rows = np.arange(128)[:, None]
grain = .92 + .08 * np.cos(rows * 2.4)
pages = np.tile(np.clip(grain[..., None] * np.array([211, 199, 170]), 30, 243), (1, 1024, 1)).astype(np.uint8)
Image.fromarray(pages).save(TEXTURES / 'jewellery_pages.png')
print('Prepared seven leather strips, book albedo, binary metal mask and page edges')
