"""Prepare exact native-reference sheets for fitted variants with no retained raw return."""

import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
OUT = HERE / "new_returns/input"
GROUPS = {
    "green_cape": (["7item106v1a", "7item106v5a"],
                   "Plain green cloth. Keep edge trim narrow and subdued; do not add bright gold trim."),
    "black_cape": (["7item107v1a", "7item107v2a", "7item107v5a"],
                   "Black cloth. Keep the original narrow upper shape; do not add a fan-shaped collar."),
    "purple_cape": (["7item108v2a", "7item108v3a"],
                    "Dark purple cloth. Keep its narrow border; do not enlarge or brighten the trim."),
    "star_cape": (["7item325v2a", "7item325v3a"],
                  "Keep the small, subdued star and moon pattern at its original scale and brightness."),
    "sun_cape": (["7item347v1a", "7item347v2a", "7item347v5a"],
                 "Red and gold cloth. Keep sun motifs at their original modest size and brightness."),
    "blue_cape": (["7item348v1a", "7item348v3a", "7item348v5a"],
                  "Blue and gold cloth. Preserve the exact gold motif shapes and restrained contrast."),
    "red_black_cape": (["7item350v1a", "7item350v2a", "7item350v5a"],
                       "Red and black cloth. Keep the original subdued ornament, narrow trim and dark value range."),
    "item133": (["item133v1", "item133v2", "item133v4", "item133v5"],
                "Preserve the item design, silhouette, materials and pose variation in every cell."),
}


def main():
    targets = {target["runtime_name"].lower(): target for target in
               json.loads((HERE.parent / "expected_targets.json").read_text())["targets"]
               if target["namespace"] == "engine"}
    for group, (names, art_note) in GROUPS.items():
        directory = OUT / group
        directory.mkdir(parents=True, exist_ok=True)
        images = []
        for name in names:
            target = targets[name]
            source = HERE / "native" / (target["id"] + ".png")
            with Image.open(source) as opened:
                native = opened.convert("RGBA")
            if list(native.size) != target["native_size"]:
                raise ValueError(f"Native preview dimensions changed: {source}")
            images.append((name, native.resize(tuple(target["x2_size"]), Image.Resampling.NEAREST)))
        columns = 2 if group == "item133" else len(images)
        rows = (len(images) + columns - 1) // columns
        column_width = max(image.width for _, image in images)
        row_height = max(image.height for _, image in images)
        gutter = 24
        width = columns * column_width + (columns + 1) * gutter
        height = rows * row_height + (rows + 1) * gutter
        sheet = Image.new("RGBA", (width, height))
        rects = {}
        for index, (name, image) in enumerate(images):
            column, row = index % columns, index // columns
            x = gutter + column * (column_width + gutter)
            y = gutter + row * (row_height + gutter)
            sheet.alpha_composite(image, (x, y))
            rects[name] = [x, y, image.width, image.height]
        reference = directory / "reference.png"
        sheet.save(reference)
        prompt = (
            "Use case: precise-object-edit\n"
            "Asset type: transparent 2D paperdoll equipment sprites for a fantasy RPG\n"
            "Input image: edit target; each separate grid cell is one original sprite enlarged to its exact 2× canvas.\n"
            f"Primary request: restore painted detail in all {len(images)} sprites while preserving each original.\n"
            f"Subject-specific constraint: {art_note}\n"
            "Composition: keep the same number and order of separate cells, each sprite's pose, scale, silhouette, "
            "holes, margins and placement. Preserve clear gutters and each full cell canvas.\n"
            "Materials: paint continuous cloth, leather or metal detail at higher resolution without enlarging "
            "native pixel blocks. Keep the original palette and lighting.\n"
            "Background: genuine transparent alpha everywhere outside the objects and through holes; no magenta "
            "matte, checkerboard, scenery, cast shadow or colored fringe.\n"
            "Avoid: new ornaments, brighter trim, changed cloth folds, merged neighbors, duplicate parts, text, "
            "labels or borders. This is a faithful restoration, not a redesign.\n"
        )
        (directory / "prompt.txt").write_text(prompt)
        (directory / "layout.json").write_text(json.dumps({
            "group": group, "names": names, "reference_size": [width, height], "rects": rects,
            "native_sources": {name: targets[name]["source_path"] for name in names},
            "status": "prepared_for_imagegen", "visual_approval": False,
        }, indent=2) + "\n")
        print(group, [width, height], len(images))


if __name__ == "__main__":
    main()
