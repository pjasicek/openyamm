"""Unresized native/restored palette probes for material boundaries."""
from PIL import Image, ImageDraw
import session_workflow as w


shared = w.load_module('palette_probe_shared', w.REPO / 'level_generation/creatures/mm7_m514/process.py')
for number in (332, 342, 352):
    root = w.SESSION / f'mm7_m{number}'
    sources = w.read(root / 'sources.json')
    variants = w.read(root / 'variants.json')['variants']
    registration = w.read(root / 'registration.json')
    cases = (('sa0', (180, 235, 340, 395)), ('wa0', (180, 235, 340, 395)),
             ('ne0', (180, 235, 340, 395)), ('wa2', (160, 250, 320, 410)),
             ('ne2', (160, 250, 320, 410)), ('wg2', (220, 250, 380, 410))) if number == 332 else (
             ('sa0', (190, 145 if number == 342 else 35, 350, 305 if number == 342 else 195)),
             ('sa4', (190, 145 if number == 342 else 35, 350, 305 if number == 342 else 195)),
             ('ne0', (190, 195 if number == 342 else 85, 350, 355 if number == 342 else 245)))
    for page, start in enumerate(range(0, len(variants), 5)):
        subset = variants[start:start + 5]
        out = Image.new('RGB', (320 * len(subset), 190 * len(cases)), (230, 230, 230))
        draw = ImageDraw.Draw(out)
        for row, (suffix, box) in enumerate(cases):
            name = f'm{number}{suffix}'
            base = Image.open(root / f'aligned_2x/{name}.png').convert('RGBA')
            mask = Image.open(root / f'masks_2x/{name}.png')
            origin = registration[name]['canvas_origin_px']
            for col, variant in enumerate(subset):
                native, _ = w.native_2x(sources['sources'][name], sources, variant['palette_id'])
                enhanced = shared.apply_variant(base, mask, variant)
                for side, im in enumerate((native.crop(box), enhanced.crop(
                        [box[k] - origin[k % 2] for k in range(4)]))):
                    bg = Image.new('RGBA', im.size, (230, 230, 230, 255))
                    bg.alpha_composite(im)
                    out.paste(bg.convert('RGB'), (col * 320 + side * 160, row * 190 + 22))
                draw.text((col * 320 + 2, row * 190 + 2),
                          f'{name} palette {variant["palette_id"]}: native / restored', fill='black')
        out.save(root / f'review/palette_detail_100_{page}.png')
