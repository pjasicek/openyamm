#!/usr/bin/env python3
"""MM9's painted map screens at 2x, by the MM7/MM8 minimap recipe the user approved on 2026-09-28
(../esrgan_study_20260928/README.md): realesr-animevideov3, direct 2x, full strength, no blend.

    python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py prepare   # originals and padded inputs
    python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py run       # Real-ESRGAN on the GPU
    python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py finish    # crop, checks, contact sheets
    python3 -B level_generation/minimaps/mm9_esrgan_20261109/upscale.py install   # PNGs into assets_dev + review roots

Sources are the original MM9 PCX files (mm9/extracted/.../MAPSCREENS/MAPS), never a generated map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "mm9/extracted/ART/ART/INTERFACESCREENS/MAPSCREENS/MAPS"
BINARY = ROOT / "tools/upscaling/realesrgan-ncnn-vulkan"
MODELS = ROOT / "tools/upscaling/models"
MODEL = "realesr-animevideov3"
SCALE = 2
PAD = 16                                    # reflected native pixels on every edge, removed after inference
# The installed map images: assets_dev and the two MM9 review roots (AGENTS.md, MM9 map Lua and scenes).
TARGETS = [ROOT / "assets_dev/worlds/mm9/ui/maps",
           ROOT / "output/mm9_rework/assets_dev/worlds/mm9/ui/maps",
           ROOT / "output/mm9_rework/isleofashes_blv_root/worlds/mm9/ui/maps"]
# Kluso's House exists twice in the archive; MM9's map screen and the catalog use KLUSOSHOUSE*, KLUSOHOUSE* is unused.
UNUSED = {"klusohousea", "klusohouseb"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources() -> list[Path]:
    return sorted(p for p in SOURCE.glob("*.pcx") if p.stem.lower() not in UNUSED)


def prepare() -> None:
    (HERE / "original").mkdir(exist_ok=True)
    (HERE / "input").mkdir(exist_ok=True)
    records = []
    for path in sources():
        stem = path.stem.lower()
        image = Image.open(path).convert("RGB")
        image.save(HERE / "original" / f"{stem}.png")
        padded = np.pad(np.asarray(image), ((PAD, PAD), (PAD, PAD), (0, 0)), mode="reflect")
        Image.fromarray(padded).save(HERE / "input" / f"{stem}.png")
        records.append({"map": stem, "source": str(path.relative_to(ROOT)), "source_sha256": sha(path),
                        "width": image.width, "height": image.height})
    (HERE / "sources.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"{len(records)} maps prepared")


def run() -> None:
    (HERE / "raw").mkdir(exist_ok=True)
    command = [str(BINARY), "-i", str(HERE / "input"), "-o", str(HERE / "raw"), "-n", MODEL, "-s", str(SCALE),
               "-m", str(MODELS), "-g", "0", "-j", "1:1:1", "-t", "0", "-f", "png"]
    (HERE / "command.txt").write_text(" ".join(command) + "\n")
    subprocess.check_call(command)


def finish() -> None:
    (HERE / "x2").mkdir(exist_ok=True)
    (HERE / "contacts").mkdir(exist_ok=True)
    records = json.loads((HERE / "sources.json").read_text())
    for record in records:
        stem = record["map"]
        raw = Image.open(HERE / "raw" / f"{stem}.png").convert("RGB")
        crop = PAD * SCALE
        result = raw.crop((crop, crop, raw.width - crop, raw.height - crop))
        size = (record["width"] * SCALE, record["height"] * SCALE)
        if result.size != size:
            raise ValueError(f"{stem}: {result.size} is not {size}")
        result.save(HERE / "x2" / f"{stem}.png", optimize=True)

        # Registration: the result reduced to native size against the original, smoothed, at shifts of -2..2 px.
        original = np.asarray(Image.open(HERE / "original" / f"{stem}.png"), dtype=np.float32).mean(axis=2)
        reduced = np.asarray(result.resize((record["width"], record["height"]), Image.LANCZOS),
                             dtype=np.float32).mean(axis=2)
        a, b = gaussian_filter(original, 1.5), gaussian_filter(reduced, 1.5)
        errors = {}
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                shifted = np.roll(np.roll(b, dy, axis=0), dx, axis=1)
                errors[(dx, dy)] = float(np.abs(a[4:-4, 4:-4] - shifted[4:-4, 4:-4]).mean())
        best = min(errors, key=errors.get)
        record.update({"x2_width": size[0], "x2_height": size[1], "x2_sha256": sha(HERE / "x2" / f"{stem}.png"),
                       "best_shift": list(best), "mean_error": round(errors[(0, 0)], 3)})
        if best != (0, 0):
            raise ValueError(f"{stem}: the 2x image is shifted by {best} against the original")

        # Contact sheet: a 256 px native crop around the image's darkest structure, nearest 2x against the result.
        lines = gaussian_filter((original < original.mean() - 40).astype(np.float32), 24)
        cy, cx = np.unravel_index(np.argmax(lines), lines.shape)
        x0 = int(np.clip(cx - 128, 0, max(0, record["width"] - 256)))
        y0 = int(np.clip(cy - 96, 0, max(0, record["height"] - 192)))
        box = (x0, y0, min(record["width"], x0 + 256), min(record["height"], y0 + 192))
        native = Image.open(HERE / "original" / f"{stem}.png").crop(box)
        native = native.resize((native.width * 2, native.height * 2), Image.NEAREST)
        upscaled = result.crop(tuple(v * 2 for v in box))
        sheet = Image.new("RGB", (native.width * 2 + 8, native.height), (40, 40, 40))
        sheet.paste(native, (0, 0))
        sheet.paste(upscaled, (native.width + 8, 0))
        sheet.save(HERE / "contacts" / f"{stem}.png")
    (HERE / "results.json").write_text(json.dumps({"model": MODEL, "scale": SCALE, "pad": PAD,
                                                   "binary_sha256": sha(BINARY), "maps": records}, indent=2) + "\n")
    print(f"{len(records)} maps at 2x, all registered at zero shift")


def install() -> None:
    records = json.loads((HERE / "results.json").read_text())["maps"]
    for target in TARGETS:
        for record in records:
            stem = record["map"]
            shutil.copyfile(HERE / "x2" / f"{stem}.png", target / f"{stem}.png")
            (target / f"{stem}.png").chmod(0o644)
            # The native PCX is replaced: the catalog names the PNG and the originals stay in mm9/extracted.
            (target / f"{stem}.pcx").unlink(missing_ok=True)
        print(f"{target.relative_to(ROOT)}: {len(records)} PNGs")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["prepare", "run", "finish", "install"])
    step = parser.parse_args().step
    {"prepare": prepare, "run": run, "finish": finish, "install": install}[step]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
