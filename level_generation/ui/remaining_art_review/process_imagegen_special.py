#!/usr/bin/env python3
"""Extract imagegen returns whose regular grid detector cannot register.

The explicit boxes below were measured against the raw returns. These are
review candidates, never acceptance or runtime files. The original hole in
makeme is restored only after the generated checkerboard aligns with it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from process_imagegen_regen import HERE, RUN, x2_resize


STRIP_BOXES = {
    "engine--icons--footer.bmp": ("retry-opaque_controls-mixed-001", (61, 311, 2109, 416)),
    "engine--icons--endcap.bmp": ("retry-opaque_controls-mixed-002", (67, 343, 2104, 383)),
    "engine--icons--ib-8pxbar.bmp": ("retry-opaque_controls-mixed-003", (338, 95, 388, 2077)),
    "engine--icons--compass.bmp": ("retry-opaque_controls-mixed-004", (90, 321, 2082, 394)),
    "engine--icons--mhp_yel.bmp": ("retry-opaque_controls-mixed-005", (69, 192, 950, 224)),
    "engine--icons--mhp_grn.bmp": ("retry-opaque_controls-mixed-005", (1036, 192, 1917, 224)),
    "engine--icons--manay.bmp": ("retry-opaque_controls-mixed-006", (179, 174, 222, 722)),
    "engine--icons--manar.bmp": ("retry-opaque_controls-mixed-006", (456, 174, 500, 722)),
    "engine--icons--manag.bmp": ("retry-opaque_controls-mixed-006", (734, 174, 777, 722)),
    "engine--icons--manab.bmp": ("retry-opaque_controls-mixed-006", (179, 921, 222, 1471)),
    "engine--icons--mhp_capr.bmp": ("retry-opaque_controls-mixed-006", (445, 1127, 508, 1220)),
    "engine--icons--mhp_capl.bmp": ("retry-opaque_controls-mixed-006", (723, 1127, 786, 1221)),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_candidate(target_id: str, image: Image.Image, source_hash: str, evidence: dict) -> dict:
    destination = RUN / "special_candidates" / target_id / "candidate-2x.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)
    return {
        "status": "candidate_technical", "source_sha256": source_hash,
        "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
        **evidence,
    }


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    retry_plan = json.loads((RUN / "retry_plan.json").read_text())
    cells = {cell["id"]: cell for sheet in plan["sheets"] + retry_plan["sheets"] for cell in sheet["cells"]}
    report = {"schema": 1, "tool": "built-in image_gen with measured manual extraction", "items": {}}
    for target_id, (sheet, box) in STRIP_BOXES.items():
        cell = cells[target_id]
        raw_path = RUN / "retry_returns" / f"{sheet}.png"
        original_path = HERE / "originals" / f"{target_id}.png"
        if sha256(original_path) != cell["original_sha256"]:
            raise ValueError(f"Original changed: {target_id}")
        with Image.open(raw_path) as raw, Image.open(original_path) as original:
            width, height = original.size
            if box[2] - box[0] < width * 2 or box[3] - box[1] < height * 2:
                raise ValueError(f"Below native 2x detail: {target_id}")
            candidate = x2_resize(raw.crop(box), (width * 2, height * 2))
            candidate.putalpha(Image.new("L", candidate.size, 255))
        report["items"][target_id] = save_candidate(target_id, candidate, cell["source_sha256"], {
            "method": "manually measured imagegen foreground box, exact 2x resize",
            "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path), "region": list(box),
            "sampling": [round((box[2] - box[0]) / width, 3), round((box[3] - box[1]) / height, 3)],
        })

    terra = next(sheet for sheet in plan["sheets"] if sheet["id"] == "terra-003")
    raw_path = RUN / "returns/terra-003.png"
    with Image.open(raw_path) as raw:
        sx = raw.width / terra["native_sheet_size"][0]
        sy = raw.height / terra["native_sheet_size"][1]
        for cell in terra["cells"]:
            target_id = cell["id"]
            x, y, width, height = cell["rect"]
            box = (round(x * sx), round(y * sy), round((x + width) * sx), round((y + height) * sy))
            if min((box[2] - box[0]) / width, (box[3] - box[1]) / height) < 2:
                raise ValueError(f"Below native 2x detail: {target_id}")
            crop = raw.crop(box).convert("RGB")
            candidate = crop.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            report["items"][target_id] = save_candidate(target_id, candidate, cell["source_sha256"], {
                "method": "regular row bounds measured in returned six-frame animation",
                "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path), "region": list(box),
                "sampling": [round(sx, 3), round(sy, 3)],
            })

    target_id = "engine--icons--makeme.pcx"
    cell = cells[target_id]
    raw_path = RUN / "returns/makeme-direct.png"
    original_path = HERE / "originals" / f"{target_id}.png"
    with Image.open(original_path) as original, Image.open(raw_path) as raw:
        original = original.convert("RGBA")
        raw = raw.convert("RGB")
        if sha256(original_path) != cell["original_sha256"] or raw.width < original.width * 2 \
                or raw.height < original.height * 2:
            raise ValueError("Changed source or below native 2x detail: makeme")
        candidate = raw.resize((original.width * 2, original.height * 2), Image.Resampling.LANCZOS).convert("RGBA")
        source_mask = np.asarray(original.getchannel("A")) == 0
        yy, xx = np.where(source_mask)
        original_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
        check = np.asarray(candidate.convert("RGB"), dtype=np.int16)
        checker = (check.min(axis=2) > 170) & (np.ptp(check, axis=2) < 5)
        expected = np.asarray(original.getchannel("A").resize(candidate.size, Image.Resampling.NEAREST)) == 0
        coverage = float(np.logical_and(checker, expected).sum() / expected.sum())
        if coverage < 0.75:
            raise ValueError(f"Generated checkerboard does not align with original hole: {coverage:.3f}")
        candidate.putalpha(original.getchannel("A").resize(candidate.size, Image.Resampling.NEAREST))
    report["items"][target_id] = save_candidate(target_id, candidate, cell["source_sha256"], {
        "method": "full-screen imagegen edit; matched checkerboard replaced by original rectangular alpha hole",
        "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
        "original_hole_box": list(original_box), "checkerboard_coverage_inside_hole": round(coverage, 4),
        "sampling": [round(raw.width / original.width, 3), round(raw.height / original.height, 3)],
    })
    (RUN / "special_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} manually registered imagegen review candidates")


if __name__ == "__main__":
    main()
