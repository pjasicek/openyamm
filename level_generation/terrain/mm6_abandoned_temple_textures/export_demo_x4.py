"""Export the focused 4x art demo and an isolated mount; production and the frozen 2x study are read-only."""

import configparser
import hashlib
import json
import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


base = Path(__file__).resolve().parent
repo = base.parents[2]
stage = repo / "output/temple-textures-stage-20261008"
original = stage / "before/assets_dev"
output = base / "runtime_x4"
output.mkdir(exist_ok=True)
(base / "runtime_demo_x2").mkdir(exist_ok=True)
review = base / "review/x4"
review.mkdir(exist_ok=True)
native = {row["name"]: row for row in json.loads((base / "full_manifest.json").read_text())["textures"]}
selected = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_source(stem, padded=False):
    path = base / "generated" / (stem + ".png")
    raw = Image.open(path)
    image = raw.convert("RGBA")
    crop = [0, 0, image.width, image.height]
    info = {"source": str(path.relative_to(base)), "source_size": list(image.size), "source_sha256": digest(path)}
    prompt = base / "prompts" / (stem + ".txt")
    assert prompt.exists(), stem
    info["prompt"] = str(prompt.relative_to(base))
    if raw.mode == "RGBA":
        alpha = np.asarray(image.getchannel("A"))
        info["raw_alpha"] = {"extrema": [int(alpha.min()), int(alpha.max())],
                             "transparent_pixels": int((alpha == 0).sum())}
    if padded:
        alpha = np.asarray(image.getchannel("A"))
        assert alpha.min() == 0 and alpha.max() >= 250, (stem, "real source alpha required")
        mask = alpha >= 240
        bbox = Image.fromarray(mask).getbbox()
        assert bbox, stem
        left, top, right, bottom = bbox
        interior = mask[top:bottom, left:right]
        rows = np.flatnonzero(interior.mean(axis=1) >= 0.95)
        columns = np.flatnonzero(interior.mean(axis=0) >= 0.95)
        assert len(rows) and len(columns), stem
        crop = [left + int(columns[0]), top + int(rows[0]),
                left + int(columns[-1]) + 1, top + int(rows[-1]) + 1]
        info["raw_alpha"] = {"extrema": [int(alpha.min()), int(alpha.max())],
                             "transparent_pixels": int((alpha == 0).sum())}
    info["crop"] = crop
    # These native panels/strips are opaque rectangles, including intentionally dark painted glass.
    return image.crop(crop).convert("RGB").convert("RGBA"), info


def reduce(image, size):
    assert all(source >= target for source, target in zip(image.size, size)), (image.size, size, "upsampling forbidden")
    return image.resize(size, Image.Resampling.LANCZOS)


def export(name, image, sources, **details):
    size = tuple(value * 4 for value in native[name]["native_size"])
    image = reduce(image, size)
    assert image.getchannel("A").getextrema() == (255, 255), name
    image.save(output / (name + ".png"))
    reduce(image, tuple(value * 2 for value in native[name]["native_size"])).save(
        base / "runtime_demo_x2" / (name + ".png"))
    selected.append({"name": name, "native_size": native[name]["native_size"], "runtime_size": list(size),
                     "sources": sources, "runtime_sha256": digest(output / (name + ".png")), **details})


plaster, plaster_info = read_source("wywl_x4_section1_clean_v2")
plaster = reduce(plaster, (1024, 1024))
export("wltil2", plaster, [plaster_info], construction="shared plaster base")
wall = Image.new("RGBA", (1024, 2048))
wall.paste(plaster, (0, 0))
wall.paste(plaster, (0, 1024))
dado, dado_info = read_source("wood_dado_x4_alpha_v1", padded=True)
wall.paste(reduce(dado, (1024, 308)), (0, 1740))
wall.save(review / "shared_wall_base.png")
export("wywl", wall, [plaster_info, dado_info], construction="plaster + dado at native y=435")
export("wywl2", wall.crop((0, 1536, 1024, 2048)), [plaster_info, dado_info],
       construction="bottom 128 native rows of the identical wall base")

for name, stem, rect, padded in [
    ("wywt", "wywt_x4_overlay_clean_v1", (14, 40, 243, 391), True),
    ("stabig2", "stabig2_x4_overlay_clean_v2", (0, 63, 256, 406), False),
]:
    # The second window return fills its canvas; its original native rectangle has no transparent gaps.
    foreground, info = read_source(stem, padded=padded)
    placement = tuple(value * 4 for value in rect)
    foreground = reduce(foreground, (placement[2] - placement[0], placement[3] - placement[1]))
    layer = Image.new("RGBA", wall.size)
    layer.paste(foreground, placement[:2])
    layer.save(review / (name + "_overlay.png"))
    composite = Image.alpha_composite(wall, layer)
    uncovered = np.asarray(layer.getchannel("A")) == 0
    assert np.array_equal(np.asarray(composite)[uncovered], np.asarray(wall)[uncovered]), name
    assert np.array_equal(np.asarray(composite)[1740:], np.asarray(wall)[1740:]), name
    export(name, composite, [plaster_info, dado_info, info], native_placement=list(rect),
           construction="registered foreground over the identical shared wall; opaque native panel interiors")

for name in ["beamplnh", "gset06", "gset05"]:
    strip, info = read_source(name + "_x4_v2", padded=True)
    rect = (round(strip.width * 0.1), 0, round(strip.width * 0.9), strip.height)
    strip = strip.crop(rect)
    info["body_crop_within_strip"] = list(rect)
    export(name, strip, [info], construction="registered central repeat body from true-alpha extended master")
    if name == "beamplnh":
        export("beamplnv", strip.transpose(Image.Transpose.ROTATE_90), [info],
               construction="same wood body rotated 90 degrees")

for name, stem in [("cekr4", "cekr4_x4_clean_v2"), ("ctflor3", "ctflor3-v1")]:
    image, info = read_source(stem)
    export(name, image, [info], construction="full fresh material master reduced to native 4x")

half, half_info = read_source("carpt01_x4_section1_clean_v2")
half = reduce(half, (1024, 1024))
carpet = Image.new("RGBA", (2048, 1024))
carpet.paste(half, (0, 0))
carpet.paste(half.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (1024, 0))
assert np.array_equal(np.asarray(carpet)[:, 1023], np.asarray(carpet)[:, 1024])
export("carpt01", carpet, [half_info], construction="symmetric carpet demo assembled from a fresh half and its mirror",
       limitation="native asymmetrical wear is not reproduced; ornament is a candidate reinterpretation")

context = []
mount = stage / "x4/assets_dev"
if not mount.exists():
    shutil.copytree(original, mount, copy_function=os.link)
target_dir = mount / "worlds/mm6/textures_x4"
assert not (original / "worlds/mm6/textures_x4").exists(), "Do not write through hard links to a frozen tier"
target_dir.mkdir(exist_ok=True)
changed = {row["name"] for row in selected}
names = set(native) | {"orwtrtyl", "sky_nit2"}
for name in sorted(names):
    baseline = original / "worlds/mm6/textures_x2" / (name + ".png")
    if name in native:
        assert digest(baseline) == native[name]["before_sha256"], (name, "baseline changed")
        assert digest(base / "runtime" / (name + ".png")) == native[name]["runtime_sha256"], name
    if name in changed:
        shutil.copy2(output / (name + ".png"), target_dir / (name + ".png"))
    elif baseline.exists():
        # ponytail: context-only pixel duplication satisfies uniform tier scaling; replace with per-file tier support
        # for a shipped mixed-resolution pack. These files are expressly not regenerated or accepted 4x artwork.
        image = Image.open(baseline).convert("RGBA")
        carrier = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        assert np.array_equal(np.asarray(carrier)[::2, ::2], np.asarray(image)), name
        carrier.save(target_dir / (name + ".png"))
        context.append({"name": name, "source": "current ESRGAN 2x; context only", "source_sha256": digest(baseline),
                        "carrier_size": list(carrier.size), "carrier_sha256": digest(target_dir / (name + ".png"))})

for row in selected:
    for label, path in [("esrgan", original / "worlds/mm6/textures_x2" / (row["name"] + ".png")),
                        ("candidate", output / (row["name"] + ".png"))]:
        image = Image.open(path).convert("RGB")
        tile = reduce(image, tuple(value * 2 for value in row["native_size"]))
        repeat = Image.new("RGB", (tile.width * 3, tile.height * 3))
        for y in range(3):
            for x in range(3):
                repeat.paste(tile, (x * tile.width, y * tile.height))
        repeat.save(review / (row["name"] + "_" + label + "_repeat.png"))

source_receipt = json.loads((base / "captures/full_before.run.json").read_text())
settings_path = Path(source_receipt["run_directory"]) / "launch-settings.ini"
assert settings_path.exists(), "Frozen baseline settings required"
settings = configparser.ConfigParser(interpolation=None)
settings.read(settings_path)
settings["startup"]["save_file"] = ""
settings["debug"]["screenshot_tour_path"] = ""
settings["assets"]["root"] = str(original)
with (base / "references/demo_x4_settings.ini").open("w") as stream:
    settings.write(stream)

manifest = {"map": "6d02.blv", "scope": "12 focused 4x candidate textures; other surfaces retain ESRGAN artwork",
            "selected": selected, "context_only": context, "stage": str(mount),
            "binary_sha256": digest(stage / "openyamm"),
            "map_sha256": digest(original / "worlds/mm6/maps/6d02.blv"),
            "status": "exported_for_native_visual_review", "production_changed": False}
(base / "demo_x4_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
assert len(selected) == 12
print("Exported 12 true 4x candidates; shared backgrounds, crop budgets and production baselines verified.")
print("Context-only ESRGAN carriers:", len(context))
print("Stage:", mount)
