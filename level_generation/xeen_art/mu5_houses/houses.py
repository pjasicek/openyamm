#!/usr/bin/env python3
"""MU-5 house kit boards (devdocs/xeen/PRODUCTION.md §4): per town kit, 6-10 house types in front elevation at native
scale, built from the kit's facade pieces (level_generation/xeen_art/kits/<kit>.yml), then one painted pass per kit.

  houses.py blocked [KIT...]        blocked_<kit>.png: the elevations from the textures, 1 texel = 1 unit, drawn at
                                    SCALE pixels per unit, with a 128 x 256 door and a 6-foot (180-unit) figure for scale
  houses.py paint KIT [--note T]    one `codex exec` call: a painted pass over the blocked row (raw/<kit>_vN.png)
  houses.py board [--pick kit=N]    board_mu5.png: per kit the blocked row, the painting and the piece swatches

Facades follow the shipped sets: a storey is a row of 128-wide pieces (left end, wall, wall with window, door, right
end) 256 tall; roofs are drawn as the roof texture over the eaves (ridge along the front) or as a gable (ridge
towards the street). The house types and their pieces per kit are in KITS below; textures are read from the shipped
x4 masters or the kit's finished new textures and reduced to native size.
"""
import argparse
import subprocess
import time
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MASTERS = ROOT / 'level_generation/textures_x4/masters'
NEW = [HERE.parent / 'kit_textures/towns/finished', HERE.parent / 'kit_textures/landmarks/finished',
       ROOT / 'level_generation/textures_xeen/finished']
SCALE = 0.5            # pixels per unit on the board
GROUND = 64            # units of ground under the houses

_cache = {}


def texture(ref):
    """A texture at native size (1 texel = 1 unit): 'world/name' from the shipped masters, or a new Xeen name."""
    if ref in _cache:
        return _cache[ref]
    if '/' in ref:
        path = MASTERS / f'{ref}.png'
    else:
        path = next(folder / f'{ref}.png' for folder in NEW if (folder / f'{ref}.png').exists())
    image = Image.open(path).convert('RGBA')
    image = image.resize((image.width // 4, image.height // 4), Image.LANCZOS)
    _cache[ref] = image
    return image


def tile(canvas, ref, box):
    """Fill box (x0, y0, x1, y1 in units, y down) with the texture repeated from its top-left corner."""
    image = texture(ref)
    x0, y0, x1, y1 = (int(v) for v in box)
    for y in range(y0, y1, image.height):
        for x in range(x0, x1, image.width):
            piece = image.crop((0, 0, min(image.width, x1 - x), min(image.height, y1 - y)))
            canvas.alpha_composite(piece, (x, y))


def roof_eaves(canvas, ref, x0, x1, top, height, overhang=32):
    """A roof seen from the front with its ridge along the facade: a trapezoid of roof texture."""
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    tile(layer, ref, (x0 - overhang, top - height, x1 + overhang, top))
    mask = Image.new('L', canvas.size, 0)
    inset = min(height * 0.9, (x1 - x0) * 0.35)
    ImageDraw.Draw(mask).polygon([(x0 - overhang, top), (x1 + overhang, top), (x1 - inset, top - height),
                                  (x0 + inset, top - height)], fill=255)
    canvas.paste(layer, (0, 0), mask)


def roof_gable(canvas, wall_ref, roof_ref, x0, x1, top, height, overhang=24):
    """A gable end towards the street: the wall texture in a triangle, the roof's edge as a band of roof texture."""
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    tile(layer, wall_ref, (x0, top - height, x1, top))
    mask = Image.new('L', canvas.size, 0)
    mid = (x0 + x1) / 2
    ImageDraw.Draw(mask).polygon([(x0, top), (x1, top), (mid, top - height)], fill=255)
    canvas.paste(layer, (0, 0), mask)
    band = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    tile(band, roof_ref, (x0 - overhang, top - height - 40, x1 + overhang, top + 8))
    edge = Image.new('L', canvas.size, 0)
    d = ImageDraw.Draw(edge)
    d.line([(x0 - overhang, top + 4), (mid, top - height - 20), (x1 + overhang, top + 4)], fill=255, width=36)
    canvas.paste(band, (0, 0), edge)


def house(kit, spec):
    """Render one house type. spec: storeys (list of piece strings, bottom first), roof (eaves|gable|cone|flat),
    roof_height, extras (sign, chimney)."""
    pieces = {**kit.get('pieces', {}), **spec.get('pieces', {})}
    storeys = spec['storeys']
    width = max(len(row.split()) for row in storeys) * 128
    wall_h = 256 * len(storeys)
    roof_h = spec.get('roof_height', 256)
    margin = 96
    height = wall_h + roof_h + GROUND + 160
    canvas = Image.new('RGBA', (width + 2 * margin, height), (0, 0, 0, 0))
    base = height - GROUND
    if 'plinth' in pieces:
        tile(canvas, pieces['plinth'], (margin - 8, base - 32, margin + width + 8, base))
    for level, row in enumerate(storeys):
        codes = row.split()
        row_w = len(codes) * 128
        x = margin + (width - row_w) // 2
        y = base - 256 * (level + 1)
        for code in codes:
            ref = pieces[code]
            tile(canvas, ref, (x, y, x + 128, y + 256))
            x += 128
    top = base - wall_h
    roof = spec.get('roof', 'eaves')
    if roof == 'eaves':
        roof_eaves(canvas, pieces['roof'], margin, margin + width, top, roof_h)
    elif roof == 'gable':
        roof_gable(canvas, pieces.get('gable', pieces['W']), pieces['roof'], margin, margin + width, top, roof_h)
    elif roof == 'cone':
        layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        tile(layer, pieces['roof'], (margin - 32, top - roof_h, margin + width + 32, top))
        mask = Image.new('L', canvas.size, 0)
        ImageDraw.Draw(mask).polygon([(margin - 32, top), (margin + width + 32, top),
                                      (margin + width / 2, top - roof_h)], fill=255)
        canvas.paste(layer, (0, 0), mask)
    elif roof == 'flat' and 'parapet' in pieces:
        tile(canvas, pieces['parapet'], (margin - 8, top - 64, margin + width + 8, top))
    if 'chimney' in spec.get('extras', []) and 'chimney' in pieces:
        cx = margin + width - 160
        tile(canvas, pieces['chimney'], (cx, top - roof_h - 64, cx + 64, top - roof_h * 0.3))
    if 'sign' in spec.get('extras', []) and 'sign' in pieces:
        sign = texture(pieces['sign'])
        door_x = margin + (storeys[0].split().index('D') * 128 if 'D' in storeys[0].split() else width // 2)
        canvas.alpha_composite(sign, (int(door_x + 64 - sign.width / 2), int(base - 256 - sign.height - 8)))
    return canvas


def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def paint_reference(kit_name):
    """The blocked houses in two rows on a 3:2 canvas (the painted pass's output shape), so the model does not have to
    squeeze a 7:1 row into 1536 x 1024: paintref_<kit>.png."""
    kit = KITS[kit_name]
    renders = [house(kit, spec) for spec in kit['houses']]
    gap = 32
    total = sum(r.width + gap for r in renders)
    split, run = len(renders), 0
    for index, render in enumerate(renders):
        run += render.width + gap
        if run >= total / 2:
            split = index + 1 if run - total / 2 < (render.width + gap) / 2 else index
            break
    rows = [renders[:split], renders[split:]]
    row_w = max(sum(r.width + gap for r in row) + gap for row in rows)
    row_h = max(r.height for r in renders) + 40
    width = max(row_w, int(2 * row_h * 1.5))
    height = int(width / 1.5)
    board = Image.new('RGBA', (width, height), (180, 196, 214, 255))
    draw = ImageDraw.Draw(board)
    top = (height - 2 * row_h) // 2
    for number, row in enumerate(rows):
        base = top + (number + 1) * row_h
        draw.rectangle((0, base - GROUND - 40, width, base), fill=(92, 112, 64, 255))
        x = (width - sum(r.width + gap for r in row) + gap) // 2
        for render in row:
            board.alpha_composite(render, (x, base - render.height - 40 + GROUND - GROUND))
            x += render.width + gap
    out = board.resize((1536, 1024), Image.LANCZOS).convert('RGB')
    out.save(HERE / f'paintref_{kit_name}.png')
    return out


def blocked(kit_name):
    kit = KITS[kit_name]
    renders = [(spec['name'], house(kit, spec)) for spec in kit['houses']]
    gap = 32
    width = sum(r.width for _, r in renders) + gap * (len(renders) + 1)
    height = max(r.height for _, r in renders) + 140
    board = Image.new('RGBA', (width, height), (180, 196, 214, 255))
    draw = ImageDraw.Draw(board)
    draw.rectangle((0, height - GROUND - 40, width, height), fill=(92, 112, 64, 255))
    x = gap
    for name, render in renders:
        board.alpha_composite(render, (x, height - render.height - 40))
        draw.text((x + 8, height - 34), name, font=font(22), fill='white')
        x += render.width + gap
    # A 180-unit figure and a 128 x 256 door outline for scale.
    fx = width - 80
    draw.rectangle((fx, height - GROUND - 40 - 180, fx + 40, height - GROUND - 40), outline='black', width=3)
    out = board.resize((int(width * SCALE), int(height * SCALE)), Image.LANCZOS).convert('RGB')
    out.save(HERE / f'blocked_{kit_name}.png')
    return out


# Read from kits_mu5.yml: per kit `title`, `look` (words for the painted pass), `pieces` (code -> texture: `L`, `R`
# ends, `W` wall, `w` wall with window, `D` door, any other one-letter codes, and the named `roof`, `gable`, `plinth`,
# `chimney`, `sign`, `parapet`), and `houses`: a list of {name, storeys: ["L w D R", ...] bottom first,
# roof: eaves|gable|cone|flat, roof_height, extras: [sign, chimney], pieces: per-house overrides}.
KITS = {}


def load_kits():
    path = HERE / 'kits_mu5.yml'
    if path.exists():
        KITS.update(yaml.safe_load(path.read_text()))


PAINT_PROMPT = """Asset: a concept painting for the house kit of a Might and Magic VI-VIII style town (a 1990s first-person fantasy RPG,
in the remaster's high-resolution art): {title}.
Reference 1 is a blocked elevation: {count} house types in two rows, in exact front view, built from the game's own wall,
door, window and roof textures at true scale (a door is 128 wide and 256 tall, about two metres). Repaint it as one
finished painting of the same two rows on the same canvas: keep every house at the same position, width, height, storey count, roof shape and
door and window placement, and keep the materials and colours of the textures; add the depth, eaves, beams, sills,
weathering, small props (barrels, planters, lanterns, a cart) and soft daylight shading of a painted concept sheet.
Flat front view, no perspective, plain light sky and a strip of ground behind and below. No text, no labels.
{look}"""

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image(s) as reference images and the IMAGE PROMPT below.
   Output size: 1536x1024 (landscape).
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""


def cmd_paint(args):
    kit = KITS[args.kit]
    raw = HERE / 'raw'
    raw.mkdir(exist_ok=True)
    version = 1 + len(list(raw.glob(f'{args.kit}_v*.png')))
    target = raw / f'{args.kit}_v{version}.png'
    prompt = PAINT_PROMPT.format(title=kit['title'], count=len(kit['houses']), look=kit['look'])
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    (raw / f'{args.kit}_v{version}.txt').write_text(prompt + '\n')
    paint_reference(args.kit)
    ref = HERE / f'paintref_{args.kit}.png'
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check',
               '-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    print(args.kit, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


def swatches(kit_name, width):
    kit = KITS[kit_name]
    refs = list(dict.fromkeys([*kit.get('pieces', {}).values(),
                               *(ref for spec in kit['houses'] for ref in spec.get('pieces', {}).values())]))
    size = 96
    per_row = max(1, width // (size + 140))
    rows = (len(refs) + per_row - 1) // per_row
    sheet = Image.new('RGB', (width, rows * (size + 30) + 10), (24, 24, 30))
    draw = ImageDraw.Draw(sheet)
    for i, ref in enumerate(refs):
        image = texture(ref).convert('RGB')
        scale = size / max(image.size)
        thumb = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.NEAREST)
        x, y = 10 + (i % per_row) * (size + 140), 10 + (i // per_row) * (size + 30)
        sheet.paste(thumb, (x, y))
        label = ref.split('/')[-1] + ('' if '/' in ref else ' NEW')
        draw.text((x + thumb.width + 6, y + 4), label, font=font(15), fill=(230, 230, 230))
    return sheet


def cmd_board(args):
    picks = dict(p.split('=') for p in args.pick)
    panels = []
    for kit_name in KITS:
        row = Image.open(HERE / f'blocked_{kit_name}.png').convert('RGB')
        width = 2000
        row = row.resize((width, int(row.height * width / row.width)), Image.LANCZOS)
        paint_path = HERE / 'raw' / f'{kit_name}_v{picks.get(kit_name, 1)}.png'
        painting = None
        if paint_path.exists():
            painting = Image.open(paint_path).convert('RGB')
            painting = painting.resize((width, int(painting.height * width / painting.width)), Image.LANCZOS)
        sw = swatches(kit_name, width)
        height = 60 + row.height + 20 + (painting.height + 20 if painting else 0) + sw.height
        panel = Image.new('RGB', (width, height), (16, 16, 22))
        d = ImageDraw.Draw(panel)
        d.text((10, 12), f'{KITS[kit_name]["title"]}: {len(KITS[kit_name]["houses"])} house types (blocked at native '
                         f'scale, then painted)', font=font(24), fill='white')
        y = 60
        panel.paste(row, (0, y))
        y += row.height + 20
        if painting:
            panel.paste(painting, (0, y))
            y += painting.height + 20
        panel.paste(sw, (0, y))
        panels.append(panel)
    for kit_name, panel in zip(KITS, panels):
        panel.save(HERE / f'board_mu5_{kit_name}.png')
    print('boards', [f'board_mu5_{k}.png' for k in KITS])


def main():
    load_kits()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('blocked')
    b.add_argument('kits', nargs='*')
    p = sub.add_parser('paint')
    p.add_argument('kit')
    p.add_argument('--note', default='')
    board = sub.add_parser('board')
    board.add_argument('--pick', nargs='*', default=[])
    args = parser.parse_args()
    if args.command == 'blocked':
        for name in args.kits or list(KITS):
            print(name, blocked(name).size)
    elif args.command == 'paint':
        cmd_paint(args)
    else:
        cmd_board(args)


if __name__ == '__main__':
    main()
