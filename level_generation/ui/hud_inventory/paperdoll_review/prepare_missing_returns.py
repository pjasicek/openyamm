"""Split new transparent family returns into exact-2× sprites for manual review."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
OUT = HERE / "new_returns"
sys.path.insert(0, str(HERE))
from prepare_raw_candidates import decontaminate_translucent_edges, digest, image_to_x2  # noqa: E402

sys.path.insert(0, str(HERE.parent))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


def main():
    queue = queue_module.Queue()
    submitted_record = OUT / "submitted_prompts.json"
    submitted = json.loads(submitted_record.read_text())
    candidate_dir = OUT / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    groups = []
    targets = []
    for layout_path in sorted((OUT / "input").glob("*/layout.json")):
        layout = json.loads(layout_path.read_text())
        group = layout["group"]
        reference = layout_path.parent / "reference.png"
        prompt_draft = layout_path.parent / "prompt.txt"
        submitted_prompt = submitted["groups"][group]
        raw_path = OUT / "raw" / (group + ".png")
        if not raw_path.is_file():
            raise FileNotFoundError(raw_path)
        with Image.open(raw_path) as opened:
            raw = opened.convert("RGBA")
        alpha = np.asarray(raw.getchannel("A"))
        if alpha.min() != 0 or alpha.max() != 255:
            raise ValueError(f"New return lacks genuine alpha: {raw_path}")
        raw_hash = digest(raw_path)
        ref_width, ref_height = layout["reference_size"]
        scale_x, scale_y = raw.width / ref_width, raw.height / ref_height
        if abs(scale_x / scale_y - 1) > .03:
            raise ValueError(f"New return altered sheet aspect: {raw_path}")
        members = []
        for name in layout["names"]:
            cell = "engine--icons--" + name + ".bmp"
            member = queue.members[cell][1]
            contract = queue.targets[member["target"]]
            if digest(Path(queue_module.ROOT) / member["source_path"]) != member["source_sha256"]:
                raise ValueError(f"Source changed: {cell}")
            x, y, width, height = layout["rects"][name]
            rect = [round(x * scale_x), round(y * scale_y),
                    round((x + width) * scale_x), round((y + height) * scale_y)]
            crop = raw.crop(tuple(rect))
            cleaned, changed = decontaminate_translucent_edges(crop, crop)
            candidate, operation = image_to_x2(cleaned, tuple(contract["x2_size"]), False)
            candidate_path = candidate_dir / (cell + ".png")
            candidate.save(candidate_path, optimize=True)
            measurements = registration.measurements(member, contract, candidate_path)
            flags = {profile: report["failures"] for profile, report in measurements["profiles"].items()
                     if report["failures"]}
            crop_alpha = np.asarray(cleaned.getchannel("A"))
            edge = [int((crop_alpha[:, 0] >= 128).sum()), int((crop_alpha[:, -1] >= 128).sum()),
                    int((crop_alpha[0, :] >= 128).sum()), int((crop_alpha[-1, :] >= 128).sum())]
            issues = []
            if any(edge):
                issues.append("subject_at_measured_cell_boundary")
            if flags:
                issues.append("registration_guard_flag")
            if group != "item133":
                issues.append("family_quality_hold_prior")
            sampling = [round(crop.width / member["source_rect"][2], 4),
                        round(crop.height / member["source_rect"][3], 4)]
            if min(sampling) < 2:
                issues.append("insufficient_raw_sampling")
            option = {
                "cell_id": cell, "attempt": "new:" + group, "path": str(candidate_path.resolve()),
                "sha256": digest(candidate_path), "raw": str(raw_path.resolve()), "raw_sha256": raw_hash,
                "raw_rect": rect, "actual_sampling": sampling, "x2_size": contract["x2_size"],
                "source_sha256": member["source_sha256"], "matte": {"method": "genuine_alpha_return",
                "fringe_rgb_from_nearest_core": changed}, "operation": operation,
                "issues": issues, "registration_flags": flags, "visual_approval": False,
            }
            targets.append({"target_id": cell, "name": name, "family": contract["treatment"],
                            "selected": option["attempt"], "alternatives": [option],
                            "status": "new_generation_prepared_for_visual_review", "kind": "new_generation"})
            members.append({"cell": cell, "raw_rect": rect, "candidate": str(candidate_path),
                            "candidate_sha256": option["sha256"], "issues": issues})
        groups.append({"group": group, "raw": str(raw_path.resolve()), "raw_sha256": raw_hash,
                       "raw_size": list(raw.size), "reference": str(reference.resolve()),
                       "reference_sha256": digest(reference),
                       "prompt_draft": str(prompt_draft.resolve()),
                       "prompt_draft_sha256": digest(prompt_draft),
                       "submitted_prompt": submitted_prompt,
                       "submitted_prompt_sha256": hashlib.sha256(
                           submitted_prompt.encode("utf-8")).hexdigest(),
                       "submitted_prompt_record": str(submitted_record.resolve()),
                       "submitted_prompt_record_sha256": digest(submitted_record),
                       "generation_tool": submitted["tool"], "members": members,
                       "visual_approval": False})
        print(group, len(members), flush=True)
    report = {"schema": "openyamm-paperdoll-new-returns-v1", "groups": groups, "targets": targets,
              "summary": {"groups": len(groups), "prepared_targets": len(targets),
                          "registration_flagged": sum("registration_guard_flag" in t["alternatives"][0]["issues"]
                                                      for t in targets)},
              "note": "New imagegen returns are prepared for manual visual classification only; no acceptance or install."}
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
