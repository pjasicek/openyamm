"""Finish the local Real-ESRGAN Body Magic spellbook page at exact 2x."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]
ORIGINAL = REVIEW / "originals/engine--icons--sbb000.bmp.png"
SOURCE = ROOT / "assets_dev/engine/icons/sbb000.bmp"
MASTER = HERE / "sbb000-x4-master.png"
CANDIDATE = HERE / "sbb000-x2.png"
MODEL_DIRECTORY = ROOT / "tools/upscaling/models"
BINARY = ROOT / "tools/upscaling/realesrgan-ncnn-vulkan"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with Image.open(ORIGINAL) as image:
        if image.size != (640, 480) or image.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError("Body Magic source is not the expected opaque 640x480 page")
    with Image.open(MASTER) as image:
        if image.size != (2560, 1920) or image.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError("Real-ESRGAN master is not the expected opaque 4x page")
        result = image.convert("RGB").resize((1280, 960), Image.Resampling.LANCZOS)
    result.save(CANDIDATE, optimize=True)
    pixels = np.asarray(result, dtype=np.float32)
    red, green, blue = [pixels[:, :, channel] for channel in range(3)]
    magenta = (red > 70) & (blue > 70) & (red > green * 1.35) & (blue > green * 1.35)
    magenta[3:-3, 3:-3] = False
    if np.any(magenta):
        raise ValueError("Purple key color reached the finished page edge")
    manifest = {
        "schema": 1,
        "method": "Real-ESRGAN x4plus inference on the complete native rendered page; Pillow Lanczos 4x-to-2x",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": digest(SOURCE),
        "native_rendered_png": ORIGINAL.relative_to(ROOT).as_posix(),
        "native_rendered_sha256": digest(ORIGINAL),
        "binary": BINARY.relative_to(ROOT).as_posix(),
        "binary_sha256": digest(BINARY),
        "model": "realesrgan-x4plus",
        "model_bin_sha256": digest(MODEL_DIRECTORY / "realesrgan-x4plus.bin"),
        "model_param_sha256": digest(MODEL_DIRECTORY / "realesrgan-x4plus.param"),
        "inference_options": {"scale": 4, "tile_size": 128, "gpu": "auto; llvmpipe software Vulkan device"},
        "master": MASTER.relative_to(ROOT).as_posix(),
        "master_sha256": digest(MASTER),
        "master_size": [2560, 1920],
        "candidate": CANDIDATE.relative_to(ROOT).as_posix(),
        "candidate_sha256": digest(CANDIDATE),
        "candidate_size": [1280, 960],
        "outer_three_pixel_magenta": 0,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Finished sbb000 exact 2x candidate: {manifest['candidate_sha256']}")


if __name__ == "__main__":
    main()
