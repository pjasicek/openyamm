"""Prepare imagegen material paintings for glTF: 512px PNG, explicit palette variants and OpenGL normals.

Raw returns stay unchanged under textures/raw. Palette variants share only genuine geometry/material families.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parents[1]
TEXTURES = HERE / 'textures'
ROUGHNESS = {'bone': 0.8, 'bone_pale': 0.8, 'bone_dark': 0.85, 'egg': 0.88,
             'horn': 0.6, 'enamel': 0.38, 'signet': 0.55, 'crystal': 0.24}
CRYSTALS = {'item270': (222, 140, 43), 'item271': (157, 159, 218),
            'item272': (191, 193, 184), 'item273': (75, 178, 88)}


def write_maps(name, rgb, kind):
    rgb = np.clip(rgb, 30, 243).astype(np.uint8)
    Image.fromarray(rgb).save(TEXTURES / (name + '.png'))
    grey = Image.fromarray(rgb).convert('L')
    detail = (np.asarray(grey, dtype=float) - np.asarray(grey.filter(ImageFilter.GaussianBlur(2)), dtype=float)) / 255
    dy, dx = np.gradient(detail)
    normal = np.stack((-dx * 2, dy * 2, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    normal = np.clip((normal * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    mr = np.zeros_like(rgb)
    mr[:, :, 0] = 255
    mr[:, :, 1] = np.clip((ROUGHNESS[kind] - detail * 0.15) * 255, 0, 255).astype(np.uint8)
    Image.fromarray(normal).save(TEXTURES / (name + '_normal.png'))
    Image.fromarray(mr).save(TEXTURES / (name + '_mr.png'))
    assert rgb.shape == (512, 512, 3) and 30 <= rgb.min() <= rgb.max() <= 243
    assert mr[:, :, 2].max() == 0
    assert np.allclose(np.linalg.norm(normal.astype(float) / 127.5 - 1, axis=-1), 1, atol=0.015)


def main():
    for kind in ('bone', 'egg', 'horn', 'enamel', 'signet', 'crystal'):
        path = TEXTURES / 'raw' / (kind + '.png')
        if not path.exists():
            continue
        image = Image.open(path).convert('RGB').resize((512, 512), Image.Resampling.LANCZOS)
        rgb = np.asarray(image, dtype=float)
        write_maps(kind, rgb, kind)
        if kind == 'bone':
            luminance = rgb.mean(axis=-1, keepdims=True)
            write_maps('bone_pale', luminance * 0.8 + np.array([65, 63, 53]), 'bone_pale')
            write_maps('bone_dark', rgb * 0.53 + np.array([18, 18, 20]), 'bone_dark')
        if kind == 'crystal':
            luminance = rgb.mean(axis=-1, keepdims=True)
            for icon, colour in CRYSTALS.items():
                write_maps('crystal_' + icon, luminance / 195 * colour, 'crystal')
    print('Prepared available material maps; raw imagegen returns preserved.')


if __name__ == '__main__':
    main()
