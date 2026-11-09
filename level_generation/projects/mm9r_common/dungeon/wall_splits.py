"""
Faces that run on under walls into other rooms, cut at those walls (Thjorgard City's split_at_walls with Thronheim
City's floor rule, as Guberland City carries it; shared since 2026-11-07 for Verhoffin Ruins). MM9 lays one floor on
under a room's walls into the next room, which the face assignment keeps whole when the two rooms share no portal
(split_minor_rooms cuts only at portal planes), and the engine finds a party's sector by the floor under it: standing
in the second room, the party was put in the first and the view drew black (Verhoffin's water-trap room on the hall's
floor). The city converters keep their own copies for now.
"""

from __future__ import annotations

import numpy as np

from .geometry import clip

FLOOR_SPLIT_AREA = 4000             # LT²: floors and ceilings this big are cut at the walls standing on or under them
WALL_SPLIT_AREA = 4000              # LT²: walls this big are cut at the partitions whose ends meet them
PARTITION_HEIGHT = 48               # LT: walls at least this tall (not beams, kerbs or sills)
WALL_FOOT_LT = 16                   # LT: a wall stands on a floor when its foot is at most this far over it (Thronheim)


def split_at_walls(polygons: list, kinds: tuple = ("floor", "ceiling", "slope", "wall"),
                   min_area: float | None = None, select=None) -> tuple[list, int]:
    """Cut the faces that run on under walls into other rooms (Thjorgard City's split_at_walls, with Thronheim City's
    floor rule). MM9 lays a street's floor on under the houses beside it, a house's long wall on behind its
    partitions and one sloped ceiling over a row of rooms; the shared converter splits a face only at portal planes or
    where a second room holds 15 % of its samples, so a strip of street floor in front of a facade goes to the room
    inside the house (the street draws the sky through it). Each big floor is cut at the plane of every wall standing
    on it (its foot at most 16 LT over the floor or below it, reaching 48 LT over it), each big ceiling at every wall
    under it (a sloped one at every partition with two corners on its plane), each big wall at every partition whose
    end meets it; a cut splits only the pieces the cutting wall reaches. Pieces under or behind the walls see no air
    and are dropped as before. kinds: the faces cut; min_area (LT²): only faces at least this big (by default
    FLOOR_SPLIT_AREA and WALL_SPLIT_AREA); select: a predicate on a face, only the faces it accepts are cut (Verhoffin
    Ruins cuts only the floor under its water-trap room)."""
    walls, wall_points = [], []
    for p in polygons:
        n = p.normal
        if p.role != "static" or abs(n[1]) > 0.01 or np.ptp(p.points[:, 1]) < PARTITION_HEIGHT:
            continue
        horizontal = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
        tangent = np.array([-horizontal[2], 0.0, horizontal[0]])
        along = p.points @ tangent
        walls.append((horizontal, float(horizontal @ p.points[0]), tangent, float(along.min()), float(along.max()),
                      float(p.points[:, 1].min()), float(p.points[:, 1].max())))
        wall_points.append(p.points)
    if not walls:
        return polygons, 0
    normals = np.array([w[0] for w in walls])
    distances = np.array([w[1] for w in walls])
    bottoms, tops = np.array([w[5] for w in walls]), np.array([w[6] for w in walls])
    ends = np.array([[w[3], w[4]] for w in walls])
    tangents = np.array([w[2] for w in walls])
    out, splits = [], 0
    for polygon in polygons:
        n = polygon.normal
        kind = ("floor" if n[1] > 0.99 else "ceiling" if n[1] < -0.99 else "wall" if abs(n[1]) < 0.01
                else "slope" if n[1] < -0.3 else None)
        threshold = min_area if min_area is not None else WALL_SPLIT_AREA if kind == "wall" else FLOOR_SPLIT_AREA
        if (polygon.role != "static" or kind not in kinds or polygon.area < threshold
                or (select is not None and not select(polygon))):
            out.append(polygon)
            continue
        points = polygon.points
        sides = points @ normals.T - distances                      # (points, walls)
        crossing = (sides.min(0) < -4) & (sides.max(0) > 4)
        if kind == "floor":
            height = float(points[0, 1])
            touching = (bottoms <= height + WALL_FOOT_LT) & (tops >= height + PARTITION_HEIGHT)
        elif kind == "ceiling":
            touching = np.abs(tops - points[0, 1]) < 1.5
        elif kind == "slope":
            # a sloped ceiling (a roof's underside over several rooms): the partitions whose top corners lie on its
            # plane (the tavern's side rooms under one lean-to ceiling)
            unit = n / np.linalg.norm(n)
            plane = float(unit @ points[0])
            touching = np.zeros(len(walls), bool)
            for k in np.flatnonzero(crossing):
                touching[k] = bool((np.abs(wall_points[k] @ unit - plane) < 1.5).sum() >= 2)
        else:
            plane_normal, plane = n / np.linalg.norm(n), float(n @ points[0] / np.linalg.norm(n))
            low, high = points[:, 1].min(), points[:, 1].max()
            touching = np.zeros(len(walls), bool)
            candidates = np.flatnonzero(crossing & (np.abs(normals @ plane_normal) < 0.99)
                                        & (bottoms < high - 4) & (tops > low + 4))
            for k in candidates:
                origin = normals[k] * distances[k]
                for end in ends[k]:
                    if abs((origin + tangents[k] * end) @ plane_normal - plane) < 1.5:
                        touching[k] = True
        pieces = [polygon]
        for k in np.flatnonzero(crossing & touching):
            normal, distance, tangent, start, end = walls[k][:5]
            key = f"cw{np.round(normal, 3).tolist()}{round(distance, 1)}"
            cut = []
            for piece in pieces:
                if kind == "wall":
                    reach_low, reach_high = piece.points[:, 1].min(), piece.points[:, 1].max()
                    reached = bottoms[k] < reach_high - 4 and tops[k] > reach_low + 4
                else:
                    along = piece.points @ tangent
                    reached = start < along.max() - 4 and end > along.min() + 4
                if reached:
                    front, back = clip(piece, normal, distance, key)
                    cut += [part for part in (front, back) if part is not None]
                else:
                    cut.append(piece)
            pieces = cut
        splits += len(pieces) - 1
        out += pieces
    return out, splits
