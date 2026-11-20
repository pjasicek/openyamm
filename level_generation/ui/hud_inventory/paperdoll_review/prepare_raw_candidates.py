"""Extract retained paperdoll/equipment returns for context review, without accepting art.

Raw masters and canonical checkpoint records are read-only. Every output keeps its
sheet, crop, sampling, matte operation and registration findings in the manifest.
"""

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage


HERE = Path(__file__).resolve().parent
INVENTORY = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(INVENTORY))
import matte  # noqa: E402
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


RECIPE = "paperdoll-raw-extraction-v2"
NATIVE_IDENTICAL_HOLDS = {
    "engine--icons--6chain1v3a.bmp": "engine--icons--6chain1v3.bmp",
    "engine--icons--6chain1v5a.bmp": "engine--icons--6chain1v5.bmp",
}


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def catalog():
    source = (HERE / "catalog.js").read_text()
    return json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))


def missing_candidate_targets(data, audit):
    assets = data["assets"]
    for target in data["reviewTargets"]:
        asset = assets[target["name"]]
        if not target["active"] or asset["candidateStatus"] in {
                "accepted", "hud_approved", "candidate", "border_repaired"}:
            continue
        cells = audit.get(target["id"], {}).get("cells", [])
        attempts = list(dict.fromkeys(attempt for cell in cells for attempt in cell.get("retained_attempts", [])))
        yield target, attempts


def reference_geometry(payload, queue):
    selected = payload["selected_cells"]
    layout = payload.get("execution_layout") or {}
    if layout.get("canvas_size") and all(cell in layout.get("cell_rects", {}) for cell in selected):
        return layout["canvas_size"], layout["cell_rects"], "execution_layout"

    manifest_path = payload.get("original_manifest")
    if manifest_path:
        manifest = read(manifest_path)
        cells = {entry["id"]: entry.get("reference_rect") or entry["member"]["reference_cell_rect"]
                 for entry in manifest["cells"]}
        if all(cell in cells for cell in selected):
            return manifest["reference_size"], cells, "original_manifest"

    if len(selected) == 1:
        for name, role in payload.get("reference_roles", {}).items():
            if role.startswith("Edit target") and Path(name).is_file():
                with Image.open(name) as reference:
                    width, height = reference.size
                return [width, height], {selected[0]: [0, 0, width, height]}, "edit_target_reference"

    job = queue.jobs[payload["job"]]
    rectangles = {cell: queue.members[cell][1]["reference_cell_rect"] for cell in selected}
    return job["reference_size"], rectangles, "frozen_job_reference"


def sheet_kind(image):
    pixels = np.asarray(image.convert("RGBA"))
    band = 12
    corners = np.concatenate((pixels[:band, :band].reshape(-1, 4),
                              pixels[:band, -band:].reshape(-1, 4),
                              pixels[-band:, :band].reshape(-1, 4),
                              pixels[-band:, -band:].reshape(-1, 4)))
    median = np.median(corners, axis=0)
    if median[3] < 128:
        return "transparent"
    if median[0] > 140 and median[2] > 140 and median[1] < 100:
        return "magenta"
    return "opaque_or_unknown_backing"


def decontaminate_translucent_edges(image, original):
    output = np.asarray(image.convert("RGBA")).copy()
    alpha = output[:, :, 3]
    core = alpha >= 250
    if not core.any():
        return image, False
    edge = (alpha > 0) & ~core
    if not edge.any():
        return image, False
    indices = ndimage.distance_transform_edt(~core, return_indices=True)[1]
    source = np.asarray(original.convert("RGB"))
    output[:, :, :3][edge] = source[indices[0], indices[1]][edge]
    output[:, :, :3][alpha == 0] = 0
    return Image.fromarray(output), True


def cleaned_crop(crop, kind, opaque_expected, matte_options=None):
    issues = []
    if kind == "magenta":
        try:
            clean, parameters = matte.extract(crop, **(matte_options or {}))
            clean, replaced = decontaminate_translucent_edges(clean, crop)
            return clean, {"method": "local_magenta_unmix", "parameters": parameters,
                           "fringe_rgb_from_nearest_core": replaced}, issues
        except AssertionError as error:
            if opaque_expected:
                return crop.convert("RGBA"), {"method": "opaque_cell_on_magenta_sheet"}, issues
            issues.append("magenta_matte_unresolved")
            return Image.new("RGBA", crop.size), {"method": "magenta_matte_failed", "error": str(error)}, issues
    if kind == "transparent":
        clean, replaced = decontaminate_translucent_edges(crop, crop)
        return clean, {"method": "retained_alpha", "fringe_rgb_from_nearest_core": replaced}, issues
    if not opaque_expected:
        issues.append("opaque_or_unknown_raw_backing")
    return crop.convert("RGBA"), {"method": "retained_opaque_raw"}, issues


def crop_rect(reference_rect, reference_size, raw_size):
    x, y, width, height = reference_rect
    sx = raw_size[0] / reference_size[0]
    sy = raw_size[1] / reference_size[1]
    return [round(x * sx), round(y * sy), round((x + width) * sx), round((y + height) * sy)]


def image_to_x2(image, size, aspect_changed):
    premultiplied = image.convert("RGBa")
    if aspect_changed:
        fit = ImageOps.contain(premultiplied, size, Image.Resampling.LANCZOS).convert("RGBA")
        output = Image.new("RGBA", size)
        output.alpha_composite(fit, ((size[0] - fit.width) // 2, (size[1] - fit.height) // 2))
        return output, "uniform_letterbox_diagnostic"
    return premultiplied.resize(size, Image.Resampling.LANCZOS).convert("RGBA"), "exact_canvas_downsample"


def repair_opaque_magenta_seam(image):
    """Replace a one-pixel sheet seam only when it is isolated at an opaque canvas edge."""
    pixels = np.asarray(image.convert("RGBA")).copy()
    color = pixels[:, :, :3].astype(np.int16)
    excess = np.minimum(color[:, :, 0], color[:, :, 2]) - color[:, :, 1]
    repaired = []
    height, width = excess.shape
    for edge, inside, label in ((0, 1, "left"), (width - 1, width - 2, "right")):
        edge_count = int((excess[:, edge] > 30).sum())
        inside_count = int((excess[:, inside] > 30).sum())
        if edge_count >= round(height * .9) or (
                edge_count >= max(16, round(height * .04)) and
                inside_count < max(4, round(height * .02)) and edge_count > 3 * max(inside_count, 1)):
            pixels[:, edge] = pixels[:, inside]
            repaired.append(label)
    for edge, inside, label in ((0, 1, "top"), (height - 1, height - 2, "bottom")):
        edge_count = int((excess[edge] > 30).sum())
        inside_count = int((excess[inside] > 30).sum())
        if edge_count >= round(width * .9) or (
                edge_count >= max(16, round(width * .04)) and
                inside_count < max(4, round(width * .02)) and edge_count > 3 * max(inside_count, 1)):
            pixels[edge] = pixels[inside]
            repaired.append(label)
    return Image.fromarray(pixels), repaired


def process_attempt(attempt_id, cells, attempt, queue, output, matte_options=None):
    raw_path = Path(attempt["raw"])
    raw_hash = digest(raw_path)
    if raw_hash != attempt["sha256"]:
        raise ValueError(f"Retained raw hash changed: {raw_path}")
    payload = read(attempt["payload"])
    if not set(cells) <= set(payload["selected_cells"]):
        raise ValueError(f"Attempt does not contain requested cells: {attempt_id}")
    reference_size, rectangles, geometry_source = reference_geometry(payload, queue)
    results = {}
    with Image.open(raw_path) as opened:
        raw = opened.convert("RGBA")
    kind = sheet_kind(raw)
    scale_x = raw.width / reference_size[0]
    scale_y = raw.height / reference_size[1]
    aspect_error = abs(scale_x / scale_y - 1)
    for cell in cells:
        member = queue.members[cell][1]
        target = queue.targets[member["target"]]
        source = ROOT / member["source_path"]
        if digest(source) != member["source_sha256"]:
            raise ValueError(f"Frozen source changed: {source}")
        ref = rectangles[cell]
        bounds = crop_rect(ref, reference_size, raw.size)
        if min(bounds) < 0 or bounds[2] > raw.width or bounds[3] > raw.height:
            raise ValueError(f"Raw crop outside sheet: {cell}, {bounds}")
        crop = raw.crop(tuple(bounds))
        opaque_expected = member["cleanup"] == "opaque_canvas"
        clean, matte_record, issues = cleaned_crop(crop, kind, opaque_expected, matte_options)
        if opaque_expected and min(clean.getchannel("A").getextrema()) < 255:
            issues.append("expected_opaque_background")
        sampling = [round(crop.width / member["source_rect"][2], 4),
                    round(crop.height / member["source_rect"][3], 4)]
        if min(sampling) < 2:
            issues.append("insufficient_raw_sampling")
        if aspect_error > .03:
            issues.append("raw_canvas_aspect_changed")
        alpha = np.asarray(clean.getchannel("A"))
        edge_pixels = [int((alpha[:, 0] >= 128).sum()), int((alpha[:, -1] >= 128).sum()),
                       int((alpha[0, :] >= 128).sum()), int((alpha[-1, :] >= 128).sum())]
        if any(edge_pixels) and len(payload["selected_cells"]) > 1:
            issues.append("subject_at_measured_cell_boundary")
        if not (alpha >= 16).any():
            issues.append("empty_extraction")
        candidate, operation = image_to_x2(clean, tuple(member["export_region"][2:]), aspect_error > .03)
        if opaque_expected and kind == "magenta":
            candidate, repaired_edges = repair_opaque_magenta_seam(candidate)
            if repaired_edges:
                matte_record["opaque_edge_repair"] = repaired_edges
                issues.append("opaque_magenta_edge_repaired")
        path = output / f"{cell}__{attempt_id}.png"
        candidate.save(path, optimize=True)
        measurements = registration.measurements(member, target, path)
        registration_flags = {profile: report["failures"] for profile, report in measurements["profiles"].items()
                              if report["failures"]}
        if registration_flags:
            issues.append("registration_guard_flag")
        results[cell] = {
            "cell_id": cell, "attempt": attempt_id, "path": str(path.resolve()), "sha256": digest(path),
            "raw": str(raw_path), "raw_sha256": raw_hash, "raw_size": list(raw.size),
            "reference_size": reference_size, "reference_rect": ref, "raw_rect": bounds,
            "geometry_source": geometry_source, "sheet_kind": kind, "sheet_aspect_error": round(aspect_error, 6),
            "actual_sampling": sampling, "x2_size": member["export_region"][2:],
            "source_sha256": member["source_sha256"], "matte": matte_record,
            "edge_opaque_pixels": edge_pixels, "operation": operation, "issues": issues,
            "registration_flags": registration_flags,
            "visual_approval": False,
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "raw_prepared")
    parser.add_argument("--limit", type=int, help="Process this many targets for a diagnostic run")
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    queue = queue_module.Queue()
    data = catalog()
    audit = {entry["target_id"]: entry for entry in read(INVENTORY / "review/second_pass/replacement_audit.json")["targets"]}
    attempt_records = {entry["id"]: entry for entry in queue.state["attempts"]}
    targets = list(missing_candidate_targets(data, audit))
    if arguments.limit:
        targets = targets[:arguments.limit]
    by_attempt = {}
    for target, attempts in targets:
        for attempt_id in attempts:
            by_attempt.setdefault(attempt_id, set()).add(target["id"])
    candidates = {}
    for index, (attempt_id, cells) in enumerate(by_attempt.items(), 1):
        candidates.update({(cell, attempt_id): result for cell, result in
                           process_attempt(attempt_id, sorted(cells), attempt_records[attempt_id], queue, output).items()})
        if index % 20 == 0 or index == len(by_attempt):
            print(f"Prepared {index}/{len(by_attempt)} retained sheets", flush=True)
    records = []
    for target, attempts in targets:
        alternatives = [candidates[(target["id"], attempt_id)] for attempt_id in attempts]
        alternatives.sort(key=lambda entry: (
            "raw_canvas_aspect_changed" in entry["issues"],
            "empty_extraction" in entry["issues"],
            "insufficient_raw_sampling" in entry["issues"],
            len(entry["registration_flags"]),
            -min(entry["actual_sampling"]),
        ))
        records.append({"target_id": target["id"], "name": target["name"],
                        "family": target["treatment"], "selected": alternatives[0]["attempt"] if alternatives else None,
                        "alternatives": alternatives, "status": "prepared_for_visual_review" if alternatives else
                        "no_retained_raw_return"})
    by_target = {entry["target_id"]: entry for entry in records}
    for entry in records:
        if entry["alternatives"]:
            continue
        donor_id = queue.state["cells"].get(entry["target_id"], {}).get("reuse_candidate_donor") or \
            NATIVE_IDENTICAL_HOLDS.get(entry["target_id"])
        if not donor_id:
            continue
        target_member = queue.members[entry["target_id"]][1]
        donor_member = queue.members[donor_id][1]
        target_contract = queue.targets[target_member["target"]]
        donor_contract = queue.targets[donor_member["target"]]
        if (target_member["source_sha256"] != donor_member["source_sha256"] or
                target_member["source_rect"] != donor_member["source_rect"] or
                target_contract["x2_size"] != donor_contract["x2_size"] or
                target_contract["compositing"] != donor_contract["compositing"]):
            raise ValueError(f"Reuse destination differs from donor: {entry['target_id']} -> {donor_id}")
        donor_prepared = by_target.get(donor_id)
        if donor_prepared and donor_prepared["alternatives"]:
            source = donor_prepared["alternatives"][0]
            candidate_path = Path(source["path"])
            raw_path = Path(source["raw"])
            raw_hash = source["raw_sha256"]
            attempt_id = source["attempt"]
            sampling = source["actual_sampling"]
            raw_rect = source["raw_rect"]
            flags = source["registration_flags"]
        else:
            donor_name = donor_contract["runtime_name"].lower()
            catalog_asset = data["assets"].get(donor_name)
            if not catalog_asset or not catalog_asset["candidate"]:
                continue
            candidate_path = (HERE / unquote(catalog_asset["candidate"])).resolve()
            raw_path = candidate_path
            raw_hash = digest(raw_path)
            attempt_id = "reuse:" + donor_id
            sampling = [2, 2]
            raw_rect = [0, 0, *target_contract["x2_size"]]
            flags = {}
        if not candidate_path.is_file() or not raw_path.is_file() or digest(raw_path) != raw_hash:
            raise ValueError(f"Donor candidate missing: {candidate_path}")
        destination_path = output / f"{entry['target_id']}__reuse-{donor_id}.png"
        shutil.copyfile(candidate_path, destination_path)
        measured = registration.measurements(target_member, target_contract, candidate_path)
        flags = {profile: report["failures"] for profile, report in measured["profiles"].items()
                 if report["failures"]}
        option = {
            "cell_id": entry["target_id"], "attempt": attempt_id, "path": str(destination_path.resolve()),
            "sha256": digest(destination_path), "raw": str(raw_path), "raw_sha256": raw_hash,
            "raw_rect": raw_rect, "actual_sampling": sampling, "x2_size": target_contract["x2_size"],
            "source_sha256": target_member["source_sha256"], "matte": {"method": "exact_native_donor_reuse"},
            "operation": "Preview exact-native donor art at this separate destination; no acceptance implied.",
            "issues": ["reuse_destination_review"] +
                      (["known_donor_geometry_hold"] if entry["target_id"] in NATIVE_IDENTICAL_HOLDS else []) +
                      (["registration_guard_flag"] if flags else []),
            "registration_flags": flags, "visual_approval": False, "reuse_of": donor_id,
        }
        entry.update(selected=attempt_id, alternatives=[option], status="donor_reuse_preview")
    report = {"schema": "openyamm-paperdoll-raw-prepared-v1", "recipe": RECIPE,
              "targets": records, "summary": {
                  "targets": len(records), "prepared": sum(bool(entry["alternatives"]) for entry in records),
                  "without_raw": sum(not entry["alternatives"] for entry in records),
                  "alternatives": sum(len(entry["alternatives"]) for entry in records),
                  "families": dict(Counter(entry["family"] for entry in records)),
                  "issues": dict(Counter(issue for entry in records for option in entry["alternatives"]
                                         for issue in option["issues"])),
              }, "note": "Technical extraction for review only; no visual approval, checkpoint change or runtime install."}
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
