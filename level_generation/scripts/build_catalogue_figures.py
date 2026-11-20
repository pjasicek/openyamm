"""Compose reference contact sheets, a native texture palette and a measured door-scale figure.

Uses existing source bitmaps and Blender renders; does not alter source screenshots or game assets.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'level_generation/catalogues/mm8_ravenshore'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(size):
    return ImageFont.truetype(FONT, size)


def build():
    data = json.loads((OUT / 'catalogue.json').read_text())
    textures = json.loads((OUT / 'textures.json').read_text())
    models = [m for m in data['models'] if m['catalogue_building']]
    for start in range(0, len(models), 24):
        batch = models[start:start + 24]
        sheet = Image.new('RGB', (1200, ((len(batch) + 3) // 4) * 288), '#202329')
        draw = ImageDraw.Draw(sheet)
        for j, model in enumerate(batch):
            im = Image.open(OUT / 'images' / f'{model["index"]:03d}.png').convert('RGB')
            im.thumbnail((300, 244))
            x, y = j % 4 * 300, j // 4 * 288
            sheet.paste(im, (x, y))
            title = f'{model["index"]:03d} ' + '; '.join(s['title'] for s in model['services'])
            draw.text((x + 4, y + 244), title[:31], font=font(16), fill='white')
            draw.text((x + 4, y + 264), model['family'], font=font(16), fill='#c9d5e0')
        sheet.save(OUT / 'images' / f'contact_{start // 24 + 1}.jpg', quality=92)

    palette = [
        ('t14a03', 'Luodrin door'), ('t14a04c', 'Luodrin window panel'),
        ('t14a01', 'Matched blank wall'), ('t14a06', 'Corner / post panel'),
        ('t14a07', 'Corner / post variant'), ('t14d01', 'Cornice / wall panel'),
        ('t14a05b', 'Flat roof / turret cap'), ('t14c01b', 'Turret stone'),
        ('t14c03', 'Stone-family door'), ('t14d03', 'Shop door panel'),
        ('sgarm', 'Armor sign'), ('sgbank', 'Bank sign'),
        ('sgweap', 'Weapon sign'), ('sgtvrn', 'Tavern sign'),
        ('bdoorb', 'Boat door: reject for houses'), ('cr_w128b', 'Crate: reject as window'),
    ]
    atlas = Image.new('RGB', (1120, 4 * 354 + 64), '#202329')
    draw = ImageDraw.Draw(atlas)
    draw.text((16, 12), 'Native art: role and bitmap size (panels enlarged with nearest sampling)', font=font(21), fill='white')
    for j, (key, role) in enumerate(palette):
        entry = textures.get(key)
        path = ROOT / entry['path'] if entry else next(p for p in
            (ROOT / 'assets_dev/worlds/mm8/textures').glob('*.bmp') if p.stem.lower() == key)
        im = Image.open(path).convert('RGB'); size = im.size
        factor = min(256 / im.width, 256 / im.height)
        im = im.resize((round(im.width * factor), round(im.height * factor)), Image.Resampling.NEAREST)
        x, y = j % 4 * 280, 64 + j // 4 * 354
        atlas.paste(im, (x + (280 - im.width) // 2, y))
        draw.text((x + 8, y + 266), f'{key}  {size[0]} × {size[1]}', font=font(17), fill='#e5cc96')
        draw.text((x + 8, y + 294), role, font=font(15), fill='white')
    atlas.save(OUT / 'images/texture_roles.png')

    # Exact game-unit axes: one pixel per game unit in the door rectangles.
    diagram = Image.new('RGB', (1100, 760), '#202329'); draw = ImageDraw.Draw(diagram)
    draw.text((28, 20), 'Door calibration — equal physical scale', font=font(30), fill='white')
    draw.text((28, 65), 'One image pixel = one game unit on the door rectangles. Ground aligned.', font=font(20), fill='#c9d5e0')
    floor = 640
    for x, key, width, height, title in [(170, 't14a03', 128, 256, 'Ravenshore'), (590, 'bdoorb', 256, 512, 'Generated town')]:
        im = Image.open(ROOT / textures[key]['path']).convert('RGB')
        diagram.paste(im.resize((width, height), Image.Resampling.NEAREST), (x, floor - height))
        draw.rectangle((x, floor - height, x + width, floor), outline='#e5cc96', width=2)
        draw.text((x - 16, floor + 18), title, font=font(22), fill='white')
        draw.text((x - 16, floor + 49), f'{width} × {height} units', font=font(19), fill='#e5cc96')
    for x in range(50, 1020, 16):
        draw.line((x, floor - 176, x + 8, floor - 176), fill='#70dfdf', width=2)
    draw.text((870, floor - 211), 'Eye: 176', font=font(20), fill='#70dfdf')
    draw.line((50, floor, 1020, floor), fill='#b9c2cb', width=2)
    draw.text((28, 722), 'MM6 New Sorpigal / MM7 Harmondale sampled medians also 128 × 256; not a universal door rule.', font=font(17), fill='#c9d5e0')
    diagram.save(OUT / 'images/door_scale.png')
    print(f'Wrote four contact sheets, texture roles and door scale from {len(models)} catalogue parts.')


if __name__ == '__main__':
    build()
