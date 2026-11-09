#!/usr/bin/env python3
"""Export the requested local repairs without repainting the rest of either map."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG = {
    "mm8": ("townport", "attempt_03", [
        (82, 111, 194, 190), (68, 264, 157, 359), (35, 612, 156, 738),
        (632, 544, 774, 700), (965, 27, 1026, 118), (948, 626, 1055, 713),
    ]),
    "mm7": ("antagrich", "attempt_01", [
        (113, 748, 264, 879), (450, 548, 527, 650), (1008, 733, 1107, 792),
    ]),
}


def artifact(path):
    return {"path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", choices=CONFIG)
    args = parser.parse_args()
    name, previous, boxes = CONFIG[args.world]
    world = HERE / args.world
    out = world / "details_20261004"
    base = world / previous / (name + ".png")
    raw = out / "raw.png"
    final = out / (name + ".png")
    assert not final.exists(), "Keep previous exports; create a new revision for another repair."
    with Image.open(raw) as master:
        assert master.width >= 1280 and master.height >= 960
        assert abs(master.width / master.height - 4 / 3) < 0.002
        master_size = list(master.size)
    shutil.copyfile(base, out / "inputs/before.png")
    subprocess.run(["magick", str(raw), "-filter", "Lanczos", "-resize", "1280x960",
                    "-alpha", "off", "-depth", "8", str(out / "resized.png")], check=True)
    for kind, inset, blur in [("support", 0, False), ("feather", 6, True)]:
        draw = " ".join(f"rectangle {x + inset},{y + inset} {r - inset - 1},{b - inset - 1}"
                        for x, y, r, b in boxes)
        command = ["magick", "-size", "1280x960", "xc:black", "-fill", "white", "-draw", draw]
        if blur:
            command += ["-blur", "0x3"]
        subprocess.run(command + ["-depth", "8", str(out / (kind + ".png"))], check=True)
    subprocess.run(["magick", str(out / "feather.png"), str(out / "support.png"),
                    "-compose", "Multiply", "-composite", str(out / "repair_mask.png")], check=True)
    subprocess.run(["magick", str(base), str(out / "resized.png"), str(out / "repair_mask.png"),
                    "-compose", "Over", "-composite", "-alpha", "off", "-depth", "8",
                    "-define", "png:color-type=2", str(final)], check=True)
    pit_raw = out / "pit_raw.png"
    if args.world == "mm7" and pit_raw.exists():
        shutil.copyfile(final, out / "first_pass.png")
        subprocess.run(["magick", str(pit_raw), "-filter", "Lanczos", "-resize", "162x140!",
                        "-alpha", "off", "-depth", "8", str(out / "pit_resized.png")], check=True)
        subprocess.run(["magick", str(final), str(out / "pit_resized.png"),
                        "-geometry", "+110+740", "-compose", "Over", "-composite",
                        str(out / "pit_canvas.png")], check=True)
        subprocess.run(["magick", "-size", "1280x960", "xc:black", "-fill", "white",
                        "-draw", "rectangle 119,754 257,872", "-blur", "0x3",
                        str(out / "pit_mask.png")], check=True)
        subprocess.run(["magick", str(out / "pit_mask.png"), str(out / "support.png"),
                        "-compose", "Multiply", "-composite", "-depth", "8",
                        str(out / "pit_mask.png")], check=True)
        subprocess.run(["magick", str(out / "first_pass.png"), str(out / "pit_canvas.png"),
                        str(out / "pit_mask.png"), "-compose", "Over", "-composite",
                        "-alpha", "off", "-depth", "8", "-define", "png:color-type=2", str(final)], check=True)
    original = np.asarray(Image.open(base).convert("RGB"))
    pixels = np.asarray(Image.open(final).convert("RGB"))
    support = np.asarray(Image.open(out / "support.png").convert("L")) > 0
    changed = np.any(original != pixels, axis=2)
    assert pixels.shape == (960, 1280, 3)
    assert not np.any(changed & ~support), "Unrequested map pixels changed."
    assert changed.any()

    spec = importlib.util.spec_from_file_location("portal_buttons", world / "prepare_buttons.py")
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    buttons = out / "buttons"
    for folder in ["default", "hover", "masks"]:
        (buttons / folder).mkdir(parents=True, exist_ok=True)
    records = []
    map_image = Image.open(final).convert("RGB")
    for item in recipe.destinations():
        icon = item["id"]
        x, y, w, h = (item["rect"][key] for key in ["x", "y", "width", "height"])
        crop = map_image.crop((2 * x, 2 * y, 2 * (x + w), 2 * (y + h)))
        hover, mask = recipe.highlight(crop, recipe.CENTERS[icon])
        for folder, image in [("default", crop), ("hover", hover), ("masks", mask)]:
            image.save(buttons / folder / (icon + ".png"))
        delta = np.any(np.asarray(crop) != np.asarray(hover), axis=2)
        assert delta.any()
        assert not delta[:4].any() and not delta[-4:].any()
        assert not delta[:, :4].any() and not delta[:, -4:].any()
        assert not np.any(delta & (np.asarray(mask) == 0))
        records.append({**item, "exports": {
            folder: artifact(buttons / folder / (icon + ".png"))
            for folder in ["default", "hover", "masks"]}})
    report = {
        "status": "review_candidate", "tool": "built-in image_gen.imagegen",
        "base": artifact(base), "raw": artifact(raw), "raw_size": master_size,
        "export": artifact(final), "export_size": [1280, 960],
        "prompt": artifact(out / "prompt.txt"), "tool_args": artifact(out / "tool_args.json"),
        "processing": "Uniform Lanczos downscale; local ImageMagick mask composite onto retained map.",
        "regions_x2": boxes, "repair_mask": artifact(out / "repair_mask.png"),
        "button_recipe": artifact(world / "prepare_buttons.py"), "buttons": records,
        "validation": {"result": "PASS", "changed_pixels": int(changed.sum()),
                       "unchanged_outside_repairs": True, "opaque_rgb": True,
                       "native_size": [640, 480], "destinations": len(records),
                       "exact_map_crops": True, "unchanged_hover_borders": True},
        "installed": False,
    }
    if args.world == "mm7" and pit_raw.exists():
        report["pit_refinement"] = {
            "raw": artifact(pit_raw), "prompt": artifact(out / "pit_prompt.txt"),
            "tool_args": artifact(out / "pit_tool_args.json"),
            "previous_export": artifact(out / "first_pass.png"), "mask": artifact(out / "pit_mask.png"),
            "crop_box_x2": [110, 740, 272, 880],
        }
    (out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    for path in out.rglob("*.png"):
        path.chmod(0o644)
    print(json.dumps(report["validation"]))


if __name__ == "__main__":
    main()
