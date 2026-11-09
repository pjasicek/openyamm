"""Assemble the matched native captures and validate this focused art demo."""

import argparse
import configparser
import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


base = Path(__file__).resolve().parent
repo = base.parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--full", action="store_true", help="Review the complete 62-texture 4x pack")
parser.add_argument("--corrected", action="store_true", help="Review the complete material correction")
args = parser.parse_args()
full = args.full or args.corrected
review = base / ("review/material_correction_x4" if args.corrected else "review/full_x4" if full else "review/x4")
runtime = base / ("runtime_corrected_x4" if args.corrected else "runtime_full_x4" if full else "runtime_x4")
manifest_name = "corrected_x4_manifest.json" if args.corrected else "full_x4_manifest.json" if full else "demo_x4_manifest.json"
manifest = json.loads((base / manifest_name).read_text())
assert len(manifest["selected"]) == (62 if full else 12)
if full:
    assert manifest["static_esrgan_context_count"] == 0
poses = json.loads((review / "demo_poses.json").read_text())
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
validation = {"selected_textures": len(manifest["selected"]), "poses": len(poses), "captures": {}, "runs": {}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_prefix(mode):
    if args.corrected and mode == "x4":
        return "corrected_x4_"
    return "full_x4_" if full else "demo_"


for mode in ["esrgan", "x4"]:
    prefix = capture_prefix(mode)
    for lighting in ["normal", "torch"]:
        key = mode + "_" + lighting
        receipt = json.loads((base / "captures" / (prefix + key + ".run.json")).read_text())
        assert receipt["status"] == "completed" and receipt["exit_code"] == 0, key
        assert receipt["loaded_map"] == "6d02.blv", key
        assert receipt["binary_sha256"] == manifest["binary_sha256"], key
        assets = Path(receipt["assets"])
        assert digest(assets / "worlds/mm6/maps/6d02.blv") == manifest["map_sha256"], key
        if mode == "x4":
            assert assets == Path(manifest["stage"]), key
        log = (Path(receipt["run_directory"]) / "game.log").read_text()
        tier = "x2" if mode == "esrgan" else "x4"
        assert "texture=" + tier in log and "Renderer: OpenGL 3.3" in log, key
        assert "GPU: vendor=0x10de" in log, key
        assert not re.search(r"(?:could not|failed to).*texture|result=missing", log, re.I), key
        files = sorted((base / "captures" / (prefix + key)).glob("*.png"))
        assert len(files) == len(poses), key
        validation["runs"][key] = {"source_save_sha256": receipt["source_save_sha256"],
                                   "binary_sha256": receipt["binary_sha256"], "status": receipt["status"],
                                   "renderer": "OpenGL 3.3", "gpu_vendor": "NVIDIA 0x10de", "texture_tier": tier}
        validation["captures"][key] = {str(path.relative_to(base)): digest(path) for path in files}
        for image in files:
            assert Image.open(image).size == (1600, 900), image

ignored = {("assets", "root"), ("startup", "save_file"), ("debug", "screenshot_tour_path"),
           ("video_quality", "texture"), ("video_quality", "textures"),
           ("logging", "fps_trace_path"), ("logging", "performance_trace_path")}
for lighting in ["normal", "torch"]:
    normalized = []
    for mode in ["esrgan", "x4"]:
        prefix = capture_prefix(mode)
        receipt = json.loads((base / "captures" / (prefix + mode + "_" + lighting + ".run.json")).read_text())
        ini = configparser.ConfigParser(interpolation=None)
        ini.read(Path(receipt["run_directory"]) / "launch-settings.ini")
        normalized.append({(section, key): value for section in ini.sections() for key, value in ini[section].items()
                           if (section, key) not in ignored})
    assert normalized[0] == normalized[1], (lighting, "unrelated settings differ")
    assert validation["runs"]["esrgan_" + lighting]["source_save_sha256"] == (
        validation["runs"]["x4_" + lighting]["source_save_sha256"])
    for kind in ["details", "comparisons"]:
        (review / kind / lighting).mkdir(parents=True, exist_ok=True)
    for index, pose in enumerate(poses):
        name = str(index + 1).zfill(2) + "-" + pose["name"] + ".png"
        before = Image.open(base / "captures" / (capture_prefix("esrgan") + "esrgan_" + lighting) / name).convert("RGB")
        after = Image.open(base / "captures" / (capture_prefix("x4") + "x4_" + lighting) / name).convert("RGB")
        if full:
            rectangle = (280, 60, 1320, 740)
            delta = np.abs(np.asarray(before.crop(rectangle), dtype=np.int16) -
                           np.asarray(after.crop(rectangle), dtype=np.int16))
            changed = float((delta.max(axis=2) > 10).mean())
            validation.setdefault("world_pixel_changes", {}).setdefault(lighting, {})[pose["name"]] = {
                "rectangle": list(rectangle), "fraction_over_10": changed,
                "mean_absolute_channel_change": float(delta.mean())}
            if lighting == "torch" and pose["name"] in ("masonry-vault", "celtic-stairs", "stone-hall-floor"):
                assert changed > 0.05, (pose["name"], "previously unchanged surfaces still look unchanged")
        board = Image.new("RGB", (3200, 930), (25, 25, 25))
        board.paste(before, (0, 30))
        board.paste(after, (1600, 30))
        draw = ImageDraw.Draw(board)
        draw.text((12, 4), "Current ESRGAN 2x - " + pose["name"] + " - " + lighting, font=font, fill="white")
        caption = "Complete fresh 4x pack — all 62 static textures" if full else "Partial 4x pack — 12/62"
        if args.corrected:
            caption = "Corrected material pack — all 62 static textures at 4x"
        if not full and pose["name"] in ("masonry-vault", "celtic-stairs", "stone-hall-floor"):
            caption = "Unchanged ESRGAN surfaces in partial 4x stage"
        draw.text((1612, 4), caption, font=font, fill="white")
        board.save(review / "comparisons" / lighting / (pose["name"] + ".png"))
        crop = (600, 180, 1040, 620)
        for label, image in [("esrgan", before), ("x4", after)]:
            image.crop(crop).save(review / "details" / lighting / (pose["name"] + "-" + label + ".png"))

wall = np.asarray(Image.open(base / "review/x4/shared_wall_base.png"))
for name in ["wywt", "stabig2"]:
    layer = Image.open(base / "review/x4" / (name + "_overlay.png"))
    alpha = np.asarray(layer.getchannel("A"))
    assert int(alpha.min()) == 0 and int(alpha.max()) == 255
    output = np.asarray(Image.open(runtime / (name + ".png")))
    assert np.array_equal(output[alpha == 0], wall[alpha == 0]), name

original = json.loads((base / "full_manifest.json").read_text())
for row in original["textures"]:
    name = row["name"]
    production = repo / "assets_dev/worlds/mm6/textures_x2" / (name + ".png")
    assert digest(production) == row["before_sha256"], name
    assert digest(base / "runtime" / (name + ".png")) == row["runtime_sha256"], name
for row in manifest["selected"]:
    export = runtime / (row["name"] + ".png")
    assert Image.open(export).size == tuple(value * 4 for value in row["native_size"])
    assert digest(export) == row["runtime_sha256"]
    assert digest(Path(manifest["stage"]) / "worlds/mm6/textures_x4" / export.name) == row["runtime_sha256"]
    for source in row["sources"]:
        assert digest(base / source["source"]) == source["source_sha256"]
        assert (base / source["prompt"]).exists()
    if full:
        before = Image.open(repo / "assets_dev/worlds/mm6/textures_x2" / export.name).convert("RGB")
        after = Image.open(export).convert("RGB").resize(before.size, Image.Resampling.LANCZOS)
        for label, image in [("esrgan", before), ("candidate", after)]:
            proof = Image.new("RGB", (image.width * 2, image.height * 2))
            for y in range(2):
                for x in range(2):
                    proof.paste(image, (x * image.width, y * image.height))
            proof.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            proof.save(review / (row["name"] + "_" + label + "_repeat.png"))

(review / "demo_data.js").write_text("const demoData = " + json.dumps(
    {"textures": manifest["selected"], "poses": poses}) + ";\n")
validation.update(status="passed", total_native_captures=len(poses) * 4, identical_exposed_composite_background=True,
                  production_baselines_unchanged=62, frozen_x2_exports_unchanged=62,
                  settings_comparison="Matched per lighting pair except tier and private asset/save/tour/log paths",
                  context="Complete material correction; no ESRGAN carriers" if args.corrected else
                          "All 62 static materials regenerated" if full else "50 static ESRGAN textures retained as context",
                  limitations=["Original face UV phase and baked lighting differences remain",
                               "PNG uploads; GPU compression and FPS/memory benchmarking not performed"])
if not full:
    validation["limitations"][:0] = ["Focused 12-texture art demo", "Carpet is a symmetric reinterpretation"]
if args.corrected:
    validation.update(corrected_materials=manifest["corrected_count"], retained_4x_materials=manifest["retained_count"],
                      fresh_candidate_captures=len(poses) * 2, frozen_esrgan_captures_reused=len(poses) * 2,
                      renderer_changed=False)
    patches = []
    for lighting in ["normal", "torch"]:
        for stem, rect in [("04-masonry-vault", [550, 350, 1050, 410]),
                           ("02-rubble-floor", [300, 480, 1300, 680])]:
            values = {}
            hashes = {}
            for label, prefix in [("esrgan", "full_x4_esrgan_"), ("previous_x4", "full_x4_x4_"),
                                  ("corrected_x4", "corrected_x4_x4_")]:
                path = base / "captures" / (prefix + lighting) / (stem + ".png")
                image = Image.open(path).convert("RGB").crop(rect)
                pixels = np.asarray(image, dtype=np.float32)
                values[label] = float((pixels @ np.array([.2126, .7152, .0722])).mean())
                hashes[label] = digest(path)
            patches.append({"pose": stem, "lighting": lighting, "rectangle": rect, "mean_display_luma": values,
                            "capture_sha256": hashes, "previous_ratio": values["previous_x4"] / values["esrgan"],
                            "corrected_ratio": values["corrected_x4"] / values["esrgan"]})
    audit = {"method": "Stored RGB display luma with Rec.709 weights; not physical brightness or roughness",
             "screen_patches": patches,
             "materials": [{key: row[key] for key in ["name", "decision", "correction", "mean_display_luma"]}
                           for row in manifest["selected"]],
             "visual_review": "All 62 export comparisons, repeat proofs and both 21-pose capture tours inspected",
             "source_quality": "Native-detail crop budgets checked; no ESRGAN carriers among the 62 static surfaces",
             "renderer_changed": False, "production_changed": False,
             "limitations": ["Original authored UV phase and baked lighting remain",
                             "Other maps sharing these texture names not visually checked",
                             "Colour-art surface finish only; no material normals/roughness added"]}
    (review / "brightness_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
(review / "demo_validation.json").write_text(json.dumps(validation, indent=2) + "\n")
print(len(poses) * 4, "native captures, matching settings/saves, correct tiers, alpha layers and unchanged production verified.")
