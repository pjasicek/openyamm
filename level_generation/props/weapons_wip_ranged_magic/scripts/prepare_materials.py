"""Prepare the generated UV swatches and explicit surface-semantic PBR maps."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parents[1]
NAMES = ['walnut', 'elm', 'leather', 'burgundy', 'steel', 'gold', 'bone', 'silver',
         'lapis', 'emerald', 'ruby', 'ebony', 'lacquer', 'scales', 'brass', 'ivory_scroll']
METAL = {4, 5, 7, 14}
ROUGH = [.64, .61, .73, .7, .39, .34, .58, .35, .25, .27, .24, .5, .4, .6, .43, .51]


def main():
    folder = HERE / 'textures'
    raw = Image.open(folder / 'material_atlas_raw.png').convert('RGB')
    base = Image.new('RGB', (2048, 2048))
    mr = Image.new('RGB', base.size)
    normal = Image.new('RGB', base.size)
    mask = Image.new('L', base.size)
    for i, name in enumerate(NAMES):
        x, y = i % 4, i // 4
        # Sampling insets avoid a generated cell boundary; the source artwork remains untouched.
        box = (int((x + .025) * raw.width / 4), int((y + .025) * raw.height / 4),
               int((x + .975) * raw.width / 4), int((y + .975) * raw.height / 4))
        tile = raw.crop(box).resize((512, 512), Image.Resampling.LANCZOS)
        a = np.clip(np.asarray(tile), 30, 243).astype(np.uint8)
        tile = Image.fromarray(a)
        base.paste(tile, (x * 512, y * 512))
        mr.paste(Image.new('RGB', (512, 512), (255, round(255 * ROUGH[i]), 255 if i in METAL else 0)),
                 (x * 512, y * 512))
        mask.paste(Image.new('L', (512, 512), 255 if i in METAL else 0), (x * 512, y * 512))
        # Fine grain only: remove the low frequencies rather than treating colour as shape.
        gray = tile.convert('L')
        detail = (np.asarray(gray, dtype=float) - np.asarray(gray.filter(ImageFilter.GaussianBlur(3)))) / 255
        dy, dx = np.gradient(detail)
        strength = .6 if i in METAL else 1.2
        n = np.stack((-dx * strength, dy * strength, np.ones_like(dx)), axis=2)
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        normal.paste(Image.fromarray(np.clip((n * .5 + .5) * 255, 0, 255).astype(np.uint8)),
                     (x * 512, y * 512))
    for im, name in [(base, 'base'), (mr, 'mr'), (normal, 'normal'), (mask, 'metal_mask')]:
        im.save(folder / f'weapon_{name}.png')
    assert set(np.unique(np.asarray(mask))) == {0, 255}
    assert np.asarray(base).min() >= 30 and np.asarray(base).max() <= 243
    assert np.asarray(normal)[:, :, 2].min() > 240
    (folder / 'surface_semantics.json').write_text(json.dumps([
        {'tile': i, 'surface': n, 'metallic': int(i in METAL), 'roughness': ROUGH[i]}
        for i, n in enumerate(NAMES)], indent=2) + '\n')
    print('Prepared 2048-square base/MR/+Y normal and binary metal mask; checks passed')


if __name__ == '__main__':
    main()
