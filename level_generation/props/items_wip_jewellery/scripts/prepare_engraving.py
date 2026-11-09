"""Bake painted UV trim into flat albedo, material masks and relightable engraved normals."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[1]
source = Image.open(PROJECT / 'references/jewellery_trim_painted.png').convert('RGB').resize((2048, 1024))
for tile in range(8):
    x, y = tile % 4 * 512, tile // 4 * 512
    raw = np.asarray(source.crop((x + 6, y + 6, x + 506, y + 506)).resize((512, 512)), float) / 255
    luminance = raw @ np.array([.2126, .7152, .0722])
    gold = (raw[:, :, 0] > raw[:, :, 2] * 1.4) & (raw[:, :, 1] > .25)
    leather = np.zeros((512, 512), bool)
    if tile in (2, 4):
        leather = ~gold
    enamel = (~gold) if tile == 7 else np.zeros((512, 512), bool)
    metal = ~(leather | enamel)
    if tile in (0, 6):
        gold[:] = True
    base = np.where(gold[..., None], np.array([196, 149, 66]), np.array([174, 182, 190])).astype(float)
    base[leather] = [77, 43, 30]
    base[enamel] = [108, 30, 43]
    # Painted shading becomes surface relief; retain only subtle material wear in albedo.
    base *= (.94 + .06 * luminance)[..., None]
    base = np.clip(base, 30, 243).astype(np.uint8)
    Image.fromarray(base).save(PROJECT / f'textures/jewellery_trim_{tile}_base.png')
    packed = np.empty_like(base)
    packed[:, :, 0] = 255
    packed[:, :, 1] = np.where(metal, 80 + luminance * 24, np.where(enamel, 28, 185))
    packed[:, :, 2] = metal * 255
    assert set(np.unique(packed[:, :, 2])).issubset({0, 255})
    Image.fromarray(packed).save(PROJECT / f'textures/jewellery_trim_{tile}_mr.png')
    height = np.asarray(Image.fromarray((luminance * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7)), float)
    dy, dx = np.gradient(height / 255)
    normal = np.stack((-dx * 5, dy * 5, np.ones_like(dx)), axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    encoded = np.clip(np.round((normal * .5 + .5) * 255), 0, 255).astype(np.uint8)
    Image.fromarray(encoded).save(PROJECT / f'textures/jewellery_trim_{tile}_normal.png')
    assert np.isfinite(normal).all() and np.allclose(np.linalg.norm(normal, axis=2), 1)
    if tile < 4:
        for suffix in ('base', 'mr', 'normal'):
            original = Image.open(PROJECT / f'textures/jewellery_trim_{tile}_{suffix}.png').resize((128, 128))
            strip = Image.new('RGB', (1024, 128))
            for repeat in range(8):
                strip.paste(original, (repeat * 128, 0))
            strip.save(PROJECT / f'textures/jewellery_trim_{tile}_band_{suffix}.png')
print('Eight UV trim sets: flat albedo, binary metallic masks, OpenGL tangent normals')
