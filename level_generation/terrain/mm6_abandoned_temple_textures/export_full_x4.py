"""Export all 62 static Temple textures from fresh masters; keep production and previous studies read-only."""

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
original = stage / "before/assets_dev"
review = base / "review/full_x4"
output = base / "runtime_full_x4"
reduced = base / "runtime_full_demo_x2"
for directory in (review, output, reduced):
    directory.mkdir(exist_ok=True)
old = json.loads((base / "full_manifest.json").read_text())
native = {row["name"]: row for row in old["textures"]}
jobs = {row["name"]: row for row in json.loads((base / "full_x4_jobs.json").read_text())}
selected = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit(image, size):
    assert all(a >= b for a, b in zip(image.size, size)), (image.size, size, "upsampling forbidden")
    # Filter authoring layers with premultiplied alpha so transparent RGB cannot create fringes.
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def source(path, prompt, crop=None, rotation=0, rectangular=False):
    assert str(path).startswith("generated/"), (path, "native/upscaled references are not artwork")
    image = Image.open(base / path).convert("RGBA")
    info = {"source": str(path), "prompt": str(prompt), "source_size": list(image.size),
            "source_sha256": digest(base / path)}
    assert (base / prompt).is_file(), prompt
    alpha = np.asarray(image.getchannel("A"))
    info["raw_alpha"] = {"extrema": [int(alpha.min()), int(alpha.max())],
                         "transparent_pixels": int((alpha == 0).sum())}
    if rectangular:
        assert alpha.min() == 0 and alpha.max() >= 250, (path, "true-alpha padded strip required")
        bounds = Image.fromarray(alpha >= 240).getbbox()
        assert bounds, path
        left, top, right, bottom = bounds
        mask = alpha[top:bottom, left:right] >= 240
        rows = np.flatnonzero(mask.mean(axis=1) >= 0.95)
        columns = np.flatnonzero(mask.mean(axis=0) >= 0.95)
        assert len(rows) and len(columns), path
        crop = [left + int(columns[0]), top + int(rows[0]),
                left + int(columns[-1]) + 1, top + int(rows[-1]) + 1]
    crop = crop or [0, 0, image.width, image.height]
    info["crop"] = list(crop)
    image = image.crop(crop)
    if rectangular:
        image = image.convert("RGB").convert("RGBA")
    if rotation == 90:
        image = image.transpose(Image.Transpose.ROTATE_90)
    info["rotation"] = rotation
    info["usable_size"] = list(image.size)
    return image, info


def fresh(name, **kwargs):
    job = jobs[name]
    return source(job["output"], job["prompt_file"], **kwargs)


def export(name, image, sources, construction, **details):
    assert name not in selected, (name, "duplicate owner")
    size = tuple(value * 4 for value in native[name]["native_size"])
    image = fit(image, size).convert("RGB").convert("RGBA")
    assert image.size == size and image.getchannel("A").getextrema() == (255, 255)
    image.save(output / (name + ".png"))
    fit(image, tuple(value * 2 for value in native[name]["native_size"])).save(reduced / (name + ".png"))
    selected[name] = {"name": name, "native_size": native[name]["native_size"], "runtime_size": list(size),
                      "sources": sources, "runtime_sha256": digest(output / (name + ".png")),
                      "construction": construction, **details}
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
    return export(name, image, sources + [info], "registered foreground on an identical shared material base",
                  native_placement=list(rect), exact_exposed_base=True)


# Trust-boundary checks: insufficient source pixels must fail, including an undersized thin strip.
for image, size in [(Image.new("RGBA", (8, 8)), (16, 8)), (Image.new("RGBA", (32, 2)), (16, 4))]:
    try:
        fit(image, size)
    except AssertionError:
        pass
    else:
        raise AssertionError("Undersized artwork accepted")
transparent = Image.new("RGBA", (4, 4), (255, 255, 255, 0))
transparent.paste((80, 60, 40, 255), (1, 1, 3, 3))
assert fit(transparent, (2, 2)).size == (2, 2)

demo = json.loads((base / "demo_x4_manifest.json").read_text())
for row in demo["selected"]:
    if row["name"] in ("carpt01", "beamplnh", "beamplnv"):
        continue
    image = Image.open(base / "runtime_x4" / (row["name"] + ".png"))
    assert digest(base / "runtime_x4" / (row["name"] + ".png")) == row["runtime_sha256"]
    export(row["name"], image, copy.deepcopy(row["sources"]), row["construction"],
           previous_demo_source=True)

for name in native:
    if name.startswith("ch1") or name in ("ctceil1", "ctdor4"):
        row = native[name]
        image, info = source(row["selected"], row["prompt"], row.get("crop"), row.get("master_rotation", 0))
        export(name, image, [info], "fresh earlier master re-exported directly at native 4x, never enlarged from 2x")

components = {"d1_pillar", "d2_pillar", "d1_grate", "d2_relief", "reflection", "carpt01_left", "carpt01_right",
              "carpet_join", "beam_body"}
for name in jobs:
    if name in components or name == "d2flor5" or name.endswith("_wrap"):
        continue
    if name in ("d2flor4", "sndston", "gset04"):
        image, info = fresh(name + "_wrap")
        size = tuple(value * 4 for value in native[name]["native_size"])
        image = fit(image, size)
        image = Image.fromarray(np.roll(np.asarray(image), (-size[1] // 2, -size[0] // 2), (0, 1)))
        info["inverse_wrap_shift"] = [-size[0] // 2, -size[1] // 2]
        export(name, image, [info], "new material with imagegen centre-wrap repair; inverse half-period shift")
    else:
        image, info = fresh(name)
        export(name, image, [info], "new fine material/illustration master reduced directly to native 4x")

row = selected["d2flor4"]
export("d2flor5", Image.open(output / "d2flor4.png"), copy.deepcopy(row["sources"]),
       "same new paving body as the native matching polygon-layout variant; shared joins")

beam, beam_info = fresh("beam_body")
band = [0, beam.height // 3, beam.width, beam.height * 2 // 3]
body = beam.crop(band)
beam_info["body_crop_within_source"] = band
export("beamplnh", body, [copy.deepcopy(beam_info)], "new continuous timber body; no repeated end caps")
beam_info["body_rotation"] = 90
export("beamplnv", body.transpose(Image.Transpose.ROTATE_90), [beam_info],
       "same new continuous timber body rotated; no repeated end caps")

# Narrow trim uses real native-detail crops of the new plank material, with orientation recorded.
wood, wood_info = fresh("bemhwal1")
for name, rotate, band in [("bdksh32b", False, 0), ("bdksv32b", True, 0),
                           ("bemsv32a", True, 1), ("bemsv32c", True, 2)]:
    top = round(wood.height * (0.07 + band / 3))
    bottom = round(wood.height * (0.27 + band / 3))
    body = wood.crop((0, top, wood.width, bottom))
    info = copy.deepcopy(wood_info)
    info["body_crop_within_source"] = [0, top, wood.width, bottom]
    if rotate:
        body = body.transpose(Image.Transpose.ROTATE_90)
    info["body_rotation"] = 90 if rotate else 0
    export(name, body, [info], "same freshly drawn wood body, registered crop and orientation")

for family, wall_name, variants in [
    ("d1", "d1wldle2", [("d1wldle", True), ("d1wldre", False),
                        ("d1wlele", True), ("d1wlere", False)]),
    ("d2", "d2wlactr", [("d2wlale", True), ("d2wlare", False)]),
]:
    wall = Image.open(output / (wall_name + ".png")).convert("RGBA")
    pillar, pillar_info = fresh(family + "_pillar", rectangular=True)
    for name, left in variants:
        sources = copy.deepcopy(selected[wall_name]["sources"])
        background = wall.crop((0 if left else wall.width - 512, 0, 512 if left else wall.width, 1024))
        assert background.size == (512, 1024)
        x = 0 if left else 96
        info = copy.deepcopy(pillar_info)
        overlay(name, background, pillar, info, (x, 0, x + 32, 256), sources)

grate, grate_info = fresh("d1_grate")
overlay("d1wldsp", Image.open(output / "d1wldle2.png").convert("RGBA"), grate, grate_info,
        (62, 18, 194, 190), copy.deepcopy(selected["d1wldle2"]["sources"]))

relief, relief_info = fresh("d2_relief")
brick = Image.open(output / "d2wlactr.png").convert("RGBA")
relief_wall = Image.new("RGBA", (1024, 1024))
relief_wall.paste(brick, (0, 0))
relief_wall.paste(brick, (512, 0))
overlay("d2wlbmnk", relief_wall, relief, relief_info, (16, 16, 240, 240),
        copy.deepcopy(selected["d2wlactr"]["sources"]))

checker = Image.open(output / "cekr4.png").convert("RGBA")
floor = Image.new("RGBA", (2048, 2048))
assert checker.size == (512, 512)
for y in range(4):
    for x in range(4):
        floor.paste(checker, (x * 512, y * 512))
reflection, reflection_info = fresh("reflection")
assert reflection.getchannel("A").getextrema()[0] == 0, "reflection needs real transparent unlit areas"
overlay("stain512", floor, reflection, reflection_info, (48, 128, 340, 384),
        copy.deepcopy(selected["cekr4"]["sources"]))

carpet = Image.new("RGBA", (2048, 1024))
carpet_sources = []
for index, side in enumerate(("left", "right")):
    image, info = fresh("carpt01_" + side)
    assert image.width == image.height, "Registered carpet context guide requires a square return"
    inset = round(image.width / 18)
    core_rect = (inset, inset, image.width - inset, image.height - inset)
    core = image.crop(core_rect)
    info["core_crop_within_source"] = list(core_rect)
    info["component_target_size"] = [1024, 1024]
    carpet.paste(fit(core, (1024, 1024)), (index * 1024, 0))
    carpet_sources.append(info)
join, join_info = fresh("carpet_join")
carpet.paste(fit(join, (1152, 1024)), (448, 0))
join_info["component_target_size"] = [1152, 1024]
join_info["placement"] = [448, 0, 1600, 1024]
carpet_sources.append(join_info)
# Ornament bands share one master to keep their row heights identical across the assembled rug.
left, _ = fresh("carpt01_left")
inset = round(left.width / 18)
left = fit(left.crop((inset, inset, left.width - inset, left.height - inset)), (1024, 1024))
border = Image.new("RGBA", (2048, 1024))
border.paste(left, (0, 0))
border.paste(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (1024, 0))
for rect in [(0, 0, 2048, 150), (0, 864, 2048, 1024)]:
    carpet.paste(border.crop(rect), rect[:2])
export("carpt01", carpet, carpet_sources,
       "new registered halves, redrawn continuous centre and shared horizontal ornament bands",
       shared_border_mirror=True, repaired_join=True)

assert set(selected) == set(native), {"missing": sorted(set(native) - set(selected)),
                                     "extra": sorted(set(selected) - set(native))}
for name, row in native.items():
    assert digest(original / "worlds/mm6/textures_x2" / (name + ".png")) == row["before_sha256"], name
    assert digest(repo / "assets_dev/worlds/mm6/textures_x2" / (name + ".png")) == row["before_sha256"], name
    assert digest(base / "runtime" / (name + ".png")) == row["runtime_sha256"], name

mount = stage / "full_x4/assets_dev"
if not mount.exists():
    shutil.copytree(original, mount, copy_function=os.link)
target = mount / "worlds/mm6/textures_x4"
assert not (original / "worlds/mm6/textures_x4").exists(), "Never write through baseline hard links"
target.mkdir(exist_ok=True)
for name in selected:
    shutil.copy2(output / (name + ".png"), target / (name + ".png"))
# Sky is outside the 62 restored static surfaces. Keep its original logical dimensions in this isolated tier.
sky = original / "worlds/mm6/textures_x2/sky_nit2.png"
if sky.is_file():
    image = Image.open(sky)
    image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST).save(target / sky.name)

manifest = {"map": "6d02.blv", "scope": "all 62 static textures", "selected": list(selected.values()),
            "stage": str(mount), "binary_sha256": digest(stage / "openyamm"),
            "map_sha256": digest(original / "worlds/mm6/maps/6d02.blv"), "production_changed": False,
            "static_esrgan_context_count": 0,
            "excluded": ["renderer-owned orwtrtyl water", "sky_nit2 sky", "invisible pending portals"],
            "status": "exported_for_native_visual_review"}
(base / "full_x4_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

archive = review / "mm6_abandoned_temple_x4_review.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
    for name in selected:
        package.write(output / (name + ".png"), "worlds/mm6/textures_x4/" + name + ".png")
    package.write(base / "full_x4_manifest.json", "full_x4_manifest.json")
    package.writestr("README.txt", "Review-only pack: all 62 static Abandoned Temple textures at native 4x.\n"
                    "Source masters/prompts and comparison captures remain in the repository study.\n"
                    "Play the isolated stage with play.sh full_x4 torch; production is unchanged.\n"
                    "Animated water, sky and invisible portals are excluded. No 3D assets are included.\n")
with zipfile.ZipFile(archive) as package:
    assert len(package.namelist()) == 64 and package.testzip() is None
    for name, row in selected.items():
        assert hashlib.sha256(package.read("worlds/mm6/textures_x4/" + name + ".png")).hexdigest() == row["runtime_sha256"]

for page in range(3):
    board = Image.new("RGB", (1820, 990), (25, 25, 25))
    draw = ImageDraw.Draw(board)
    for i, name in enumerate(list(native)[page * 21:(page + 1) * 21]):
        image = Image.open(output / (name + ".png"))
        image.thumbnail((240, 280), Image.Resampling.LANCZOS)
        x, y = (i % 7) * 260, (i // 7) * 330
        board.paste(image, (x + (260 - image.width) // 2, y + 28))
        draw.text((x + 5, y + 5), name + " — native 4x", fill="white")
    board.save(review / ("contact_" + str(page + 1) + ".png"))
print("62 native 4x textures exported; no static ESRGAN context. Production and earlier exports unchanged.")
print("Stage:", mount)
