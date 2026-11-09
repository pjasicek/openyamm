#!/usr/bin/env python3
"""Make unapproved opaque-edge color repairs for x2 HUD candidates with pink matte spill."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


HERE = Path(__file__).resolve().parent
OUT = HERE / "opaque_edge_repair"


def read_data() -> dict:
    source = (HERE / "data.js").read_text()
    return json.loads(source.removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def chroma(rgb: np.ndarray) -> np.ndarray:
    colors = rgb.astype(np.int16)
    return np.minimum(colors[:, :, 0], colors[:, :, 2]) - colors[:, :, 1]


def edge_region(height: int, width: int, depth: int = 4) -> np.ndarray:
    ys, xs = np.indices((height, width))
    return np.minimum.reduce((ys, xs, height - 1 - ys, width - 1 - xs)) < depth


def repair_mask(candidate: np.ndarray, native: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    native_x2 = np.repeat(np.repeat(native[:, :, :3], 2, axis=0), 2, axis=1)
    candidate_rgb = candidate[:, :, :3]
    candidate_chroma = chroma(candidate_rgb)
    native_chroma = chroma(native_x2)
    excess = candidate_chroma - native_chroma
    edge = edge_region(*candidate.shape[:2])
    visible = candidate[:, :, 3] >= 128
    seed = (edge & visible & (candidate_chroma >= 70) & (excess >= 45)
            & (candidate_rgb[:, :, 0] >= 110) & (candidate_rgb[:, :, 2] >= 110))
    soft = edge & visible & (candidate_chroma >= 38) & (excess >= 28)
    mask = ndimage.binary_propagation(seed, mask=soft) if seed.any() else seed
    return mask, edge


def color_repair(candidate: np.ndarray, mask: np.ndarray) -> np.ndarray:
    result = candidate.copy()
    if not mask.any():
        return result
    _, nearest = ndimage.distance_transform_edt(mask, return_indices=True)
    result[mask, :3] = candidate[nearest[0][mask], nearest[1][mask], :3]
    return result


def thumb(image: Image.Image, background: str) -> Image.Image:
    canvas = Image.new("RGBA", image.size, background)
    canvas.alpha_composite(image)
    output = canvas.convert("RGB")
    output.thumbnail((115, 96), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (115, 96), background)
    result.paste(output, ((115 - output.width) // 2, (96 - output.height) // 2))
    return result


def make_contacts(records: list[dict]) -> None:
    items = [record for record in records if record.get("output")]
    for first in range(0, len(items), 24):
        page = items[first:first + 24]
        sheet = Image.new("RGB", (1160, 52 + 12 * 143), "#1b252b")
        draw = ImageDraw.Draw(sheet)
        draw.text((12, 13), "Native | current x2 | opaque edge repair | repair on light", fill="#f5dfa6")
        for index, record in enumerate(page):
            x = (index % 2) * 580
            y = 52 + (index // 2) * 143
            draw.text((x + 12, y + 2), record["name"] + " · " + str(record["changed_pixels"]) + " edge pixels",
                      fill="white")
            native = rgba(HERE / record["native_path"]).resize(record["size"], Image.Resampling.NEAREST)
            current = rgba(HERE / record["current_path"])
            repaired = rgba(HERE / record["output"])
            for column, art in enumerate((native, current, repaired, repaired)):
                background = "#ddd2bb" if column == 3 else "#172127"
                sheet.paste(thumb(art, background), (x + 12 + column * 140, y + 26))
        sheet.save(OUT / f"contact-{first // 24 + 1:02}.png")


def main() -> None:
    data = read_data()["assets"]
    output_dir = OUT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, asset in sorted(data.items()):
        restored = asset.get("restored", {})
        if not restored.get("image") or restored.get("alpha_repair") or restored.get("status") == "staged":
            continue
        native_path = HERE / asset["native"]
        native = np.asarray(rgba(native_path), dtype=np.uint8)
        if float((native[:, :, 3] < 128).mean()) > .01:
            continue
        current_path = HERE / (restored.get("keyed_image") or restored["image"])
        current = np.asarray(rgba(current_path), dtype=np.uint8)
        if current.shape[:2] != (native.shape[0] * 2, native.shape[1] * 2):
            continue
        mask, edge = repair_mask(current, native)
        if not mask.any():
            continue
        repaired = color_repair(current, mask)
        source_path = HERE / restored["original"]
        destination = output_dir / (asset["target"].rsplit(".", 1)[0] + ".png")
        Image.fromarray(repaired).save(destination, optimize=True)
        before = chroma(current[:, :, :3])
        after = chroma(repaired[:, :, :3])
        records.append({"name": asset["name"], "target": asset["target"],
                        "status": "opaque_edge_color_repaired_review_required", "size": list(current.shape[1::-1]),
                        "source": restored["original"], "source_sha256": sha256(source_path),
                        "native_path": asset["native"], "native_sha256": sha256(native_path),
                        "current_path": (restored.get("keyed_image") or restored["image"]),
                        "changed_pixels": int(mask.sum()), "changed_pct": round(100 * float(mask.mean()), 3),
                        "edge_chroma_before": round(float(before[mask].mean()), 3),
                        "edge_chroma_after": round(float(after[mask].mean()), 3),
                        "output": destination.relative_to(HERE).as_posix(), "output_sha256": sha256(destination),
                        "alpha_unchanged": bool(np.array_equal(current[:, :, 3], repaired[:, :, 3])),
                        "outside_mask_unchanged": bool(np.array_equal(current[~mask], repaired[~mask]))})
    (OUT / "manifest.json").write_text(json.dumps({
        "schema": "openyamm-hud-opaque-edge-repair-v1", "count": len(records),
        "method": "native-guided pink-chroma mask within four-pixel outer edge; nearest clean color",
        "scope": "unapproved review candidate only; opaque alpha preserved",
        "records": records,
    }, indent=2) + "\n")
    make_contacts(records)
    print(json.dumps({"selected": len(records), "changed_pixels": sum(r["changed_pixels"] for r in records),
                      "all_alpha_unchanged": all(r["alpha_unchanged"] for r in records),
                      "all_outside_unchanged": all(r["outside_mask_unchanged"] for r in records)}, indent=2))


if __name__ == "__main__":
    main()
