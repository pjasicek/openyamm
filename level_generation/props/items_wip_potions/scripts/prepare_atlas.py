"""Prepare imagegen artwork for exact UV tiles and binary metallic masks; no icon projection."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

PROJECT = Path(__file__).resolve().parents[1]
SIZE = 256


def main():
    source = Image.open(PROJECT / 'textures/potions_atlas_generated.png').convert('RGB')
    base = np.zeros((SIZE * 4, SIZE * 8, 3), np.uint8)
    orm = np.zeros_like(base)
    normal = np.full_like(base, (128, 128, 255))
    tiles = []
    for i in range(16):
        x, y = i % 4, i // 4
        box = (round(x * source.width / 4) + 5, round(y * source.height / 4) + 5,
               round((x + 1) * source.width / 4) - 5, round((y + 1) * source.height / 4) - 5)
        tile = np.asarray(source.crop(box).resize((SIZE, SIZE)), dtype=float)
        mean = tile.mean(axis=(0, 1))
        tile = mean + (tile - mean) * (0.40 if 4 <= i <= 11 else 0.65)
        tiles.append(np.clip(tile, 30, 243).astype(np.uint8))
    gold = tiles[12].astype(float)
    luminance = gold.mean(axis=2)
    filigree = luminance > np.percentile(luminance, 73)
    for i in range(32):
        original = i if i < 16 else 4 + (i - 16) % 8
        tile = tiles[original].copy()
        metallic = np.full((SIZE, SIZE), 255 if original in (0, 1, 2, 12, 14) else 0, np.uint8)
        rough = np.full((SIZE, SIZE), 90 if original in (0, 1, 2, 12, 14) else 62, np.uint8)
        if original in (3, 15):
            rough[:] = 210
        if i >= 16:
            tile[filigree] = gold[filigree]
            metallic[filigree] = 255
            rough[filigree] = 95
        if i == 24:
            tile = np.clip(tiles[7].astype(float) * (1.05, 1.65, 0.70), 30, 243).astype('uint8')
            metallic[:] = 0
            rough[:] = 62
        if i == 25:
            tile = np.clip(tiles[9].astype(float) * (0.81, 0.85, 0.86), 30, 243).astype('uint8')
            metallic[:] = 0
            rough[:] = 62
        if i == 26:
            tile = np.clip(tiles[8].astype(float) * (1.5, 0.9, 0.9), 30, 243).astype('uint8')
            metallic[:] = 0
            rough[:] = 105
        if i == 27:
            tile = tiles[6].copy()
            tile[filigree] = tiles[4][filigree]
            metallic[:] = 0
            rough[:] = 62
        if i == 28:
            tile = np.clip(tiles[8].astype(float) * (2.3, 1.0, 1.1), 30, 243).astype('uint8')
            tile[filigree] = gold[filigree]
        if i == 29:
            tile = np.clip(tiles[3].astype(float) * (0.62, 0.43, 0.28), 30, 243).astype('uint8')
            metallic[:] = 0
            rough[:] = 185
        if i == 30:
            tile = tiles[8].copy()
            tile[filigree] = tiles[6][filigree]
            metallic[:] = 0
            rough[:] = 62
        if i == 31:
            tile = tiles[6].copy()
            tile[filigree] = tiles[5][filigree]
            metallic[:] = 0
            rough[:] = 62
        if i == 0:
            tile = np.clip(tile.astype(float) * (0.82, 0.92, 0.64), 30, 243).astype('uint8')
        # Four-pixel dilation makes UV boundaries safe at lower mips.
        for array in (tile, metallic, rough):
            array[:4] = array[4:5]
            array[-4:] = array[-5:-4]
            array[:, :4] = array[:, 4:5]
            array[:, -4:] = array[:, -5:-4]
        y, x = (i // 8) * SIZE, (i % 8) * SIZE
        base[y:y + SIZE, x:x + SIZE] = tile
        orm[y:y + SIZE, x:x + SIZE] = np.stack((np.full_like(rough, 255), rough, metallic), axis=-1)
        if original in (0, 1, 2, 3, 12, 14, 15):
            height = tile.mean(axis=2) / 255
            blur = np.asarray(Image.fromarray((height * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(2))) / 255
            dy, dx = np.gradient(height - blur)
            vector = np.stack((-dx * 0.7, dy * 0.7, np.ones_like(dx)), axis=-1)
            vector /= np.linalg.norm(vector, axis=2)[..., None]
            normal[y:y + SIZE, x:x + SIZE] = ((vector * 0.5 + 0.5) * 255).astype('uint8')
    for name, data in [('basecolor', base), ('orm', orm), ('normal', normal)]:
        Image.fromarray(data).save(PROJECT / f'textures/potions_{name}.png')
    assert set(np.unique(orm[..., 2])) == {0, 255}
    assert base.min() >= 30 and base.max() <= 243
    print('Prepared 32 padded tiles, binary metal masks and OpenGL tangent normal map')


if __name__ == '__main__':
    main()
