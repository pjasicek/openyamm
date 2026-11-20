"""Fleet Foot spellbook picture: sba10a (highlighted, the Codex painting) and sba10b (normal, derived sepia) for the
MM9 world, in the size and placement conventions of the engine's Fly pair (300 x 298 RGBA).

python3 -I build_spellbook.py [--check]
  Inputs: masters/fleet_foot_v4.png (Codex, attempt 4; see the README for attempts 1-3), the engine's original x2 spell pictures.
  Outputs: out/sba10a.png, out/sba10b.png, previews/spellbook_fly_vs_fleet_foot.png.
  --check also derives the normal state of the engine's own Fly picture and writes
  previews/sepia_check_fly.png (original sba10b vs derived) to show the derivation matches the originals.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
ICONS = ROOT / "assets_dev/engine/icons_x2"
OUT = STUDY / "out"
PREVIEWS = STUDY / "previews"
MASTER = "masters/fleet_foot_v4.png"
# Caption glyphs mirrored left-right in the master (x0, y0, x1, y1): the first glyph of the second row read as a "9".
GLYPH_MIRROR_BOXES = [(153, 653, 201, 704)]
SIZE = (300, 298)
# Fly's visible content box in its 300 x 298 picture (x0, y0, x1, y1), measured: the new picture fills the same box.
CONTENT_BOX = (12, 9, 290, 292)
LUMA = np.array([0.299, 0.587, 0.114])
SEPIA_SOURCES = ["sba01b", "sba02b", "sba04b", "sba05b", "sba10b", "sbw04b", "sbb03b", "sbf06b", "sbde04b"]


def load(path):
    return Image.open(path).convert("RGBA")


def rune_green(rgb):
    """Pixels in the teal-green ink of the large rune: green well above red and above blue."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (g > r * 1.3) & (g > b * 1.05) & (rgb @ LUMA < 190)


def rune_mask(rgba):
    """The large caption rune: the biggest green component in the bottom-left part of the picture (Fly's caption
    place), widened by a pixel for its anti-aliased rim. Scattered green tints elsewhere (feathers) are not runes."""
    rgb = rgba[..., :3]
    candidate = rune_green(rgb) & (rgba[..., 3] > 40)
    labels, count = nd.label(nd.binary_closing(candidate), structure=np.ones((3, 3)))
    if count == 0:
        return candidate
    height, width = candidate.shape
    best, best_size = 0, 0
    for index in range(1, count + 1):
        component = labels == index
        ys, xs = np.nonzero(component)
        size = int((component & candidate).sum())
        if ys.mean() > height * 0.5 and xs.mean() < width * 0.5 and size > best_size:
            best, best_size = index, size
    rune = nd.binary_dilation(labels == best) if best else np.zeros_like(candidate)
    return rune & (rgb[..., 1] >= rgb[..., 0])


def tone_ramp(pixels):
    """Median colour of each luminance level (256 entries) of a set of RGB pixels, gaps interpolated."""
    lum = pixels @ LUMA
    order = np.argsort(lum)
    pixels, lum = pixels[order], lum[order]
    ramp = np.full((256, 3), np.nan)
    for level in range(256):
        lo, hi = np.searchsorted(lum, [level - 5, level + 5])
        if hi - lo >= 8:
            ramp[level] = np.median(pixels[lo:hi], axis=0)
    valid = ~np.isnan(ramp[:, 0])
    for channel in range(3):
        ramp[:, channel] = np.interp(np.arange(256), np.nonzero(valid)[0], ramp[valid, channel])
    return ramp


def sepia_ramp():
    pixels = []
    for name in SEPIA_SOURCES:
        array = np.asarray(load(ICONS / f"{name}.png")).reshape(-1, 4).astype(np.float64)
        keep = (array[:, 3] > 200) & ~rune_green(array[:, :3])
        pixels.append(array[keep, :3])
    return tone_ramp(np.concatenate(pixels))


def sepia_state(highlighted, ramp):
    """Normal state: luminance on the originals' sepia ramp; the large teal-green rune keeps its colour."""
    rgba = np.asarray(highlighted).astype(np.float64)
    rgb = rgba[..., :3]
    toned = ramp[np.clip(rgb @ LUMA, 0, 255).astype(int)]
    green = rune_mask(rgba)
    toned[green] = rgb[green]
    rgba[..., :3] = toned
    return Image.fromarray(np.clip(rgba + 0.5, 0, 255).astype(np.uint8))


def mirror_glyphs(master):
    for box in GLYPH_MIRROR_BOXES:
        master.paste(master.crop(box).transpose(Image.FLIP_LEFT_RIGHT), box[:2])
    return master


def fit_into_slot(master):
    """Crops the master to its content and scales it into Fly's content box, centred, on a 300 x 298 canvas."""
    alpha = np.asarray(master.getchannel("A"))
    ys, xs = np.nonzero(alpha > 6)
    content = master.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    box_w = CONTENT_BOX[2] - CONTENT_BOX[0]
    box_h = CONTENT_BOX[3] - CONTENT_BOX[1]
    scale = min(box_w / content.width, box_h / content.height)
    size = (max(1, round(content.width * scale)), max(1, round(content.height * scale)))
    content = content.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    x = CONTENT_BOX[0] + (box_w - size[0]) // 2
    y = CONTENT_BOX[1] + (box_h - size[1]) // 2
    canvas.alpha_composite(content, (x, y))
    return canvas


def save(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    path.chmod(0o644)


def side_by_side(images, labels_bg=(34, 32, 36, 255), gap=24):
    width = sum(image.width for image in images) + gap * (len(images) + 1)
    height = max(image.height for image in images) + gap * 2
    sheet = Image.new("RGBA", (width, height), labels_bg)
    x = gap
    for image in images:
        sheet.alpha_composite(image, (x, gap))
        x += image.width + gap
    return sheet.convert("RGB")


def main():
    ramp = sepia_ramp()
    if "--check" in sys.argv:
        fly_a = load(ICONS / "sba10a.png")
        derived = sepia_state(fly_a, ramp)
        save(side_by_side([fly_a, load(ICONS / "sba10b.png"), derived]), PREVIEWS / "sepia_check_fly.png")
    highlighted = fit_into_slot(mirror_glyphs(load(STUDY / MASTER)))
    normal = sepia_state(highlighted, ramp)
    save(highlighted, OUT / "sba10a.png")
    save(normal, OUT / "sba10b.png")
    fly = [load(ICONS / "sba10a.png"), load(ICONS / "sba10b.png")]
    save(side_by_side(fly + [highlighted, normal]), PREVIEWS / "spellbook_fly_vs_fleet_foot.png")


if __name__ == "__main__":
    main()
