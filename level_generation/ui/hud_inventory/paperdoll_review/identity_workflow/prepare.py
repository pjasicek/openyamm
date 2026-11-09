"""Prepare portrait-linked doll and limb references without accepting generated art."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OUT = HERE / "prepared"
FIELDS = ("leftClosed", "leftHold", "leftOpen", "rightOpen", "rightHold", "rightFingers")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_catalog():
    source = (REVIEW / "catalog.js").read_text()
    return json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))


def native_image(entry):
    path = (REVIEW / unquote(entry["native"])).resolve()
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def unique_parts(character, fields):
    return list(dict.fromkeys(character[field] for field in fields if character[field]))


def assembled_poses(character, doll_type, assets):
    poses = []
    conditions = (
        ("empty", character["rightOpen"], character["leftOpen"], None),
        ("one_hand", character["rightHold"], character["leftOpen"], character["rightFingers"]),
        ("two_hand", character["rightHold"], character["leftHold"], character["rightFingers"]),
        ("shield", character["rightHold"], character["leftClosed"], character["rightFingers"]),
    )
    for label, right, left, fingers in conditions:
        layers = [(character["body"], character["bodyX"], character["bodyY"])]
        if right:
            right_x = doll_type["rightOpenX"] if label == "empty" else doll_type["rightClosedX"]
            right_y = doll_type["rightOpenY"] if label == "empty" else doll_type["rightClosedY"]
            layers.append((right, right_x, right_y))
        if left:
            if label == "empty" or label == "one_hand":
                left_x, left_y = doll_type["leftFingersX"], doll_type["leftFingersY"]
            elif label == "shield":
                left_x, left_y = doll_type["leftClosedX"], doll_type["leftClosedY"]
            else:
                left_x, left_y = doll_type["leftOpenX"], doll_type["leftOpenY"]
            layers.append((left, left_x, left_y))
        if fingers:
            layers.append((fingers, doll_type["rightFingersX"], doll_type["rightFingersY"]))
        canvas = Image.new("RGBA", (350, 756))
        for name, x, y in layers:
            if name not in assets:
                continue
            image = native_image(assets[name])
            image = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
            canvas.alpha_composite(image, (x * 2, y * 2))
        poses.append((label, canvas, layers))
    sheet = Image.new("RGBA", (4 * 350 + 3 * 12, 756), "#253137")
    for index, (_, pose, _) in enumerate(poses):
        sheet.alpha_composite(pose, (index * 362, 0))
    return sheet, [{"pose": label, "layers": layers} for label, _, layers in poses]


def prepare_character(character, data):
    assets = data["assets"]
    portrait = assets.get(character["portrait"])
    body = assets.get(character["body"])
    record = {"character_id": character["id"], "portrait": character["portrait"],
              "body": character["body"], "head_field": character["head"], "notes": character["notes"]}
    if not portrait or not body:
        record["status"] = "missing_portrait_or_body"
        record["missing"] = [name for name, asset in ((character["portrait"], portrait),
                                                   (character["body"], body)) if not asset]
        return record
    folder = OUT / f"doll_{character['id']:02d}"
    folder.mkdir(parents=True, exist_ok=True)
    portrait_image = native_image(portrait)
    portrait_x4 = portrait_image.resize((portrait_image.width * 4, portrait_image.height * 4),
                                       Image.Resampling.NEAREST)
    portrait_path = folder / "assigned_portrait_original_x4.png"
    portrait_x4.save(portrait_path, optimize=True)

    left = unique_parts(character, ("leftClosed", "leftHold", "leftOpen"))
    right = unique_parts(character, ("rightOpen", "rightHold", "rightFingers"))
    cells = []
    body_asset = assets[character["body"]]
    body_width, body_height = body_asset["size"]
    body_x, body_y = 12, 12
    cells.append((character["body"], body_x, body_y))
    column_x = body_x + body_width + 16
    heights = []
    for group in (left, right):
        column_y = 12
        for name in group:
            if name not in assets:
                continue
            cells.append((name, column_x, column_y))
            column_y += assets[name]["size"][1] + 8
        heights.append(column_y)
        column_x += max((assets[name]["size"][0] for name in group if name in assets), default=0) + 16
    sheet_width = max(body_x + body_width + 12, column_x - 4)
    sheet_height = max(body_y + body_height + 12, *heights)
    sheet = Image.new("RGBA", (sheet_width * 2, sheet_height * 2))
    layout = {}
    for name, x, y in cells:
        entry = assets[name]
        image = native_image(entry)
        image = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        sheet.alpha_composite(image, (x * 2, y * 2))
        layout[name] = {"rect": [x * 2, y * 2, image.width, image.height],
                        "native_size": entry["size"], "source": entry["source"],
                        "source_sha256": entry["sourceHash"]}
    sheet_path = folder / "body_and_limbs_original_x2.png"
    sheet.save(sheet_path, optimize=True)
    pose_path = None
    poses = []
    if left or right:
        pose_sheet, poses = assembled_poses(character, data["types"][str(character["type"])], assets)
        pose_path = folder / "assembled_native_poses_x2.png"
        pose_sheet.save(pose_path, optimize=True)
    prompt = (
        "Use case: precise-object-edit. Asset type: 2D fantasy RPG paperdoll sprites. "
        "Image 1 is the edit target sheet containing the original body and separate hand/arm layers. "
        "Image 2 is the assigned original character portrait and is the authoritative facial identity reference. "
        "Image 3, when supplied, shows the native parts assembled at the game's exact offsets in empty, one-hand, "
        "two-hand and shield poses. Restore painted detail while keeping every sprite in Image 1 separate, in its "
        "same cell rectangle, at its original scale and pose. Match the body's hair, brows, eyes, nose, beard and "
        "skin tone to Image 2 without changing its expression or face shape. Keep skin, cuffs, seams and lighting "
        "consistent across the body and all limb states. Preserve the overlap/joint ends so the arms attach cleanly "
        "in all four assembled poses. Preserve all canvas margins and transparent holes. Return only the Image 1 "
        "sheet, with its same layout and genuine transparent alpha outside each sprite. No magenta matte, scenery, "
        "labels, borders, new equipment, extra parts, shadows, checkerboard or enlarged pixel blocks."
    )
    (folder / "prompt_draft.txt").write_text(prompt + "\n")
    record.update({"status": "prepared", "kind": "jointed" if left or right else "body_only",
                   "portrait_source": portrait["source"], "portrait_source_sha256": portrait["sourceHash"],
                   "portrait_original_x4": str(portrait_path.resolve()),
                   "portrait_original_x4_sha256": digest(portrait_path),
                   "target_sheet": str(sheet_path.resolve()), "target_sheet_sha256": digest(sheet_path),
                   "sheet_size": list(sheet.size), "cells": layout,
                   "assembled_poses": str(pose_path.resolve()) if pose_path else None,
                   "assembled_poses_sha256": digest(pose_path) if pose_path else None,
                   "pose_layers": poses, "missing_limbs": [name for name in left + right if name not in assets],
                   "prompt_draft": str((folder / "prompt_draft.txt").resolve())})
    (folder / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--doll", type=int, help="Prepare one character; default prepares every table row")
    arguments = parser.parse_args()
    data = read_catalog()
    characters = [entry for entry in data["characters"] if arguments.doll is None or entry["id"] == arguments.doll]
    if not characters:
        raise ValueError(f"Character {arguments.doll} is not in character_data.txt")
    records = [prepare_character(entry, data) for entry in characters]
    report = {"schema": "openyamm-paperdoll-identity-references-v1", "records": records,
              "summary": dict(Counter(entry["status"] for entry in records)),
              "note": "Original portrait anchors and native assembly references only; no artwork approval."}
    output = OUT / ("manifest.json" if arguments.doll is None else f"doll_{arguments.doll:02d}_manifest.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
