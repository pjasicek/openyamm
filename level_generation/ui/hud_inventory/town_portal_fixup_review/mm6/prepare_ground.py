#!/usr/bin/env python3
"""Restore crisp terrain and keep the approved gargoyle as a separate pixel cutout."""

import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

from prepare_creature_fixup import digest, region_mask


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE / "creature_fixup_v3"


def main():
    if (HERE.parents[1] / "town_portal_acceptance_20260927/accepted.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before preparing new artwork.")
    OUT.mkdir(exist_ok=True)
    previous = Image.open(HERE / "creature_fixup_v2/master.png").convert("RGB")
    original = Image.open(HERE / "attempt_01/raw.png").convert("RGB")
    ground = Image.open(HERE / "attempt_07/raw.png").convert("RGB")
    ground = ground.resize((220, 220), Image.Resampling.LANCZOS)

    # The surrounding ground comes directly from the first approved sharp map.
    # Only the original creature's old footprint needs newly reconstructed terrain.
    restore_box = (174, 328, 295, 450)
    terrain = previous.copy()
    terrain.paste(original.crop(restore_box), restore_box[:2])
    plate = terrain.copy()
    plate.paste(ground, (125, 280))
    old_figure_box = (210, 346, 284, 444)
    ground_mask = region_mask(terrain.size, old_figure_box, 4)
    terrain = Image.composite(plate, terrain, ground_mask)
    terrain.save(OUT / "terrain.png")
    ground_mask.save(OUT / "terrain_repair_mask.png")

    # Extract the existing brown stencil; do not ask imagegen to redraw its silhouette.
    crop_box = (175, 345, 250, 447)
    sprite = previous.crop(crop_box)
    rgb = np.asarray(sprite)
    luma = rgb @ np.array([0.2126, 0.7152, 0.0722])
    yy, xx = np.mgrid[:sprite.height, :sprite.width]
    enclosure = (xx >= 8) & (xx <= 68) & (yy >= 2) & (yy <= 99)
    labels, count = ndimage.label((luma < 170) & enclosure)
    assert count > 0
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    ink = labels == int(areas.argmax())
    support = ndimage.binary_dilation(ink, iterations=1) & enclosure
    opacity = np.clip((188 - luma) / 18, 0, 1) * support
    # Warm interior fills enclosed by the outline remain solid; genuine light gaps stay open.
    interior = ndimage.binary_fill_holes(ink) & (luma < 182)
    opacity[interior] = 1
    alpha = np.rint(opacity * 255).astype(np.uint8)
    layer = Image.fromarray(np.dstack([rgb, alpha]))
    layer.save(OUT / "gargoyle.png")
    Image.fromarray(alpha).save(OUT / "gargoyle_mask.png")
    master_image = terrain.copy()
    master_image.paste(layer, crop_box[:2], layer.getchannel("A"))
    master = OUT / "master.png"
    master_image.save(master)
    export = OUT / "tpenroth.png"
    subprocess.run([
        "magick", str(master), "-filter", "Lanczos", "-resize", "1280x960",
        "-define", "png:color-type=2", str(export),
    ], check=True)

    solid = alpha == 255
    final_crop = np.asarray(master_image.crop(crop_box))
    assert np.array_equal(final_crop[solid], rgb[solid]), "The approved stencil was recolored"
    assert np.array_equal(np.asarray(layer)[..., :3], rgb), "The foreground pixels were redrawn"
    before = np.asarray(Image.open(HERE / "creature_fixup_v2/tpenroth.png"))
    after = np.asarray(Image.open(export))
    changed = np.any(before != after, axis=2)
    allowed_box = (149, 285, 266, 403)
    allowed = np.zeros(changed.shape, dtype=bool)
    allowed[allowed_box[1]:allowed_box[3], allowed_box[0]:allowed_box[2]] = True
    assert not (changed & ~allowed).any()

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    detail_box = (150, 305, 320, 475)
    proof = Image.new("RGB", (1020, 555), (27, 31, 36))
    draw = ImageDraw.Draw(proof)
    for i, (title, picture) in enumerate([("Previous blurred ground", previous),
                                         ("Restored terrain + retained gargoyle", master_image)]):
        proof.paste(picture.crop(detail_box).resize((510, 510), Image.Resampling.NEAREST), (i * 510, 45))
        draw.text((i * 510 + 12, 12), title, fill=(239, 226, 199), font=font)
    proof.save(OUT / "comparison.png")
    inputs = [HERE / "creature_fixup_v2/master.png", HERE / "attempt_01/raw.png", HERE / "attempt_07/raw.png"]
    manifest = {
        "schema": 1, "target": "engine--icons--tpenroth.bmp", "status": "review_candidate",
        "scope": "Restore crisp terrain behind the approved gargoyle using separate terrain and foreground layers",
        "accepted_in_ledger": False, "installed": False, "logical_size": [640, 480], "export_size": [1280, 960],
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in inputs],
        "layers": {"restored_original_box": list(restore_box), "generated_ground_box": list(old_figure_box),
                   "gargoyle_box": list(crop_box), "foreground_method": "Connected brown ink and enclosed fills; "
                   "one-pixel luminance antialias edge; unchanged source RGB; no resize or translation"},
        "master": {"path": str(master.relative_to(ROOT)), "sha256": digest(master), "size": [1448, 1086]},
        "export": {"path": str(export.relative_to(ROOT)), "sha256": digest(export)},
        "validation": {"result": "PASS", "changed_pixels": int(changed.sum()),
                       "change_bounds_x2": list(allowed_box), "all_other_map_pixels_identical": True,
                       "foreground_rgb_unchanged": True, "solid_gargoyle_pixels_identical": True,
                       "gargoyle_position_and_scale_unchanged": True,
                       "titan_dragon_and_destinations_unchanged": True, "opaque_rgb": True},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["validation"], indent=2))


if __name__ == "__main__":
    main()
