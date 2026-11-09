#!/usr/bin/env python3
"""Keep the Fly, Water Walk, and Levitate drawings stationary across their loops.

The sheet restorations vary the anatomy and silhouette from frame to frame. Placement
registration cannot remove that wobble. This pass uses one restored drawing per
sequence and confines animation to wings, fixed-position stars, or lighting.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
MASTER_INDEX = {"sp21a": 3, "sp27a": 4, "sp109": 3}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_candidate(row: dict) -> np.ndarray:
    path = REVIEW / row["artifact"]
    if digest(path) != row["artifact_sha256"]:
        raise ValueError(f"Changed input candidate: {path}")
    with Image.open(path) as image:
        return np.asarray(image.convert("RGBA")).copy()


def locked_boot(master: np.ndarray, moving: np.ndarray) -> np.ndarray:
    """Keep the boot and wing joints fixed; let upper feathers and stars change."""
    result = moving.copy()
    result[68:] = master[68:]
    result[55:68, 43:101] = master[55:68, 43:101]
    return result


def pulse(master: np.ndarray, family: str, frame_index: int, count: int) -> np.ndarray:
    """Animate light on a fixed silhouette without moving any drawn object."""
    result = master.copy()
    y, x = np.indices(master.shape[:2])
    rgb = master[:, :, :3].astype(np.float32)
    alpha = master[:, :, 3]
    phase = 2 * np.pi * frame_index / count
    red, green, blue = [rgb[:, :, channel] for channel in range(3)]
    if family == "sp27a":
        # The walker remains pixel-identical. A light sweep crosses the water,
        # while the small isolated stars twinkle in their original positions.
        water = (alpha > 0) & (y >= 83) & (blue > red * 1.18)
        sweep_x = 64 + 23 * np.sin(phase)
        sweep = np.exp(-((x - sweep_x) / 17) ** 2) * np.exp(-((y - 102) / 27) ** 2)
        result[:, :, 0][water] = np.clip(red[water] * (0.94 + 0.23 * sweep[water]), 0, 255)
        result[:, :, 1][water] = np.clip(green[water] * (0.94 + 0.27 * sweep[water]), 0, 255)
        result[:, :, 2][water] = np.clip(blue[water] * (0.96 + 0.19 * sweep[water]), 0, 255)
        star = (alpha > 0) & (y < 83) & ((x < 36) | (x >= 94)) & (blue > red * 1.08)
        twinkle = 0.90 + 0.16 * np.sin(phase + x * 0.11)
        for channel in range(3):
            result[:, :, channel][star] = np.clip(rgb[:, :, channel][star] * twinkle[star], 0, 255)
    else:
        # The entire hooded figure is identical in every frame. Only the cloud's
        # light travels across its fixed outline and alpha channel.
        cloud = (alpha > 0) & (y >= 92)
        sweep_x = 64 + 18 * np.sin(phase)
        sweep = np.exp(-((x - sweep_x) / 23) ** 2)
        factor = 0.91 + 0.17 * sweep + 0.035 * np.cos(phase)
        for channel in range(3):
            result[:, :, channel][cloud] = np.clip(rgb[:, :, channel][cloud] * factor[cloud], 0, 255)
    return result


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    base = json.loads((HERE / "report.json").read_text())["items"]
    previous = json.loads((HERE / "stabilization_report.json").read_text())["items"]
    output_dir = HERE / "locked"
    output_dir.mkdir(exist_ok=True)
    result = {"schema": 1, "kind": "stationary_idle_pc_effect_core_candidates", "families": {}, "items": {}}
    for family, master_index in MASTER_INDEX.items():
        frames = jobs[family]["frames"]
        inputs = [previous.get(frame["id"], base[frame["id"]]) for frame in frames]
        pixels = [load_candidate(row) for row in inputs]
        if len({image.shape for image in pixels}) != 1 or pixels[0].shape != (128, 128, 4):
            raise ValueError(f"Inconsistent 2x canvases in {family}")
        master = pixels[master_index]
        master_id = frames[master_index]["id"]
        family_rows = []
        for index, (frame, before) in enumerate(zip(frames, pixels)):
            updated = locked_boot(master, before) if family == "sp21a" else pulse(master, family, index, len(frames))
            if not np.any(updated[:, :, 3] > 0):
                raise ValueError(f"Empty idle animation frame: {frame['id']}")
            artifact = output_dir / f"{frame['id']}.png"
            Image.fromarray(updated, "RGBA").save(artifact, optimize=True)
            row = {"id": frame["id"], "sequence": family, "frame_index": index + 1,
                   "source_sha256": base[frame["id"]]["source_sha256"],
                   "input_sha256": inputs[index]["artifact_sha256"],
                   "master_id": master_id, "master_sha256": inputs[master_index]["artifact_sha256"],
                   "status": "candidate_technical", "artifact": artifact.relative_to(REVIEW).as_posix(),
                   "artifact_sha256": digest(artifact), "origin": "Imagegen restoration",
                   "method": "stationary core with in-place wing or lighting animation"}
            result["items"][frame["id"]] = row
            family_rows.append(row)
        result["families"][family] = family_rows
    (HERE / "idle_core_report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"families": len(result["families"]), "frames": len(result["items"]),
                      "masters": {name: rows[0]["master_id"] for name, rows in result["families"].items()}},
                     indent=2))


if __name__ == "__main__":
    main()
