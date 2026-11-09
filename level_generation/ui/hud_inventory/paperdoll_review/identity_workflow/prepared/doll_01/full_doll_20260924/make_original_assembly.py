"""Assemble PC01's original hand poses at the game table coordinates."""

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
MANIFEST = HERE.parent / "manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    record = json.loads(MANIFEST.read_text())
    source = (REVIEW / "catalog.js").read_text()
    catalog = json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    poses = []
    for pose in record["pose_layers"]:
        stage = Image.new("RGBA", (350, 756))
        inputs = []
        for name, x, y in pose["layers"]:
            asset = catalog["assets"][name]
            source_path = (REVIEW / asset["native"]).resolve()
            with Image.open(source_path) as opened:
                native = opened.convert("RGBA")
            if native.size != tuple(asset["size"]):
                raise ValueError(f"{name}: native image size changed")
            restored_size = (native.width * 2, native.height * 2)
            stage.alpha_composite(native.resize(restored_size, Image.Resampling.NEAREST), (x * 2, y * 2))
            inputs.append({"name": name, "source": asset["source"], "source_sha256": asset["sourceHash"],
                           "placement_x2": [x * 2, y * 2], "canvas_x2": list(restored_size)})

        x2_path = HERE / f"original_assembled_{pose['pose']}_x2.png"
        x4_path = HERE / f"original_assembled_{pose['pose']}_x4.png"
        stage.save(x2_path, optimize=True)
        stage.resize((700, 1512), Image.Resampling.NEAREST).save(x4_path, optimize=True)
        poses.append({"pose": pose["pose"], "inputs": inputs,
                      "x2": {"path": x2_path.name, "sha256": digest(x2_path)},
                      "x4": {"path": x4_path.name, "sha256": digest(x4_path)}})

    report = {"schema": "openyamm-pc01-original-assembly-v2", "stage_x2": [350, 756], "poses": poses}
    (HERE / "original_assembly.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"poses": {pose["pose"]: [entry["name"] for entry in pose["inputs"]]
                                for pose in poses}}, indent=2))


if __name__ == "__main__":
    main()
