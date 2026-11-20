"""
Baked indoor lighting of a built dungeon (devdocs/INDOOR_BAKED_LIGHTING.md): tools/lighting/bake_indoor.py with the
map's profile (tools/lighting/baked_indoors/profiles/mm9_<stem>.yml), passes in output/mm9_rework/bakes/<stem>, the
sidecar pair installed through review_root.install(). The bake belongs to the BLV it was made from: bake again after
every convert.py that changes the map (the game ignores a stale bake and logs it).

Bake-only lights: the map's MM9 lights that the converter left out of the BLV because a floor point was already under
four (work/lights.json, reason "a floor point already under four lights": the large fill lights) light the bake, which
has no such cap (`--extra-lights`); they reach neither the runtime's vertex light nor the actors' light grid. The
profile's `emitters` add MM9's sky faces and outward window panes as area lights.

Directional lights: a profile with `dirlights: true` adds MM9's DirLight objects as bake-only spot lights: position,
radius and colour × BrightScale as authored, aim from `Rotation`, `FOV` the full cone angle, with the profile of MM9's
preprocessor (tools/PreProcessor/LightMapMaker.cpp CalcLightSample: the quartic window times a linear cone term). Off
by default: a map's calibration changes with them.

Texture lights: a DTX with a `LIGHTDEFS` section (`center x y radius r g b`) has MM9's preprocessor attach a light to
every surface using the texture (devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md finding 1: the Lich Lab's teal pod and
crown glass, YANMIRSOLIDICE1). Each built model (brush) with such a texture adds one bake-only point light of that
colour and radius at the centre of its polygons with it. A profile's `texture_lights: {per_polygon: true, scale: s,
offset_lt: d}` adds one per polygon instead, `d` LT in front of it at `s` of full strength: closer to MM9, whose lights
sit on the surfaces, and needed where a brush's centre is shut in (the Lich Lab's sealed pods: a centre light never gets
out, s 0.18 is the fit to MM9's lightmaps).

    python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_<map> \
        [--samples N] [--recompose] [--no-install] [--remove]
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_root  # noqa: E402
from dungeon.source import ROOT  # noqa: E402

CAPPED = "a floor point already under four lights"
# The map lights' strength in the static light (IndoorBakedStaticLightAlpha, 224 / 255).
LIGHT_ALPHA = 224 / 255


def project_stem(directory: Path) -> str:
    """The map stem: overrides.yml `map.stem` (maps on the shared converter), else the project's name (Anskram)."""
    overrides = yaml.safe_load((directory / "overrides.yml").read_text()) or {}
    return (overrides.get("map") or {}).get("stem") or directory.name.removeprefix("mm9r_")


def write_extra_lights(directory: Path, path: Path) -> int:
    """The lights the converter dropped over the runtime's four-per-point cap, as bake-only point lights. The BLV
    lights carry no BrightScale (the profile's direct_scale stands for their typical one); MM9 authors its big fill
    lights much dimmer (Anskram's Light6 at 0.3), so a bake-only light's strength is its BrightScale relative to the
    median of the map's kept lights, at most the full strength."""
    lights = json.loads((directory / "work/lights.json").read_text())
    kept = sorted(light.get("bright_scale", 1.0) for light in lights if light["kept"])
    typical = kept[len(kept) // 2] if kept else 1.0
    extra = [{"name": light["name"], "position": light["position"], "radius": light["radius"],
              "color": light["colour"],
              "alpha": LIGHT_ALPHA * min(1.0, light.get("bright_scale", 1.0) / typical)}
             for light in lights if not light["kept"] and light.get("reason") == CAPPED]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(extra, indent=1) + "\n")
    return len(extra)


def lt_forward(rotation) -> list[float]:
    """The LithTech unit vector an object with Euler (pitch, yaw, roll) points along (gr_SetupMatrixEuler's third
    basis vector), in LithTech coordinates."""
    pitch, yaw = float(rotation[0]), float(rotation[1])
    return [math.cos(pitch) * math.sin(yaw), -math.sin(pitch), math.cos(pitch) * math.cos(yaw)]


def write_dirlights(directory: Path) -> list[dict]:
    """MM9's DirLights as bake-only spot lights. Strength as write_extra_lights: BrightScale relative to the map's
    typical kept light, at most full."""
    from dungeon.source import SCALE, Project, Source, lt_vector_to_native
    project = Project.load(directory, install=False)
    lights = json.loads((directory / "work/lights.json").read_text())
    kept = sorted(light.get("bright_scale", 1.0) for light in lights if light["kept"])
    typical = kept[len(kept) // 2] if kept else 1.0
    result = []
    for entry in Source(project).objects:
        if entry["class"] != "DirLight":
            continue
        p = entry["properties"]
        bright = float(p.get("BrightScale", 1.0))
        if bright <= 0.0:
            continue
        result.append({"name": f"dirlight:{entry['name']}",
                       "position": [int(round(v)) for v in project.native(p["Pos"])],
                       "radius": int(round(float(p.get("LightRadius", 300)) * SCALE)),
                       "color": [int(round(c)) for c in p.get("InnerColor", [255, 255, 255])],
                       "alpha": LIGHT_ALPHA * min(1.0, bright / typical),
                       "direction": [round(float(v), 5) for v in lt_vector_to_native(lt_forward(p["Rotation"]))],
                       "fov": float(p.get("FOV", 90.0))})
    return result


def texture_lights(dtx: Path) -> list[tuple]:
    """A DTX's LIGHTDEFS `center` lights: (radius LT, (r, g, b)) each; [] without the section."""
    data = dtx.read_bytes()
    found = data.find(b"LIGHTDEFS")
    if found < 0:
        return []
    lights = []
    # The section's name, lengths, then its text (`center ...`, lines or `;`-separated).
    text = data[found + 9:found + 1024].decode("latin-1")
    for line in text.replace("\0", "\n").replace(";", "\n").splitlines():
        words = line.split()
        if len(words) >= 7 and words[0].lower() == "center":
            lights.append((float(words[3]), tuple(int(float(v)) for v in words[4:7])))
    return lights


def write_texture_lights(directory: Path, settings: dict | None = None) -> list[dict]:
    """Bake-only point lights for the LIGHTDEFS textures of the map's built models (static and movers), one per brush,
    or one per polygon with the profile's `texture_lights` (`settings`)."""
    from dungeon.source import SCALE, Project, Source, classify_models
    project = Project.load(directory, install=False)
    source = Source(project)
    plan = classify_models(source)
    lights_by_texture, centres, result = {}, {}, []
    for model in list(plan["static"]) + sorted(plan["movers"]):
        for polygon in source.polygons(model):
            texture = polygon.texture.lower()
            if texture not in lights_by_texture:
                alias = source.aliases.get(texture) or {}
                dtx = ROOT / alias["physical_path"] if alias.get("physical_path") else None
                lights_by_texture[texture] = texture_lights(dtx) if dtx and dtx.exists() else []
            if lights_by_texture[texture]:
                centres.setdefault((model, texture), []).append(polygon)
    if settings and settings.get("per_polygon"):
        offset, scale = float(settings.get("offset_lt", 8.0)), float(settings.get("scale", 1.0))
        for (model, texture), polygons in centres.items():
            for index, polygon in enumerate(polygons):
                centre = project.native(polygon.points.mean(0) + polygon.normal * offset)
                for radius, colour in lights_by_texture[texture]:
                    result.append({"name": f"lightdefs:{Path(texture.replace(chr(92), '/')).stem}:{model}:{index}",
                                   "position": [int(round(v)) for v in centre],
                                   "radius": int(round(radius * SCALE)), "color": list(colour),
                                   "alpha": LIGHT_ALPHA * scale})
        return result
    for (model, texture), polygons in centres.items():
        points = [polygon.points.mean(0) for polygon in polygons]
        centre = project.native(np.mean(points, axis=0))
        for radius, colour in lights_by_texture[texture]:
            result.append({"name": f"lightdefs:{Path(texture.replace(chr(92), '/')).stem}:{model}",
                           "position": [int(round(v)) for v in centre], "radius": int(round(radius * SCALE)),
                           "color": list(colour), "alpha": LIGHT_ALPHA})
    return result


def mm9_texel_units(directory: Path) -> float:
    """Half MM9's lightmap grid (its WorldInfo LMGridSize, LT) in native units: two of our texels per MM9 texel keep
    its light (sampled bilinearly), at a small fraction of the Cycles bakes' 16-unit texels."""
    from dungeon.source import SCALE
    from transcode_mm9_dat_to_odm import read_dat_world
    overrides = yaml.safe_load((directory / "overrides.yml").read_text()) or {}
    settings = overrides.get("map") or {}
    stem = project_stem(directory)
    world = read_dat_world(ROOT / "mm9/extracted/WORLDS/WORLDS" / settings.get("dat", f"{stem.upper()}.dat"))
    return round(float(world.world_info.light_map_grid_size) * SCALE / 2.0, 2)


def main(directory: Path, argv=None) -> int:
    parser = argparse.ArgumentParser(description="bake the map's indoor lighting")
    parser.add_argument("--samples", type=int)
    parser.add_argument("--recompose", action="store_true")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--remove", action="store_true", help="remove the installed bake from the review root")
    parser.add_argument("--no-extra-lights", action="store_true", help="bake the BLV's own lights only")
    parser.add_argument("--layout-only", action="store_true",
                        help="no render: charts at half MM9's lightmap grid with flat pages, the base of "
                             "lightmap_transfer.py (seconds, not the Cycles bake's tens of minutes)")
    parser.add_argument("--root", type=Path,
                        help="the review root holding the map (default: output/mm9_rework/assets_dev; the outdoor "
                             "BLVs: output/mm9_rework/isleofashes_blv_root)")
    args = parser.parse_args(argv)
    if args.root is not None:
        review_root.ASSETS = args.root.resolve()
        if review_root.ASSETS.name == "isleofashes_blv_root":
            review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"
    stem = project_stem(directory)
    files = [f"{stem}.lighting", f"{stem}.bake.json"]
    maps = "worlds/mm9/maps"
    if args.remove:
        for name in files:
            review_root.remove(f"{maps}/{name}")
        print("removed", ", ".join(files))
        return 0
    profile = ROOT / f"tools/lighting/baked_indoors/profiles/mm9_{stem}.yml"
    output = ROOT / f"output/mm9_rework/bakes/{stem}"
    if args.layout_only and list(output.glob("page_*_direct.npy")):
        # a Cycles bake's passes stay, beside the layout (bakes/<stem>_cycles: --recompose there restores it)
        kept = output.parent / f"{stem}_cycles"
        if kept.exists():
            raise SystemExit(f"{kept} exists: move or remove it before a layout-only run")
        output.rename(kept)
        print("Cycles bake kept in", kept)
    if args.layout_only and not profile.exists():
        # a map without a Cycles profile (the cities, the regions): the layout needs only its name
        output.mkdir(parents=True, exist_ok=True)
        profile = output.parent / f"{stem}_layout_profile.json"
        profile.write_text(json.dumps({"world": "mm9", "map": f"{stem}.blv", "page_size": 4096}) + "\n")
    command = ["blender", "--background", "--factory-startup", "--python-exit-code", "1",
               "--python", str(ROOT / "tools/lighting/bake_indoor.py"), "--",
               "--profile", str(profile), "--output", str(output), "--assets", str(review_root.ASSETS)]
    if args.samples:
        command += ["--samples", str(args.samples)]
    if args.layout_only:
        command += ["--layout-only", "--units-per-texel", f"{mm9_texel_units(directory):g}"]
        # the terrain draws with its materials under the daylight, never its lightmap: no charts for it
        scene_file = review_root.ASSETS / f"{maps}/{stem}.scene.yml"
        terrain = (yaml.load(scene_file.read_text(), Loader=yaml.CSafeLoader) or {}).get("terrain") \
            if scene_file.exists() else None
        if terrain and terrain.get("textures"):
            command += ["--skip-textures", ",".join(terrain["textures"])]
            # terrain-textured faces drawn as ordinary faces (terrain_blend.py: under the terrain) take MM9's lightmap
            if terrain.get("exclude_faces"):
                command += ["--keep-faces", ",".join(str(f) for f in terrain["exclude_faces"])]
    elif args.recompose:
        command.append("--recompose")
    elif not args.no_extra_lights:
        extra = output.parent / f"{stem}_extra_lights.json"
        print("extra lights", write_extra_lights(directory, extra))
        if (directory / "overrides.yml").exists() and "map" in (yaml.safe_load((directory / "overrides.yml")
                                                                                .read_text()) or {}):
            texture = write_texture_lights(directory, json.loads(profile.read_text()).get("texture_lights"))
            print("texture (LIGHTDEFS) lights", len(texture))
            extra.write_text(json.dumps(json.loads(extra.read_text()) + texture, indent=1) + "\n")
            if json.loads(profile.read_text()).get("dirlights"):
                directional = write_dirlights(directory)
                print("directional lights", len(directional))
                extra.write_text(json.dumps(json.loads(extra.read_text()) + directional, indent=1) + "\n")
        command += ["--extra-lights", str(extra)]
    subprocess.run(command, check=True, cwd=ROOT)
    if not args.no_install:
        for name in files:
            print("installed", review_root.install_file(f"{maps}/{name}", output / name))
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve(), sys.argv[2:]))
