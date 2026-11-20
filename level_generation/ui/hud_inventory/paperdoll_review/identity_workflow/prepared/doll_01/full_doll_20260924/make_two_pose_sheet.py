"""Make the user's two-cell PC01 source sheet at the existing game offsets."""

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
CELL_X2 = (350, 756)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    catalog = json.loads((REVIEW / "catalog.js").read_text().removeprefix(
        "window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    poses = json.loads((HERE.parent / "manifest.json").read_text())["pose_layers"]
    sheet = Image.new("RGBA", (CELL_X2[0] * 2, CELL_X2[1]))
    records = []
    for index, pose_name in enumerate(("empty", "one_hand")):
        pose = next(entry for entry in poses if entry["pose"] == pose_name)
        cell = Image.new("RGBA", CELL_X2)
        layers = []
        for name, x, y in pose["layers"]:
            if name == "pc01rhb":
                continue  # The finger-over-weapon layer is extracted later.
            asset = catalog["assets"][name]
            source = REVIEW / asset["native"]
            with Image.open(source) as opened:
                image = opened.convert("RGBA")
            if image.size != tuple(asset["size"]):
                raise ValueError(f"{name}: source size changed")
            cell.alpha_composite(image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST),
                                 (x * 2, y * 2))
            layers.append({"name": name, "source": str(source.relative_to(REVIEW)),
                           "sha256": digest(source), "xy_x2": [x * 2, y * 2]})
        cell_path = HERE / f"source_two_pose_{pose_name}_x2.png"
        cell.save(cell_path, optimize=True)
        sheet.alpha_composite(cell, (index * CELL_X2[0], 0))
        records.append({"pose": pose_name, "cell_index": index, "layers": layers,
                        "cell": cell_path.name, "sha256": digest(cell_path)})

    x2_path = HERE / "source_two_pose_sheet_x2.png"
    x4_path = HERE / "source_two_pose_sheet_x4.png"
    sheet.save(x2_path, optimize=True)
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).save(x4_path, optimize=True)
    report = {"schema": "openyamm-pc01-two-pose-source-v1", "layout": "1 row x 2 equal columns",
              "cell_x2": list(CELL_X2), "sheet_x2": [sheet.width, sheet.height], "poses": records,
              "sheet": {"x2": x2_path.name, "x2_sha256": digest(x2_path),
                        "x4": x4_path.name, "x4_sha256": digest(x4_path)},
              "identity_reference": "../assigned_portrait_original_x4.png"}
    (HERE / "source_two_pose_sheet.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"size_x2": sheet.size, "pose_layers": {r["pose"]: [x["name"] for x in r["layers"]]
                        for r in records}}, indent=2))


if __name__ == "__main__":
    main()
