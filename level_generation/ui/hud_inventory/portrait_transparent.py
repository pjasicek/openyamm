"""Prepare, inventory and technically gate the user-authorized portrait re-restoration.

No network calls. Generated artwork enters only through the built-in imagegen tool.
All image writes here are reference assembly or diagnostic/export derivations.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
PACK = BASE / "review/second_pass/portrait_families"
RUN = BASE / "review/second_pass/portrait_transparent_v1"
SIZE = (1008, 1162)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    manifest_path = RUN / "manifest.json"
    if manifest_path.exists():
        raise SystemExit("Run already prepared; use status, record or review. Never overwrite a run.")
    inventory = read(PACK / "manifest.json")
    families = []
    for summary in inventory["families"]:
        family_id = summary["path"]
        family = read(PACK / family_id / "manifest.json")
        folder = RUN / family_id
        folder.mkdir(parents=True, exist_ok=True)
        entry = {"id": family_id, "prefix": summary["prefix"], "characters": summary["characters"],
                 "state": "pending", "frames": [], "references": [], "attempts": [], "selected": None}
        if any(not f.get("source") for f in family["frames"]):
            entry.update(state="missing_native", reason="Table references missing native frames; no invention.")
            families.append(entry)
            continue
        guide = Image.new("RGB", SIZE, (255, 0, 255))
        for i, frame in enumerate(family["frames"]):
            src = ROOT / frame["source"]["source_path"]
            if digest(src) != frame["source"]["source_sha256"]:
                raise ValueError(f"Native source changed: {src}")
            native = Image.open(src).convert("RGB")
            if native.size != (59, 79):
                raise ValueError(f"Unexpected native size: {src}: {native.size}")
            x, y = (i % 8) * 126 + 4, (i // 8) * 166 + 4
            guide.paste(native.resize((118, 158), Image.Resampling.NEAREST), (x, y))
            entry["frames"].append({"cell": frame["cell"], "name": frame["name"], "frame": frame["frame"],
                                    "native": str(src), "native_sha256": digest(src),
                                    "reference_rect": [x, y, 118, 158]})
        guide.save(folder / "native_layout.png")
        # Full-resolution retained references, greedily covering this identity; no guessed crops.
        wanted = {f["cell"] for f in entry["frames"]}
        masters = {}
        for master in inventory["raw_masters"].values():
            if wanted.intersection(master["selected_cells"]):
                masters.setdefault(master["raw_sha256"], master)
        uncovered = set(wanted)
        while masters and uncovered and len(entry["references"]) < 4:
            best = max(masters.values(), key=lambda m: len(uncovered.intersection(m["selected_cells"])))
            coverage = uncovered.intersection(best["selected_cells"])
            if not coverage:
                break
            if digest(best["raw"]) != best["raw_sha256"]:
                raise ValueError(f"Retained raw changed: {best['raw']}")
            entry["references"].append({"path": best["raw"], "sha256": best["raw_sha256"],
                                        "master_id": best["id"], "covered_cells": sorted(coverage)})
            uncovered -= coverage
            masters.pop(best["raw_sha256"])
        entry["native_only_reference_cells"] = sorted(uncovered)
        entry["input_paths"] = [str(folder / "native_layout.png")] + [r["path"] for r in entry["references"]]
        entry["input_hashes"] = [digest(p) for p in entry["input_paths"]]
        prompt = f'''Use case: identity-preserve.
Asset type: restored game player-portrait animation spritesheet, family {summary['prefix']}.
Primary request: re-restore the EXISTING restored portrait art as high-resolution continuous painted fantasy portraits with GENUINE TRANSPARENT BACKGROUNDS. Keep the complete generated artwork, not just a mask.
Input image 1: native GEOMETRY AND FRAME-ORDER GUIDE only, 56 distinct frames in an 8-column by 7-row grid, read left-to-right top-to-bottom. It is a nearest-enlarged historical reference, NOT the desired pixelated finish.
Input images 2 onward: full-resolution PREVIOUS RESTORED MASTERS for identity, colors and resolved detail. They may contain subsets or different grid layouts. Do not copy their grid. Use their character artwork to improve all corresponding poses in image 1. If a frame has no restored reference, reconstruct that native pose consistently with its restored siblings.
Output layout: exactly 56 occupied slots, 8 columns and 7 rows, one identity only, matching image 1. Canvas aspect 1008:1162. Each logical slot is 63 by 83 native pixels; its portrait canvas is 59 by 79 with 2-pixel padding on every side. Keep the full portrait coordinates, proportions, margins, head position and scale; do not stretch faces, recenter, crop-to-head or enlarge tiny partial poses. Preserve distinct gaze, eye closure, mouth opening, tilt, faint/low poses and status effects in their exact slots. No duplicated or omitted frames.
Resolution: deliver a genuinely rendered high-resolution master, ideally 2016 by 2324, never an interpolated enlargement. Every native 59x79 portrait must have more than 118x158 actual generated pixels of corresponding canvas/detail. Keep gutters small and empty, not inflated to fake sampling.
Finish: reconstruct continuous curved surfaces, resolved eyes/lips and fine hair/material detail. NO enlarged source-pixel squares, mosaic shading, staircase outlines, pixel-art filters, coarse facets, blur-only upscaling or plastic smoothing. Preserve original character identity, age, species, palette and period fantasy-rendered aesthetic. Modest attractive refinements are allowed, but no redesign, exaggerated eyes or altered head proportions. Consistent lighting/detail across all frames; no progressive brightening.
Transparency: remove the copied background/panel and ALL magenta gutters. Actual RGBA alpha=0 outside the character and inside true holes, not a painted checkerboard or colored matte. Keep faces and solid materials opaque, natural antialiased edge transitions and fine hair. Preserve green skin, dark hair, gold jewelry, horns, intrinsic mist/glow, injury details and stone/status effects as foreground. No green/magenta fringe, new shadows, labels, borders or added scenery.
Before returning, verify all 56 positions against image 1. The deliberately partial heads are NOT missing content to complete. Do not replace any difficult expression with the neutral face.
'''
        (folder / "prompt.txt").write_text(prompt)
        entry["prompt_sha256"] = digest(folder / "prompt.txt")
        families.append(entry)
    manifest = {"schema": 1, "scope": "data-referenced player portraits only", "tool": "built-in imagegen",
                "compositing_override": "user_authorized_foreground_alpha_rerestoration",
                "source_manifest_sha256": digest(PACK / "manifest.json"), "families": families}
    write(manifest_path, manifest)
    refresh()


def analyze(entry, attempt):
    folder = RUN / entry["id"] / attempt["id"]
    image = Image.open(folder / "raw.png").convert("RGBA")
    width, height = image.size
    sx, sy = width / SIZE[0], height / SIZE[1]
    alpha = np.array(image.getchannel("A"))
    checks = {"raw_sha256": digest(folder / "raw.png"), "size": [width, height],
              "nominal_sampling_xy": [sx * 2, sy * 2], "sheet_aspect_error": abs(sx / sy - 1),
              "transparent_fraction": float((alpha == 0).mean()), "frames": [],
              "note": "Nominal coordinates only until full-sheet/native correspondence is visually verified."}
    errors = []
    if min(sx, sy) * 2 <= 2:
        errors.append("insufficient_actual_master_sampling")
    if checks["sheet_aspect_error"] > .005:
        errors.append("sheet_aspect_mismatch")
    if checks["transparent_fraction"] < .05:
        errors.append("missing_real_transparency")
    contact = Image.new("RGBA", SIZE)
    frames_dir = folder / "frames"
    frames_dir.mkdir(exist_ok=True)
    for frame in entry["frames"]:
        x, y, w, h = frame["reference_rect"]
        rect = [round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy)]
        crop = image.crop(rect)
        a = np.array(crop.getchannel("A"))
        occupied = float((a > 16).mean())
        sample = [crop.width / 59, crop.height / 79]
        if min(sample) <= 2:
            errors.append(f"{frame['name']}:sampling")
        if occupied < .001:
            errors.append(f"{frame['name']}:blank")
        checks["frames"].append({"cell": frame["cell"], "raw_rect_ltrb": rect,
                                  "nominal_sampling_xy": sample, "occupied_fraction": occupied})
        # Exact native-canvas diagnostic; full source rect, never alpha trimming/recentering.
        export = crop.convert("RGBa").resize((118, 158), Image.Resampling.LANCZOS).convert("RGBA")
        export.save(frames_dir / f"{frame['frame']:02d}.png")
        contact.paste(export, (x, y))
    contact.save(folder / "contact_x2.png")
    checks["automatic_failures"] = errors
    write(folder / "checks.json", checks)
    attempt.update(raw_sha256=checks["raw_sha256"], automatic_failures=errors,
                   state="technical_hold" if errors else "awaiting_visual_technical_review")


def record(family_id, source, receipt, prompt_path=None, parent=None):
    manifest = read(RUN / "manifest.json")
    entry = next(f for f in manifest["families"] if f["id"] == family_id)
    for path, expected in zip(entry["input_paths"], entry["input_hashes"]):
        if digest(path) != expected:
            raise ValueError(f"Input changed: {path}")
    if prompt_path is None:
        prompt_path = RUN / family_id / "prompt.txt"
        if digest(prompt_path) != entry["prompt_sha256"]:
            raise ValueError("Prompt changed; create an explicit new run/revision")
    else:
        prompt_path = prompt_path.resolve()
        if not prompt_path.is_file() or parent is None:
            raise ValueError("Repair requires a saved prompt and parent attempt")
        prior = next((a for a in entry["attempts"] if a["id"] == parent), None)
        if prior is None or digest(RUN / family_id / parent / "raw.png") != prior["raw_sha256"]:
            raise ValueError("Repair parent attempt changed or missing")
    output_hash = digest(source)
    if any(a.get("raw_sha256") == output_hash for a in entry["attempts"]):
        raise ValueError("Return already recorded")
    attempt = {"id": f"attempt_{len(entry['attempts']) + 1:02d}", "tool": "built-in imagegen",
               "generated_path": str(source), "receipt": receipt, "prompt_sha256": digest(prompt_path),
               "parent_attempt": parent}
    folder = RUN / family_id / attempt["id"]
    folder.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source, folder / "raw.png")
    shutil.copy2(prompt_path, folder / "prompt.txt")
    write(folder / "receipt.json", attempt)
    analyze(entry, attempt)
    entry["attempts"].append(attempt)
    entry["state"] = attempt["state"]
    entry["selected"] = attempt["id"]
    write(RUN / "manifest.json", manifest)
    refresh()


def review(family_id, evidence_path):
    manifest = read(RUN / "manifest.json")
    entry = next(f for f in manifest["families"] if f["id"] == family_id)
    attempt = next(a for a in entry["attempts"] if a["id"] == entry["selected"])
    evidence = read(evidence_path)
    if evidence["raw_sha256"] != attempt["raw_sha256"]:
        raise ValueError("Review hash does not match selected raw")
    required = ["master_detail", "frame_order_count", "native_proportions_placement", "alpha_edges", "x2_detail"]
    if any(not evidence.get(key) for key in required):
        raise ValueError("Missing visual technical evidence")
    if evidence["verdict"] not in ["ready_for_user", "technical_hold"]:
        raise ValueError("Invalid verdict")
    if evidence["verdict"] == "ready_for_user" and attempt["automatic_failures"]:
        raise ValueError("Automatic failures remain")
    write(RUN / family_id / attempt["id"] / "review.json", evidence)
    attempt["state"] = entry["state"] = evidence["verdict"]
    write(RUN / "manifest.json", manifest)
    refresh()


def refresh():
    manifest = read(RUN / "manifest.json")
    summary = {}
    for family in manifest["families"]:
        summary[family["state"]] = summary.get(family["state"], 0) + 1
    manifest["summary"] = summary
    write(RUN / "manifest.json", manifest)
    # Embedded data works over file:// without a server or fetch permissions.
    (RUN / "data.js").write_text("window.PORTRAITS = " + json.dumps(manifest).replace("<", "\\u003c") + ";\n")
    for name in ["index.html", "app.js", "style.css"]:
        source = BASE / "portrait_review_ui" / name
        if source.exists():
            shutil.copy2(source, RUN / name)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("status")
    rec = sub.add_parser("record")
    rec.add_argument("family")
    rec.add_argument("source", type=Path)
    rec.add_argument("--receipt", default="Built-in tool returned local image")
    rec.add_argument("--prompt", type=Path)
    rec.add_argument("--parent")
    rev = sub.add_parser("review")
    rev.add_argument("family")
    rev.add_argument("evidence", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "record":
        record(args.family, args.source, args.receipt, args.prompt, args.parent)
    elif args.command == "review":
        review(args.family, args.evidence)
    else:
        refresh()
