"""
Frosgard City's wall splits: Thjorgard City's map-local `split_at_walls` (../mm9r_thjorgardcity/convert.py, itself
Klusos House's route for any wall direction), copied here so the projects stay independent. A street floor MM9 lays
on under the houses and a long wall behind partitions are cut where walls stand on them, so each piece goes to the
room in front of it (no sky drawn through a floor strip that went to a house).
"""

from __future__ import annotations

import numpy as np

from dungeon.geometry import clip

# Faces that run on under walls into other rooms (split_at_walls below)
FLOOR_SPLIT_AREA = 4000             # LT²: floors and ceilings this big are cut at the walls standing on or under them
WALL_SPLIT_AREA = 4000              # LT²: walls this big are cut at the partitions whose ends meet them
PARTITION_HEIGHT = 48               # LT: walls at least this tall (not beams, kerbs or sills)


def split_at_walls(polygons: list) -> tuple[list, int]:
    """Cut the faces that run on under walls into other rooms (Klusos House's split_at_walls, for any wall direction).
    MM9 lays a street's floor on under the houses beside it and a house's long wall on behind its partitions; the
    shared converter splits a face only at portal planes or where a second room holds 15 % of its samples, so a strip
    of street floor in front of a facade went to the room inside the house (the street drew the sky through it) and a
    tavern wall behind a storeroom, a corridor and a kitchen went to the storeroom (the corridor drew the sky). Each big
    floor is cut at the plane of every wall standing on it, each big ceiling at every wall under it, each big wall at
    every partition whose end meets it; a cut splits only the pieces the cutting wall reaches. Pieces under or behind
    the walls see no air and are dropped as before."""
    walls = []
    for p in polygons:
        n = p.normal
        if p.role != "static" or abs(n[1]) > 0.01 or np.ptp(p.points[:, 1]) < PARTITION_HEIGHT:
            continue
        horizontal = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
        tangent = np.array([-horizontal[2], 0.0, horizontal[0]])
        along = p.points @ tangent
        walls.append((horizontal, float(horizontal @ p.points[0]), tangent, float(along.min()), float(along.max()),
                      float(p.points[:, 1].min()), float(p.points[:, 1].max())))
    if not walls:
        return polygons, 0
    normals = np.array([w[0] for w in walls])
    distances = np.array([w[1] for w in walls])
    bottoms, tops = np.array([w[5] for w in walls]), np.array([w[6] for w in walls])
    out, splits = [], 0
    for polygon in polygons:
        n = polygon.normal
        kind = "floor" if n[1] > 0.99 else "ceiling" if n[1] < -0.99 else "wall" if abs(n[1]) < 0.01 else None
        if polygon.role != "static" or kind is None or polygon.area < (
                WALL_SPLIT_AREA if kind == "wall" else FLOOR_SPLIT_AREA):
            out.append(polygon)
            continue
        points = polygon.points
        sides = points @ normals.T - distances                      # (points, walls)
        crossing = (sides.min(0) < -4) & (sides.max(0) > 4)
        if kind == "floor":
            touching = np.abs(bottoms - points[0, 1]) < 1.5
        elif kind == "ceiling":
            touching = np.abs(tops - points[0, 1]) < 1.5
        else:
            plane_normal, plane = n / np.linalg.norm(n), float(n @ points[0] / np.linalg.norm(n))
            ends = np.array([[w[3], w[4]] for w in walls])            # the partition's ends along its tangent
            tangents = np.array([w[2] for w in walls])
            # a partition meets this wall when one of its ends lies on the wall's plane
            low, high = points[:, 1].min(), points[:, 1].max()
            touching = np.zeros(len(walls), bool)
            candidates = np.flatnonzero(crossing & (np.abs(normals @ plane_normal) < 0.99)
                                        & (bottoms < high - 4) & (tops > low + 4))
            for k in candidates:
                # the partition's end points: its plane point moved along its tangent to each end
                origin = normals[k] * distances[k]
                for end in ends[k]:
                    point = origin + tangents[k] * end
                    # the end's horizontal distance to this wall's plane (y does not matter: both are vertical)
                    if abs(point @ plane_normal - plane) < 1.5:
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
