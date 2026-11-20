"""Cut the generated meadow plant sheets out of their magenta backgrounds and build the plants_v4 atlas.

The atlas is 4 x 4 cells of 256 x 192, plants grounded at row 190 like plants_v2. Cells 2-9 are plants_v2's
(mid and dry grass, reeds, tropical low plants, dead tufts); the meadow cells replace and add:
  0, 1   short grass clump cards: one card of a five-card star clump each, rendered from the Poly Haven
         grass_medium_01 model by clump_cards/ (plants_v3 had wide, low grass mats here, still cut from
         art/raw/short_meadow_magenta.png into the review sheet's bottom row for comparison)
  10, 11 purple flower spikes, fern
  12, 13 tall seed-head grass (uncut patches and verges)
  14, 15 yellow buttercups, white daisies and yarrow
Cells 2-15 are identical to plants_v3's.
Usage: python3 level_generation/terrain/meadow/process_art.py [--install]
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CELL = (256, 192)
GROUND = 190
# Sheet: (left cell, right cell).
SHEETS = {'short_meadow': (0, 1), 'purple_fern': (10, 11), 'tall_seed': (12, 13), 'flowers_yw': (14, 15)}
# The generator washes thin blades and seed heads with a faint pink: the grass sheets accept only colours greener
# than magenta (straw and cream included); the flower sheets keep white petals. The short lawn grass also loses the
# warm seed tips the generator paints in, which read as pink specks on the ground.
SOLID_LIMIT = {'short_meadow': -2, 'tall_seed': -2, 'purple_fern': 4, 'flowers_yw': 4}
BACKGROUND = np.array([255, 0, 255], np.float32)
# The short grass mats grow straight out of the ground, so their mean colour under the MM6 grass rule tint
# (0.82, 0.98, 0.78) matches New Sorpigal's grass ground (grass_meadow under its world tint), 8 % brighter.
SHORT_GRASS_MEAN = np.array([0.313, 0.383, 0.218])
# Clump cards (rendered by clump_cards/scripts/render_cards.py). Each card's solid texels are matched to
# SHORT_GRASS_MEAN times its variety factor: cell 0 a little greener, cell 1 a little warmer; the two factors average
# to one, so the pair keeps the short-grass mean the rule tints and the ground matching rely on.
CLUMP_CARDS = HERE / 'clump_cards/renders'
CLUMP_VARIETY = {0: np.array([0.98, 1.025, 1.02]), 1: np.array([1.02, 0.975, 0.98])}
# Blades are one to three texels wide in the cell; filtering leaves their edges and tips below the game's 0.5 alpha
# test, so the cards' coverage is raised to keep thin blades and tips whole.
CLUMP_ALPHA_GAIN = 1.5
CLUMP_BASE_ROWS = 28
CLUMP_BASE_BLEND = 0.6
# The generated seed heads are nearly white in the game's light; uncut grass reads darker and greener.
TALL_GRASS_GAIN = np.array([0.76, 0.84, 0.76])


def extract(path, limit, green=False):
    """RGBA of a magenta-backed sheet: alpha from the distance towards the nearest solid foreground colour. Solid
    texels are those whose min(red, blue) - green is below limit (and, for green, whose green channel leads)."""
    rgb = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
    magenta = np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]
    core = magenta < limit
    if green:
        core &= rgb[..., 1] >= np.maximum(rgb[..., 0], rgb[..., 2])
    nearest = ndimage.distance_transform_edt(~core, return_distances=False, return_indices=True)
    foreground = rgb[nearest[0], nearest[1]]
    direction = foreground - BACKGROUND
    alpha = np.clip(np.sum((rgb - BACKGROUND) * direction, axis=2) /
                    np.maximum(np.sum(direction * direction, axis=2), 1), 0, 1)
    alpha[core] = 1
    alpha[magenta > 170] = 0
    alpha[alpha < 0.04] = 0
    # Every partly covered texel takes the nearest solid colour: unmixing thin blades still leaves a pink cast.
    corrected = np.where(core[..., None], rgb, foreground)
    labels, count = ndimage.label(alpha > 0)
    sizes = np.bincount(labels.ravel())
    small = sizes < 24
    small[0] = False
    alpha[small[labels]] = 0
    rgba = np.dstack((np.rint(corrected), np.rint(alpha * 255))).astype(np.uint8)
    rgba[alpha == 0, :3] = 0
    return Image.fromarray(rgba, 'RGBA')


def split(image):
    """The two plants: crops either side of the widest empty column band in the middle of the sheet."""
    alpha = np.asarray(image.getchannel('A')) > 0
    columns = alpha.sum(axis=0)
    width = image.width
    central = np.arange(int(width * 0.35), int(width * 0.65))
    clear = central[columns[central] == 0]
    assert clear.size > 8, 'no empty gap between the two plants'
    gaps = np.split(clear, np.where(np.diff(clear) > 1)[0] + 1)
    gap = max(gaps, key=len)
    middle = int(gap[len(gap) // 2])
    crops = []
    for left, right in [(0, middle), (middle, width)]:
        part = image.crop((left, 0, right, image.height))
        crops.append(part.crop(part.getchannel('A').getbbox()))
    return crops


def cell_of(crop, scale, alpha_gain=1.0):
    size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    reduced = crop.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
    cell = Image.new('RGBA', CELL)
    cell.paste(reduced, ((CELL[0] - size[0]) // 2, GROUND - size[1]))
    pixels = np.array(cell)
    if alpha_gain != 1.0:
        pixels[..., 3] = np.clip(np.rint(pixels[..., 3] * alpha_gain), 0, 255).astype(np.uint8)
    # Fill the colour of transparent texels from the nearest solid one so mips and filtering do not darken edges.
    solid = pixels[..., 3] >= 128
    nearest = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    pixels[~solid, :3] = pixels[nearest[0][~solid], nearest[1][~solid], :3]
    pixels[pixels[..., 3] == 0, :3] = pixels[nearest[0], nearest[1], :3][pixels[..., 3] == 0]
    return Image.fromarray(pixels, 'RGBA')


def match_mean(cell, target):
    """cell with its solid texels' mean colour scaled to target (0-1 RGB)."""
    pixels = np.asarray(cell).astype(np.float32)
    solid = pixels[..., 3] >= 102
    gain = target * 255 / pixels[solid][:, :3].mean(axis=0)
    pixels[..., :3] = np.clip(pixels[..., :3] * gain, 0, 255)
    return Image.fromarray(np.rint(pixels).astype(np.uint8), 'RGBA')


def clump_card(index):
    """Atlas cell of a rendered clump card: cropped to its plant, scaled to fit the cell (premultiplied filtering),
    grounded at GROUND and colour-matched."""
    render = Image.open(CLUMP_CARDS / f'card{index}.png').convert('RGBA')
    left, top, right, bottom = render.getchannel('A').getbbox()
    # The render's middle column is the tuft's base: crop symmetrically about it so the base lands mid-cell.
    half = max(render.width // 2 - left, right - render.width // 2)
    crop = render.crop((render.width // 2 - half, top, render.width // 2 + half, bottom))
    scale = min((CELL[0] - 4) / crop.width, (GROUND - 2) / crop.height)
    pixels = np.asarray(cell_of(crop, scale, CLUMP_ALPHA_GAIN)).astype(np.float32)
    # The pale leaf sheaths at the base would read as a light knot: blend the lowest rows towards the card's mean
    # colour (up to CLUMP_BASE_BLEND at the ground row), so the tuft grows out of the ground colour.
    solid = pixels[..., 3] >= 102
    mean = pixels[..., :3][solid].mean(axis=0)
    rows = np.arange(CELL[1], dtype=np.float32)[:, None, None]
    blend = CLUMP_BASE_BLEND * np.clip((rows - (GROUND - CLUMP_BASE_ROWS)) / CLUMP_BASE_ROWS, 0, 1)
    pixels[..., :3] = pixels[..., :3] * (1 - blend) + mean * blend
    target = SHORT_GRASS_MEAN * CLUMP_VARIETY[index]
    cell = match_mean(Image.fromarray(np.rint(pixels).astype(np.uint8), 'RGBA'), target)
    # The scan is yellower than the target, so matching lifts blue and turns the few brown dry tips lilac: make
    # those straw again and match once more.
    pixels = np.asarray(cell).astype(np.float32)
    r, g, b = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    lilac = (b > 0.85 * g) & (r > 0.9 * g)
    pixels[lilac, :3] = np.stack((r, np.maximum(g, 1.02 * r), np.minimum(b, 0.7 * g)), axis=-1)[lilac]
    print(f'cell {index}: {int((lilac & (pixels[..., 3] > 0)).sum())} lilac texels made straw')
    return match_mean(Image.fromarray(np.rint(pixels).astype(np.uint8), 'RGBA'), target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true', help='write plants_v4.png into every world')
    args = parser.parse_args()
    previous = Image.open(HERE / 'art/plants_v2.png').convert('RGBA')
    cells = {}
    mats = {}
    for index in range(12):
        x, y = index % 4 * CELL[0], index // 4 * CELL[1]
        cells[index] = previous.crop((x, y, x + CELL[0], y + CELL[1]))
    for sheet, (left, right) in SHEETS.items():
        crops = split(extract(HERE / 'art/raw' / f'{sheet}_magenta.png', SOLID_LIMIT[sheet], sheet == 'short_meadow'))
        scale = min((CELL[0] - 4) / max(c.width for c in crops), (GROUND - 2) / max(c.height for c in crops))
        cells[left], cells[right] = (cell_of(crop, scale) for crop in crops)
        if sheet == 'short_meadow':
            for index in (left, right):
                mats[index] = match_mean(cells[index], SHORT_GRASS_MEAN)
                cells[index] = clump_card(index)
        if sheet == 'tall_seed':
            for index in (left, right):
                pixels = np.asarray(cells[index]).astype(np.float32)
                pixels[..., :3] = np.clip(pixels[..., :3] * TALL_GRASS_GAIN, 0, 255)
                cells[index] = Image.fromarray(np.rint(pixels).astype(np.uint8), 'RGBA')
    atlas = Image.new('RGBA', (CELL[0] * 4, CELL[1] * 4))
    # Review: the atlas on dark and light panels, and below it plants_v3's grass mats for comparison.
    review = Image.new('RGB', (CELL[0] * 8, CELL[1] * 5), '#24242a')
    draw = ImageDraw.Draw(review)
    entries = [(str(index), cell, index % 4 * CELL[0], index // 4 * CELL[1]) for index, cell in cells.items()]
    entries += [(f'v3 {index}', mat, index * CELL[0], CELL[1] * 4) for index, mat in mats.items()]
    for label, cell, x, y in entries:
        if not label.startswith('v3'):
            atlas.paste(cell, (x, y))
        for panel_index, colour in enumerate(['#24242a', '#c9c3b3']):
            panel = Image.new('RGBA', CELL, colour)
            panel.alpha_composite(cell)
            review.paste(panel.convert('RGB'), (panel_index * CELL[0] * 4 + x, y))
            draw.text((panel_index * CELL[0] * 4 + x + 4, y + 4), label, fill='white')
    pixels = np.asarray(atlas).astype(int)
    spill = (pixels[..., 0] > pixels[..., 1] + 30) & (pixels[..., 2] > pixels[..., 1] + 30) & (pixels[..., 3] > 32)
    # Purple flowers are legitimately red and blue; only count spill outside their cell.
    spill[CELL[1] * 2:CELL[1] * 3, CELL[0] * 2:CELL[0] * 3] = False
    print('magenta spill texels outside the purple flowers:', int(spill.sum()))
    for index in (0, 1):
        x, y = index % 4 * CELL[0], index // 4 * CELL[1]
        solid = pixels[y:y + CELL[1], x:x + CELL[0]][pixels[y:y + CELL[1], x:x + CELL[0], 3] >= 102]
        box = cells[index].getchannel('A').getbbox()
        print(f'cell {index}: plant {box[2] - box[0]} x {box[3] - box[1]} (aspect '
              f'{(box[2] - box[0]) / (box[3] - box[1]):.2f}), solid mean {np.round(solid[:, :3].mean(axis=0) / 255, 3)}')
    atlas.save(HERE / 'plants_v4.png')
    review.save(HERE / 'art/review.png')
    if args.install:
        for world in ['mm6', 'mm7', 'mm8']:
            atlas.save(ROOT / 'assets_dev/worlds' / world / 'terrain_decorations/plants_v4.png', optimize=True)
        print('installed plants_v4.png for mm6, mm7 and mm8')


if __name__ == '__main__':
    main()
