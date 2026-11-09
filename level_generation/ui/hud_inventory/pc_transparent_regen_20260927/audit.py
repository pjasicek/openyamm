"""Check staged portraits and preservation of their native/accepted/runtime sources."""

from collections import Counter
import json
from pathlib import Path

import numpy as np
from PIL import Image

import run


def audit():
    catalogue = run.read(run.HERE / "catalogue.json")
    errors, pending, measurements = [], [], []
    counts = Counter()
    originals = 0
    native_frames = {}

    def check(condition, label):
        if not condition:
            errors.append(label)

    acceptance = None
    accepted = {}
    if (run.HERE / "acceptance.json").exists():
        acceptance = run.read(run.HERE / "acceptance.json")
        revision = run.ROOT / acceptance["revision"]
        check(run.digest(revision) == acceptance["revision_sha256"], "Accepted revision receipt changed")
        accepted = {r["runtime_output_path"]: r for r in run.read(revision)["records"].values()}
        check(set(accepted) == {f["runtime_path"] for family in catalogue["families"] for f in family["frames"]},
              "Accepted revision scope differs from the generated portrait scope")

    for family in catalogue["families"]:
        check([f["number"] for f in family["frames"]] == list(range(1, 57)),
              f"{family['id']}: incomplete native family")
        for frame in family["frames"]:
            originals += 1
            native_frames[frame["name"]] = frame
            runtime_hash = frame["accepted_sha256"]
            if acceptance:
                approved = accepted.get(frame["runtime_path"], {})
                runtime_hash = approved.get("sha256")
                artifact = Path(approved.get("artifact", ""))
                check(artifact.is_file() and run.digest(artifact) == runtime_hash,
                      f"{frame['name']}: accepted transparent export changed or missing")
            for path, expected, label in [
                (run.ROOT / frame["source"], frame["source_sha256"], "native"),
                (Path(frame["accepted_artifact"]), frame["accepted_sha256"], "accepted"),
                (run.ROOT / frame["runtime_path"], runtime_hash, "runtime"),
            ]:
                check(path.is_file() and run.digest(path) == expected,
                      f"{frame['name']}: {label} hash changed or file missing")

    for job in catalogue["jobs"]:
        folder = run.HERE / job["path"]
        state = run.read(folder / "state.json")
        counts[state["status"]] += 1
        if state["status"] != "reviewed":
            pending.append({"id": job["id"], "status": state["status"],
                            "frames": job["frames"], "reason": state.get("error") or
                            state.get("extraction_error") or state.get("visual_review", {}).get("note")})
        attempt = folder / state["attempt"]
        if state["status"] == "reviewed":
            check((attempt / "report.json").is_file(), f"{job['id']}: reviewed sheet lacks an extraction report")
        if not (attempt / "report.json").exists():
            continue
        report = run.read(attempt / "report.json")
        check(run.digest(attempt / "raw.png") == state["raw_sha256"] == report["raw_sha256"],
              f"{job['id']}: master hash mismatch")
        check(run.digest(attempt / "prompt.txt") == state["prompt_sha256"],
              f"{job['id']}: prompt hash mismatch")
        check(run.digest(folder / "reference.png") == state["reference_sha256"],
              f"{job['id']}: reference hash mismatch")
        raw = Image.open(attempt / "raw.png")
        check(raw.mode == "RGBA", f"{job['id']}: master lacks RGBA")
        check(float(np.mean(np.asarray(raw.convert("RGBA"))[:, :, 3] == 0)) >= .10,
              f"{job['id']}: master lacks transparent exterior")
        check([f["number"] for f in report["frames"]] == job["frames"],
              f"{job['id']}: incorrect extracted frame sequence")
        for frame in report["frames"]:
            label = f"{job['id']}/{frame['name']}"
            original = native_frames[frame["name"]]
            if acceptance:
                check(frame["sha256"] == accepted.get(original["runtime_path"], {}).get("sha256"),
                      f"{label}: candidate differs from the user-approved export")
            for key in ["native_box", "native_anchor", "native_contact_band"]:
                check(frame[key] == original[key], f"{label}: stale {key} reference measurement")
            path = run.HERE / frame["candidate"]
            im = Image.open(path)
            check(im.mode == "RGBA" and im.size == run.SIZE, f"{label}: wrong mode or dimensions")
            check(run.digest(path) == frame["sha256"], f"{label}: export hash mismatch")
            alpha = np.asarray(im.convert("RGBA"))[:, :, 3]
            # Imagegen sometimes quantizes near-opaque interiors to 253/254.
            # Match the processor's solid-subject threshold, retaining raw alpha.
            check(int(alpha.max()) >= 240 and float(np.mean(alpha == 0)) >= .08,
                  f"{label}: missing solid subject or transparent exterior")
            check(np.array_equal(alpha, np.asarray(Image.open(run.HERE / frame["alpha"]))),
                  f"{label}: alpha preview mismatch")
            body = run.portrait_mask(alpha)
            bounds = run.box(body)
            contact = run.bottom_contact(body, frame["native_contact_band"])
            native = frame["native_box"]
            center = (bounds[0] + bounds[2] - native[0] - native[2]) / 2
            crown_error = abs(bounds[1] - native[1])
            bottom_error = abs(bounds[3] - native[3])
            contact_error = abs(contact[0] - frame["native_anchor"][0])
            check(bounds == frame["output_box"] and contact == frame["output_anchor"],
                  f"{label}: stale geometry report")
            check(center == frame["center_error"], f"{label}: stale center report")
            check(crown_error <= 2 and bottom_error <= 2 and contact_error <= 4 and abs(center) <= 6,
                  f"{label}: placement outside tolerance")
            check(min(frame["sampling"]) >= 2, f"{label}: insufficient master detail sampling")
            check(not frame["issues"], f"{label}: unresolved flags {frame['issues']}")
            measurements.append({"crown": crown_error, "bottom": bottom_error,
                                 "contact_x": contact_error, "center_x": abs(center),
                                 "sampling": min(frame["sampling"]),
                                 "maximum_alpha": int(alpha.max()),
                                 "transparent_fraction": float(np.mean(alpha == 0))})

    result = {"updated_at": run.now(), "technical_checks_pass": not errors,
              "publication_status": acceptance["status"] if acceptance else "staged",
              "all_sheets_reviewed": not pending, "native_families": len(catalogue["families"]),
              "expected_frames": originals, "audited_frames": len(measurements),
              "sheet_counts": dict(counts), "pending_sheets": pending, "errors": errors,
              "missing_native_families": catalogue["missing_native_families"]}
    if measurements:
        result["maximum_errors_pixels"] = {k: max(m[k] for m in measurements)
                                           for k in ["crown", "bottom", "contact_x", "center_x"]}
        result["minimum_master_sampling"] = min(m["sampling"] for m in measurements)
        result["minimum_peak_subject_alpha"] = min(m["maximum_alpha"] for m in measurements)
        result["minimum_transparent_fraction"] = min(m["transparent_fraction"] for m in measurements)
    run.save(run.HERE / "audit.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    audit()
