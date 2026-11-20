#!/usr/bin/env python3
"""Liquid surfaces of MM7's stat barrel 7dec32 (decoration_overlays.yml states 1-7 of 7dec32): a copy of the MM6
New Sorpigal barrel's build_liquids.py (../../../mm6_new_sorpigal_3d/barrel/scripts/, read only) in
mm7_deco_7dec32.glb's asset space. Changes: the surface sits SURFACE_Z map units up (8.5 below the 121-unit rim, as
the MM6 barrel's 7 %), the disc radius is the open barrel's inner stave wall at that height (barrel_spec.json and
build_barrel.inner_radius) on the flats of its 24-sided LOD0; on LOD1-LOD3 (16 and 10 sides) its edge hides inside
the 1.4-unit staves. Output names mm7_deco_7dec32_liquid_<colour>.glb. Everything else (palette, foam, ripple,
COLOR_0 shadow, alpha) is unchanged.

Original notes:
Liquid surfaces of the stat barrels (decorations.yml state_overlays of bigbarel).

Each GLB is one disc in the barrel model's asset space, about 7 % of the barrel's height below the rim (rim top
0.8713 in mm6_deco_barrel.glb), so a full barrel still shows a band of dark staves above the liquid. The engine draws
it with the barrel's own placement matrix. Colours follow the barrel events (Global.lua 269-275): red Might, yellow
Accuracy, blue Personality, orange Intellect, green Endurance, purple Speed, white Luck.

v2 (2026-10-13/14, player feedback "the palette is a bit sharp", then the user's requests): muted colours that keep
the seven hues apart, a weaker glow, pale foam drifts with small bubbles after MM9's liquid-*.dtx (one shared pattern
under every colour), a slowly drifting ripple (openyamm_uv_scroll, as on the fountain water), and a glossy surface a
little below the rim of the open barrel (mm6_deco_barrel.glb has no lid since v2: drunk, it is empty). The clear
liquid is slightly transparent, so the dark staves show faintly through it; foam and bubbles are opaque. The shadow
toward the staves is in COLOR_0, so the tiling colour and ripple textures can scroll without moving it.

    python3 barrel_liquids.py [out_dir]     # default ../work/liquids
"""

import io
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

UNITS_PER_METRE = 81.7
_SPEC = json.load(open(Path(__file__).resolve().parent / 'barrel_spec.json'))['7dec32']
SURFACE_Z = _SPEC['surface_z']
SURFACE_Y = SURFACE_Z / UNITS_PER_METRE


def _inner_radius(z):
    """build_barrel.inner_radius: the barrel profile less the 1.4-unit staves."""
    h = _SPEC['height']
    r_end = _SPEC['r_end'][0] if z < h / 2 else _SPEC['r_end'][1]
    return _SPEC['r_mid'] - (_SPEC['r_mid'] - r_end) * ((z - h / 2) / (h / 2)) ** 2 - 1.4


# On the flats of LOD0's 24-sided inner wall at the surface ring.
RADIUS = _inner_radius(SURFACE_Z) * math.cos(math.pi / 24) / UNITS_PER_METRE
SEGMENTS = 32
# Ring radii as fractions of RADIUS; denser toward the staves, where the COLOR_0 shadow falls off.
RINGS = [0.4, 0.65, 0.82, 0.93, 1.0]
TEXTURE_SIZE = 256
# Texture repeats across the disc diameter, and the drift in texture units per second (one disc width in ~50 s).
TILES = 1.0
SCROLL = [0.016, 0.011]
ROUGHNESS = 0.1
SPECULAR = 0.6
GLOW = 0.06
# Opacity of the clear liquid (foam and bubbles are opaque): the open barrel's dark staves show faintly through.
ALPHA = 0.5

# sRGB base colours by barrel state (1..7).
LIQUIDS = [
    ("red", (164, 28, 26)),
    ("yellow", (214, 162, 36)),
    ("blue", (38, 72, 168)),
    ("orange", (214, 98, 22)),
    ("green", (46, 138, 48)),
    ("purple", (112, 38, 152)),
    ("white", (214, 210, 198)),
]


def edge_shade(fraction):
    # Linear multiplier of the base colour: full in the middle, shadowed by the staves toward the rim.
    return 1.0 - 0.5 * fraction ** 3


def disc_mesh():
    positions = [(0.0, SURFACE_Y, 0.0)]
    shades = [edge_shade(0.0)]
    for fraction in RINGS:
        for segment in range(SEGMENTS):
            angle = 2.0 * math.pi * segment / SEGMENTS
            positions.append((RADIUS * fraction * math.cos(angle), SURFACE_Y, RADIUS * fraction * math.sin(angle)))
            shades.append(edge_shade(fraction))
    indices = []
    for segment in range(SEGMENTS):
        following = (segment + 1) % SEGMENTS
        # Counter-clockwise seen from above (+y).
        indices += [0, 1 + following, 1 + segment]
    for ring in range(1, len(RINGS)):
        inner = 1 + (ring - 1) * SEGMENTS
        outer = 1 + ring * SEGMENTS
        for segment in range(SEGMENTS):
            following = (segment + 1) % SEGMENTS
            indices += [inner + segment, inner + following, outer + following]
            indices += [inner + segment, outer + following, outer + segment]
    positions = np.array(positions, dtype=np.float32)
    normals = np.tile(np.array([0.0, 1.0, 0.0], dtype=np.float32), (len(positions), 1))
    uvs = np.stack([positions[:, 0], positions[:, 2]], axis=1) / (2.0 * RADIUS) * TILES + 0.5
    tangents = np.tile(np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32), (len(positions), 1))
    colors = np.array([(shade, shade, shade, 1.0) for shade in shades], dtype=np.float32)
    return positions, normals, uvs.astype(np.float32), tangents, colors, np.array(indices, dtype=np.uint16)


def periodic_noise(seed, frequency, bandwidth):
    """Isotropic noise that tiles: white noise band-passed around `frequency` cycles per texture, -1..1."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((TEXTURE_SIZE, TEXTURE_SIZE)))
    k = np.fft.fftfreq(TEXTURE_SIZE) * TEXTURE_SIZE
    radius = np.hypot(*np.meshgrid(k, k))
    field = np.real(np.fft.ifft2(spectrum * np.exp(-((radius - frequency) / bandwidth) ** 2)))
    return field / np.abs(field).max()


def froth_layers():
    """Shared by the colour and ripple maps, after MM9's liquid-*.dtx: pale foam patches with small bubbles.

    Returns the foam cover (0..1), the bubble rims (0..1) and the bubble domes (0..1), all tiling.
    """
    # Fine speckle, kept where a broad cluster field is high, so foam gathers in drifts.
    cluster = np.clip(periodic_noise(23, 1.5, 1.0) * 1.6 + 0.2, 0.0, 1.0)
    speckle = np.clip((periodic_noise(29, 18.0, 6.0) - 0.05) * 3.0, 0.0, 1.0)
    foam = cluster * speckle
    rng = np.random.default_rng(31)
    coords = np.arange(TEXTURE_SIZE)
    u, v = np.meshgrid(coords, coords)
    rims = np.zeros_like(foam)
    domes = np.zeros_like(foam)
    placed = 0
    while placed < 40:
        x, y = rng.uniform(0, TEXTURE_SIZE, size=2)
        # Mostly in the foam, a few loose ones on the clear liquid.
        if rng.uniform() > 0.12 + 0.88 * foam[int(y), int(x)]:
            continue
        radius = rng.uniform(2.5, 5.0)
        du = (u - x + TEXTURE_SIZE / 2) % TEXTURE_SIZE - TEXTURE_SIZE / 2
        dv = (v - y + TEXTURE_SIZE / 2) % TEXTURE_SIZE - TEXTURE_SIZE / 2
        distance = np.hypot(du, dv) / radius
        rims = np.maximum(rims, np.clip(1.0 - np.abs(distance - 0.75) * 3.0, 0.0, 1.0))
        domes = np.maximum(domes, np.sqrt(np.clip(1.0 - distance ** 2, 0.0, 1.0)))
        placed += 1
    return foam, rims, domes


def base_color_image(srgb, layers):
    foam, rims, _ = layers
    # Slow mottling (+-8 %); the radial shadow is the vertex colour.
    mottle = periodic_noise(7, 1.5, 1.5)
    base = np.array(srgb, dtype=np.float32)[None, None, :] * (1.0 + 0.08 * mottle)[:, :, None]
    # Foam is the liquid's own hue thinned toward white.
    pale = base * 0.45 + 255.0 * 0.55
    cover = np.clip(0.45 * foam + 0.6 * rims, 0.0, 1.0)[:, :, None]
    color = base * (1.0 - cover) + pale * cover
    alpha = (ALPHA + (1.0 - ALPHA) * cover) * 255.0
    return Image.fromarray(np.clip(np.concatenate([color, alpha], axis=2), 0, 255).astype(np.uint8), "RGBA")


def normal_image(layers):
    # Shallow, irregular ripples about a quarter of the disc across, plus the bubbles' domes.
    _, _, domes = layers
    height = 0.4 * periodic_noise(11, 4.0, 1.5) + 0.12 * domes
    du = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dv = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    normal = np.stack([-du, -dv, np.ones_like(height)], axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    return Image.fromarray(((normal * 0.5 + 0.5) * 255).astype(np.uint8), "RGB")


def png_bytes(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def write_glb(path, name, srgb, layers):
    positions, normals, uvs, tangents, colors, indices = disc_mesh()
    chunks = []
    views = []

    def add_view(data, target=None):
        offset = sum(len(chunk) for chunk in chunks)
        padded = data + b"\0" * (-len(data) % 4)
        chunks.append(padded)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        views.append(view)
        return len(views) - 1

    accessors = []

    def add_accessor(array, kind, component, target, bounds=False):
        accessor = {"bufferView": add_view(array.tobytes(), target), "componentType": component,
                    "count": int(array.shape[0]), "type": kind}
        if bounds:
            accessor["min"] = array.min(axis=0).tolist()
            accessor["max"] = array.max(axis=0).tolist()
        accessors.append(accessor)
        return len(accessors) - 1

    position = add_accessor(positions, "VEC3", 5126, 34962, bounds=True)
    normal = add_accessor(normals, "VEC3", 5126, 34962)
    tangent = add_accessor(tangents, "VEC4", 5126, 34962)
    uv = add_accessor(uvs, "VEC2", 5126, 34962)
    color = add_accessor(colors, "VEC4", 5126, 34962)
    index = add_accessor(indices, "SCALAR", 5123, 34963)
    base_view = add_view(png_bytes(base_color_image(srgb, layers)))
    normal_view = add_view(png_bytes(normal_image(layers)))

    linear = [(channel / 255.0) ** 2.2 for channel in srgb]
    document = {
        "asset": {"version": "2.0", "generator": "OpenYAMM barrel_liquids.py"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Liquid"}],
        "meshes": [{"name": "Liquid", "primitives": [{
            "attributes": {"POSITION": position, "NORMAL": normal, "TANGENT": tangent, "TEXCOORD_0": uv,
                           "COLOR_0": color},
            "indices": index, "material": 0}]}],
        "materials": [{
            "name": "liquid_" + name,
            "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0,
                                     "roughnessFactor": ROUGHNESS},
            "normalTexture": {"index": 1, "scale": 1.0},
            "alphaMode": "BLEND",
            # A faint glow keeps the colour readable in dim dungeons.
            "emissiveFactor": [value * GLOW for value in linear],
            "extras": {"openyamm_uv_scroll": SCROLL, "openyamm_specular": SPECULAR},
        }],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "images": [{"bufferView": base_view, "mimeType": "image/png", "name": "liquid_" + name + "_basecolor"},
                   {"bufferView": normal_view, "mimeType": "image/png", "name": "liquid_normal"}],
        "textures": [{"source": 0, "sampler": 0}, {"source": 1, "sampler": 0}],
        "accessors": accessors,
        "bufferViews": views,
    }
    binary = b"".join(chunks)
    document["buffers"] = [{"byteLength": len(binary)}]
    text = json.dumps(document, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    with open(path, "wb") as output:
        output.write(struct.pack("<III", 0x46546C67, 2, total))
        output.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        output.write(struct.pack("<II", len(binary), 0x004E4942) + binary)


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "work" / "liquids"
    print('SURFACE', SURFACE_Z, 'units', round(SURFACE_Y, 5), 'm; RADIUS', round(RADIUS * UNITS_PER_METRE, 2), 'units',
          round(RADIUS, 5), 'm')
    out_dir.mkdir(parents=True, exist_ok=True)
    layers = froth_layers()
    for name, srgb in LIQUIDS:
        path = out_dir / f"mm7_deco_7dec32_liquid_{name}.glb"
        write_glb(path, name, srgb, layers)
        print(path, path.stat().st_size)


if __name__ == "__main__":
    main()
