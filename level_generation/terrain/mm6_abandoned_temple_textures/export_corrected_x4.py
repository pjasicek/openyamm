"""Export the material correction as an isolated review pack; preserve all earlier artwork."""

import copy
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


base = Path(__file__).resolve().parent
repo = base.parents[2]
stage = repo / "output/temple-textures-stage-20261008"
review = base / "review/material_correction_x4"
output = base / "runtime_corrected_x4"
reduced = base / "runtime_corrected_demo_x2"
previous = json.loads((review / "input_manifest.json").read_text())
old = {row["name"]: row for row in previous["selected"]}
jobs = {row["name"]: row for row in json.loads((base / "material_correction_x4_jobs.json").read_text())}
selected = {}
for directory in (review, output, reduced):
    directory.mkdir(exist_ok=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit(image, size):
    assert all(a >= b for a, b in zip(image.size, size)), (image.size, size, "upsampling forbidden")
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def source(path, prompt, crop=None, rectangular=False):
    assert str(path).startswith("generated/") and (base / prompt).is_file()
    image = Image.open(base / path).convert("RGBA")
    alpha = np.asarray(image.getchannel("A"))
    info = {"source": path, "prompt": prompt, "source_size": list(image.size),
            "source_sha256": digest(base / path),
            "raw_alpha": {"extrema": [int(alpha.min()), int(alpha.max())],
                          "transparent_pixels": int((alpha == 0).sum())}}
    if rectangular:
        assert alpha.min() == 0 and alpha.max() >= 250, (path, "real alpha required")
        left, top, right, bottom = Image.fromarray(alpha >= 240).getbbox()
        mask = alpha[top:bottom, left:right] >= 240
        rows = np.flatnonzero(mask.mean(axis=1) >= .95)
        columns = np.flatnonzero(mask.mean(axis=0) >= .95)
        assert len(rows) and len(columns), path
        crop = [left + int(columns[0]), top + int(rows[0]),
                left + int(columns[-1]) + 1, top + int(rows[-1]) + 1]
    crop = crop or [0, 0, image.width, image.height]
    image = image.crop(crop)
    info.update(crop=list(crop), usable_size=list(image.size), rotation=0)
    if rectangular:
        image = image.convert("RGB").convert("RGBA")
    return image, info


def fresh(name, **kwargs):
    job = jobs[name]
    assert job["status"] in ("generated_for_review", "reviewed"), name
    assert digest(base / job["output"]) == job["source_sha256"], name
    return source(job["output"], job["prompt_file"], **kwargs)


def export(name, image, sources, construction, **details):
    assert name not in selected, name
    size = tuple(value * 4 for value in old[name]["native_size"])
    image = fit(image, size).convert("RGB").convert("RGBA")
    assert image.getchannel("A").getextrema() == (255, 255)
    image.save(output / (name + ".png"))
    fit(image, tuple(value * 2 for value in old[name]["native_size"])).save(reduced / (name + ".png"))
    selected[name] = {"name": name, "native_size": old[name]["native_size"], "runtime_size": list(size),
                      "sources": sources, "runtime_sha256": digest(output / (name + ".png")),
                      "construction": construction, "decision": "corrected",
                      "previous_runtime_sha256": old[name]["runtime_sha256"], **details}
    return image


def overlay(name, background, foreground, info, rect, sources):
    target = tuple(value * 4 for value in rect)
    size = (target[2] - target[0], target[3] - target[1])
    info["component_target_size"] = list(size)
    layer = Image.new("RGBA", background.size)
    layer.paste(fit(foreground, size), target[:2])
    layer.save(review / (name + "_overlay.png"))
    image = Image.alpha_composite(background, layer)
    uncovered = np.asarray(layer.getchannel("A")) == 0
    assert np.array_equal(np.asarray(image)[uncovered], np.asarray(background)[uncovered]), name
    return export(name, image, sources + [info], "registered foreground on the identical corrected shared base",
                  native_placement=list(rect), exact_exposed_base=True,
                  correction="Reassembled over corrected shared material with registered true-alpha artwork")


# A narrow source must also fail when only one dimension is insufficient.
for image, size in [(Image.new("RGBA", (8, 8)), (16, 8)), (Image.new("RGBA", (32, 2)), (16, 4))]:
    try:
        fit(image, size)
    except AssertionError:
        pass
    else:
        raise AssertionError("Undersized artwork accepted")

components = {"chest_front", "chest_back", "chest_lid", "beam_body", "bemsv32_body",
              "d1_pillar", "d2_pillar", "d2_relief"}
for name in jobs:
    if name in components:
        continue
    image, info = fresh(name, rectangular=name in ("gset05", "gset06"))
    if jobs[name].get("inverse_half_wrap"):
        # Keep the accepted matte body; use the seam return only for its repaired central section.
        original_job = next(row for row in jobs[name]["rejected"] if row["output"].endswith("_v2.png"))
        original_body, original_info = source(original_job["output"], original_job["prompt_file"], rectangular=True)
        size = tuple(value * 4 for value in old[name]["native_size"])
        original_body = fit(original_body, size)
        original_body = Image.fromarray(np.roll(np.asarray(original_body), size[0] // 2, axis=1))
        repair = fit(image, size)
        rect = [size[0] * 2 // 5, 0, size[0] * 3 // 5, size[1]]
        original_body.paste(repair.crop(rect), rect[:2])
        image = Image.fromarray(np.roll(np.asarray(original_body), -size[0] // 2, axis=1))
        info.update(repair_native4x_rect=rect, inverse_wrap_shift=[-size[0] // 2, 0])
        original_info["offset_wrap_shift"] = [size[0] // 2, 0]
        export(name, image, [original_info, info], "matte body with registered imagegen centre-wrap repair",
               correction=jobs[name]["reason"], repaired_join=True)
        continue
    export(name, image, [info], "new material correction reduced directly from native-detail artwork",
           correction=jobs[name]["reason"])

for family, names in {
    "chest_front": ["ch1frle", "ch1frntb", "ch1frre"],
    "chest_back": ["ch1bkle", "ch1bakb", "ch1bkre"],
    "chest_lid": ["ch1tplev", "ch1tpbv", "ch1tprev"],
}.items():
    for name in names:
        previous_source = old[name]["sources"][0]
        assert jobs[family]["source_size"] == previous_source["source_size"], family
        image, info = fresh(family, crop=previous_source["crop"])
        export(name, image, [info], "registered cuts from one corrected connected chest master",
               correction=jobs[family]["reason"])

beam, beam_info = fresh("beam_body")
band = [0, beam.height // 3, beam.width, beam.height * 2 // 3]
body = beam.crop(band)
beam_info["body_crop_within_source"] = band
for name, rotate in [("beamplnh", False), ("beamplnv", True)]:
    info = copy.deepcopy(beam_info)
    info["body_rotation"] = 90 if rotate else 0
    image = body.transpose(Image.Transpose.ROTATE_90) if rotate else body
    export(name, image, [info], "corrected continuous timber body with registered orientation",
           correction=jobs["beam_body"]["reason"])

wood, wood_info = fresh("bemsv32_body")
for index, name in enumerate(["bemsv32a", "bemsv32c"]):
    band = [index * wood.width // 2, 0, (index + 1) * wood.width // 2, wood.height]
    info = copy.deepcopy(wood_info)
    info["body_crop_within_source"] = band
    export(name, wood.crop(band), [info], "fine warm timber body, separate native-detail vertical sections",
           correction=jobs["bemsv32_body"]["reason"])

for family, wall_name, variants in [
    ("d1", "d1wldle2", [("d1wldle", True), ("d1wldre", False)]),
    ("d1", "d1wldle3", [("d1wlele", True), ("d1wlere", False)]),
    ("d2", "d2wlactr", [("d2wlale", True), ("d2wlare", False)]),
]:
    wall = Image.open(output / (wall_name + ".png")).convert("RGBA")
    pillar, pillar_info = fresh(family + "_pillar", rectangular=True)
    for name, left in variants:
        background = wall.crop((0 if left else wall.width - 512, 0, 512 if left else wall.width, 1024))
        x = 0 if left else 96
        overlay(name, background, pillar, copy.deepcopy(pillar_info), (x, 0, x + 32, 256),
                copy.deepcopy(selected[wall_name]["sources"]))

grate, info = source("generated/full_x4/d1_grate_v1.png", "prompts/full_x4/d1_grate_v1.txt")
overlay("d1wldsp", Image.open(output / "d1wldle2.png").convert("RGBA"), grate, info,
        (62, 18, 194, 190), copy.deepcopy(selected["d1wldle2"]["sources"]))

relief, info = fresh("d2_relief")
brick = Image.open(output / "d2wlactr.png").convert("RGBA")
wall = Image.new("RGBA", (1024, 1024))
wall.paste(brick, (0, 0))
wall.paste(brick, (512, 0))
overlay("d2wlbmnk", wall, relief, info, (16, 16, 240, 240), copy.deepcopy(selected["d2wlactr"]["sources"]))

checker = Image.open(output / "cekr4.png").convert("RGBA")
floor = Image.new("RGBA", (2048, 2048))
for y in range(4):
    for x in range(4):
        floor.paste(checker, (x * 512, y * 512))
reflection, info = source("generated/full_x4/reflection_v1.png", "prompts/full_x4/reflection_v1.txt")
assert reflection.getchannel("A").getextrema()[0] == 0
overlay("stain512", floor, reflection, info, (48, 128, 340, 384), copy.deepcopy(selected["cekr4"]["sources"]))

for name, row in old.items():
    assert digest(base / "runtime_full_x4" / (name + ".png")) == row["runtime_sha256"], name
    if name in selected:
        continue
    shutil.copy2(base / "runtime_full_x4" / (name + ".png"), output / (name + ".png"))
    shutil.copy2(base / "runtime_full_demo_x2" / (name + ".png"), reduced / (name + ".png"))
    selected[name] = copy.deepcopy(row)
    selected[name].update(decision="retained", correction="Passed brightness and surface-finish review; unchanged 4x art")

assert set(selected) == set(old) and len(selected) == 62
for row in json.loads((base / "full_manifest.json").read_text())["textures"]:
    name = row["name"]
    assert digest(repo / "assets_dev/worlds/mm6/textures_x2" / (name + ".png")) == row["before_sha256"], name
assert digest(base / "full_x4_manifest.json") == digest(review / "input_manifest.json")

mount = stage / "corrected_x4/assets_dev"
original = stage / "before/assets_dev"
if not mount.exists():
    shutil.copytree(original, mount, copy_function=os.link)
target = mount / "worlds/mm6/textures_x4"
assert not (original / "worlds/mm6/textures_x4").exists(), "Never write through baseline hard links"
target.mkdir(exist_ok=True)
for name, row in selected.items():
    shutil.copy2(output / (name + ".png"), target / (name + ".png"))
    assert digest(target / (name + ".png")) == row["runtime_sha256"]
sky = stage / "full_x4/assets_dev/worlds/mm6/textures_x4/sky_nit2.png"
if sky.is_file():
    shutil.copy2(sky, target / sky.name)
# Water is unchanged comparison context; the uniform tier still requires native logical dimensions.
water = original / "worlds/mm6/textures_x2/orwtrtyl.png"
if water.is_file():
    image = Image.open(water)
    image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).save(target / water.name)

changed = sum(row["decision"] == "corrected" for row in selected.values())
manifest = {"map": "6d02.blv", "scope": "all 62 static textures; material-only correction",
            "selected": [selected[name] for name in old], "stage": str(mount),
            "binary_sha256": digest(stage / "openyamm"), "map_sha256": previous["map_sha256"],
            "production_changed": False, "renderer_changed": False, "static_esrgan_context_count": 0,
            "corrected_count": changed, "retained_count": 62 - changed, "correction_master_count": len(jobs),
            "comparison_context": {"orwtrtyl": "Unchanged original water in a tier-sized carrier; not fresh 4x art",
                                   "sky_nit2": "Unchanged original sky in a tier-sized carrier; not fresh 4x art"},
            "excluded": previous["excluded"], "status": "exported_for_native_visual_review"}
for row in manifest["selected"]:
    row["mean_display_luma"] = {}
    for label, path in [("esrgan", original / "worlds/mm6/textures_x2"),
                        ("previous_x4", base / "runtime_full_x4"), ("corrected_x4", output)]:
        pixels = np.asarray(Image.open(path / (row["name"] + ".png")).convert("RGB"), dtype=np.float32)
        row["mean_display_luma"][label] = round(float((pixels @ np.array([.2126, .7152, .0722])).mean()), 3)
(base / "corrected_x4_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

archive = review / "mm6_abandoned_temple_corrected_x4_review.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
    for name in old:
        package.write(output / (name + ".png"), "worlds/mm6/textures_x4/" + name + ".png")
    package.write(base / "corrected_x4_manifest.json", "corrected_x4_manifest.json")
    package.writestr("README.txt", "Review-only corrected material pack: all 62 static Temple textures at native 4x.\n"
                    "Use play.sh corrected_x4 torch. Production and renderer remain unchanged.\n"
                    "Animated water, sky and invisible portals are excluded. No 3D assets are included.\n")
with zipfile.ZipFile(archive) as package:
    assert len(package.namelist()) == 64 and package.testzip() is None
    for row in manifest["selected"]:
        assert hashlib.sha256(package.read("worlds/mm6/textures_x4/" + row["name"] + ".png")).hexdigest() == (
            row["runtime_sha256"])

for page in range(4):
    board = Image.new("RGB", (1800, 1160), (25, 25, 25))
    draw = ImageDraw.Draw(board)
    for i, name in enumerate(list(old)[page * 16:(page + 1) * 16]):
        x, y = (i % 4) * 450, (i // 4) * 290
        draw.text((x + 4, y + 3), name + " - " + selected[name]["decision"], fill="white")
        for col, root in enumerate([original / "worlds/mm6/textures_x2", base / "runtime_full_x4", output]):
            image = Image.open(root / (name + ".png")).convert("RGB")
            image.thumbnail((146, 248), Image.Resampling.LANCZOS)
            board.paste(image, (x + col * 150 + (146 - image.width) // 2, y + 26))
        draw.text((x + 5, y + 270), "ESRGAN        previous 4x        corrected 4x", fill="white")
    board.save(review / ("exports_review_" + str(page + 1) + ".png"))
print(f"62 verified native 4x exports: {changed} corrected, {62 - changed} retained; {len(jobs)} correction masters.")
print("Stage:", mount)
