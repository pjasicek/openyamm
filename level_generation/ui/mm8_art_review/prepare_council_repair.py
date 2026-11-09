"""Prepare identity-bound repair references for MM6 council body portraits."""

import hashlib
import json
from pathlib import Path

from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent

GROUPS = (
    ("goatee_0003", ("npc0002",), "npc0003",
     "Match his angular brown eyes, narrow face, auburn hair, and short dark goatee. Keep the purple cap and raised hand."),
    ("mustache_0006", ("npc0004", "npc0005"), "npc0006",
     "Both poses are the same middle-aged man: match his eyes, nose, facial proportions and dark moustache under the brown hat."),
    ("goatee_0009", ("npc0007", "npc0008"), "npc0009",
     "Both poses are the same long-haired man: match his face, eyes, dark moustache and pointed goatee."),
    ("eyes_0012", ("npc0010", "npc0011"), "npc0012",
     "Both poses are the same young man. Remove the invented round glasses completely; show his visible eyes and strong eyebrows as in the avatar. Keep his dark floppy cap."),
    ("boy_0015", ("npc0013", "npc0014"), "npc0015",
     "Both poses depict the same youthful boy as the avatar, not a woman. Match his boyish face, dark hair, brown cap and natural lips. Give the white shirt and burgundy vest a flat male chest without cleavage."),
    ("beard_0018", ("npc0016", "npc0017"), "npc0018",
     "Both poses are the same middle-aged man: match his eyes, broad nose, dark moustache and pointed goatee. Keep his hat, dark vest, white sleeves and hand gestures."),
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_image(path):
    with Image.open(path) as image:
        return image.convert("RGBA")


def put_body(canvas, image, slot):
    enlarged = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    slot_x = 80 if slot == 0 else 536
    x = slot_x + (400 - enlarged.width) // 2
    y = (640 - enlarged.height) // 2
    canvas.alpha_composite(enlarged, (x, y))
    return [x, y, enlarged.width, enlarged.height]


def main():
    catalog = {item["name"]: item for item in read_catalog()["items"]
               if item["namespace"] == "worlds/mm6" and item["category"] == "NPC portraits"}
    base = HERE / "council_body_repair"
    for name, body_names, avatar_name, focus in GROUPS:
        directory = base / name
        directory.mkdir(parents=True, exist_ok=True)
        target = Image.new("RGBA", (960, 640))
        native = Image.new("RGBA", (960, 640))
        cells = []
        for slot, body_name in enumerate(body_names):
            item = catalog[body_name]
            parent = next(candidate for candidate in item["candidates"]
                          if candidate["source"] == "new NPC imagegen master")
            parent_path = (HERE / parent["path"]).resolve()
            current = source_image(parent_path)
            original = source_image(HERE / item["original"])
            if original.size != tuple(item["native_size"]) or current.size != tuple(item["x2_size"]):
                raise ValueError(f"Unexpected body size: {body_name}")
            current_rect = put_body(target, current, slot)
            native_x2 = original.resize(tuple(item["x2_size"]), Image.Resampling.NEAREST)
            native_rect = put_body(native, native_x2, slot)
            if current_rect != native_rect:
                raise ValueError(f"Reference slot drift: {body_name}")
            cells.append({
                "id": item["id"], "name": body_name, "slot": slot,
                "sheet_rect": current_rect, "x2_size": item["x2_size"],
                "source_sha256": item["source_sha256"],
                "parent_artifact": str(parent_path.relative_to(HERE.parents[2])),
                "parent_sha256": sha256(parent_path),
            })
        avatar = catalog[avatar_name]
        avatar_candidate = next(candidate for candidate in avatar["candidates"]
                                if candidate["source"] == "review-only border repair")
        portrait = source_image(HERE / avatar_candidate["path"])
        original_avatar = source_image(HERE / avatar["original"])
        identity = Image.new("RGBA", (640, 400), (46, 52, 56, 255))
        big = portrait.resize((portrait.width * 2, portrait.height * 2), Image.Resampling.LANCZOS)
        native_avatar = original_avatar.resize(big.size, Image.Resampling.NEAREST)
        identity.alpha_composite(big, (34, (400 - big.height) // 2))
        identity.alpha_composite(native_avatar, (354, (400 - native_avatar.height) // 2))
        target.save(directory / "edit_target.png", optimize=True)
        native.save(directory / "native_bodies.png", optimize=True)
        identity.save(directory / "identity.png", optimize=True)
        prompt = (
            "Use case: identity-preserve. Asset type: MM6 Free Haven Oracle council body portrait repair. "
            "Image 1 is the edit target: one or two restored body cutouts in fixed slots. Image 2 is the "
            "identity reference: the approved-looking restored avatar on the left and its native original "
            "on the right. Image 3 is the native body pose reference. Change the body portraits in image 1 "
            "so their faces clearly depict the exact same person as image 2. " + focus + " "
            "Preserve each complete body, costume, hands, raised or lowered thumb, pose, scale, placement, "
            "lighting and painted fantasy game style. Preserve the transparent background, all gaps and "
            "the exact 960x640 sheet composition. No new props, borders, text, symbols or other people. "
            "Do not include the avatar reference in the output. Return only the repaired body sheet with "
            "the same slot order, at least 960x640."
        )
        (directory / "prompt.txt").write_text(prompt + "\n")
        (directory / "layout.json").write_text(json.dumps({
            "schema": 1, "sheet_size": [960, 640], "group": name,
            "avatar": avatar["id"], "avatar_sha256": avatar["source_sha256"],
            "avatar_candidate_sha256": avatar_candidate["sha256"],
            "cells": cells,
        }, indent=2) + "\n")
        print(name, body_names, avatar_name)


if __name__ == "__main__":
    main()
