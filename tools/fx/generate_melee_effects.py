#!/usr/bin/env python3
"""Generate the melee contact effects: slash, thrust, crush and claw (original OpenYAMM artwork, CC0).

Writes:
  assets_source/engine/effects/authored/textures/melee_*.png  procedural frames (lossless sources, local)
  assets_dev/engine/effects/authored/sprites/melee_*.yml      effect sprites, each naming its cooked atlas
  assets_dev/engine/effects/authored/melee_resource_bindings.yml
  assets_dev/engine/effects/authored/melee_library.yml        openyamm:fx/melee/* effects
then runs tools/cook_effect_textures.py, which packs each sprite's frames into one BC7 (desktop) and one ASTC
(android) atlas, textures/<sprite>.oytex, the files the game loads (--no-cook skips it).

The game spawns one effect per landed melee blow at the contact point (MELEE_HIT_FEEDBACK_DESIGN.md). Every layer
lies in the effect's local XY plane: local +X is the direction of the blow on screen and local +Y the outer side of the
arc, and the game turns that plane to face the camera. The arc and thrust flipbooks travel along +U; the thrust head
ends at THRUST_HEAD_U, which the recipe offsets onto the contact point. Sizes are tuned for a 160-unit target; the
game scales the whole effect by the target's height.

Deterministic: edit the parameters here and rerun. Requires numpy, Pillow and PyYAML.
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
AUTHORED = ROOT / "assets_dev/engine/effects/authored"
SOURCES = ROOT / "assets_source/engine/effects/authored/textures"
SPRITE = "openyamm:effect-sprite/"
TEXTURE = "openyamm:texture/fx/"

# Arc: a circle below the texture whose top crosses it; the sweep runs from ARC_START to ARC_END degrees.
ARC_SIZE = (512, 256)
ARC_CENTER_Y = -0.705
ARC_RADIUS = 1.005
ARC_START = 156.0
ARC_END = 24.0
ARC_FPS = 45
# Where the blade crosses the contact point, in the texture's x (-1 to 1): about 70% through the sweep, so most of the
# arc lies on the side the blow came from.
ARC_CONTACT_X = 0.44
# (head progress, trail length as a fraction of the sweep, thickness) per sweep frame; the last entry is the
# lingering frame that fades after the sweep.
ARC_FRAMES = [(0.16, 0.16, 1.0), (0.38, 0.36, 1.0), (0.60, 0.52, 1.0), (0.80, 0.62, 0.95), (0.94, 0.66, 0.9),
              (1.0, 0.62, 0.8)]
ARC_LINGER = (1.0, 0.58, 0.55)

THRUST_SIZE = (512, 128)
THRUST_FPS = 40
THRUST_HEAD_U = 0.93
# (head position along U, trail length in U, thickness) per frame.
THRUST_FRAMES = [(0.30, 0.30, 1.0), (0.62, 0.55, 1.0), (0.93, 0.80, 1.0), (0.93, 0.70, 0.8)]
THRUST_LINGER = (0.93, 0.55, 0.5)

IMPACT_SIZE = 256
IMPACT_FPS = 40
IMPACT_FRAMES = 5

# Logical (world) sizes of the sprites at scale 1, for a 160-unit target.
ARC_LOGICAL = (250, 125)
THRUST_LOGICAL = (240, 60)
IMPACT_LOGICAL = 150
RING_LOGICAL = 150
FLARE_LOGICAL = 110
CHIP_LOGICAL = 16


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def value_noise_1d(samples, cells, rng, octaves=3):
    """Smooth 1D fractal noise in [0, 1] sampled at positions in [0, 1]."""
    total = np.zeros_like(samples)
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        count = cells * 2 ** octave
        lattice = rng.random(count + 2)
        x = np.clip(samples, 0.0, 1.0) * count
        x0 = np.floor(x).astype(int)
        f = smoothstep(0.0, 1.0, x - x0)
        total += amplitude * (lattice[x0] * (1.0 - f) + lattice[x0 + 1] * f)
        norm += amplitude
        amplitude *= 0.5
    return total / norm


def colourise(intensity, edge_rgb, core_rgb=(1.0, 1.0, 1.0)):
    """White-hot where intense, the edge colour where faint; alpha follows intensity."""
    intensity = np.clip(intensity, 0.0, 1.0)
    mix = np.sqrt(intensity)[..., None]
    rgb = np.array(edge_rgb)[None, None, :] * (1.0 - mix) + np.array(core_rgb)[None, None, :] * mix
    rgba = np.empty(intensity.shape + (4,))
    rgba[..., :3] = rgb
    rgba[..., 3] = intensity
    return rgba


def blurred(intensity, radius, size=None, gain=1.6):
    """A soft halo of an intensity map, optionally at a smaller size."""
    image = Image.fromarray(np.clip(intensity * 255.0, 0, 255).astype(np.uint8), "L")
    if size:
        image = image.resize(size, Image.LANCZOS)
    image = image.filter(ImageFilter.GaussianBlur(radius))
    return np.clip(np.asarray(image, dtype=np.float64) / 255.0 * gain, 0.0, 1.0)


def arc_intensity(head, trail, thickness, seed):
    width, height = ARC_SIZE
    rng = np.random.default_rng(seed)
    x = (np.arange(width) + 0.5) / width * 2.0 - 1.0
    y = 0.5 - (np.arange(height) + 0.5) / height
    px, py = np.meshgrid(x, y)
    # The texture is twice as wide as tall: x spans 2 units, y spans 1, so distances are isotropic.
    radius = np.hypot(px, py - ARC_CENTER_Y)
    angle = np.degrees(np.arctan2(py - ARC_CENTER_Y, px))
    sweep = ARC_START - ARC_END
    head_angle = ARC_START - head * sweep
    # s: 0 at the head, 1 at the tail end of the trail.
    s = (angle - head_angle) / max(trail * sweep, 1e-3)
    along = np.clip(s, 0.0, 1.0)
    # Thickest just behind the head, tapering to a hairline at the tail; the head is a short rounded cap.
    band = 0.2 * thickness * (1.0 - along) ** 0.7 * smoothstep(-0.04, 0.10, s)
    offset = radius - ARC_RADIUS
    outer = 1.0 - smoothstep(0.0, 0.006, offset)
    inner = np.clip((offset + band) / np.maximum(band, 1e-4), 0.0, 1.0)
    # A bright rim fading inwards over the band, and a faint wide smear inside it (the air the blade cut).
    smear = np.clip((offset + 2.4 * band) / np.maximum(2.4 * band, 1e-4), 0.0, 1.0)
    across = outer * (inner ** 1.6 + 0.22 * smear ** 1.5)
    # Fine concentric streaks (the smear of the edge) that break up the tail.
    radial = np.clip((ARC_RADIUS - radius) / 0.16, 0.0, 1.0)
    streaks = value_noise_1d(radial, 24, rng, octaves=2)
    erosion = smoothstep(along * 0.9 - 0.05, along * 0.9 + 0.25, streaks)
    fade = (1.0 - along) ** 1.3 * (s >= -0.05) * (s <= 1.0)
    intensity = across * fade * (0.55 + 0.45 * erosion)
    # A hot glint on the rim at the head.
    glint = np.exp(-((angle - head_angle) / 4.0) ** 2) * np.exp(-(offset / 0.012) ** 2)
    intensity = intensity + 0.6 * glint * thickness
    return np.clip(intensity * 1.15, 0.0, 1.0)


def thrust_intensity(head, trail, thickness, seed):
    width, height = THRUST_SIZE
    rng = np.random.default_rng(seed)
    u = (np.arange(width) + 0.5) / width
    v = (np.arange(height) + 0.5) / height - 0.5
    pu, pv = np.meshgrid(u, v)
    s = (head - pu) / max(trail, 1e-3)
    along = np.clip(s, 0.0, 1.0)
    # A pointed head widening over a short distance, then tapering to the tail.
    half = 0.16 * thickness * smoothstep(-0.01, 0.12, s) * (1.0 - along) ** 0.6
    across = np.exp(-(pv / np.maximum(half, 1e-4)) ** 2 * 2.2) * (half > 1e-4)
    lines = value_noise_1d(np.clip(pv / 0.34 + 0.5, 0.0, 1.0), 20, rng, octaves=2)
    erosion = smoothstep(along * 0.8 - 0.05, along * 0.8 + 0.3, lines)
    fade = (1.0 - along) ** 1.2 * (s >= -0.02) * (s <= 1.0)
    intensity = across * fade * (0.5 + 0.5 * erosion)
    tip = np.exp(-((pu - head) / 0.018) ** 2) * np.exp(-(pv / 0.05) ** 2)
    return np.clip(intensity * 1.2 + 0.7 * tip * thickness, 0.0, 1.0)


def impact_intensity(frame, seed):
    size = IMPACT_SIZE
    rng = np.random.default_rng(seed)
    coords = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    px, py = np.meshgrid(coords, -coords)
    r = np.hypot(px, py)
    angle = np.arctan2(py, px)
    t = frame / (IMPACT_FRAMES - 1)
    total = np.zeros((size, size))
    spikes = 12
    for index in range(spikes):
        base = (index + rng.uniform(-0.3, 0.3)) / spikes * 2.0 * math.pi
        length = rng.uniform(0.55, 0.95) * (0.45 + 0.55 * t ** 0.6)
        start = 0.08 + 0.35 * t ** 1.5
        width = rng.uniform(0.05, 0.09) * (1.0 - 0.6 * t)
        delta = np.angle(np.exp(1j * (angle - base)))
        along = np.clip((r - start) / max(length - start, 1e-3), 0.0, 1.0)
        taper = width * (1.0 - along)
        wedge = np.exp(-(delta / np.maximum(taper, 1e-4)) ** 2 * 3.0) * (r >= start) * (r <= length)
        total = np.maximum(total, wedge * (1.0 - along) ** 0.7)
    core = np.exp(-(r / (0.22 * (1.0 - 0.7 * t))) ** 2)
    intensity = (total * (1.0 - 0.75 * t) + core * (1.0 - t) ** 1.5)
    return np.clip(intensity * (1.0 - smoothstep(0.92, 1.0, r)), 0.0, 1.0)


def ring_intensity():
    size = IMPACT_SIZE
    coords = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    px, py = np.meshgrid(coords, coords)
    r = np.hypot(px, py)
    rim = np.exp(-((r - 0.86) / 0.03) ** 2)
    inner = smoothstep(0.45, 0.86, r) * (1.0 - smoothstep(0.84, 0.9, r)) * 0.15
    return np.clip(rim + inner, 0.0, 1.0)


def flare_intensity():
    size = IMPACT_SIZE
    coords = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    px, py = np.meshgrid(coords, coords)
    r = np.hypot(px, py)
    horizontal = np.exp(-(py / 0.02) ** 2) * (1.0 - smoothstep(0.0, 0.95, np.abs(px)))
    vertical = np.exp(-(px / 0.025) ** 2) * (1.0 - smoothstep(0.0, 0.6, np.abs(py)))
    glow = np.exp(-(r / 0.16) ** 2) + 0.35 * np.exp(-(r / 0.4) ** 2)
    return np.clip(horizontal + vertical * 0.8 + glow, 0.0, 1.0) * (1.0 - smoothstep(0.9, 1.0, r))


def chip_rgba(size=64):
    """A sharp, irregular light-grey shard with a lit and a shadowed face; the recipe tints it (bone, stone, wood)."""
    scale = 4
    big = size * scale

    def points(outline):
        return [((x + 1.0) * 0.5 * big, (1.0 - (y + 1.0) * 0.5) * big) for x, y in outline]

    outline = [(-0.92, 0.12), (-0.35, 0.5), (0.55, 0.36), (0.95, -0.04), (0.25, -0.42), (-0.62, -0.3)]
    lit = [(-0.92, 0.12), (-0.35, 0.5), (0.55, 0.36), (0.95, -0.04)]
    alpha = Image.new("L", (big, big), 0)
    shade = Image.new("L", (big, big), 0)
    ImageDraw.Draw(alpha).polygon(points(outline), fill=255)
    ImageDraw.Draw(shade).polygon(points(outline), fill=135)
    ImageDraw.Draw(shade).polygon(points(lit), fill=255)
    alpha = np.asarray(alpha.resize((size, size), Image.LANCZOS), dtype=np.float64) / 255.0
    shade = np.asarray(shade.resize((size, size), Image.LANCZOS), dtype=np.float64) / 255.0
    rgba = np.empty((size, size, 4))
    rgba[..., :3] = np.clip(shade / np.maximum(alpha, 1e-3), 0.0, 1.0)[..., None]
    rgba[..., 3] = alpha
    return rgba


def drop_rgba(size=64):
    """A round drop with a soft rim and a small highlight; the recipe tints it (water, ichor, goo)."""
    coords = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    px, py = np.meshgrid(coords, -coords)
    r = np.hypot(px, py)
    alpha = 1.0 - smoothstep(0.6, 0.8, r)
    highlight = np.exp(-(((px + 0.25) ** 2 + (py - 0.3) ** 2) / 0.02))
    shade = 0.7 + 0.3 * (1.0 - r) + 0.6 * highlight
    rgba = np.empty((size, size, 4))
    rgba[..., :3] = np.clip(shade, 0.0, 1.0)[..., None]
    rgba[..., 3] = alpha
    return rgba


def streak_drop_rgba(width=64, height=32):
    """A drop drawn out along its flight: a round head at +U thinning to a hairline tail; the recipe tints it."""
    u = (np.arange(width) + 0.5) / width
    v = (np.arange(height) + 0.5) / height - 0.5
    pu, pv = np.meshgrid(u, v)
    head = 0.85
    half = np.where(pu > head, np.sqrt(np.clip(0.0144 - (pu - head) ** 2, 0.0, None)) / 0.12 * 0.3,
                    0.3 * np.clip((pu - 0.05) / (head - 0.05), 0.0, 1.0) ** 2.4)
    half = np.maximum(half, 1e-4)
    alpha = 1.0 - smoothstep(half * 0.7, half, np.abs(pv))
    alpha *= half > 2e-4
    shade = 0.75 + 0.25 * np.clip(-pv / 0.36, -1.0, 1.0) + 0.35 * np.exp(-((pu - 0.88) ** 2 + (pv + 0.08) ** 2) / 0.002)
    rgba = np.empty((height, width, 4))
    rgba[..., :3] = np.clip(shade, 0.0, 1.0)[..., None]
    rgba[..., 3] = np.clip(alpha, 0.0, 1.0)
    return rgba


def mist_rgba(size=128, seed=53):
    """A soft, ragged puff of fine spray; white, the recipe tints it."""
    rng = np.random.default_rng(seed)
    coords = (np.arange(size) + 0.5) / size * 2.0 - 1.0
    px, py = np.meshgrid(coords, coords)
    r = np.hypot(px, py)
    angle = np.arctan2(py, px)
    ragged = 0.62 + 0.18 * value_noise_1d((angle + math.pi) / (2.0 * math.pi), 9, rng, octaves=3)
    body = 1.0 - smoothstep(ragged * 0.35, ragged, r)
    speckle = np.asarray(Image.fromarray((rng.random((size // 4, size // 4)) * 255).astype(np.uint8), "L")
                         .resize((size, size), Image.BICUBIC), dtype=np.float64) / 255.0
    alpha = body * (0.55 + 0.45 * speckle)
    rgba = np.ones((size, size, 4))
    rgba[..., 3] = np.clip(alpha, 0.0, 1.0)
    return rgba


SILVER = (0.62, 0.76, 1.0)
WARM = (1.0, 0.85, 0.62)


def build_textures():
    """Returns {texture name: RGBA float array}."""
    textures = {}
    for index, (head, trail, thickness) in enumerate(ARC_FRAMES + [ARC_LINGER]):
        name = f"melee_arc_{index:02d}" if index < len(ARC_FRAMES) else "melee_arc_end_00"
        intensity = arc_intensity(head, trail, thickness, seed=7)
        textures[name] = colourise(intensity, SILVER)
        glow = blurred(intensity, 5, size=(256, 128))
        textures[name.replace("melee_arc", "melee_arc_glow")] = colourise(glow, SILVER)
    for index, (head, trail, thickness) in enumerate(THRUST_FRAMES + [THRUST_LINGER]):
        name = f"melee_thrust_{index:02d}" if index < len(THRUST_FRAMES) else "melee_thrust_end_00"
        intensity = thrust_intensity(head, trail, thickness, seed=13)
        textures[name] = colourise(intensity, SILVER)
        glow = blurred(intensity, 4, size=(256, 64))
        textures[name.replace("melee_thrust", "melee_thrust_glow")] = colourise(glow, SILVER)
    for frame in range(IMPACT_FRAMES):
        textures[f"melee_impact_{frame:02d}"] = colourise(impact_intensity(frame, seed=29), WARM)
    textures["melee_ring_00"] = colourise(ring_intensity(), SILVER)
    textures["melee_flare_00"] = colourise(flare_intensity(), WARM)
    textures["melee_chip_00"] = chip_rgba()
    textures["melee_drop_00"] = drop_rgba()
    textures["melee_streak_drop_00"] = streak_drop_rgba()
    textures["melee_mist_00"] = mist_rgba()
    return textures


def sprite_frames(textures):
    """Returns {sprite name: (frames per second, logical size, [texture names])}."""
    arc = sorted(name for name in textures if name.startswith("melee_arc_0"))
    arc_glow = sorted(name for name in textures if name.startswith("melee_arc_glow_0"))
    thrust = sorted(name for name in textures if name.startswith("melee_thrust_0"))
    thrust_glow = sorted(name for name in textures if name.startswith("melee_thrust_glow_0"))
    impact = sorted(name for name in textures if name.startswith("melee_impact_"))
    return {
        "melee_arc": (ARC_FPS, ARC_LOGICAL, arc),
        "melee_arc_glow": (ARC_FPS, ARC_LOGICAL, arc_glow),
        "melee_arc_end": (1, ARC_LOGICAL, ["melee_arc_end_00"]),
        "melee_arc_glow_end": (1, ARC_LOGICAL, ["melee_arc_glow_end_00"]),
        "melee_thrust": (THRUST_FPS, THRUST_LOGICAL, thrust),
        "melee_thrust_glow": (THRUST_FPS, THRUST_LOGICAL, thrust_glow),
        "melee_thrust_end": (1, THRUST_LOGICAL, ["melee_thrust_end_00"]),
        "melee_thrust_glow_end": (1, THRUST_LOGICAL, ["melee_thrust_glow_end_00"]),
        "melee_impact": (IMPACT_FPS, (IMPACT_LOGICAL, IMPACT_LOGICAL), impact),
        "melee_ring": (1, (RING_LOGICAL, RING_LOGICAL), ["melee_ring_00"]),
        "melee_flare": (1, (FLARE_LOGICAL, FLARE_LOGICAL), ["melee_flare_00"]),
        "melee_chip": (1, (CHIP_LOGICAL, CHIP_LOGICAL), ["melee_chip_00"]),
        "melee_drop": (1, (CHIP_LOGICAL, CHIP_LOGICAL), ["melee_drop_00"]),
        "melee_streak_drop": (1, (CHIP_LOGICAL * 2, CHIP_LOGICAL), ["melee_streak_drop_00"]),
        "melee_mist": (1, (128, 128), ["melee_mist_00"]),
    }


def key(time, rgb, transparency):
    return {"time": time, "rgb": list(rgb), "transparency": transparency}


def layer(sprite, start, end, blend, scale_keys, color_keys, offset=None, camera_facing=False):
    component = {"type": "sprite", "start_seconds": start, "end_seconds": end, "sprite_resource": SPRITE + sprite,
                 "blend": blend}
    if offset:
        component["offset"] = list(offset)
    if not camera_facing:
        component.update({"alignment": "world_plane", "plane_right": [1.0, 0.0, 0.0], "plane_up": [0.0, 1.0, 0.0]})
    component["scale_keys"] = [{"time": time, "value": round(value, 3)} for time, value in scale_keys]
    component["color_keys"] = color_keys
    component["motion_keys"] = []
    return component


def fade(rgb, start_transparency, end_transparency=255):
    return [key(0, rgb, start_transparency), key(1, rgb, end_transparency)]


def burst(sprite, count, lifetime, velocity, scale_keys, color_keys, blend="alpha", spread=120.0, gravity=0.0,
          shape="cone", start=0.0, streak=None, spin=0.0):
    """A one-off spray of world-space particles from the effect's origin: along local +Z within a cone (spread 100 is
    about 45 degrees) or in every direction (shape sphere). streak lays sprites along their velocity and stretches
    them; gravity pulls them down the world's -Z (negative values make them rise)."""
    component = {"type": "sprite_system", "start_seconds": start, "end_seconds": round(start + 0.02, 3),
                 "sprite_resource": SPRITE + sprite, "particle_space": "world", "blend": blend,
                 "sprites_per_emission": count, "emission_interval_seconds": 0.02,
                 "particle_lifetime_seconds": lifetime, "emission_shape": shape,
                 "radius": spread if shape == "cone" else 2.0, "plane_direction": [0.0, 0.0, 1.0],
                 "velocity": velocity}
    if gravity:
        component["gravity"] = gravity
    if streak:
        component["alignment"] = "velocity"
        component["stretch_u"] = streak
    if spin:
        component["random_roll"] = True
        component["spin_speed"] = spin
    component["scale_keys"] = [{"time": time, "value": round(value, 3)} for time, value in scale_keys]
    component["color_keys"] = color_keys
    component["motion_keys"] = []
    return component


# Strength variants: (name suffix, size, opacity, glow opacity, heavy extras).
STRENGTHS = [("_light", 0.8, 70, 150, False), ("", 1.0, 0, 90, False), ("_heavy", 1.25, 0, 40, True)]
WHITE = (255, 255, 255)
GLOW_TINT = (190, 215, 255)
HEAVY_TINT = (255, 228, 180)


def slash_recipe(suffix, size, opacity, glow, heavy):
    sweep = round(len(ARC_FRAMES) / ARC_FPS, 3)
    linger = round(sweep + (0.2 if heavy else 0.15), 3)
    tint = HEAVY_TINT if heavy else GLOW_TINT
    # Move the arc so its rim passes through the contact point at ARC_CONTACT_X (local +X is the blow's direction,
    # +Y the outer side; the texture's y spans -0.5 to 0.5 of its height).
    rim_y = math.sqrt(ARC_RADIUS ** 2 - ARC_CONTACT_X ** 2) + ARC_CENTER_Y
    offset = (round(-ARC_CONTACT_X * 0.5 * ARC_LOGICAL[0] * size, 2), round(-rim_y * ARC_LOGICAL[1] * size, 2), 0.0)
    components = [
        layer("melee_arc_glow", 0, sweep, "additive", [(0, size * 1.08)], [key(0, tint, glow)], offset),
        layer("melee_arc", 0, sweep, "alpha", [(0, size)], [key(0, WHITE, opacity)], offset),
        layer("melee_arc_glow_end", sweep, linger, "additive", [(0, size * 1.08), (1, size * 1.12)],
              fade(tint, glow), offset),
        layer("melee_arc_end", sweep, linger, "alpha", [(0, size), (1, size * 1.03)], fade(WHITE, opacity), offset),
        layer("melee_flare", 0.03, 0.12, "additive", [(0, 0.4 * size), (1, 0.9 * size)], fade((255, 245, 225), 0),
              camera_facing=True),
    ]
    if heavy:
        components.append(layer("melee_ring", 0.03, 0.24, "additive", [(0, 0.3), (1, 1.2)], fade(HEAVY_TINT, 110)))
    return components


# The claw rake: three thinner arcs side by side across the blow (local +Y), each a step behind the one before, as
# three talons drawn through the contact point. Dragons' claws and bite (devdocs/solo_action/DRAGON.md).
RAKE_STREAKS = 3
RAKE_SIZE = 0.62
RAKE_SPACING = 0.16      # between neighbouring streaks, as a fraction of the arc's logical height
RAKE_STAGGER = 0.025     # seconds between the streaks
RAKE_TINT = (255, 196, 160)


def rake_offsets(size, outward=0.0):
    """The local offset of each rake streak: the arc's rim through the contact point, the streaks spread about it."""
    base = arc_offset(size * RAKE_SIZE, outward)
    spread = RAKE_SPACING * ARC_LOGICAL[1] * size
    return [(base[0], round(base[1] + (index - (RAKE_STREAKS - 1) / 2) * spread, 2), 0.0)
            for index in range(RAKE_STREAKS)]


def claw_recipe(suffix, size, opacity, glow, heavy):
    sweep = round(len(ARC_FRAMES) / ARC_FPS, 3)
    linger = round(sweep + (0.2 if heavy else 0.15), 3)
    tint = HEAVY_TINT if heavy else RAKE_TINT
    streak = size * RAKE_SIZE
    components = []
    for index, offset in enumerate(rake_offsets(size)):
        start = round(index * RAKE_STAGGER, 3)
        end = round(start + sweep, 3)
        components += [
            layer("melee_arc_glow", start, end, "additive", [(0, streak * 1.08)], [key(0, tint, glow)], offset),
            layer("melee_arc", start, end, "alpha", [(0, streak)], [key(0, WHITE, opacity)], offset),
            layer("melee_arc_end", end, round(end + linger - sweep, 3), "alpha", [(0, streak), (1, streak * 1.03)],
                  fade(WHITE, opacity), offset),
        ]
    components.append(layer("melee_flare", 0.03, 0.12, "additive", [(0, 0.4 * size), (1, 0.9 * size)],
                            fade((255, 235, 215), 0), camera_facing=True))
    if heavy:
        components.append(layer("melee_ring", 0.03, 0.24, "additive", [(0, 0.3), (1, 1.2)], fade(HEAVY_TINT, 110)))
    return components


def thrust_recipe(suffix, size, opacity, glow, heavy):
    sweep = round(len(THRUST_FRAMES) / THRUST_FPS, 3)
    linger = round(sweep + (0.16 if heavy else 0.12), 3)
    tint = HEAVY_TINT if heavy else GLOW_TINT
    # Put the streak's head (THRUST_HEAD_U along the texture) on the contact point.
    shift = -(THRUST_HEAD_U - 0.5) * THRUST_LOGICAL[0] * size
    offset = (round(shift, 2), 0.0, 0.0)
    components = [
        layer("melee_thrust_glow", 0, sweep, "additive", [(0, size)], [key(0, tint, glow)], offset),
        layer("melee_thrust", 0, sweep, "alpha", [(0, size)], [key(0, WHITE, opacity)], offset),
        layer("melee_thrust_glow_end", sweep, linger, "additive", [(0, size)], fade(tint, glow), offset),
        layer("melee_thrust_end", sweep, linger, "alpha", [(0, size)], fade(WHITE, opacity), offset),
        layer("melee_flare", 0.05, 0.15, "additive", [(0, 0.35 * size), (1, 0.8 * size)], fade((255, 245, 225), 0),
              camera_facing=True),
        layer("melee_ring", 0.05, 0.2, "additive", [(0, 0.15 * size), (1, 0.55 * size)], fade(tint, 60)),
    ]
    if heavy:
        components.append(layer("melee_ring", 0.05, 0.26, "additive", [(0, 0.3), (1, 1.1)], fade(HEAVY_TINT, 110)))
    return components


def crush_recipe(suffix, size, opacity, glow, heavy):
    burst = round(IMPACT_FRAMES / IMPACT_FPS, 3)
    tint = HEAVY_TINT if heavy else (255, 238, 210)
    components = [
        layer("melee_impact", 0, burst, "additive", [(0, size)], [key(0, tint, glow // 2)]),
        layer("melee_impact", 0, burst, "alpha", [(0, size * 0.9)], [key(0, WHITE, max(opacity, 40))]),
        layer("melee_ring", 0, 0.2, "additive", [(0, 0.25 * size), (1, 1.0 * size)], fade(tint, 90)),
        layer("melee_flare", 0, 0.09, "additive", [(0, 0.6 * size), (1, 1.0 * size)], fade((255, 245, 225), 0),
              camera_facing=True),
    ]
    return components


def arc_offset(size, outward=0.0):
    """Local offset putting the arc's rim through the contact point, or outward * height beyond it (a miss)."""
    rim_y = math.sqrt(ARC_RADIUS ** 2 - ARC_CONTACT_X ** 2) + ARC_CENTER_Y
    return (round(-ARC_CONTACT_X * 0.5 * ARC_LOGICAL[0] * size, 2),
            round((outward - rim_y) * ARC_LOGICAL[1] * size, 2), 0.0)


def thrust_offset(size, beyond=0.0, beside=0.0):
    """Local offset putting the streak's head on the contact point, or beyond and beside it (a miss)."""
    return (round((beyond - (THRUST_HEAD_U - 0.5)) * THRUST_LOGICAL[0] * size, 2),
            round(beside * THRUST_LOGICAL[1] * size, 2), 0.0)


def miss_recipe(name):
    """A faint blow that passes the target without touching it: no flare, ring or particles. Maces and staves swing
    an arc too."""
    if name == "thrust":
        sweep = round(len(THRUST_FRAMES) / THRUST_FPS, 3)
        offset = thrust_offset(0.9, beyond=0.12, beside=0.9)
        return [
            layer("melee_thrust_glow", 0, sweep, "additive", [(0, 0.9)], [key(0, GLOW_TINT, 170)], offset),
            layer("melee_thrust", 0, sweep, "alpha", [(0, 0.9)], [key(0, WHITE, 150)], offset),
            layer("melee_thrust_end", sweep, round(sweep + 0.08, 3), "alpha", [(0, 0.9)], fade(WHITE, 150), offset),
        ]
    sweep = round(len(ARC_FRAMES) / ARC_FPS, 3)
    if name == "claw":
        streak = 0.9 * RAKE_SIZE
        components = []
        for index, offset in enumerate(rake_offsets(0.9, outward=0.45)):
            start = round(index * RAKE_STAGGER, 3)
            components += [
                layer("melee_arc", start, round(start + sweep, 3), "alpha", [(0, streak)], [key(0, WHITE, 150)],
                      offset),
                layer("melee_arc_end", round(start + sweep, 3), round(start + sweep + 0.1, 3), "alpha",
                      [(0, streak)], fade(WHITE, 150), offset),
            ]
        return components
    offset = arc_offset(0.9, outward=0.45)
    return [
        layer("melee_arc_glow", 0, sweep, "additive", [(0, 0.97)], [key(0, GLOW_TINT, 170)], offset),
        layer("melee_arc", 0, sweep, "alpha", [(0, 0.9)], [key(0, WHITE, 140)], offset),
        layer("melee_arc_end", sweep, round(sweep + 0.1, 3), "alpha", [(0, 0.9)], fade(WHITE, 140), offset),
    ]


# Weapon elements: (name, glow tint, particles). The accent is spawned with the blow's own effect and transform.
ELEMENTS = [
    ("fire", (255, 130, 45), lambda: [
        layer("fire_burst", 0.02, 0.34, "additive", [(0, 0.45), (1, 0.8)], fade((255, 190, 120), 20),
              camera_facing=True),
        burst("flame_lick", 10, 0.45, 120, [(0, 0.45), (1, 0.15)], fade((255, 170, 70), 20), blend="additive",
              shape="sphere", gravity=-300, start=0.03, spin=2.0),
        burst("spark", 10, 0.5, 260, [(0, 0.16), (1, 0.05)], fade((255, 190, 90), 0), blend="additive",
              shape="sphere", gravity=250, start=0.03)]),
    ("air", (150, 170, 255), lambda: [
        burst("electric", 3, 0.14, 30, [(0, 0.6), (1, 0.75)], fade((175, 195, 255), 0), blend="additive",
              shape="sphere", start=0.03, spin=6.0),
        burst("streak", 8, 0.22, 320, [(0, 0.1), (1, 0.05)], fade((190, 210, 255), 0), blend="additive",
              shape="sphere", start=0.03, streak=2.5)]),
    ("water", (140, 215, 255), lambda: [
        burst("glint", 7, 0.45, 70, [(0, 0.2), (1, 0.05)], fade((200, 240, 255), 0), blend="additive",
              shape="sphere", gravity=80, start=0.03, spin=3.0),
        burst("dust_cloud", 2, 0.45, 25, [(0, 0.35), (1, 0.7)], fade((200, 235, 255), 170), shape="sphere",
              start=0.03)]),
    ("body", (130, 225, 85), lambda: [
        burst("melee_drop", 8, 0.45, 200, [(0, 0.9), (1, 0.6)], fade((120, 210, 70), 30), shape="sphere",
              gravity=650, start=0.03),
        burst("smoke_puff", 2, 0.5, 25, [(0, 0.3), (1, 0.6)], fade((120, 200, 80), 175), shape="sphere",
              start=0.03)]),
    ("light", (255, 232, 150), lambda: [
        burst("soft_star", 7, 0.5, 70, [(0, 0.18), (1, 0.05)], fade((255, 240, 185), 0), blend="additive",
              shape="sphere", gravity=-120, start=0.03)]),
    ("dark", (165, 85, 255), lambda: [
        burst("smoke_puff", 3, 0.5, 30, [(0, 0.3), (1, 0.65)], fade((70, 30, 110), 120), shape="sphere",
              start=0.03),
        burst("soft_star", 5, 0.45, 60, [(0, 0.15), (1, 0.05)], fade((180, 110, 255), 0), blend="additive",
              shape="sphere", gravity=90, start=0.03)]),
]


def accent_recipe(name, tint):
    """A coloured halo over the blow's own shape, under its white body: the class layers in the element's tint."""
    if name == "slash":
        sweep = round(len(ARC_FRAMES) / ARC_FPS, 3)
        offset = arc_offset(1.0)
        return [layer("melee_arc_glow", 0, sweep, "additive", [(0, 1.18)], [key(0, tint, 40)], offset),
                layer("melee_arc_glow_end", sweep, round(sweep + 0.18, 3), "additive", [(0, 1.18), (1, 1.24)],
                      fade(tint, 40), offset)]
    if name == "claw":
        sweep = round(len(ARC_FRAMES) / ARC_FPS, 3)
        return [layer("melee_arc_glow", 0, sweep, "additive", [(0, RAKE_SIZE * 1.18)], [key(0, tint, 40)], offset)
                for offset in rake_offsets(1.0)]
    if name == "thrust":
        sweep = round(len(THRUST_FRAMES) / THRUST_FPS, 3)
        offset = thrust_offset(1.0)
        return [layer("melee_thrust_glow", 0, sweep, "additive", [(0, 1.15)], [key(0, tint, 40)], offset),
                layer("melee_thrust_glow_end", sweep, round(sweep + 0.15, 3), "additive", [(0, 1.15)],
                      fade(tint, 40), offset)]
    return [layer("melee_impact", 0, round(IMPACT_FRAMES / IMPACT_FPS, 3), "additive", [(0, 1.2)],
                  [key(0, tint, 50)]),
            layer("melee_ring", 0, 0.24, "additive", [(0, 0.3), (1, 1.15)], fade(tint, 80))]


# Material contact particles, spawned at the contact point with local +Z along the outward surface normal. Blood
# for flesh and leather is the separate MM9 effect (engine/data_tables/melee_hit_materials.txt names each one).
def chips(rgb, count=8, velocity=230, gravity=750, size=1.0):
    return burst("melee_chip", count, 0.55, velocity, [(0, 0.6 * size), (1, 0.5 * size)], fade(rgb, 0, 60),
                 gravity=gravity, spin=9.0, spread=110)


def dust(rgb, transparency=140, count=2, size=1.0):
    return burst("dust_cloud", count, 0.55, 45, [(0, 0.3 * size), (1, 0.75 * size)], fade(rgb, transparency),
                 spread=80)


def drops(rgb, count=10, velocity=240, gravity=900, size=1.0):
    return burst("melee_drop", count, 0.5, velocity, [(0, 1.0 * size), (1, 0.6 * size)], fade(rgb, 20, 90),
                 gravity=gravity, spread=120)


BLOOD_DARK = (105, 6, 8)
BLOOD = (150, 14, 14)


def blood():
    """Our blood: a spurt of drawn-out drops arcing down, round drops in two shades, and a quick fine mist."""
    return [
        burst("melee_streak_drop", 16, 0.5, 340, [(0, 0.38), (1, 0.3)], fade(BLOOD, 0, 70), spread=90, gravity=950,
              streak=1.8),
        burst("melee_drop", 12, 0.55, 240, [(0, 0.4), (1, 0.3)], fade(BLOOD_DARK, 0, 80), spread=120, gravity=900),
        burst("melee_drop", 10, 0.5, 170, [(0, 0.28), (1, 0.2)], fade(BLOOD, 0, 80), spread=140, gravity=850),
        burst("melee_mist", 2, 0.3, 50, [(0, 0.2), (1, 0.45)], fade((120, 10, 12), 100), spread=60),
    ]


CONTACTS = [
    ("blood", "Flesh and leather: a spurt of blood arcing down with a fine mist", blood),
    ("sparks", "Armour and metal: hot sparks arcing out of the blow", lambda: [
        burst("streak", 14, 0.35, 420, [(0, 0.1), (1, 0.05)], fade((255, 215, 140), 0), blend="additive",
              spread=130, gravity=650, streak=3.0),
        layer("glint", 0, 0.07, "additive", [(0, 0.35), (1, 0.55)], fade((255, 240, 200), 0), camera_facing=True)]),
    ("bone", "Bone: pale chips and a puff of bone dust", lambda: [
        chips((235, 225, 200)), dust((225, 215, 195))]),
    ("stone", "Stone: grey chips and dust", lambda: [chips((150, 146, 140)), dust((165, 160, 150), 120, 3)]),
    ("earth", "Earth: brown clods and dust", lambda: [
        chips((120, 92, 64), count=7, size=1.2), dust((140, 112, 82), 110, 3)]),
    ("wood", "Wood: splinters and a little sawdust", lambda: [
        chips((150, 106, 62), count=9), dust((170, 140, 100), 170)]),
    ("glass", "Glass and crystal: glinting shards", lambda: [
        burst("glint", 9, 0.4, 260, [(0, 0.22), (1, 0.08)], fade((215, 240, 255), 0), blend="additive",
              gravity=600, spin=6.0),
        chips((210, 235, 255), count=6, size=0.8)]),
    ("splash", "Liquid: a splash of water drops", lambda: [
        drops((150, 190, 245)), dust((190, 215, 245), 175)]),
    ("motes", "Ethereal: glowing motes scattering from the blow", lambda: [
        burst("soft_star", 9, 0.6, 90, [(0, 0.16), (1, 0.04)], fade((205, 225, 255), 0), blend="additive",
              shape="sphere", gravity=-60),
        burst("wisp", 2, 0.4, 20, [(0, 0.35), (1, 0.6)], fade((200, 220, 255), 120), blend="additive",
              shape="sphere", spin=4.0)]),
    ("ichor", "Chitin: yellow-green ichor and shell flakes", lambda: [
        drops((165, 190, 55), count=8, size=0.9), chips((70, 60, 35), count=4, size=0.8)]),
    ("goo", "Slime: heavy green goo", lambda: [
        drops((95, 190, 80), count=8, velocity=170, gravity=700, size=1.4)]),
]


CLASSES = [
    ("slash", "Sword and axe: a bright arc swept through the contact point", slash_recipe),
    ("thrust", "Spear and dagger: a straight streak ending in a puncture flash at the contact point", thrust_recipe),
    ("crush", "Mace, staff, club and fists: a radial burst and a shock ring, no arc", crush_recipe),
    ("claw", "Dragon claws and bite: a rake of three streaks swept through the contact point", claw_recipe),
]
STRENGTH_NOTES = {"_light": "glancing blow", "": "normal blow", "_heavy": "critical hit or kill, larger and warmer"}


# Contact strength variants, chosen by the blow: (suffix, particle count, speed, size, note). Every material's contact
# effect has all three (engine/data_tables/melee_hit_materials.txt names the base id).
CONTACT_STRENGTHS = [("_light", 0.45, 0.8, 0.8, "glancing blow"), ("", 1.0, 1.0, 1.0, "normal blow"),
                     ("_heavy", 1.8, 1.2, 1.2, "critical hit or kill")]


def scaled_contact(components, count, speed, size):
    for component in components:
        if component["type"] == "sprite_system":
            component["sprites_per_emission"] = max(1, round(component["sprites_per_emission"] * count))
            component["velocity"] = round(component["velocity"] * speed, 1)
        component["scale_keys"] = [{"time": item["time"], "value": round(item["value"] * size, 3)}
                                   for item in component["scale_keys"]]
    return components


def effect(effect_id, display_name, comment, components):
    for index, component in enumerate(components, start=1):
        component["id"] = index
    duration = max(component["end_seconds"] + component.get("particle_lifetime_seconds", 0.0)
                   for component in components)
    return {
        "comment": comment,
        "id": effect_id,
        "display_name": display_name,
        "duration_seconds": round(duration, 3),
        "compatibility_profile": "predictable",
        "components": [{"id": component.pop("id"), **component} for component in components],
    }


def build_effects():
    effects = []
    for name, comment, recipe in CLASSES:
        for suffix, size, opacity, glow, heavy in STRENGTHS:
            components = recipe(suffix, size, opacity, glow, heavy)
            for index, component in enumerate(components, start=1):
                component["id"] = index
            duration = max(component["end_seconds"] for component in components)
            effects.append({
                "comment": f"{comment}; {STRENGTH_NOTES[suffix]}.",
                "id": f"openyamm:fx/melee/{name}{suffix}",
                "display_name": f"Melee {name}{suffix.replace('_', ' ')}",
                "duration_seconds": duration,
                "compatibility_profile": "predictable",
                "components": [{"id": component.pop("id"), **component} for component in components],
            })
        effects.append(effect(f"openyamm:fx/melee/{name}_miss", f"Melee {name} miss",
                              f"Missed {name}: a faint blow passing beside the target.", miss_recipe(name)))
        for element, tint, particles in ELEMENTS:
            effects.append(effect(f"openyamm:fx/melee/{name}_element_{element}", f"Melee {name} {element}",
                                  f"{element.capitalize()} weapon accent over a {name}, spawned with it.",
                                  accent_recipe(name, tint) + particles()))
    for name, comment, particles in CONTACTS:
        for suffix, count, speed, size, note in CONTACT_STRENGTHS:
            effects.append(effect(f"openyamm:fx/melee/contact/{name}{suffix}", f"Melee contact {name}{suffix}",
                                  f"{comment}; {note}.", scaled_contact(particles(), count, speed, size)))
    return effects


class Dumper(yaml.SafeDumper):
    pass


def represent_dict(dumper, data):
    flow = "time" in data and len(data) <= 3
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items(), flow_style=flow)


def represent_list(dumper, data):
    flow = all(isinstance(item, (int, float)) for item in data)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)


Dumper.add_representer(dict, represent_dict)
Dumper.add_representer(list, represent_list)


def write_text(path, text):
    path.write_text(text)
    path.chmod(0o644)


def save(rgba, path):
    pixels = np.clip(np.round(rgba * 255.0), 0, 255).astype(np.uint8)
    Image.fromarray(pixels, "RGBA").save(path, optimize=True)
    path.chmod(0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=AUTHORED, help="authored effects directory")
    parser.add_argument("--sources", type=Path, default=SOURCES, help="where the source frames are written")
    parser.add_argument("--no-cook", action="store_true", help="do not run tools/cook_effect_textures.py")
    args = parser.parse_args()
    textures = build_textures()
    args.sources.mkdir(parents=True, exist_ok=True)
    (args.output / "sprites").mkdir(parents=True, exist_ok=True)
    for name, rgba in textures.items():
        save(rgba, args.sources / f"{name}.png")

    bindings = []
    for name, (fps, (width, height), frames) in sprite_frames(textures).items():
        frame_height, frame_width = textures[frames[0]].shape[:2]
        columns = math.ceil(math.sqrt(len(frames)))
        lines = ["schema: openyamm.effectSprite.v2", f"id: {SPRITE}{name}", f"framesPerSecond: {fps}",
                 f"logicalWidth: {width}", f"logicalHeight: {height}", f"atlas: {TEXTURE}{name}_atlas",
                 f"atlasColumns: {columns}", f"frameCount: {len(frames)}", f"frameWidth: {frame_width}",
                 f"frameHeight: {frame_height}"]
        write_text(args.output / "sprites" / f"{name}.yml", "\n".join(lines) + "\n")
        bindings.append({"resource": f"{TEXTURE}{name}_atlas", "asset": f"engine/effects/authored/textures/{name}.oytex",
                         "status": "bound", "kind": "texture"})
        bindings.append({"resource": SPRITE + name, "asset": f"engine/effects/authored/sprites/{name}.yml",
                         "status": "bound", "kind": "sprite"})
    header = "# Generated by tools/fx/generate_melee_effects.py; edit the generator and rerun, not this file.\n"
    write_text(args.output / "melee_resource_bindings.yml",
               header + yaml.dump({"schema": "openyamm.effectResourceBindings.v1", "bindings": bindings},
                                  sort_keys=False, width=118))

    effects = build_effects()
    lines = [header.rstrip("\n"), "schema: openyamm.effectLibrary.v1", "effects:"]
    for item in effects:
        lines.append("# " + item.pop("comment"))
        lines.extend(yaml.dump([item], Dumper=Dumper, sort_keys=False, width=118).rstrip("\n").split("\n"))
    write_text(args.output / "melee_library.yml", "\n".join(lines) + "\n")
    print(f"wrote {len(textures)} source frames, {len(sprite_frames(textures))} sprites and {len(effects)} effects")
    if not args.no_cook:
        subprocess.run([sys.executable, str(ROOT / "tools/cook_effect_textures.py")], check=True)


if __name__ == "__main__":
    main()
