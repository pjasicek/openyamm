#!/usr/bin/env python3
"""Exports runtime_x2/talent_<id>.png (128 x 128 RGBA) from masters/<id>.png, builds the previews/ contact sheets at
40 and 128 px on the Talents page colours, and writes the self-contained viewer.html.

The engine draws an icon_item fitted into its box on IconBack (#151b1c, GameplaySoloTalentsPage.cpp) and loads it
with the item-icon decode, which keys out near-magenta and near-cyan texels; the export nudges any such texel.
"""

import base64
import html
import io
import json
import os

from PIL import Image, ImageDraw, ImageFont

STUDY = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
REPO = os.path.normpath(os.path.join(STUDY, '../../..'))
FONT = os.path.join(REPO, 'assets_dev/engine/fonts/truetype/fondamento_regular.ttf')
PAGE = (12, 15, 16, 255)
ICON_BACK = (0x15, 0x1b, 0x1c, 255)
INK = (0xe8, 0xd1, 0xa4, 255)
TREES = [('arms', 'Arms'), ('archery', 'Archery'), ('arcana', 'Arcana'), ('any', 'Any tree'),
         ('keystone', 'Keystones')]
FIT = 124


def load_icons():
    with open(os.path.join(STUDY, 'icons.json')) as f:
        return json.load(f)


def runtime_path(entry):
    return os.path.join(STUDY, 'runtime_x2', 'talent_' + entry['id'] + '.png')


def export_runtime(icons):
    for entry in icons:
        master = os.path.join(STUDY, 'masters', entry['id'] + '.png')
        if not os.path.exists(master):
            continue
        try:
            image = Image.open(master).convert('RGBA')
        except OSError:
            print('skipped (unreadable, still being written?):', master)
            continue
        image = image.crop(image.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox())
        fit = FIT / max(image.size)
        image = image.resize((max(1, round(image.width * fit)), max(1, round(image.height * fit))), Image.LANCZOS)
        runtime = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        runtime.alpha_composite(image, ((128 - image.width) // 2, (128 - image.height) // 2))
        pixels = runtime.load()
        for y in range(128):
            for x in range(128):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    pixels[x, y] = (0, 0, 0, 0)
                elif r >= 248 and g <= 8 and b >= 248:
                    pixels[x, y] = (r, 12, b, a)
                elif r <= 8 and g >= 248 and b >= 248:
                    pixels[x, y] = (12, g, b, a)
        path = runtime_path(entry)
        runtime.save(path)
        os.chmod(path, 0o644)


def contact_sheet(icons, size, name):
    """One row per tree: each icon on an IconBack tile, as the Talents page draws it, with its name below."""
    font = ImageFont.truetype(FONT, 15 if size < 64 else 20)
    label_w = 110
    cell_w = max(size + 16, 132 if size < 64 else size + 24)
    rows = [[e for e in icons if e['tree'] == tree and os.path.exists(runtime_path(e))] for tree, _ in TREES]
    columns = max(len(r) for r in rows)
    row_h = size + 16 + 26
    sheet = Image.new('RGBA', (label_w + columns * cell_w + 12, len(rows) * row_h + 16), PAGE)
    draw = ImageDraw.Draw(sheet)
    for r, ((tree, title), row) in enumerate(zip(TREES, rows)):
        y = 12 + r * row_h
        draw.text((12, y + size // 2 + 4), title, font=font, fill=INK, anchor='lm')
        for c, entry in enumerate(row):
            x = label_w + c * cell_w + (cell_w - size - 8) // 2
            draw.rectangle([x, y, x + size + 7, y + size + 7], fill=ICON_BACK, outline=(0x5a, 0x4a, 0x2c, 255))
            icon = Image.open(runtime_path(entry)).convert('RGBA').resize((size, size), Image.LANCZOS)
            sheet.alpha_composite(icon, (x + 4, y + 4))
            draw.text((label_w + c * cell_w + cell_w // 2, y + size + 20), entry['name'], font=font, fill=INK,
                      anchor='mm')
    sheet.save(os.path.join(STUDY, 'previews', name))


def beside_spells(icons):
    """Twelve spell icons (the reference set) then every talent icon, at 40 px, magnified 2x (box filter at an integer scale, the same as nearest; this PIL build's NEAREST resize fails)
    sampling so the 40 px reading can be judged."""
    spells = ['sbf06a', 'sba05a', 'sba10a', 'sbe01a', 'sbe06a', 'sbb10a', 'sbm05a', 'sbw10a', 'sbd01a', 'sbf09a',
              'sbs07a', 'sbe02a']
    paths = [os.path.join(REPO, 'assets_dev/engine/icons_x2', n + '.png') for n in spells]
    paths += [runtime_path(e) for e in icons if os.path.exists(runtime_path(e))]
    cell = 48
    columns = 12
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new('RGBA', (columns * cell + 8, rows * cell + 8), PAGE)
    for i, path in enumerate(paths):
        icon = Image.open(path).convert('RGBA')
        icon.thumbnail((40, 40), Image.LANCZOS)
        x = 8 + (i % columns) * cell
        y = 8 + (i // columns) * cell
        tile = Image.new('RGBA', (40, 40), ICON_BACK)
        tile.alpha_composite(icon, ((40 - icon.width) // 2, (40 - icon.height) // 2))
        sheet.paste(tile, (x, y))
    sheet = sheet.convert('RGB').resize((sheet.width * 2, sheet.height * 2), Image.BOX)
    sheet.save(os.path.join(STUDY, 'previews', 'beside_spells_40px_x2.png'))


def data_uri(path):
    with open(path, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()


def viewer(icons):
    sections = []
    for tree, title in TREES:
        cards = []
        for entry in icons:
            if entry['tree'] != tree or not os.path.exists(runtime_path(entry)):
                continue
            uri = data_uri(runtime_path(entry))
            kind = entry['kind']
            cards.append(f'''<article class="card">
  <div class="icons"><span class="slot s40"><img src="{uri}" width="40" height="40" alt=""></span>
  <span class="slot s128"><img src="{uri}" width="128" height="128" alt=""></span></div>
  <h3>{html.escape(entry['name'])} <small>{html.escape(kind)}</small></h3>
  <p>{html.escape(entry['effect'])}</p>
  <p class="subject">{html.escape(entry['subject'])}</p>
</article>''')
        strip = ''.join(f'<span class="slot s40" title="{html.escape(e["name"])}"><img src="{data_uri(runtime_path(e))}"'
                        f' width="40" height="40" alt="{html.escape(e["name"])}"></span>'
                        for e in icons if e['tree'] == tree and os.path.exists(runtime_path(e)))
        sections.append(f'<section><h2>{title}</h2><div class="strip">{strip}</div>'
                        f'<div class="cards">{"".join(cards)}</div></section>')
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Solo Talent Icons</title>
<style>
:root {{ --page:#0c0f10; --back:#151b1c; --ink:#e8d1a4; --muted:#9a8f7a; --brass:#5a4a2c; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; padding:24px 16px; background:var(--page); color:var(--ink);
  font:15px/1.45 Georgia, "Times New Roman", serif; }}
main {{ max-width:1180px; margin:0 auto; }}
h1 {{ font-weight:normal; margin:0 0 4px; }} h2 {{ font-weight:normal; border-bottom:1px solid var(--brass);
  padding-bottom:4px; margin:32px 0 12px; }}
.lede {{ color:var(--muted); margin:0; }}
.strip {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; }}
.slot {{ display:inline-flex; align-items:center; justify-content:center; background:var(--back);
  border:1px solid var(--brass); }}
.s40 {{ width:48px; height:48px; }} .s128 {{ width:140px; height:140px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); gap:12px; }}
.card {{ background:#111617; border:1px solid #232b2c; padding:12px; }}
.icons {{ display:flex; align-items:center; gap:12px; }}
h3 {{ margin:10px 0 4px; font-weight:normal; font-size:18px; }} h3 small {{ color:var(--muted); font-size:13px; }}
p {{ margin:0 0 6px; }} .subject {{ color:var(--muted); font-size:13px; }}
img {{ display:block; }}
</style></head><body><main>
<h1>Solo talent icons</h1>
<p class="lede">MAW solo run, talent tree v2: 19 talents and 2 keystones, at 40 px (the action bar and Talents page)
and 128 px (the x2 file), on the Talents page's icon colour.</p>
{''.join(sections)}
</main></body></html>
'''
    with open(os.path.join(STUDY, 'viewer.html'), 'w') as f:
        f.write(page)


def main():
    icons = load_icons()
    os.makedirs(os.path.join(STUDY, 'previews'), exist_ok=True)
    export_runtime(icons)
    contact_sheet(icons, 40, 'contact_40px.png')
    contact_sheet(icons, 128, 'contact_128px.png')
    beside_spells(icons)
    viewer(icons)


if __name__ == '__main__':
    main()
