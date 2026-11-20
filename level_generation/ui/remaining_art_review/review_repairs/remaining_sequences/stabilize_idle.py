#!/usr/bin/env python3
"""Pin three idle HUD animations without changing their animated details."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
FAMILIES = ("sp21a", "sp27a", "sp109")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def translated(pixels: np.ndarray, dx: int, dy: int) -> np.ndarray:
    result = np.zeros_like(pixels)
    height, width = pixels.shape[:2]
    source_x0 = max(0, -dx)
    source_x1 = min(width, width - dx)
    source_y0 = max(0, -dy)
    source_y1 = min(height, height - dy)
    if source_x0 < source_x1 and source_y0 < source_y1:
        result[source_y0 + dy:source_y1 + dy, source_x0 + dx:source_x1 + dx] = \
            pixels[source_y0:source_y1, source_x0:source_x1]
    return result


def largest_component(mask: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(mask)
    if count == 0:
        raise ValueError("Idle-effect anchor has no connected component")
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    return labels == int(np.argmax(areas))


def boot_anchor(pixels: np.ndarray) -> tuple[float, float]:
    red, green, blue, alpha = [pixels[:, :, index].astype(float) for index in range(4)]
    y, _ = np.indices(alpha.shape)
    brown = (alpha > 96) & (y >= 50) & (y < 116) & (red > 55) \
        & (red > green * 1.15) & (green > blue * 1.1)
    component = largest_component(brown)
    yy, xx = np.nonzero(component)
    if len(xx) < 1000:
        raise ValueError("Could not isolate the winged boot")
    return float(xx.mean()), float(yy.mean())


def feature(pixels: np.ndarray, family: str) -> np.ndarray:
    rgba = pixels.astype(float) / 255.0
    red, green, blue, alpha = [rgba[:, :, index] for index in range(4)]
    y, x = np.indices(alpha.shape)
    if family == "sp27a":
        brightness = (red + green + blue) / 3 * alpha
        region = (x >= 44) & (x <= 86) & (y >= 17) & (y <= 91)
    else:
        brightness = (0.15 * red + 0.25 * green + 0.6 * blue) * alpha
        region = (x >= 19) & (x <= 108) & (y >= 15) & (y <= 94)
    return np.hypot(ndimage.sobel(brightness, 0), ndimage.sobel(brightness, 1)) * region


def register(reference: np.ndarray, moving: np.ndarray, family: str) -> tuple[int, int, float]:
    fixed = feature(reference, family)
    shifted = feature(moving, family)
    fixed_norm = np.linalg.norm(fixed)
    moving_norm = np.linalg.norm(shifted)
    if fixed_norm == 0 or moving_norm == 0:
        raise ValueError(f"Empty registration feature: {family}")
    matches = []
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            image = translated(shifted, dx, dy)
            score = float(np.sum(fixed * image) / (fixed_norm * moving_norm))
            matches.append((score, -abs(dx) - abs(dy), dx, dy))
    score, _, dx, dy = max(matches)
    if score < 0.58:
        raise ValueError(f"Uncertain idle-effect registration: {family}: {score:.3f}")
    return dx, dy, round(score, 4)


def person_mask(pixels: np.ndarray) -> np.ndarray:
    red, green, blue, alpha = [pixels[:, :, index].astype(float) for index in range(4)]
    y, x = np.indices(alpha.shape)
    neutral = (alpha > 24) & (x >= 39) & (x <= 93) & (y >= 11) & (y <= 85) \
        & ((blue - red < 26) | (blue - green < 23) | (red > green * 1.12))
    connected = largest_component(ndimage.binary_closing(neutral, iterations=1))
    if int(connected.sum()) < 1000:
        raise ValueError("Could not isolate the walking figure")
    expanded = ndimage.binary_dilation(connected, iterations=5)
    upper = (alpha > 0) & (x >= 30) & (x <= 100) & (y < 58)
    return (expanded | upper) & (alpha > 0)


def move_person(pixels: np.ndarray, dx: int, dy: int) -> np.ndarray:
    if not dx and not dy:
        return pixels.copy()
    mask = person_mask(pixels)
    layer = pixels.copy()
    layer[~mask] = 0
    background = pixels.copy()
    nearest = ndimage.distance_transform_edt(mask, return_distances=False, return_indices=True)
    lower = mask.copy()
    lower[:45] = False
    background[lower] = pixels[nearest[0][lower], nearest[1][lower]]
    background[mask & ~lower] = 0
    base = Image.fromarray(background, "RGBA")
    over = Image.fromarray(translated(layer, dx, dy), "RGBA")
    return np.asarray(Image.alpha_composite(base, over)).copy()


def cloud_anchor(pixels: np.ndarray) -> float:
    red, green, blue, alpha = [pixels[:, :, index].astype(float) for index in range(4)]
    y, _ = np.indices(alpha.shape)
    white = (alpha > 64) & (y >= 98) & (red > 90) & (green > 90) & (blue > 90)
    component = largest_component(white)
    _, xx = np.nonzero(component)
    if len(xx) < 1000:
        raise ValueError("Could not isolate the spell cloud")
    return float(xx.mean())


def move_robe_and_cloud(pixels: np.ndarray, body_shift: tuple[int, int], cloud_dx: int) -> np.ndarray:
    body = pixels.copy()
    body[92:] = 0
    cloud = pixels.copy()
    cloud[:92] = 0
    base = Image.fromarray(translated(cloud, cloud_dx, 0), "RGBA")
    over = Image.fromarray(translated(body, *body_shift), "RGBA")
    return np.asarray(Image.alpha_composite(base, over)).copy()


def check_no_cutoff(original: np.ndarray, updated: np.ndarray, family: str, name: str) -> None:
    if updated.shape != original.shape or not np.any(updated[:, :, 3] >= 32):
        raise ValueError(f"Empty or resized stabilized frame: {name}")
    if family == "sp21a":
        if np.any(original[:, :2, 3] > 32) or np.any(original[:, -2:, 3] > 32):
            raise ValueError(f"Winged boot frame is already clipped: {name}")
    if family == "sp109":
        if np.any(updated[0, :, 3] > 32) or np.any(updated[-1, :, 3] > 32):
            raise ValueError(f"Stabilized robe or cloud hit a canvas edge: {name}")


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    source_rows = json.loads((HERE / "report.json").read_text())["items"]
    output_dir = HERE / "stabilized"
    output_dir.mkdir(exist_ok=True)
    changed = {}
    families = {}
    for family in FAMILIES:
        frames = jobs[family]["frames"]
        inputs = []
        for frame in frames:
            source = source_rows[frame["id"]]
            path = REVIEW / source["artifact"]
            if digest(path) != source["artifact_sha256"]:
                raise ValueError(f"Changed whole-sequence candidate: {frame['id']}")
            with Image.open(path) as image:
                inputs.append(np.asarray(image.convert("RGBA")).copy())
        if len({image.shape for image in inputs}) != 1:
            raise ValueError(f"Mixed canvas sizes in {family}")
        if family == "sp21a":
            anchors = [boot_anchor(image) for image in inputs]
            target = [float(np.median([anchor[axis] for anchor in anchors])) for axis in range(2)]
        elif family == "sp27a":
            preliminary = [register(inputs[3], image, family) for image in inputs]
            first_pass = [move_person(image, shift[0], shift[1]) for image, shift in zip(inputs, preliminary)]
            residual = [register(first_pass[3], image, family) for image in first_pass]
        elif family == "sp109":
            cloud_centers = [cloud_anchor(image) for image in inputs]
            cloud_target = float(np.median(cloud_centers))
            body_tops = [int(np.nonzero(image[:92, :, 3] >= 32)[0].min()) for image in inputs]
            body_y_offset = int(round(float(np.median(body_tops)))) - body_tops[3]
        reference = inputs[3]
        family_rows = []
        for index, (frame, pixels) in enumerate(zip(frames, inputs)):
            if family == "sp21a":
                dx = int(round(target[0] - anchors[index][0]))
                dy = int(round(target[1] - anchors[index][1]))
                if max(abs(dx), abs(dy)) > 2:
                    raise ValueError(f"Unexpected boot displacement: {frame['id']}: {(dx, dy)}")
                updated = translated(pixels, dx, dy)
                placement = {"whole_frame": [dx, dy], "anchor": [round(value, 3) for value in anchors[index]]}
            elif family == "sp27a":
                initial_dx, initial_dy, score = preliminary[index]
                correction_dx, correction_dy, _ = residual[index]
                if max(abs(correction_dx), abs(correction_dy)) > 1:
                    raise ValueError(f"Walking-figure registration did not settle: {frame['id']}")
                dx, dy = initial_dx + correction_dx, initial_dy + correction_dy
                if max(abs(dx), abs(dy)) > 3:
                    raise ValueError(f"Unexpected walking-figure displacement: {frame['id']}: {(dx, dy)}")
                updated = move_person(pixels, dx, dy)
                placement = {"person": [dx, dy], "registration_score": score,
                             "residual_correction": [correction_dx, correction_dy]}
            else:
                dx, dy, score = register(reference, pixels, family)
                dy += body_y_offset
                if max(abs(dx), abs(dy)) > 6:
                    raise ValueError(f"Unexpected robe displacement: {frame['id']}: {(dx, dy)}")
                cloud_dx = int(round(cloud_target - cloud_centers[index]))
                if abs(cloud_dx) > 2:
                    raise ValueError(f"Unexpected cloud displacement: {frame['id']}: {cloud_dx}")
                updated = move_robe_and_cloud(pixels, (dx, dy), cloud_dx)
                placement = {"robe": [dx, dy], "cloud": [cloud_dx, 0],
                             "registration_score": score}
            check_no_cutoff(pixels, updated, family, frame["name"])
            row = {"id": frame["id"], "sequence": family, "frame_index": index + 1,
                   "source_sha256": source_rows[frame["id"]]["source_sha256"],
                   "input_sha256": source_rows[frame["id"]]["artifact_sha256"],
                   "placement": placement, "changed": not np.array_equal(updated, pixels)}
            if row["changed"]:
                artifact = output_dir / f"{frame['id']}.png"
                Image.fromarray(updated, "RGBA").save(artifact, optimize=True)
                row.update({"status": "candidate_technical", "artifact": artifact.relative_to(REVIEW).as_posix(),
                            "artifact_sha256": digest(artifact), "origin": "Imagegen restoration",
                            "method": "idle-animation anchor stabilization from whole-sequence imagegen art"})
                changed[frame["id"]] = row
            family_rows.append(row)
        families[family] = family_rows
    result = {"schema": 1, "kind": "stationary_idle_pc_effect_candidates", "families": families,
              "items": changed}
    (HERE / "stabilization_report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"sequences": len(families), "frames": sum(map(len, families.values())),
                      "changed": len(changed), "placements": {family: [row["placement"] for row in rows]
                                                      for family, rows in families.items()}}, indent=2))


if __name__ == "__main__":
    main()
