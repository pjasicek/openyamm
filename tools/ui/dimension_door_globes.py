#!/usr/bin/env python3
"""Writes the lit portal pictures of the Dimension Door screens: each continent's globe seen through its portal.

The Dimension Door screen (the spell and the towns' dimensional travel pedestals) draws a door's lit picture over the
backdrop while the pointer is on it. This tool makes each lit picture from the backdrop itself: it crops the door's
place, finds the portal's oval glass there (the light, bluish pixels joined to the oval's middle), and fits the round
globe of that continent's new-game card into it (the globe only, not the card's gilt frame), over a deepened copy of
the portal's own mist, with a soft edge, a faint halo and a glass sheen.

Inputs, all read from the game's data:
- the screens, places and door pictures: `assets_dev/engine/data_tables/dimension_doors.yml` and each world's
  `data_tables/dimension_doors.yml`;
- the globes: the `card.picture` of the continent with the door's key in `character_selection.yml`
  (`new_game_continents`) and each world's `data_tables/new_game_continents.yml`.

Each picture is written where the door's `pictures` entry points (the engine's doors on the engine's screen into the
engine folder, a world's screen into that world's folder). The first run copies each picture it replaces to
`--backup` (default `output/dimension_door_pre_globes/`, the same relative path) unless a copy is there already.

    python3 tools/ui/dimension_door_globes.py            # write every screen's pictures
    python3 tools/ui/dimension_door_globes.py --check    # say what would be written, write nothing
    python3 tools/ui/dimension_door_globes.py --preview out.png   # also a sheet of the screens, every door lit
    python3 tools/ui/dimension_door_globes.py --out DIR  # write under DIR (paths as under assets_dev) for a look
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets_dev"
ENGINE = ASSETS / "engine"

# The globe's glass inside the card's gilt frame: a circle about the picture's middle, as a share of its size.
GLOBE_RADIUS_SHARE = 190.0 / 444.0
# The globe's radius as a share of the oval's half width (the oval is taller than wide: mist shows above and below).
GLOBE_IN_OVAL = 0.95


def resolve_asset(relative, suffix=".png"):
    """An asset path as the game names it: under the engine package, else under assets_dev (worlds/...)."""
    name = relative if relative.endswith(suffix) else relative + suffix
    for base in (ENGINE, ASSETS):
        if (base / name).is_file():
            return base / name
    if relative.startswith("worlds/"):
        return ASSETS / name
    return ENGINE / name


def load_yaml(path):
    with open(path, encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def world_folders():
    worlds = ASSETS / "worlds"
    return sorted(path for path in worlds.iterdir() if path.is_dir()) if worlds.is_dir() else []


def read_tables():
    """Screens by door count, each door's pictures by count, and each continent key's globe."""
    screens = {}
    pictures = {}
    sources = [ENGINE / "data_tables" / "dimension_doors.yml"]
    sources += [world / "data_tables" / "dimension_doors.yml" for world in world_folders()]
    for path in sources:
        if not path.is_file():
            continue
        table = load_yaml(path)
        for screen in table.get("screens") or []:
            screens[len(screen["places"])] = screen
        for door in table.get("doors") or []:
            for count, picture in (door.get("pictures") or {}).items():
                pictures.setdefault(door["key"], {})[int(count)] = (picture, door.get("place"))

    globes = {}
    cards = [ENGINE / "data_tables" / "character_selection.yml"]
    cards += [world / "data_tables" / "new_game_continents.yml" for world in world_folders()]
    for path in cards:
        if not path.is_file():
            continue
        for continent in load_yaml(path).get("new_game_continents") or []:
            card = continent.get("card") or {}
            if card.get("picture"):
                globes[continent["key"]] = resolve_asset(card["picture"], "")
    return screens, pictures, globes


def door_places(pictures):
    """Each door key's place, its rank left to right (the new-game card order): the entry that gave it."""
    places = {}
    for key, by_count in pictures.items():
        for _picture, place in by_count.values():
            if place:
                places[key] = place
    return places


def screen_slots(pictures, places, count):
    """The doors on the screen of `count` doors, by key: their slot (0 = leftmost). The doors take the screen's places
    in the order of their `place`, as the game draws them."""
    keys = sorted((key for key, by_count in pictures.items() if count in by_count and key in places),
                  key=lambda key: places[key])
    return {key: slot for slot, key in enumerate(keys)}


def glass_mask(crop):
    """The portal's oval glass in a crop of the backdrop: light, bluish pixels joined to the crop's middle."""
    pixels = np.asarray(crop.convert("RGB")).astype(np.float32)
    light = pixels.mean(axis=2) > 90.0
    bluish = pixels[..., 2] >= pixels[..., 0] - 3.0
    rough = Image.fromarray(((light & bluish) * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))
    rough = rough.point(lambda value: 255 if value > 127 else 0)
    middle = (crop.width // 2, crop.height // 2)
    if rough.getpixel(middle) != 255:
        raise SystemExit("no portal glass in the middle of a place; check its picture rect")
    ImageDraw.floodfill(rough, middle, 128)
    mask = rough.point(lambda value: 255 if value == 128 else 0)
    # Fill pinholes (stars of the mist), then soften the edge against the stone.
    return mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))


def ellipse_of(mask):
    """Centre and half axes of a filled oval mask (from its second moments)."""
    ys, xs = np.nonzero(np.asarray(mask) > 127)
    cx, cy = xs.mean(), ys.mean()
    return cx, cy, 2.0 * np.sqrt(((xs - cx) ** 2).mean()), 2.0 * np.sqrt(((ys - cy) ** 2).mean())


def round_globe(path, radius):
    """The card's round globe without its frame, scaled to the radius, with a soft-edged circular alpha."""
    card = Image.open(path).convert("RGB")
    size = min(card.size)
    inner = GLOBE_RADIUS_SHARE * size
    box = (card.width / 2 - inner, card.height / 2 - inner, card.width / 2 + inner, card.height / 2 + inner)
    diameter = int(round(radius * 2))
    globe = card.resize((diameter, diameter), Image.LANCZOS, box=box)
    supersample = 4
    alpha = Image.new("L", (diameter * supersample, diameter * supersample), 0)
    ImageDraw.Draw(alpha).ellipse((0, 0, diameter * supersample - 1, diameter * supersample - 1), fill=255)
    alpha = alpha.resize((diameter, diameter), Image.LANCZOS).filter(ImageFilter.GaussianBlur(max(1.0, radius / 60)))
    globe.putalpha(alpha)
    return globe


def lit_picture(backdrop, rect, scale, globe_path):
    x, y, width, height = (int(round(value * scale)) for value in rect)
    crop = backdrop.crop((x, y, x + width, y + height)).convert("RGB")
    mask = glass_mask(crop)
    cx, cy, half_width, _half_height = ellipse_of(mask)

    # The portal's own mist, deepened and blued: the glass is lit from beyond.
    mist = np.asarray(crop).astype(np.float32)
    deep = np.array([18.0, 34.0, 70.0])
    glow = np.array([120.0, 170.0, 230.0])
    shade = mist.mean(axis=2, keepdims=True) / 255.0
    inside = deep + (glow - deep) * shade ** 1.4
    inside = Image.fromarray(np.clip(inside, 0, 255).astype(np.uint8))

    radius = half_width * GLOBE_IN_OVAL
    globe = round_globe(globe_path, radius)
    corner = (int(round(cx - radius)), int(round(cy - radius)))

    # A faint halo round the globe, then the globe.
    halo = Image.new("L", inside.size, 0)
    ImageDraw.Draw(halo).ellipse((cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2), fill=150)
    halo = halo.filter(ImageFilter.GaussianBlur(radius / 12))
    inside = Image.composite(Image.new("RGB", inside.size, (200, 225, 255)), inside, halo)
    inside.paste(globe, corner, globe)

    # Seen through glass: the mist's swirl faintly over everything, and a sheen from the upper left.
    swirl = crop.convert("L").filter(ImageFilter.GaussianBlur(1)).point(lambda value: int(value * 0.16))
    inside = ImageChops.add(inside, Image.merge("RGB", (swirl, swirl, swirl)), 1.0, -12)
    sheen = Image.new("L", inside.size, 0)
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.ellipse((cx - half_width * 0.85, cy - half_width * 1.35, cx + half_width * 0.25,
                        cy - half_width * 0.35), fill=46)
    sheen = sheen.filter(ImageFilter.GaussianBlur(half_width / 5))
    inside = Image.composite(Image.new("RGB", inside.size, (255, 255, 255)), inside, sheen)

    # Darker towards the stone, so the glass has depth.
    rim = mask.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.GaussianBlur(half_width / 9))
    edge_shade = Image.eval(rim, lambda value: int(0.55 * 255 + 0.45 * value))
    inside = ImageChops.multiply(inside, Image.merge("RGB", (edge_shade, edge_shade, edge_shade)))

    soft = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(max(1.0, scale)))
    return Image.composite(inside, crop, soft)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="say what would be written; write nothing")
    parser.add_argument("--backup", default=str(ROOT / "output" / "dimension_door_pre_globes"),
                        help="where the replaced pictures are copied once (by their path under assets_dev)")
    parser.add_argument("--preview", help="also write a sheet of every screen with every door lit")
    parser.add_argument("--out", help="write the pictures under this folder (their path under assets_dev) instead")
    args = parser.parse_args()

    screens, pictures, globes = read_tables()
    places = door_places(pictures)
    sheets = []
    failures = 0

    for count, screen in sorted(screens.items()):
        backdrop_path = resolve_asset(screen["backdrop"])
        backdrop = Image.open(backdrop_path).convert("RGB")
        scale = backdrop.width / 640.0
        sheet = backdrop.copy()

        slots = screen_slots(pictures, places, count)
        for key, by_count in sorted(pictures.items(), key=lambda item: slots.get(item[0], len(slots))):
            if count not in by_count:
                continue
            picture, _place = by_count[count]
            slot = slots.get(key)
            if key not in globes or slot is None or slot >= len(screen["places"]):
                print(f"{count} doors, {key}: no globe or place; left as it is", file=sys.stderr)
                failures += 1
                continue
            rect = screen["places"][slot]["picture"]
            target = resolve_asset(picture)
            print(f"{count} doors, place {slot + 1}, {key}: {globes[key].relative_to(ROOT)} -> "
                  f"{target.relative_to(ROOT)}")
            if args.check:
                continue

            image = lit_picture(backdrop, rect, scale, globes[key])
            sheet.paste(image, (int(round(rect[0] * scale)), int(round(rect[1] * scale))))
            backup = Path(args.backup) / target.relative_to(ASSETS)
            if args.out:
                target = Path(args.out) / target.relative_to(ASSETS)
                target.parent.mkdir(parents=True, exist_ok=True)
            elif target.is_file() and not backup.is_file():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            # A new file renamed into place: the old one may be hard-linked into play roots, which keep their copy.
            fresh = target.with_name(target.stem + ".new.png")
            image.save(fresh, optimize=True)
            os.chmod(fresh, 0o644)
            os.replace(fresh, target)

        sheets.append(sheet)

    if args.preview and sheets:
        width = max(sheet.width for sheet in sheets) // 2
        preview = Image.new("RGB", (width, sum(sheet.height // 2 for sheet in sheets)))
        top = 0
        for sheet in sheets:
            half = sheet.resize((sheet.width // 2, sheet.height // 2), Image.LANCZOS)
            preview.paste(half, (0, top))
            top += half.height
        preview.save(args.preview)
        print(f"preview: {args.preview}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
