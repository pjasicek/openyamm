"""Inventory accepted MM6 placement without changing artwork or acceptance records.

Bounds are screening evidence, not anatomical landmarks. Re-run from repository root.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from ground_anchor_audit import HERE, REPO, atlas_image, bounds

OUT = HERE / "ground_anchor_review" / "accepted"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    OUT.mkdir(parents=True, exist_ok=True)
    redo = {r["project"]: r for r in read(HERE / "redo_2x/progress.json")["families"]}
    families, rows, excluded = [], [], []
    baseline_path = OUT / 'checkpoints/before_anchor_correction/audit.json'
    repair_scope = baseline_path.exists()
    if repair_scope:
        baseline = read(baseline_path)
        selected = [dict(label=f['family'], package=f['package'], status=f['execution'])
                    for f in baseline['families']]
        excluded = baseline['excluded']
    else:
        selected = read(HERE / "progress.json")["families"]
    for family in selected:
        project = (REPO / family["package"]).parent
        if repair_scope and project.name == 'redo_2x':
            project = project.parent
        key = str(project.relative_to(REPO))
        execution = redo.get(key, {}).get("status", family["status"])
        if not repair_scope and not execution.startswith("validated"):
            excluded.append(dict(family=family["label"], status=execution, project=key))
            continue
        root = (REPO / family['package']).parent if repair_scope else (
            project / "redo_2x" if key in redo else project)
        manifest = read(root / "manifest.json")
        sources = read(project / "sources.json")["sources"]
        registration = read(root / "registration.json")
        acceptance_path = root / ("review/acceptance.json" if key in redo else "acceptance.json")
        acceptance = read(acceptance_path)
        acceptance_failures = []
        for file, expected in acceptance.get("artifact_hashes", {}).items():
            path = root / file
            if not path.exists() or sha(path) != expected:
                acceptance_failures.append(file)
        if "manifest_sha256" in acceptance and sha(root / "manifest.json") != acceptance["manifest_sha256"]:
            acceptance_failures.append("manifest.json")
        pages, local, membership = {}, [], defaultdict(set)
        animations = manifest["animations"]
        for action, animation in animations.items():
            for view, sequence in animation.get("views", {}).items():
                for step in sequence:
                    membership[step["frame"]].add(action + "/" + view)
        tier = manifest["pixels_per_logical_pixel"]
        canvas, pivot = manifest["logical_canvas"], manifest["logical_pivot"]
        centered = manifest.get("anchor") == "center"
        geometry_errors = []
        source_sizes = set()
        for name, frame in manifest["frames"].items():
            source = sources[name]
            native = Image.open(REPO / source["path"])
            source_sizes.add(native.size)
            na = (np.array(native) != 0).astype(np.uint8) * 255
            enhanced = atlas_image(root, manifest, frame, pages)
            ea = np.array(enhanced)[:, :, 3]
            crop = frame["crop_origin_px"]
            origin = frame["aligned_canvas_origin_px"]
            rect = frame["crop_in_aligned_px"]
            errors = []
            transparent_rgb_difference = False
            if crop != [origin[i] + rect[i] for i in range(2)]:
                errors.append("crop_origin")
            if [rect[2]-rect[0], rect[3]-rect[1]] != list(enhanced.size):
                errors.append("crop_size")
            aligned_path = root / "aligned_2x" / (name + ".png")
            if aligned_path.exists():
                aligned = Image.open(aligned_path).convert("RGBA")
                master_pixels, atlas_pixels = np.array(aligned.crop(rect)), np.array(enhanced)
                if not np.array_equal(master_pixels, atlas_pixels):
                    alpha_equal = np.array_equal(master_pixels[:, :, 3], atlas_pixels[:, :, 3])
                    visible_equal = np.all((master_pixels[:, :, :3] == atlas_pixels[:, :, :3])
                                           | (master_pixels[:, :, 3:] == 0))
                    if alpha_equal and visible_equal:
                        transparent_rgb_difference = True
                    else:
                        errors.append("atlas_master_pixels")
                ab = aligned.getchannel("A").getbbox()
                if ab and not (rect[0] <= ab[0] and rect[1] <= ab[1] and rect[2] >= ab[2] and rect[3] >= ab[3]):
                    errors.append("crop_discards_alpha")
            else:
                errors.append("missing_master")
            expected_offset = [(canvas[0]-native.width)/2,
                               (canvas[1]-native.height)/(2 if centered else 1)]
            if frame["native_offset"][:2] != expected_offset:
                errors.append("native_offset")
            if pivot != [canvas[0]/2, canvas[1]/(2 if centered else 1)]:
                errors.append("logical_pivot")
            record = registration.get(name, {})
            independent = record.get("independent_residual_logical", {})
            legacy = record.get("placement_landmarks", {})
            if "other_landmark_residual" in legacy:
                independent = dict(independent, secondary=(np.asarray(legacy["other_landmark_residual"]).ravel()/tier).tolist())
            row = dict(family=family["label"], frame=name, actions=sorted(membership[name]), errors=errors,
                       independent_residual_logical=independent,
                       native_offset_error=[frame["native_offset"][i]-expected_offset[i] for i in range(2)],
                       transparent_rgb_difference=transparent_rgb_difference, thresholds={})
            for threshold in (16, 96, 128, 224):
                nb, eb = bounds(na, threshold), bounds(ea, threshold)
                if nb is None or eb is None:
                    row["thresholds"][str(threshold)] = dict(native_empty=nb is None, enhanced_empty=eb is None)
                    continue
                # Compare in the native canvas coordinate system, preserving intentional motion.
                eb = [(eb[i]+crop[i % 2])/tier-expected_offset[i % 2] for i in range(4)]
                row["thresholds"][str(threshold)] = dict(
                    bottom_delta=eb[3]-nb[3], top_delta=eb[1]-nb[1],
                    bounds_center_x_delta=(eb[0]+eb[2]-nb[0]-nb[2])/2)
            local.append(row)
            if errors:
                geometry_errors.append(dict(frame=name, errors=errors))
        sequence_screens = []
        by_name = {r["frame"]: r for r in local}
        for action, animation in animations.items():
            for view, steps in animation.get("views", {}).items():
                deltas = [by_name[s["frame"]]["thresholds"]["128"] for s in steps]
                for metric in ("bottom_delta", "bounds_center_x_delta"):
                    values = [d[metric] for d in deltas if metric in d]
                    if values:
                        sequence_screens.append(dict(action=action, view=view, metric=metric,
                                                     residual_range=max(values)-min(values)))
        worst = sorted(sequence_screens, key=lambda r: r["residual_range"], reverse=True)
        bottom = [r["thresholds"]["128"]["bottom_delta"] for r in local
                  if "bottom_delta" in r["thresholds"]["128"]]
        independent_values = [abs(v) for r in local for xy in r["independent_residual_logical"].values() for v in xy]
        summary = dict(family=family["label"], package=str((root/"manifest.json").relative_to(REPO)),
                       manifest_sha256=sha(root/"manifest.json"), acceptance=str(acceptance_path.relative_to(REPO)),
                       acceptance_hash_failures=acceptance_failures, execution=execution, frames=len(local),
                       acceptance_status=acceptance.get('status', 'accepted' if acceptance.get('accepted') else 'unknown'),
                       animation_metadata_matches_original=all(manifest.get(k) == read(project/"manifest.json").get(k)
                           for k in ("animations", "animations_by_palette", "native_frame_scale")),
                       transparent_rgb_only_frames=sum(r["transparent_rgb_difference"] for r in local),
                       native_sizes=sorted(source_sizes), geometry_errors=geometry_errors,
                       bottom_delta_range=[min(bottom), max(bottom)] if bottom else None,
                       bottom_over_2=sum(abs(v)>2 for v in bottom),
                       independent_evidence_frames=sum(bool(r["independent_residual_logical"]) for r in local),
                       independent_max_abs=max(independent_values) if independent_values else None,
                       worst_sequence_screens=worst[:6],
                       placement_status="not_certified; independent anatomical and motion review required")
        families.append(summary)
        rows.extend(local)
        print(family["label"], len(local), "geometry", len(geometry_errors), "bottom>2", summary["bottom_over_2"], flush=True)
    report = dict(scope="Placement repair scope: originally accepted MM6 redo packages plus four retained families",
                  units="Native logical pixels; bottom_delta positive is lower; bounds are not anatomy",
                  limits="No automated metric proves anatomical correspondence or perfect animation. "
                         "Saved secondary residuals are evidence, not independent remeasurement. "
                         "This audit is read-only; repairs are tracked in placement_queue.json. No watched playback.",
                  family_count=len(families), frame_count=len(rows), families=families, excluded=excluded, frames=rows)
    (OUT/"audit.json").write_text(json.dumps(report, indent=2)+"\n")
    lines = ["# Accepted MM6 anchor inventory", "", "Reproduce: `python3 level_generation/creatures/mm6_remaining/accepted_anchor_audit.py`.", "",
             f"Checked {len(families)} originally accepted families, {len(rows)} frame records. "
             f"{sum(f['acceptance_status'].startswith('pending') for f in families)} now await placement reacceptance. "
             f"{len(excluded)} unfinished redo families excluded.", "",
             "Positive bottom delta means restored artwork extends lower than native, in native logical pixels. "
             "The 2 px cutoff is triage only, not an acceptance tolerance. Silhouette bounds can follow weapons, "
             "wings or effects. Secondary residuals are recorded evidence, not a fresh anatomical measurement. "
             "No family is certified pixel-perfect by this audit.", "",
             "| Family | Frames | Native sizes | Geometry errors | Bottom delta min/max | >2 px frames | Secondary evidence frames | Secondary max abs px |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    offset_rows = [r for r in rows if "native_offset" in r["errors"]]
    secondary_count = sum(f["independent_evidence_frames"] for f in families)
    summary_lines = [
        "## Findings", "",
        "Current repair progress and artifact-bound visual decisions: [placement_queue.json](placement_queue.json).",
        f"- Acceptance hash failures: {sum(len(f['acceptance_hash_failures']) for f in families)}. "
        f"Visible atlas/master mismatches: {sum('atlas_master_pixels' in r['errors'] for r in rows)}. "
        f"{sum(f['transparent_rgb_only_frames'] for f in families)} frames differ only in fully transparent RGB, "
        "which is not an anchor defect.",
        f"- {len(offset_rows)} frames in {len({r['family'] for r in offset_rows})} families have reference-centering errors "
        f"{sorted({tuple(r['native_offset_error']) for r in offset_rows})} in logical X/Y pixels. "
        "The native source is centered with integer division when its width has opposite parity to the shared canvas. "
        "This can add a half-pixel animation step; mirrored views reverse the sign. "
        "See `mm6_remaining/prepare_configured.py:57`. The correct reference offset is fractional; "
        "at 2x export it is representable as one physical pixel. Do not repair accepted art automatically without "
        "checking the registration and atlas together.",
        f"- {sum(len(f['native_sizes']) > 1 for f in families)} families have multiple native BMP sizes. "
        "Originals did not universally share a fixed canvas. "
        "Their center/bottom actor anchor must be retained when mapping them into the shared logical canvas.",
        f"- {sum(f['bottom_over_2'] for f in families)} frames exceed 2 logical pixels in bottom-silhouette difference. "
        "This is a review queue, not proven foot-placement defects. "
        "Airborne poses, effects, weapons and changed anatomy affect bounds.",
        f"- Animation/scale metadata mismatches against original staged manifests: "
        f"{sum(not f['animation_metadata_matches_original'] for f in families)}. "
        "This is an offline asset audit; no GPU playback or installed-package certification was performed.",
        f"- {secondary_count} frames have saved secondary residual evidence; "
        f"{len(rows)-secondary_count} do not have it in the supported fields. "
        "Existing visual reviews may contain additional evidence. Neither group is newly certified by this audit.",
        "", "## Visual checks performed on 2026-09-22", "",
        "The following are initial diagnostic findings, before the repairs tracked in placement_queue.json. "
        "Static images only, not watched playback. These do not certify every pose.", "",
        "- Cockatrice `cktwlkb4`, before repair: head/dorsal registration holds while the feet are approximately 28.6 logical pixels "
        "too high. The neighboring `cktwlka4` sole is close, so the sequence changes leg/body proportions. "
        "Translation alone cannot align both head and feet. Revisit anatomical scale/pose registration and the "
        "selected artwork, then inspect the full walk-4 sequence. "
        "[Marked contact](../../../mm6_ckt/redo_2x/review/walk_4_redo_01_registered_contact.png).",
        "- Cobra `cobwald2`: the reported 133.7-pixel contact X residual marks different positions along the "
        "continuous snake body. It is not evidence for a 133.7-pixel translation. "
        "Use the same identifiable anatomical point in both images. "
        "[Marked contact](../../../mm6_cob/redo_2x/review/walk_2_redo_02_registered_contact.png).",
        "- PeasantF4 `natfded0`: the native sole candidate lies under the prone torso while the restored point "
        "lies by a foot. The reported 75.6-pixel X error is invalid correspondence; pelvis and actual matching "
        "feet need separate annotation. "
        "[Marked contact](../../../mm6_natf/redo_2x/review/death_corpse_redo_01_registered_contact.png).",
        "- Cleric attack A-D: inspected native-size head/neck/sole contacts. These provide useful local evidence, "
        "but do not establish the other actions or subpixel equality. "
        "[Marked contact](../../../mm6_cle/redo_2x/review/placement_attack_0_00.png).",
        "", "## Required before strict placement acceptance", "",
        "Preserve the native per-frame actor origin, including half pixels. Verify a motion-appropriate anchor "
        "and an independently identified anatomical feature on every pose at native size or larger. "
        "Review frame-to-frame residual changes, loops, action transitions, mirrored views and sheet boundaries. "
        "Do not flatten intentional native bobbing or lifted feet. Fix whole-frame translation only when both "
        "features agree; incompatible residuals require a scale/anatomy correction. Apply any correction equally "
        "to base/masks and re-export, checking crop reconstruction and acceptance hashes. "
        "Use timed playback for remaining motion uncertainty. Existing accepted status is not proof of exact motion.", "",
        "## Family inventory", "",
    ]
    lines[6:6] = summary_lines
    for f in families:
        br=f["bottom_delta_range"]
        lines.append(f"| {f['family']} | {f['frames']} | {len(f['native_sizes'])} | {len(f['geometry_errors'])} | "
                     f"{br[0]:.2f} / {br[1]:.2f} | {f['bottom_over_2']} | {f['independent_evidence_frames']} | "
                     + (f"{f['independent_max_abs']:.2f}" if f['independent_max_abs'] is not None else "missing") + " |")
    lines += ["", "Detailed frame flags, manifest hashes, acceptance hash checks and action/view residual ranges: [audit.json](audit.json).", "", "Excluded unfinished redo families: " + ", ".join(f["family"] for f in excluded)+"."]
    (OUT/"INVENTORY.md").write_text("\n".join(lines)+"\n")


if __name__ == "__main__":
    audit()
