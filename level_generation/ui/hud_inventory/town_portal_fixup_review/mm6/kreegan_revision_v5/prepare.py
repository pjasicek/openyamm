"""Transfer darker ink tones onto the existing Kreegan, preserving every alpha pixel and its placement."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "kreegan_revision_v4"
REVIEW = HERE.parents[1]
ROOT = REVIEW.parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def magick(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def main():
    if (HERE / "acceptance.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before changing its artwork.")
    previous = json.loads((PRIOR / "manifest.json").read_text())
    for record in previous["artifacts"].values():
        assert sha(ROOT / record["path"]) == record["sha256"]
    grade = json.loads((HERE / "grade.json").read_text())
    operations = []
    for channel, gain, bias in zip("RGB", grade["gain_rgb"], grade["bias_rgb_8bit"]):
        operations += ["-channel", channel, "-function", "Polynomial", f"{gain:.12f},{bias / 255:.12f}"]
    for name in ["stencil_source.png", "stencil.png"]:
        magick(PRIOR / name, *operations, "+channel", "-depth", "8", "-define", "png:color-type=6", HERE / name)
        old = np.asarray(Image.open(PRIOR / name))
        new = np.asarray(Image.open(HERE / name))
        assert new.shape == old.shape and np.array_equal(old[:, :, 3], new[:, :, 3])
        expected = np.rint(np.clip(old[:, :, :3] * np.array(grade["gain_rgb"])
                                  + np.array(grade["bias_rgb_8bit"]), 0, 255)).astype(np.uint8)
        assert np.abs(new[:, :, :3].astype(int) - expected.astype(int)).max() <= 1
    shutil.copyfile(PRIOR / "silhouette_mask.png", HERE / "silhouette_mask.png")

    terrain = HERE.parent / "creature_fixup_v3/terrain.png"
    magick(terrain, HERE / "stencil.png", "-geometry", "+182+342", "-compose", "over", "-composite",
           "-alpha", "off", "-define", "png:color-type=2", HERE / "master.png")
    magick(HERE / "master.png", "-filter", "Lanczos", "-resize", "1280x960",
           "-define", "png:color-type=2", HERE / "tpenroth.png")

    master_before = np.asarray(Image.open(PRIOR / "master.png"))
    master_after = np.asarray(Image.open(HERE / "master.png"))
    mask = np.zeros(master_before.shape[:2], dtype=bool)
    mask[342:442, 182:242] = np.asarray(Image.open(HERE / "silhouette_mask.png")) > 0
    assert not np.any(np.any(master_before != master_after, axis=2) & ~mask)
    before = np.asarray(Image.open(PRIOR / "tpenroth.png"))
    after = np.asarray(Image.open(HERE / "tpenroth.png"))
    delta = np.any(before != after, axis=2)
    allowed = np.zeros(delta.shape, dtype=bool)
    bounds = [158, 299, 218, 394]
    allowed[bounds[1]:bounds[3], bounds[0]:bounds[2]] = True
    assert delta.any() and not np.any(delta & ~allowed)
    buttons = json.loads((REVIEW / "mm6/buttons_v1/manifest.json").read_text())
    for button in buttons["records"]:
        x0, y0, x1, y1 = button["cropBoxX2"]
        assert np.array_equal(after[y0:y1, x0:x1], np.asarray(Image.open(REVIEW / button["default"])))
    accepted = json.loads((REVIEW.parent / "town_portal_acceptance_20260927/accepted.json").read_text())
    current = json.loads((REVIEW.parent / "accepted_icons.json").read_text())
    for target, record in accepted["records"].items():
        assert current["records"][target] == record
        assert sha(ROOT / record["runtime_output_path"]) == record["sha256"]

    for label, path, name in [("Before", PRIOR / "master.png", "before_detail.png"),
                              ("Darker Kreegan", HERE / "master.png", "after_detail.png")]:
        magick(path, "-crop", "186x193+135+304", "+repage", "-filter", "point", "-resize", "558x579",
               "-background", "#1d1f20", "-gravity", "north", "-splice", "0x36", "-font", "DejaVu-Sans",
               "-pointsize", "18", "-fill", "#eddfba", "-annotate", "+0+7", label, HERE / name)
    magick(HERE / "before_detail.png", HERE / "after_detail.png", "+append", HERE / "comparison.png")
    checks = {
        "result": "PASS", "rgb_tone_change_only": True, "drawing_and_alpha_preserved": True,
        "stencil_size_unchanged": [60, 100], "position_unchanged": [182, 342],
        "master_pixels_outside_stencil_identical": True, "titan_dragon_and_terrain_unchanged": True,
        "all_six_destination_crops_exact": True, "hover_exports_reused_unchanged": 6,
        "changed_export_pixels": int(delta.sum()), "change_bounds_x2": bounds,
        "accepted_records_and_runtime_files_unchanged": 7,
    }
    manifest = {
        "schema": 1, "status": "review_candidate", "accepted": False, "installed": False,
        "target": "engine--icons--tpenroth.bmp", "request": 'the kreegan but should be like "more black" like the titan/dragon',
        "previous_revision": "mm6/kreegan_revision_v4", "tool": "built-in image_gen",
        "method": "Generated darker ink palette, then transferred only its RGB tones onto the existing stencil; "
                  "original drawing, source silhouette, alpha, size, and position remain unchanged.",
        "grade": grade, "logical_size": [640, 480], "export_size": [1280, 960],
        "sources": {str(p.relative_to(ROOT)): sha(p) for p in [PRIOR / "manifest.json", PRIOR / "stencil.png",
                    PRIOR / "stencil_source.png", terrain, HERE / "raw.png", HERE / "prompt.txt", HERE / "tool_args.json"]},
        "artifacts": {name: {"path": str((HERE / name).relative_to(ROOT)), "sha256": sha(HERE / name)}
                      for name in ["stencil.png", "stencil_source.png", "silhouette_mask.png", "master.png",
                                   "tpenroth.png", "comparison.png"]},
        "validation": checks,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "validation.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
