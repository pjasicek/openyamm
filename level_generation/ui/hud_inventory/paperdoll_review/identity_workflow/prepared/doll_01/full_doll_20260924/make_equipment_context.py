"""Render original PC01 hand poses with the game's item-table placements."""

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = (REVIEW / "catalog.js").read_text()
    catalog = json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    character = next(entry for entry in catalog["characters"] if entry["id"] == 1)
    doll_type = catalog["types"][str(character["type"])]
    items = {entry["id"]: entry for entry in catalog["items"]}
    poses = json.loads((HERE.parent / "manifest.json").read_text())["pose_layers"]
    records = []

    def native(name: str) -> Image.Image:
        asset = catalog["assets"][name]
        with Image.open(REVIEW / asset["native"]) as opened:
            image = opened.convert("RGBA")
        if image.size != tuple(asset["size"]):
            raise ValueError(f"{name}: original canvas changed")
        return image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)

    def item_position(item_id: int, slot: str) -> tuple[int, int]:
        item = items[item_id]
        if slot == "main":
            finger_width = catalog["assets"][character["rightFingers"]]["size"][0]
            grip_x = doll_type["rightFingersX"] + (finger_width + 1) // 2
            return (grip_x - item["equipX"],
                    doll_type["rightClosedY"] + doll_type["mainHandOffsetY"] - item["equipY"])
        return (doll_type["leftClosedX"] + doll_type["shieldX"] - item["equipX"],
                doll_type["leftClosedY"] + doll_type["shieldY"] - item["equipY"])

    for pose_name, item_ids in (("one_hand", [(1, "main")]),
                                ("shield", [(1, "main"), (99, "shield")])):
        pose = next(entry for entry in poses if entry["pose"] == pose_name)
        stage = Image.new("RGBA", (350, 756))
        for name, x, y in pose["layers"]:
            if name == character["rightFingers"]:
                continue
            stage.alpha_composite(native(name), (x * 2, y * 2))
        placed_items = []
        for item_id, slot in item_ids:
            item = items[item_id]
            x, y = item_position(item_id, slot)
            stage.alpha_composite(native(item["icon"]), (x * 2, y * 2))
            placed_items.append({"id": item_id, "icon": item["icon"], "slot": slot,
                                 "table_position": [x, y], "position_x2": [x * 2, y * 2]})
        fingers = next((layer for layer in pose["layers"] if layer[0] == character["rightFingers"]), None)
        if fingers:
            stage.alpha_composite(native(fingers[0]), (fingers[1] * 2, fingers[2] * 2))
        x2_path = HERE / f"original_{pose_name}_equipped_x2.png"
        x4_path = HERE / f"original_{pose_name}_equipped_x4.png"
        stage.save(x2_path, optimize=True)
        stage.resize((700, 1512), Image.Resampling.NEAREST).save(x4_path, optimize=True)
        records.append({"pose": pose_name, "items": placed_items,
                        "x2": {"path": x2_path.name, "sha256": digest(x2_path)},
                        "x4": {"path": x4_path.name, "sha256": digest(x4_path)}})

    (HERE / "equipment_context.json").write_text(json.dumps({"records": records}, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
