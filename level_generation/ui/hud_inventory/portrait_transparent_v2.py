"""Two-sheet-per-family transparent portrait restoration, with explicit return checks."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent
RUN = BASE / "review/second_pass/portrait_transparent_v2"
PREVIOUS = BASE / "review/second_pass/portrait_transparent_v1/manifest.json"
PACK = BASE / "review/second_pass/portrait_families"
REFERENCE_SIZE = (994, 728)
FRAME_SIZE = (118, 158)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def prepare():
    if (RUN / "manifest.json").exists():
        raise SystemExit("Run already prepared")
    prior = read(PREVIOUS)
    families = []
    for family in prior["families"]:
        entry = {"id": family["id"], "prefix": family["prefix"], "characters": family["characters"],
                 "frames": family["frames"], "references": family["references"],
                 "state": "missing_native" if family["state"] == "missing_native" else "pending",
                 "sheets": []}
        if entry["state"] == "missing_native":
            entry["reason"] = family["reason"]
            families.append(entry)
            continue
        for part in range(2):
            frames = entry["frames"][part * 28:(part + 1) * 28]
            sheet_id = "A" if part == 0 else "B"
            folder = RUN / entry["id"] / sheet_id
            folder.mkdir(parents=True, exist_ok=True)
            guide = Image.new("RGBA", REFERENCE_SIZE)
            for slot, frame in enumerate(frames):
                source = Path(frame["native"])
                if sha(source) != frame["native_sha256"]:
                    raise ValueError(f"Native source changed: {source}")
                native = Image.open(source).convert("RGBA")
                x, y = slot % 7 * 142 + 12, slot // 7 * 182 + 12
                guide.paste(native.resize(FRAME_SIZE, Image.Resampling.NEAREST), (x, y))
                frame[f"reference_rect_{sheet_id}"] = [x, y, *FRAME_SIZE]
            guide.save(folder / "native_layout.png")
            relevant = set(f["cell"] for f in frames)
            references = [r for r in family["references"] if relevant.intersection(r["covered_cells"])]
            if not references:
                references = family["references"][:1]
            refs = references[:3]
            paths = [str(folder / "native_layout.png")] + [r["path"] for r in refs]
            prompt = f'''Use case: identity-preserve.
Asset type: transparent player-portrait animation spritesheet, family {entry['prefix']}, part {sheet_id} of two.
Image 1 is the edit/layout target: EXACTLY 28 native poses in seven columns and four rows, read left to right then top to bottom. It is a nearest-enlarged geometry reference, not finished art. Its transparent gutters show intentional separation. Image 2 onward are earlier restored full-resolution masters for this SAME identity and fine painted detail, possibly in a different grid.
Re-restore all 28 native poses as coherent, finely painted fantasy portraits with genuine RGBA transparent backgrounds. Use the earlier restored faces/dragon/materials as the style and identity source. Preserve image 1's 28 poses, state order, head directions, facial landmarks, proportions, native offsets, scale and framing. Do not replace expressions with the neutral pose; do not complete partial heads. Keep all 28 portrait canvases with generous transparent gutters, exactly seven columns by four rows. Canvas aspect ratio 994:728, portrait logical canvas 59:79, portrait reference canvas 118:158 within 142x182 slots with 12px padding on each side. Output native sampling strictly greater than 2x in both axes, with actual new fine detail at 100% master view. No enlarged square pixels, pixel-art filter, blur-only smoothing or coarse facets.
Remove the copied green panel/backdrop behind EVERY portrait and any magenta from previous-master references. Outside each head and through genuine holes, output alpha=0. Solid face, hair, horns, scales, gold, jewelry and stone are opaque. Preserve intentional translucency only in ghost/fade states, injury and breath effects. Make soft antialiased edge pixels clean against white, dark and the green HUD panel; no magenta/red/yellow/white specks, halos, rectangular haze or stray pixels. No checkerboard, scenery, text or grid borders.
Do not crop-to-head, recenter, stretch, pack closer, redraw species, brighten whole sequences or invent features. Each output slot must be independently clean and must not touch its neighbor. Every pose must still read as the same person/creature and match its specific native frame, including faint, partial, damaged and petrified frames.
'''
            (folder / "prompt.txt").write_text(prompt)
            entry["sheets"].append({"id": sheet_id, "frames": [f["frame"] for f in frames],
                                     "input_paths": paths, "input_hashes": [sha(p) for p in paths],
                                     "prompt_sha256": sha(folder / "prompt.txt"), "attempts": [], "selected": None,
                                     "state": "pending"})
        families.append(entry)
    write(RUN / "manifest.json", {"schema": 2, "source_sha256": sha(PREVIOUS), "families": families})
    refresh()


def check(family, sheet, attempt):
    folder = RUN / family["id"] / sheet["id"] / attempt["id"]
    raw = Image.open(folder / "raw.png").convert("RGBA")
    sx, sy = raw.width / REFERENCE_SIZE[0], raw.height / REFERENCE_SIZE[1]
    alpha = np.asarray(raw.getchannel("A"))
    failures = []
    if min(2 * sx, 2 * sy) <= 2:
        failures.append("actual_sampling_not_above_x2")
    if abs(sx / sy - 1) > .01:
        failures.append("sheet_aspect_ratio_mismatch")
    if np.mean(alpha == 0) < .07:
        failures.append("background_not_transparent")
    output = Image.new("RGBA", (7 * 126, 4 * 166))
    details = []
    override_file = RUN / "extraction_overrides.json"
    overrides = read(override_file) if override_file.exists() else {}
    family_overrides = overrides.get(family["id"], {})
    grid_calibration = family_overrides.get("grid_calibration", {}).get(sheet["id"])
    if grid_calibration and grid_calibration["raw_sha256"] != sha(folder / "raw.png"):
        grid_calibration = None
    frames = [f for f in family["frames"] if f["frame"] in sheet["frames"]]
    (folder / "frames").mkdir(exist_ok=True)
    for slot, frame in enumerate(frames):
        x, y, w, h = frame[f"reference_rect_{sheet['id']}"]
        # Keep a small guard band inside each model slot to exclude accidental
        # fragments from the neighboring row. The 130:174 rectangle preserves
        # the native 59:79 canvas ratio to within rounding, without anisotropic scale.
        cell_x, cell_y = slot % 7 * 142, slot // 7 * 182
        use_reference_box = str(frame["frame"]) in family_overrides
        if use_reference_box:
            rect = [round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy)]
        else:
            rect = [round((cell_x + 6) * sx), round((cell_y + 4) * sy),
                    round((cell_x + 136) * sx), round((cell_y + 178) * sy)]
        if grid_calibration:
            column, row = slot % 7, slot // 7
            dx = round(grid_calibration["x_origin"] + column * grid_calibration["x_step"])
            dy = round(grid_calibration["y_origin"] + row * grid_calibration["y_step"])
            rect = [rect[0] + dx, rect[1] + dy, rect[2] + dx, rect[3] + dy]
        crop = raw.crop(rect)
        coverage = float(np.mean(np.asarray(crop.getchannel("A")) > 16))
        if crop.width / 59 <= 2 or crop.height / 79 <= 2:
            failures.append(f"frame_{frame['frame']:02d}_sampling")
        if coverage < .001:
            failures.append(f"frame_{frame['frame']:02d}_blank")
        preview = crop.convert("RGBa").resize(FRAME_SIZE, Image.Resampling.LANCZOS).convert("RGBA")
        preview.save(folder / "frames" / f"{frame['frame']:02d}.png")
        output.paste(preview, (slot % 7 * 126 + 4, slot // 7 * 166 + 4))
        details.append({"frame": frame["frame"], "raw_rect_ltrb": rect,
                        "extraction_policy": ("native_reference_box" if use_reference_box else "guarded_slot")
                        + ("+hash_bound_grid_calibration" if grid_calibration else ""),
                        "input_portrait_reference_rect": [x, y, w, h],
                        "sampling_xy": [crop.width / 59, crop.height / 79],
                        "occupied_fraction": coverage})
    output.save(folder / "contact_x2.png")
    checks = {"raw_sha256": sha(folder / "raw.png"), "size": raw.size,
              "sampling_xy": [2 * sx, 2 * sy], "aspect_error": abs(sx / sy - 1),
              "transparent_fraction": float(np.mean(alpha == 0)), "frames": details,
              "automatic_failures": failures,
              "warning": "Automatic checks do not establish frame correspondence, silhouette fidelity or fine detail."}
    write(folder / "checks.json", checks)
    attempt.update(raw_sha256=checks["raw_sha256"], state="technical_hold" if failures else "awaiting_visual_technical_review",
                   automatic_failures=failures)


def record(family_id, sheet_id, source, receipt, prompt_file=None, reference_paths=None):
    manifest = read(RUN / "manifest.json")
    family = next(f for f in manifest["families"] if f["id"] == family_id)
    sheet = next(s for s in family["sheets"] if s["id"] == sheet_id)
    folder = RUN / family_id / sheet_id
    for path, expected in zip(sheet["input_paths"], sheet["input_hashes"]):
        if sha(path) != expected:
            raise ValueError(f"Input changed: {path}")
    if sha(folder / "prompt.txt") != sheet["prompt_sha256"]:
        raise ValueError("Prompt changed")
    active_prompt = prompt_file or folder / "prompt.txt"
    if not active_prompt.is_file():
        raise ValueError(f"Prompt missing: {active_prompt}")
    active_references = reference_paths or [Path(path) for path in sheet["input_paths"]]
    for path in active_references:
        if not path.is_file():
            raise ValueError(f"Reference missing: {path}")
    actual = sha(source)
    if any(a["raw_sha256"] == actual for a in sheet["attempts"]):
        raise ValueError("Duplicate return")
    attempt = {"id": f"attempt_{len(sheet['attempts']) + 1:02d}", "receipt": receipt,
               "generated_path": str(source), "prompt_sha256": sha(active_prompt),
               "reference_paths": [str(path) for path in active_references],
               "reference_sha256s": [sha(path) for path in active_references]}
    target = folder / attempt["id"]
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source, target / "raw.png")
    shutil.copy2(active_prompt, target / "prompt.txt")
    check(family, sheet, attempt)
    write(target / "receipt.json", attempt)
    sheet["attempts"].append(attempt)
    sheet["selected"] = attempt["id"]
    sheet["state"] = attempt["state"]
    if all(s["selected"] for s in family["sheets"]):
        family["state"] = ("technical_hold" if any(s["state"] == "technical_hold" for s in family["sheets"])
                           else "awaiting_visual_technical_review")
    else:
        family["state"] = "partial"
    write(RUN / "manifest.json", manifest)
    refresh()


def recheck(family_ids=None):
    manifest = read(RUN / "manifest.json")
    for family in manifest["families"]:
        if family_ids and family["id"] not in family_ids:
            continue
        if not family["sheets"]:
            continue
        for sheet in family["sheets"]:
            if not sheet["selected"]:
                continue
            attempt = next(a for a in sheet["attempts"] if a["id"] == sheet["selected"])
            source = RUN / family["id"] / sheet["id"] / attempt["id"] / "raw.png"
            if sha(source) != attempt["raw_sha256"]:
                raise ValueError(f"Raw artwork changed: {source}")
            check(family, sheet, attempt)
            sheet["state"] = attempt["state"]
        family["state"] = ("awaiting_visual_technical_review" if all(s["selected"] for s in family["sheets"])
                           else "partial" if any(s["selected"] for s in family["sheets"]) else "pending")
    write(RUN / "manifest.json", manifest)
    refresh()


def remove_mixed_references():
    """Revise unsent jobs that accidentally included another identity in a raw master."""
    manifest = read(RUN / "manifest.json")
    raw_masters = read(PACK / "manifest.json")["raw_masters"]
    master_by_path = {record["raw"]: record for record in raw_masters.values()}
    revised = []
    for family in manifest["families"]:
        for sheet in family["sheets"]:
            if sheet["attempts"]:
                continue
            inputs = sheet["input_paths"]
            mixed = []
            pure = []
            for path in inputs[1:]:
                record = master_by_path.get(path)
                if record and any(not cell.startswith("engine--icons--" + family["id"])
                                  for cell in record["selected_cells"]):
                    mixed.append(path)
                else:
                    pure.append(path)
            if not mixed:
                continue
            contact = PACK / family["id"] / "candidate_x2.png"
            if not contact.is_file():
                raise ValueError(f"Family preview missing: {contact}")
            sheet["input_paths"] = [inputs[0], str(contact)] + pure[:2]
            sheet["input_hashes"] = [sha(p) for p in sheet["input_paths"]]
            sheet["reference_revision"] = {"removed_mixed_master_paths": mixed,
                                           "replacement": str(contact),
                                           "reason": "Avoid presenting another player identity as same-family art."}
            folder = RUN / family["id"] / sheet["id"]
            prompt = (folder / "prompt.txt").read_text()
            prompt = prompt.replace(
                "Image 2 onward are earlier restored full-resolution masters for this SAME identity and fine painted detail, possibly in a different grid.",
                "Image 2 is a DIAGNOSTIC CONTACT of earlier restored candidate previews for only this identity; it has labels and provisional slots, so use the face art but not labels or the review layout. Images 3 onward, when present, are full-resolution previous masters for this identity. Some contact cells are provisional, and Image 1 controls the exact pose and order.")
            (folder / "prompt.txt").write_text(prompt)
            sheet["prompt_sha256"] = sha(folder / "prompt.txt")
            revised.append(f"{family['id']}{sheet['id']}")
    write(RUN / "manifest.json", manifest)
    refresh()
    print("Revised unsent mixed-identity inputs:", ", ".join(revised))


def review(family_id, evidence_path):
    manifest = read(RUN / "manifest.json")
    family = next(f for f in manifest["families"] if f["id"] == family_id)
    if not all(s["selected"] for s in family["sheets"]):
        raise ValueError("Both returned sheets are required for family review")
    evidence = read(evidence_path)
    expected = [next(a for a in s["attempts"] if a["id"] == s["selected"])["raw_sha256"]
                for s in family["sheets"]]
    if evidence.get("raw_sha256s") != expected:
        raise ValueError("Review source hashes changed")
    if evidence.get("verdict") not in ["ready_for_user", "technical_hold"]:
        raise ValueError("Invalid technical verdict")
    required = ["master_detail", "frame_order_count", "native_proportions_placement", "alpha_edges",
                "x2_detail", "light_dark_hud_composite"]
    if any(not evidence.get(key) for key in required):
        raise ValueError("Missing visual technical evidence")
    if evidence["verdict"] == "ready_for_user":
        for sheet in family["sheets"]:
            selected = next(a for a in sheet["attempts"] if a["id"] == sheet["selected"])
            if selected["automatic_failures"]:
                raise ValueError("Automatic failure remains")
    write(RUN / family_id / "technical_review.json", evidence)
    family["state"] = evidence["verdict"]
    if evidence["verdict"] == "ready_for_user":
        family.pop("reason", None)
    else:
        family["reason"] = evidence.get("reason", "Visual technical review requires a new attempt")
    write(RUN / "manifest.json", manifest)
    refresh()


def hold(family_id, reason):
    manifest = read(RUN / "manifest.json")
    family = next(f for f in manifest["families"] if f["id"] == family_id)
    if not any(sheet["selected"] for sheet in family["sheets"]):
        raise ValueError("Only generated work can be put on technical hold")
    family["state"] = "technical_hold"
    family["reason"] = reason
    write(RUN / "manifest.json", manifest)
    refresh()


def refresh():
    manifest = read(RUN / "manifest.json")
    counts = {}
    for family in manifest["families"]:
        counts[family["state"]] = counts.get(family["state"], 0) + 1
    manifest["summary"] = counts
    write(RUN / "manifest.json", manifest)
    # One browser-facing family record; generated master halves are retained separately.
    gallery = {"summary": counts, "families": []}
    prior_root = BASE / "review/second_pass/portrait_transparent_v1"
    for family in manifest["families"]:
        item = {"id": family["id"], "prefix": family["prefix"], "characters": family["characters"],
                "state": family["state"], "frames": family["frames"], "references": family["references"],
                "attempts": [], "selected": None, "reason": family.get("reason")}
        original_guide = prior_root / family["id"] / "native_layout.png"
        if original_guide.exists():
            shutil.copy2(original_guide, RUN / family["id"] / "native_layout.png")
        if all(sheet["selected"] for sheet in family["sheets"]):
            hashes = [next(a for a in s["attempts"] if a["id"] == s["selected"])["raw_sha256"]
                      for s in family["sheets"]]
            combined_hash = hashlib.sha256("".join(hashes).encode()).hexdigest()
            combined = RUN / family["id"] / "combined"
            (combined / "frames").mkdir(parents=True, exist_ok=True)
            sheet_image = Image.new("RGBA", (8 * 134, 7 * 190))
            masters = []
            for sheet in family["sheets"]:
                part = RUN / family["id"] / sheet["id"] / sheet["selected"]
                masters.append(f"{sheet['id']}/{sheet['selected']}/raw.png")
                for frame_number in sheet["frames"]:
                    name = f"{frame_number:02d}.png"
                    src = part / "frames" / name
                    shutil.copy2(src, combined / "frames" / name)
                    i = frame_number - 1
                    sheet_image.paste(Image.open(src), (i % 8 * 134 + 8, i // 8 * 190 + 24))
            sheet_image.save(combined / "contact_x2.png")
            item["selected"] = "combined"
            item["attempts"].append({"id": "combined", "raw_sha256": combined_hash,
                                     "master_paths": masters, "status": family["state"]})
        gallery["families"].append(item)
    (RUN / "data.js").write_text("window.PORTRAITS = " + json.dumps(gallery).replace("<", "\\u003c") + ";\n")
    for name in ["index.html", "app.js", "style.css"]:
        shutil.copy2(BASE / "portrait_review_ui" / name, RUN / name)
    print(json.dumps(counts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("status")
    rech = sub.add_parser("recheck")
    rech.add_argument("families", nargs="*")
    sub.add_parser("remove-mixed-references")
    payload = sub.add_parser("payload")
    payload.add_argument("families", nargs="+")
    rec = sub.add_parser("record")
    rec.add_argument("family")
    rec.add_argument("sheet", choices=["A", "B"])
    rec.add_argument("source", type=Path)
    rec.add_argument("--receipt", default="Built-in imagegen result")
    rec.add_argument("--prompt-file", type=Path)
    rec.add_argument("--reference", action="append", type=Path)
    rev = sub.add_parser("review")
    rev.add_argument("family")
    rev.add_argument("evidence", type=Path)
    hld = sub.add_parser("hold")
    hld.add_argument("family")
    hld.add_argument("reason")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "record":
        record(args.family, args.sheet, args.source, args.receipt, args.prompt_file, args.reference)
    elif args.command == "review":
        review(args.family, args.evidence)
    elif args.command == "hold":
        hold(args.family, args.reason)
    elif args.command == "recheck":
        recheck(args.families)
    elif args.command == "remove-mixed-references":
        remove_mixed_references()
    elif args.command == "payload":
        manifest = read(RUN / "manifest.json")
        jobs = []
        for family in manifest["families"]:
            if family["id"] not in args.families:
                continue
            for sheet in family["sheets"]:
                if sheet["selected"]:
                    continue
                folder = RUN / family["id"] / sheet["id"]
                for path, expected in zip(sheet["input_paths"], sheet["input_hashes"]):
                    if sha(path) != expected:
                        raise ValueError(f"Input changed: {path}")
                jobs.append({"family": family["id"], "sheet": sheet["id"],
                             "input_paths": sheet["input_paths"],
                             "prompt": (folder / "prompt.txt").read_text(),
                             "prompt_sha256": sheet["prompt_sha256"]})
        print(json.dumps(jobs))
    else:
        refresh()
