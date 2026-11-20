"""Recover native-anchored x2 portrait frames from generated transparent sheets.

The raw imagegen sheets are immutable inputs. Grid detection and registration are
deliberately conservative: a geometric candidate is not an art approval.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


BASE = Path(__file__).resolve().parent
INPUT = BASE / "review/second_pass/portrait_transparent_v2"
OUTPUT = BASE / "review/second_pass/portrait_transparent_v3"
PREVIOUS = BASE / "review/second_pass/portrait_families"
NATIVE_SIZE = (59, 79)
X2_SIZE = (118, 158)
GRID = (7, 4)
ALPHA_THRESHOLD = 96


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def largest_component(mask):
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if not count:
        return None, 0, 0
    sizes = np.bincount(labels.ravel())[1:]
    winner = int(sizes.argmax() + 1)
    detached = int(sizes[sizes >= 12].sum() - sizes[winner - 1])
    return bbox(labels == winner), int(sizes[winner - 1]), detached


def background_bbox(path):
    native = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    if native.shape[:2] != (NATIVE_SIZE[1], NATIVE_SIZE[0]):
        raise ValueError(f"Unexpected native portrait size: {path}")
    # The original PC portraits share the muted green portrait-panel matte.
    # Median corner patches estimate that matte without assuming an exact palette.
    corners = np.concatenate((native[:6, :6].reshape(-1, 3), native[:6, -6:].reshape(-1, 3),
                              native[-6:, :6].reshape(-1, 3), native[-6:, -6:].reshape(-1, 3)))
    green = np.median(corners, axis=0)
    distance = np.linalg.norm(native - green, axis=2)
    foreground = distance > 29
    box, size, _ = largest_component(foreground)
    if box is None or size < 100:
        return [0, 0, *NATIVE_SIZE], "weak_native_foreground"
    return box, None


def gap(projection, nominal, radius, quiet_limit):
    start = max(1, nominal - radius)
    stop = min(len(projection) - 1, nominal + radius + 1)
    quiet = projection[start:stop] <= quiet_limit
    runs = []
    run_start = None
    for index, value in enumerate(quiet):
        if value and run_start is None:
            run_start = start + index
        if run_start is not None and (not value or index == len(quiet) - 1):
            end = start + index if not value else start + index + 1
            runs.append((run_start, end))
            run_start = None
    if runs:
        # A wide transparent gutter is more reliable than one anomalously clear pixel.
        best = max(runs, key=lambda run: (run[1] - run[0]) - abs((run[0] + run[1]) / 2 - nominal) / 4)
        return round((best[0] + best[1]) / 2), best[1] - best[0], None
    # Preserve a candidate for review, but explicitly flag the lack of a clean split.
    scores = np.convolve(projection.astype(float), np.ones(3) / 3, mode="same")
    center = int(start + np.argmin(scores[start:stop]))
    return center, 0, "no_clear_gutter"


def sheet_geometry(raw):
    alpha = np.asarray(raw.getchannel("A")) > ALPHA_THRESHOLD
    height, width = alpha.shape
    columns = [0]
    rows = [0]
    issues = []
    column_occupancy = alpha.sum(axis=0)
    row_occupancy = alpha.sum(axis=1)
    for number in range(1, GRID[0]):
        position, span, issue = gap(column_occupancy, round(number * width / GRID[0]),
                                    round(width / GRID[0] * .17), max(2, round(height * .006)))
        columns.append(position)
        if issue:
            issues.append(f"column_{number}_{issue}")
        if span < 3:
            issues.append(f"column_{number}_narrow_gutter")
    columns.append(width)
    for number in range(1, GRID[1]):
        position, span, issue = gap(row_occupancy, round(number * height / GRID[1]),
                                    round(height / GRID[1] * .12), max(2, round(width * .006)))
        rows.append(position)
        if issue:
            issues.append(f"row_{number}_{issue}")
        if span < 3:
            issues.append(f"row_{number}_narrow_gutter")
    rows.append(height)
    return columns, rows, issues


def collect_sheet(family, sheet):
    attempt = next(a for a in sheet["attempts"] if a["id"] == sheet["selected"])
    raw_path = INPUT / family["id"] / sheet["id"] / sheet["selected"] / "raw.png"
    if digest(raw_path) != attempt["raw_sha256"]:
        raise ValueError(f"Changed raw master: {raw_path}")
    raw = Image.open(raw_path).convert("RGBA")
    columns, rows, grid_issues = sheet_geometry(raw)
    records = []
    for slot, frame_number in enumerate(sheet["frames"]):
        column, row = slot % GRID[0], slot // GRID[0]
        rect = [columns[column], rows[row], columns[column + 1], rows[row + 1]]
        cell = raw.crop(rect)
        alpha = np.asarray(cell.getchannel("A")) > ALPHA_THRESHOLD
        master_box, main_size, detached = largest_component(alpha)
        frame = next(frame for frame in family["frames"] if frame["frame"] == frame_number)
        if digest(frame["native"]) != frame["native_sha256"]:
            raise ValueError(f"Changed native frame: {frame['native']}")
        native_box, native_issue = background_bbox(frame["native"])
        issues = []
        if master_box is None:
            issues.append("no_master_subject")
        if native_issue:
            issues.append(native_issue)
        if master_box:
            edge_opaque = [int(alpha[:, 0].sum()), int(alpha[:, -1].sum()),
                           int(alpha[0, :].sum()), int(alpha[-1, :].sum())]
            if max(edge_opaque) > 3:
                issues.append("master_subject_at_slot_boundary")
            if detached > main_size * .01:
                issues.append("detached_alpha_components")
        else:
            edge_opaque = [0, 0, 0, 0]
        records.append({"frame": frame_number, "name": frame["name"], "native_sha256": frame["native_sha256"],
                        "source_rect": rect, "master_box": master_box, "native_box": native_box,
                        "main_pixels": main_size, "detached_pixels": detached, "edge_opaque": edge_opaque,
                        "issues": issues, "cell": cell})
    return {"id": sheet["id"], "attempt": sheet["selected"], "raw_path": raw_path,
            "raw_sha256": attempt["raw_sha256"], "raw_size": raw.size, "columns": columns,
            "rows": rows, "grid_issues": grid_issues, "records": records}


def sheet_scales(sheets):
    candidates = []
    scales = {}
    for sheet in sheets:
        sheet_candidates = []
        for frame in sheet["records"]:
            source, native = frame["master_box"], frame["native_box"]
            if source is None or frame["main_pixels"] < 800 or frame["detached_pixels"] > 100:
                continue
            native_width, native_height = native[2] - native[0], native[3] - native[1]
            source_width, source_height = source[2] - source[0], source[3] - source[1]
            if native_width < 42 or native_height < 55 or source_width < 90 or source_height < 150:
                continue
            candidate = min(2 * native_width / source_width, 2 * native_height / source_height)
            candidates.append(candidate)
            sheet_candidates.append(candidate)
        if sheet_candidates:
            scales[sheet["id"]] = round(float(np.median(sheet_candidates)), 6)
    if len(candidates) < 6 or len(scales) != len(sheets):
        return None, candidates
    # Imagegen can draw the two halves at different sizes. Calibrate each half
    # against its own native frames; keep the scale fixed within its 28 poses.
    return scales, candidates


def fit_frame(frame, scale):
    output = Image.new("RGBA", X2_SIZE)
    if frame["master_box"] is None or scale is None:
        return output, ["cannot_register"]
    source = frame["master_box"]
    native = frame["native_box"]
    native_center = ((native[0] + native[2]), (native[1] + native[3]))
    source_center = ((source[0] + source[2]) / 2, (source[1] + source[3]) / 2)
    resized_size = (max(1, round(frame["cell"].width * scale)),
                    max(1, round(frame["cell"].height * scale)))
    resized = frame["cell"].convert("RGBa").resize(resized_size, Image.Resampling.LANCZOS).convert("RGBA")
    offset = (round(native_center[0] - source_center[0] * scale),
              round(native_center[1] - source_center[1] * scale))
    output.paste(resized, offset)
    projected = [offset[0] + source[0] * scale, offset[1] + source[1] * scale,
                 offset[0] + source[2] * scale, offset[1] + source[3] * scale]
    native_width, native_height = native[2] - native[0], native[3] - native[1]
    fill = ((projected[2] - projected[0]) / (2 * native_width),
            (projected[3] - projected[1]) / (2 * native_height))
    issues = []
    if native_width >= 42 and native_height >= 55 and min(fill) < .9:
        issues.append("underfills_native_frame")
    if projected[0] < -.5 or projected[1] < -.5 or projected[2] > X2_SIZE[0] + .5 or projected[3] > X2_SIZE[1] + .5:
        issues.append("subject_outside_x2_canvas")
    alpha = np.asarray(output.getchannel("A")) > 128
    edge = [int(alpha[:, 0].sum()), int(alpha[:, -1].sum()),
            int(alpha[0, :].sum()), int(alpha[-1, :].sum())]
    if max(edge) > 3:
        issues.append("x2_subject_touches_edge")
    frame["output_offset"] = offset
    frame["projected_box"] = [round(value, 2) for value in projected]
    frame["native_fill_ratio_xy"] = [round(value, 4) for value in fill]
    frame["x2_edge_opaque"] = edge
    return output, issues


def process_family(family, output_root):
    sheets = [collect_sheet(family, sheet) for sheet in family["sheets"]]
    scales, candidates = sheet_scales(sheets)
    family_root = output_root / family["id"]
    frames_root = family_root / "frames"
    frames_root.mkdir(parents=True, exist_ok=True)
    complete = Image.new("RGBA", (GRID[0] * X2_SIZE[0], 2 * GRID[1] * X2_SIZE[1]))
    sheet_reports = []
    for sheet_index, sheet in enumerate(sheets):
        scale = scales.get(sheet["id"]) if scales else None
        atlas = Image.new("RGBA", (GRID[0] * X2_SIZE[0], GRID[1] * X2_SIZE[1]))
        frame_reports = []
        for slot, record in enumerate(sheet["records"]):
            output, fit_issues = fit_frame(record, scale)
            record["issues"].extend(fit_issues)
            output.save(frames_root / f"{record['frame']:02d}.png")
            x, y = slot % GRID[0] * X2_SIZE[0], slot // GRID[0] * X2_SIZE[1]
            atlas.paste(output, (x, y))
            complete.paste(output, (x, y + sheet_index * GRID[1] * X2_SIZE[1]))
            frame_reports.append({key: value for key, value in record.items() if key != "cell"})
        atlas.save(family_root / f"sheet_{sheet['id']}_x2.png")
        sheet_reports.append({key: value for key, value in sheet.items() if key not in ("records", "raw_path")}
                             | {"raw_path": str(sheet["raw_path"]), "scale": scale,
                                "master_pixels_per_native_pixel": round(2 / scale, 4) if scale else None,
                                "frames": frame_reports})
    complete.save(family_root / "all_56_x2.png")
    issue_count = sum(bool(frame["issues"]) for sheet in sheet_reports for frame in sheet["frames"])
    report = {"family": family["id"], "native_size": list(NATIVE_SIZE), "x2_size": list(X2_SIZE),
              "sheet_scales": scales,
              "scale_sample_count": len(candidates),
              "status": "needs_review" if issue_count or any(sheet["grid_issues"] for sheet in sheets) or
              scales is None or any(scale >= 1 for scale in scales.values())
              else "geometry_candidate", "flagged_frames": issue_count, "sheets": sheet_reports,
              "warning": "Geometry checks do not approve pixel detail, alpha color, identity or gameplay replacement."}
    save_json(family_root / "report.json", report)
    return {"family": family["id"], "status": report["status"], "flagged_frames": issue_count,
            "sheet_scales": scales, "report": f"{family['id']}/report.json"}


def previous_background(family):
    folder = PREVIOUS / family["id"]
    manifest_path = folder / "manifest.json"
    sheet_path = folder / "candidate_x2.png"
    manifest = json.loads(manifest_path.read_text())
    records = manifest["frames"]
    if len(records) != len(family["frames"]):
        raise ValueError(f"Previous portrait frame count differs: {family['id']}")
    frames = []
    for source, record in zip(family["frames"], records):
        if (record["name"], record["source"]["source_sha256"]) != (source["name"], source["native_sha256"]):
            raise ValueError(f"Previous portrait source differs: {source['name']}")
        rect = record["sheet_rect"] if record["selected"] else None
        if rect and rect[2:] != list(X2_SIZE):
            raise ValueError(f"Previous portrait preview has unexpected size: {source['name']}")
        frames.append({"status": record["status"], "rect": rect})
    return {"sheet": f"../portrait_families/{family['id']}/candidate_x2.png",
            "sheet_sha256": digest(sheet_path), "manifest_sha256": digest(manifest_path), "frames": frames}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("families", nargs="*", help="Family ids; omit with --all to process every source-backed family")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    manifest = json.loads((INPUT / "manifest.json").read_text())
    available = {family["id"]: family for family in manifest["families"] if family["sheets"]}
    selected = list(available) if args.all else args.families
    if not selected:
        parser.error("Choose family ids or --all")
    unknown = set(selected) - set(available)
    if unknown:
        parser.error(f"Unknown or missing-native family ids: {', '.join(sorted(unknown))}")
    results = []
    for family_id in selected:
        result = process_family(available[family_id], args.output)
        results.append(result)
        print(f"{family_id}: {result['status']}, {result['flagged_frames']} flagged frames, "
              f"scales {result['sheet_scales']}", flush=True)
    source_hash, extractor_hash = digest(INPUT / "manifest.json"), digest(__file__)
    run_path = args.output / "run_report.json"
    if not args.all and run_path.exists():
        previous = json.loads(run_path.read_text())
        if (previous.get("source_manifest_sha256"), previous.get("extractor_sha256")) != (
                source_hash, extractor_hash):
            raise ValueError("The source or extractor changed; run --all before updating the gallery")
        results = list({item["family"]: item for item in previous["results"] + results}.values())
    save_json(run_path, {"source_manifest_sha256": source_hash, "extractor_sha256": extractor_hash,
                         "results": results})
    gallery = {"source_manifest_sha256": source_hash, "extractor_sha256": extractor_hash,
               "families": []}
    for result in results:
        report = json.loads((args.output / result["family"] / "report.json").read_text())
        previous = previous_background(available[result["family"]])
        report_frames = [frame for sheet in report["sheets"] for frame in sheet["frames"]]
        gallery["families"].append({"id": result["family"], "status": report["status"],
                                    "flagged_frames": result["flagged_frames"],
                                    "sheet_scales": report["sheet_scales"],
                                    "previous_background": {key: value for key, value in previous.items()
                                                            if key != "frames"},
                                    "raw_sha256s": [sheet["raw_sha256"] for sheet in report["sheets"]],
                                    "attempts": {sheet["id"]: sheet["attempt"] for sheet in report["sheets"]},
                                    "grid_issues": {sheet["id"]: sheet["grid_issues"] for sheet in report["sheets"]},
                                    "frames": [{"frame": frame["frame"], "name": frame["name"],
                                                "issues": frame["issues"],
                                                "native_fill_ratio_xy": frame.get("native_fill_ratio_xy"),
                                                "previous_background": old}
                                               for frame, old in zip(report_frames, previous["frames"])]})
    (args.output / "data.js").write_text("window.PORTRAIT_EXTRACTION = " + json.dumps(gallery) + ";\n")


if __name__ == "__main__":
    main()
