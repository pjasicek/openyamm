"""
City structure: the sectors of an MM9 city's open air (../CITY_PLAYBOOK.md).

An MM9 city is walled districts under a sky lid. The dungeon converter (../dungeon) makes each walk-in house a room
behind its door and window portals, and each district's open air one huge room (its streets, plazas and the air over
the roofs, joined over the rooftops). This module divides that open air, as `Hooks.extra_portals` portals with their
barrier voxels:

1. **The roof line.** A horizontal barrier at `street_top_lt` (LithTech y, just under the lowest eaves along the
   streets) separates each district's street air below it from the air over the roofs above it. The air over the
   roofs stays one room per district (the roofs, the upper walls, the sky faces). A straight line of sight from one
   street to another never passes through the roof room (it would have to cross the barrier's plane twice), so
   streets see each other only through the street cuts below.
2. **Street cuts.** Vertical cuts across the streets below the roof line, found automatically: on lines every
   `cut_spacing_lt` along x and along z (each moved up to `cut_search_lt` to the narrowest place), a cut where the
   street is a plain corridor there (walls straight for `corridor_lt` on both sides) and at most `max_cut_width_lt`
   wide. Plazas and junctions are never cut. A cut is the street's cross-section from the ground to the roof line;
   a cut whose two sides stay one room (a loop cut once) is dropped.
3. **Top portals.** Each street room's footprint at the roof line, as rectangles (greedy, largest first): the
   portals from a street up into its district's roof room. With `merged_top_portals: true` (opt-in, 2026-11-01) the
   rectangles are merged into few convex polygons, run on over walls and roofs (`merge_cover`, below): Thjorgard
   City's 1 373 rectangles (staircases along its diagonal streets) become about 140 portals.

Settings (overrides.yml `city`): street_top_lt, district_min_voxels (rooms at least this big are districts,
default 300 000), cut_spacing_lt (1280), cut_search_lt (320), corridor_lt (128), max_cut_width_lt (768),
min_cut_width_lt (48), street_box_lt ([[x0, z0], [x1, z1]] LT: the roof line and the streets only in this plan
box; default everywhere), extra_cuts ([{axis: x|z, point: [x, y, z] LT}], cut by hand like archway cuts, below the roof
line), no_cuts ([[x, z] LT points: no automatic cut within 256 of them]), merged_top_portals (false: the top
portals as merged convex polygons, `merged_top_portals`), top_portal_extension (0.5: how much a merge may add over
cells the street does not open, as a share of the merged pieces' own area).
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from scipy import ndimage

import heapq

from dungeon.geometry import SIX, rectangle_points, sample_polygon
from dungeon.rooms import label_rooms, portal_sides

DEFAULTS = {"district_min_voxels": 300_000, "cut_spacing_lt": 1280, "cut_search_lt": 320, "corridor_lt": 128,
            "max_cut_width_lt": 768, "min_cut_width_lt": 48, "extra_cuts": [], "no_cuts": [],
            "merged_top_portals": False, "top_portal_extension": 0.5}


def settings_of(project) -> dict:
    return dict(DEFAULTS, **(project.overrides.get("city") or {}))


def runs(line: np.ndarray) -> list[tuple[int, int]]:
    """The runs of True in a 1D mask: [(start, end)] inclusive."""
    padded = np.concatenate([[False], line, [False]])
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    return [(int(a), int(b) - 1) for a, b in zip(edges[::2], edges[1::2])]


def corridor_like(mask: np.ndarray, axis: int, c: int, run: tuple[int, int], k: int) -> bool:
    """Whether the street crossing line c (along `axis` of the 2D mask) as `run` has straight walls for k cells on
    both sides: every line within k has a run with the same ends (within one cell)."""
    a, b = run
    for dc in range(-k, k + 1):
        cc = c + dc
        if cc < 0 or cc >= mask.shape[axis]:
            return False
        line = mask[cc, :] if axis == 0 else mask[:, cc]
        found = [r for r in runs(line) if r[0] <= (a + b) // 2 <= r[1]]
        if not found or abs(found[0][0] - a) > 1 or abs(found[0][1] - b) > 1:
            return False
    return True


def find_cuts(mask: np.ndarray, grid, settings: dict) -> list[dict]:
    """Automatic street cuts on one district's 2D street mask (x, z cells): [{axis, c, run}] (axis 0: a plane of
    constant x, the run along z; axis 2: constant z, the run along x)."""
    size = grid.size
    spacing = settings["cut_spacing_lt"] / size
    search = int(round(settings["cut_search_lt"] / size))
    k = int(round(settings["corridor_lt"] / size))
    widest = settings["max_cut_width_lt"] / size
    narrowest = settings["min_cut_width_lt"] / size
    blocked = [np.asarray(p, float) for p in settings["no_cuts"]]
    cuts = []
    for axis2d, axis3d in ((0, 0), (1, 2)):
        extent = mask.shape[axis2d]
        origin = grid.origin[axis3d]
        first = int(np.ceil((origin / size) / spacing))
        for n in range(first, int((origin / size + extent) / spacing) + 1):
            c0 = int(round(n * spacing - origin / size))
            if not 0 <= c0 < extent:
                continue
            line0 = mask[c0, :] if axis2d == 0 else mask[:, c0]
            for run0 in runs(line0):
                best = None
                for c in range(max(0, c0 - search), min(extent, c0 + search + 1)):
                    line = mask[c, :] if axis2d == 0 else mask[:, c]
                    for run in runs(line):
                        if run[1] < run0[0] or run[0] > run0[1]:
                            continue
                        width = run[1] - run[0] + 1
                        if not narrowest <= width <= widest or not corridor_like(mask, axis2d, c, run, k):
                            continue
                        if best is None or (width, abs(c - c0)) < (best[0], abs(best[1] - c0)):
                            best = (width, c, run)
                if best is None:
                    continue
                _, c, run = best
                middle = (run[0] + run[1]) / 2
                plan = np.array([c, middle] if axis2d == 0 else [middle, c], float)
                plan_lt = grid.origin[[0, 2]] + (plan + 0.5) * size
                if any(np.abs(plan_lt - p).max() < 256 for p in blocked):
                    continue
                key = (axis3d, c, run)
                if all((cut["axis"], cut["c"], cut["run"]) != key for cut in cuts):
                    cuts.append({"axis": axis3d, "c": c, "run": run, "plan_lt": plan_lt.round().tolist()})
    return cuts


def cut_portal(grid, lower: np.ndarray, cut: dict, name: str) -> dict | None:
    """The portal of a street cut: the street air (below the roof line) in the cut's plane, connected to the run's
    middle within the run (one cell of slack each way), as a rectangle with its barrier cells."""
    axis = cut["axis"]
    other = 2 if axis == 0 else 0
    plane = np.take(lower, cut["c"], axis=axis)             # (x or z, y) over the two other axes, in order
    # np.take keeps the remaining axes in order: for axis 0 -> (y, z); for axis 2 -> (x, y)
    if axis == 0:
        plane = plane.T                                     # -> (z, y)
    a, b = cut["run"]
    window = np.zeros_like(plane)
    window[max(0, a - 1):b + 2, :] = True
    labelled, _ = ndimage.label(plane & window)
    middle = (a + b) // 2
    column = labelled[middle]
    ids = [v for v in np.unique(column) if v]
    if not ids:
        return None
    component = np.isin(labelled, ids)
    cells2 = np.argwhere(component)                         # (along, y)
    cells = np.zeros((len(cells2), 3), np.int64)
    cells[:, axis] = cut["c"]
    cells[:, other] = cells2[:, 0]
    cells[:, 1] = cells2[:, 1]
    low = np.array([cells2[:, 0].min(), cells2[:, 1].min()], float)
    high = np.array([cells2[:, 0].max() + 1, cells2[:, 1].max() + 1], float)
    centre = np.zeros(3)
    centre[axis] = grid.origin[axis] + (cut["c"] + 0.5) * grid.size
    centre[other] = grid.origin[other] + (low[0] + high[0]) / 2 * grid.size
    centre[1] = grid.origin[1] + (low[1] + high[1]) / 2 * grid.size
    normal = np.zeros(3); normal[axis] = 1.0
    axis_a = np.zeros(3); axis_a[other] = 1.0
    return {"name": name, "kind": "street_cut", "centre": centre, "normal": normal, "axis_a": axis_a,
            "half_a": (high[0] - low[0]) / 2 * grid.size, "axis_b": np.array([0.0, 1.0, 0.0]),
            "half_b": (high[1] - low[1]) / 2 * grid.size, "cells": cells, "plan_lt": cut.get("plan_lt")}


def grow_cut_faces(cuts: list[dict], grid, h: int) -> None:
    """A street cut's face covers its barrier's air voxels (16 LT each), but the walls, the floor and the roof line it
    runs between stand up to a voxel beyond them: through that strip the two rooms see each other with no portal, and
    whatever lies behind it is not drawn (Thjorgard City 2026-11-01: sky beside a house corner, street_24_1). The face
    is grown by one voxel at each end of its run that no other piece of the same cut continues, one voxel down into the
    floor and up to the roof line's plane (layer h + 0.5). A portal face running on into a solid is harmless: it only
    widens the aperture (as the merged top portals). The barrier cells do not change, so neither do the rooms."""
    size = grid.size
    roof = grid.origin[1] + (h + 0.5) * size
    planes = defaultdict(list)
    for cut in cuts:
        plane = int(np.argmax(np.abs(cut["normal"])))
        planes[(plane, round(float(cut["centre"][plane]), 3))].append(cut)
    for group in planes.values():
        spans = []
        for cut in group:
            along = int(np.argmax(np.abs(cut["axis_a"])))
            spans.append((cut["centre"][along] - cut["half_a"], cut["centre"][along] + cut["half_a"]))
        for index, cut in enumerate(group):
            along = int(np.argmax(np.abs(cut["axis_a"])))
            low, high = spans[index]
            others = [span for k, span in enumerate(spans) if k != index]
            if not any(abs(other[1] - low) < 1e-3 for other in others):
                low -= size
            if not any(abs(other[0] - high) < 1e-3 for other in others):
                high += size
            bottom = cut["centre"][1] - cut["half_b"] - size
            top = cut["centre"][1] + cut["half_b"]
            if roof - size <= top < roof:
                top = roof
            centre = cut["centre"].copy()
            centre[along] = (low + high) / 2
            centre[1] = (bottom + top) / 2
            cut.update(centre=centre, half_a=(high - low) / 2, half_b=(top - bottom) / 2)


def rectangles(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """A 2D mask as disjoint rectangles (x0, z0, x1, z1 inclusive), greedily largest first."""
    if not mask.any():
        return []
    cells = np.argwhere(mask)
    (bx, bz), (ex, ez) = cells.min(0), cells.max(0) + 1
    return [(x0 + bx, z0 + bz, x1 + bx, z1 + bz) for x0, z0, x1, z1 in _rectangles(mask[bx:ex, bz:ez])]


def _row_best(x: int, heights: np.ndarray) -> tuple:
    """The largest rectangle whose bottom row is x (histogram method): the first one found of the largest area."""
    best = (0, None)
    stack = []
    for z in range(len(heights) + 1):
        h = int(heights[z]) if z < len(heights) else 0
        start = z
        while stack and stack[-1][1] >= h:
            start, height = stack.pop()
            area = height * (z - start)
            if area > best[0]:
                best = (area, (x - height + 1, start, x, z - 1))
        stack.append((start, h))
    return best


def _rectangles(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Greedy cover, largest rectangle first, the first of equal ones in row order. Each row keeps its best rectangle;
    taking one out rescans only the rows whose histogram it changed (Thjorgard City's 45 masks: 74 s of a build when
    every row was rescanned for every rectangle)."""
    left = mask.copy()
    heights = np.zeros(left.shape, int)
    run = np.zeros(left.shape[1], int)
    for x in range(left.shape[0]):
        run = np.where(left[x], run + 1, 0)
        heights[x] = run
    rows = [_row_best(x, heights[x]) for x in range(left.shape[0])]
    found = []
    while left.any():
        best = (0, None)
        for row in rows:
            if row[0] > best[0]:
                best = row
        x0, z0, x1, z1 = best[1]
        found.append((x0, z0, x1, z1))
        left[x0:x1 + 1, z0:z1 + 1] = False
        run = heights[x0 - 1].copy() if x0 > 0 else np.zeros(left.shape[1], int)
        for x in range(x0, left.shape[0]):
            run = np.where(left[x], run + 1, 0)
            if x > x1 and np.array_equal(run, heights[x]):
                break       # the rows below count on from an unchanged row
            if not np.array_equal(run, heights[x]):
                heights[x] = run
                rows[x] = _row_best(x, run)
    return found


def split_by_sides(grid, labels: np.ndarray, portal: dict) -> list[dict]:
    """A street cut as one portal per run of the cut (along it) whose two sides are the same pair of rooms."""
    axis = 0 if portal["normal"][0] else 2
    other = 2 if axis == 0 else 0
    cells = portal["cells"]
    sides = []
    for sign in (2, -2):
        probe = cells.copy()
        probe[:, axis] = np.clip(probe[:, axis] + sign, 0, grid.shape[axis] - 1)
        sides.append(labels[probe[:, 0], probe[:, 1], probe[:, 2]])
    columns = {}
    for u in np.unique(cells[:, other]):
        mask = cells[:, other] == u
        pair = []
        for side in sides:
            values = [int(v) for v in side[mask] if v]
            pair.append(Counter(values).most_common(1)[0][0] if values else 0)
        columns[int(u)] = tuple(pair)
    runs_of = []
    for u in sorted(columns):
        if runs_of and runs_of[-1][1] == u - 1 and runs_of[-1][2] == columns[u]:
            runs_of[-1][1] = u
        else:
            runs_of.append([u, u, columns[u]])
    if len(runs_of) == 1:
        return [portal]
    parts = []
    for k, (u0, u1, pair) in enumerate(runs_of):
        part_cells = cells[(cells[:, other] >= u0) & (cells[:, other] <= u1)]
        if 0 in pair or pair[0] == pair[1]:
            # no portal for a stretch with air on one side only or one room on both: its cells stay a barrier of the
            # next part (they separate nothing), so the labels do not change
            if parts:
                parts[-1]["cells"] = np.concatenate([parts[-1]["cells"], part_cells])
            else:
                parts.append({"carry": part_cells})
            continue
        low = np.array([part_cells[:, other].min(), part_cells[:, 1].min()], float)
        high = np.array([part_cells[:, other].max() + 1, part_cells[:, 1].max() + 1], float)
        centre = portal["centre"].copy()
        centre[other] = grid.origin[other] + (low[0] + high[0]) / 2 * grid.size
        centre[1] = grid.origin[1] + (low[1] + high[1]) / 2 * grid.size
        piece = dict(portal, name=f"{portal['name']}_{k + 1}", centre=centre, cells=part_cells,
                     half_a=(high[0] - low[0]) / 2 * grid.size, half_b=(high[1] - low[1]) / 2 * grid.size)
        if parts and "carry" in parts[-1]:
            piece["cells"] = np.concatenate([parts.pop()["carry"], piece["cells"]])
        parts.append(piece)
    if parts and "carry" in parts[-1]:
        carry = parts.pop()["carry"]
        if parts:
            parts[-1]["cells"] = np.concatenate([parts[-1]["cells"], carry])
    return parts or [portal]


def city_portals(build) -> list[dict]:
    """The city's extra portals (module docstring): street cuts and top portals with their barrier cells. Also
    leaves `build.city_report` (districts, cuts kept and dropped, rooms, top portal rectangles)."""
    settings = settings_of(build.project)
    grid, air = build.grid, build.air
    size = grid.size
    labels, count = label_rooms(grid, air, build.portals)
    sizes = ndimage.sum(np.ones_like(labels), labels, range(count + 1))
    districts = [r for r in range(1, count + 1) if sizes[r] >= settings["district_min_voxels"]]
    h = int((float(settings["street_top_lt"]) - grid.origin[1]) // size)
    outdoor = np.isin(labels, districts)
    lower = outdoor.copy()
    lower[:, h:, :] = False
    # `street_box_lt` (opt-in): the roof line and the streets only inside this plan box; outside it (a hillside up
    # to a castle, Thjorgard City) the open air stays one room with the air over the roofs.
    inside = np.ones((grid.shape[0], grid.shape[2]), bool)
    if settings.get("street_box_lt"):
        (bx0, bz0), (bx1, bz1) = settings["street_box_lt"]
        xs = grid.origin[0] + (np.arange(grid.shape[0]) + 0.5) * size
        zs = grid.origin[2] + (np.arange(grid.shape[2]) + 0.5) * size
        inside = ((xs >= bx0) & (xs <= bx1))[:, None] & ((zs >= bz0) & (zs <= bz1))[None, :]
        lower &= inside[:, None, :]
    report = {"street_top_layer": h, "districts": [], "cuts": [], "dropped_cuts": []}
    candidates = []
    for district in districts:
        mask = lower[:, h - 1, :] & (labels[:, h - 1, :] == district)
        cuts = find_cuts(mask, grid, settings)
        report["districts"].append({"room": district, "voxels": int(sizes[district]), "auto_cuts": len(cuts)})
        part = lower & (labels == district)
        for k, cut in enumerate(cuts):
            portal = cut_portal(grid, part, cut, f"street_{district}_{k + 1}")
            if portal is not None:
                candidates.append(portal)
    for k, extra in enumerate(settings["extra_cuts"]):
        point = np.asarray(extra["point"], float)
        cell = grid.index(point[None])[0]
        axis = {"x": 0, "z": 2}[extra["axis"]]
        other = 2 if axis == 0 else 0
        line = np.take(lower[:, min(int(cell[1]), h - 1), :], cell[axis], axis=0 if axis == 0 else 1)
        run = next((r for r in runs(line) if r[0] <= cell[other] <= r[1]), None)
        if run is None:
            report["dropped_cuts"].append({"name": f"hand_{k + 1}", "reason": "no street air at the point"})
            continue
        portal = cut_portal(grid, lower, {"axis": axis, "c": int(cell[axis]), "run": run}, f"street_hand_{k + 1}")
        if portal is not None:
            portal["plan_lt"] = [float(point[0]), float(point[2])]
            candidates.append(portal)
    barrier = np.zeros(grid.shape, bool)
    barrier[:, h, :] = outdoor[:, h, :] & inside
    roof_line = {"name": "roof_line", "kind": "roof_line_barrier", "cells": np.argwhere(barrier)}
    # Drop cuts whose two sides stay one room, until every cut separates two rooms.
    kept = list(candidates)
    while True:
        labels2, _ = label_rooms(grid, air, build.portals + [roof_line] + kept)
        bad = [p for p in kept if len(set(portal_sides(grid, labels2, p))) < 2 or 0 in portal_sides(grid, labels2, p)]
        if not bad:
            break
        for p in bad:
            report["dropped_cuts"].append({"name": p["name"], "plan_lt": p.get("plan_lt"),
                                           "rooms": list(portal_sides(grid, labels2, p))})
        kept = [p for p in kept if p not in bad]
    # A cut that crosses other cuts (or a hand cut across a junction) joins more than one pair of rooms: split it into
    # runs of one pair each, or the rooms of the minor pairs would share a barrier with no portal face (a hole).
    kept = [part for portal in kept for part in split_by_sides(grid, labels2, portal)]
    grow_cut_faces(kept, grid, h)
    # Top portals: each street room's footprint at the roof line, as rectangles.
    tops = []
    below = labels2[:, h - 1, :]
    street_rooms = sorted(set(int(v) for v in np.unique(below[lower[:, h - 1, :]])) - {0})
    y_plane = grid.origin[1] + (h + 0.5) * size
    for room in street_rooms:
        footprint = (below == room) & outdoor[:, h, :] & inside
        for k, (x0, z0, x1, z1) in enumerate(rectangles(footprint)):
            cells2 = np.argwhere(footprint[x0:x1 + 1, z0:z1 + 1]) + [x0, z0]
            cells = np.stack([cells2[:, 0], np.full(len(cells2), h), cells2[:, 1]], axis=1)
            centre = np.array([grid.origin[0] + (x0 + x1 + 1) / 2 * size, y_plane,
                               grid.origin[2] + (z0 + z1 + 1) / 2 * size])
            tops.append({"name": f"roofline_{room}_{k + 1}", "kind": "roof_line", "centre": centre,
                         "normal": np.array([0.0, 1.0, 0.0]), "axis_a": np.array([1.0, 0.0, 0.0]),
                         "half_a": (x1 - x0 + 1) / 2 * size, "axis_b": np.array([0.0, 0.0, 1.0]),
                         "half_b": (z1 - z0 + 1) / 2 * size, "cells": cells})
    # A rectangle with no air over it (a covered strip whose ceiling sits on the roof line) joins nothing: it stays a
    # barrier (its cells go to a portal of the same room) but is no portal. Cells of the roof line over a roof top
    # (no street air under them) need no barrier: they touch only the air over the roofs.
    valid, blind = [], []
    for portal in tops:
        sides = portal_sides(grid, labels2, portal)
        (blind if 0 in sides or sides[0] == sides[1] else valid).append(portal)
    for portal in blind:
        room = portal["name"].split("_")[1]
        keeper = next((p for p in valid if p["name"].split("_")[1] == room), None)
        if keeper is not None:
            keeper["cells"] = np.concatenate([keeper["cells"], portal["cells"]])
    report["blind_top_rectangles"] = len(blind)
    tops = valid
    report["cuts"] = [{"name": p["name"], "plan_lt": p.get("plan_lt"), "width_lt": round(2 * p["half_a"]),
                       "height_lt": round(2 * p["half_b"])} for p in kept]
    report["street_rooms"] = len(street_rooms)
    report["top_rectangles"] = len(tops)
    report["top_rectangles_per_room"] = dict(Counter(int(p["name"].split("_")[1]) for p in tops))
    if settings["merged_top_portals"]:
        tops = merged_top_portals(build, labels2, outdoor, inside, h, street_rooms, tops, settings, report)
    build.city_report = report
    return kept + tops


# --- Merged top portals (`merged_top_portals: true`, 2026-11-01; devdocs/mm9_rework/CITY_STREET_COST.md proposal 3) --
#
# The rectangles above follow the footprint cell by cell: a 45-degree street becomes a staircase of thin rectangles
# (Thjorgard City 1 373, Thronheim 890), each a portal link of the roof room, and the renderer enters the roof room
# once per visible rectangle (the 256-node cap was hit at 3 of Thjorgard's 12 street poses). Here each street room's
# open footprint is covered by few convex polygons instead. What a top portal must be:
# - convex and planar: the renderer clips each portal against the view frustum and builds its frustum from the
#   polygon's edges, which is only right for a convex polygon (IndoorPortalVisibility.cpp);
# - over every open cell (a street cell with the roof room's air over the roof line): a piece missing there would
#   hide the roof room seen through it (a hole). It may run on over cells solid at the roof line: a wall, a roof, the
#   street's own eaves. A ray through such a part first passes the solid there, so it only makes the portal's frustum
#   a little wider (more drawn, nothing lost);
# - over nothing that is another room's at the roof line (layers h - 1 .. h + 2): another street, a house whose air
#   reaches the roof line. The compiler marks the roof room's sector "floor portals" (a horizontal portal stands for
#   a floor when a point looks for its sector, IndoorGeometryUtils.cpp findIndoorSectorForPoint), so a point in a
#   house just over a top portal that runs over it would be put in the roof room;
# - over a covered strip (a street cell whose ceiling sits within 1.5 voxels of the roof line: eaves, arcades) only
#   where that ceiling is drawn: it hides what the portal lets through. Not where a sky face covers it (sky faces are
#   not drawn; the roof room would show through the sky). The plain cover leaves covered strips out; Arslegard City's
#   eaves are 16-48 LT over its roof line, and keeping off them all left 405 top portals instead of 157;
# - disjoint from the other top portals: one point over two portals is two floor candidates (the lookup keeps five).
# The barrier voxels stay the footprint (the labels and rooms do not change, except that a street room with no open
# cell keeps its footprint as a barrier, as Arslegard City did by hand); the faces are split at the roof line where the
# plain rectangles would split them (`split_boxes`, rooms.crossing_portals), so only the portal faces change.

MERGE_EPS = 0.02            # cells: a polygon reaches into a cell (or another polygon) only by more than this
MERGE_MAX_CORNERS = 24      # a merged hull with more corners is not made (the native face adds up to one per corner)


def convex_hull(points: np.ndarray) -> np.ndarray:
    """Counter-clockwise hull of 2D points, collinear points dropped (monotone chain)."""
    pts = np.unique(np.asarray(points, float), axis=0)
    if len(pts) < 3:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 1e-9:
            lower.pop()
        lower.append(p)
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 1e-9:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def polygon_area(poly: np.ndarray) -> float:
    x, z = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(z, -1)) - np.dot(z, np.roll(x, -1)))


def polygon_edges(poly: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit outward normals and offsets of a counter-clockwise polygon: inside is n . p <= c."""
    d = np.roll(poly, -1, axis=0) - poly
    n = np.stack([d[:, 1], -d[:, 0]], axis=1)
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    return n, np.einsum("ij,ij->i", n, poly)


def cells_reached(poly: np.ndarray, shape) -> tuple[np.ndarray, np.ndarray]:
    """The cells (x, z) whose square the polygon's interior reaches into by more than MERGE_EPS."""
    lo = np.maximum(np.floor(poly.min(0)).astype(int), 0)
    hi = np.minimum(np.ceil(poly.max(0)).astype(int), np.array(shape))
    xs, zs = np.meshgrid(np.arange(lo[0], hi[0]), np.arange(lo[1], hi[1]), indexing="ij")
    reach = (xs + 1 > poly[:, 0].min() + MERGE_EPS) & (xs < poly[:, 0].max() - MERGE_EPS)
    reach &= (zs + 1 > poly[:, 1].min() + MERGE_EPS) & (zs < poly[:, 1].max() - MERGE_EPS)
    n, c = polygon_edges(poly)
    for (nx, nz), ci in zip(n, c):
        reach &= nx * xs + nz * zs + min(nx, 0.0) + min(nz, 0.0) < ci - MERGE_EPS    # the square's lowest projection
    return xs[reach], zs[reach]


def polygons_overlap(a: np.ndarray, b: np.ndarray) -> bool:
    """Whether two convex polygons overlap by more than MERGE_EPS (no separating axis among their edge normals)."""
    for poly, other in ((a, b), (b, a)):
        n, c = polygon_edges(poly)
        if ((other @ n.T).min(0) >= c - MERGE_EPS).any():
            return False
    return True


def merge_cover(rects: list, ok: np.ndarray, others: list, limit: float) -> tuple[list, float]:
    """Rectangles (x0, z0, x1, z1 inclusive cells) of one street room's open cells, merged into few convex polygons
    (cell-corner coordinates, counter-clockwise): two pieces become their convex hull while the hull reaches only
    `ok` cells, overlaps no other piece (this room's or `others`, the pieces made before) and has at most
    MERGE_MAX_CORNERS corners, and adds at most `limit` x the pieces' own area (+ 4 cells) over cells they did not
    cover. Nearby pieces only (bounds within 2 cells), cheapest merge first. Returns the pieces and the cells added."""
    pieces = {k: np.array([[x0, z0], [x1 + 1, z0], [x1 + 1, z1 + 1], [x0, z1 + 1]], float)
              for k, (x0, z0, x1, z1) in enumerate(rects)}
    own = {k: polygon_area(p) for k, p in pieces.items()}
    boxes = {k: (p.min(0), p.max(0)) for k, p in pieces.items()}
    other_boxes = [(p.min(0), p.max(0)) for p in others]
    next_id = len(pieces)

    def near(a, b, gap=2.0):
        (alo, ahi), (blo, bhi) = boxes[a], boxes[b]
        return bool((alo <= bhi + gap).all() and (blo <= ahi + gap).all())

    def candidate(a, b):
        hull = convex_hull(np.concatenate([pieces[a], pieces[b]]))
        cost = polygon_area(hull) - own[a] - own[b]
        if len(hull) > MERGE_MAX_CORNERS or cost > limit * (own[a] + own[b]) + 4.0:
            return None
        return cost, hull

    def clear(hull, a, b):
        xs, zs = cells_reached(hull, ok.shape)
        if not ok[xs, zs].all():
            return False
        lo, hi = hull.min(0), hull.max(0)
        tests = [(boxes[k], p) for k, p in pieces.items() if k not in (a, b)] + list(zip(other_boxes, others))
        return not any((plo < hi - MERGE_EPS).all() and (lo < phi - MERGE_EPS).all() and polygons_overlap(hull, p)
                       for (plo, phi), p in tests)

    heap = []
    ids = list(pieces)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            found = near(a, b) and candidate(a, b)
            if found:
                heapq.heappush(heap, (found[0], a, b))
    while heap:
        _, a, b = heapq.heappop(heap)
        if a not in pieces or b not in pieces:
            continue
        found = candidate(a, b)
        if found is None or not clear(found[1], a, b):
            continue
        k, next_id = next_id, next_id + 1
        pieces[k], own[k], boxes[k] = found[1], own.pop(a) + own.pop(b), (found[1].min(0), found[1].max(0))
        for gone in (a, b):
            pieces.pop(gone)
            boxes.pop(gone)
        for other in list(pieces):
            if other != k and near(k, other):
                found = candidate(k, other)
                if found is not None:
                    heapq.heappush(heap, (found[0], min(k, other), max(k, other)))
    return list(pieces.values()), sum(polygon_area(p) - own[k] for k, p in pieces.items())


def sky_over_roof_line(build, h: int, settings: dict) -> np.ndarray:
    """Plan cells (x, z) where a sky face (the `sky_alias` texture, MM9's skymarker) passes through layers h .. h + 2:
    a covered strip there is covered by sky. Needs the polygons CityHooks.edit_polygons keeps (`city_polygons`)."""
    grid = build.grid
    cover = np.zeros((grid.shape[0], grid.shape[2]), bool)
    sky_alias = settings.get("sky_alias", "sky04").lower()
    low, high = grid.origin[1] + h * grid.size, grid.origin[1] + (h + 3) * grid.size
    for polygon in getattr(build, "city_polygons", []):
        alias = build.source.aliases.get(polygon.texture.lower(), {}).get("alias", "")
        if str(alias).lower() != sky_alias or polygon.points[:, 1].max() < low or polygon.points[:, 1].min() > high:
            continue
        points = sample_polygon(polygon.points, grid.size / 4)
        points = points[(points[:, 1] >= low) & (points[:, 1] < high)]
        cells = grid.index(points)
        cover[cells[:, 0], cells[:, 2]] = True
    return cover


def merged_top_portals(build, labels2, outdoor, inside, h, street_rooms, plain, settings, report) -> list[dict]:
    """The top portals as merged convex polygons (the notes above): per street room and the room over its open cells
    (the label at layer h + 2), the plain cover's rectangles of those cells merged by `merge_cover`. Each portal's face
    is its polygon (`ring`, expanded to whole native units so the rounded face still covers it); its sides are read
    at its open cells (`side_points`); the footprint is its barrier; `split_boxes` carries the plain cover's portal
    rectangles (`plain`), so faces crossing the roof line are split as before."""
    grid, air, project = build.grid, build.air, build.project
    size = grid.size
    # The room over a cell: the air's at layer h + 2, or at h + 1 where a ceiling (eaves, an arcade) leaves air only
    # there. Such a pocket is still another room's (it reaches the roof room along the eaves), and the barrier cuts it
    # off from the street: with no portal there its ceiling, drawn with that room, was missing from the street (MM9
    # portal sweep 2026-11-08: uncovered barriers in every city, dungeon/rooms.py uncovered_barriers). The portal's
    # sides are read one voxel off its layer (side_points, rooms.portal_sides). Only a cell with no air over it at
    # all (a ceiling sitting on the roof line) opens nothing, as the plain cover's blind rectangles.
    below = labels2[:, h - 1, :]
    up = np.where(air[:, h + 2, :], labels2[:, h + 2, :], np.where(air[:, h + 1, :], labels2[:, h + 1, :], 0))
    air_m, air_h = air[:, h - 1, :], air[:, h, :]
    out_h = outdoor[:, h, :]
    y_plane = grid.origin[1] + (h + 0.5) * size
    sky_cover = sky_over_roof_line(build, h, settings)
    pieces, made, footprints, added = [], [], {}, 0.0
    for room in street_rooms:
        footprint = (below == room) & out_h & inside
        footprints[room] = np.argwhere(footprint)
        opened = footprint & (up != 0) & (up != room)
        for over in sorted(set(int(v) for v in np.unique(up[opened]))):
            must = opened & (up == over)
            ok = inside & (~air_m | (below == room)) & (~air_h | out_h)
            for layer in (h + 1, h + 2):
                ok &= ~air[:, layer, :] | (labels2[:, layer, :] == over)
            ok &= ~(footprint & ~opened & sky_cover)    # no sight up through a sky face over a covered strip
            polygons, extra = merge_cover(rectangles(must), ok, made, float(settings["top_portal_extension"]))
            made += polygons
            added += extra
            pieces += [(room, polygon, must) for polygon in polygons]
    tops, kept_cells = [], 0
    per_room = Counter()
    for room, polygon, must in pieces:
        per_room[room] += 1
        n, c = polygon_edges(polygon)
        cells2 = np.argwhere(must)
        centres = cells2 + 0.5
        inside_cells = cells2[((centres @ n.T) <= c + 1e-6).all(1)]
        if len(inside_cells) > 400:
            inside_cells = inside_cells[np.linspace(0, len(inside_cells) - 1, 400).astype(int)]
        side_points = np.stack([grid.origin[0] + (inside_cells[:, 0] + 0.5) * size,
                                np.full(len(inside_cells), y_plane),
                                grid.origin[2] + (inside_cells[:, 1] + 0.5) * size], axis=1)
        # The ring in whole native units: the hull of each corner's four surrounding integer points covers the polygon.
        corners = project.native(np.stack([grid.origin[0] + polygon[:, 0] * size, np.full(len(polygon), y_plane),
                                           grid.origin[2] + polygon[:, 1] * size], axis=1))
        lattice = np.concatenate([np.stack([fx(corners[:, 0]), fy(corners[:, 1])], axis=1)
                                  for fx in (np.floor, np.ceil) for fy in (np.floor, np.ceil)])
        ring_native = convex_hull(lattice)
        ring = np.array([project.lt_from_native((x, y, corners[0, 2])) for x, y in ring_native])
        lo, hi = ring.min(0), ring.max(0)
        tops.append({"name": f"roofline_{room}_{per_room[room]}", "kind": "roof_line",
                     "centre": np.array([(lo[0] + hi[0]) / 2, y_plane, (lo[2] + hi[2]) / 2]),
                     "normal": np.array([0.0, 1.0, 0.0]), "axis_a": np.array([1.0, 0.0, 0.0]),
                     "half_a": (hi[0] - lo[0]) / 2, "axis_b": np.array([0.0, 0.0, 1.0]), "half_b": (hi[2] - lo[2]) / 2,
                     "ring": ring, "side_points": side_points, "split_boxes": [],
                     "cells": np.zeros((0, 3), np.int64), "room_key": room})
    if tops:
        for room, cells2 in footprints.items():
            keeper = next((p for p in tops if p["room_key"] == room), None)
            if keeper is None:
                keeper, kept_cells = tops[0], kept_cells + len(cells2)
            cells = np.stack([cells2[:, 0], np.full(len(cells2), h), cells2[:, 1]], axis=1)
            keeper["cells"] = np.concatenate([keeper["cells"], cells])
        tops[0]["split_boxes"] = [(p["name"], rectangle_points(p["centre"], p["axis_a"], p["half_a"] + size,
                                                               p["axis_b"], p["half_b"] + size, 1e9)) for p in plain]
    report["top_portals"] = len(tops)
    report["top_portals_per_room"] = dict(per_room)
    report["top_portal_corners_max"] = max((len(p["ring"]) for p in tops), default=0)
    report["top_portal_extension_lt2"] = round(added * size * size)
    report["roof_line_cells_kept"] = kept_cells
    report["roof_line_cells_under_sky"] = int(sky_cover.sum())
    return tops
