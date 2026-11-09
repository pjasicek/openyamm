"""Review-only grids retaining native coordinates on both sides."""
from PIL import Image, ImageDraw
from session import SESSION, read, native_2x

out = SESSION / 'mm8_m408' / 'redo_2x'
sources = read(out.parent / 'sources.json')
records = read(out / 'registration.json')
run = read(out / 'run.json')
for view in range(5):
    job = next(j for j in run['jobs'] if j['id'] == f'attack_{view}_sheet')
    for label, names in [('last_two', job['frames'][-2:]), ('middle_two', job['frames'][2:4])]:
        items, boxes = [], []
        for name in names:
            rec = records[name]
            sides = [(native_2x(sources['sources'][name], sources, sources['base_palette'])[0], (0, 0)),
                     (Image.open(out / 'aligned_2x' / f'{name}.png').convert('RGBA'), rec['canvas_origin_px'])]
            for im, origin in sides:
                b = im.getbbox()
                boxes.append([b[0] + origin[0], b[1] + origin[1], b[2] + origin[0], b[3] + origin[1]])
            items.append((name, sides))
        x0, y0 = min(b[0] for b in boxes) - 12, min(b[1] for b in boxes) - 12
        x1, y1 = max(b[2] for b in boxes) + 12, max(b[3] for b in boxes) + 12
        w, h = x1 - x0, y1 - y0
        panel = Image.new('RGB', (w * 2 + 60, (h + 35) * 2), (36, 40, 38))
        draw = ImageDraw.Draw(panel)
        for row, (name, sides) in enumerate(items):
            for side, (im, origin) in enumerate(sides):
                px, py = 20 + side * (w + 20), 30 + row * (h + 35)
                tile = Image.new('RGBA', (w, h))
                tile.alpha_composite(im, (origin[0] - x0, origin[1] - y0))
                panel.paste(tile, (px, py), tile)
                draw.text((px, py - 23), name + (' native 2x' if side == 0 else ' restored 2x'), fill='white')
                for x in range((x0 // 40 + 1) * 40, x1, 40):
                    draw.line((px + x - x0, py, px + x - x0, py + h), fill=(64, 70, 68))
                    draw.text((px + x - x0 + 2, py + 2), str(x / 2), fill='grey')
                for y in range((y0 // 20 + 1) * 20, y1, 20):
                    draw.line((px, py + y - y0, px + w, py + y - y0), fill=(64, 70, 68))
                    draw.text((px + 2, py + y - y0 + 2), str(y / 2), fill='grey')
        panel.save(out / 'review' / f'attack_{view}_sheet_{label}_landmarks.png')
print('Generated middle and final attack coordinate comparisons.')
