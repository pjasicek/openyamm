#!/usr/bin/env python3
"""Prepare the mockup backdrops, Bjarni's portrait crop and the current-state text zoom comparison.

Inputs are the engine-native captures under current/ (see README.md, "How the captures were made").
Outputs: mockups/assets/backdrop_<w>x900.jpg, mockups/assets/portrait_bjarni.png and
current/text_zoom_comparison.png.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
CURRENT = STUDY / "current"
ASSETS = STUDY / "mockups" / "assets"


def clean_backdrop(path: Path) -> Image.Image:
    """Paint over the 'Talk' hover plate and the crosshair with the floor/wall a little to the left."""
    image = Image.open(path).convert("RGB")
    width, _ = image.size
    centre = width // 2
    for box, shift in (((centre - 44, 648, centre + 44, 694), 100), ((centre - 12, 438, centre + 12, 462), 30)):
        patch = image.crop((box[0] - shift, box[1], box[2] - shift, box[3]))
        image.paste(patch, box[:2])
    return image


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for size in ("1600x900", "1200x900", "1950x900"):
        clean_backdrop(CURRENT / f"backdrops_{size}" / "01-bjarni_hall.png").save(
            ASSETS / f"backdrop_{size}.jpg", quality=92)

    # Bjarni's head as an in-engine render would frame it (stand-in for a model-rendered portrait).
    hall = Image.open(CURRENT / "backdrops_1600x900" / "01-bjarni_hall.png").convert("RGB")
    hall.crop((742, 126, 850, 234)).resize((208, 208), Image.LANCZOS).save(ASSETS / "portrait_bjarni.png")

    # Text at 3x nearest: the RUDE bitmap font at 1600x900 (x1.5) and 1920x1080 (x1.8), and the Obsidian house dialogue.
    font = ImageFont.load_default()
    crops = [
        ("RUDE now, 1600x900 (canvas x1.5)", CURRENT / "shots_1600" / "01_bjarni_entry_eight_choices.png",
         (430, 640, 830, 690)),
        ("RUDE now, 1920x1080 (canvas x1.8)", CURRENT / "shots_1920" / "01_bjarni_entry_eight_choices.png",
         (520, 770, 1000, 830)),
        ("Obsidian house dialogue (Arrus TTF), 1200x900",
         ROOT / "level_generation/ui/obsidian_npc_frame_20260929/native/house-memoria.png", (30, 490, 430, 560)),
    ]
    tiles = []
    for label, path, box in crops:
        crop = Image.open(path).convert("RGB").crop(box)
        crop = crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST)
        tile = Image.new("RGB", (crop.width, crop.height + 24), (16, 20, 20))
        tile.paste(crop, (0, 24))
        ImageDraw.Draw(tile).text((6, 6), label, fill=(230, 220, 199), font=font)
        tiles.append(tile)
    width = max(tile.width for tile in tiles)
    sheet = Image.new("RGB", (width, sum(tile.height + 8 for tile in tiles)), (8, 10, 10))
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height + 8
    sheet.save(CURRENT / "text_zoom_comparison.png")


if __name__ == "__main__":
    main()
