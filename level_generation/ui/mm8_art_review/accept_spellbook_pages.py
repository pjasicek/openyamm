"""Record the twelve approved spellbook pages, including the Real-ESRGAN Body page."""

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / "staged_spellbook_pages"
BODY = "engine--icons--sbb000.bmp"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def outer_magenta(pixels):
    red, green, blue = [pixels[:, :, channel].astype(np.float32) for channel in range(3)]
    purple = ((red > 70) & (blue > 70) & (red > green * 1.35)
              & (blue > green * 1.35) & (pixels[:, :, 3] >= 16))
    purple[3:-3, 3:-3] = False
    return int(purple.sum())


def main():
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))
    pages = [item for item in catalog["items"] if item["category"] == "Spellbook pages"]
    if len(pages) != 12 or len({item["id"] for item in pages}) != 12:
        raise ValueError("Expected 12 distinct active spellbook pages")
    body = json.loads((HERE / "sbb000_esrgan/manifest.json").read_text())
    for key, hash_key in (("source", "source_sha256"),
                          ("native_rendered_png", "native_rendered_sha256"),
                          ("master", "master_sha256"), ("candidate", "candidate_sha256"),
                          ("binary", "binary_sha256")):
        if digest(ROOT / body[key]) != body[hash_key]:
            raise ValueError(f"Real-ESRGAN Body page provenance changed: {key}")
    for extension in ("bin", "param"):
        path = ROOT / f"tools/upscaling/models/realesrgan-x4plus.{extension}"
        if digest(path) != body[f"model_{extension}_sha256"]:
            raise ValueError(f"Real-ESRGAN model changed: {path}")
    if body["model"] != "realesrgan-x4plus" or body["candidate_size"] != [1280, 960]:
        raise ValueError("Unexpected Body page restoration method or canvas")
    approvals = []
    staged = []
    for item in pages:
        identity = item["id"]
        source = HERE / item["source"]
        if identity == BODY:
            artwork = ROOT / body["candidate"]
            candidate_sha256 = body["candidate_sha256"]
            if body["source_sha256"] != item["source_sha256"]:
                raise ValueError("Body page source changed since Real-ESRGAN inference")
        else:
            candidate = next((entry for entry in item["candidates"]
                              if entry["status"] == "pipeline accepted"), None)
            if candidate is None:
                raise ValueError(f"No accepted 2x page candidate: {identity}")
            artwork = HERE / candidate["path"]
            candidate_sha256 = candidate["sha256"]
        if digest(source) != item["source_sha256"] or digest(artwork) != candidate_sha256:
            raise ValueError(f"Source or candidate changed: {identity}")
        with Image.open(artwork) as image:
            if list(image.size) != item["x2_size"]:
                raise ValueError(f"Page is not exact 2x: {identity}")
            pixels = np.asarray(image.convert("RGBA"))
        if np.any(pixels[:, :, 3] != 255) or outer_magenta(pixels):
            raise ValueError(f"Page has transparency or a purple edge: {identity}")
        destination = OUTPUT / "engine/icons_x2" / (item["name"] + ".png")
        if destination.exists() and digest(destination) != candidate_sha256:
            raise ValueError(f"Staged copy differs from the approved page: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copy2(artwork, destination)
        if digest(destination) != candidate_sha256:
            raise ValueError(f"Staged page changed: {identity}")
        approvals.append({"id": identity, "category": "Spellbook pages", "decision": "approve",
                          "source_sha256": item["source_sha256"],
                          "candidate_sha256": candidate_sha256,
                          "artifact": destination.relative_to(HERE).as_posix()})
        staged.append({"id": identity, "source_sha256": item["source_sha256"],
                       "artifact": destination.relative_to(ROOT).as_posix(),
                       "artifact_sha256": candidate_sha256, "status": "review approved and staged",
                       "source_label": "approved spellbook page",
                       "method": "Real-ESRGAN x4plus, Lanczos to exact 2x" if identity == BODY
                       else "existing accepted restoration"})
    if len(approvals) != 12:
        raise ValueError(f"Expected 12 restored pages; found {len(approvals)}")
    revision = hashlib.sha256(json.dumps(approvals, sort_keys=True).encode()).hexdigest()[:16]
    write_json(OUTPUT / "manifest.json", {"schema": 1, "kind": "staged_spellbook_pages",
                                           "revision": revision, "count": len(staged), "pending": [],
                                           "items": staged})
    write_json(HERE / "spellbook_review_acceptance.json", {"schema": 1, "kind": "visual_review_acceptance",
                                                          "revision": revision, "scope": ["Spellbook pages"],
                                                          "requested_total": 12, "pending": [], "items": approvals})
    print(f"Approved and staged all {len(staged)} spellbook pages")


if __name__ == "__main__":
    main()
