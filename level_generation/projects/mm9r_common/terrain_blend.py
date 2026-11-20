#!/usr/bin/env python3
"""
Terrain materials for an outdoor BLV (devdocs/INDOOR_OPEN_SKY.md "Terrain"): the ground faces of a remade MM9 region
are drawn from blended library ground materials (the outdoor maps' terrain style) instead of MM9's textures, which
MM9 mapped per polygon (the patterns break at a third of the cliff edges) and never blended.

The project's `overrides.yml` names the ground textures by their MM9 file stem and the world material each becomes:

    terrain:
      materials: {ashcliff: cliff_layered, ashrock: grass, ashrock2: grass_patches, nwrock: cliff_layered}
      slope: cliff_layered          # optional: the world's slope material (world.yml `slope`) for this map

This step reads the built BLV, rasterises those faces from above (the topmost face wins: a ledge over a tunnel) into
layer weights over the 65 536-unit map frame, softens every transition over the world's `edge_softness` and writes,
into the review root,

    worlds/<world>/terrain_materials/<map>_blv.yml        the material file (tools/terrain_materials.py's format)
    worlds/<world>/terrain_materials/<map>_blv_weights0.png
    worlds/<world>/maps/<map>.scene.yml                    with `terrain: {materials, textures}`

Each material's tint takes the mean colour of the MM9 textures it replaces (over their faces' area) against the
library material's mean, so the isle keeps MM9's palette; the world's per-map `shade` and `tint_scale` apply on top.
The slope layer (world.yml `slope`, the cliff) also covers every steep face whatever its texture.
A floor-like face with a terrain texture under the terrain (COVER) on a polygon MM9 lightmapped (a tunnel's floor
strip) is no ground: the scene's `terrain: {exclude_faces}` draws it with its texture and lightmap (dungeon/lighting.py
charts it).

    python3 level_generation/projects/mm9r_common/terrain_blend.py <project dir> [--root <review root>]
"""

from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "util"))
import review_root  # noqa: E402
from map_export import parse_blv_file  # noqa: E402

MAP_CELLS = 128
TEXELS_PER_CELL = 16                    # 32 world units a weight texel, as on the outdoor maps
FRAME = 65536.0
LIBRARY = ROOT / "assets_dev/engine/terrain_materials/library.yml"
NATIVES = ROOT / "assets_editor_dev/worlds/mm9/textures"
LUMA = np.array([0.2126, 0.7152, 0.0722])
MAX_CHANNEL_LIFT = 1.0
# A terrain-textured floor this far under the terrain over it at every sample is a tunnel's or a cave's, not the
# ground: the scene's `exclude_faces` draws it as an ordinary face with its lightmap (Isle of Ashes' tunnel floor strips
# of ashdirt3, PhysicsBSP seams under the mountain: the blend took the mountain top's rock and the open sky's daylight,
# user play-test 2026-11-06).
COVER = 128.0
FLOOR_NORMAL_Z = 0.7


def texture_stems(stem: str) -> dict:
    """Alias (lower case) -> MM9 texture file stem (lower case), from the map's material aliases."""
    aliases = yaml.safe_load((ROOT / f"assets_editor_dev/worlds/mm9/maps/{stem}.material_aliases.yml").read_text())
    result = {}
    for entry in aliases.get("textures") or []:
        source = entry.get("source_texture") or ""
        result[entry["alias"].lower()] = Path(source.replace("\\", "/")).stem.lower()
    return result


def face_points(payload: dict, face: dict) -> np.ndarray:
    vertices = payload["vertices"]
    return np.array([[vertices[i]["x"], vertices[i]["y"], vertices[i]["z"]] for i in face["vertex_indices"]], float)


def polygon_area(points: np.ndarray) -> float:
    return float(np.linalg.norm(np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0)) * 0.5)


def rasterise(payload: dict, faces: list, size: int, heights: bool = False):
    """Per weight texel the layer of the topmost terrain face over it (-1: none). faces: [(face, layer)]. With
    heights, also that face's height there (-inf: none)."""
    units = FRAME / size
    layer_map = np.full((size, size), -1, np.int16)
    height = np.full((size, size), -np.inf)
    for face, layer in faces:
        points = face_points(payload, face)
        for index in range(1, len(points) - 1):
            triangle = points[[0, index, index + 1]]
            # Texel space: column from the frame's west edge, row from its north edge.
            column = (triangle[:, 0] + FRAME / 2) / units - 0.5
            row = (FRAME / 2 - triangle[:, 1]) / units - 0.5
            x0, x1 = int(np.floor(column.min())), int(np.ceil(column.max()))
            y0, y1 = int(np.floor(row.min())), int(np.ceil(row.max()))
            x0, y0 = max(x0, 0), max(y0, 0)
            x1, y1 = min(x1, size - 1), min(y1, size - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            (ax, bx, cx), (ay, by, cy) = column, row
            denominator = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(denominator) < 1e-9:
                # Seen edge-on from above (a wall of cliff): its line of texels.
                continue
            wa = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / denominator
            wb = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / denominator
            wc = 1.0 - wa - wb
            inside = (wa >= -1e-6) & (wb >= -1e-6) & (wc >= -1e-6)
            if not inside.any():
                continue
            z = wa * triangle[0, 2] + wb * triangle[1, 2] + wc * triangle[2, 2]
            block = height[y0:y1 + 1, x0:x1 + 1]
            higher = inside & (z > block)
            block[higher] = z[higher]
            layer_map[y0:y1 + 1, x0:x1 + 1][higher] = layer
    return (layer_map, height) if heights else layer_map


def covered_faces(payload: dict, faces: list, size: int) -> list[int]:
    """The floor-like faces of `faces` over the sea surface that lie COVER or more under the topmost of them at their
    centre and at points three quarters of the way out to each vertex."""
    _, height = rasterise(payload, [(face, 0) for face in faces], size, heights=True)
    units = FRAME / size
    result = []
    for face in faces:
        points = face_points(payload, face)
        normal = np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0)
        length = float(np.linalg.norm(normal))
        if length <= 0.0 or abs(normal[2]) / length < FLOOR_NORMAL_Z:
            continue
        centre = points.mean(axis=0)
        if centre[2] <= 0.0:
            # under the sea surface (the frame's z 0): a seabed under the land, the sea's business (dungeon/water.py)
            continue
        samples = np.vstack([centre, centre + (points - centre) * 0.75])
        columns = np.clip(((samples[:, 0] + FRAME / 2) / units).astype(int), 0, size - 1)
        rows = np.clip(((FRAME / 2 - samples[:, 1]) / units).astype(int), 0, size - 1)
        if (height[rows, columns] > samples[:, 2] + COVER).all():
            result.append(int(face["index"]))
    return sorted(result)


def lightmapped_in_mm9(project_dir: Path, payload: dict, face_ids: list[int]) -> list[int]:
    """The faces of face_ids that lie on a floor polygon MM9 lightmapped (a structure's: MM9 lit its terrain per
    vertex), at their centre. Those draw as faces with MM9's lightmap; a covered terrain polygon (Guberland's stacked
    terrain, Sturmford's seabed under the land) stays terrain."""
    if not face_ids:
        return []
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    from dungeon.geometry import poly_ring
    from dungeon.source import Project
    from transcode_mm9_dat_to_odm import read_dat_world
    project = Project.load(project_dir, install=False)
    polygons = []
    for model in read_dat_world(project.dat).world_models:
        for poly in model.polies:
            if not poly.lightmap_pixels_bgra:
                continue
            ring = np.array([model.points[i] for i in poly_ring(poly)], float)
            if len(ring) < 3:
                continue
            normal = np.cross(ring, np.roll(ring, -1, axis=0)).sum(axis=0)
            length = float(np.linalg.norm(normal))
            if length < 1e-6 or abs(normal[1]) / length < FLOOR_NORMAL_Z:
                continue
            polygons.append((ring, normal / length, ring.min(axis=0), ring.max(axis=0)))
    result = []
    for face_id in face_ids:
        centre = project.lt_from_native(face_points(payload, payload["faces"][face_id]).mean(axis=0))
        for ring, normal, low, high in polygons:
            if not (low[0] - 1 <= centre[0] <= high[0] + 1 and low[2] - 1 <= centre[2] <= high[2] + 1) \
                    or abs(float(normal @ (centre - ring[0]))) > 2.0:
                continue
            inside = False
            for (x1, _, z1), (x2, _, z2) in zip(ring, np.roll(ring, -1, axis=0)):
                if (z1 > centre[2]) != (z2 > centre[2]) and \
                        centre[0] < x1 + (centre[2] - z1) / (z2 - z1) * (x2 - x1):
                    inside = not inside
            if inside:
                result.append(face_id)
                break
    return result


def native_mean(alias: str) -> np.ndarray:
    pixels = np.asarray(Image.open(NATIVES / f"{alias.upper()}.bmp").convert("RGB"), float) / 255.0
    return pixels.reshape(-1, 3).mean(axis=0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--root", type=Path, help="review root (default: the shared review root)")
    args = parser.parse_args()
    if args.root:
        review_root.ASSETS = args.root.resolve()
        review_root.OWNED = args.root.resolve().parent / f"{args.root.resolve().name.removesuffix('_root')}_owned.txt"
    print(install(args.project.resolve()))
    return 0


DEFAULT_GRASS = "worlds/mm6/terrain_decorations/oute3.yml"
# The short grass's tint per region, fitted by grass_tint.py (missing: New Sorpigal's).
GRASS_TINTS = HERE / "grass_tints.yml"


def region_grass(stem: str) -> str:
    """Writes New Sorpigal's grass settings for this region (level_generation/terrain/MEADOW.md, GRASS_LOD.md):
    DEFAULT_GRASS's density, patches, LOD and first rule with its plant library (the families file by its virtual
    path), the rule's tint the region's fitted one (grass_tint.py: the short mats match the ground under them, as on
    New Sorpigal; mats that do not match read as dashes, on MM9's grounds as rows of small bushes). Returns its
    virtual path."""
    source = yaml.safe_load((ROOT / "assets_dev" / DEFAULT_GRASS).read_text())
    tints = (yaml.safe_load(GRASS_TINTS.read_text()) if GRASS_TINTS.exists() else None) or {}
    rule = {key: value for key, value in source["rules"][0].items() if key != "mask"}
    if stem in tints:
        rule["tint"] = tints[stem]
    config = {key: value for key, value in source.items() if key not in ("rules", "families_file")}
    config["families_file"] = (Path(DEFAULT_GRASS).parent / source["families_file"]).as_posix()
    config["rules"] = [rule]
    path = Path(f"worlds/mm9/terrain_decorations/{stem}_blv.yml")
    header = (f"# Written by level_generation/projects/mm9r_common/terrain_blend.py: New Sorpigal's grass\n"
              f"# ({DEFAULT_GRASS}) for {stem}.blv, its tint fitted to the region's ground (grass_tint.py).\n")
    review_root.install(path, (header + yaml.safe_dump(config, sort_keys=False, width=120)).encode())
    return path.as_posix()


def install(project: Path) -> str:
    """Writes the project's terrain into the current review root (review_root.ASSETS, after its build installed the
    map); returns a one-line summary. A project without `terrain` in overrides.yml is left as it is."""
    overrides = yaml.safe_load((project / "overrides.yml").read_text())
    stem = overrides["map"]["stem"] if "stem" in (overrides.get("map") or {}) else project.name.removeprefix(
        "mm9r_").removesuffix("_blv")
    if not overrides.get("terrain"):
        return "terrain: none (overrides.yml has no terrain block)"
    wanted = {name.lower(): material for name, material in overrides["terrain"]["materials"].items()}
    # The world's per-map shades and tint scales match MM8's reference tiles to MM9; the tints here come from MM9's
    # own textures, so only a variant's tint scale (its tone against its parent) applies.
    world = yaml.safe_load((HERE / "terrain_materials_world.yml").read_text())
    if overrides["terrain"].get("slope"):
        world["slope"] = {**world["slope"], "material": overrides["terrain"]["slope"]}
    library = yaml.safe_load(LIBRARY.read_text())["materials"]

    payload = parse_blv_file(review_root.ASSETS / f"worlds/mm9/maps/{stem}.blv")["payload"]
    stems = texture_stems(stem)
    size = MAP_CELLS * TEXELS_PER_CELL
    ground = [face for face in payload["faces"]
              if wanted.get(stems.get((face.get("texture_name") or "").strip().lower(), "")) is not None
              and not face.get("is_portal") and len(face["vertex_indices"]) >= 3]
    excluded = lightmapped_in_mm9(project, payload, covered_faces(payload, ground, size))
    excluded_set = set(excluded)
    weighted = []
    faces = []
    area = {}
    colour = {}
    textures = set()
    for face in payload["faces"]:
        alias = (face.get("texture_name") or "").strip().lower()
        material = wanted.get(stems.get(alias, ""))
        if material is None or face.get("is_portal") or len(face["vertex_indices"]) < 3 \
                or face["index"] in excluded_set:
            continue
        if material not in weighted:
            weighted.append(material)
        faces.append((face, weighted.index(material)))
        textures.add(alias)
        face_area = polygon_area(face_points(payload, face))
        area[material] = area.get(material, 0.0) + face_area
        if alias not in colour:
            colour[alias] = native_mean(alias)
        colour.setdefault(material + "#sum", np.zeros(3))
        colour[material + "#sum"] = colour[material + "#sum"] + colour[alias] * face_area
    if not faces:
        raise SystemExit("no face carries a terrain texture of overrides.yml terrain.materials")
    if len(weighted) > 4:
        raise SystemExit(f"{len(weighted)} weighted terrain materials; one weight image holds 4")
    display = {material: colour[material + "#sum"] / area[material] for material in weighted}

    layers = list(weighted)
    slope = world.get("slope")
    if slope and slope["material"] not in layers:
        layers.append(slope["material"])
    for material in list(layers):
        variant = world["materials"][material].get("variant")
        if variant and variant not in layers:
            layers.append(variant)
    if len(layers) > 8:
        raise SystemExit(f"{len(layers)} terrain material layers; at most 8")

    layer_map = rasterise(payload, faces, size)
    # Texels no terrain face covers take their nearest layer, so the blur never pulls the ground towards nothing.
    empty = layer_map < 0
    if empty.any():
        _, nearest = ndimage.distance_transform_edt(empty, return_indices=True)
        layer_map = layer_map[nearest[0], nearest[1]]
    field = np.stack([(layer_map == index).astype(np.float32) for index in range(len(weighted))], axis=-1)
    softness = float(world.get("edge_softness", 0.0))
    units = FRAME / size
    if softness > 0.0:
        field = np.stack([ndimage.gaussian_filter(field[..., c], softness / units, mode="nearest")
                          for c in range(field.shape[-1])], axis=-1)
    field /= np.maximum(field.sum(axis=-1, keepdims=True), 1e-6)
    field = np.concatenate([field, np.zeros((size, size, 4 - len(weighted)), np.float32)], axis=-1)
    quantized = np.clip(field * 255.0 + 0.5, 0, 255).astype(np.uint8)

    name = f"{stem}_blv"
    directory = Path("worlds/mm9/terrain_materials")
    weights_file = f"{name}_weights0.png"
    buffer = BytesIO()
    Image.fromarray(quantized, "RGBA").save(buffer, format="PNG", optimize=True)
    review_root.install(directory / weights_file, buffer.getvalue())

    variant_parent = {entry["variant"]: parent for parent, entry in world["materials"].items()
                      if entry.get("variant") in layers and parent in layers}
    slope_material = slope["material"] if slope else None
    cliff_mean = np.array(library[world["materials"][slope_material]["library"]]["mean_color"]) if slope else None
    entries = []
    for material in layers:
        entry = world["materials"][material]
        mean = np.array(library[entry["library"]]["mean_color"])
        if material in display:
            tint = display[material] / np.maximum(mean, 1e-3)
            # No channel may rise over the brightness ratio: per-channel tints cannot desaturate, and
            # pushing blue into a saturated library green to reach MM9's grey olive turns its soil texels lilac.
            luminance = float(LUMA @ display[material]) / max(float(LUMA @ mean), 1e-3)
            tint = np.minimum(tint, luminance * MAX_CHANNEL_LIFT)
        elif material in variant_parent:
            # A variant keeps its own tones under its parent's tint (tools/terrain_materials.py).
            parent = variant_parent[material]
            parent_mean = np.array(library[world["materials"][parent]["library"]]["mean_color"])
            tint = display.get(parent, parent_mean) / np.maximum(parent_mean, 1e-3)
            tint = tint * np.array(entry.get("tint_scale", [1.0, 1.0, 1.0]))
        else:
            tint = np.ones(3)
        extra = {}
        if slope and material in weighted:
            # Steep ground of every layer takes MM9's cliff colour (the cliff texture's own mean when it is mapped).
            source = display.get(slope_material, display[material])
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
            **({"variant": layers.index(entry["variant"]), "variant_amount": entry.get("variant_amount", 0.4)}
               if entry.get("variant") else {}),
            **extra,
        })
    config = {"version": 1, "texels_per_cell": TEXELS_PER_CELL, "weights": [weights_file],
              "weighted_layers": len(weighted), "fringe": world.get("fringe", {"strength": 0.0, "scale": 2048.0}),
              "layers": entries}
    if world.get("meadow"):
        config["meadow"] = world["meadow"]
    if slope:
        config["slope"] = {"layer": layers.index(slope_material), "start": slope["start"], "end": slope["end"]}
    header = (f"# Written by level_generation/projects/mm9r_common/terrain_blend.py for {stem}.blv's terrain faces\n"
              f"# ({', '.join(sorted(textures))}).\n")
    review_root.install(directory / f"{name}.yml",
                        (header + yaml.safe_dump(config, sort_keys=False, width=120)).encode())

    scene_path = Path(f"worlds/mm9/maps/{stem}.scene.yml")
    scene = json.loads((review_root.ASSETS / scene_path).read_text())
    scene["terrain"] = {"materials": f"{name}.yml", "textures": sorted(textures)}
    if excluded:
        scene["terrain"]["exclude_faces"] = excluded
    # Grass tufts over the grass layers (devdocs/INDOOR_OPEN_SKY.md "Terrain"): New Sorpigal's meadow by default
    # (region_grass), `terrain: {grass: <decoration file path> | none}` in overrides.yml to choose or leave them out
    # (whatever the player's terrain decoration setting). Without the default, its generated file goes.
    grass = overrides["terrain"].get("grass") or region_grass(stem)
    if grass != "none":
        scene["terrain"]["grass"] = grass
    generated = f"worlds/mm9/terrain_decorations/{stem}_blv.yml"
    if overrides["terrain"].get("grass") and grass != generated:
        review_root.remove(generated)
    review_root.install(scene_path, (json.dumps(scene, indent=1) + "\n").encode())
    return (f"terrain: {len(faces)} faces, {len(textures)} textures -> layers {layers}; "
            f"{len(excluded)} under the terrain drawn as faces {excluded[:12]}{' ...' if len(excluded) > 12 else ''}")


if __name__ == "__main__":
    sys.exit(main())
