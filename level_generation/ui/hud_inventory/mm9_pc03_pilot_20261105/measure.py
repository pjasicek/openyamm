"""Measure every portrait frame of the MM6-MM8 families and the pilot with a face-landmark model.

Needs mediapipe (not a project dependency): run with a scratch venv python and pass the face_landmarker.task model.
Per frame it records MediaPipe blendshapes (eyes, gaze, jaw, smile, pucker, brows), head yaw/pitch/roll from the
facial transformation matrix, the visible head height (alpha), and skin tint relative to the family's frame 01.
Writes measurements.json: {family: {frame: {...}}}.

    venv/bin/python measure.py --model face_landmarker.task
"""

import argparse
import json
import math
import re
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ICONS = ROOT / "assets_dev/engine/icons_x2"
SHAPES = ["eyeBlinkLeft", "eyeBlinkRight", "eyeLookUpLeft", "eyeLookUpRight", "eyeLookDownLeft", "eyeLookDownRight",
          "eyeLookInLeft", "eyeLookInRight", "eyeLookOutLeft", "eyeLookOutRight", "eyeWideLeft", "eyeWideRight",
          "eyeSquintLeft", "eyeSquintRight", "jawOpen", "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft",
          "mouthFrownRight", "mouthPucker", "mouthFunnel", "browInnerUp", "browDownLeft", "browDownRight",
          "mouthPressLeft", "mouthPressRight", "mouthRollLower", "cheekPuff"]


def families():
    found = {}
    for path in sorted(ICONS.glob("*-56.png")):
        prefix = path.name[:-len("-56.png")]
        if all((ICONS / f"{prefix}-{n:02d}.png").exists() for n in range(1, 57)):
            found[prefix] = lambda n, p=prefix: ICONS / f"{p}-{n:02d}.png"
    found["mm9pc03"] = lambda n: HERE / "frames" / f"mm9pc03-{n:02d}.png"
    return found


def prepared(path):
    rgba = Image.open(path).convert("RGBA")
    canvas = Image.new("RGBA", (rgba.width + 60, rgba.height + 60), (128, 128, 128, 255))
    canvas.alpha_composite(rgba, (30, 30))
    big = canvas.convert("RGB").resize((canvas.width * 4, canvas.height * 4), Image.Resampling.LANCZOS)
    return rgba, np.ascontiguousarray(np.asarray(big))


def euler(matrix):
    r = np.asarray(matrix)[:3, :3]
    yaw = math.degrees(math.atan2(-r[2, 0], math.hypot(r[0, 0], r[1, 0])))
    pitch = math.degrees(math.atan2(r[2, 1], r[2, 2]))
    roll = math.degrees(math.atan2(r[1, 0], r[0, 0]))
    return yaw, pitch, roll


def tint(rgba):
    a = np.asarray(rgba).astype(float)
    mask = a[..., 3] > 250
    rgb = a[..., :3][mask]
    total = rgb.sum(axis=1, keepdims=True) + 1e-6
    chroma = (rgb / total).mean(axis=0)
    return [float(v) for v in chroma], float(rgb.mean()), float(np.std(rgb, axis=1).mean())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    options = vision.FaceLandmarkerOptions(base_options=mp_tasks.BaseOptions(model_asset_path=args.model),
                                           output_face_blendshapes=True,
                                           output_facial_transformation_matrixes=True, num_faces=1,
                                           min_face_detection_confidence=0.2, min_face_presence_confidence=0.2)
    result = {}
    with vision.FaceLandmarker.create_from_options(options) as landmarker:
        for family, frame_path in families().items():
            rows = {}
            for number in range(1, 57):
                rgba, big = prepared(frame_path(number))
                alpha = np.asarray(rgba.getchannel("A")) > 128
                ys = np.where(alpha.any(axis=1))[0]
                chroma, brightness, saturation = tint(rgba)
                row = {"head_top": int(ys.min()) if len(ys) else None,
                       "head_height": int(ys.max() - ys.min() + 1) if len(ys) else 0,
                       "chroma": chroma, "brightness": brightness, "saturation": saturation}
                detection = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=big))
                if detection.face_blendshapes:
                    shapes = {c.category_name: c.score for c in detection.face_blendshapes[0]}
                    row["shapes"] = {name: round(shapes[name], 3) for name in SHAPES}
                    yaw, pitch, roll = euler(detection.facial_transformation_matrixes[0])
                    row.update(yaw=round(yaw, 1), pitch=round(pitch, 1), roll=round(roll, 1))
                rows[f"{number:02d}"] = row
            result[family] = rows
            detected = sum("shapes" in r for r in rows.values())
            print(family, detected, "/ 56 detected", flush=True)
    (HERE / "measurements.json").write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    main()
