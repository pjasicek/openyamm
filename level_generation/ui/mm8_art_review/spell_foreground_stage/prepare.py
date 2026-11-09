"""Prepare paired spell foreground edit sheets from the frozen visual review catalog.

This creates reference sheets only. Returned art is registered separately and never
changes the restoration checkpoint or game assets.
"""

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
BATCHES = [
    ("sbb01", "sbb04"),
    ("sbb02", "sbb03"),
    ("sbb05", "sbb06"),
    ("sbb07", "sbb08"),
    ("sbb09", "sbb10"),
    ("sbb11", "sbdk03"),
    ("sbe03", "sbe08"),
    ("sbe11", "sbf01"),
    ("sbl01", "sbl04"),
    ("sbl05", "sbl07"),
    ("sbl10", "sbm06"),
    ("sbm11", "sbs01"),
    ("sbs11", "sbw02"),
    ("sbw04", "sbw05"),
    ("sbw07",),
]
PROMPT_EXTRAS = {
    3: "The bottom pair's detached horizontal strip above the art is an extraction artifact: omit it completely.",
    4: "The top pair is intentionally a narrow cropped vertical fist and glyph; keep that crop and do not invent the rest of the fist. Omit the detached narrow strip at far left.",
    7: "The first state of each pair has corrupted dark/magenta extraction residue; omit it. Preserve the intentional crop of the art in all four panels.",
    8: "The bottom pair has a broad torch shadow that is part of the drawing; preserve its fine hatching and flame while removing the white/background matte. Omit tiny detached extraction strips above the torch.",
    9: "Keep the top pair's full horizontal beam and both runes, but omit the page's square missing corner. Keep the bottom pair's full spine illustration and glyphs, with no paper patch.",
    10: "The bottom prism/beam pair retains its dark ink hatching as foreground, but no rectangular paper patch or book notch.",
    13: "The top pair depicts a clothed fantasy resurrection figure rising beside a gravestone; preserve the person and stones exactly, without extending the stair-step page silhouette. The bottom pair depicts a snake head with a fine arcing spray; keep the fine spray transparent between droplets.",
    14: "The top pair's glowing sword has turquoise glow that belongs to the art. The bottom pair's walking legs and water have irregular edges; remove only the parchment and page-corner notches.",
    15: "This single pair has explosive green and brown illustration strokes and separate glyphs. Keep the energetic strokes and exact paired-state composition, but remove all flat yellow parchment and the square paper notch.",
}
PILOT_PROMPT = (
    "Precise batch foreground extraction of this 2-column × 2-row Might and Magic spell art sheet. "
    "Keep exactly four independent icon cells in their existing grid, with no movement, enlargement, identity "
    "changes or new features. The top pair is a color/sepia anatomical torso; the bottom pair is a color/sepia "
    "armored knight. Preserve each figure, all small glyphs, each pair's state color, and their positions and "
    "sizes. Remove the yellow parchment, top magenta lines, and all page texture from inside every cell. "
    "Make the sheet's background and empty gutters genuinely transparent RGBA, including gaps between figure "
    "and glyphs. Do not paint a checkerboard, background, shadow, or page. Preserve soft anti-aliased ink edges. "
    "Keep cells separately extractable and do not merge the four artworks."
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))
    items = {row["name"]: row for row in catalog["items"] if row["category"] == "Spell icons"}
    manifest = []
    for number, pairs in enumerate(BATCHES, 1):
        names = [pair + state for pair in pairs for state in "ab"]
        width = max(items[name]["x2_size"][0] for name in names) + 24
        height = max(items[name]["x2_size"][1] for name in names) + 24
        if number == 2:
            width, height = 300, 370  # Preserve the already edited pilot sheet layout.
        gutter = 24
        rows = len(pairs)
        sheet = Image.new("RGB", (width * 2 + gutter * 3, height * rows + gutter * (rows + 1)), "#484848")
        cells = []
        for index, name in enumerate(names):
            item = items[name]
            candidate = item["candidates"][0]
            source = (REVIEW / candidate["path"]).resolve()
            art = Image.open(source).convert("RGBA")
            x = gutter + (index % 2) * (width + gutter)
            y = gutter + (index // 2) * (height + gutter)
            sheet.paste(art, (x, y), art)
            cells.append({
                "id": item["id"], "name": name, "source_sha256": item["source_sha256"],
                "current_artifact": str(source.relative_to(REVIEW.parents[2])),
                "current_sha256": digest(source), "x2_size": item["x2_size"],
                "reference_rect": [x, y, art.width, art.height],
                "slot_rect": [x - gutter, y - gutter, width + gutter, height + gutter],
            })
        directory = HERE / "batches" / f"{number:02d}"
        directory.mkdir(parents=True, exist_ok=True)
        reference = directory / "reference.png"
        sheet.save(reference)
        layout = {"schema": 1, "pairs": pairs, "reference_size": sheet.size,
                  "reference_sha256": digest(reference), "cells": cells}
        (directory / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")
        prompt = (
            "Precise batch foreground extraction of this two-column Might and Magic spell art sheet. "
            "Each row is a color/sepia state pair. Keep exactly the existing cells and their grid, "
            "figures, glyphs, colors, placement and identity. Remove every parchment/book background, "
            "page ornament and magenta sheet edge. Output genuine RGBA transparency around and between "
            "all illustrations and separate glyphs, including the gutters. Preserve fine hatching and "
            "soft effects. Do not paint a checkerboard or redraw the subjects or runes. "
            "Keep rows and states separately extractable. "
            f"Top pair: {pairs[0]}. " + (f"Bottom pair: {pairs[1]}." if len(pairs) > 1 else "")
        )
        if number == 2:
            prompt = PILOT_PROMPT
        elif number in PROMPT_EXTRAS:
            prompt += "\n" + PROMPT_EXTRAS[number]
        prompt_path = directory / "prompt.txt"
        prompt_path.write_text(prompt + "\n")
        manifest.append({"batch": number, "pairs": pairs, "reference": str(reference.relative_to(HERE)),
                         "reference_sha256": digest(reference), "layout": str((directory / "layout.json").relative_to(HERE)),
                         "prompt": str(prompt_path.relative_to(HERE)), "prompt_sha256": digest(prompt_path)})
    (HERE / "batches.json").write_text(json.dumps({"schema": 1, "batches": manifest}, indent=2) + "\n")


if __name__ == "__main__":
    main()
