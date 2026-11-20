"""Session-local native/enhanced palette contacts, with original 2x pixels and R8 coverage."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('family')
root = Path(__file__).resolve().parent.parent / parser.parse_args().family
assert not (root / 'review/acceptance.json').exists(), 'Frozen accepted family'
sources = json.loads((root / 'sources.json').read_text())
registration = json.loads((root / 'registration.json').read_text())
palettes = list(map(int, sources['palette_sources']))
evidence = []


def composite(im):
    out = Image.new('RGBA', im.size, '#343438')
    out.alpha_composite(im)
    return out.convert('RGB')


for name, record in registration.items():
    master = Image.open(root / 'aligned_2x' / (name + '.png')).convert('RGBA')
    alpha = np.asarray(master)[:, :, 3]
    mask = Image.open(root / 'masks_2x' / (name + '.png')).convert('L')
    assert mask.size == master.size
    assert not np.asarray(mask)[alpha == 0].any(), name
    native_canvas = Image.new('RGBA', master.size)
    native_base = Image.open(root / 'native_variants' / f'{name}_{sources["base_palette"]}.png').convert('RGBA')
    origin = record['canvas_origin_px']
    native_canvas.alpha_composite(native_base.resize((native_base.width * 2, native_base.height * 2), Image.Resampling.NEAREST), (-origin[0], -origin[1]))
    union = Image.new('RGBA', master.size)
    union.alpha_composite(native_canvas)
    union.alpha_composite(master)
    x0, y0, x1, y1 = union.getbbox()
    crop = (max(0, x0 - 4), max(0, y0 - 4), min(master.width, x1 + 4), min(master.height, y1 + 4))
    width, height = crop[2] - crop[0], crop[3] - crop[1]
    panel = Image.new('RGB', ((width + 8) * 3, (height + 24) * len(palettes)), '#343438')
    draw = ImageDraw.Draw(panel)
    for row, palette in enumerate(palettes):
        preview = Image.open(root / 'previews' / f'{name}_{palette}.png').convert('RGBA')
        assert preview.size == master.size and np.array_equal(np.asarray(preview)[:, :, 3], alpha), name
        if palette == sources['base_palette']:
            assert np.array_equal(np.asarray(preview), np.asarray(master)), name
        native = Image.open(root / 'native_variants' / f'{name}_{palette}.png').convert('RGBA')
        canvas = Image.new('RGBA', master.size)
        canvas.alpha_composite(native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST), (-origin[0], -origin[1]))
        for col, (label, tile) in enumerate([
            (f'{name} native ACT {palette}', composite(canvas.crop(crop))),
            (f'enhanced ACT {palette} 2x', composite(preview.crop(crop))),
            ('enhanced RGB-authored R8', mask.crop(crop).convert('RGB')),
        ]):
            x, y = col * (width + 8), row * (height + 24)
            draw.text((x + 3, y + 3), label, fill='white')
            panel.paste(tile, (x + 4, y + 20))
    file = f'review/palette_pose_{name}.png'
    panel.save(root / file)
    evidence.append(file)

record = dict(status='visual_review_pending', frames=len(registration), palettes=palettes,
    alpha_unchanged=True, mask_outside_alpha_zero=True, base_exact_bypass=True,
    material_masks='Enhanced RGB and native ACT colour samples; no resized spatial native mask',
    evidence=evidence)
(root / 'review/palette_checks.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: value for key, value in record.items() if key != 'evidence'}))
