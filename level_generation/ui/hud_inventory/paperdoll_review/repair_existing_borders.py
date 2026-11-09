"""Prepare review copies of audited opaque candidates with isolated magenta sheet seams."""

import json
import sys
from pathlib import Path
from urllib.parse import unquote

from PIL import Image


HERE = Path(__file__).resolve().parent
OUT = HERE / "edge_repaired"
sys.path.insert(0, str(HERE))
from prepare_raw_candidates import digest, repair_opaque_magenta_seam  # noqa: E402


def main():
    source = (HERE / "catalog.js").read_text()
    data = json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    OUT.mkdir(exist_ok=True)
    records = []
    for target in data["reviewTargets"]:
        entry = data["assets"][target["name"]]
        if not target["active"] or entry["candidateStatus"] not in {"candidate", "border_repaired"}:
            continue
        original_option = next((option for option in entry["preparedAlternatives"]
                                if option["attempt"] == "audited-original"), None)
        original_url = original_option["path"] if original_option else entry["candidate"]
        original_hash = original_option["sha256"] if original_option else entry["candidateHash"]
        original = (HERE / unquote(original_url)).resolve()
        if digest(original) != original_hash:
            raise ValueError(f"Audited candidate changed: {original}")
        with Image.open(original) as image:
            if image.mode != "RGBA" or image.getchannel("A").getextrema() != (255, 255):
                continue
            repaired, edges = repair_opaque_magenta_seam(image)
        if not edges:
            continue
        destination = OUT / (target["id"] + ".png")
        repaired.save(destination, optimize=True)
        records.append({
            "target_id": target["id"], "name": target["name"], "source_sha256": entry["sourceHash"],
            "original": str(original), "original_sha256": original_hash,
            "prepared": str(destination.resolve()), "prepared_sha256": digest(destination),
            "size": list(repaired.size), "edges": edges, "visual_approval": False,
        })
    report = {"schema": "openyamm-paperdoll-border-repairs-v1", "targets": records,
              "summary": {"prepared": len(records)},
              "note": "One-pixel opaque sheet seam repair for manual review; original audited artwork is retained."}
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
