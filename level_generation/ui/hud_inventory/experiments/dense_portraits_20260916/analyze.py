"""Measure actual opaque portrait interiors and build review proofs; never accept art."""
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
NAMES = ["landscape_72", "portrait_72", "square_63", "wide_75", "tight_81"]


def analyze(name):
    folder = HERE / name
    manifest = json.loads((folder / "manifest.json").read_text())
    raw = Image.open(folder / "raw.png").convert("RGB")
    rgb = np.asarray(raw).astype(np.int16)
    matte = ((rgb[:, :, 0] > 160) & (rgb[:, :, 2] > 130) & (rgb[:, :, 1] < 130)
             & (rgb[:, :, 0] - rgb[:, :, 1] > 80) & (rgb[:, :, 2] - rgb[:, :, 1] > 60))
    labels, _ = ndimage.label(~matte)
    boxes = []
    for y_slice, x_slice in ndimage.find_objects(labels):
        w, h = x_slice.stop - x_slice.start, y_slice.stop - y_slice.start
        if w > 60 and h > 90:
            boxes.append([x_slice.start, y_slice.start, w, h])
    # All returned grids were visually checked; group by coarse row before sorting left-right.
    boxes.sort(key=lambda b: (b[1] // 40, b[0]))
    assert len(boxes) == len(manifest["cells"]), (name, len(boxes))
    columns, rows = manifest["grid"]
    for row in range(rows):
        group = boxes[row * columns:(row + 1) * columns]
        assert max(b[1] for b in group) - min(b[1] for b in group) <= 3
    (folder / "review").mkdir(exist_ok=True)
    (folder / "raw_cells").mkdir(exist_ok=True)
    results = []
    cards = []
    for index, (cell, box) in enumerate(zip(manifest["cells"], boxes)):
        x, y, w, h = box
        generated = raw.crop((x, y, x+w, y+h))
        generated.save(folder / "raw_cells" / f"{index+1:03d}.png")
        native = Image.open(folder / cell["source_png"]).convert("RGB")
        native2 = native.resize((118, 158), Image.Resampling.NEAREST)
        # Unscaled raw pixels on the right; the proof is not a fitted final candidate.
        proof = Image.new("RGB", (118+w+18, max(158, h)+34), "#252525")
        proof.paste(native2, (0, 27))
        proof.paste(generated, (136, 27))
        draw = ImageDraw.Draw(proof)
        draw.text((1, 3), f"{index+1:03d} native x2", fill="white")
        draw.text((137, 3), f"raw {w}x{h}", fill="white")
        proof.save(folder / "review" / f"{index+1:03d}.png")
        expected = cell["native_rect"]
        sx = raw.width / manifest["native_sheet_size"][0]
        sy = raw.height / manifest["native_sheet_size"][1]
        result = dict(id=cell["id"], slot=index+1, raw_xywh=box,
                      raw_sampling_xy=[w/59, h/79],
                      minimum_raw_sampling=min(w/59, h/79),
                      sufficient_2x_rectangle=w >= 118 and h >= 158,
                      size_error_vs_global_transform=[w-expected[2]*sx, h-expected[3]*sy],
                      review_status="not_production_accepted")
        results.append(result)
        cls = "pass" if result["sufficient_2x_rectangle"] else "fail"
        cards.append(f'<article class="{cls}"><b>{index+1:03d}: {html.escape(cell["id"])}</b>'
                     f'<p>{w}×{h}; sampling {w/59:.3f}×{h/79:.3f} — size gate only</p>'
                     f'<img loading="lazy" src="review/{index+1:03d}.png"></article>')
    # A selection of expression/effect/edge cases, with common IDs for cross-layout comparison.
    sample_ids = ["7pc01-07.bmp", "7pc01-11.bmp", "7pc01-12.bmp", "7pc01-25.bmp",
                  "7pc01-35.bmp", "7pc02-07.bmp", "7pc02-09.bmp", "7pc02-25.bmp"]
    samples = []
    for suffix in sample_ids:
        item = next((r for r in results if r["id"].endswith(suffix)), None)
        if item:
            samples.append(Image.open(folder / "review" / f'{item["slot"]:03d}.png').convert("RGB"))
    cw = max(im.width for im in samples) + 8
    ch = max(im.height for im in samples) + 8
    contact = Image.new("RGB", (cw*4, ch*2), "#444444")
    for index, im in enumerate(samples):
        contact.paste(im, ((index % 4)*cw, (index//4)*ch))
    contact.save(folder / "review" / "samples.png")
    summary = dict(name=name, target_count=len(results), grid=manifest["grid"],
                   requested_output=manifest["requested_output"], actual_size=list(raw.size),
                   actual_pixels=raw.width*raw.height,
                   widths=[min(b[2] for b in boxes), max(b[2] for b in boxes)],
                   heights=[min(b[3] for b in boxes), max(b[3] for b in boxes)],
                   minimum_sampling=min(r["minimum_raw_sampling"] for r in results),
                   below_2x=sum(not r["sufficient_2x_rectangle"] for r in results),
                   rows=[dict(y=boxes[i*columns][1], min_height=min(b[3] for b in boxes[i*columns:(i+1)*columns]),
                              max_height=max(b[3] for b in boxes[i*columns:(i+1)*columns])) for i in range(rows)],
                   measurement="Conservative opaque-interior connected components separated by magenta; edge antialiasing creates approximately one-pixel boundary uncertainty. No resizing of raw results.",
                   caveat="Rectangle sampling is not proof of facial geometry, expression fidelity or reconstructed detail.")
    (folder / "measurements.json").write_text(json.dumps(dict(summary=summary, cells=results), indent=2)+"\n")
    (folder / "index.html").write_text(f'''<!doctype html><meta charset="utf-8"><title>{name} review</title>
<style>body{{background:#181818;color:#eee;font:15px sans-serif}}nav{{position:sticky;top:0;background:#333;padding:12px}}
section{{display:flex;flex-wrap:wrap;gap:12px}}article{{padding:8px;border:2px solid #777}}article.fail{{border-color:#f85}}
article img{{display:block;image-rendering:pixelated}}p{{margin:5px 0}}b{{font-size:12px}}</style>
<nav><a href="../index.html" style="color:#9cf">All experiments</a> · {name} · native x2 left, unscaled generated pixels right.
<button onclick="document.querySelectorAll('article img').forEach(x=>x.style.width=x.naturalWidth+'px')">1:1</button>
<button onclick="document.querySelectorAll('article img').forEach(x=>x.style.width=x.naturalWidth*2+'px')">2× inspection</button></nav>
<p>These are raw-cell diagnostic crops, not registered exports or accepted artwork. Orange border = below strict size threshold.</p>
<section>{''.join(cards)}</section>''')
    manifest["status"] = "generated_experiment_pending_production_fidelity_review"
    manifest["receipt"] = "receipt.json"
    manifest["measurements"] = "measurements.json"
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    return summary


def main():
    summaries = [analyze(name) for name in NAMES]
    (HERE / "measurements.json").write_text(json.dumps(summaries, indent=2)+"\n")
    rows = []
    for s in summaries:
        rows.append(f'<tr><td><a href="{s["name"]}/index.html">{s["name"]}</a></td>'
                    f'<td>{s["grid"]}</td><td>{s["actual_size"]}</td><td>{s["widths"]} × {s["heights"]}</td>'
                    f'<td>{s["minimum_sampling"]:.3f}</td><td>{s["below_2x"]}</td></tr>')
    (HERE / "index.html").write_text('''<!doctype html><meta charset="utf-8"><title>Portrait density test</title>
<style>body{background:#1d2127;color:#eee;font:16px sans-serif;max-width:1100px;margin:30px auto}a{color:#8cf}td,th{padding:12px;border-bottom:1px solid #555;text-align:left}table{border-collapse:collapse}</style>
<h1>MM6–8 portrait sheet density test</h1><p>Five actual built-in imagegen calls. Sources: bundles 016–025, 59×79 native portraits.
Every row links to all native/raw comparisons with a zoom control. No production artwork accepted.</p>
<p><a href="README.md">Findings and limitations</a> · <a href="measurements.json">Measurements</a></p>
<table><tr><th>Experiment</th><th>Grid</th><th>Returned raster</th><th>Portrait width × height ranges</th><th>Minimum sampling</th><th>Cells below 2×</th></tr>'''
        + ''.join(rows) + '</table><p>Size gates measure generated rectangle pixels, not semantic fidelity. The extreme 81-cell result has one-pixel boundary sensitivity.</p>')
    for s in summaries:
        print(json.dumps({k:v for k,v in s.items() if k not in ("rows", "measurement", "caveat")}))


if __name__ == "__main__":
    main()
