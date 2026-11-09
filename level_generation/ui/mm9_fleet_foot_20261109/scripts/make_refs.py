"""Builds the reference sheets attached to the Codex runs (refs/).

python3 -I make_refs.py
  refs/refs_air_vignettes.png  original Air spell pictures as pairs on parchment: highlighted (colour) left, normal
                               (sepia) right. Fly, Jump; Feather Fall, Lightning Bolt.
  refs/refs_mm9_fleetfoot.png  MM9's own Fleet Foot spell picture (highlighted), 3x nearest: the subject.
  refs/refs_fly_caption.png    Fly's highlighted picture beside its lower-left quarter (caption and haze) at 3x, on
                               parchment: the caption's stroke weight and the haze's darkness (vignette attempt 4).
  refs/refs_hud.png            MM9's Fleet Foot HUD frames (8x nearest) above the engine's HD Fly indicator frames
                               (2x nearest): subject/motion and the HD icon style.
"""
from pathlib import Path

from PIL import Image

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
ICONS = ROOT / "assets_dev/engine/icons_x2"
MM9_ART = ROOT / "mm9/extracted/ART/ART"
REFS = STUDY / "refs"
PARCHMENT = (226, 206, 160, 255)
DARK = (40, 40, 44, 255)


def pcx(path):
    """A native MM9 picture with its cyan key made transparent."""
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y][:3] == (0, 255, 255):
                pixels[x, y] = (0, 0, 0, 0)
    return image


def air_sheet():
    cell = 340
    pairs = [("sba10", 0, 0), ("sba04", 0, 2), ("sba02", 1, 0), ("sba05", 1, 2)]
    sheet = Image.new("RGBA", (cell * 4, cell * 2), PARCHMENT)
    for stem, row, col in pairs:
        for state, offset in (("a", 0), ("b", 1)):
            image = Image.open(ICONS / f"{stem}{state}.png").convert("RGBA")
            x = (col + offset) * cell + (cell - image.width) // 2
            y = row * cell + (cell - image.height) // 2
            sheet.alpha_composite(image, (x, y))
    sheet.convert("RGB").save(REFS / "refs_air_vignettes.png")


def mm9_sheet():
    image = pcx(MM9_ART / "SPELLS/SPELLFLEETFOOT-HIGHLIGHT.pcx")
    image = image.resize((image.width * 3, image.height * 3), Image.NEAREST)
    sheet = Image.new("RGBA", (image.width + 40, image.height + 40), PARCHMENT)
    sheet.alpha_composite(image, (20, 20))
    sheet.convert("RGB").save(REFS / "refs_mm9_fleetfoot.png")


def hud_sheet():
    strip = pcx(MM9_ART / "HUD/FLEETFOOTANIM.pcx")
    sheet = Image.new("RGBA", (8 * 300, 300 + 280), DARK)
    for k in range(8):
        frame = strip.crop((k * 36, 0, k * 36 + 36, 36)).resize((288, 288), Image.NEAREST)
        sheet.alpha_composite(frame, (k * 300 + 6, 6))
        fly = Image.open(ICONS / f"sp21a{k + 1}0.png").convert("RGBA").resize((256, 256), Image.NEAREST)
        sheet.alpha_composite(fly, (k * 300 + 22, 310))
    sheet.convert("RGB").save(REFS / "refs_hud.png")


def fly_caption_sheet():
    fly = Image.open(ICONS / "sba10a.png").convert("RGBA")
    detail = fly.crop((0, 150, 200, 298))
    detail = detail.resize((detail.width * 3, detail.height * 3), Image.LANCZOS)
    sheet = Image.new("RGBA", (fly.width + detail.width + 60, max(fly.height, detail.height) + 40), PARCHMENT)
    sheet.alpha_composite(fly, (20, 20))
    sheet.alpha_composite(detail, (fly.width + 40, 20))
    sheet.convert("RGB").save(REFS / "refs_fly_caption.png")


def main():
    REFS.mkdir(exist_ok=True)
    air_sheet()
    fly_caption_sheet()
    mm9_sheet()
    hud_sheet()


if __name__ == "__main__":
    main()
