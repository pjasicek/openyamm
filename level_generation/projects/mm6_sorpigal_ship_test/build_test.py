#!/usr/bin/env python3
"""Build an isolated New Sorpigal ship test using the native reader/writer."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from PIL import Image
import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
BUILD = PROJECT / "build"
PLAYTEST = PROJECT / "playtest"
ASSETS = PLAYTEST / "assets_dev"
sys.path.insert(0, str(ROOT / "util"))
from map_export import parse_odm_file


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy(source, destination):
    """Replace the test entry, never write through a shared hard link."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".ship-tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--install-lighting", action="store_true")
    action.add_argument("--package", action="store_true", help="Archive only the 28 changed map/texture files")
    args = parser.parse_args()
    config = json.loads((PROJECT / "source/ship.json").read_text())
    base = ROOT / config["base_map"]
    donor = ROOT / config["donor_map"]
    for path, expected in [(base, config["base_sha256"]), (donor, config["donor_sha256"]),
                           (base.with_suffix(".scene.yml"), config["base_scene_sha256"])]:
        if digest(path) != expected:
            raise RuntimeError("Pinned source changed; review the source manifest before rebuilding: " + str(path))
    target_maps = ASSETS / "worlds/mm6/maps"
    if args.install_lighting:
        for name in ("oute3.lighting", "oute3.bake.json"):
            atomic_copy(PROJECT / "bake" / name, target_maps / name)
        print("Installed isolated lighting/recipe pair.")
        return
    if args.package:
        report = json.loads((BUILD / "report.json").read_text())
        assert digest(target_maps / "oute3.odm") == report["geometry_sha256"]
        assert digest(target_maps / "oute3.scene.yml") == report["scene_sha256"]
        files = [target_maps / name for name in ("oute3.odm", "oute3.scene.yml", "oute3.lighting", "oute3.bake.json")]
        for texture in report["textures"]:
            files.append(ASSETS / "worlds/mm6/textures" / (texture["target"] + ".bmp"))
            files.append(ASSETS / "worlds/mm6/textures_x2" / (texture["target"] + ".png"))
        package = BUILD / "ship_overlay.zip"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                archive.write(path, path.relative_to(ASSETS))
        with zipfile.ZipFile(package) as archive:
            assert archive.testzip() is None
        manifest = {"package": package.name, "sha256": digest(package),
                    "files": [{"path": str(path.relative_to(ASSETS)), "sha256": digest(path),
                               "bytes": path.stat().st_size} for path in files]}
        (BUILD / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(json.dumps({"package": str(package), "files": len(files), "bytes": package.stat().st_size}))
        return

    BUILD.mkdir(parents=True, exist_ok=True)
    compiler = BUILD / "port_ship"
    subprocess.run(["c++", "-std=c++20", "-O2", "-I", str(ROOT),
                    str(PROJECT / "source/port_ship.cpp"), str(ROOT / "game/outdoor/OutdoorMapData.cpp"),
                    "-o", str(compiler)], check=True)
    original = parse_odm_file(base)["payload"]
    source = parse_odm_file(donor)["payload"]
    texture_names = sorted({f["texture_name"].lower() for i in config["donor_models"]
                            for f in source["bmodels"][i]["faces"]})
    remap = {name: "ns8s" + str(i).zfill(2) for i, name in enumerate(texture_names)}
    remap_path = BUILD / "textures.tsv"
    remap_path.write_text("".join(a + "\t" + b + "\n" for a, b in remap.items()))
    suppressed_path = BUILD / "suppressed_faces.tsv"
    suppressed_path.write_text("".join(f"{model}\t{face}\n" for model, face in config["suppressed_coplanar_faces"]))
    doors_path = BUILD / "door_faces.tsv"
    doors_path.write_text("".join(f"{model}\t{face}\n" for model, face in config["door_faces"]))
    result = subprocess.check_output([str(compiler), str(base), str(donor), str(BUILD / "oute3.odm"),
                                      str(remap_path), *map(str, config["position"]), str(suppressed_path),
                                      str(doors_path)], text=True)
    report = json.loads(result)
    compiled = parse_odm_file(BUILD / "oute3.odm")["payload"]
    for key in ("height_map", "tile_map", "attribute_map", "some_other_map", "normal_map", "normals", "spawns"):
        assert compiled[key] == original[key], key
    for before, after in zip(original["bmodels"], compiled["bmodels"]):
        assert before["vertices"] == after["vertices"]
        for a, b in zip(before["faces"], after["faces"]):
            for key in ("vertex_indices", "texture_us", "texture_vs", "texture_name", "attributes",
                        "texture_delta_u", "texture_delta_v", "cog_number", "cog_triggered_number", "cog_trigger"):
                assert a[key] == b[key], (before["index"], a["index"], key)
            assert base64.b64decode(a["raw_record_base64"])[:16] == base64.b64decode(b["raw_record_base64"])[:16]
    for a, b in zip(original["entities"], compiled["entities"]):
        if a["index"] != config["retired_decoration"]:
            assert a == b, ("decoration", a["index"])
    door_faces = {(len(original["bmodels"]) + config["donor_models"].index(model), face)
                  for model, face in config["door_faces"]}
    for model in compiled["bmodels"][report["bmodels_before"]:]:
        for face in model["faces"]:
            is_door = (model["index"], face["index"]) in door_faces
            assert bool(face["attributes"] & 0x02000000) == is_door
            assert face["cog_triggered_number"] == (config["event"] if is_door else 0)
            if is_door:
                assert face["texture_name"] == remap["bdoorb"]

    scene = yaml.load(base.with_suffix(".scene.yml").read_text(), Loader=yaml.CSafeLoader)
    retired = scene["entities"][config["retired_decoration"]]
    assert retired["entity_index"] == config["retired_decoration"] and retired["name"] == "SHP"
    retired["name"] = ""
    for key in ("decoration_list_id", "ai_attributes", "event_id_primary", "event_id_secondary", "variable_primary",
                "variable_secondary", "special_trigger", "initial_decoration_flag"):
        retired[key] = 0
    for model in compiled["bmodels"][report["bmodels_before"]:]:
        for face in model["faces"]:
            scene["bmodel_faces"]["interactive_faces"].append({
                "bmodel_index": model["index"], "face_index": face["index"],
                "legacy_attributes": face["attributes"], "cog_number": 0,
                "cog_triggered_number": face["cog_triggered_number"], "cog_trigger": 0})
    (BUILD / "oute3.scene.yml").write_text(yaml.safe_dump(scene, sort_keys=False, width=120))

    if not ASSETS.exists():
        PLAYTEST.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-al", str(ROOT / "assets_dev"), str(ASSETS)], check=True)
    for name in ("oute3.odm", "oute3.scene.yml"):
        atomic_copy(BUILD / name, target_maps / name)
    # Remove only the test links to now-stale lighting. The original files remain intact.
    for name in ("oute3.lighting", "oute3.bake.json"):
        path = target_maps / name
        if path.exists():
            path.unlink()

    textures = []
    for old, new in remap.items():
        native = ROOT / "assets_dev/worlds/mm8/textures" / (old + ".bmp")
        enhanced = ROOT / "assets_dev/worlds/mm8/textures_x2" / (old + ".png")
        target_native = ASSETS / "worlds/mm6/textures" / (new + ".bmp")
        target_enhanced = ASSETS / "worlds/mm6/textures_x2" / (new + ".png")
        atomic_copy(enhanced, target_enhanced)
        with Image.open(enhanced) as image:
            logical_size = tuple(v // 2 for v in image.size)
            if native.exists():
                with Image.open(native) as base_image:
                    assert base_image.size == logical_size
                atomic_copy(native, target_native)
                native_origin = str(native.relative_to(ROOT))
            else:
                temporary = target_native.with_suffix(".ship-tmp")
                image.convert("RGB").resize(logical_size, Image.Resampling.LANCZOS).save(temporary, format="BMP")
                os.replace(temporary, target_native)
                native_origin = "Logical-size BMP derived from existing x2 PNG; no native BMP was present."
        textures.append({"source": old, "target": new, "logical_size": logical_size,
                         "native_origin": native_origin, "x2_source": str(enhanced.relative_to(ROOT)),
                         "x2_sha256": digest(enhanced)})

    # Use unmodified bake producers in this independent root; their root-relative paths resolve to the test copy.
    for name in ("bake_outdoor.py", "bake_geometry.py", "bake_assets.py", "bake_decorations.py"):
        atomic_copy(ROOT / "tools/lighting" / name, PLAYTEST / "tools/lighting" / name)
    atomic_copy(ROOT / "util/map_export.py", PLAYTEST / "util/map_export.py")
    profile = json.loads(base.with_suffix(".bake.json").read_text())["profile"]
    profile["preview_position"] = [-1000, -11900, 1200]
    profile["preview_target"] = [2200, -9968, 500]
    (PROJECT / "source/bake_profile.json").write_text(json.dumps(profile, indent=2) + "\n")
    report.update(geometry_sha256=digest(BUILD / "oute3.odm"), scene_sha256=digest(BUILD / "oute3.scene.yml"),
                  textures=textures, unchanged=["terrain arrays", "original BModels", "other decorations", "spawns"],
                  ship_event=config["event"], ship_position=config["position"],
                  door_faces=[list(face) for face in sorted(door_faces)],
                  suppressed_coplanar_faces=config["suppressed_coplanar_faces"])
    (BUILD / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    assert digest(base) == config["base_sha256"]
    assert digest(base.with_suffix(".scene.yml")) == config["base_scene_sha256"]
    print(json.dumps({k: v for k, v in report.items() if k != "textures"}, indent=2))


if __name__ == "__main__":
    main()
