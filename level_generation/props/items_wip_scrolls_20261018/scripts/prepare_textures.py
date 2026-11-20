"""Crop the purpose-built Imagegen parchment atlas and pack one PBR material per icon."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

P = Path(__file__).resolve().parents[1]
DONOR = P.parent / 'items_wip_amulets_gauntlets_20261018/textures'
NAMES = ['written_aged', 'written_ivory', 'ochre', 'taupe', 'blue', 'vine', 'arcane', 'vellum', 'reverse']
DESIGNS = {'item264': (0, 'bronze', 'red'), 'item265': (1, 'bronze', 'red'),
           'scroll1': (2, 'bronze', 'red'), 'scroll2': (3, 'steel', 'red'),
           'scroll3': (4, 'bronze', 'red'), 'scroll4': (5, 'bronze', 'red'),
           'scroll5': (6, 'gold', 'purple'), '7item182': (7, 'bronze', 'red'),
           '7item251': (7, 'bronze', 'red')}


def main():
    raw_path = P / 'references/parchment_atlas_raw.png'
    raw = Image.open(raw_path).convert('RGB')
    assert raw.width == raw.height and raw.width >= 1024
    tiles = []
    for i, name in enumerate(NAMES):
        x, y = i % 3, i // 3
        box = (round(x * raw.width / 3) + 4, round(y * raw.height / 3) + 4,
               round((x + 1) * raw.width / 3) - 4, round((y + 1) * raw.height / 3) - 4)
        tile = raw.crop(box).resize((256, 256), Image.Resampling.LANCZOS)
        tiles.append(np.clip(np.array(tile), 30, 243).astype(np.uint8))
        Image.fromarray(tiles[-1]).save(P / 'textures' / f'{name}.png')
    reused = []
    for name in ('gold', 'bronze', 'steel', 'purple', 'red'):
        for suffix in ('basecolor', 'mr', 'normal'):
            source = DONOR / f'{name}_{suffix}.png'
            target = P / 'references' / source.name
            shutil.copy2(source, target)
            reused.append({'source': str(source), 'copy': str(target.relative_to(P)),
                           'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    for icon, (tile, metal, trim) in DESIGNS.items():
        base = np.empty((512, 512, 3), dtype=np.uint8)
        # Decorative scrolls carry their dyed parchment on both sides; written letters have a plain reverse.
        reverse = tiles[8] if icon in ('item264', 'item265') else tiles[tile]
        paper = [tiles[tile], reverse]
        layout_path = P / 'work' / f'uv_{icon}.json'
        layout = json.loads(layout_path.read_text()) if layout_path.exists() else {}
        if layout:
            # Fit each painting to the physically proportional UV rectangle, then dilate its edge gutters.
            usize, vsize = layout['u_size'], layout['v_size']
            x0, x1 = [round(256 * (.025 + .95 * (.5 + s * usize / 2))) for s in (-1, 1)]
            y0, y1 = [round(256 * (.025 + .95 * (.5 + s * vsize / 2))) for s in (-1, 1)]
            fitted = []
            for rgb in paper:
                content = np.array(Image.fromarray(rgb).resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS))
                fitted.append(np.pad(content, ((y0, 256 - y1), (x0, 256 - x1), (0, 0)), mode='edge'))
            paper = fitted
        base[:256, :256], base[:256, 256:] = paper
        for name, x in ((metal, 0), (trim, 256)):
            image = Image.open(P / 'references' / f'{name}_basecolor.png').convert('RGB')
            base[256:, x:x + 256] = np.array(image.resize((256, 256)))
        if icon == 'scroll5':
            # Painted gold embroidery on the purple textile collar; binary metal mask follows these stitches.
            purple = base[256:, 256:].copy()
            yy, xx = np.indices((256, 256))
            embroidery = (abs((xx + yy // 2) % 64 - 32) < 3) | (xx < 9) | (xx > 246)
            gold = base[256:, :256]
            purple[embroidery] = gold[embroidery]
            base[256:, 256:] = purple
        base = np.clip(base, 30, 243).astype(np.uint8)
        mr = np.zeros_like(base)
        mr[..., 0], mr[..., 1] = 255, 213
        mr[256:, :256, 1], mr[256:, :256, 2] = 90, 255
        mr[256:, 256:, 1] = 155
        if icon == 'scroll5':
            mr[256:, 256:, 2] = embroidery.astype(np.uint8) * 255
            mr[256:, 256:, 1] = np.where(embroidery, 90, 190)
        normal = np.zeros_like(base)
        for x, y in ((0, 0), (256, 0), (0, 256), (256, 256)):
            rgb = base[y:y + 256, x:x + 256] / 255
            lum = rgb @ np.array([.2126, .7152, .0722])
            # Restrain parchment fibres; handwritten ink stays nearly flush with the sheet.
            height = (lum - gaussian_filter(lum, 1.4, mode='reflect')) * .10
            dy, dx = np.gradient(height)
            n = np.stack([-dx * 3, dy * 3, np.ones_like(dx)], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            assert np.allclose(np.linalg.norm(n, axis=-1), 1)
            normal[y:y + 256, x:x + 256] = np.rint((n * .5 + .5) * 255).astype(np.uint8)
        for suffix, pixels in (('basecolor', base), ('mr', mr), ('normal', normal)):
            Image.fromarray(pixels).save(P / 'textures' / f'{icon}_{suffix}.png')
        assert set(np.unique(mr[..., 2])) <= {0, 255}
    receipt = {'tool': 'built-in image_gen.imagegen', 'prompt': 'references/atlas_prompt.txt',
               'retained_image': str(raw_path.relative_to(P)),
               'sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
               'maps': '512-square basecolor, packed MR and OpenGL tangent normal per icon',
               'derivation': 'Measured 3x3 crop, inset and resize; 2x2 packed UV regions with internal gutters. '
                             'Physical roughness and binary metallic masks; restrained high-frequency fibre normals.',
               'donor_materials': reused, 'designs': DESIGNS}
    (P / 'receipts/textures.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('Prepared', len(DESIGNS), 'one-material PBR atlases')


if __name__ == '__main__':
    main()
