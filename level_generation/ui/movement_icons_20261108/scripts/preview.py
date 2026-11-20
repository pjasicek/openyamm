"""Contact sheet (native 2x nearest, current HD, new HD) and animated GIF previews at game pace.

python3 preview.py fly|waterwalk|levitate
"""
import sys

import numpy as np
from PIL import Image

from common import FRAME_SECONDS, HD_DIR, NATIVE_DIR, OUT_DIR, PREVIEW_DIR

SETS = {
    "fly": ("fly", [f"sp21a{k}0" for k in range(1, 9)]),
    "waterwalk": ("waterwalk", [f"sp27a{k}0" for k in range(1, 9)]),
    "levitate": ("levitate", [f"sp109-0{k}" for k in range(1, 7)]),
}
BACKGROUND = (22, 24, 30, 255)


def on_background(image, size):
    bg = Image.new("RGBA", image.size, BACKGROUND)
    bg.alpha_composite(image)
    return bg.resize(size, Image.NEAREST if size[0] <= image.size[0] * 3 else Image.LANCZOS)


def native_rgba(name):
    im = Image.open(NATIVE_DIR / f"{name}.bmp")
    idx = np.asarray(im)
    rgba = np.asarray(im.convert("RGBA")).copy()
    rgba[idx == 0] = 0
    return Image.fromarray(rgba, "RGBA")


def main():
    key = sys.argv[1]
    folder, names = SETS[key]
    new = [Image.open(OUT_DIR / folder / f"{n}.png").convert("RGBA") for n in names]
    native = [native_rgba(n) for n in names]
    current = []
    for n in names:
        path = HD_DIR / f"{n}.png"
        current.append(Image.open(path).convert("RGBA") if path.exists() else Image.new("RGBA", (128, 128)))
    cell = 192
    sheet = Image.new("RGBA", (cell * len(names), cell * 3), BACKGROUND)
    for i in range(len(names)):
        sheet.alpha_composite(on_background(native[i].resize((128, 128), Image.NEAREST), (cell, cell)), (i * cell, 0))
        sheet.alpha_composite(on_background(current[i], (cell, cell)), (i * cell, cell))
        sheet.alpha_composite(on_background(new[i], (cell, cell)), (i * cell, 2 * cell))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(PREVIEW_DIR / f"{key}_sheet.png")
    duration = int(round(FRAME_SECONDS * 1000))
    for label, size in (("1x", (64, 64)), ("2x", (128, 128)), ("3x", (384, 384))):
        frames = [on_background(f.resize(size, Image.LANCZOS) if size[0] < 128 else f, size).convert("RGB")
                  for f in new]
        frames[0].save(PREVIEW_DIR / f"{key}_{label}.gif", save_all=True, append_images=frames[1:],
                       duration=duration, loop=0, disposal=2)
    old = [on_background(f, (384, 384)).convert("RGB") for f in current]
    old[0].save(PREVIEW_DIR / f"{key}_current_3x.gif", save_all=True, append_images=old[1:], duration=duration,
                loop=0)
    # static check: pixels that differ between frames
    arr = np.stack([np.asarray(f).astype(np.int16) for f in new])
    moving = (np.abs(arr - arr[0]).max(0).max(-1) > 0)
    Image.fromarray((moving * 255).astype(np.uint8)).resize((256, 256), Image.NEAREST).save(
        PREVIEW_DIR / f"{key}_moving.png")
    print(f"{key}: {len(names)} frames, {moving.mean() * 100:.1f}% of pixels change across the loop")


if __name__ == "__main__":
    main()
