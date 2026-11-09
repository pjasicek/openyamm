#!/usr/bin/env python3
"""Prepare all MM6 ship replacements in an isolated asset root; never modify the source worlds."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
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
MAPS = ASSETS / "worlds/mm6/maps"
sys.path.insert(0, str(ROOT / "util"))
import map_export as odm


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fnv(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".ship-tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def native_layout(data):
    """Section boundaries from the native schema, used to keep all old records verbatim."""
    assert data["version"] == 8
    count = odm.TERRAIN_SECTION_OFFSET_V8 + 3 * odm.TERRAIN_MAP_SIZE
    count += 4 + odm.CMAP1_SIZE + odm.CMAP2_SIZE + 12 * data["terrain_normal_count"]
    headers = count + 4
    bodies = headers + odm.BMODEL_HEADER_SIZE * data["bmodel_count"]
    ends = [bodies]
    for model in data["bmodels"]:
        ends.append(ends[-1] + model["vertex_count"] * odm.BMODEL_VERTEX_SIZE
                    + model["face_count"] * (odm.BMODEL_FACE_SIZE + odm.BMODEL_FACE_FLAGS_SIZE
                                              + odm.BMODEL_TEXTURE_NAME_SIZE)
                    + model["bsp_node_count"] * odm.BMODEL_BSP_NODE_SIZE)
    return count, headers, bodies, ends


def append_without_reserializing(base, candidate, original, generated, ships):
    """Take only new BModels from the native writer. Preserve opaque original fields too."""
    count, headers, bodies, ends = native_layout(original)
    new_count, new_headers, new_bodies, new_ends = native_layout(generated)
    assert count == new_count
    old_count = original["bmodel_count"]
    tail = bytearray(base[ends[-1]:])
    entity_count = struct.unpack_from("<I", tail)[0]
    assert entity_count == original["entity_count"]
    for ship in ships:
        entity = ship["entity"]
        # Empty marker, same position/facing and same index. Retain the two reserved bytes.
        offset = 4 + entity * odm.VERSION7_ENTITY_SIZE
        tail[offset:offset + 4] = bytes(4)
        tail[offset + 20:offset + 30] = bytes(10)
        name = 4 + entity_count * odm.VERSION7_ENTITY_SIZE + entity * odm.ENTITY_NAME_SIZE
        tail[name:name + odm.ENTITY_NAME_SIZE] = bytes(odm.ENTITY_NAME_SIZE)
    return (base[:count] + struct.pack("<I", generated["bmodel_count"])
            + base[headers:bodies]
            + candidate[new_headers + old_count * odm.BMODEL_HEADER_SIZE:new_bodies]
            + base[bodies:ends[-1]] + candidate[new_ends[old_count]:new_ends[-1]] + tail)


def update_scene(text, original, compiled, ships):
    scene = yaml.load(text, Loader=yaml.CSafeLoader)
    expected = copy.deepcopy(scene)
    for ship in ships:
        entity = ship["entity"]
        record = expected["entities"][entity]
        assert record["entity_index"] == entity and record["name"] == "SHP"
        assert record["event_id_secondary"] == ship["event"]
        pattern = rf"(?m)^  - entity_index: {entity}\n(?:(?!  - entity_index:|^[a-z]).*\n)*"
        match = re.search(pattern, text)
        assert match, entity
        replacement = match[0]
        fields = ["decoration_list_id", "ai_attributes", "event_id_primary", "event_id_secondary",
                  "variable_primary", "variable_secondary", "special_trigger", "initial_decoration_flag"]
        for key in ["name"] + fields:
            record[key] = "" if key == "name" else 0
            value = '""' if key == "name" else "0"
            replacement, n = re.subn(rf"(?m)^    {key}: .*", f"    {key}: {value}", replacement)
            assert n == 1, (entity, key)
        text = text[:match.start()] + replacement + text[match.end():]
    added = []
    for model in compiled["bmodels"][original["bmodel_count"]:]:
        for face in model["faces"]:
            added.append({"bmodel_index": model["index"], "face_index": face["index"],
                          "legacy_attributes": face["attributes"], "cog_number": 0,
                          "cog_triggered_number": face["cog_triggered_number"], "cog_trigger": 0})
    expected["bmodel_faces"]["interactive_faces"].extend(added)
    lines = "".join("    - bmodel_index: " + str(face["bmodel_index"]) + "\n"
                    + "".join(f"      {key}: {value}\n" for key, value in face.items() if key != "bmodel_index")
                    for face in added)
    assert text.count("\nentities:\n") == 1
    result = text.replace("\nentities:\n", "\n" + lines + "entities:\n")
    assert yaml.load(result, Loader=yaml.CSafeLoader) == expected
    return result


def rotate(x, y, quarters):
    return [(x, y), (-y, x), (-x, -y), (y, -x)][quarters]


def pose(ship, x, y, z, yaw=0, pitch=0):
    rx, ry = rotate(x, y, ship["rotation_quarters"])
    px, py, pz = ship["position"]
    return {"x": px + rx, "y": py + ry, "z": pz + z,
            "yaw": yaw + ship["rotation_quarters"] * math.pi / 2, "pitch": pitch}


def review_inputs(map_config, initial_count):
    name = map_config["map"]
    stem = Path(name).stem
    shots = []
    for i, ship in enumerate(map_config["ships"]):
        slug = re.sub(r"[^a-z0-9]+", "_", ship["service"].lower()).strip("_")
        for suffix, location in [
            ("overview", pose(ship, -2700, -2300, 1500, 0.62, -0.3)),
            ("boarding", pose(ship, 272, -698, 264, math.pi / 2, -0.2)),
            ("return", pose(ship, 272, -152, 193, -math.pi / 2, -0.12)),
            ("cabin", pose(ship, 496, 0, 193))]:
            if not ship["event"] and suffix != "overview":
                continue
            shots.append({"name": slug + "_" + suffix,
                          "position": [location[k] for k in "xyz"],
                          "yaw": location["yaw"], "pitch": location["pitch"]})
        if not ship["event"]:
            continue
        # The same donor entry ramp, tested across the four rotations and three pier elevations.
        forward = {"map": name, **pose(ship, 272, -632, 265, math.pi / 2)}
        aboard = {"map": name, **pose(ship, 272, -152, 193, math.pi / 2)}
        backward = {"map": name, **pose(ship, 272, -152, 193, -math.pi / 2)}
        ashore = {"map": name, **pose(ship, 272, -537, 265, -math.pi / 2)}
        def movement(start, stop):
            return {"movement_segment": {"start": start, "expect_stop": stop, "seconds": 1.25,
                    "input": "forward", "shift": True, "actor_ai": False, "tolerance_xy": 16, "tolerance_z": 3}}
        scenario = {"id": f"mm6.ships.{stem}.{slug}", "title": ship["service"] + " boarding and cabin",
                    "world": "mm6", "mode": "faithful", "steps": [
                        {"new_game_flow": {"start_map": name}}, movement(forward, aboard), movement(backward, ashore),
                        {"press_interact": {"pose": {"map": name, **pose(ship, 496, 0, 193)},
                         "expect": {"can_activate": True, "target_index": initial_count + i * 5 + 2,
                                    "face_index": 42, "triggered_event": ship["event"]}}}]}
        path = PROJECT / "source/scenarios" / (stem + "_" + slug + ".yml")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(scenario, sort_keys=False))
    tour = {"output_dir": "../../review/" + stem, "settle_seconds": 1.5, "exit": True, "shots": shots}
    path = PROJECT / "source/tours" / (stem + ".yml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(tour, sort_keys=False))


def verify_map(original, compiled, ships, remap):
    retired = {ship["entity"] for ship in ships}
    assert compiled["bmodels"][:original["bmodel_count"]] == original["bmodels"], "Existing BModel changed"
    for key in original:
        if key not in ("bmodels", "bmodel_count", "total_faces_count", "entities"):
            assert original[key] == compiled[key], key
    for before, after in zip(original["entities"], compiled["entities"]):
        if before["index"] not in retired:
            assert before == after, ("entity", before["index"])
        else:
            assert not after["name"] and not after["event_id_secondary"] and not after["decoration_list_id"]
            assert before["position"] == after["position"] and before["facing"] == after["facing"]
    assert compiled["bmodel_count"] == original["bmodel_count"] + 5 * len(ships)
    for i, ship in enumerate(ships):
        start = original["bmodel_count"] + i * 5
        for model in compiled["bmodels"][start:start + 5]:
            for face in model["faces"]:
                door = ship["event"] != 0 and (model["index"], face["index"]) == (start + 2, 42)
                assert bool(face["attributes"] & 0x02000000) == door
                assert face["cog_triggered_number"] == (ship["event"] if door else 0)
                assert face["cog_number"] == face["cog_trigger"] == 0
                if door:
                    assert face["texture_name"] == remap["bdoorb"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--install-lighting", action="store_true")
    action.add_argument("--package", action="store_true")
    args = parser.parse_args()
    config = json.loads((PROJECT / "source/ships.json").read_text())
    base_maps = PROJECT / config["base_maps_root"]
    sources = {config["donor_map"]: config["donor_sha256"]}
    for entry in config["maps"]:
        sources.update(entry["sources"])
    for name, expected in sources.items():
        source = base_maps / Path(name).name if name.startswith("assets_dev/worlds/mm6/maps/") else ROOT / name
        assert digest(source) == expected, "Pinned source changed: " + str(source)
    if args.install_lighting:
        for entry in config["maps"]:
            stem = Path(entry["map"]).stem
            for suffix in (".lighting", ".bake.json"):
                atomic_copy(PROJECT / "bake" / stem / (stem + suffix), MAPS / (stem + suffix))
        print("Installed seven isolated lighting/recipe pairs.")
        return
    if args.package:
        report = json.loads((BUILD / "report.json").read_text())
        files = []
        for entry in report["maps"]:
            stem = Path(entry["map"]).stem
            assert digest(MAPS / entry["map"]) == entry["geometry_sha256"]
            assert digest(MAPS / (stem + ".scene.yml")) == entry["scene_sha256"]
            bake = json.loads((PROJECT / "bake" / stem / "report.json").read_text())
            assert digest(MAPS / (stem + ".lighting")) == bake["output_sha256"]
            for suffix in (".odm", ".scene.yml", ".bake.json"):
                key = "worlds/mm6/maps/" + stem + suffix
                assert fnv((ASSETS / key).read_bytes()) == bake["dependencies"][key], key
            lighting_geometry = struct.unpack_from("<Q", (MAPS / (stem + ".lighting")).read_bytes(), 16)[0]
            assert lighting_geometry == bake["dependencies"]["worlds/mm6/maps/" + stem + ".odm"]
            for suffix in (".odm", ".scene.yml", ".lighting", ".bake.json"):
                files.append(MAPS / (stem + suffix))
        for texture in report["textures"]:
            for directory, suffix in [("textures", ".bmp"), ("textures_x2", ".png")]:
                files.append(ASSETS / "worlds/mm6" / directory / (texture["target"] + suffix))
        archive_path = BUILD / "mm6_ships_overlay.zip"
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                # Fixed metadata makes repeated packaging reproducible.
                info = zipfile.ZipInfo(str(path.relative_to(ASSETS)), (2026, 9, 29, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        with zipfile.ZipFile(archive_path) as archive:
            assert archive.testzip() is None
        write_json(BUILD / "package.json", {"package": archive_path.name, "sha256": digest(archive_path),
                   "files": [{"path": str(path.relative_to(ASSETS)), "sha256": digest(path),
                              "bytes": path.stat().st_size} for path in files]})
        print(f"Packaged {len(files)} files: {archive_path}")
        return

    BUILD.mkdir(parents=True, exist_ok=True)
    compiler = BUILD / "port_ship"
    subprocess.run(["c++", "-std=c++20", "-O2", "-I", str(ROOT), str(PROJECT / "source/port_ship.cpp"),
                    str(ROOT / "game/outdoor/OutdoorMapData.cpp"), "-o", str(compiler)], check=True)
    donor = ROOT / config["donor_map"]
    donor_data = odm.parse_odm_file(donor)["payload"]
    names = sorted({f["texture_name"].lower() for i in config["donor_models"] for f in donor_data["bmodels"][i]["faces"]})
    remap = {name: f"ns8s{i:02}" for i, name in enumerate(names)}
    (BUILD / "textures.tsv").write_text("".join(f"{a}\t{b}\n" for a, b in remap.items()))
    for key, file in [("door_faces", "doors.tsv"), ("suppressed_coplanar_faces", "suppressed.tsv")]:
        (BUILD / file).write_text("".join(f"{m}\t{f}\n" for m, f in config[key]))
    if not ASSETS.exists():
        PLAYTEST.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-al", str(ROOT / "assets_dev"), str(ASSETS)], check=True)
    report = {"maps": [], "textures": [], "lua_changes": [], "original_sources": sources}
    for entry in config["maps"]:
        name = entry["map"]
        stem = Path(name).stem
        base = base_maps / name
        original = odm.parse_odm_file(base)["payload"]
        assert {e["index"] for e in original["entities"] if e["name"] == "SHP"} == {s["entity"] for s in entry["ships"]}
        lua = (ROOT / "assets_dev/worlds/mm6/events/maps" / (stem + ".lua")).read_text(encoding="latin-1")
        for ship in entry["ships"]:
            if ship["event"]:
                pattern = rf'RegisterEvent\({ship["event"]}, "{re.escape(ship["service"])}", function\(\)(.*?)\nend'
                handler = re.search(pattern, lua, re.S)
                assert handler and f'evt.EnterHouse({ship["house"]})' in handler[1], ship["service"]
        placements = BUILD / (stem + ".tsv")
        placements.write_text("".join("\t".join(map(str, [s["entity"], s["event"], s["rotation_quarters"], *s["position"]]))
                                     + "\n" for s in entry["ships"]))
        candidate = BUILD / (stem + "-candidate.odm")
        subprocess.run([str(compiler), str(base), str(donor), str(candidate), str(BUILD / "textures.tsv"),
                        str(placements), str(BUILD / "suppressed.tsv"), str(BUILD / "doors.tsv")], check=True)
        generated = odm.parse_odm_file(candidate)["payload"]
        (BUILD / name).write_bytes(append_without_reserializing(base.read_bytes(), candidate.read_bytes(),
                                                             original, generated, entry["ships"]))
        compiled = odm.parse_odm_file(BUILD / name)["payload"]
        verify_map(original, compiled, entry["ships"], remap)
        subprocess.run([str(compiler), "--check", str(BUILD / name)], check=True)
        scene_path = BUILD / (stem + ".scene.yml")
        scene_path.write_text(update_scene(base.with_suffix(".scene.yml").read_text(), original, compiled, entry["ships"]))
        for path in (BUILD / name, scene_path):
            atomic_copy(path, MAPS / path.name)
        for suffix in (".lighting", ".bake.json"):
            (MAPS / (stem + suffix)).unlink(missing_ok=True)
        profile = json.loads(base.with_suffix(".bake.json").read_text())["profile"]
        write_json(PROJECT / "source/profiles" / (stem + ".json"), profile)
        review_inputs(entry, original["bmodel_count"])
        report["maps"].append({"map": name, "location": entry["location"], "ships": entry["ships"],
            "original_bmodels": original["bmodel_count"], "added_bmodels": 5 * len(entry["ships"]),
            "unchanged_original_bmodels_including_opaque_bytes": True,
            "unchanged_terrain_spawns_other_entities_and_scene_state": True,
            "geometry_sha256": digest(BUILD / name), "scene_sha256": digest(scene_path)})
        candidate.unlink()
    for old, new in remap.items():
        native = ROOT / "assets_dev/worlds/mm8/textures" / (old + ".bmp")
        enhanced = ROOT / "assets_dev/worlds/mm8/textures_x2" / (old + ".png")
        target = ASSETS / "worlds/mm6/textures" / (new + ".bmp")
        atomic_copy(enhanced, ASSETS / "worlds/mm6/textures_x2" / (new + ".png"))
        with Image.open(enhanced) as image:
            logical = tuple(v // 2 for v in image.size)
            if native.exists():
                with Image.open(native) as bitmap:
                    assert bitmap.size == logical
                atomic_copy(native, target)
            else:
                temporary = target.with_suffix(".ship-tmp.bmp")
                image.convert("RGB").resize(logical, Image.Resampling.LANCZOS).save(temporary)
                os.replace(temporary, target)
        report["textures"].append({"source": old, "target": new, "logical_size": logical,
                                   "native_sha256": digest(target), "enhanced_sha256": digest(enhanced)})
    for name in ("bake_outdoor.py", "bake_geometry.py", "bake_assets.py", "bake_decorations.py"):
        atomic_copy(ROOT / "tools/lighting" / name, PLAYTEST / "tools/lighting" / name)
    atomic_copy(ROOT / "util/map_export.py", PLAYTEST / "util/map_export.py")
    write_json(BUILD / "report.json", report)
    print("Prepared 12 ships on seven maps; original geometry, scene content and Lua preserved.")


if __name__ == "__main__":
    main()
