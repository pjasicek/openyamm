"""Previews of the Fleet Foot HUD indicator.

python3 -I preview_hud.py
  previews/hud_sheet.png       top: MM9's native frames (4x nearest, 144 px), bottom: the new 128 px frames, on the
                               dark HUD-like background; frame numbers between.
  previews/hud_loop.gif        the new loop at game pace (0.16 s a frame), 1x, on the dark background.
  previews/hud_loop_2x.gif     the same at 2x (nearest), for review.
  previews/hud_moving.png      pixels that change anywhere in the loop (white), over the first frame: only the wings
                               and the boot's whole-pixel bob may move.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
NATIVE = ROOT / "mm9/extracted/ART/ART/HUD/FLEETFOOTANIM.pcx"
OUT = STUDY / "out"
PREVIEWS = STUDY / "previews"
BG = (34, 32, 36, 255)
FRAME_MS = 160


def native_frames():
    strip = Image.open(NATIVE).convert("RGBA")
    pixels = np.asarray(strip).copy()
    key = (pixels[..., 0] == 0) & (pixels[..., 1] == 255) & (pixels[..., 2] == 255)
    pixels[key] = 0
    strip = Image.fromarray(pixels)
    return [strip.crop((k * 36, 0, k * 36 + 36, 36)) for k in range(8)]


def new_frames():
    return [Image.open(OUT / f"fleetfoot{k + 1:02d}.png").convert("RGBA") for k in range(8)]


def on_bg(image):
    canvas = Image.new("RGBA", image.size, BG)
    canvas.alpha_composite(image)
    return canvas


def main():
    PREVIEWS.mkdir(exist_ok=True)
    natives, frames = native_frames(), new_frames()
    cell = 160
    sheet = Image.new("RGBA", (cell * 8 + 16, cell * 2 + 40), BG)
    draw = ImageDraw.Draw(sheet)
    for k in range(8):
        native = natives[k].resize((144, 144), Image.NEAREST)
        sheet.alpha_composite(native, (8 + k * cell + 8, 8))
        draw.text((8 + k * cell + 70, cell + 6), f"{k + 1:02d}", fill=(200, 200, 200, 255))
        sheet.alpha_composite(frames[k], (8 + k * cell + 16, cell + 26))
    sheet.convert("RGB").save(PREVIEWS / "hud_sheet.png")

    gif = [on_bg(f).convert("RGB") for f in frames]
    gif[0].save(PREVIEWS / "hud_loop.gif", save_all=True, append_images=gif[1:], duration=FRAME_MS, loop=0)
    gif2 = [g.resize((256, 256), Image.NEAREST) for g in gif]
    gif2[0].save(PREVIEWS / "hud_loop_2x.gif", save_all=True, append_images=gif2[1:], duration=FRAME_MS, loop=0)

    stack = np.stack([np.asarray(f).astype(np.int32) for f in frames])
    moving = np.abs(stack - stack[0]).sum(-1).max(0) > 8
    base = np.asarray(on_bg(frames[0]).convert("RGB")).copy()
    base[moving] = (255, 255, 255)
    Image.fromarray(base).resize((256, 256), Image.NEAREST).save(PREVIEWS / "hud_moving.png")


if __name__ == "__main__":
    main()
