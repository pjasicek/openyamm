#!/usr/bin/env python3
"""Contact sheet of a Xeen town kit: every shipped and new texture of kits/<kit>.yml as a labelled swatch, by role.

  kit_sheet.py cloudside_town [darkside_town sandcaster]   -> kits/<kit>_sheet.png (about 2000 px wide)

Shipped textures are read from the accepted x4 masters (level_generation/textures_x4/masters/<world>/<name>.png),
new ones from level_generation/xeen_art/kit_textures/towns/finished/<name>.png; both are downsampled in memory.
"""
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MASTERS = ROOT / 'level_generation/textures_x4/masters'
NEW = HERE.parent / 'kit_textures/towns/finished'
WIDTH = 2000
SCALE = 0.75          # logical texels -> sheet pixels for shipped swatches
NEW_SIGN_SCALE = 1.5  # new signs larger, so their lettering can be read
MIN_SIDE = 40
BG = (34, 34, 36)


def font(size):
    for name in ('DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def swatch(image, size, scale):
    w, h = size
    sw, sh = w * scale, h * scale
    grow = max(1.0, MIN_SIDE / min(sw, sh))
    return image.convert('RGB').resize((round(sw * grow), round(sh * grow)), Image.LANCZOS)


def entries(kit):
    for role, items in kit['shipped'].items():
        cells = []
        for item in items:
            world, name = item['tex'].split('/')
            path = MASTERS / world / f'{name}.png'
            if not path.exists():
                continue
            cells.append((swatch(Image.open(path), item['size'], SCALE), f'{name} {world}',
                          f'{item["size"][0]}x{item["size"][1]}', False))
        yield role, cells
    new = []
    for item in kit.get('new', []):
        path = NEW / f'{item["name"]}.png'
        if not path.exists():
            continue
        scale = NEW_SIGN_SCALE if item['kind'] == 'sign' else SCALE * 1.5
        new.append((swatch(Image.open(path), item['size'], scale), item['name'],
                    f'{item["size"][0]}x{item["size"][1]} NEW', True))
    if new:
        yield 'NEW (generated for this kit)', new


def layout(kit):
    label, small, head = font(13), font(11), font(20)
    pad, gap = 16, 10
    blocks = []
    y = 70
    for role, cells in entries(kit):
        if not cells:
            continue
        blocks.append(('head', role, (pad, y)))
        y += 30
        x, row_h = pad, 0
        for image, name, size, is_new in cells:
            cell_w = max(image.width, int(label.getlength(name)) + 2, int(small.getlength(size)) + 2)
            if x + cell_w > WIDTH - pad:
                x, y = pad, y + row_h + gap
                row_h = 0
            blocks.append(('cell', (image, name, size, is_new), (x, y)))
            x += cell_w + gap
            row_h = max(row_h, image.height + 32)
        y += row_h + gap + 8
    sheet = Image.new('RGB', (WIDTH, y + pad), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 14), f'{kit["kit"]}: {kit["title"]}', fill=(255, 230, 120), font=head)
    draw.text((pad, 42), '  '.join(kit['look']), fill=(200, 200, 200), font=label)
    for kind, payload, (x, y) in blocks:
        if kind == 'head':
            draw.text((x, y), payload, fill=(140, 200, 255), font=head)
            draw.line((x, y + 26, WIDTH - pad, y + 26), fill=(70, 70, 80))
            continue
        image, name, size, is_new = payload
        sheet.paste(image, (x, y))
        if is_new:
            draw.rectangle((x - 2, y - 2, x + image.width + 1, y + image.height + 1), outline=(255, 80, 60), width=2)
        draw.text((x, y + image.height + 3), name, fill=(255, 255, 255) if not is_new else (255, 120, 100), font=label)
        draw.text((x, y + image.height + 18), size, fill=(170, 170, 170) if not is_new else (255, 120, 100),
                  font=small)
    return sheet


def main():
    for name in sys.argv[1:] or ['cloudside_town', 'darkside_town', 'sandcaster']:
        kit = yaml.safe_load((HERE / f'{name}.yml').read_text())
        sheet = layout(kit)
        out = HERE / f'{name}_sheet.png'
        sheet.save(out, optimize=True)
        print(out, sheet.size)


if __name__ == '__main__':
    main()
