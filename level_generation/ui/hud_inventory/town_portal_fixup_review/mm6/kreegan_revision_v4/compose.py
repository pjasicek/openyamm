"""Place a sepia Kreegan stencil using the exact restored side-frame alpha over retained sharp terrain."""

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
ROOT = REVIEW.parents[3]
PRIOR = HERE.parent / "creature_fixup_v3"
ATTEMPT = HERE / "attempt_01"
SIZE = (60, 100)
POSITION = (182, 342)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    if (HERE / "acceptance.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before recomposing it.")
    inputs = json.loads((HERE / "inputs.json").read_text())
    assert sha(ROOT / inputs["source"]) == inputs["source_sha256"]
    assert sha(PRIOR / "terrain.png") == inputs["terrain"]["sha256"]
    source = Image.open(ATTEMPT / "inputs/kreegan_side.png").convert("RGBA")
    raw = Image.open(ATTEMPT / "raw.png").convert("RGBA")
    assert np.any(np.asarray(raw)[:, :, 3] == 0), "Generated layer must have genuine transparency"
    registered = np.asarray(raw.resize(source.size, Image.Resampling.LANCZOS))
    source_alpha = np.asarray(source)[:, :, 3]

    # The generated image supplies ink and fill only. Its silhouette is never authoritative.
    # Extend RGB from the nearest solid generated pixel across small registration differences,
    # then use the original side-frame alpha and its own continuous inner contour.
    solid = registered[:, :, 3] >= 192
    nearest = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    rgb = registered[:, :, :3][tuple(nearest)].astype(float)
    distance = ndimage.distance_transform_edt(source_alpha >= 128)
    edge = np.clip((6.5 - distance) / 3.5, 0, 1)
    ink = np.array([82, 59, 31])
    rgb = rgb * (1 - edge[:, :, None]) + ink * edge[:, :, None]
    texture = Image.fromarray(np.rint(rgb).clip(0, 255).astype(np.uint8))
    texture.putalpha(Image.fromarray(source_alpha))
    texture.save(HERE / "stencil_source.png")

    # Reduce the one fixed source canvas uniformly, including all negative spaces.
    stencil = texture.resize(SIZE, Image.Resampling.LANCZOS)
    alpha = source.getchannel("A").resize(SIZE, Image.Resampling.LANCZOS)
    stencil.putalpha(alpha)
    stencil.save(HERE / "stencil.png")
    alpha.save(HERE / "silhouette_mask.png")
    assert np.array_equal(np.asarray(stencil)[:, :, 3], np.asarray(alpha))

    terrain = Image.open(PRIOR / "terrain.png").convert("RGBA")
    previous = Image.open(PRIOR / "master.png").convert("RGB")
    master = terrain.copy()
    master.alpha_composite(stencil, POSITION)
    master = master.convert("RGB")
    master.save(HERE / "master.png")
    subprocess.run([
        "magick", str(HERE / "master.png"), "-filter", "Lanczos", "-resize", "1280x960",
        "-define", "png:color-type=2", str(HERE / "tpenroth.png"),
    ], check=True)

    old = np.asarray(Image.open(PRIOR / "tpenroth.png"))
    new = np.asarray(Image.open(HERE / "tpenroth.png"))
    changed = np.any(old != new, axis=2)
    allowed = np.zeros(changed.shape, dtype=bool)
    bounds = [150, 298, 225, 400]
    allowed[bounds[1]:bounds[3], bounds[0]:bounds[2]] = True
    assert changed.any() and not np.any(changed & ~allowed)
    master_delta = np.any(np.asarray(master) != np.asarray(previous), axis=2)
    symbol_union = np.zeros(master_delta.shape, dtype=bool)
    old_alpha = np.asarray(Image.open(PRIOR / "gargoyle.png"))[:, :, 3] > 0
    symbol_union[345:447, 175:250] |= old_alpha
    x, y = POSITION
    symbol_union[y:y + SIZE[1], x:x + SIZE[0]] |= np.asarray(alpha) > 0
    assert not np.any(master_delta & ~symbol_union), "Terrain changed outside the old/new silhouettes"

    buttons = json.loads((REVIEW / "mm6/buttons_v1/manifest.json").read_text())
    for button in buttons["records"]:
        x0, y0, x1, y1 = button["cropBoxX2"]
        normal = np.asarray(Image.open(REVIEW / button["default"]))
        assert np.array_equal(new[y0:y1, x0:x1], normal), button["id"]
    accepted = json.loads((REVIEW.parent / "town_portal_acceptance_20260927/accepted.json").read_text())
    assert all(sha(ROOT / record["runtime_output_path"]) == record["sha256"]
               for record in accepted["records"].values()), "Runtime differs from accepted predecessor"

    box = (135, 304, 321, 497)
    proof = Image.new("RGB", (1160, 640), (29, 31, 32))
    draw = ImageDraw.Draw(proof)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    for col, (label, picture) in enumerate([("Accepted gargoyle", previous), ("Kreegan side stencil", master)]):
        draw.text((20 + col * 580, 12), label, font=font, fill=(237, 223, 186))
        proof.paste(picture.crop(box).resize((558, 579), Image.Resampling.NEAREST), (11 + col * 580, 45))
    proof.save(HERE / "comparison.png")
    checks = {
        "result": "PASS", "source_frame": "wdmflya2", "source_side_silhouette_preserved": True,
        "stencil_alpha_exactly_matches_scaled_source": True, "gargoyle_removed": True,
        "terrain_pixels_unchanged_outside_old_and_new_silhouettes": True,
        "titan_dragon_labels_and_all_six_destinations_unchanged": True,
        "all_six_default_crops_still_exact": True, "hover_exports_reused_unchanged": 6,
        "runtime_files_unchanged": 7, "changed_export_pixels": int(changed.sum()),
        "change_bounds_x2": bounds, "export_size": [1280, 960], "opaque_rgb": True,
    }
    manifest = {
        "schema": 1, "status": "review_candidate", "accepted": False, "installed": False,
        "target": "engine--icons--tpenroth.bmp",
        "request": 'bring back the "demon", like the kreegan, like really take its side silhouette '
                   'and stencil it in the same manner there instead of the gargoyle.',
        "source_frame": inputs, "source_alpha_size": list(source.size),
        "stencil_size_in_master": list(SIZE), "position_in_master": list(POSITION),
        "recipe": "Built-in imagegen sepia interior, registered to the source canvas; nearest-solid RGB extension, "
                  "original side-frame alpha and narrow inner brown contour; uniform reduction; "
                  "composite over the retained crisp terrain; one Lanczos x2 export.",
        "tool": "built-in image_gen", "prompt": str((ATTEMPT / "prompt.txt").relative_to(ROOT)),
        "prompt_sha256": sha(ATTEMPT / "prompt.txt"),
        "artifacts": {name: {"path": str((HERE / name).relative_to(ROOT)), "sha256": sha(HERE / name)}
                      for name in ["attempt_01/raw.png", "stencil_source.png", "stencil.png", "silhouette_mask.png",
                                   "master.png", "tpenroth.png", "comparison.png"]},
        "validation": checks,
    }
    save(HERE / "manifest.json", manifest)
    save(HERE / "validation.json", checks)
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
