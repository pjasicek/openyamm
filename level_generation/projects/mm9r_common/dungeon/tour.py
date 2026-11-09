"""
Review tours: eye-level screenshot views given in MM9 (LithTech) coordinates, converted with the map's frame, the
party's feet on the floor below the view point (the game adds the eye height). The same views run on the new BLV
and, with --original, on the old bmodel_world map (same frame, against output/mm9_rework/assets_original).

    tour.write(project, views, "v01")            -> <project>/review_tour_v01.yml (shots in review/v01/)
    tour.write(project, views, "v01", True)      -> review_tour_v01_original.yml (review/v01_original/)

views: {name: (eye x, eye z, target x, target z[, eye y for the floor query[, pitch degrees]])}.
"""

from __future__ import annotations

import math

import yaml

from .source import Source, classify_models, floor_below


def write(project, views: dict, name: str, original: bool = False, settle: float = 1.5) -> dict:
    tour_name = name + ("_original" if original else "")
    source = Source(project)
    plan = classify_models(source)
    polygons = [p for model in plan["static"] for p in source.polygons(model)]
    shots = []
    for label, view in views.items():
        ex, ez, tx, tz = view[:4]
        query = view[4] if len(view) > 4 and view[4] is not None else 10000
        pitch = math.radians(view[5]) if len(view) > 5 else 0.0
        floor = floor_below(polygons, (ex, query, ez))
        if floor is None:
            raise SystemExit(f"view {label}: no floor under ({ex}, {ez})")
        eye = project.native([ex, floor, ez])
        target = project.native([tx, floor, tz])
        shots.append({"name": label, "position": [round(eye[0]), round(eye[1]), round(eye[2]) + 1],
                      "yaw": round(math.atan2(target[1] - eye[1], target[0] - eye[0]), 4), "pitch": round(pitch, 4)})
    output = project.directory / "review" / tour_name
    tour = {"output_dir": str(output), "settle_seconds": settle, "exit": True, "shots": shots}
    path = project.directory / f"review_tour_{tour_name}.yml"
    path.write_text(yaml.safe_dump(tour, sort_keys=False))
    first = shots[0]
    print(path)
    print("start:", *first["position"], "yaw", first["yaw"])
    return tour
