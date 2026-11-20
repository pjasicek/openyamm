"""Textures of the solid projectile models -> textures/<name>_basecolor.png (and _normal.png).

Surfaces are the CC0 Poly Haven scans of the MM8 props batch (../../decorations/mm8_3d/props/source/), the whole
2k scan scaled down (so it still tiles), graded to the projectile sprite's mean colour times GAIN (the sprites carry
their painted light; the game lights the model itself, as for the arrow), with the scan's OpenGL normal map:
- iron (cannonball, spell70c), boulder (cyclops boulder), rock (Rock Blast / Death Blossom, spell41),
  steel (Blades spell39, Shrap Metal spell93, Fire Spike spell07), lava (the burning core of Meteor Shower: dark
  crust, glowing cracks; drawn unlit) and lava_hot (Starburst's star: mostly white-yellow glow, dark cinders).
Ice (Ice Bolt / Ice Blast shards spell26, Flying Fist spell76) is procedural: pale blue with frosty streaks; so is
Harm's serpent (spell70: gold-brown scales, dark diamonds along the back, a paler belly). Toxic Cloud's skull is the
MM6 skeleton's bone texture recoloured poison green, slightly transparent.
Flames: the painted frames of Starburst (sp22b) and Meteor Shower (sp09b), turned so the burning core is at the left
(the front of the flight) and the trail runs right, keyed to the flames (saturation or brightness, as the fire arrow)
and premultiplied for additive drawing, 2 x 4 cells. flames.json records each window in sprite pixels.
Thrown items (dagger, axe, egg): their side-view item sprites in a power-of-two canvas, colours dilated outward.
Usage: python3 -I make_solid_textures.py"""
import json
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
SCANS = os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'props', 'source')
OUT = os.path.join(HERE, 'textures')
GAIN = 1.35
# name: (scan, sprite whose mean is the target, saturation kept (0 grey .. 1 scan), contrast, size)
SURFACES = {
    'iron': ('rust_coarse_01', 'spell70c_p5.png', 0.25, 1.1, 256),
    'boulder': ('rock_boulder_dry', 'boulder_p5.png', 0.8, 1.25, 256),
    'rock': ('rock_boulder_dry', 'sp41b10_p5.png', 1.0, 1.45, 256),
    'steel': ('metal_plate_02', 'sp3912_p6.png', 0.4, 1.15, 256),
}
# Thrown items traced from their side-view sprites (build_traced.py).
TRACED = {'dagger': '3dagger_p547.png', 'axe': '3axe_p547.png', 'egg': '3egg_p547.png'}
# name: (frames, cell size (along, across), window (x0, y0, w, h) in the turned sprite's pixels)
FLAMES = {
    'starburst_flame': ([f'sp22b{c}_p5.png' for c in 'abcdefgh'], (256, 128), (4, 54, 252, 134)),
    'meteor_flame': ([f'sp09b{c}_p5.png' for c in 'abdeghjk'], (256, 64), (4, 90, 252, 72)),
}


def scan(name, suffix, size, mode='RGB'):
    path = os.path.join(SCANS, name, f'{name}_{suffix}_2k.png')
    return np.array(Image.open(path).convert(mode).resize((size, size), Image.LANCZOS)).astype(np.float32)


def sprite_mean(name):
    pixels = np.array(Image.open(sprite_path(name)).convert('RGBA')).astype(np.float32)
    return pixels[pixels[:, :, 3] > 200][:, :3].mean(0)


def save(array, name):
    Image.fromarray(np.clip(array + 0.5, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name))


def grade(rgb, target, saturation, contrast):
    luma = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    rgb = luma[:, :, None] + (rgb - luma[:, :, None]) * saturation
    mean = rgb.reshape(-1, 3).mean(0)
    rgb = mean + (rgb - mean) * contrast
    return np.clip(rgb * (target / np.maximum(rgb.reshape(-1, 3).mean(0), 1.0)), 0, 255)


def smoothstep(edge0, edge1, value):
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def flame_key(rgb):
    red = rgb[:, :, 0].astype(np.float32)
    blue = rgb[:, :, 2].astype(np.float32)
    saturation = (red - blue) / np.maximum(red, 1.0)
    luma = rgb.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    return np.maximum(smoothstep(0.55, 0.8, saturation) * smoothstep(60.0, 120.0, red),
                      smoothstep(175.0, 215.0, luma))


def surfaces():
    for name, (scan_name, target_sprite, saturation, contrast, size) in SURFACES.items():
        target = sprite_mean(target_sprite) * GAIN
        save(grade(scan(scan_name, 'diff', size), target, saturation, contrast), f'{name}_basecolor.png')
        save(scan(scan_name, 'nor_gl', size), f'{name}_normal.png')
        print(name, 'target', target.round())
    # Lava: the rock's dark crevices glow, the rest is a dark crust.
    rock = scan('rock_boulder_dry', 'diff', 256)
    luma = rock @ np.array([0.299, 0.587, 0.114], np.float32)
    crack = smoothstep(0.45, 0.15, (luma - luma.min()) / (luma.max() - luma.min()))[:, :, None]
    crust = np.array([52, 34, 24], np.float32) * (0.6 + 0.8 * luma[:, :, None] / luma.mean())
    hot = np.array([255, 150, 45], np.float32)
    save(crust * (1.0 - crack) + hot * crack, 'lava_basecolor.png')
    # The falling star burns hotter: most of it glows, white-yellow, with dark cinders.
    glow = smoothstep(0.95, 0.45, (luma - luma.min()) / (luma.max() - luma.min()))[:, :, None]
    cinder = np.array([120, 50, 15], np.float32)
    white_hot = np.array([255, 225, 150], np.float32)
    save(cinder * (1.0 - glow) + white_hot * glow, 'lava_hot_basecolor.png')
    # Ice: pale blue, brighter frosty streaks along the length (u), a little noise.
    rng = np.random.default_rng(7)
    size = 128
    streaks = np.repeat(rng.random((1, size)), size, 0)
    streaks = (np.roll(streaks, 1, 1) + streaks + np.roll(streaks, -1, 1)) / 3.0
    grain = rng.random((size, size)) * 0.25
    ice_target = sprite_mean('sp26b10_p6.png') * 1.2
    ice = ice_target[None, None, :] * (0.75 + 0.35 * streaks[:, :, None] + grain[:, :, None])
    save(np.clip(ice, 0, 255), 'ice_basecolor.png')
    # Harm's serpent: gold-brown scales (the painted serpent's mean x GAIN), a chain of dark diamonds along the back
    # (v = 0.5 round the body), a paler belly (v near 0 and 1); u runs along the body, 12 diamonds.
    width, height = 256, 64
    u = (np.arange(width)[None, :] + 0.5) / width
    v = (np.arange(height)[:, None] + 0.5) / height
    gold = sprite_mean('spell70b12_p5.png') * GAIN
    phase = np.abs(((u * 12.0) % 1.0) - 0.5) * 2.0
    diamond = (np.abs(v - 0.5) * 6.0 + phase) < 1.0
    belly = smoothstep(0.32, 0.1, np.minimum(v, 1.0 - v))
    scale_noise = 0.85 + 0.3 * rng.random((height, width))
    serpent = gold[None, None, :] * scale_noise[:, :, None]
    serpent = serpent * (1.0 - 0.6 * diamond[:, :, None]) + np.array([60.0, 40.0, 0.0]) * belly[:, :, None]
    save(np.clip(serpent, 0, 255), 'serpent_basecolor.png')
    # Toxic Cloud's skull: the MM6 skeleton's bone texture (its UVs come with the skull) as poison green, its
    # luminance onto a dark-to-pale green ramp graded to the painted cloud's mean; alpha 0.6 (drawn blended).
    bone = np.array(Image.open(os.path.join(REPO, 'level_generation', 'decorations', 'mm8_3d', 'props', 'textures',
                                            'skeleton_basecolor.png')).convert('RGB').resize((512, 512), Image.LANCZOS))
    luma = (bone.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)) / 255.0
    dark, pale = np.array([25.0, 60.0, 22.0]), np.array([150.0, 220.0, 115.0])
    toxic = dark + (pale - dark) * np.clip(luma, 0, 1)[:, :, None] ** 1.2
    toxic *= sprite_mean('sp90ba_p6.png') * GAIN / toxic.reshape(-1, 3).mean(0)
    rgba = np.dstack([np.clip(toxic, 0, 255), np.full(luma.shape, 150.0)])
    Image.fromarray(np.clip(rgba + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(
        os.path.join(OUT, 'toxic_skull_basecolor.png'))
    # The fist: a saturated ice blue, near uniform (its shape and occlusion carry the detail). The painted fist's
    # mean is paler, but the enhanced Flying Fist effect lights it red-orange, which turned that pink in game.
    fist = np.array([95.0, 145.0, 210.0])
    save(np.clip(fist[None, None, :] * (0.94 + 0.12 * rng.random((32, 32, 1))), 0, 255), 'fist_ice_basecolor.png')


def flames():
    records = {}
    for name, (frames, cell, window) in FLAMES.items():
        width, height = cell
        x0, y0, w, h = window
        atlas = np.zeros((height * 4, width * 2, 4), np.uint8)
        for index, frame_name in enumerate(frames):
            frame = Image.open(sprite_path(frame_name)).convert('RGBA').rotate(-90, expand=True)
            piece = np.array(frame.crop((x0, y0, x0 + w, y0 + h)).resize((width, height), Image.LANCZOS))
            piece[:, :, 3] = (piece[:, :, 3] * flame_key(piece[:, :, :3]) + 0.5).astype(np.uint8)
            piece[:, :, :3] = (piece[:, :, :3] * (piece[:, :, 3:4] / 255.0) + 0.5).astype(np.uint8)
            row, column = divmod(index, 2)
            atlas[row * height:(row + 1) * height, column * width:(column + 1) * width] = piece
        Image.fromarray(atlas, 'RGBA').save(os.path.join(OUT, f'{name}_basecolor.png'))
        records[name] = {'window': window, 'frames': len(frames)}
        print(name, 'window', window)
    with open(os.path.join(OUT, 'flames.json'), 'w') as handle:
        json.dump(records, handle, indent=2)


def traced():
    """Side-view item sprites copied into a power-of-two canvas, colours dilated outward (build_traced.py maps its
    rings straight onto the sprite's pixels)."""
    for name, sprite_name in TRACED.items():
        image = np.array(Image.open(sprite_path(sprite_name)).convert('RGBA'))
        height, width = image.shape[:2]
        canvas = np.zeros((1 << (height - 1).bit_length(), 1 << (width - 1).bit_length(), 4), np.uint8)
        canvas[:height, :width] = image
        known = canvas[:, :, 3] >= 160
        rgb = canvas[:, :, :3].astype(np.float32)
        while not known.all():
            total = np.zeros_like(rgb)
            count = np.zeros(known.shape, np.float32)
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                shifted = np.roll(np.roll(known, dy, 0), dx, 1)
                total += np.roll(np.roll(rgb * known[:, :, None], dy, 0), dx, 1) * shifted[:, :, None]
                count += shifted
            grow = ~known & (count > 0)
            rgb[grow] = total[grow] / count[grow][:, None]
            known |= grow
        save(rgb, f'{name}_basecolor.png')


def main():
    os.makedirs(OUT, exist_ok=True)
    surfaces()
    flames()
    traced()


main()
