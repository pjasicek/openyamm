"""Resumable original-to-transparent PC portrait restoration and registration.

Imagegen calls are made with the built-in tool, outside this script. This script
prepares exact requests, records immutable returns, measures/extracts them, and
builds review data. It never installs or accepts artwork.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


HERE = Path(__file__).resolve().parent
HUD = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HUD))
from pc_background_removal_20260927.build import inputs, backing_estimate, native_guide
from extract_transparent_portraits import sheet_geometry

SIZE = (118, 158)
REFERENCE_SIZE = (1092, 728)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def box(mask):
    ys, xs = np.where(mask)
    if not len(xs):
        raise ValueError("Empty subject mask")
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def portrait_mask(alpha):
    # Measure the connected head, not detached status droplets or isolated
    # antialias specks. This mask is never applied to the exported pixels.
    labels, _ = ndimage.label(alpha >= 128, structure=np.ones((3, 3)))
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    if not sizes.any():
        raise ValueError("Empty portrait component")
    return labels == sizes.argmax()


def bottom_contact(mask, band):
    bounds = box(mask)
    ys, xs = np.where(mask[max(0, bounds[3] - band):bounds[3]])
    return [float(np.median(xs) + .5), float(bounds[3])]


def native_contact_band(bounds):
    # Average the lower contact over a short native-coordinate strip. The very
    # last paletted row can contain one off-center background-colored fragment.
    return min(16, max(4, round((bounds[3] - bounds[1]) * .10)))


def prompt(family, sheet):
    start = 1 if sheet == "A" else 29
    return f"""Use case: identity-preserve.
Asset type: transparent fantasy-game player portrait spritesheet, {family}, sheet {sheet} of two, native frames {start:02} through {start+27:02}.
Input image 1 is the authoritative ORIGINAL reference. It contains exactly 28 distinct states of ONE character in seven columns and four rows, reading order. Reconstruct each corresponding original portrait with the same identity, facial proportions, hairstyle, accessories, muted material colors, lighting direction, head angle, gaze and expression.
Primary request: Restore all 28 low-resolution portraits as finely detailed coherent pre-rendered/painted fantasy-game artwork on a GENUINELY TRANSPARENT RGBA background. Remove the complete textured green-gray portrait-panel backdrop. Return only the existing character silhouette, including all hair, ears, headwear, earrings and other visible original features. Keep pale/white features, gray stone material, and green-colored character material opaque; these belong to the character. Only the exterior background and real empty holes become transparent. Use a thin clean antialiased edge, no green halo or soft surrounding shadow. Do not paint white, black, brown, or checkerboard to imitate transparency.
Layout: EXACTLY 7 columns by 4 rows; 28 separate portraits in the original reading order. Landscape 3:2 sheet around 1536x1024 or larger. The reference is 1092x728: slots 156x182, original portrait windows 118x158 at inset (19,12). Keep uniform transparent gutters and preserve those virtual portrait windows. No labels, border rectangles, selection rings, guide marks, text or watermark.
Registration: Preserve the original head height within each window, the original vertical centerline, and the lower silhouette contact near the bottom-middle of the window. The bottom contact can span several pixels; preserve its location relative to the original. Keep the character full height rather than floating above the lower edge. Preserve the visible width and the placement of every accessory. Do not force an oval crop or trim hair/ears. Keep the original lower cutoff without adding shoulders or extra neck. Angled poses retain their original offsets and direction, not a recentered nose.
States: Preserve each distinct original mouth/eye state, color/material status and expression. When the reference lowers the head or shows only a small partial head, reproduce that partial state at the same low position; do not complete it into a full head or enlarge its fragment. Preserve only the modest non-graphic facial status details already present in the originals; invent no new marks or anatomy.
Detail: This is a fresh high-resolution reconstruction, not nearest-neighbor enlargement, smoothing, or a pixel-art filter. Require more than two genuinely generated pixels per native pixel in BOTH axes for each subject. Reconstruct smooth continuous contours, coherent facial planes, hair locks, eye and mouth details, and convincing material shading. No enlarged square texels, source-grid dithering, staircase outlines, faceted pixel blocks, blur-only restoration, redesign or beauty retouching.
Final output: 28 individually separated character portraits on real alpha transparency, faithful native states and stable native height/center/bottom registration.
"""


def prepare():
    if (HERE / "catalogue.json").exists():
        raise ValueError("This run is already prepared; use next/progress to resume")
    families, missing = inputs()
    priority = ["pc02", "7pc05", "7pc01", "pc23"]
    families.sort(key=lambda f: (priority.index(f["id"]) if f["id"] in priority else len(priority), f["id"]))
    backing, support = backing_estimate(families)
    np.savez_compressed(HERE / "native_backing.npz", backing=backing, support=support)
    catalogue = {"schema": 1, "created_at": now(), "status": "in_progress", "native_size": [59, 79],
                 "output_size": list(SIZE), "missing_native_families": missing, "families": [], "jobs": []}
    for family in families:
        folder = HERE / "families" / family["id"]
        (folder / "native").mkdir(parents=True)
        (folder / "native_geometry").mkdir()
        frames = []
        for frame in family["frames"]:
            number = frame["number"]
            native = Image.open(frame["native"]).convert("RGB")
            assert native.size == (59, 79)
            guide = native_guide(np.asarray(native), backing, support)
            name = Path(frame["native"]).stem + ".png"
            native.resize(SIZE, Image.Resampling.NEAREST).save(folder / "native" / name)
            Image.fromarray(guide).convert("L").save(folder / "native_geometry" / name)
            frames.append({"number": number, "name": name, "source": str(Path(frame["native"]).relative_to(ROOT)),
                           "source_sha256": frame["source_sha256"], "native_box": box(guide),
                           "native_anchor": bottom_contact(guide, native_contact_band(box(guide))),
                           "native_contact_band": native_contact_band(box(guide)),
                           "native": f"families/{family['id']}/native/{name}",
                           "geometry": f"families/{family['id']}/native_geometry/{name}",
                           "accepted_artifact": frame["artifact"], "accepted_sha256": frame["sha256"],
                           "runtime_path": frame["runtime_output_path"]})
        catalogue["families"].append({"id": family["id"], "frames": frames})
        for letter, first in [("A", 0), ("B", 28)]:
            job_id = f"{family['id']}_{letter}"
            job_folder = folder / letter
            attempt = job_folder / "attempt_01"
            attempt.mkdir(parents=True)
            reference = Image.new("RGBA", REFERENCE_SIZE)
            for slot, frame in enumerate(frames[first:first+28]):
                native = Image.open(HERE / frame["native"]).convert("RGBA")
                reference.paste(native, (slot % 7 * 156 + 19, slot // 7 * 182 + 12))
            reference.save(job_folder / "reference.png")
            text = prompt(family["id"], letter)
            (attempt / "prompt.txt").write_text(text)
            request = {"prompt": text, "referenced_image_paths": [str(job_folder / "reference.png")]}
            save(attempt / "request.json", request)
            save(job_folder / "state.json", {"id": job_id, "status": "prepared", "attempt": "attempt_01"})
            catalogue["jobs"].append({"id": job_id, "family": family["id"], "sheet": letter,
                                      "path": str(job_folder.relative_to(HERE)), "frames": list(range(first+1, first+29))})
    save(HERE / "catalogue.json", catalogue)
    rebuild_browser()
    progress()


def job_info(job_id):
    catalogue = read(HERE / "catalogue.json")
    job = next(job for job in catalogue["jobs"] if job["id"] == job_id)
    folder = HERE / job["path"]
    state = read(folder / "state.json")
    return catalogue, job, folder, state


def next_jobs(count):
    catalogue = read(HERE / "catalogue.json")
    result = []
    for job in catalogue["jobs"]:
        folder = HERE / job["path"]
        state = read(folder / "state.json")
        if state["status"] != "prepared":
            continue
        request = read(folder / state["attempt"] / "request.json")
        result.append({"id": job["id"], "family": job["family"], "sheet": job["sheet"], "request": request})
        if len(result) == count:
            break
    print(json.dumps(result))


def claim(job_id):
    _, job, folder, state = job_info(job_id)
    if state["status"] != "prepared":
        raise ValueError(f"Job {job_id} is already {state['status']}")
    attempt = folder / state["attempt"]
    state.update(status="submitted", submitted_at=now(), prompt_sha256=digest(attempt / "prompt.txt"),
                 reference_sha256=digest(folder / "reference.png"))
    save(folder / "state.json", state)
    print(json.dumps({"id": job_id, "status": "submitted"}))


def resample(cell, scales, offset):
    sx, sy = scales
    x, y = offset
    border = max(cell.size)
    padded = Image.new("RGBA", (cell.width + 2 * border, cell.height + 2 * border))
    padded.paste(cell, (border, border))
    window = (border - x / sx, border - y / sy,
              border + (SIZE[0] - x) / sx, border + (SIZE[1] - y) / sy)
    return padded.convert("RGBa").resize(SIZE, Image.Resampling.LANCZOS, box=window).convert("RGBA")


def process(job_id):
    catalogue, job, folder, state = job_info(job_id)
    attempt = folder / state["attempt"]
    path = attempt / "raw.png"
    if digest(path) != state["raw_sha256"]:
        raise ValueError("Master hash changed")
    raw = Image.open(path)
    if raw.mode != "RGBA":
        raise ValueError("Imagegen did not return RGBA transparency")
    alpha = np.asarray(raw.getchannel("A"))
    if np.mean(alpha == 0) < .10 or int(alpha.max()) < 240:
        raise ValueError("Imagegen alpha lacks a transparent exterior or solid subject")
    columns, rows, grid_issues = sheet_geometry(raw)
    column_rows = [rows for _ in range(7)]
    grid_path = attempt / "extraction_grid.json"
    if grid_path.exists():
        # A reviewed grid can stagger row cuts when portraits in different
        # columns overlap vertically. Every cut must still cross transparent air.
        grid = read(grid_path)
        if grid["raw_sha256"] != state["raw_sha256"] or grid["columns"] != columns:
            raise ValueError("Reviewed extraction grid does not match the master")
        column_rows = grid["column_rows"]
        if len(column_rows) != 7 or any(issue.startswith("column_") for issue in grid_issues):
            raise ValueError("Invalid reviewed column layout")
        for column, cuts in enumerate(column_rows):
            if (len(cuts) != 5 or cuts[0] != 0 or cuts[-1] != raw.height
                    or any(a >= b for a, b in zip(cuts, cuts[1:]))):
                raise ValueError("Invalid reviewed row layout")
            for cut in cuts[1:-1]:
                if int(alpha[cut, columns[column]:columns[column + 1]].max()) > 8:
                    raise ValueError("Reviewed row cut crosses visible alpha")
    elif grid_issues:
        raise ValueError("Unreliable sheet split: " + ", ".join(grid_issues))
    family = next(f for f in catalogue["families"] if f["id"] == job["family"])
    native_frames = {f["number"]: f for f in family["frames"]}
    output = attempt / "frames"
    output.mkdir(exist_ok=True)
    (attempt / "alpha").mkdir(exist_ok=True)
    (attempt / "uncorrected").mkdir(exist_ok=True)
    records = []
    for slot, number in enumerate(job["frames"]):
        source = native_frames[number]
        cuts = column_rows[slot % 7]
        rect = [columns[slot % 7], cuts[slot // 7], columns[slot % 7+1], cuts[slot // 7+1]]
        cell = raw.crop(rect)
        a = np.asarray(cell.getchannel("A"))
        body = portrait_mask(a)
        outline = box(body)
        fringe = box(a >= 8)
        native = source["native_box"]
        native_anchor = source["native_anchor"]
        contact_band = source["native_contact_band"]
        nw, nh = native[2] - native[0], native[3] - native[1]
        mw, mh = outline[2] - outline[0], outline[3] - outline[1]
        # Height and bottom contact are authoritative. Width is independent;
        # preserving a hair fringe must never shrink the character vertically.
        sy = nh / mh
        anchor = bottom_contact(body, max(2, round(contact_band / sy)))
        sx = min(sy, nw / mw)
        if anchor[0] > fringe[0]:
            sx = min(sx, native_anchor[0] / (anchor[0] - fringe[0]))
        if fringe[2] > anchor[0]:
            sx = min(sx, (SIZE[0] - native_anchor[0]) / (fringe[2] - anchor[0]))
        offset = [native_anchor[0] - sx * anchor[0], native_anchor[1] - sy * outline[3]]
        center_delta = offset[0] + sx * (outline[0] + outline[2]) / 2 - (native[0] + native[2]) / 2
        center_shift = 0.0
        if abs(center_delta) > 6:
            # Slight pose/neck-shape differences can put exact bottom contact
            # and the head center in conflict. Permit a small translation while
            # keeping contact within 4 pixels and the full fringe in the canvas.
            wanted = -np.sign(center_delta) * min(4, np.ceil((abs(center_delta) - 5.5) * 2) / 2)
            left = max(-4, -offset[0] - sx * fringe[0])
            right = min(4, SIZE[0] - offset[0] - sx * fringe[2])
            if left <= right:
                center_shift = float(np.clip(wanted, left, right))
                offset[0] += center_shift
        candidate = resample(cell, (sx, sy), offset)
        initial_sy = sy
        # Thin hair tips can disappear when downsampling. Refine vertical scale
        # against the actual raster, always resampling the immutable master.
        for _ in range(3):
            bounds = box(portrait_mask(np.asarray(candidate.getchannel("A"))))
            if max(abs(bounds[1] - native[1]), abs(bounds[3] - native[3])) <= 1:
                break
            correction = nh / (bounds[3] - bounds[1])
            sy *= correction
            offset[1] = native[3] + correction * (offset[1] - bounds[3])
            candidate = resample(cell, (sx, sy), offset)
        # Raster rounding can move the final center beyond the continuous fit.
        # Refine translation only, within the same contact/fringe limits.
        for _ in range(8):
            body_after = portrait_mask(np.asarray(candidate.getchannel("A")))
            bounds = box(body_after)
            delta = (bounds[0] + bounds[2] - native[0] - native[2]) / 2
            if abs(delta) <= 6:
                break
            step = -float(np.sign(delta)) * .5
            shifted = [offset[0] + step, offset[1]]
            if (abs(center_shift + step) > 4
                    or shifted[0] + sx * fringe[0] < 0
                    or shifted[0] + sx * fringe[2] > SIZE[0]):
                break
            trial = resample(cell, (sx, sy), shifted)
            trial_body = portrait_mask(np.asarray(trial.getchannel("A")))
            if abs(bottom_contact(trial_body, contact_band)[0] - native_anchor[0]) > 4:
                break
            candidate, offset = trial, shifted
            center_shift += step
        candidate.save(output / source["name"])
        candidate.getchannel("A").save(attempt / "alpha" / source["name"])
        nominal_scale = REFERENCE_SIZE[0] / raw.width
        nominal_left = (slot % 7 * 156 + 19) / nominal_scale
        nominal_top = (slot // 7 * 182 + 12) / nominal_scale
        nominal = resample(cell, (nominal_scale, nominal_scale),
                           ((rect[0] - nominal_left) * nominal_scale, (rect[1] - nominal_top) * nominal_scale))
        nominal.save(attempt / "uncorrected" / source["name"])
        oa = np.asarray(candidate.getchannel("A"))
        output_body = portrait_mask(oa)
        output_box = box(output_body)
        output_anchor = bottom_contact(output_body, contact_band)
        sample = [mw / (nw / 2), (outline[3] - outline[1]) / (nh / 2)]
        issues = []
        if min(sample) < 2:
            issues.append("insufficient_master_sampling")
        if abs(output_box[1] - native[1]) > 2:
            issues.append("height_mismatch")
        if abs(output_box[3] - native[3]) > 2:
            issues.append("bottom_mismatch")
        if abs(output_anchor[0] - native_anchor[0]) > 4:
            issues.append("bottom_contact_x_mismatch")
        source_center = (outline[0] + outline[2]) / 2
        target_center = (native[0] + native[2]) / 2
        predicted_center_error = offset[0] + sx * source_center - target_center
        center_error = (output_box[0] + output_box[2]) / 2 - target_center
        if abs(center_error) > 6:
            issues.append("silhouette_center_mismatch")
        if abs(sx / sy - 1) > .25:
            issues.append("large_shape_correction")
        if abs(sy / initial_sy - 1) > .10:
            issues.append("large_vertical_refinement")
        if np.mean(oa == 0) < .08:
            issues.append("weak_exterior_transparency")
        native_hash = digest(ROOT / source["source"])
        assert native_hash == source["source_sha256"]
        records.append({"number": number, "name": source["name"], "sheet": job["sheet"],
                        "native": source["native"], "geometry": source["geometry"],
                        "candidate": str((output / source["name"]).relative_to(HERE)),
                        "uncorrected": str((attempt / "uncorrected" / source["name"]).relative_to(HERE)),
                        "alpha": str((attempt / "alpha" / source["name"]).relative_to(HERE)),
                        "sha256": digest(output / source["name"]),
                        "native_box": native, "native_anchor": native_anchor, "master_box": outline,
                        "native_contact_band": contact_band,
                        "master_anchor": anchor, "measurement": "connected_alpha_128_eight_neighbors",
                        "master_full_box": box(a >= 128), "output_full_box": box(oa >= 128),
                        "output_box": output_box, "output_anchor": output_anchor,
                        "scale": [round(sx, 8), round(sy, 8)], "offset": [round(v, 6) for v in offset],
                        "center_balance_shift_x": center_shift,
                        "source_rect": rect, "sampling": [round(v, 4) for v in sample],
                        "center_error": round(center_error, 3),
                        "predicted_center_error": round(predicted_center_error, 3), "issues": issues,
                        "transparent_pixels": int(np.count_nonzero(oa == 0)),
                        "notes": ["Lowered pose: the original fragment height and bottom contact are preserved."]
                                 if number in [35, 36] else []})
    report = {"id": job_id, "family": job["family"], "sheet": job["sheet"],
              "attempt": state["attempt"], "raw_size": list(raw.size), "raw_sha256": state["raw_sha256"],
              "raw_transparent_fraction": float(np.mean(alpha == 0)), "columns": columns, "rows": rows,
              "column_rows": column_rows,
              "minimum_sampling": min(min(r["sampling"]) for r in records), "frames": records}
    save(attempt / "report.json", report)
    contact = Image.new("RGB", (7 * 256, 4 * 196), (25, 29, 35))
    draw = ImageDraw.Draw(contact)
    for slot, record in enumerate(records):
        x, y = slot % 7 * 256, slot // 7 * 196
        draw.text((x + 5, y + 4), record["name"][:-4] + (" !" if record["issues"] else ""), fill="white")
        contact.paste(Image.open(HERE / record["native"]), (x + 5, y + 25))
        preview = Image.new("RGBA", SIZE, (66, 71, 81, 255))
        preview.alpha_composite(Image.open(HERE / record["candidate"]))
        contact.paste(preview.convert("RGB"), (x + 133, y + 25))
    contact.save(attempt / "comparison.png")
    state.update(status="extracted", extracted_at=now(),
                 flagged_frames=[r["number"] for r in records if r["issues"]])
    save(folder / "state.json", state)
    rebuild_browser()
    print(json.dumps({"id": job_id, "status": state["status"], "minimum_sampling": report["minimum_sampling"],
                      "flagged_frames": [{"frame": r["number"], "issues": r["issues"]} for r in records if r["issues"]]}))


def record(job_id, source_path):
    _, _, folder, state = job_info(job_id)
    if state["status"] != "submitted":
        raise ValueError(f"Expected submitted job, got {state['status']}")
    target = folder / state["attempt"] / "raw.png"
    if target.exists():
        raise ValueError("Refusing to overwrite a master")
    shutil.copy2(source_path, target)
    target.chmod(0o644)
    state.update(status="raw_returned", returned_at=now(), raw_sha256=digest(target),
                 tool="built-in image_gen", tool_output_path=str(source_path))
    save(folder / "state.json", state)
    try:
        process(job_id)
    except (ValueError, AssertionError) as error:
        state.update(status="needs_repair", extraction_error=str(error))
        save(folder / "state.json", state)
        print(json.dumps({"id": job_id, "status": "needs_repair", "error": str(error)}))


def review(job_id, decision, note):
    _, _, folder, state = job_info(job_id)
    if state["status"] not in ["extracted", "reviewed", "needs_repair"]:
        raise ValueError("Record/extract before reviewing")
    state.update(status="reviewed" if decision == "pass" else "needs_repair", reviewed_at=now(),
                 visual_review={"decision": decision, "note": note})
    save(folder / "state.json", state)
    rebuild_browser()
    print(json.dumps({"id": job_id, "status": state["status"]}))


def tool_error(job_id, note):
    _, _, folder, state = job_info(job_id)
    state.update(status="tool_hold", error=note, error_at=now())
    save(folder / "state.json", state)
    rebuild_browser()
    progress()


def rebuild_browser():
    if not (HERE / "catalogue.json").exists():
        return
    catalogue = read(HERE / "catalogue.json")
    families = []
    for family in catalogue["families"]:
        frames, sheets = [], []
        for job in [j for j in catalogue["jobs"] if j["family"] == family["id"]]:
            folder = HERE / job["path"]
            state = read(folder / "state.json")
            report_path = folder / state["attempt"] / "report.json"
            sheet = {"id": job["sheet"], "status": state["status"],
                     "frames": job["frames"], "error": state.get("error"),
                     "review": state.get("visual_review")}
            if report_path.exists():
                frames.extend(read(report_path)["frames"])
                sheet.update(raw=str((folder / state["attempt"] / "raw.png").relative_to(HERE)),
                             comparison=str((folder / state["attempt"] / "comparison.png").relative_to(HERE)))
            sheets.append(sheet)
        families.append({"id": family["id"], "frames": sorted(frames, key=lambda f: f["number"]), "sheets": sheets})
    states = [read(HERE / j["path"] / "state.json") for j in catalogue["jobs"]]
    counts = {s: sum(j["status"] == s for j in states) for s in sorted({j["status"] for j in states})}
    status = "in_progress"
    if counts.get("reviewed", 0) == len(states):
        status = "ready_for_review"
    elif counts.get("reviewed", 0) + counts.get("tool_hold", 0) == len(states):
        status = "awaiting_tool_hold_decision"
    manifest = {"schema": 1, "updated_at": now(), "status": status, "counts": counts,
                "native_family_count": len(families), "expected_frames": sum(len(f["frames"]) for f in catalogue["families"]),
                "candidate_frames": sum(len(f["frames"]) for f in families), "families": families,
                "missing_native_families": catalogue["missing_native_families"]}
    if (HERE / "acceptance.json").exists():
        acceptance = read(HERE / "acceptance.json")
        revision = ROOT / acceptance["revision"]
        if digest(revision) != acceptance["revision_sha256"]:
            raise ValueError("Accepted revision receipt changed")
        accepted = {r["reviewed_artifact"]: r["sha256"] for r in read(revision)["records"].values()}
        selected = {str(HERE / f["candidate"]): f["sha256"] for family in families for f in family["frames"]}
        if selected != accepted:
            raise ValueError("Preview selection differs from the accepted revision; create a separate revision")
        manifest.update(status=acceptance["status"], acceptance=acceptance)
    save(HERE / "manifest.json", manifest)
    (HERE / "manifest.js").write_text("window.PC_ALL = " + json.dumps(manifest) + ";\n")


def progress():
    catalogue = read(HERE / "catalogue.json")
    states = [read(HERE / j["path"] / "state.json") for j in catalogue["jobs"]]
    print(json.dumps({"families": len(catalogue["families"]), "frames": sum(len(f["frames"]) for f in catalogue["families"]),
                      "sheets": len(states), "counts": {s: sum(j["status"] == s for j in states)
                                                        for s in sorted({j["status"] for j in states})},
                      "missing_native_families": catalogue["missing_native_families"]}))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("progress")
    sub.add_parser("browser-data")
    sub.add_parser("next").add_argument("--count", type=int, default=4)
    sub.add_parser("claim").add_argument("job")
    sub.add_parser("process").add_argument("job")
    p = sub.add_parser("record"); p.add_argument("job"); p.add_argument("path")
    p = sub.add_parser("review"); p.add_argument("job"); p.add_argument("decision", choices=["pass", "repair"]); p.add_argument("note")
    p = sub.add_parser("tool-error"); p.add_argument("job"); p.add_argument("note")
    args = parser.parse_args()
    if args.command == "prepare": prepare()
    elif args.command == "progress": progress()
    elif args.command == "next": next_jobs(args.count)
    elif args.command == "claim": claim(args.job)
    elif args.command == "record": record(args.job, args.path)
    elif args.command == "process": process(args.job)
    elif args.command == "review": review(args.job, args.decision, args.note)
    elif args.command == "tool-error": tool_error(args.job, args.note)
    elif args.command == "browser-data": rebuild_browser()


if __name__ == "__main__":
    main()
