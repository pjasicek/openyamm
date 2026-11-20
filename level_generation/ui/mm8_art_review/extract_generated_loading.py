"""Make exact-2x review previews from the new full-screen loading masters."""

import hashlib
import json
from pathlib import Path

from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = {row["name"]: row for row in read_catalog()["items"]
               if row["category"] == "Loading screens"}
    output_root = HERE / "generated_large" / "x2"
    output_root.mkdir(parents=True, exist_ok=True)
    entries = []
    if any(catalog[name]["source_sha256"] != catalog["loading3"]["source_sha256"]
           for name in ("loading", "loading5")):
        raise ValueError("loading or loading5 changed; generate separate masters")
    for name in ("loading", "loading2", "loading3", "loading4", "loading5"):
        item = catalog[name]
        raw_name = "loading3" if name in ("loading", "loading5") else name
        raw_path = HERE / "generated_large" / "raw" / (raw_name + ".png")
        with Image.open(raw_path) as raw:
            if raw.width < item["x2_size"][0] or raw.height < item["x2_size"][1]:
                raise ValueError(f"Insufficient generated sampling: {name}")
            if abs(raw.width / raw.height / (item["x2_size"][0] / item["x2_size"][1]) - 1) > 0.01:
                raise ValueError(f"Generated loading art changed aspect ratio: {name}")
            candidate = raw.convert("RGB").resize(tuple(item["x2_size"]), Image.Resampling.LANCZOS)
            target = output_root / (item["id"] + ".png")
            candidate.save(target, optimize=True)
        entries.append({
            "id": item["id"], "source_sha256": item["source_sha256"],
            "artifact": str(target.relative_to(ROOT)), "artifact_sha256": sha256(target),
            "raw": str(raw_path.relative_to(ROOT)), "raw_sha256": sha256(raw_path),
            "status": "unverified new imagegen master extraction",
            "source_label": "new loading imagegen master" +
                            (" (same native image as loading3)" if name in ("loading", "loading5") else ""),
            "note": "Full-frame imagegen restoration resized to exact 2x; composition and lettering need review.",
        })
    (HERE / "generated_large" / "manifest.json").write_text(
        json.dumps({"schema": 1, "items": entries}, indent=2) + "\n")
    print(f"Prepared {len(entries)} exact-2x loading previews from 3 new masters.")


if __name__ == "__main__":
    main()
