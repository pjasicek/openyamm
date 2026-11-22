#!/usr/bin/env python3
"""Contact sheets of the Xeen landmark kits and the dungeon families (about 2000 px wide, labelled swatches by role).

  landmark_sheet.py [royal_castle towers ancient dungeon_families]   -> kits/<name>_sheet.png

Shipped textures are read from the accepted x4 masters (level_generation/textures_x4/masters/<world>/<name>.png; a name
without its own master uses its inventory `canonical`, the identical texture), new ones from
level_generation/xeen_art/kit_textures/landmarks/finished/<name>.png (or the town kits' finished/ for a shared one);
everything is downsampled in memory. New textures are framed red and marked NEW.
"""
import json
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MASTERS = ROOT / 'level_generation/textures_x4/masters'
NEW = [HERE.parent / 'kit_textures/landmarks/finished', HERE.parent / 'kit_textures/towns/finished']
WIDTH = 2000
SCALE = 0.5            # logical texels -> sheet pixels
FAMILY_SCALE = 0.3     # dungeon families: smaller swatches
MIN_SIDE = 40
BG = (34, 34, 36)
INVENTORY = {}
for entry in json.loads((ROOT / 'level_generation/textures_x4/inventory.json').read_text())['textures']:
    INVENTORY[(entry['world'], entry['name'].lower())] = entry


def font(size):
    for name in ('DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def master_path(tex):
    world, name = tex.split('/')
    path = MASTERS / world / f'{name.lower()}.png'
    if path.exists():
        return path
    canonical = (INVENTORY.get((world, name.lower())) or {}).get('canonical')
    if canonical:
        w, n = canonical.split('/')
        path = MASTERS / w / f'{n.lower()}.png'
        if path.exists():
            return path
    return None


def size_of(tex):
    entry = INVENTORY.get(tuple(p.lower() if i else p for i, p in enumerate(tex.split('/'))))
    return entry.get('size') if entry and entry.get('size') else None


def swatch(path, size, scale):
    image = Image.open(path)
    if image.mode == 'RGBA':
        backdrop = Image.new('RGBA', image.size, (70, 70, 74, 255))
        backdrop.alpha_composite(image)
        image = backdrop
    w, h = size if size else (image.width // 4, image.height // 4)
    sw, sh = w * scale, h * scale
    grow = max(1.0, MIN_SIDE / min(sw, sh))
    grow = min(grow, max(1.0, 3 * MIN_SIDE / max(sw, sh)))  # thin trims: grow the thin side, but not into a huge bar
    return image.convert('RGB').resize((max(1, round(sw * grow)), max(1, round(sh * grow))), Image.LANCZOS)


def missing(size, scale, label):
    w, h = size or (128, 128)
    image = Image.new('RGB', (max(MIN_SIDE, round(w * scale)), max(MIN_SIDE, round(h * scale))), (90, 40, 40))
    ImageDraw.Draw(image).text((3, 3), 'no x4\nmaster', fill=(255, 200, 200), font=font(10))
    return image


def shipped_cell(tex, scale, size=None):
    size = size or size_of(tex)
    path = master_path(tex)
    world, name = tex.split('/')
    image = swatch(path, size, scale) if path else missing(size, scale, tex)
    return image, f'{name} {world}', f'{size[0]}x{size[1]}' if size else '', False


def new_cell(item, scale):
    path = next((folder / f'{item["name"]}.png' for folder in NEW if (folder / f'{item["name"]}.png').exists()), None)
    image = swatch(path, item['size'], scale) if path else missing(item['size'], scale, item['name'])
    return image, item['name'], f'{item["size"][0]}x{item["size"][1]} {item["kind"]} NEW', True


def kit_blocks(kit):
    for role, items in kit['shipped'].items():
        yield role, [shipped_cell(item['tex'], SCALE, item['size']) for item in items]
    hesper = [h for h in kit.get('hesper_reuse', []) if 'tex' in h]
    if hesper:
        cells = []
        for h in hesper:
            image = swatch(ROOT / h['tex'], h['size'], SCALE)
            cells.append((image, Path(h['tex']).stem, f'{h["size"][0]}x{h["size"][1]} Hesper', False))
        yield 'Hesper candidates (not shipped; reuse counts as new)', cells
    new = [new_cell(item, SCALE * 1.5) for item in kit.get('new', [])]
    if new:
        yield 'NEW (generated for the landmark kits)', new


def family_blocks(data):
    for style, block in data['styles'].items():
        for family in block['families']:
            cells = []
            for role, texs in family['textures'].items():
                for tex in texs:
                    image, name, size, _ = shipped_cell(tex, FAMILY_SCALE)
                    cells.append((image, name, f'{role} {size}', False))
            title = f'{style}: {family["map"]} {family["name"]}'
            uses = [k for k, v in block['assign'].items() if family['map'] in v]
            if uses:
                title += '  ->  ' + ', '.join(u.split(' (')[0] for u in uses)
            yield title, cells


def layout(title, subtitle, blocks, width=WIDTH, top=70):
    label, small, head = font(13), font(11), font(19 if width == WIDTH else 15)
    pad, gap = 16, 10
    placed = []
    y = top
    for heading, cells in blocks:
        if not cells:
            continue
        placed.append(('head', heading, (pad, y)))
        y += 30
        x, row_h = pad, 0
        for image, name, size, is_new in cells:
            cell_w = max(image.width, int(label.getlength(name)) + 2, int(small.getlength(size)) + 2)
            if x + cell_w > width - pad:
                x, y = pad, y + row_h + gap
                row_h = 0
            placed.append(('cell', (image, name, size, is_new), (x, y)))
            x += cell_w + gap
            row_h = max(row_h, image.height + 32)
        y += row_h + gap + 6
    sheet = Image.new('RGB', (width, y + pad), BG)
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((pad, 12), title, fill=(255, 230, 120), font=font(22))
        draw.text((pad, 42), subtitle, fill=(200, 200, 200), font=label)
    for kind, payload, (x, y) in placed:
        if kind == 'head':
            draw.text((x, y), payload, fill=(140, 200, 255), font=head)
            draw.line((x, y + 22, width - pad, y + 22), fill=(70, 70, 80))
            continue
        image, name, size, is_new = payload
        sheet.paste(image, (x, y))
        colour = (255, 120, 100) if is_new else (255, 255, 255)
        if is_new:
            draw.rectangle((x - 2, y - 2, x + image.width + 1, y + image.height + 1), outline=(255, 80, 60), width=2)
        draw.text((x, y + image.height + 3), name, fill=colour, font=label)
        draw.text((x, y + image.height + 18), size, fill=(255, 120, 100) if is_new else (170, 170, 170), font=small)
    return sheet


def two_columns(title, subtitle, blocks):
    """Each family as its own block, packed into two columns (the shorter column takes the next block)."""
    half = WIDTH // 2
    parts = [layout(None, None, [block], width=half, top=8) for block in blocks]
    heights = [70, 70]
    spots = []
    for part in parts:
        column = 0 if heights[0] <= heights[1] else 1
        spots.append((part, column * half, heights[column]))
        heights[column] += part.height
    sheet = Image.new('RGB', (WIDTH, max(heights) + 8), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), title, fill=(255, 230, 120), font=font(22))
    draw.text((16, 42), subtitle, fill=(200, 200, 200), font=font(13))
    for part, x, y in spots:
        sheet.paste(part, (x, y))
    draw.line((half, 64, half, sheet.height), fill=(70, 70, 80))
    return sheet


def main():
    for name in sys.argv[1:] or ['royal_castle', 'towers', 'ancient', 'dungeon_families']:
        data = yaml.safe_load((HERE / f'{name}.yml').read_text())
        if name == 'dungeon_families':
            sheet = two_columns('Xeen dungeon families (shipped only)', data['title'], family_blocks(data))
        else:
            sheet = layout(f'{data["kit"]}: {data["title"]}', '  '.join(data['look']), kit_blocks(data))
        out = HERE / f'{name}_sheet.png'
        sheet.save(out, optimize=True)
        print(out, sheet.size)


if __name__ == '__main__':
    main()
