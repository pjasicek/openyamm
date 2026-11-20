"""Record the approved spell foregrounds and stage exact 2x PNGs for later integration.

The user's approval applies to the 222 candidates in spell_foreground_stage_v2.
This staging area is separate from the older HUD queue and runtime asset roots.
"""

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = HERE / "spell_foreground_stage_v2"
OUTPUT = HERE / "staged_spell_icons"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def main():
    stage = json.loads((STAGE / "manifest.json").read_text())
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))
    originals = {item["id"]: item for item in catalog["items"] if item["category"] == "Spell icons"}
    if stage["stage"] != "transparent spell foregrounds v2" or len(stage["items"]) != 222:
        raise ValueError("Expected the complete v2 spell review stage")
    if len(originals) != 222 or len({item["id"] for item in stage["items"]}) != 222:
        raise ValueError("Spell stage does not match the 222 active spell icon states")

    approvals = []
    staged = []
    for item in stage["items"]:
        identity = item["id"]
        original = originals[identity]
        source = HERE / original["source"]
        candidate = STAGE / item["candidate"]
        if original["source_sha256"] != item["source_sha256"] or digest(source) != item["source_sha256"]:
            raise ValueError(f"Native source changed: {identity}")
        if digest(candidate) != item["candidate_sha256"] or original["x2_size"] != item["x2_size"]:
            raise ValueError(f"Reviewed candidate changed: {identity}")
        with Image.open(candidate) as image:
            if image.mode != "RGBA" or list(image.size) != item["x2_size"]:
                raise ValueError(f"Candidate is not an exact 2x RGBA image: {identity}")
            minimum, maximum = image.getchannel("A").getextrema()
            if minimum != 0 or maximum == 0:
                raise ValueError(f"Candidate lacks a transparent foreground: {identity}")
        destination = OUTPUT / "engine/icons_x2" / (item["name"] + ".png")
        if destination.exists() and digest(destination) != item["candidate_sha256"]:
            raise ValueError(f"Staged file differs from the approved candidate: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(candidate, destination)
        if digest(destination) != item["candidate_sha256"]:
            raise ValueError(f"Staged copy changed: {identity}")
        artifact = destination.relative_to(HERE).as_posix()
        approvals.append({"id": identity, "category": "Spell icons", "decision": "approve",
                          "source_sha256": item["source_sha256"],
                          "candidate_sha256": item["candidate_sha256"], "artifact": artifact})
        staged.append({"id": identity, "source_sha256": item["source_sha256"],
                       "artifact": destination.relative_to(ROOT).as_posix(),
                       "artifact_sha256": item["candidate_sha256"],
                       "status": "review approved and staged", "source_label": "approved transparent spell foreground v2",
                       "source_stage": "spell_foreground_stage_v2"})

    revision = hashlib.sha256(json.dumps(approvals, sort_keys=True).encode()).hexdigest()[:16]
    write_json(OUTPUT / "manifest.json", {"schema": 1, "kind": "staged_spell_foregrounds",
                                           "revision": revision, "count": len(staged), "items": staged})
    write_json(HERE / "spell_review_acceptance.json", {"schema": 1, "kind": "visual_review_acceptance",
                                                       "revision": revision, "scope": ["Spell icons"],
                                                       "stage": stage["stage"], "items": approvals})
    print(f"Approved and staged {len(staged)} spell icon states at revision {revision}")


if __name__ == "__main__":
    main()
