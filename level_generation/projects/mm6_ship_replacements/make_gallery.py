#!/usr/bin/env python3
"""Index the unmodified engine captures and create small diagnostic contact sheets."""
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
config = json.loads((PROJECT / "source/ships.json").read_text())
sections = []
for entry in config["maps"]:
    stem = Path(entry["map"]).stem
    images = sorted((PROJECT / "review" / stem).glob("*.png"))
    if not images:
        continue
    sections.append(f'<h2>{html.escape(entry["location"])}</h2><div class="grid">')
    sheet = Image.new("RGB", (1280, ((len(images) + 1) // 2) * 386), "#171a20")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(images):
        label = path.stem[3:].replace("_", " ")
        href = path.relative_to(PROJECT).as_posix()
        sections.append(f'<figure><a href="{href}"><img loading="lazy" src="{href}" alt="{label}"></a>'
                        f'<figcaption>{html.escape(label)}</figcaption></figure>')
        with Image.open(path) as image:
            thumbnail = image.convert("RGB").resize((640, 360), Image.Resampling.LANCZOS)
        x, y = (i % 2) * 640, (i // 2) * 386
        sheet.paste(thumbnail, (x, y))
        draw.text((x + 8, y + 366), label, fill="white")
    sections.append("</div>")
    destination = PROJECT / "review/contact" / (stem + ".jpg")
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=92)
(PROJECT / "index.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MM6 ships</title>
<style>body{margin:30px auto;max-width:1400px;background:#171a20;color:#eee;font:17px system-ui;padding:0 20px}
a{color:#c1d9fb}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:20px}
figure{margin:0}img{display:block;width:100%}figcaption{padding:8px 0 20px}h2{margin-top:40px}</style>
<h1>MM6 ships</h1><p>Twelve ship replacements on seven unchanged port maps. Click a capture for full size.</p>
<p>Only cabin doors open the original travel services. Free Haven's offshore ship remains scenery.
<a href="README.md">Build, package and play instructions</a>.</p>
''' + "\n".join(sections) + "</html>\n")
