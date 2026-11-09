#!/usr/bin/env python3
"""Size of every 3D actor binding of a world against the native tables.

Two checks per descriptor family (descriptor without its tier letter):

  tiers     each tier's effective scale (scale, times the standing sprite scale ratio with scale_reference, as
            WorldFxSystem applies it) relative to the family's first tier must equal the ratio of their standing sprite
            scales (sprite frame data, first standing frame); a mismatch is a binding error.
  absolute  native standing frame height (opaque rows of its front frame, pixels) times its sprite scale, against the
            model's standing height times its scale (world units). Informational only: native heights include raised
            weapons, wings and hover padding, and project READMEs record what each scale was fitted to; fliers are
            fitted by silhouette area. Ratios outside 0.88..1.12 are marked for a look at the project README.

    scale_audit.py [--world mm8] [--match <descriptor glob>] [--sprites DIR ...]

Native sprites are looked up (case-insensitively, <texture>0 then <texture>, .bmp or .png) in assets_dev/engine/sprites,
assets_dev/worlds/<world>/sprites, every assets_legacy/*/assets_dev/engine/sprites and any --sprites directory.
Exits non-zero on a tier mismatch. The descriptor table's Height column is collision height, not a visual size.
"""
import argparse
import fnmatch
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "floor"))
import floor_audit  # noqa: E402
import glb_pose  # noqa: E402

ROOT = floor_audit.ROOT


def standing_frames():
    """Descriptor -> (standing sprite scale, first standing texture name)."""
    frames = {}
    paths = [ROOT / "assets_dev/engine/rendering/sprite_frame_data_common.yml"]  # MM6 monster sprites live here
    paths += sorted((ROOT / "assets_dev/engine/rendering/sprite_frames/monsters").glob("*.yml"))
    for path in paths:
        for sprite in (yaml.safe_load(path.read_text()) or {}).get("sprites", []):
            first = sprite["frames"][0]
            frames[sprite["sprite_name"].lower()] = (float(first.get("scale", 1.0)), first["texture_name"].lower())
    result = {}
    for fields in floor_audit.read_table(ROOT / "assets_dev/engine/data_tables/monster_descriptors.txt"):
        if fields[11].lower() in frames:
            result[fields[1]] = frames[fields[11].lower()]
    return result


def sprite_index(world, extra):
    directories = [ROOT / "assets_dev/engine/sprites", ROOT / f"assets_dev/worlds/{world}/sprites"]
    directories += sorted(ROOT.glob("assets_legacy/*/assets_dev/engine/sprites")) + [Path(path) for path in extra]
    index = {}
    for directory in directories:
        if directory.is_dir():
            for path in directory.iterdir():
                if path.suffix.lower() in (".bmp", ".png"):
                    index.setdefault(path.stem.lower(), path)
    return index


def native_height(index, texture):
    """Opaque height (pixels) of a texture's front frame; the corner colour is the transparent key."""
    path = index.get(texture + "0") or index.get(texture)
    if path is None:
        return None
    image = np.asarray(Image.open(path).convert("RGBA"))
    opaque = (image[..., 3] > 0) & np.any(image[..., :3] != image[0, 0, :3], axis=-1)
    rows = np.where(opaque.any(axis=1))[0]
    return int(rows.max() - rows.min() + 1) if len(rows) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--world", default="mm8")
    parser.add_argument("--match")
    parser.add_argument("--sprites", action="append", default=[])
    args = parser.parse_args()
    actors = yaml.safe_load((ROOT / f"assets_dev/worlds/{args.world}/models/actors.yml").read_text())["actors"]
    frames = standing_frames()
    index = sprite_index(args.world, args.sprites)
    families, models = {}, {}
    for actor in actors:
        if not args.match or fnmatch.fnmatch(actor["descriptor"], args.match):
            name = actor["descriptor"]
            families.setdefault(name[:-2] if name[-2:-1] == " " else name, []).append(actor)
    mismatches = 0
    for family, members in families.items():
        cells, mismatch = [], False
        first = members[0]
        base_frame = frames.get(first["descriptor"])
        for actor in members:
            name = actor["descriptor"]
            frame = frames.get(name)
            if frame is None or base_frame is None:
                cells.append(f"{name[-1]}: no standing sprite")
                continue
            scale = float(actor["scale"])
            if "scale_reference" in actor:
                scale *= frame[0] / frames[actor["scale_reference"]][0]
            base_scale = float(first["scale"])
            if "scale_reference" in first:
                base_scale *= base_frame[0] / frames[first["scale_reference"]][0]
            model_ratio, native_ratio = scale / base_scale, frame[0] / base_frame[0]
            mismatch |= abs(model_ratio - native_ratio) > 0.02
            cell = f"{name[-1]}: sprite x{frame[0]:.3f} scale {scale:.2f} ratio {model_ratio:.2f}/{native_ratio:.2f}"
            if actor is first:
                model = models.setdefault(actor["model"], glb_pose.Model(glb_pose.Glb(ROOT / "assets_source"
                                                                                     / actor["model"])))
                top = model.highest(actor["clips"]["standing"], 0.0) * scale
                pixels = native_height(index, frame[1])
                if pixels:
                    fit = top / (pixels * frame[0])
                    cell += f" | native {pixels}px x{frame[0]:.2f} = {pixels * frame[0]:.0f}, model {top:.0f}" \
                            f" ({fit:.2f}{' look' if abs(fit - 1) > 0.12 else ''})"
                else:
                    cell += f" | native sprite {frame[1]} not found"
            cells.append(cell)
        mismatches += mismatch
        print(f"{'MISMATCH' if mismatch else 'ok':8} {family[:30]:30} " + " | ".join(cells))
    print(f"\n{len(families)} families, {mismatches} with tier scales that differ from the sprite tables")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
