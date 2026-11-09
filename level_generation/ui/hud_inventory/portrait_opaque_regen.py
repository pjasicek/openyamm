"""Prepare and assemble a fresh, review-only opaque PC portrait regeneration run."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "review/second_pass/portrait_transparent_v2/manifest.json"
RUNS = {"approved_six": HERE / "review/second_pass/portrait_opaque_regen_v1",
        "remaining": HERE / "review/second_pass/portrait_opaque_regen_remaining_v1"}
APPROVED_SIX = ("7pc01", "7pc19", "pc04", "pc06", "pc23", "pc28")
SHEET_SIZE = (994, 728)
PANEL_SIZE = (118, 158)
SLOT_SIZE = (142, 182)
PADDING = 12


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prompt(family_id, part):
    return f"""Use case: identity-preserve.
Asset type: fresh high-resolution restoration of an opaque fantasy-game player portrait spritesheet, {family_id} part {part} of two.
Input image: Image 1 is the EDIT TARGET and authoritative geometry reference, not finished high-resolution art. It contains exactly 28 different native portrait frames in seven columns and four rows, in reading order. The flat magenta areas are gutters outside the portrait panels, NOT part of any portrait.
Primary request: Repaint all 28 portraits as genuinely restored, finely detailed pre-rendered/painted fantasy-game art. Replace low-resolution square-pixel structure with continuous facial, hair, clothing and material contours and fine coherent shading. Retain the original muted palette and lighting; do not globally brighten the sequence.
Composition and background: Preserve every frame's original 59:79 full-canvas rectangle, head scale, horizontal and vertical placement, viewing direction, expression, pose and partial/low/faded state. Crucially, KEEP the original opaque green/gray painted background inside every portrait rectangle. Do not remove the backgrounds or make portrait cutouts. Keep the exterior gutters flat pure magenta and empty, with no labels, borders, text, objects or stray pixels. Keep exactly seven columns and four rows with independent rectangles; no merging panels or reordering.
Geometry: The supplied 994:728 sheet has 142x182 slots, each containing a 118x158 nearest-neighbor enlargement of the native 59x79 portrait at 12px inset. Preserve this sheet aspect, slot pitch, panel aspect, panel boundaries and internal subject registration. The returned master must have more than two genuinely generated pixels per native pixel in BOTH axes for every portrait; do not meet that by merely enlarging source pixels.
Identity and detail: Keep all 28 states distinct and recognizable as the same character, including closed eyes, angled heads, injury, petrification, ghost/fade, raised/lowered/partial poses, and mouth/gaze differences wherever present in Image 1. Refine the existing art rather than inventing anatomy, accessories, expressions or scenery.
Gutter cleanliness: Magenta must NEVER bleed, glow, tint, stripe, or intrude into a portrait panel, even along a one-pixel edge. Keep all four edges of every green-backed rectangle clean and complete, including the bottom row.
Avoid: pixel-art filters, enlarged rectangular pixels, staircase contours, blur-only smoothing, coarse faceted shading, photo realism, beauty retouching, head recentering, rescaling, stretching, cropped heads, transparent portrait backgrounds, altered character identity, new text or watermarks.
"""


def prepare(run_name):
    run = RUNS[run_name]
    if (run / "manifest.json").exists():
        raise SystemExit(f"Run already prepared: {run}")
    source = json.loads(SOURCE.read_text())
    families = {entry["id"]: entry for entry in source["families"]}
    family_ids = (APPROVED_SIX if run_name == "approved_six" else
                  [entry["id"] for entry in source["families"]
                   if entry["id"] not in APPROVED_SIX and entry["state"] != "missing_native"
                   and len(entry["frames"]) == 56])
    result = {"schema": 1, "purpose": "review_only_not_accepted_or_installed",
              "source_manifest": str(SOURCE), "source_manifest_sha256": sha256(SOURCE),
              "prior_user_approved_families": list(APPROVED_SIX) if run_name == "remaining" else [],
              "excluded_missing_native": [entry["id"] for entry in source["families"]
                                          if entry["state"] == "missing_native"],
              "families": []}
    for family_id in family_ids:
        family = families[family_id]
        if len(family["frames"]) != 56:
            raise ValueError(f"Expected 56 frames for {family_id}")
        out_family = {"id": family_id, "prefix": family["prefix"], "sheets": []}
        for half, part in enumerate(("A", "B")):
            folder = run / family_id / part
            folder.mkdir(parents=True, exist_ok=False)
            reference = Image.new("RGB", SHEET_SIZE, (255, 0, 255))
            frames = []
            for slot, frame in enumerate(family["frames"][half * 28:(half + 1) * 28]):
                native_path = Path(frame["native"])
                if sha256(native_path) != frame["native_sha256"]:
                    raise ValueError(f"Native frame changed: {native_path}")
                native = Image.open(native_path).convert("RGB")
                if native.size != (59, 79):
                    raise ValueError(f"Unexpected native dimensions: {native_path} {native.size}")
                x = slot % 7 * SLOT_SIZE[0] + PADDING
                y = slot // 7 * SLOT_SIZE[1] + PADDING
                reference.paste(native.resize(PANEL_SIZE, Image.Resampling.NEAREST), (x, y))
                frames.append({"frame": frame["frame"], "name": frame["name"],
                               "native": str(native_path), "native_sha256": frame["native_sha256"],
                               "slot": slot, "reference_rect": [x, y, *PANEL_SIZE]})
            reference_path = folder / "reference.png"
            prompt_path = folder / "prompt.txt"
            reference.save(reference_path)
            prompt_path.write_text(prompt(family_id, part))
            out_family["sheets"].append({"part": part, "frames": frames,
                                         "reference": str(reference_path),
                                         "reference_sha256": sha256(reference_path),
                                         "prompt": str(prompt_path), "prompt_sha256": sha256(prompt_path),
                                         "raw": None, "status": "prepared"})
        result["families"].append(out_family)
    (run / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Prepared {len(result['families'])} families / {2 * len(result['families'])} sheets: {run}")


def prepare_safe_b_prompts():
    run = RUNS["remaining"]
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    template_path = run / "7pc02/B/prompt_safe.txt"
    template = template_path.read_text()
    for family in manifest["families"]:
        sheet = next(sheet for sheet in family["sheets"] if sheet["part"] == "B")
        path = run / family["id"] / "B/prompt_safe.txt"
        content = template.replace("7pc02", family["id"])
        if path.exists():
            if path.read_text() != content:
                raise ValueError(f"Existing safe prompt differs from template: {path}")
        else:
            path.write_text(content)
        sheet["prompt"] = str(path)
        sheet["prompt_sha256"] = sha256(path)
        if not (run / family["id"] / "B/raw.png").exists():
            sheet["status"] = "safe_prompt_prepared"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Prepared non-graphic B-sheet prompts:", len(manifest["families"]))


def spans(values):
    boundaries = np.flatnonzero(np.diff(np.r_[False, values, False].astype(np.int8)))
    return [(int(first), int(last)) for first, last in zip(boundaries[::2], boundaries[1::2])]


def magenta_mask(rgb):
    pixels = np.asarray(rgb, dtype=np.int16)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    return ((red > 180) & (blue > 180) & (green < 90)
            & (red - green > 100) & (blue - green > 100))


def measure_panels(raw):
    magenta = magenta_mask(raw)
    columns = spans((~magenta).mean(axis=0) > 0.5)
    rows = spans((~magenta).mean(axis=1) > 0.5)
    if len(columns) != 7 or len(rows) != 4:
        raise ValueError(f"Unable to measure 7x4 portrait panels: {columns}, {rows}")
    if abs(raw.width / raw.height / (SHEET_SIZE[0] / SHEET_SIZE[1]) - 1) > 0.01:
        raise ValueError(f"Returned sheet aspect differs from reference: {raw.size}")
    panels = []
    for slot in range(28):
        left, right = columns[slot % 7]
        top, bottom = rows[slot // 7]
        width, height = right - left, bottom - top
        sampling = (width / 59, height / 79)
        aspect_error = abs((width / height) / (59 / 79) - 1)
        # Small model gutter drift is handled by isotropic fit; cap the actual
        # edge loss so an incorrect panel cannot pass as a harmless ratio error.
        edge_trim = ((width - height * (59 / 79)) / 2, 0.0) if width / height > 59 / 79 else (
            0.0, (height - width / (59 / 79)) / 2)
        if min(sampling) <= 2 or aspect_error > 0.025 or max(edge_trim) > 3.0:
            raise ValueError(f"Panel {slot + 1} fails x2/aspect check: {width}x{height}")
        interior = magenta[top + 3:bottom - 3, left + 3:right - 3]
        magenta_fraction = float(interior.mean())
        # Magenta eyes and jewels are legitimate in some original portraits.
        # This catches large pure-gutter intrusions; diffuse spill still needs visual review.
        if magenta_fraction > 0.03:
            raise ValueError(f"Panel {slot + 1} has magenta contamination: {magenta_fraction:.2%}")
        panels.append({"slot": slot, "raw_rect_ltrb": [left, top, right, bottom],
                       "sampling_xy": [round(value, 4) for value in sampling],
                       "aspect_error": round(aspect_error, 6),
                       "symmetric_edge_trim_px": [round(max(0, value), 4) for value in edge_trim],
                       "magenta_interior_fraction": round(magenta_fraction, 6)})
    return {"columns": columns, "rows": rows, "panels": panels}


def assemble(run_name, partial=False):
    run = RUNS[run_name]
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    summary = {"purpose": "review_only_not_accepted_or_installed", "families": 0,
               "sheets": 0, "frames": 0, "minimum_sampling_xy": [float("inf"), float("inf")],
               "maximum_aspect_error": 0.0, "maximum_symmetric_edge_trim_px": 0.0,
               "sheet_reports": []}
    for family in manifest["families"]:
        family_id = family["id"]
        original_dir = run / family_id / "originals"
        restored_dir = run / family_id / "restored"
        original_dir.mkdir(exist_ok=True)
        restored_dir.mkdir(exist_ok=True)
        for sheet in family["sheets"]:
            part = sheet["part"]
            folder = run / family_id / part
            raw_name = ("raw_attempt_02.png" if run_name == "approved_six"
                        and (family_id, part) == ("pc06", "A") else "raw.png")
            raw_path = folder / raw_name
            if partial and not raw_path.is_file():
                continue
            if sha256(sheet["reference"]) != sheet["reference_sha256"]:
                raise ValueError(f"Reference changed: {sheet['reference']}")
            with Image.open(raw_path) as image:
                alpha = image.getchannel("A") if "A" in image.getbands() else None
                if alpha is not None and alpha.getextrema() != (255, 255):
                    raise ValueError(f"Raw sheet unexpectedly has transparent pixels: {raw_path}")
                raw = image.convert("RGB")
            measurement = measure_panels(raw)
            contact = Image.new("RGB", SHEET_SIZE, (255, 0, 255))
            for frame, panel in zip(sheet["frames"], measurement["panels"]):
                native_path = Path(frame["native"])
                if sha256(native_path) != frame["native_sha256"]:
                    raise ValueError(f"Native source changed: {native_path}")
                native = Image.open(native_path).convert("RGB")
                if native.size != (59, 79):
                    raise ValueError(f"Native frame has wrong size: {native_path}")
                number = frame["frame"]
                original = native.resize(PANEL_SIZE, Image.Resampling.NEAREST)
                original.save(original_dir / f"{number:02d}.png")
                crop = raw.crop(panel["raw_rect_ltrb"])
                if run_name == "remaining":
                    # Discard the model's one-pixel anti-aliased gutter edge, never subject-fit.
                    crop = crop.crop((2, 2, crop.width - 2, crop.height - 2))
                restored = ImageOps.fit(crop, PANEL_SIZE,
                                        method=Image.Resampling.LANCZOS)
                if run_name == "remaining":
                    restored_magenta = magenta_mask(restored)
                    edge_mask = np.zeros(restored_magenta.shape, dtype=bool)
                    edge_mask[:2] = True
                    edge_mask[-2:] = True
                    edge_mask[:, :2] = True
                    edge_mask[:, -2:] = True
                    native_magenta = magenta_mask(native)
                    matched_native = 0
                    for edge_y, edge_x in np.argwhere(restored_magenta & edge_mask):
                        native_x, native_y = round(edge_x / 2), round(edge_y / 2)
                        near_native = native_magenta[max(0, native_y - 3):min(79, native_y + 4),
                                                      max(0, native_x - 3):min(59, native_x + 4)]
                        if not near_native.any():
                            raise ValueError(f"Magenta gutter edge remained after crop: {family_id}-{number:02d}")
                        matched_native += 1
                    panel["magenta_edge_pixels_matching_native"] = matched_native
                restored.save(restored_dir / f"{number:02d}.png")
                x, y, _, _ = frame["reference_rect"]
                contact.paste(restored, (x, y))
                summary["minimum_sampling_xy"] = [
                    min(summary["minimum_sampling_xy"][axis], panel["sampling_xy"][axis])
                    for axis in range(2)]
                summary["maximum_aspect_error"] = max(summary["maximum_aspect_error"], panel["aspect_error"])
                summary["maximum_symmetric_edge_trim_px"] = max(
                    summary["maximum_symmetric_edge_trim_px"], *panel["symmetric_edge_trim_px"])
                summary["frames"] += 1
            contact.save(folder / "restored_sheet_x2.png")
            submitted_prompt = (str(folder / "prompt_attempt_02.txt")
                                if raw_name == "raw_attempt_02.png" else sheet["prompt"])
            if sha256(submitted_prompt) != sheet.get("prompt_sha256", sha256(submitted_prompt)) \
                    and raw_name != "raw_attempt_02.png":
                raise ValueError(f"Submitted prompt changed: {submitted_prompt}")
            report = {"family": family_id, "part": part, "raw": str(raw_path),
                      "raw_sha256": sha256(raw_path), "raw_size": list(raw.size),
                      "reference": sheet["reference"], "reference_sha256": sheet["reference_sha256"],
                      "submitted_prompt": submitted_prompt,
                      "tool": "built-in image_gen.imagegen", "model": "tool-managed; not exposed",
                      "x2_fit": "isotropic_centered_full_panel; no subject fitting",
                      "columns": measurement["columns"], "rows": measurement["rows"],
                      "panels": measurement["panels"], "automatic_failures": [],
                      "visual_status": "awaiting_user_review"}
            report["submitted_prompt_sha256"] = sha256(report["submitted_prompt"])
            if run_name == "approved_six" and (family_id, part) == ("pc06", "A"):
                first_raw = folder / "raw_attempt_01.png"
                report["superseded_attempt"] = {
                    "raw": str(first_raw), "raw_sha256": sha256(first_raw),
                    "submitted_prompt": str(folder / "prompt.txt"),
                    "submitted_prompt_sha256": sha256(folder / "prompt.txt"),
                    "reason": "Visible magenta gutter-color spill into bottom-row portrait panels",
                }
            (folder / "report.json").write_text(json.dumps(report, indent=2) + "\n")
            sheet["raw"] = str(raw_path)
            sheet["raw_sha256"] = report["raw_sha256"]
            sheet["selected_prompt"] = report["submitted_prompt"]
            sheet["selected_prompt_sha256"] = report["submitted_prompt_sha256"]
            sheet["report"] = str(folder / "report.json")
            sheet["status"] = "technical_geometry_pass_visual_review_pending"
            summary["sheet_reports"].append(sheet["report"])
            summary["sheets"] += 1
        summary["families"] += 1
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    (run / "technical_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "sheet_reports"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "prepare-safe-b", "assemble"))
    parser.add_argument("--run", choices=tuple(RUNS), default="approved_six")
    parser.add_argument("--partial", action="store_true", help="Assemble only sheets with raw returns")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.run)
    elif args.action == "prepare-safe-b":
        if args.run != "remaining":
            raise SystemExit("Safe B prompts are only for the remaining-family run")
        prepare_safe_b_prompts()
    else:
        assemble(args.run, partial=args.partial)
