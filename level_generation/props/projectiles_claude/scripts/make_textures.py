"""Projectile textures from the restored side-view sprites -> textures/<name>_basecolor.png.

Body textures: the side view (frame 2, 400 x 120 at x2) is copied unscaled into the top left of a 512 x 128 canvas,
and its colours are pushed outward into the transparent pixels (nearest opaque colour), so geometry traced slightly
outside the painted silhouette, and mip levels, never sample the background. The builders map their UVs straight onto
sprite pixels. A shaft strip (rows STRIP_ROWS, below the sprite) holds per column the mean of the painted shaft rows
times a gain: the painting is mostly its shadow side and a yellow highlight line, too dark (and the line too pale) as
a base colour under the game's own lighting, while the mean keeps the detail along the shaft.
The fire arrow's body is the arrow's with the fire arrow's own fletching (its shaft and head lie under the painted
flames). Its flame flipbook (fire_arrow_flame) holds the six painted side frames' front halves, 2 x 4 cells of
256 x 128 (a b c d e f e d, so the loop runs back and forth), keyed to the flames only (flame_key) and premultiplied
for additive drawing.
Usage: python3 -I make_textures.py"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# The flight sprites were archived once their models were installed (retire_sprites.py); item sprites stay.
SPRITE_DIRS = [SPRITES, os.path.join(REPO, 'assets_legacy', 'projectiles_x2_20261016')]


def sprite_path(name):
    return next((os.path.join(d, name) for d in SPRITE_DIRS if os.path.exists(os.path.join(d, name))),
                os.path.join(SPRITES, name))
SIZE = (512, 128)
# Painted shaft rows averaged into the strip (not its highlight line), and the gain.
SHAFT_ROWS = (81, 82, 85, 86, 87, 88, 89, 90)
SHAFT_GAIN = 1.4
STRIP_ROWS = (120, 128)
ARROW = 'arrowa2_p338.png'
FIRE_ARROW_FRAMES = [f'frarw{frame}2_p5.png' for frame in 'abcdefed']
# Columns of the fire arrow's fletching (and nock) taken over into its body texture.
FIRE_FLETCHING_COLUMNS = 112
# Flame cells: the sprite window [x0, x0 + 256) x [y0, y0 + 128) of each side frame, with every column left of
# FLAME_FIRST_X (shaft and fletching, no flames) cleared.
FLAME_CELL = (256, 128)
FLAME_WINDOW = (160, -4)
FLAME_FIRST_X = 176


def sprite(name):
    return np.array(Image.open(sprite_path(name)).convert('RGBA'))


def dilate(rgba, opaque):
    """Fill every non-opaque pixel with the colour of a nearby opaque one, ring by ring."""
    rgb = rgba[:, :, :3].astype(np.float32)
    known = opaque.copy()
    while not known.all():
        total = np.zeros_like(rgb)
        count = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            shifted = np.roll(np.roll(known, dy, 0), dx, 1)
            total += np.roll(np.roll(rgb * known[:, :, None], dy, 0), dx, 1) * shifted[:, :, None]
            count += shifted
        grow = ~known & (count > 0)
        rgb[grow] = total[grow] / count[grow][:, None]
        known |= grow
    return rgb


def body(side_view, out_name):
    canvas = np.zeros((SIZE[1], SIZE[0], 4), np.uint8)
    canvas[:side_view.shape[0], :side_view.shape[1]] = side_view
    opaque = canvas[:, :, 3] >= 160
    rows = canvas[list(SHAFT_ROWS)].astype(np.float32)
    weights = (rows[:, :, 3] >= 160).astype(np.float32)
    columns = weights.sum(0) > 0
    mean = (rows[:, :, :3] * weights[:, :, None]).sum(0)[columns] / weights.sum(0)[columns][:, None]
    canvas[STRIP_ROWS[0]:STRIP_ROWS[1], columns, :3] = np.clip(mean * SHAFT_GAIN, 0, 255).astype(np.uint8)
    canvas[STRIP_ROWS[0]:STRIP_ROWS[1], columns, 3] = 255
    opaque[STRIP_ROWS[0]:STRIP_ROWS[1]] = canvas[STRIP_ROWS[0]:STRIP_ROWS[1], :, 3] == 255
    rgb = dilate(canvas, opaque)
    out = os.path.join(HERE, 'textures', f'{out_name}_basecolor.png')
    Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), 'RGB').save(out)
    print('wrote', out)


def smoothstep(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def flame_key(rgb):
    """0..1 flame weight: the flames are strongly saturated orange (red far above blue) or brighter than the arrow;
    the painted shaft (brown with a pale highlight) and the iron head are neither, and would add a ghost arrow."""
    red = rgb[:, :, 0].astype(np.float32)
    blue = rgb[:, :, 2].astype(np.float32)
    saturation = (red - blue) / np.maximum(red, 1.0)
    luma = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    # The flames' yellow-white core is unsaturated but brighter than anything on the arrow (its highlight peaks
    # near 160).
    return np.maximum(smoothstep(0.55, 0.8, saturation) * smoothstep(60.0, 120.0, red),
                      smoothstep(175.0, 215.0, luma))


def flame_flipbook():
    width, height = FLAME_CELL
    x0, y0 = FLAME_WINDOW
    atlas = np.zeros((height * 4, width * 2, 4), np.uint8)
    for index, name in enumerate(FIRE_ARROW_FRAMES):
        frame = sprite(name)
        frame[:, :FLAME_FIRST_X, 3] = 0
        cell = np.zeros((height, width, 4), np.uint8)
        for y in range(height):
            if 0 <= y0 + y < frame.shape[0]:
                cell[y, :min(width, frame.shape[1] - x0)] = frame[y0 + y, x0:x0 + width]
        cell[:, :, 3] = (cell[:, :, 3] * flame_key(cell[:, :, :3]) + 0.5).astype(np.uint8)
        cell[:, :, :3] = (cell[:, :, :3].astype(np.float32) * (cell[:, :, 3:4] / 255.0) + 0.5).astype(np.uint8)
        row, column = divmod(index, 2)
        atlas[row * height:(row + 1) * height, column * width:(column + 1) * width] = cell
    out = os.path.join(HERE, 'textures', 'fire_arrow_flame_basecolor.png')
    Image.fromarray(atlas, 'RGBA').save(out)
    print('wrote', out)


def main():
    os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
    arrow = sprite(ARROW)
    body(arrow, 'arrow')
    fire = arrow.copy()
    fire[:, :FIRE_FLETCHING_COLUMNS] = sprite(FIRE_ARROW_FRAMES[0])[:, :FIRE_FLETCHING_COLUMNS]
    body(fire, 'fire_arrow')
    flame_flipbook()


main()
