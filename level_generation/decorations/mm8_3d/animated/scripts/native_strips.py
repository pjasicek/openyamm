"""Frame strips of the native animated sprites (x2 restored frames and the native bitmaps), one per decoration.

Writes review/native_frames/<name>.png (x2 frames on grey, frame number and loop time) and
review/native_frames/<name>_native.png (native 8-bit bitmaps x3, nearest). Usage: python3 native_strips.py [names]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parents[1]
INV = HERE.parent / "inventory.json"
X2 = ROOT / "assets_legacy/decorations_x2_mm8_20261016"   # retired from assets_dev 2026-10-16
BMP = ROOT / "assets_dev/_legacy/sprites_original"
OUT = HERE / "review/native_frames"
NAMES = ["dec57", "dec58", "dec59", "dec07", "dec08", "dec27", "dec02", "dec06", "dec24", "dec30"]


def find_bmp(tex):
    for p in BMP.iterdir():
        if p.stem.lower() == tex.lower() and p.suffix.lower() == ".bmp":
            return p
    return None


def native_rgba(tex):
    p = find_bmp(tex)
    im = Image.open(p)
    rgba = im.convert("RGBA")
    if im.mode == "P":
        idx = im.load()
        px = rgba.load()
        for y in range(im.height):
            for x in range(im.width):
                if idx[x, y] == 0:
                    px[x, y] = (0, 0, 0, 0)
    return rgba


def strip(images, labels, bg=(96, 96, 96, 255)):
    w = sum(i.width for i in images) + 8 * (len(images) + 1)
    h = max(i.height for i in images) + 28
    sheet = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(sheet)
    x = 8
    for im, lab in zip(images, labels):
        sheet.alpha_composite(im, (x, h - 4 - im.height))
        d.text((x, 4), lab, fill=(255, 255, 255, 255))
        x += im.width + 8
    return sheet


def main():
    names = sys.argv[1:] or NAMES
    inv = {e["name"]: e for e in json.loads(INV.read_text())}
    OUT.mkdir(parents=True, exist_ok=True)
    for n in names:
        e = inv[n]
        texs = e["frame_textures"]
        pal = e["files"][0].rsplit("_p", 1)[1]
        frame_s = e["anim"] / 16.0 / max(1, e["frames"])
        x2 = [Image.open(X2 / f"{t}_p{pal}").convert("RGBA") for t in texs]
        labels = [f"{i} {t} {i * frame_s:.2f}s" for i, t in enumerate(texs)]
        strip(x2, labels).save(OUT / f"{n}.png")
        nat = []
        for t in texs:
            im = native_rgba(t)
            nat.append(im.resize((im.width * 3, im.height * 3), Image.NEAREST))
        strip(nat, labels).save(OUT / f"{n}_native.png")
        print(n, len(texs), "frames, loop", e["anim"] / 16.0, "s")


if __name__ == "__main__":
    main()
