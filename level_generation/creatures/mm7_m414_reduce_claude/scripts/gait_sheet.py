#!/usr/bin/env python3
"""Clay contact sheet of looping clips straight from a GLB (no Blender): rows = clip x view, columns = evenly spaced
phases of each clip, a floor line and a 10 cm grid, with the model's walking direction to the right in side views.

    gait_sheet.py <out.png> <glb>:<clip>[:label] ... [--views side,front,tq] [--phases 8] [--cell 220]

Painter's-order flat shading of the LOD0 triangles; good enough to judge posture, stride, lift and arm swing.
"""
import argparse
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "claude_shared" / "floor"))
import glb_pose  # noqa: E402

VIEWS = {
    # (right axis, up axis, toward-camera axis) in model space (+Y up, faces +Z)
    "side": (np.array([0.0, 0.0, 1.0]), np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0])),
    "front": (np.array([-1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])),
    "tq": (np.array([-0.7071, 0.0, 0.7071]), np.array([0.0, 1.0, 0.0]), np.array([0.7071, 0.0, 0.7071])),
}
LIGHT = np.array([0.4, 0.8, 0.45])


def render(posed, view, cell, height):
    right, up, toward = VIEWS[view]
    image = Image.new("RGB", (cell, cell), (205, 212, 220))
    draw = ImageDraw.Draw(image)
    scale = cell * 0.82 / height
    origin = np.array([cell / 2, cell * 0.92])

    def project(points):
        return np.stack([origin[0] + scale * (points @ right), origin[1] - scale * (points @ up)], axis=1)

    for metres in np.arange(-1.0, 1.01, 0.1):
        x = origin[0] + scale * metres
        draw.line([(x, origin[1]), (x, origin[1] + 6)], fill=(150, 150, 160))
    draw.line([(0, origin[1]), (cell, origin[1])], fill=(90, 90, 100), width=1)
    faces, depth, shade = [], [], []
    for points, triangles in posed:
        a, b, c = (points[triangles[:, k]] for k in range(3))
        normal = np.cross(b - a, c - a)
        length = np.linalg.norm(normal, axis=1)
        keep = length > 1e-10
        normal = normal[keep] / length[keep, None]
        tri = triangles[keep]
        facing = normal @ toward
        tri, normal = tri[facing > 0], normal[facing > 0]
        centre = points[tri].mean(axis=1)
        faces.append(project(points)[tri])
        depth.append(centre @ toward)
        light = np.clip(normal @ (LIGHT / np.linalg.norm(LIGHT)), 0, 1)
        shade.append(0.35 + 0.65 * light)
    faces, depth, shade = np.concatenate(faces), np.concatenate(depth), np.concatenate(shade)
    for index in np.argsort(depth):
        value = int(200 * shade[index])
        draw.polygon([tuple(p) for p in faces[index]], fill=(value, int(value * 0.93), int(value * 0.85)))
    draw.line([(0, origin[1]), (cell, origin[1])], fill=(60, 60, 70), width=1)
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("clips", nargs="+")
    parser.add_argument("--views", default="side,front")
    parser.add_argument("--phases", type=int, default=8)
    parser.add_argument("--cell", type=int, default=220)
    args = parser.parse_args()
    models = {}
    rows = []
    for spec in args.clips:
        parts = spec.split(":")
        path, clip = parts[0], parts[1]
        label = parts[2] if len(parts) > 2 else clip
        model = models.setdefault(path, glb_pose.Model(glb_pose.Glb(path)))
        length = model.clip_times(clip)[-1]
        posed_frames = [model.skinned_positions(model.world(model.sample(clip, length * k / args.phases)))
                        for k in range(args.phases)]
        rest = model.skinned_positions(model.world({}))
        height = max(float(np.concatenate([p for p, _ in rest])[:, 1].max()), 1e-3)
        for view in args.views.split(","):
            rows.append((f"{label} {view} ({length:.2f} s)", [render(posed, view, args.cell, height)
                                                              for posed in posed_frames]))
    label_width = 150
    sheet = Image.new("RGB", (label_width + args.cell * args.phases, args.cell * len(rows)), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for row, (label, images) in enumerate(rows):
        draw.text((6, row * args.cell + args.cell // 2), label, fill=(0, 0, 0))
        for column, image in enumerate(images):
            sheet.paste(image, (label_width + column * args.cell, row * args.cell))
    sheet.save(args.out)
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
