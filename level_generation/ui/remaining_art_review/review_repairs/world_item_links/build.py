#!/usr/bin/env python3
"""Find inventory art that can reuse an already approved ground-sprite master."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
ROOT = HERE.parents[4]
SPRITES = ROOT / "level_generation/sprites/restoration_jobs"
WORLD = ROOT / "assets_dev/engine/decorations_x2"
PRIMARY_NAMES = {"item160", "item162"}
INVENTORY_TO_WORLD_SOURCE = {"7item263"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item_rows() -> dict[str, list[dict]]:
    result = defaultdict(list)
    with (ROOT / "assets_dev/engine/data_tables/items.txt").open(encoding="cp1252", newline="") as stream:
        next(stream)
        for row in csv.DictReader(stream, delimiter="\t"):
            try:
                sprite_index = int(row["Sprite Index"])
            except (KeyError, ValueError):
                continue
            name = row.get("Pic File", "").strip().lower()
            if name:
                result[name].append({"item_id": row["Item #"], "item_name": row["Name"],
                                     "sprite_index": sprite_index})
    return result


def object_rows() -> dict[int, dict]:
    result = {}
    path = ROOT / "assets_dev/engine/data_tables/object_list.txt"
    for line in path.read_text(encoding="cp1252").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            result[int(parts[2])] = {"object_name": parts[0], "sprite_name": parts[1].lower()}
        except ValueError:
            continue
    return result


def rgb_similarity(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    visible = a[:, :, 3] > 0
    left = a[:, :, :3][visible].astype(np.float64)
    right = b[:, :, :3][visible].astype(np.float64)
    if len(left) < 10:
        return 0.0, 255.0
    correlation = float(np.corrcoef(left.ravel(), right.ravel())[0, 1])
    difference = float(np.median(np.abs(left - right)))
    return correlation, difference


def fit_world_master(world_art: Image.Image, restored_box: tuple[int, int, int, int],
                     placed_box: list[int], canvas_size: list[int]) -> tuple[Image.Image, str, list[int]]:
    cropped = world_art.crop(restored_box)
    width, height = canvas_size
    if 0 <= placed_box[0] and 0 <= placed_box[1] and placed_box[2] <= width and placed_box[3] <= height:
        method = "exact"
        x, y = placed_box[:2]
    else:
        scale = min(1.0, width / cropped.width, height / cropped.height)
        if scale < 1.0:
            size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
            cropped = cropped.resize(size, Image.Resampling.LANCZOS)
            method = "uniformly scaled to fit inventory canvas"
        else:
            method = "translated inside inventory canvas"
        center_x = (placed_box[0] + placed_box[2]) / 2
        center_y = (placed_box[1] + placed_box[3]) / 2
        x = max(0, min(width - cropped.width, round(center_x - cropped.width / 2)))
        y = max(0, min(height - cropped.height, round(center_y - cropped.height / 2)))
    result = Image.new("RGBA", (width, height))
    result.paste(cropped, (x, y))
    return result, method, [x, y, x + cropped.width, y + cropped.height]


def main() -> None:
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(";\n"))
    rows = item_rows()
    objects = object_rows()
    source_assets = json.loads((SPRITES / "sources.json").read_text())
    source_by_name = defaultdict(list)
    for asset_id, source in source_assets.items():
        for alias in source.get("aliases", []):
            source_by_name[alias["name"].lower()].append((asset_id, source, alias))
    accepted = defaultdict(list)
    for binding in json.loads((WORLD / "manifest.json").read_text())["bindings"]:
        accepted[binding["name"].lower()].append(binding)
    prior_primary = {}
    for name in ("inventory_regen_report.json", "component_reuse_report.json"):
        old = json.loads((HERE.parent / name).read_text())["items"]
        for target_id, row in old.items():
            if target_id in {f"engine--icons--{value}.bmp" for value in PRIMARY_NAMES}:
                prior_primary[target_id] = row["artifact_sha256"]

    candidates = HERE / "candidates"
    candidates.mkdir(parents=True, exist_ok=True)
    links = {}
    primary = {}
    totals = defaultdict(int)
    for item in catalog["items"]:
        if item["treatment"] != "inventory_items":
            continue
        totals["inventory_targets"] += 1
        match_rows = rows.get(item["name"].lower(), [])
        world_links = []
        for row in match_rows:
            obj = objects.get(row["sprite_index"])
            if obj:
                world_links.append({**row, **obj})
        if world_links:
            totals["linked_to_world_sprite"] += 1
        if any(accepted.get(link["sprite_name"]) for link in world_links):
            totals["linked_to_approved_world_sprite"] += 1
        record = {"item_name": item["name"], "world_links": world_links}
        links[item["id"]] = record
        original = Image.open(REVIEW / item["original"]).convert("RGBA")
        native_box = original.getchannel("A").getbbox()
        if not native_box:
            continue
        best = None
        for link in world_links:
            sprite_name = link["sprite_name"]
            for asset_id, source, alias in source_by_name.get(sprite_name, []):
                native_world = Image.open(SPRITES / source["native"]).convert("RGBA")
                world_box = native_world.getchannel("A").getbbox()
                if not world_box:
                    continue
                a = np.asarray(original.crop(native_box))
                b = np.asarray(native_world.crop(world_box))
                if a.shape != b.shape or not np.array_equal(a[:, :, 3], b[:, :, 3]):
                    continue
                correlation, median_difference = rgb_similarity(a, b)
                if best is None or correlation > best["source_rgb_correlation"]:
                    best = {"link": link, "asset_id": asset_id, "palette_id": alias["palette_id"],
                            "native_box": native_box, "world_box": world_box,
                            "source_rgb_correlation": correlation,
                            "source_rgb_median_difference": median_difference}
        if best is None:
            continue
        totals["identical_native_alpha_shape"] += 1
        record["native_match"] = {
            "sprite_name": best["link"]["sprite_name"],
            "asset_id": best["asset_id"],
            "palette_id": best["palette_id"],
            "inventory_box": list(best["native_box"]),
            "world_box": list(best["world_box"]),
            "rgb_correlation": round(best["source_rgb_correlation"], 4),
            "rgb_median_difference": round(best["source_rgb_median_difference"], 2),
        }
        if best["source_rgb_correlation"] < 0.9 or best["source_rgb_median_difference"] > 20:
            record["reuse_status"] = "same alpha shape, different artwork or colors"
            totals["alpha_only_mismatch"] += 1
            continue
        totals["same_native_drawing"] += 1
        bindings = [binding for binding in accepted[best["link"]["sprite_name"]]
                    if binding["palette_id"] == best["palette_id"]]
        if len(bindings) != 1:
            record["reuse_status"] = "no unique approved palette binding"
            totals["missing_approved_binding"] += 1
            continue
        binding = bindings[0]
        world_path = WORLD / binding["file"]
        if digest(world_path) != binding["sha256"]:
            raise ValueError(f"Approved world sprite changed: {world_path}")
        world_art = Image.open(world_path).convert("RGBA")
        restored_box = world_art.getchannel("A").getbbox()
        if not restored_box:
            raise ValueError(f"Approved world sprite is empty: {world_path}")
        dx = 2 * (best["native_box"][0] - best["world_box"][0])
        dy = 2 * (best["native_box"][1] - best["world_box"][1])
        placed_box = [restored_box[0] + dx, restored_box[1] + dy,
                      restored_box[2] + dx, restored_box[3] + dy]
        record["approved_world"] = {
            "path": str(world_path.relative_to(ROOT)), "sha256": binding["sha256"],
            "logical_size": binding["logical_size"], "placement_delta_2x": [dx, dy],
            "placed_box_2x": placed_box,
        }
        overhang = placed_box[0] < 0 or placed_box[1] < 0 or placed_box[2] > item["x2_size"][0] \
            or placed_box[3] > item["x2_size"][1]
        if overhang:
            totals["approved_world_overhang"] += 1
        if item["name"] in INVENTORY_TO_WORLD_SOURCE:
            record["reuse_status"] = "inventory restoration selected for ground sprite"
            totals["inventory_to_world_source"] += 1
            continue
        result, method, fitted_box = fit_world_master(world_art, restored_box, placed_box, item["x2_size"])
        artifact = candidates / f"{item['id']}.png"
        result.save(artifact, optimize=True)
        record["reuse_status"] = ("exact approved pixels placed on inventory canvas" if method == "exact"
                                  else "approved world master fitted to inventory canvas")
        record["fit_method"] = method
        record["fit_source_box_2x"] = list(restored_box)
        record["fit_placed_box_2x"] = fitted_box
        record["candidate"] = str(artifact.relative_to(REVIEW))
        record["candidate_sha256"] = digest(artifact)
        totals["fitted_approved_world_candidate"] += 1
        if overhang:
            totals["overhang_fitted"] += 1
        else:
            totals["exact_world_pixel_fit"] += 1
        if item["name"] in PRIMARY_NAMES:
            if item["id"] not in prior_primary:
                raise ValueError(f"Missing predecessor for requested primary: {item['id']}")
            primary[item["id"]] = {
                "status": "candidate_technical", "source_sha256": item["source_sha256"],
                "input_sha256": prior_primary[item["id"]],
                "artifact": record["candidate"], "artifact_sha256": record["candidate_sha256"],
                "origin": "Approved world sprite master",
                "method": f"lossless placement of approved {best['link']['sprite_name']} x2 pixels; "
                          f"same native silhouette and {best['source_rgb_correlation']:.3f} source RGB correlation",
                "world_sha256": binding["sha256"],
            }
    if set(primary) != {f"engine--icons--{name}.bmp" for name in PRIMARY_NAMES}:
        raise ValueError("The two requested item masters were not fitted")
    (HERE / "report.json").write_text(json.dumps({"schema": 1, "summary": dict(totals),
                                                 "items": links}, indent=2) + "\n")
    (HERE.parent / "shared_world_primary_report.json").write_text(
        json.dumps({"schema": 1, "items": primary}, indent=2) + "\n")
    print(json.dumps(dict(totals), indent=2))


if __name__ == "__main__":
    main()
