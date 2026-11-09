#!/usr/bin/env python3
"""Procedural, tileable textures for the New Sorpigal props (props/textures/): every map is built from FFT-filtered
noise, so it repeats seamlessly. Per material: <name>_basecolor.png (sRGB, RGBA where cut out or blended),
<name>_normal.png (OpenGL tangent space, from the material's height field), <name>_mr.png (glTF metallic-roughness:
G = roughness, B = metal). The fire is a looping flipbook atlas (fire_basecolor.png, FIRE_COLUMNS x FIRE_ROWS
frames, left to right then top to bottom), periodic in time so the last frame flows into the first.
Bark for the cauldron logs comes from Poly Haven bark_brown_01 (CC0, trees/source/). Usage: make_textures.py"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'textures')
BARK = os.path.join(HERE, '..', 'trees', 'source', 'bark_brown_01')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(6611)
FIRE_COLUMNS, FIRE_ROWS = 4, 4


def noise(shape, beta=2.0, scale=(1.0, 1.0)):
    """Periodic fractal noise in [0, 1]: white noise filtered by 1 / f^beta (per-axis frequency scale stretches it)."""
    field = rng.normal(size=shape)
    freqs = np.meshgrid(*[np.fft.fftfreq(n) * s for n, s in zip(shape, scale + (1.0,) * (len(shape) - len(scale)))],
                        indexing='ij')
    radius = np.sqrt(sum(f * f for f in freqs))
    radius[(0,) * len(shape)] = 1.0
    spectrum = np.fft.fftn(field) / radius ** beta
    spectrum[(0,) * len(shape)] = 0.0
    values = np.real(np.fft.ifftn(spectrum))
    return (values - values.min()) / (values.max() - values.min())


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def normal_from_height(height, strength):
    """OpenGL normal map of a periodic height field (wrap-around gradients)."""
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save(name, colour_linear, height, strength, roughness, metal, alpha=None):
    rgb = (srgb(colour_linear) * 255 + 0.5).astype(np.uint8)
    if alpha is not None:
        rgb = np.dstack([rgb, (np.clip(alpha, 0, 1) * 255 + 0.5).astype(np.uint8)])
    Image.fromarray(rgb).save(os.path.join(OUT, f'{name}_basecolor.png'))
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        os.path.join(OUT, f'{name}_normal.png'))
    rough = np.broadcast_to(np.asarray(roughness, np.float64), height.shape)
    metal_map = np.broadcast_to(np.asarray(metal, np.float64), height.shape)
    mr = np.dstack([np.zeros(height.shape), rough, metal_map])
    Image.fromarray((np.clip(mr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(OUT, f'{name}_mr.png'))
    mean = (srgb(colour_linear).reshape(-1, 3).mean(0) * 255).round(1)
    print('TEXTURE', name, colour_linear.shape[:2], 'mean sRGB', mean)


def tint(value, dark, light):
    value = value[..., None]
    return np.asarray(dark) * (1 - value) + np.asarray(light) * value


S = 512
# Weathered wood along v (tripod poles, flag pole): long grain streaks, reddish brown like the sprite's tripod.
grain = noise((S, S), 1.6, (8.0, 0.4))
knots = noise((S, S), 2.6)
wood_h = 0.7 * grain + 0.3 * knots
save('wood', tint(wood_h, [0.06, 0.02, 0.012], [0.22, 0.08, 0.04]), wood_h, 6.0, 0.75, 0.0)

# Dark cast iron (kettle, chain, buoy cage): mottled with slight rust.
iron_h = 0.6 * noise((S, S), 2.2) + 0.4 * noise((S, S), 1.3)
rust = np.clip((noise((S, S), 2.8) - 0.7) * 4, 0, 1)
speckle = np.clip((noise((S, S), 0.9) - 0.6) * 4, 0, 1)
iron = tint(iron_h, [0.04, 0.035, 0.045], [0.16, 0.14, 0.17]) * (1 - rust[..., None] * 0.6) \
    + rust[..., None] * 0.6 * np.array([0.14, 0.06, 0.04]) + speckle[..., None] * np.array([0.12, 0.07, 0.10])
save('iron', iron, iron_h, 3.0, 0.55 + 0.25 * rust, 0.75 * (1 - rust))

# Stones around the fire: grey-violet like the sprite's.
stone_h = 0.6 * noise((S, S), 2.0) + 0.4 * noise((S, S), 1.2)
save('stone', tint(stone_h, [0.08, 0.06, 0.08], [0.42, 0.33, 0.40]), stone_h, 5.0, 0.85, 0.0)

# White marble (fountain urn) with grey veins.
veins = np.abs(np.sin(noise((S, S), 1.8) * 18.0))
marble_h = 0.5 * noise((S, S), 2.4) + 0.2 * veins
marble = tint(np.clip(0.55 + 0.45 * noise((S, S), 1.4) - 0.35 * (veins < 0.18), 0, 1),
              [0.16, 0.16, 0.18], [0.62, 0.62, 0.65])
save('marble', marble, marble_h, 2.0, 0.35, 0.0)

# Gold trim (fountain rings and brackets, buoy finial).
gold_h = noise((S, S), 2.6)
save('gold', tint(gold_h, [0.45, 0.28, 0.06], [0.85, 0.62, 0.20]), gold_h, 1.5, 0.35, 1.0)

# Painted red (buoy dome) and red cloth (flag pennant).
red_h = noise((S, S), 2.6)
save('redpaint', tint(red_h, [0.30, 0.012, 0.01], [0.62, 0.03, 0.02]), red_h, 1.5, 0.4, 0.0)
weave = (np.sin(np.arange(S)[None, :] * np.pi / 2) * np.sin(np.arange(S)[:, None] * np.pi / 2)) * 0.5 + 0.5
cloth_h = 0.3 * weave + 0.7 * noise((S, S), 2.2)
save('cloth', tint(cloth_h, [0.30, 0.01, 0.01], [0.70, 0.04, 0.03]), cloth_h, 2.0, 0.85, 0.0)

# Sword: polished steel blade/guard and dark leather grip.
steel_h = noise((S, S), 2.8, (0.3, 6.0))
save('steel', tint(steel_h, [0.62, 0.62, 0.60], [0.92, 0.91, 0.86]), steel_h, 0.8, 0.3, 0.45)
bronze_h = noise((S, S), 2.4)
save('bronze', tint(bronze_h, [0.12, 0.06, 0.025], [0.38, 0.22, 0.09]), bronze_h, 1.5, 0.45, 0.8)
leather_h = noise((S, S), 2.4)
save('leather', tint(leather_h, [0.03, 0.015, 0.008], [0.12, 0.06, 0.03]), leather_h, 3.0, 0.7, 0.0)

# Falling water (fountain streams): blue streaks along v, tileable for scrolling; alpha follows the streaks.
streaks = noise((S, S), 1.5, (6.0, 0.25))
foamy = np.clip((noise((S, S), 1.8, (3.0, 0.5)) - 0.72) * 3, 0, 1) * 0.6
water = tint(streaks, [0.008, 0.03, 0.22], [0.12, 0.26, 0.70]) * (1 - foamy[..., None]) + foamy[..., None] * 0.6
save('water', water, streaks, 3.0, 0.08, 0.0, alpha=0.82 + 0.15 * streaks + 0.1 * foamy)

# Surf foam ring: white foam patches with soft alpha, tileable.
foam_n = noise((S, S), 1.8)
foam_alpha = np.clip((foam_n - 0.28) * 2.2, 0, 1) ** 1.2
save('foam', tint(foam_n, [0.65, 0.75, 0.85], [0.95, 0.97, 1.0]), foam_n, 1.0, 0.3, 0.0, alpha=foam_alpha)

# Logs: Poly Haven bark, darkened toward charcoal.
bark = np.asarray(Image.open(os.path.join(BARK, 'bark_brown_01_diff_2k.png')).convert('RGB').resize((S, S),
                  Image.LANCZOS), np.float64) / 255.0
bark_lin = np.where(bark <= 0.04045, bark / 12.92, ((bark + 0.055) / 1.055) ** 2.4) * np.array([0.7, 0.42, 0.3])
bark_h = np.asarray(Image.open(os.path.join(BARK, 'bark_brown_01_disp_2k.png')).convert('L').resize((S, S),
                    Image.LANCZOS), np.float64) / 255.0
save('logs', bark_lin, bark_h, 8.0, 0.9, 0.0)

# Fire flipbook: frames of 128 x 256, noise periodic in time and scrolled upward by whole periods over the loop.
W, H, T = 128, 256, FIRE_COLUMNS * FIRE_ROWS
flow = noise((T, H, W), 2.0, (0.5, 1.0, 1.4))
flow2 = noise((T, H, W), 1.6, (0.5, 2.0, 2.0))
y = (H - 1 - np.arange(H))[:, None] / (H - 1)                  # 0 at the bottom, 1 at the top
x = (np.arange(W)[None, :] - (W - 1) / 2) / (W / 2)
atlas = np.zeros((H * FIRE_ROWS, W * FIRE_COLUMNS, 4), np.uint8)
for t in range(T):
    shift = int(round(H * 2 * t / T))                          # two noise periods per loop: seamless
    n = np.roll(flow[t], -shift, axis=0) * 0.7 + np.roll(flow2[t], -shift, axis=0) * 0.3
    width = 0.85 * (1 - y) ** 0.8 + 0.04
    body = np.clip(1 - (np.abs(x) / width) ** 2, 0, 1) * np.clip(1.1 - y * 1.0, 0, 1) ** 0.7
    # Tongues: the noise eats the flame from its edges and top, so it breaks into flickering licks.
    heat = np.clip(body * 1.25 - (1 - n) ** 1.3 * (0.55 + 1.1 * y), 0, 1)
    heat = ndimage.gaussian_filter(heat, 0.8)
    colour = np.where(heat[..., None] < 0.55,
                      tint(np.clip(heat / 0.55, 0, 1), [0.30, 0.015, 0.0], [1.0, 0.28, 0.02]),
                      tint(np.clip((heat - 0.55) / 0.45, 0, 1), [1.0, 0.28, 0.02], [1.0, 0.85, 0.45]))
    alpha = np.clip((heat - 0.06) / 0.25, 0, 1)
    frame = np.dstack([(srgb(colour) * 255 + 0.5).astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    row, column = divmod(t, FIRE_COLUMNS)
    atlas[row * H:(row + 1) * H, column * W:(column + 1) * W] = frame
Image.fromarray(atlas).save(os.path.join(OUT, 'fire_basecolor.png'))
print('TEXTURE fire', atlas.shape, 'frames', T)

# Sword blade (not tiled): u runs across the blade from edge to edge on both faces, v along it from the point (inside
# the stone, bottom rows) to the guard (top rows). Polished bevels along both edges, brushed flats, a darker
# fuller down the middle, grime and a few rust specks where the blade enters the stone.
BW, BH = 256, 1024
u = (np.arange(BW) + 0.5) / BW
v = 1.0 - (np.arange(BH) + 0.5) / BH
across = np.abs(u - 0.5) * 2                      # 0 at the centre line, 1 at an edge
bevel = np.clip((across - 0.66) / 0.06, 0, 1)[None, :] * np.ones((BH, 1))
fuller = np.clip(1 - np.abs(u - 0.5) / 0.09, 0, 1)[None, :] ** 0.7 * np.ones((BH, 1))
fuller *= np.clip((v[:, None] - 0.30) / 0.06, 0, 1) * np.clip((0.97 - v[:, None]) / 0.02, 0, 1)
brushed = noise((BH, BW), 2.6, (0.15, 8.0))
grime = np.clip((0.22 - v[:, None]) / 0.12, 0, 1) * (0.55 + 0.45 * noise((BH, BW), 2.0, (1.0, 1.0)))
specks = (noise((BH, BW), 1.2) > 0.86) * np.clip((0.45 - v[:, None]) / 0.3, 0, 1)
# Bright steel: the sprite's blade is near white. A fully metallic, near-mirror blade would only show the blue sky
# in game, so the flats are lighter, warm, somewhat rough and partly metallic (sunlight shows on them).
blade_colour = tint(0.35 + 0.65 * brushed, [0.70, 0.69, 0.66], [0.84, 0.83, 0.79])
blade_colour = blade_colour * (1 - 0.15 * fuller[..., None]) + bevel[..., None] * np.array([0.12, 0.12, 0.11])
blade_colour = blade_colour * (1 - grime[..., None]) + grime[..., None] * np.array([0.10, 0.075, 0.05])
blade_colour = blade_colour * (1 - 0.6 * specks[..., None]) + 0.6 * specks[..., None] * np.array([0.22, 0.09, 0.03])
blade_height = 0.25 * brushed - 0.9 * fuller + 0.4 * grime
save('blade', blade_colour, blade_height, 2.5, np.clip(0.44 - 0.14 * bevel + 0.08 * fuller + 0.35 * grime
     + 0.3 * specks, 0, 1), np.clip(0.6 - 0.35 * grime - 0.4 * specks, 0, 1))

# --- Props for Silver Cove, Misty Islands, Castle Ironfist and Eel Infested Waters (2026-10-09); appended after the
# New Sorpigal textures so those regenerate unchanged.
# Bone (skull pile filler): dark aged bone with grime, matte.
bone_h = 0.55 * noise((S, S), 2.4) + 0.45 * noise((S, S), 1.3)
grime_b = np.clip((noise((S, S), 1.8) - 0.55) * 2.5, 0, 1)
bone = tint(bone_h, [0.045, 0.03, 0.014], [0.24, 0.18, 0.09]) * (1 - 0.45 * grime_b[..., None])
save('bone', bone, bone_h, 3.0, 0.72, 0.0)
# Basalt (burning rock): blackened volcanic rock with a red-brown cast and oxidation, rough.
basalt_h = 0.5 * noise((S, S), 2.2) + 0.5 * noise((S, S), 1.1)
oxide = np.clip((noise((S, S), 1.6) - 0.5) * 2.0, 0, 1)
basalt = tint(basalt_h, [0.007, 0.0025, 0.002], [0.05, 0.015, 0.009]) * (1 - oxide[..., None] * 0.3) \
    + oxide[..., None] * np.array([0.12, 0.012, 0.003])
save('basalt', basalt, basalt_h, 6.0, 0.88, 0.0)
# Lava (the burning rock's cracks, unlit): molten orange-red with brighter yellow cores.
lava_n = noise((S, S), 1.8)
save('lava', np.where(lava_n[..., None] > 0.6, tint(np.clip((lava_n - 0.6) / 0.4, 0, 1), [0.9, 0.18, 0.01],
     [1.0, 0.62, 0.12]), tint(np.clip(lava_n / 0.6, 0, 1), [0.30, 0.02, 0.0], [0.9, 0.18, 0.01])), lava_n, 1.0,
     0.6, 0.0)
# Embers (campfire bed, unlit): glowing orange coals with dark ash patches.
ember_n = noise((S, S), 2.0)
ash = np.clip((noise((S, S), 1.6) - 0.55) * 3, 0, 1)
embers = tint(ember_n, [0.45, 0.06, 0.0], [1.0, 0.45, 0.05]) * (1 - ash[..., None]) + ash[..., None] * 0.04
save('embers', embers, ember_n, 1.0, 0.8, 0.0)
# Blue cloth (fla1 pennant): deep royal blue with the weave and soft folds.
weave_b = (np.sin(np.arange(S)[None, :] * np.pi / 2) * np.sin(np.arange(S)[:, None] * np.pi / 2)) * 0.5 + 0.5
bluecloth_h = 0.3 * weave_b + 0.7 * noise((S, S), 2.2)
save('bluecloth', tint(bluecloth_h, [0.012, 0.02, 0.16], [0.06, 0.10, 0.52]), bluecloth_h, 2.0, 0.85, 0.0)
# Lava veins (burning rock overlay shell, unlit, alpha-tested): fine branching molten streaks along the ridges of a
# noise field, dark red with orange-yellow cores; transparent between them.
ridge = 1 - np.abs(noise((S, S), 2.5) - 0.5) * 2
ridge2 = 1 - np.abs(noise((S, S), 2.3, (1.0, 2.0)) - 0.5) * 2
vein = np.clip((np.maximum(ridge ** 14, 0.85 * ridge2 ** 18) - 0.25) / 0.55, 0, 1)
veins = np.where(vein[..., None] < 0.7, tint(np.clip(vein / 0.7, 0, 1), [0.16, 0.004, 0.0], [0.78, 0.10, 0.008]),
                 tint(np.clip((vein - 0.7) / 0.3, 0, 1), [0.78, 0.10, 0.008], [1.0, 0.45, 0.06]))
save('lavaveins', veins, vein, 1.0, 0.6, 0.0, alpha=np.clip(vein * 3.0, 0, 1))
# Skull (skull pile): one skull's features painted over yellowed, grimy bone, for a sphere-like skull mapped u = around
# (front at u = 0.5), v = bottom (0) to top (1): two dark eye sockets with shaded rims, a nasal cavity, a row of teeth
# with dark gaps above a dark mouth line, and shading under the cheekbones. Not tileable; build_skullpile.py models
# the same features at the same coordinates.
SK = 256
uu = (np.arange(SK)[None, :] + 0.5) / SK
vv = 1.0 - (np.arange(SK)[:, None] + 0.5) / SK
skull_h = 0.55 * noise((SK, SK), 2.4) + 0.45 * noise((SK, SK), 1.3)
grime_s = np.clip((noise((SK, SK), 1.8) - 0.45) * 2.0, 0, 1)
skull = tint(skull_h, [0.07, 0.045, 0.018], [0.36, 0.27, 0.12]) * (1 - 0.6 * grime_s[..., None])
dark = np.zeros((SK, SK))
for eye_u in (0.418, 0.582):
    e = ((uu - eye_u) / 0.066) ** 2 + ((vv - 0.585) / 0.095) ** 2
    dark = np.maximum(dark, np.clip((1.25 - e) * 2.0, 0, 1) ** 0.5)
nose = np.clip(1 - np.abs(uu - 0.5) / (0.012 + 0.25 * np.clip(0.49 - vv, 0, 1)), 0, 1) \
    * (vv > 0.375) * (vv < 0.49)
dark = np.maximum(dark, nose ** 0.7)
teeth_band = (vv > 0.235) * (vv < 0.345) * (np.abs(uu - 0.5) < 0.1)
gaps = (np.abs(((uu - 0.5) / 0.03) % 1 - 0.5) < 0.16) * teeth_band
mouth = (np.abs(vv - 0.29) < 0.014) * (np.abs(uu - 0.5) < 0.105)
cheek = np.clip(1 - (((np.abs(uu - 0.5) - 0.13) / 0.05) ** 2 + ((vv - 0.43) / 0.05) ** 2), 0, 1) * 0.3
dark = np.maximum.reduce([dark, gaps * 0.85, mouth * 0.9, cheek])
teeth_light = teeth_band * (1 - gaps) * 0.12
skull = skull * (1 - dark[..., None] * 0.96) + teeth_light[..., None]
save('skull', skull, skull_h - 0.8 * dark, 3.0, 0.72 + 0.15 * dark, 0.0)

# Bonfire flipbook (campfire, burning rock): like the fire atlas, but the flame fills its frame (a broad base up to a
# tall licking crown), so a card's height is the flame's height. Same frame layout and loop.
bonfire_flow = noise((T, H, W), 1.8, (0.5, 2.0, 0.6))
bonfire_flow2 = noise((T, H, W), 1.6, (0.5, 2.0, 2.0))
bonfire = np.zeros((H * FIRE_ROWS, W * FIRE_COLUMNS, 4), np.uint8)
for t in range(T):
    shift = int(round(H * 2 * t / T))
    n = np.roll(bonfire_flow[t], -shift, axis=0)
    n2 = np.roll(bonfire_flow2[t], -shift, axis=0)
    n = np.clip((n - 0.5) * 1.8 + 0.5, 0, 1)                    # contrast: the noise tears the flame apart
    wx = x + (n2 - 0.5) * 0.9 * y                               # licks sway sideways as they rise
    width = 0.92 * (1 - y) ** 0.6 + 0.06
    body = np.clip(1 - (np.abs(wx) / width) ** 2, 0, 1) * np.clip(1.08 - y * 0.95, 0, 1) ** 0.5
    # Vertical tongues: noise stretched along the flame, eating it harder toward the top and the edges.
    heat = np.clip(body * 1.3 - (1 - n) ** 1.1 * (0.45 + 0.8 * y), 0, 1)
    heat = ndimage.gaussian_filter(heat, 0.8)
    colour = np.where(heat[..., None] < 0.6,
                      tint(np.clip(heat / 0.6, 0, 1), [0.30, 0.01, 0.0], [1.0, 0.24, 0.01]),
                      tint(np.clip((heat - 0.6) / 0.4, 0, 1), [1.0, 0.24, 0.01], [1.0, 0.72, 0.22]))
    alpha = np.clip((heat - 0.04) / 0.16, 0, 1)
    frame = np.dstack([(srgb(colour) * 255 + 0.5).astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    row, column = divmod(t, FIRE_COLUMNS)
    bonfire[row * H:(row + 1) * H, column * W:(column + 1) * W] = frame
Image.fromarray(bonfire).save(os.path.join(OUT, 'bonfire_basecolor.png'))
print('TEXTURE bonfire', bonfire.shape, 'frames', T)
# Camp stones (campfire ring): warm grey field stone with darker pits and soot.
campstone_h = 0.6 * noise((S, S), 2.0) + 0.4 * noise((S, S), 1.2)
soot = np.clip((noise((S, S), 1.7) - 0.55) * 2.5, 0, 1)
save('campstone', tint(campstone_h, [0.05, 0.04, 0.03], [0.27, 0.22, 0.17]) * (1 - 0.5 * soot[..., None]),
     campstone_h, 5.0, 0.85, 0.0)

# --- Pedestal, food bowl, keg and impaled corpses for outd2 (2026-10-09); appended after the earlier textures so they
# regenerate unchanged.
# Granite (ped06 pedestal): light grey stone with dense dark navy speckles, a few white flecks and fine dark cracks.
granite_h = 0.6 * noise((S, S), 2.2) + 0.4 * noise((S, S), 1.0)
speck_n = noise((S, S), 0.9)
speck_d = np.clip((speck_n - np.quantile(speck_n, 0.74)) / 0.04, 0, 1)
speck_n = noise((S, S), 0.3)
speck_w = np.clip((speck_n - np.quantile(speck_n, 0.93)) / 0.04, 0, 1)
crack = np.clip((1 - np.abs(noise((S, S), 2.0) - 0.5) * 2) ** 60 * 1.2, 0, 1) * (noise((S, S), 2.0) > 0.55)
granite = tint(granite_h, [0.14, 0.14, 0.16], [0.36, 0.36, 0.39])
granite = granite * (1 - speck_d[..., None] * 0.85) + speck_d[..., None] * 0.85 * np.array([0.015, 0.018, 0.06])
granite = granite * (1 - speck_w[..., None] * 0.5) + speck_w[..., None] * 0.5 * np.array([0.72, 0.72, 0.74])
granite *= (1 - 0.7 * crack[..., None])
save('granite', granite, granite_h * 0.4 - 0.6 * crack - 0.15 * speck_d, 3.0, 0.45 + 0.2 * crack, 0.0)
# Pewter (food bowl): pale bluish metal with soft mottling and scratches.
pewter_h = noise((S, S), 2.6)
scratch = noise((S, S), 1.8, (0.2, 6.0))
save('pewter', tint(0.7 * pewter_h + 0.3 * scratch, [0.36, 0.37, 0.40], [0.62, 0.63, 0.67]), pewter_h, 0.8,
     0.22 + 0.12 * scratch, 0.85)
# Porridge (food bowl contents): chunky mash of pale yellow lumps between dark olive-green bits.
lumps = 0.5 * noise((S, S), 1.5) + 0.5 * noise((S, S), 1.0)
lumps = np.clip((lumps - lumps.mean()) * 2.6 + 0.6, 0, 1)
bits = noise((S, S), 0.8)
bits = np.clip((bits - np.quantile(bits, 0.82)) / 0.05, 0, 1)
porridge = np.where(lumps[..., None] < 0.5, tint(np.clip(lumps / 0.5, 0, 1), [0.025, 0.035, 0.006], [0.24, 0.24, 0.07]),
                    tint(np.clip((lumps - 0.5) / 0.5, 0, 1), [0.24, 0.24, 0.07], [0.72, 0.64, 0.32]))
porridge = porridge * (1 - bits[..., None] * 0.7) + bits[..., None] * 0.7 * np.array([0.04, 0.07, 0.01])
save('porridge', porridge, lumps - 0.3 * bits, 6.0, 0.5 - 0.2 * lumps, 0.0)
# Keg staves (smlbarel): orange-red wood, eight staves per texture width (u around the keg), grain along v, dark gaps
# between the staves and a slight per-stave tone.
STAVES = 8
stave_u = (np.arange(S) + 0.5) / S * STAVES
stave_id = np.floor(stave_u).astype(int)
stave_frac = stave_u - stave_id
gap = np.clip(1 - np.minimum(stave_frac, 1 - stave_frac) / 0.05, 0, 1)[None, :] * np.ones((S, 1))
tone = np.array([0.92, 1.08, 0.97, 1.04, 0.88, 1.0, 1.1, 0.95])[stave_id][None, :] * np.ones((S, 1))
keg_grain = 0.45 * noise((S, S), 1.3, (6.0, 0.5)) + 0.55 * noise((S, S), 0.7, (10.0, 0.3))
keg_knots = noise((S, S), 2.6)
keg_h = 0.85 * keg_grain + 0.15 * keg_knots
kegwood = tint(np.clip((keg_h - keg_h.mean()) * 2.4 + 0.55, 0, 1), [0.07, 0.012, 0.002], [0.56, 0.17, 0.018]) \
    * tone[..., None]
kegwood = kegwood * (1 - 0.88 * gap[..., None])
save('kegwood', kegwood, keg_h * 0.5 - 0.8 * gap, 4.0, 0.72 + 0.2 * gap, 0.0)
# Keg hoops: worn pale steel band (u along the band, v across it) with eight dark round rivet heads per texture width.
hoop_u = (np.arange(S)[None, :] + 0.5) / S * 8
hoop_v = (np.arange(S)[:, None] + 0.5) / S
# round on the band: a rivet's radius is 0.15 of its spacing along u and 0.14 of the band across v
rivet = np.clip(1 - (((hoop_u % 1) - 0.5) / 0.15) ** 2 - ((hoop_v - 0.5) / 0.14) ** 2, 0, 1) ** 0.5
hoop_h = 0.6 * noise((S, S), 2.4) + 0.4 * noise((S, S), 1.2, (0.2, 4.0))
hoop_rust = np.clip((noise((S, S), 2.0) - 0.62) * 3, 0, 1)
hoop = tint(hoop_h, [0.30, 0.27, 0.25], [0.62, 0.57, 0.52]) * (1 - 0.5 * hoop_rust[..., None]) \
    + hoop_rust[..., None] * 0.5 * np.array([0.16, 0.07, 0.03])
hoop = hoop * (1 - 0.75 * rivet[..., None]) + rivet[..., None] * 0.75 * np.array([0.09, 0.07, 0.06])
save('hoop', hoop, 0.3 * hoop_h + 0.8 * rivet, 3.0, 0.45 + 0.3 * hoop_rust, 0.8 * (1 - hoop_rust))
# Stake (impaled corpses; not tiled in v): u around the stake, v from the ground (0, bottom rows) to the sharpened tip
# (1, top rows). Grey-brown weathered wood, coated in fresh blood toward the tip with drips running down.
SV = 1024
sv = 1.0 - (np.arange(SV)[:, None] + 0.5) / SV
stake_grain = noise((SV, 128), 1.6, (5.0, 0.4))
stake_wood = tint(stake_grain, [0.06, 0.03, 0.015], [0.26, 0.14, 0.07])
drip_n = noise((1, 128), 0.6)[0]
drip_len = np.clip((drip_n - np.quantile(drip_n, 0.55)) / 0.2, 0, 1)[None, :]
coat = np.clip((sv - (0.66 - 0.30 * drip_len)) / 0.015, 0, 1)
smear = np.clip((noise((SV, 128), 1.8, (1.0, 2.0)) - 0.55) * 4, 0, 1) * np.clip((sv - 0.35) / 0.3, 0, 1)
stake_blood = np.maximum(coat, smear * 0.8)
blood_tone = tint(noise((SV, 128), 2.2), [0.10, 0.004, 0.002], [0.36, 0.012, 0.006])
stake = stake_wood * (1 - stake_blood[..., None]) + blood_tone * stake_blood[..., None]
save('stake', stake, stake_grain * 0.6 + 0.2 * stake_blood, 3.0, 0.8 - 0.55 * stake_blood, 0.0)
