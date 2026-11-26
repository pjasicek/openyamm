#!/usr/bin/env python3
"""Ground materials of the outdoor terrain (game/outdoor/OutdoorTerrainMaterials.cpp).

  tools/terrain_materials.py prepare [ids...]
      Pack each downloaded CC0 material in assets_source/engine/terrain_materials (sources.yml) into
      albedo_height.png (RGB colour with low-frequency lighting flattened, A height) and normal_ao_rough.png
      (RG OpenGL normal XY, B ambient occlusion, A roughness), and record the material in the runtime library.
      An entry's pools (coverage, colour) fill that share of its broad hollows with standing water (swamps).
  tools/terrain_materials.py cook --profile desktop|android [--output ROOT] [ids...]
      Block-compress the packed sources with the model texture cooker: desktop into assets_dev, android into
      assets_cooked/android, both at engine/terrain_materials/<id>/<map>.oytex. The cooker sharpens the mips
      (terrain_material jobs) so the ground keeps its detail at grazing distances. --output cooks the named
      materials into another runtime root instead (an isolated stage that owns materials not in the library).
  tools/terrain_materials.py macro
      Write the tileable macro variation texture (engine/terrain_materials/macro_variation.png): RGBA cloudy
      noise at four scales that varies brightness and tint across large fields (UE-style macro variation).
  tools/terrain_materials.py caustics
      Write the tileable caustics (engine/terrain_materials/caustics.png): two Voronoi webs stacked vertically, the
      main pattern and a finer faint one, with varying line thickness and brightness, a soft glow and a slight
      chromatic fringe.
  tools/terrain_materials.py weights --world mm6 --map oute3.odm [--preview out.png]
      Classify every native terrain tile of the map into the world's materials (worlds/<world>/terrain_materials/
      world.yml) and write the map's weight image and slot file beside it, and its liquid edge masks.
  tools/terrain_materials.py edges --world mm6
      Write the liquid edge masks of every map of the world with a slot file (worlds/<world>/terrain_materials/
      liquid_edges/<tile>.png) and remove the ones no map uses: per edge tile over a liquid (water, tar, lava),
      where the liquid shows (255) at the liquid renderer's coverage size, from the native tile's alpha.
  tools/terrain_materials.py plants --world xeen --map xeen_x1.odm
      Write the map's ground plants (worlds/<world>/terrain_decorations/<map>.yml and the transition tiles' masks)
      from the world's hand-written terrain_decorations/plants.yml: what grows on each material, per map. `weights`
      does it too, so a map rebuilt and re-weighted keeps its plants. A world without plants.yml is left alone.
  tools/terrain_materials.py check --world xeen [--map xeen_x7.odm ...] [--max-run 4]
      Check every map's weights (open-air BLVs' too): each texel's layers sum to one (a NaN split stored zeros, a
      texel without weight drew a hard straight seam, F11 2026-11-21) and no straight run of hard material switches
      (both texels at 0.9 or more of different layers) is longer than --max-run texels. Non-zero exit on a failure.

The native tiles are source art (assets_source/worlds/<world>/terrain_x2). The runtime reads only
engine/terrain_materials/library.yml, the cooked arrays and each map's slot file, weights and liquid edge masks.
"""

import argparse
import csv
import fnmatch
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from util.map_export import parse_odm_file  # noqa: E402

SOURCE_ROOT = ROOT / "assets_source/engine/terrain_materials"
LIBRARY = ROOT / "assets_dev/engine/terrain_materials/library.yml"
OUTPUT = {"desktop": ROOT / "assets_dev", "android": ROOT / "assets_cooked/android"}
CODEC = {"desktop": "bc7", "android": "etc2_rgba"}
MAX_SIZE = {"desktop": 2048, "android": 1024}
TILE_TABLES = {"mm6": "terrain_tile_data_3.txt", "mm7": "terrain_tile_data_2.txt", "mm8": "terrain_tile_data.txt"}
# Terrain samples per side on a classic map; an ODM v2 map stores its own (util/map_export.py "terrain_side"), and the
# weight, shore and density images cover its side x texels_per_cell texels.
MAP_CELLS = 128
DIRECT_TILE_BASES = [0, 450, 630]
LIQUIDS = ROOT / "assets_dev/engine/liquids/liquids.yml"
# The asset root whose worlds the weights and edges commands read and write (--assets): assets_dev, or an isolated
# review root that mirrors it.
ASSETS = ROOT / "assets_dev"
# game/render/WaterCoverage.h WaterCoverageSize, and the tile flags of game/maps/TerrainTileData.h.
EDGE_MASK_SIZE = 128
TILE_FLAG_LIQUID = 0x0001 | 0x0002
TILE_FLAG_TRANSITION = 0x0200
SOURCE_SIZE = 2048


def load_yaml(path):
    with open(path) as handle:
        return yaml.safe_load(handle)


def write_yaml(path, data, header):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = header + yaml.safe_dump(data, sort_keys=False, default_flow_style=None, width=118)
    path.write_text(text)


def image(path, mode):
    with Image.open(path) as source:
        picture = source.convert(mode)
        if picture.size != (SOURCE_SIZE, SOURCE_SIZE):
            picture = picture.resize((SOURCE_SIZE, SOURCE_SIZE), Image.LANCZOS)
        return np.asarray(picture, dtype=np.float64)


def gray(path):
    with Image.open(path) as source:
        values = np.asarray(source, dtype=np.float64)
        if values.ndim == 3:
            values = values[..., 0]
        scale = 65535.0 if values.max() > 255.0 else 255.0
        picture = Image.fromarray((values / scale).astype(np.float32), "F")
        if picture.size != (SOURCE_SIZE, SOURCE_SIZE):
            picture = picture.resize((SOURCE_SIZE, SOURCE_SIZE), Image.LANCZOS)
        return np.asarray(picture, dtype=np.float64)


def srgb_to_linear(values):
    return np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(values):
    values = np.clip(values, 0.0, 1.0)
    return np.where(values <= 0.0031308, values * 12.92, 1.055 * values ** (1.0 / 2.4) - 0.055)


def prepare(ids):
    sources = load_yaml(SOURCE_ROOT / "sources.yml")["materials"]
    library = load_yaml(LIBRARY) if LIBRARY.exists() else {"version": 1, "materials": {}}
    for material_id in ids or sources:
        entry = sources[material_id]
        directory = SOURCE_ROOT / material_id
        maps = {key: directory / value for key, value in entry["maps"].items()}
        color = image(maps["color"], "RGB") / 255.0
        # Flatten lighting and tone at scales above an eighth of the repeat: those gradients repeat visibly.
        linear = srgb_to_linear(color)
        luminance = linear @ np.array([0.2126, 0.7152, 0.0722])
        broad = ndimage.gaussian_filter(luminance, SOURCE_SIZE / 8.0, mode="wrap")
        linear *= (luminance.mean() / np.maximum(broad, 1e-4))[..., None] ** 0.85
        color = linear_to_srgb(linear)
        height = gray(maps["height"])
        low, high = np.percentile(height, [0.5, 99.5])
        height = np.clip((height - low) / max(high - low, 1e-6), 0.0, 1.0)
        normal = image(maps["normal_gl"], "RGB")
        if "arm" in maps:
            arm = image(maps["arm"], "RGB")
            ambient, roughness = arm[..., 0], arm[..., 1]
        else:
            roughness = gray(maps["roughness"]) * 255.0
            # A scan without an occlusion map (ambientCG's ice) is unoccluded.
            ambient = gray(maps["ao"]) * 255.0 if "ao" in maps else np.full_like(roughness, 255.0)
        if "pools" in entry:
            # Standing water in the material's broad hollows (swamps): flat, dark, smooth and lowest.
            pools = entry["pools"]
            broad = ndimage.gaussian_filter(height, SOURCE_SIZE * float(pools.get("scale", 0.01)), mode="wrap")
            level = np.percentile(broad, 100.0 * float(pools["coverage"]))
            edge = float(pools.get("edge", 0.03))
            water = np.clip((level + edge - broad) / (2.0 * edge), 0.0, 1.0)
            water = water * water * (3.0 - 2.0 * water)
            color = color * (1.0 - water[..., None]) + np.array(pools["color"]) * water[..., None]
            height = height * (1.0 - water)
            normal[..., :2] = normal[..., :2] * (1.0 - water[..., None]) + 128.0 * water[..., None]
            ambient = ambient * (1.0 - water) + 255.0 * water
            roughness = roughness * (1.0 - water) + float(pools.get("roughness", 0.1)) * 255.0 * water
        albedo_height = np.dstack([color * 255.0, height * 255.0])
        normal_ao_rough = np.dstack([normal[..., 0], normal[..., 1], ambient, roughness])
        for name, pixels in (("albedo_height", albedo_height), ("normal_ao_rough", normal_ao_rough)):
            Image.fromarray(np.clip(pixels + 0.5, 0, 255).astype(np.uint8), "RGBA").save(directory / f"{name}.png")
        library["materials"][material_id] = {
            "albedo_height": f"{material_id}/albedo_height.oytex",
            "normal_ao_rough": f"{material_id}/normal_ao_rough.oytex",
            "mean_color": [round(float(value), 4) for value in color.reshape(-1, 3).mean(axis=0)],
            "physical_size_m": entry["physical_size_m"],
            "license": entry["license"],
            "origin": entry["origin"],
            **({"pools": True} if "pools" in entry else {}),
            # How strongly the ground highlight (sun and point lights) shows on it: rock, gravel, flagstones.
            **({"specular": entry["specular"]} if "specular" in entry else {}),
            # How much of the rain-wet sheen it takes (1 when absent): grass blades scatter instead of forming a film.
            **({"wet_sheen": entry["wet_sheen"]} if "wet_sheen" in entry else {}),
            # Glowing texels (lava, creep veins): {color: [r, g, b], threshold: albedo red minus blue where it starts}.
            **({"emissive": entry["emissive"]} if "emissive" in entry else {}),
        }
        print(f"prepared {material_id}: mean colour {library['materials'][material_id]['mean_color']}")
    library["materials"] = dict(sorted(library["materials"].items()))
    write_yaml(LIBRARY, library, "# Terrain material library, written by tools/terrain_materials.py prepare.\n"
               "# Cooked arrays are relative to this directory; mean_color is the display-encoded albedo mean that\n"
               "# world tints are measured against.\n")


# Bump when the cooker writes different terrain material output for the same inputs.
COOK_REVISION = 1


def cook(profile, ids, force=False, output=None):
    """Cook the layer textures whose source or settings changed since their receipt (assets_source/.cook-cache)."""
    if output is not None and not ids:
        raise SystemExit("cook --output needs the material ids to cook")
    root = output.resolve() if output is not None else OUTPUT[profile]
    library = load_yaml(LIBRARY)["materials"]
    cooker = (ROOT / "build/game/openyamm_model_texture_cook").resolve(strict=True)
    # Another output root keeps its own receipts, so it never marks the default root's files as cooked.
    suffix = "" if output is None else "-" + hashlib.sha256(str(root).encode()).hexdigest()[:8]
    receipts_path = ROOT / "assets_source/.cook-cache/terrain_materials" / f"{profile}{suffix}.json"
    receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() and not force else {}
    jobs, pending = [], {}
    total = 0
    for material_id in ids or library:
        for name, semantic, linear in (("albedo_height", "srgb", 0), ("normal_ao_rough", "linear", 1)):
            total += 1
            source = SOURCE_ROOT / material_id / f"{name}.png"
            target = root / "engine/terrain_materials" / material_id / f"{name}.oytex"
            digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
            inputs = {"source": digest, "codec": CODEC[profile], "max_size": MAX_SIZE[profile],
                      "revision": COOK_REVISION}
            key = target.relative_to(root).as_posix()
            receipt = receipts.get(key)
            if receipt and receipt["inputs"] == inputs and target.exists() \
                    and hashlib.sha256(target.read_bytes()).hexdigest() == receipt["output"]:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            # terrain_material: the cooker sharpens the tiling mips, so detail holds up at grazing distances.
            jobs.append("\t".join(map(str, (source, target, CODEC[profile], semantic, 0, 1, MAX_SIZE[profile],
                                            linear, digest, "terrain_material"))))
            pending[key] = (target, inputs)
    if jobs:
        with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as handle:
            handle.write("\n".join(jobs) + "\n")
        subprocess.run([str(cooker), handle.name], check=True)
        Path(handle.name).unlink()
        for key, (target, inputs) in pending.items():
            receipts[key] = {"inputs": inputs, "output": hashlib.sha256(target.read_bytes()).hexdigest()}
        receipts_path.parent.mkdir(parents=True, exist_ok=True)
        receipts_path.write_text(json.dumps(receipts, indent=1, sort_keys=True) + "\n")
    print(f"cooked {len(jobs)} {profile} terrain material textures, {total - len(jobs)} unchanged")


MACRO_SIZE = 1024


def periodic_noise(rng, wavelength, size=MACRO_SIZE):
    """Tileable cloudy noise with features about wavelength pixels across, stretched to 0..1."""
    white = rng.standard_normal((size, size))
    frequency = np.fft.fftfreq(size)
    radius = np.hypot(*np.meshgrid(frequency, frequency))
    # Two octaves: the main band plus a weaker one at twice the frequency for ragged patch edges.
    spectrum = np.exp(-(radius * wavelength) ** 2) + 0.35 * np.exp(-(radius * wavelength / 2.0) ** 2)
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * spectrum))
    low, high = np.percentile(field, [1.0, 99.0])
    return np.clip((field - low) / (high - low), 0.0, 1.0)


def macro():
    # One repeat covers 16384 world units (32 terrain cells): R ~4000 units, G ~1000, B ~2500 (tint), A ~250.
    rng = np.random.default_rng(1607)
    channels = [periodic_noise(rng, wavelength) for wavelength in (250.0, 64.0, 160.0, 16.0)]
    pixels = np.clip(np.dstack(channels) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    target = LIBRARY.parent / "macro_variation.png"
    Image.fromarray(pixels, "RGBA").save(target, optimize=True)
    print(f"wrote {target}")


CAUSTICS_SIZE = 512


def caustic_web(seed, cells, glow):
    """Tileable Voronoi cell borders on a warped domain: bright, wobbly lines of varying thickness and brightness
    around dark cells, with a soft glow; red and blue are shifted slightly sideways for a chromatic fringe."""
    rng = np.random.default_rng(seed)
    grid = np.arange(cells)
    sites = (np.stack(np.meshgrid(grid, grid), axis=-1).reshape(-1, 2) + 0.15 + 0.7 * rng.random((cells * cells, 2)))
    sites /= cells
    y, x = np.mgrid[0:CAUSTICS_SIZE, 0:CAUSTICS_SIZE] / CAUSTICS_SIZE
    warp_x = (periodic_noise(rng, 40.0, CAUSTICS_SIZE) - 0.5) * 0.05
    warp_y = (periodic_noise(rng, 40.0, CAUSTICS_SIZE) - 0.5) * 0.05
    thickness = 0.0025 + 0.006 * periodic_noise(rng, 60.0, CAUSTICS_SIZE)
    brightness = 0.35 + 0.65 * periodic_noise(rng, 50.0, CAUSTICS_SIZE)
    channels = []
    for shift in (0.0012, 0.0, -0.0012):
        px = (x + warp_x + shift) % 1.0
        py = (y + warp_y) % 1.0
        nearest = np.full(px.shape, 9.0)
        second = np.full(px.shape, 9.0)
        for site_x, site_y in sites:
            dx = np.abs(px - site_x)
            dy = np.abs(py - site_y)
            distance = np.hypot(np.minimum(dx, 1.0 - dx), np.minimum(dy, 1.0 - dy))
            second = np.where(distance < nearest, nearest, np.minimum(second, distance))
            nearest = np.minimum(nearest, distance)
        # Distance from the border between the two nearest sites.
        edge = second - nearest
        line = np.exp(-(edge / thickness) ** 2)
        halo = np.exp(-(edge / (thickness * 5.0)) ** 2)
        channels.append(brightness * (line + glow * halo))
    return np.clip(np.dstack(channels), 0.0, 1.0)


def caustics():
    # One repeat of each web spans a few hundred world units (the shader's scales): seven and eleven cells across.
    layers = [caustic_web(11, 7, 0.22), caustic_web(23, 11, 0.3)]
    pixels = np.clip(np.concatenate(layers, axis=0) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    target = LIBRARY.parent / "caustics.png"
    Image.fromarray(pixels, "RGB").save(target, optimize=True)
    print(f"wrote {target}")


def rgb_to_lab(rgb):
    linear = srgb_to_linear(rgb)
    matrix = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = linear @ matrix.T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116.0 * f[..., 1] - 16.0, 500.0 * (f[..., 0] - f[..., 1]), 200.0 * (f[..., 1] - f[..., 2])],
                    axis=-1)


def world_terrain_config(world):
    return load_yaml(ASSETS / "worlds" / world / "terrain_materials/world.yml")


def tile_table_name(world):
    """The world's tile table: MM6-MM8 by name, another world names it in its world.yml (`tile_table`)."""
    return TILE_TABLES[world] if world in TILE_TABLES else world_terrain_config(world)["tile_table"]


def tile_art_directory(world):
    """The native tile art: the world's own, or that of the world whose tile table it shares (`tile_art_world`)."""
    art_world = world if world in TILE_TABLES else world_terrain_config(world)["tile_art_world"]
    return ROOT / "assets_source/worlds" / art_world / "terrain_x2"


def tile_art_path(world, name):
    """A tile's native art: the art world's, else a shipped world's (the MM7 table's lava rows are MM8's tiles)."""
    for directory in [tile_art_directory(world)] + [ROOT / "assets_source/worlds" / other / "terrain_x2"
                                                    for other in ("mm8", "mm7", "mm6")]:
        if (directory / f"{name}.png").exists():
            return directory / f"{name}.png"
    return tile_art_directory(world) / f"{name}.png"


def tile_pixels(world, name):
    path = tile_art_path(world, name)
    with Image.open(path) as source:
        pixels = np.asarray(source.convert("RGBA"), dtype=np.float64) / 255.0
    return pixels


def matching_rule(rules, name):
    for rule in rules:
        if any(fnmatch.fnmatch(name, pattern) for pattern in rule["match"]):
            return rule
    raise SystemExit(f"No terrain material rule matches tile {name}")


def map_terrain(world, map_name):
    """The map's raw tile id per cell and its 256 resolved tile descriptors (table rows; None for invalid ids)."""
    source = ASSETS / "worlds" / world / "maps" / map_name
    native = parse_odm_file(source)["payload"]
    environment = load_yaml(source.with_suffix(".scene.yml"))["environment"]
    # The map's scene overlay may correct the terrain (Shadowspire's master tile), as it does in the engine.
    overlay = source.with_name(f"{source.stem}_1.scene.yml")
    if overlay.exists():
        environment = {**environment, **(load_yaml(overlay).get("environment") or {})}
    lookups = environment["tile_set_lookup_indices"]
    master = int(environment.get("master_tile", 0))
    table = ASSETS / "engine/data_tables" / tile_table_name(world)
    with open(table) as handle:
        descriptors = list(csv.DictReader(handle, delimiter="\t"))
    tiles = []
    for raw in range(256):
        # As game/maps/TerrainTileData.cpp: MM8 offsets the direct ids by the master tile; 234+ are invalid.
        if raw >= 234 or master >= len(DIRECT_TILE_BASES):
            index = raw if raw < 234 else None
        elif raw < 90:
            index = raw + DIRECT_TILE_BASES[master] if world == "mm8" and raw != 0 else raw
        else:
            index = lookups[(raw - 90) // 36] + (raw - 90) % 36
        tiles.append(descriptors[index] if index is not None else None)
    return native["tile_map"], tiles


def map_tiles(world, map_name):
    """The texture name per cell, side x side rows (the last row and column empty)."""
    tile_map, tiles = map_terrain(world, map_name)
    cells = math.isqrt(len(tile_map))
    names = [["" for _ in range(cells)] for _ in range(cells)]
    for gy in range(cells - 1):
        for gx in range(cells - 1):
            tile = tiles[tile_map[gy * cells + gx]]
            if tile is not None:
                names[gy][gx] = tile["texture_name"].lower()
    return names


def table_number(value):
    value = value.strip()
    return int(value, 16) if value.lower().startswith("0x") else int(value or 0)


def tile_name(tile):
    return (tile["texture_name"].strip().lower() or "pending") if tile is not None else "pending"


def terrain_liquid(liquids, name):
    """The liquids.yml liquid drawing a terrain tile of this name (LiquidTable::findMatch)."""
    for liquid in liquids:
        match = liquid.get("match") or {}
        if "terrain" in liquid.get("applies_to", []) and (
                name in match.get("texture_names", [])
                or any(name.startswith(prefix) for prefix in match.get("texture_prefixes", []))):
            return liquid
    return None


def liquid_edge_tiles(world, map_name, liquids):
    """The map's liquid edge tiles: transitions whose liquid keeps its edge overlay, the overlay's alpha being where
    the liquid shows (findTerrainLiquidForDescriptor and buildOutdoorTerrainTiles in game/maps/MapAssetLoader.cpp)."""
    tile_map, tiles = map_terrain(world, map_name)

    def liquid_base(tile):
        fallback = None
        for candidate in tiles:
            if (candidate is None or table_number(candidate["tileset"]) != table_number(tile["tileset"])
                    or tile_name(candidate) == "pending"
                    or not table_number(candidate["flags"]) & TILE_FLAG_LIQUID
                    or table_number(candidate["flags"]) & TILE_FLAG_TRANSITION):
                continue
            fallback = fallback or candidate
            if table_number(candidate["variant"]) == 0:
                return candidate
        return fallback

    edges = set()
    for raw in set(tile_map):
        tile = tiles[raw]
        name = tile_name(tile)
        if name == "pending":
            continue
        transition = bool(table_number(tile["flags"]) & TILE_FLAG_TRANSITION)
        base = liquid_base(tile) if transition else None
        liquid = terrain_liquid(liquids, name)
        if liquid is None:
            base = base or liquid_base(tile)
            liquid = terrain_liquid(liquids, tile_name(base)) if base is not None else None
        if (liquid is not None and liquid.get("terrain_transition_overlay") and transition and base is not None
                and tile_name(base) != name):
            edges.add(name)
    return edges


def write_liquid_edge(world, name):
    """The liquid's coverage of an edge tile: 255 minus the alpha (the engine's magenta and teal keys transparent),
    box-averaged to EDGE_MASK_SIZE as game/render/WaterCoverage.h waterCoverageFromOverlay."""
    rgba = np.asarray(Image.open(tile_art_path(world, name)).convert("RGBA"))
    size = rgba.shape[0]
    if rgba.shape[1] != size or size % EDGE_MASK_SIZE:
        raise SystemExit(f"{world} tile {name} is {rgba.shape[1]}x{size}, not a multiple of {EDGE_MASK_SIZE} square")
    red, green, blue = (rgba[..., channel].astype(np.int64) for channel in range(3))
    keyed = ((red >= 248) & (green <= 8) & (blue >= 248)) | ((red <= 8) & (green >= 248) & (blue >= 248))
    coverage = np.where(keyed, 255, 255 - rgba[..., 3].astype(np.int64))
    factor = size // EDGE_MASK_SIZE
    count = factor * factor
    blocks = coverage.reshape(EDGE_MASK_SIZE, factor, EDGE_MASK_SIZE, factor).sum(axis=(1, 3))
    mask = ((blocks + count // 2) // count).astype(np.uint8)
    target = ASSETS / "worlds" / world / "terrain_materials/liquid_edges" / f"{name}.png"
    target.parent.mkdir(exist_ok=True)
    Image.fromarray(mask, "L").save(target, optimize=True)
    return target


def edges(world):
    directory = ASSETS / "worlds" / world / "terrain_materials"
    liquids = load_yaml(LIQUIDS)["liquids"]
    # Outdoor maps only: an open-air BLV's ground (`<map>_blv.yml`, XD-17) has no terrain tiles and no liquid edges.
    maps = sorted(path.stem + ".odm" for path in directory.glob("*.yml")
                  if path.name != "world.yml" and not path.stem.endswith("_blv"))
    used = set()
    for map_name in maps:
        used |= liquid_edge_tiles(world, map_name, liquids)
    for name in sorted(used):
        write_liquid_edge(world, name)
    stale = sorted(path for path in (directory / "liquid_edges").glob("*.png") if path.stem not in used)
    for path in stale:
        path.unlink()
    print(f"{world}: {len(used)} liquid edge masks for {len(maps)} maps, {len(stale)} stale removed")


def reference_colors(world, config, names):
    """Lab and display colour of every world material, from its reference tile or its two-material tiles."""
    materials = config["materials"]
    lab, display = {}, {}
    for material, entry in materials.items():
        if entry.get("reference_tile"):
            pixels = tile_pixels(world, entry["reference_tile"])
            opaque = pixels[..., 3] > 0.5
            display[material] = pixels[..., :3][opaque].mean(axis=0)
            lab[material] = rgb_to_lab(display[material])
    used = sorted({name for row in names for name in row if name})
    for material in materials:
        if material in lab:
            continue
        samples = []
        other = None
        for name in used:
            rule = matching_rule(config["tiles"], name)
            # A tile with no art of its own (Shadowspire's gdrdscap, drawn with `shape_from`) gives no colours.
            if material in rule.get("materials", []) and tile_art_path(world, name).exists():
                pixels = tile_pixels(world, name)
                samples.append(pixels[..., :3][pixels[..., 3] > 0.5])
                other = next(m for m in rule["materials"] if m != material)
        if not samples:
            continue
        rgb = np.concatenate(samples)
        points = rgb_to_lab(rgb)
        known = lab[other]
        # The quarter of the pixels least like the other material: edges and mortar would pull a clustering
        # towards the shared background.
        distance = np.linalg.norm(points - known, axis=1)
        mine = distance > np.percentile(distance, 75)
        lab[material], display[material] = points[mine].mean(axis=0), rgb[mine].mean(axis=0)
    return lab, display


def tile_coverage(world, name, rule, slot_of, lab, texels):
    """Per-slot coverage of one tile at texels x texels, summing to one."""
    coverage = np.zeros((texels, texels, len(slot_of)))
    if rule.get("water"):
        return None
    if "material" in rule:
        coverage[..., slot_of[rule["material"]]] = 1.0
        return coverage
    first, second = rule["materials"]
    shape = rule.get("shape_from")
    pixels = tile_pixels(world, name.replace(shape[0], shape[1], 1) if shape else name)
    size = pixels.shape[0]
    rgb = np.stack([ndimage.gaussian_filter(pixels[..., c], size / 128.0, mode="nearest") for c in range(3)], -1)
    points = rgb_to_lab(rgb)
    first_lab, second_lab = lab[first], lab[second]
    if shape:
        # The shape comes from a tile of the same layout whose two parts differ clearly in colour: split it into
        # its two colour clusters, the one nearer the first material taking its place.
        flat = points.reshape(-1, 3)
        centers = np.percentile(flat, [10, 90], axis=0)
        for _ in range(8):
            nearest = np.argmin(np.linalg.norm(flat[:, None, :] - centers[None], axis=-1), axis=1)
            centers = np.array([flat[nearest == k].mean(axis=0) for k in range(2)])
        order = np.argsort(np.linalg.norm(centers - lab[first], axis=-1))
        first_lab, second_lab = centers[order[0]], centers[order[1]]
    to_first = np.linalg.norm(points - first_lab, axis=-1)
    to_second = np.linalg.norm(points - second_lab, axis=-1)
    softness = 0.12 * np.linalg.norm(first_lab - second_lab)
    if softness < 0.12:
        # Two materials of the same colour cannot split a tile: the share would be 0/0 (NaN weights, F11).
        raise SystemExit(f"tile {name}: {first} and {second} have the same classification colour; give one of "
                         "them its own reference_tile in world.yml")
    share = 1.0 / (1.0 + np.exp(np.clip((to_first - to_second) / softness, -40.0, 40.0)))
    share = ndimage.gaussian_filter(share, size / 170.0, mode="nearest")
    step = size // texels
    share = share.reshape(texels, step, texels, step).mean(axis=(1, 3))
    coverage[..., slot_of[first]] = share
    coverage[..., slot_of[second]] = 1.0 - share
    return coverage


def water_mask(world, names, rules, texels):
    """Water share of every weight texel: open water tiles, and shore tiles where their alpha shows the water."""
    cells = len(names)
    size = cells * texels
    mask = np.zeros((size, size))
    cache = {}
    for gy in range(cells):
        for gx in range(cells):
            name = names[gy][gx]
            if not name:
                continue
            if name not in cache:
                if rules[name].get("shore") is False:
                    # Lava, tar and their edges: no beach and no seabed.
                    cache[name] = np.zeros((texels, texels))
                elif rules[name].get("water"):
                    cache[name] = np.ones((texels, texels))
                else:
                    # A tile drawn with another's shape (Shadowspire's roads: `shape_from`) may have no art of its
                    # own (gdrdscap, gdrdcros): its coverage is that tile's.
                    shape = rules[name].get("shape_from")
                    alpha = tile_pixels(world, name.replace(shape[0], shape[1], 1) if shape else name)[..., 3]
                    step = alpha.shape[0] // texels
                    cache[name] = 1.0 - alpha.reshape(texels, step, texels, step).mean(axis=(1, 3))
            mask[gy * texels:(gy + 1) * texels, gx * texels:(gx + 1) * texels] = cache[name]
    return mask


def water_floors(world, map_name, liquids, mask, texels):
    """The texels under horizontal BModel water faces lying at the level of the terrain water they cover (Smuggler's
    Cove's mouth over the sea): the same body of water, so the waterline follows their edges and the rendered seabed
    sinks under them instead of the beach rising through them. Fountains, wells and pools above the ground keep
    the terrain under them."""
    floors = np.zeros(mask.shape, dtype=bool)
    native = parse_odm_file(ASSETS / "worlds" / world / "maps" / map_name)["payload"]
    side = native.get("terrain_side", MAP_CELLS)
    heights = np.array(native["height_map"], dtype=np.float64).reshape(side, side) * 32.0
    half = side * 256.0
    units = 512.0 / texels
    for bmodel in native["bmodels"]:
        for face in bmodel["faces"]:
            name = face["texture_name"].lower()
            liquid = next((entry for entry in liquids if "face" in entry.get("applies_to", [])
                           and entry["kind"] == "water"
                           and (name in (entry.get("match") or {}).get("texture_names", [])
                                or any(name.startswith(prefix)
                                       for prefix in (entry.get("match") or {}).get("texture_prefixes", [])))),
                          None)
            points = [bmodel["vertices"][index] for index in face["vertex_indices"]]
            if liquid is None or len(points) < 3 or len({point["z"] for point in points}) != 1:
                continue
            xs = np.array([point["x"] for point in points], dtype=np.float64)
            ys = np.array([point["y"] for point in points], dtype=np.float64)
            first_x = max(int((xs.min() + half) // units), 0)
            last_x = min(int((xs.max() + half) // units), mask.shape[1] - 1)
            first_y = max(int((half - ys.max()) // units), 0)
            last_y = min(int((half - ys.min()) // units), mask.shape[0] - 1)
            # Texel centres inside the face (even-odd rule).
            px, py = np.meshgrid((np.arange(first_x, last_x + 1) + 0.5) * units - half,
                                 half - (np.arange(first_y, last_y + 1) + 0.5) * units)
            inside = np.zeros(px.shape, dtype=bool)
            for a in range(len(points)):
                b = (a + 1) % len(points)
                crosses = (ys[a] > py) != (ys[b] > py)
                with np.errstate(divide="ignore", invalid="ignore"):
                    edge_x = xs[a] + (py - ys[a]) * (xs[b] - xs[a]) / (ys[b] - ys[a])
                inside ^= crosses & (px < edge_x)
            region = mask[first_y:last_y + 1, first_x:last_x + 1]
            wet = inside & (region > 0.0)
            if not wet.any():
                continue
            # The water level under the face: the lowest native corner of the water and shore cells it covers.
            cells = {(int((first_y + y) // texels), int((first_x + x) // texels)) for y, x in zip(*np.nonzero(wet))}
            level = min(heights[cy + dy, cx + dx] for cy, cx in cells for dy in (0, 1) for dx in (0, 1))
            if -8.0 <= points[0]["z"] - level <= 16.0:
                floors[first_y:last_y + 1, first_x:last_x + 1] |= inside
    return floors


def shore_distance(mask, texels):
    """Signed distance in world units to the waterline: positive on land, negative under water. The mask is
    smoothed over half a cell first: diagonal coasts drawn with square tiles become lines instead of staircases,
    while one-cell rivers and inlets keep their water."""
    units = 512.0 / texels
    land = ndimage.gaussian_filter(mask, texels * 0.5, mode="nearest") < 0.5
    to_water = ndimage.distance_transform_edt(land)
    to_land = ndimage.distance_transform_edt(~land)
    distance = np.where(land, to_water - 0.5, 0.5 - to_land) * units
    return ndimage.gaussian_filter(distance, 1.0, mode="nearest")


def map_config(world, map_name):
    """The world's material config with the map's own entries (world.yml `maps`) applied, and the world's materials
    as they are without them."""
    config = load_yaml(ASSETS / "worlds" / world / "terrain_materials" / "world.yml")
    world_materials = {material: dict(entry) for material, entry in config["materials"].items()}
    for key, keys in (config.get("maps") or {}).get(map_name, {}).items():
        if key in ("shore", "slope"):
            config[key] = {**config[key], **keys}
        elif key == "tiles":
            # The map's own tile rules, tried before the world's.
            config["tiles"] = list(keys) + config["tiles"]
        elif key in config["materials"]:
            config["materials"][key] = {**config["materials"][key], **keys}
        else:
            raise SystemExit(f"world.yml maps.{map_name} names unknown material {key}")
    return config, world_materials


def classification_colors(world, config, world_materials, names):
    """The Lab colours that split transition tiles into their two materials: the world's own materials' (their
    reference tiles show the native tile art), never a map's override of a material's look. X7 and D6 tint both their
    ash and their edge cinder from 6voltyl; split by those, the two halves of every ash edge tile were equally near,
    the split was 0/0 and the weights NaN, stored as zero: a hard straight seam where they met (F11, 2026-11-21)."""
    lab, _ = reference_colors(world, {**config, "materials": world_materials}, names)
    return lab


def check_field(field, map_name):
    """Refuse weights that are not a partition of the ground: every texel's weighted layers sum to one. A NaN (two
    materials split by equal colours) is stored as zero, and a texel without weight draws its first layer with no
    blend: a hard straight seam (F11, 2026-11-21)."""
    if not np.isfinite(field).all():
        bad = np.argwhere(~np.isfinite(field).all(axis=-1))
        raise SystemExit(f"{map_name}: {len(bad)} weight texels are not numbers (first at row, column {bad[0]})")
    sums = field.sum(axis=-1)
    if np.abs(sums - 1.0).max() > 0.01:
        bad = np.argwhere(np.abs(sums - 1.0) > 0.01)
        raise SystemExit(f"{map_name}: {len(bad)} weight texels do not sum to one (first at row, column {bad[0]})")


def weights(world, map_name, texels, preview):
    directory = ASSETS / "worlds" / world / "terrain_materials"
    config, world_materials = map_config(world, map_name)
    library = load_yaml(LIBRARY)["materials"]
    liquids = load_yaml(LIQUIDS)["liquids"]
    for name in sorted(liquid_edge_tiles(world, map_name, liquids)):
        write_liquid_edge(world, name)
    names = map_tiles(world, map_name)
    used = sorted({name for row in names for name in row if name})
    rules = {name: matching_rule(config["tiles"], name) for name in used}
    weighted = []
    for rule in config["tiles"]:
        if any(rules[name] is rule for name in used):
            for material in ([rule["material"]] if "material" in rule else rule.get("materials", [])):
                if material not in weighted:
                    weighted.append(material)
    shore = config.get("shore")
    water = water_mask(world, names, rules, texels) if shore else None
    floors = water_floors(world, map_name, liquids, water, texels) if shore else None
    if shore:
        water[floors] = 1.0
    if water is not None and water.max() < 0.5:
        shore, water = None, None
    if shore and shore["material"] not in weighted:
        weighted.append(shore["material"])
    if len(weighted) > 8:
        raise SystemExit(f"{map_name} uses {len(weighted)} weighted materials; at most 8 are supported")
    layers = list(weighted)
    slope = config.get("slope")
    if slope and slope["material"] not in layers:
        layers.append(slope["material"])
    for material in list(layers):
        variant = config["materials"][material].get("variant")
        if variant and variant not in layers:
            layers.append(variant)
    if len(layers) > 8:
        raise SystemExit(f"{map_name} needs {len(layers)} material layers; at most 8 are supported")
    slot_of = {material: index for index, material in enumerate(weighted)}
    _, display = reference_colors(world, config, names)
    lab = classification_colors(world, config, world_materials, names)
    variant_parent = {entry["variant"]: parent for parent, entry in config["materials"].items()
                      if entry.get("variant") in layers}
    fallback = slot_of.get("dirt", 0)
    cache = {}
    cells = len(names)
    size = cells * texels
    field = np.zeros((size, size, len(weighted)))
    for gy in range(cells):
        for gx in range(cells):
            name = names[gy][gx]
            coverage = None
            if name:
                if name not in cache:
                    cache[name] = tile_coverage(world, name, rules[name], slot_of, lab, texels)
                coverage = cache[name]
            block = field[gy * texels:(gy + 1) * texels, gx * texels:(gx + 1) * texels]
            if coverage is None:
                block[..., fallback] = 1.0
            else:
                block[...] = coverage
    channels = int(np.ceil(len(weighted) / 4.0)) * 4
    # Widen every transition into a soft band; the shader's fringe noise turns that band into islands and holes.
    # A material may keep a narrower edge (roads): it is softened on its own and laid over the rest.
    softness = float(config.get("edge_softness", 0.0))
    units = 512.0 / texels
    own = {index: float(config["materials"][material]["edge_softness"])
           for index, material in enumerate(weighted)
           if "edge_softness" in config["materials"][material]
           and float(config["materials"][material]["edge_softness"]) < softness}
    crisp = {index: (ndimage.gaussian_filter(field[..., index], value / units, mode="nearest") if value > 0.0
                     else field[..., index].copy()) for index, value in own.items()}
    for index in own:
        field[..., index] = 0.0
    if softness > 0.0:
        field = np.stack([ndimage.gaussian_filter(field[..., c], softness / units, mode="nearest")
                          for c in range(field.shape[-1])], axis=-1)
    field /= np.maximum(field.sum(axis=-1, keepdims=True), 1e-6)
    for index, weight in crisp.items():
        field *= (1.0 - weight)[..., None]
        field[..., index] += weight
    shore_file = None
    if shore:
        # Sand under the water and along the beach, with the waterline exactly where the shore tiles put it.
        distance = shore_distance(water, texels)
        # The smoothed waterline rounds off the floors' corners; the ground stays under them all the same.
        distance[floors] = np.minimum(distance[floors], -512.0 / texels)
        sand = 1.0 - np.clip(distance / float(shore["beach_width"]), 0.0, 1.0) ** 0.75
        if floors.any():
            # A water face's floor ends where the face ends, maybe on land (D3's spring pool): the sand under it
            # blends out over the edge softness, not in a straight line along the face's edge (F11, 2026-11-21).
            sand = np.maximum(sand, ndimage.gaussian_filter(floors.astype(np.float64), max(softness, units) / units,
                                                            mode="nearest"))
        slot_of_all = weighted.index(shore["material"])
        field *= (1.0 - sand)[..., None]
        field[..., slot_of_all] += sand
        field /= np.maximum(field.sum(axis=-1, keepdims=True), 1e-6)
        shore_range = float(shore.get("range", 1024))
        encoded = np.clip(128.0 + distance / shore_range * 127.0 + 0.5, 0, 255).astype(np.uint8)
        shore_file = f"{Path(map_name).stem}_shore.png"
        Image.fromarray(encoded, "L").save(directory / shore_file, optimize=True)
    check_field(field, map_name)
    field = np.concatenate([field, np.zeros((size, size, channels - len(weighted)))], axis=-1)
    quantized = np.clip(field * 255.0 + 0.5, 0, 255).astype(np.uint8)
    stem = Path(map_name).stem
    files = []
    for index in range(channels // 4):
        file_name = f"{stem}_weights{index}.png"
        Image.fromarray(quantized[..., index * 4:index * 4 + 4], "RGBA").save(directory / file_name, optimize=True)
        files.append(file_name)
    entries = []
    cliff_mean = np.array(library[config["materials"][slope["material"]]["library"]]["mean_color"]) if slope else None
    for material in layers:
        entry = config["materials"][material]
        mean = np.array(library[entry["library"]]["mean_color"])
        if material in variant_parent:
            # A variant keeps its own tones under its parent's tint: lighter, mossier patches in the same palette.
            parent = variant_parent[material]
            tint = display[parent] / np.maximum(np.array(library[config["materials"][parent]["library"]]
                                                         ["mean_color"]), 1e-3)
            tint = tint * np.array(config["materials"][parent].get("shade", [1.0, 1.0, 1.0]))
        else:
            tint = display[material] / np.maximum(mean, 1e-3)
        tint = tint * np.array(entry.get("tint_scale", [1.0, 1.0, 1.0]))
        tint = tint * np.array(entry.get("shade", [1.0, 1.0, 1.0]))
        extra = {}
        if slope and material in weighted:
            # Cliffs take the colour of the ground they break through (cliff_from, default the layer itself).
            source = display[entry.get("cliff_from", material)]
            extra["cliff_tint"] = [round(float(v), 4) for v in np.clip(source / np.maximum(cliff_mean, 1e-3), 0, 4)]
        entries.append({
            "name": material,
            "library": entry["library"],
            "tint": [round(float(value), 4) for value in np.clip(tint, 0.0, 4.0)],
            "repeat": entry["repeat"],
            "height_contrast": entry.get("height_contrast", 0.35),
            "normal_strength": entry.get("normal_strength", 1.0),
            "cavity": entry.get("cavity", 0.0),
            "macro_brightness": entry.get("macro_brightness", 0.15),
            "macro_tint": entry.get("macro_tint", [1.0, 1.0, 1.0]),
            "fringe": entry.get("fringe", 1.0),
            **({"meadow": entry["meadow"]} if entry.get("meadow") else {}),
            **({"pools": True} if library[entry["library"]].get("pools") else {}),
            **({"variant": layers.index(entry["variant"]), "variant_amount": entry.get("variant_amount", 0.4)}
               if entry.get("variant") else {}),
            **extra,
        })
    slot_file = {"version": 1, "texels_per_cell": texels, "weights": files, "weighted_layers": len(weighted),
                 "fringe": config.get("fringe", {"strength": 0.0, "scale": 2048.0}),
                 "layers": entries}
    if "continuous_bank_projection" in config:
        slot_file["continuous_bank_projection"] = config["continuous_bank_projection"]
    if config.get("meadow"):
        slot_file["meadow"] = config["meadow"]
    if slope:
        slot_file["slope"] = {"layer": layers.index(slope["material"]), "start": slope["start"],
                              "end": slope["end"]}
    if shore_file:
        slot_file["shore"] = {"file": shore_file, "range": float(shore.get("range", 1024)),
                              "beach_slope": float(shore.get("beach_slope", 0.3)),
                              "seabed_slope": float(shore.get("seabed_slope", 0.5)),
                              "seabed_depth": float(shore.get("seabed_depth", 160)),
                              "opaque_depth": float(shore.get("opaque_depth", 72)),
                              "detail_depth": float(shore.get("detail_depth", 24)),
                              "layer": layers.index(shore["material"])}
    write_yaml(directory / f"{stem}.yml", slot_file,
               f"# Generated by tools/terrain_materials.py weights --world {world} --map {map_name}; edit world.yml.\n"
               "# weights: RGBA images covering the 128x128 cell map, channels in layer order (north row first).\n"
               "# shore: signed distance to the waterline, 128 + distance / range * 127 (positive on land).\n")
    print(f"{map_name}: {len(used)} tiles, layers {layers}, weights {files}")
    written = plants(world, map_name)
    if written:
        print(f"{map_name}: plants {written.relative_to(ASSETS)}")
    if preview:
        colors = np.array([display[m] for m in weighted] + [[0, 0, 0]] * (channels - len(weighted)))
        image_rgb = field @ colors
        Image.fromarray(np.clip(image_rgb * 255.0 + 0.5, 0, 255).astype(np.uint8), "RGB").save(preview)


PLANT_RULE_KEYS = ("family", "density", "tint", "candidates", "width", "height", "wind_strength", "full_footprint")
PLANT_SETTINGS = ("near_distance", "far_distance", "stone_distance", "lod_max_scale", "foliage_tint",
                  "minimum_normal_z", "density_variation", "patch_size", "tall_grass_chance", "tall_grass_scale")


def plants(world, map_name, texels=None):
    """The map's ground plants (worlds/<world>/terrain_decorations/<map>.yml, level_generation/terrain/MEADOW.md) from
    the world's plants.yml beside it: what grows on each ground material, per map. Each tile of the map grows the
    plants of its material (world.yml `tiles`, with the map's own rules); a transition tile grows each part's plants
    under a coverage mask of that part (masks/<tile>_<material>.png), split as the weights split it, so the plants
    stand where their ground is drawn. A world without plants.yml is left alone. Returns the file written, or None.

    plants.yml: `families_file` (a worlds/ or engine/ path, or a file beside it), `settings` (map file keys such as
    near_distance, tall_grass_chance), `materials` ({material: {family, density, tint, ...}}; unlisted materials stay
    bare) and `maps` ({<map>.odm: {enabled: false, reason}, or settings and materials that replace the world's}).
    A grass rule's tint is multiplied by the map's shade of that material (world.yml maps.<map>.<material>.shade),
    so the short mats keep the colour of the ground under them (MEADOW.md)."""
    directory = ASSETS / "worlds" / world / "terrain_decorations"
    source = directory / "plants.yml"
    if not source.exists():
        return None
    spec = load_yaml(source)
    stem = Path(map_name).stem
    own = (spec.get("maps") or {}).get(map_name, {})
    header = (f"# Generated by tools/terrain_materials.py plants --world {world} --map {map_name} (also by weights);\n"
              "# edit plants.yml beside it, never this file.\n")
    if own.get("enabled") is False:
        write_yaml(directory / f"{stem}.yml", {"version": 2, "enabled": False, "reason": own.get("reason", "")},
                   header)
        return directory / f"{stem}.yml"
    growth = {**(spec.get("materials") or {}), **(own.get("materials") or {})}
    growth = {material: entry for material, entry in growth.items() if entry}
    settings = {**(spec.get("settings") or {}), **(own.get("settings") or {})}
    unknown = sorted(set(settings) - set(PLANT_SETTINGS))
    if unknown:
        raise SystemExit(f"plants.yml settings has unknown keys: {unknown}")
    seed = int(hashlib.sha1(f"{world}/{stem}".encode()).hexdigest()[:8], 16) % 2147483647
    if map_name.endswith(".blv"):
        # An open-air BLV's ground (its scene's `terrain: {grass: worlds/<world>/terrain_decorations/<stem>_blv.yml}`,
        # devdocs/INDOOR_OPEN_SKY.md): the grass grows at the density of the ground's meadow layers, with the first
        # grass rule's family and tint; one rule per growing material of the ground file oymap wrote.
        ground = load_yaml(ASSETS / "worlds" / world / "terrain_materials" / f"{stem}_blv.yml")
        layers = [layer["name"] for layer in ground["layers"][:ground["weighted_layers"]]]
        rules = [{"texture": material, **{key: entry[key] for key in PLANT_RULE_KEYS if key in entry}}
                 for material, entry in growth.items() if material in layers]
        if not rules:
            raise SystemExit(f"{map_name}: no ground layer of {stem}_blv.yml grows plants in plants.yml")
        written = directory / f"{stem}_blv.yml"
        write_yaml(written, {"version": 2, "families_file": spec["families_file"], "seed": seed, **settings,
                             "rules": rules}, header)
        return written
    config, world_materials = map_config(world, map_name)
    unknown = sorted(set(growth) - set(config["materials"]))
    if unknown:
        raise SystemExit(f"plants.yml names materials world.yml does not have: {unknown}")
    names = map_tiles(world, map_name)
    used = sorted({name for row in names for name in row if name})
    rules_of = {name: matching_rule(config["tiles"], name) for name in used}
    lab = classification_colors(world, config, world_materials, names)
    size = int(spec.get("mask_size", 64))
    (directory / "masks").mkdir(exist_ok=True)
    rules = []
    for name in used:
        tile_rule = rules_of[name]
        if tile_rule.get("water"):
            continue
        parts = [tile_rule["material"]] if "material" in tile_rule else list(tile_rule.get("materials", []))
        coverage = None
        for material in parts:
            entry = growth.get(material)
            if not entry:
                continue
            rule = {"texture": name, **{key: entry[key] for key in PLANT_RULE_KEYS if key in entry}}
            if "tint" in rule:
                shade = np.array(config["materials"][material].get("shade", [1.0, 1.0, 1.0]))
                rule["tint"] = [round(float(value), 4) for value in np.clip(np.array(rule["tint"]) * shade, 0, 2)]
            if len(parts) == 2:
                if coverage is None:
                    coverage = tile_coverage(world, name, tile_rule, {part: index for index, part in enumerate(parts)},
                                             lab, size)
                mask = np.clip(coverage[..., parts.index(material)] * 255.0 + 0.5, 0, 255).astype(np.uint8)
                mask_name = f"masks/{name}_{material}.png"
                path = directory / mask_name
                image_bytes = Image.fromarray(mask, "L")
                if not path.exists() or not np.array_equal(np.asarray(Image.open(path).convert("L")), mask):
                    image_bytes.save(path.with_name(path.name + ".new.png"), optimize=True)
                    path.with_name(path.name + ".new.png").replace(path)
                rule["mask"] = mask_name
            rules.append(rule)
    if not rules:
        write_yaml(directory / f"{stem}.yml",
                   {"version": 2, "enabled": False, "reason": "no ground of this map grows plants (plants.yml)"},
                   header)
        return directory / f"{stem}.yml"
    document = {"version": 2, "families_file": spec["families_file"], "seed": seed, **settings, "rules": rules}
    write_yaml(directory / f"{stem}.yml", document, header)
    return directory / f"{stem}.yml"


def seams(weights_field, hard=0.9):
    """Hard switches between neighbouring weight texels: the strongest layer changes while both texels hold at least
    `hard` of their own layer, so nothing blends across the line. Returns the number of such texel pairs and the
    longest straight run of them (texels) along a row or a column."""
    best = weights_field.argmax(axis=-1)
    strong = weights_field.max(axis=-1) >= hard
    pairs, longest = 0, 0
    for axis in (0, 1):
        a = [slice(None), slice(None)]
        b = [slice(None), slice(None)]
        a[axis], b[axis] = slice(0, -1), slice(1, None)
        switch = (best[tuple(a)] != best[tuple(b)]) & strong[tuple(a)] & strong[tuple(b)]
        pairs += int(switch.sum())
        # A straight run: switches next to each other along the boundary line (across the other axis).
        line = switch if axis == 0 else switch.T
        for row in line:
            if row.any():
                padded = np.concatenate([[0], row.astype(np.int8), [0]])
                edges = np.flatnonzero(np.diff(padded))
                longest = max(longest, int((edges[1::2] - edges[0::2]).max()))
    return pairs, longest


def check(world, maps, max_run):
    """Every slot file of the world (or the named maps): its weights sum to one on every texel and no straight run
    of hard material switches is longer than max_run texels. Non-zero exit on a failure (F11, 2026-11-21)."""
    directory = ASSETS / "worlds" / world / "terrain_materials"
    files = sorted(path for path in directory.glob("*.yml") if path.name != "world.yml")
    if maps:
        wanted = {Path(name).stem for name in maps}
        files = [path for path in files if path.stem in wanted or path.stem.removesuffix("_blv") in wanted]
    failed = 0
    for path in files:
        slot = load_yaml(path)
        if "weights" not in slot:
            continue
        field = np.concatenate([np.asarray(Image.open(directory / name).convert("RGBA"), dtype=np.float64)
                                for name in slot["weights"]], axis=-1) / 255.0
        field = field[..., :int(slot.get("weighted_layers", field.shape[-1]))]
        sums = field.sum(axis=-1)
        empty = int((np.abs(sums - 1.0) > 0.04).sum())
        pairs, longest = seams(field)
        bad = empty > 0 or longest > max_run
        failed += bad
        print(f"{'FAIL' if bad else 'ok  '} {path.stem}: {empty} texels whose weights do not sum to one, "
              f"{pairs} hard switches, longest straight run {longest} texels")
    if failed:
        raise SystemExit(f"{world}: {failed} of {len(files)} maps fail the weight check")


def main():
    global ASSETS, LIBRARY, LIQUIDS
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("ids", nargs="*")
    cook_parser = commands.add_parser("cook")
    cook_parser.add_argument("--profile", choices=sorted(OUTPUT), required=True)
    cook_parser.add_argument("ids", nargs="*")
    cook_parser.add_argument("--force", action="store_true", help="ignore the receipts and cook every texture")
    cook_parser.add_argument("--output", type=Path, help="runtime root to cook into (default assets_dev for desktop)")
    commands.add_parser("macro")
    commands.add_parser("caustics")
    weights_parser = commands.add_parser("weights")
    weights_parser.add_argument("--world", required=True)
    weights_parser.add_argument("--map", required=True)
    weights_parser.add_argument("--texels-per-cell", type=int, default=16)
    weights_parser.add_argument("--preview", type=Path)
    weights_parser.add_argument("--assets", type=Path, help="asset root to read the map from and write into")
    plants_parser = commands.add_parser("plants")
    plants_parser.add_argument("--world", required=True)
    plants_parser.add_argument("--map", required=True)
    plants_parser.add_argument("--assets", type=Path, help="asset root to read the map from and write into")
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--world", required=True)
    check_parser.add_argument("--map", action="append", default=[], help="only these maps (repeatable)")
    check_parser.add_argument("--max-run", type=int, default=4,
                              help="longest straight run of hard switches allowed, in texels (default 4)")
    check_parser.add_argument("--assets", type=Path, help="asset root to read the maps from")
    edges_parser = commands.add_parser("edges")
    edges_parser.add_argument("--world", required=True)
    edges_parser.add_argument("--assets", type=Path, help="asset root to read the maps from and write into")
    args = parser.parse_args()
    if getattr(args, "assets", None) is not None:
        ASSETS = args.assets.resolve()
        LIBRARY = ASSETS / "engine/terrain_materials/library.yml"
        LIQUIDS = ASSETS / "engine/liquids/liquids.yml"
    if args.command == "prepare":
        prepare(args.ids)
    elif args.command == "cook":
        cook(args.profile, args.ids, args.force, args.output)
    elif args.command == "macro":
        macro()
    elif args.command == "caustics":
        caustics()
    elif args.command == "edges":
        edges(args.world)
    elif args.command == "plants":
        written = plants(args.world, args.map)
        print(f"{args.map}: plants {written.relative_to(ASSETS) if written else 'not configured (no plants.yml)'}")
    elif args.command == "check":
        check(args.world, args.map, args.max_run)
    else:
        weights(args.world, args.map, args.texels_per_cell, args.preview)


if __name__ == "__main__":
    main()
