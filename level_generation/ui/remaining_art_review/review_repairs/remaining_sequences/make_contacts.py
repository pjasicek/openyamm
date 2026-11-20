#!/usr/bin/env python3
"""Render native and regenerated effect frames in engine order for visual review."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
PLAYER = REVIEW / "pc_effect_sequences"
CELL_WIDTH = 150
CELL_HEIGHT = 194


def paste_centered(sheet: Image.Image, image: Image.Image, x: int, y: int) -> None:
    left = x + (CELL_WIDTH - image.width) // 2
    top = y + 25 + (CELL_HEIGHT - 25 - image.height) // 2
    sheet.alpha_composite(image, (left, top))


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    report = json.loads((HERE / "report.json").read_text())["items"]
    stabilized = json.loads((HERE / "stabilization_report.json").read_text())
    locked = json.loads((HERE / "idle_core_report.json").read_text())
    output = HERE / "contacts"
    output.mkdir(exist_ok=True)
    font = ImageFont.load_default()
    for family, job in jobs.items():
        frames = job["frames"]
        pinned = family in stabilized["families"]
        rows = 4 if pinned else 2
        sheet = Image.new("RGBA", (len(frames) * CELL_WIDTH, rows * CELL_HEIGHT), (32, 43, 51, 255))
        draw = ImageDraw.Draw(sheet)
        for index, frame in enumerate(frames):
            x = index * CELL_WIDTH
            for row in range(rows):
                draw.rectangle((x, row * CELL_HEIGHT, x + CELL_WIDTH - 1,
                                (row + 1) * CELL_HEIGHT - 1), outline=(77, 96, 105))
            draw.text((x + 6, 6), f"{frame['name']} native", font=font, fill=(230, 235, 231))
            draw.text((x + 6, CELL_HEIGHT + 6), f"{frame['name']} " + ("before" if pinned else "2x"),
                      font=font, fill=(230, 235, 231))
            with Image.open(PLAYER / frame["original"]) as image:
                native = image.convert("RGBA")
            native = native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST)
            with Image.open(REVIEW / report[frame["id"]]["artifact"]) as image:
                restored = image.convert("RGBA")
            paste_centered(sheet, native, x, 0)
            paste_centered(sheet, restored, x, CELL_HEIGHT)
            if pinned:
                selected = stabilized["items"].get(frame["id"], report[frame["id"]])
                with Image.open(REVIEW / selected["artifact"]) as image:
                    current = image.convert("RGBA")
                draw.text((x + 6, 2 * CELL_HEIGHT + 6), f"{frame['name']} pinned",
                          font=font, fill=(230, 235, 231))
                paste_centered(sheet, current, x, 2 * CELL_HEIGHT)
                with Image.open(REVIEW / locked["items"][frame["id"]]["artifact"]) as image:
                    final = image.convert("RGBA")
                draw.text((x + 6, 3 * CELL_HEIGHT + 6), f"{frame['name']} fixed core",
                          font=font, fill=(230, 235, 231))
                paste_centered(sheet, final, x, 3 * CELL_HEIGHT)
        sheet.save(output / f"{family}.png", optimize=True)
    cards = "\n".join(
        f'<section id="{escape(family)}"><h2>{escape(family)}</h2>'
        f'<p><a href="../../../pc_effect_sequences/index.html?sequence={escape(family)}&amp;pause=1">'
        'Play this sequence</a> · '
        f'<a href="{escape(family)}.png">Open full-size sheet</a></p>'
        f'<img loading="lazy" src="{escape(family)}.png" alt="Native and restored {escape(family)} frames"></section>'
        for family in jobs)
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>PC effect sequence contact sheets</title><style>'
        ':root{font:16px/1.5 system-ui,sans-serif;color-scheme:dark}'
        'body{margin:0 auto;max-width:1900px;padding:24px;background:#162028;color:#edf3ef}'
        'a{color:#83d9bb}section{margin:28px 0 45px}h1{margin:0}h2{margin:0}'
        'p{margin:5px 0 12px}img{max-width:100%;height:auto;border:1px solid #50616b}'
        '</style></head><body><h1>PC effect sequence contacts</h1>'
        '<p>Each sequence shows native frames above its fitted 2× candidates, in engine order. '
        'The three idle sequences add registered and fixed-core rows; the fourth row is the review candidate. '
        '<a href="../../../pc_effect_sequences/index.html">Open animation player</a>.</p>'
        + cards + '</body></html>\n')
    print(f"Wrote {len(jobs)} native/restored contact sheets to {output}")


if __name__ == "__main__":
    main()
