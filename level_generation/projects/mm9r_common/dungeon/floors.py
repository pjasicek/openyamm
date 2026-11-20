"""
Floor holes and cracks (devdocs/mm9_rework/SPIRAL_STAIR_PATHING.md, option A1). Two repairs after the face
assignment, both on by default (overrides.yml `map: {restore_floor_holes: false, weld_floor_cracks: false}` turns
them off), and the check that reports what is left:

- **Restored floor faces.** An up-facing polygon that the room assignment drops ("no air in front": a thin wedge of
  a slab tread whose voxels the treads around it touch) is kept when a kept coplanar polygon of the same model and
  role shares an edge with it and labelled air lies right above it with no polygon in between (Occluders): it takes
  that polygon's room. The air test keeps the faces that were rightly dropped dropped: tops under a wall standing on
  them, outside shells and tops of ceilings have no labelled air above, and a face under a floor slab does not see the
  room above through the slab (Verhoffin Ruins' ledges). The Thousand Terrors' spiral stair lost eight tread tops so.
- **Welded cracks.** Two kept horizontal floors at the same height whose parallel edges lie at most WELD_GAP_NATIVE
  apart (MM9's brushes leave such cracks: 3 units between the Thousand Terrors' landing and its exit floor) get a strip
  between the edges over their overlap, when labelled air lies above the crack and no floor already covers it. A
  monster's path planner samples the floor every 2 units and falls through any crack wider than that.
- **The check** (`floor_holes`): up-facing dropped faces with labelled air above and a kept floor of the same height
  beside them, and same-height floor cracks up to CRACK_REPORT_NATIVE that no floor (or weld strip) covers.
  The build prints a WARNING line for each kind and writes them to work/floor_holes.json.

All geometry is in LithTech units (y up), as in geometry.py.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .geometry import Polygon, clip, sample_polygon
from .source import SCALE

UP = 0.7                        # a polygon whose normal's y is at least this is a floor
HORIZONTAL = 0.999              # a floor this flat takes part in the crack weld
COPLANAR_DOT, COPLANAR_OFFSET = 0.999, 0.25         # LT
EDGE_ON_LINE, EDGE_OVERLAP = 0.1, 1.0               # LT: an edge lies on another's line; the shortest shared length
ABOVE_VOXELS = (1.0, 1.5, 2.0, 2.5, 3.0)           # where labelled air is looked for over a face, in voxels
WELD_GAP_NATIVE = 6.0           # cracks up to this wide (native) are closed (MM9 brush cracks: 2.6-5.5)
CRACK_REPORT_NATIVE = 16.0      # wider ones up to this are reported
SAME_HEIGHT_NATIVE = 1.0        # two floors this close in height are one surface
WELD_OVERLAP_LT = 4.0           # the shortest crack worth a strip
HOLE_MIN_AREA_LT = 20.0         # the check ignores dropped slivers smaller than this
HOLE_NEIGHBOUR_LT = 48.0 / SCALE  # a same-height floor this close (48 native) makes a dropped face a hole


def _edges(polygon: Polygon):
    points = polygon.points
    return [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]


def _segment_overlap(a0, a1, b0, b1) -> float:
    """The length over which segment b lies on segment a's line (0 when b leaves the line or misses a)."""
    axis = a1 - a0
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        return 0.0
    axis = axis / length
    for point in (b0, b1):
        offset = point - a0
        if np.linalg.norm(offset - axis * (offset @ axis)) > EDGE_ON_LINE:
            return 0.0
    t0, t1 = sorted((float((b0 - a0) @ axis), float((b1 - a0) @ axis)))
    return max(0.0, min(length, t1) - max(0.0, t0))


def _shares_edge(a: Polygon, b: Polygon) -> bool:
    return any(_segment_overlap(a0, a1, b0, b1) >= EDGE_OVERLAP for a0, a1 in _edges(a) for b0, b1 in _edges(b))


def _coplanar(a: Polygon, b: Polygon) -> bool:
    na, nb = a.normal, b.normal
    return float(na @ nb) >= COPLANAR_DOT and abs(float(na @ (b.points[0] - a.points[0]))) <= COPLANAR_OFFSET


class Occluders:
    """The non-vertical polygons of the map in a grid over x, z: does one cross a vertical segment?"""
    CELL = 64.0

    def __init__(self, polygons: list[Polygon]):
        self.grid = defaultdict(list)
        for polygon in polygons:
            normal = polygon.normal
            if abs(normal[1]) < 0.05:
                continue                        # walls: a vertical segment does not cross them
            low, high = polygon.points.min(0), polygon.points.max(0)
            entry = (polygon, normal, float(normal @ polygon.points[0]), low, high)
            for gx in range(int(np.floor(low[0] / self.CELL)), int(np.floor(high[0] / self.CELL)) + 1):
                for gz in range(int(np.floor(low[2] / self.CELL)), int(np.floor(high[2] / self.CELL)) + 1):
                    self.grid[(gx, gz)].append(entry)

    def crossed(self, point: np.ndarray, top: float) -> bool:
        """A polygon crosses the vertical segment from point (exclusive, 0.5 LT up) to the height top."""
        x, z = float(point[0]), float(point[2])
        for polygon, normal, d, low, high in self.grid.get((int(np.floor(x / self.CELL)), int(np.floor(z / self.CELL))),
                                                           ()):
            if x < low[0] or x > high[0] or z < low[2] or z > high[2] or high[1] < point[1] + 0.5 or low[1] > top:
                continue
            y = (d - normal[0] * x - normal[2] * z) / normal[1]
            if not (point[1] + 0.5 < y < top):
                continue
            ring = polygon.points[:, [0, 2]]
            edges = np.roll(ring, -1, axis=0) - ring
            cross = edges[:, 0] * (z - ring[:, 1]) - edges[:, 1] * (x - ring[:, 0])
            if (cross >= -1e-6).all() or (cross <= 1e-6).all():
                return True
        return False


def air_above(rooms, polygon: Polygon, fraction: float = 0.0, occluders: Occluders | None = None) -> bool:
    """Labelled air within three voxels over the polygon (along its normal), and with `occluders` no polygon between
    the face and that air (a floor slab over a face under it: the air of the room above does not count): over more
    than `fraction` of its samples (any sample with the default)."""
    samples = sample_polygon(polygon.points, rooms.grid.size / 2)
    if not len(samples):
        return False
    reach = np.full(len(samples), np.inf)
    for step in ABOVE_VOXELS[::-1]:             # the nearest labelled air above each sample
        cells = rooms.grid.index(samples + polygon.normal * rooms.grid.size * step)
        found = rooms.labels[cells[:, 0], cells[:, 1], cells[:, 2]] > 0
        reach[found] = step
    hit = np.isfinite(reach)
    if occluders is not None:
        for i in np.flatnonzero(hit):
            # up to the far side of the voxel holding the air
            top = float(samples[i][1] + polygon.normal[1] * rooms.grid.size * (reach[i] + 0.5))
            if occluders.crossed(samples[i], top):
                hit[i] = False
    return hit.mean() > fraction if fraction else bool(hit.any())


def _record(polygon: Polygon, **extra) -> dict:
    return dict({"model": polygon.model, "texture": polygon.texture.split("\\")[-1],
                 "centre_lt": polygon.points.mean(0).round(1).tolist(), "normal_lt": polygon.normal.round(2).tolist(),
                 "area_lt": round(polygon.area), "ring_lt": polygon.points.round(1).tolist()}, **extra)


def restore_floor_holes(rooms, kept: list[Polygon], dropped: list[Polygon], stats, log,
                        occluders: Occluders | None = None) -> list[Polygon]:
    """Dropped up-facing polygons beside a kept coplanar polygon of the same model and role, with labelled air above
    and nothing between (occluders: all the map's polygons): each takes that polygon's room (repeated, so a run of
    dropped pieces restores from its kept end). Returns the restored polygons; the rest stay in `dropped`."""
    if occluders is None:
        occluders = Occluders(kept + dropped)
    by_model = defaultdict(list)
    for polygon in kept:
        if polygon.normal[1] >= UP and polygon.label > 0:
            by_model[(polygon.model, polygon.role)].append(polygon)
    restored = []
    pending = [p for p in dropped if p.normal[1] >= UP and p.role != "glass"]
    # each group's boxes as arrays, extended as restored polygons join it (the per-pair box tests in Python took 80 s
    # of Thronheim City's build)
    boxes = {}

    def group_boxes(key):
        group = by_model.get(key, ())
        lows, highs = boxes.get(key, (np.zeros((0, 3)), np.zeros((0, 3))))
        if len(lows) < len(group):
            lows = np.vstack([lows] + [p.points.min(0)[None] for p in group[len(lows):]])
            highs = np.vstack([highs] + [p.points.max(0)[None] for p in group[len(highs):]])
            boxes[key] = (lows, highs)
        return group, lows, highs

    changed = True
    while changed and pending:
        changed = False
        for polygon in list(pending):
            low, high = polygon.points.min(0) - 1.0, polygon.points.max(0) + 1.0
            group, lows, highs = group_boxes((polygon.model, polygon.role))
            near = np.flatnonzero(~((highs < low).any(1) | (lows > high).any(1)))
            for other in (group[i] for i in near):
                if not (_coplanar(polygon, other) and _shares_edge(polygon, other)):
                    continue
                if not air_above(rooms, polygon, occluders=occluders):
                    # under a wall or a floor, outside: stays dropped
                    pending = [p for p in pending if p is not polygon]
                    break
                polygon.label = other.label
                restored.append(polygon)
                by_model[(polygon.model, polygon.role)].append(polygon)
                pending = [p for p in pending if p is not polygon]
                log.setdefault("restored", []).append(_record(polygon, room=int(other.label)))
                changed = True
                break
    stats["floor_faces_restored"] = len(restored)
    stats["floor_area_restored_lt2"] = round(sum(p.area for p in restored))
    gone = {id(p) for p in restored}
    dropped[:] = [p for p in dropped if id(p) not in gone]
    return restored


def _crack_pairs(polygons: list[Polygon], max_gap_lt: float):
    """Pairs of edges of two horizontal floors at the same height that run parallel, face each other across a gap of
    at most max_gap_lt and overlap along their length: (gap, overlap, polygon a, edge a, polygon b, edge b)."""
    floors = [p for p in polygons if p.normal[1] >= HORIZONTAL and p.role == "static" and p.label > 0]
    same_height = SAME_HEIGHT_NATIVE / SCALE
    cell = 64.0
    grid = defaultdict(list)
    edges = []
    for index, polygon in enumerate(floors):
        centre = polygon.points.mean(0)
        for a0, a1 in _edges(polygon):
            direction = a1 - a0
            length = float(np.hypot(direction[0], direction[2]))
            if length < WELD_OVERLAP_LT:
                continue
            # the outward normal in the horizontal plane (away from the polygon's centre)
            outward = np.array([direction[2], 0.0, -direction[0]]) / length
            if outward @ (a0 - centre) < 0:
                outward = -outward
            record = (index, a0, a1, outward, len(edges))
            edges.append(record)
            low = np.minimum(a0, a1) - max_gap_lt
            high = np.maximum(a0, a1) + max_gap_lt
            for gx in range(int(np.floor(low[0] / cell)), int(np.floor(high[0] / cell)) + 1):
                for gz in range(int(np.floor(low[2] / cell)), int(np.floor(high[2] / cell)) + 1):
                    grid[(gx, gz)].append(record)
    seen = set()
    for bucket in grid.values():
        for i in range(len(bucket)):
            ia, a0, a1, na, ea = bucket[i]
            for j in range(i + 1, len(bucket)):
                ib, b0, b1, nb, eb = bucket[j]
                if ia == ib or (ea, eb) in seen:
                    continue
                if abs(float(a0[1] - b0[1])) > same_height or abs(float(a1[1] - b1[1])) > same_height:
                    continue
                if float(na @ nb) > -0.9995:              # facing each other, parallel within about 1.8 degrees
                    continue
                gap = float((b0 - a0) @ na)
                gap1 = float((b1 - a0) @ na)
                if not (0.02 < gap <= max_gap_lt and 0.02 < gap1 <= max_gap_lt):
                    continue
                axis = (a1 - a0) / np.linalg.norm(a1 - a0)
                ta = sorted((0.0, float((a1 - a0) @ axis)))
                tb = sorted((float((b0 - a0) @ axis), float((b1 - a0) @ axis)))
                start, end = max(ta[0], tb[0]), min(ta[1], tb[1])
                if end - start < WELD_OVERLAP_LT:
                    continue
                seen.add((ea, eb))
                yield (gap, gap1, start, end, floors[ia], (a0, a1, na), floors[ib], (b0, b1, nb))


def _strip(a: Polygon, edge_a, edge_b, start: float, end: float) -> Polygon:
    """The strip between two facing edges over [start, end] along edge a."""
    a0, a1, na = edge_a
    b0, b1, nb = edge_b
    axis = (a1 - a0) / np.linalg.norm(a1 - a0)

    def on_b(point):                             # the point of b's line across the gap from a point of a
        direction = b1 - b0
        t = float((point - b0) @ direction) / float(direction @ direction)
        return b0 + direction * t

    p0, p1 = a0 + axis * start, a0 + axis * end
    ring = np.array([p0, p1, on_b(p1), on_b(p0)])
    strip = Polygon(ring, [("weld", tuple(np.round(p, 2))) for p in ring], a.texture, a.mapping, a.flags, a.model,
                    a.role, label=a.label, notes=dict(a.notes, welded=True))
    if strip.normal[1] < 0:
        strip = Polygon(ring[::-1].copy(), strip.keys[::-1], a.texture, a.mapping, a.flags, a.model, a.role,
                        label=a.label, notes=dict(a.notes, welded=True))
    return strip


class _FloorBoxes:
    """The floors' mean heights and boxes as arrays, for the many point and box tests over all floors (the crack and
    hole checks: 20 s of a city build in per-floor Python)."""
    def __init__(self, floors: list[Polygon]):
        self.floors = floors
        self.height = np.array([float(p.points[:, 1].mean()) for p in floors])
        self.low = np.array([p.points.min(0) for p in floors]).reshape(-1, 3)
        self.high = np.array([p.points.max(0) for p in floors]).reshape(-1, 3)

    def covered(self, point: np.ndarray, tolerance_lt: float) -> bool:
        """`_covered` over these floors."""
        near = np.flatnonzero((np.abs(point[1] - self.height) <= tolerance_lt)
                              & (self.low[:, 0] <= point[0]) & (self.high[:, 0] >= point[0])
                              & (self.low[:, 2] <= point[2]) & (self.high[:, 2] >= point[2]))
        return _covered(point, [self.floors[i] for i in near], tolerance_lt)

    def beside(self, height: float, tolerance: float, low: np.ndarray, high: np.ndarray) -> bool:
        """A floor of about this height whose box meets the box low..high."""
        return bool(((np.abs(self.height - height) <= tolerance) & ~(self.high < low).any(1)
                     & ~(self.low > high).any(1)).any())


def _covered(point: np.ndarray, floors: list[Polygon], tolerance_lt: float) -> bool:
    """A floor polygon of about the point's height over the point (seen from above)."""
    for polygon in floors:
        points = polygon.points
        if abs(float(point[1] - points[:, 1].mean())) > tolerance_lt:
            continue
        if (points[:, 0].min() > point[0]) or (points[:, 0].max() < point[0]) or \
                (points[:, 2].min() > point[2]) or (points[:, 2].max() < point[2]):
            continue
        inside = True
        sign = 0.0
        for i in range(len(points)):
            p, q = points[i], points[(i + 1) % len(points)]
            cross = (q[0] - p[0]) * (point[2] - p[2]) - (q[2] - p[2]) * (point[0] - p[0])
            if abs(cross) < 1e-9:
                continue
            if sign == 0.0:
                sign = np.sign(cross)
            elif np.sign(cross) != sign:
                inside = False
                break
        if inside:
            return True
    return False


def weld_floor_cracks(rooms, polygons: list[Polygon], stats, log) -> list[Polygon]:
    """Strips over the cracks (at most WELD_GAP_NATIVE wide) between same-height horizontal floors, where labelled
    air lies over the crack and no floor already covers it. Returns the strips (each in room of its first floor)."""
    floors = _FloorBoxes([p for p in polygons if p.normal[1] >= UP])
    occluders = Occluders(polygons)
    strips = []
    for gap, gap1, start, end, a, edge_a, b, edge_b in _crack_pairs(polygons, WELD_GAP_NATIVE / SCALE):
        strip = _strip(a, edge_a, edge_b, start, end)
        middle = strip.points.mean(0)
        tolerance = SAME_HEIGHT_NATIVE / SCALE
        if floors.covered(middle, tolerance) or _covered(middle, strips, tolerance):
            continue
        if not air_above(rooms, strip, fraction=0.5, occluders=occluders):
            log.setdefault("cracks_left", []).append(_record(strip, gap_native=round(max(gap, gap1) * SCALE, 2),
                                                             reason="no air above"))
            continue
        strips.append(strip)
        log.setdefault("welded", []).append(_record(strip, gap_native=round(max(gap, gap1) * SCALE, 2),
                                                    length_native=round((end - start) * SCALE),
                                                    rooms=[int(a.label), int(b.label)]))
    stats["floor_cracks_welded"] = len(strips)
    return strips


def floor_holes(rooms, polygons: list[Polygon], dropped: list[Polygon]) -> dict:
    """The check: up-facing dropped faces (at least HOLE_MIN_AREA_LT) with labelled air above and a kept floor of
    their height within 48 native, and same-height cracks wider than the weld (up to CRACK_REPORT_NATIVE) with air
    above and no floor over them. Native coordinates are left to the caller (LT here)."""
    floors = _FloorBoxes([p for p in polygons if p.normal[1] >= UP and p.label > 0])
    same_height = SAME_HEIGHT_NATIVE / SCALE
    occluders = Occluders(polygons + dropped)
    holes = []
    for polygon in dropped:
        if polygon.normal[1] < UP or polygon.area < HOLE_MIN_AREA_LT or polygon.role == "glass":
            continue
        low, high = polygon.points.min(0) - HOLE_NEIGHBOUR_LT, polygon.points.max(0) + HOLE_NEIGHBOUR_LT
        height = float(polygon.points[:, 1].mean())
        beside = floors.beside(height, same_height + 0.5, low, high)
        if beside and air_above(rooms, polygon, occluders=occluders):
            holes.append(_record(polygon, role=polygon.role))
    cracks = []
    for gap, gap1, start, end, a, edge_a, b, edge_b in _crack_pairs(polygons, CRACK_REPORT_NATIVE / SCALE):
        strip = _strip(a, edge_a, edge_b, start, end)
        if floors.covered(strip.points.mean(0), same_height) or \
                not air_above(rooms, strip, fraction=0.5, occluders=occluders):
            continue
        cracks.append(_record(strip, gap_native=round(max(gap, gap1) * SCALE, 2),
                              length_native=round((end - start) * SCALE), rooms=[int(a.label), int(b.label)]))
    return {"holes": holes, "cracks": cracks}


# --- Invisible brush bottoms (2026-10-31) ---------------------------------------------------------------------------
# The party's collision height (IndoorWorldRuntime PartyCollisionHeight 192 native units) in LT units.
PARTY_HEIGHT_LT = 192 / 2.56


def _plane_height(polygon, x: np.ndarray, z: np.ndarray) -> np.ndarray:
    normal, origin = polygon.normal, polygon.points[0]
    return origin[1] - (normal[0] * (x - origin[0]) + normal[2] * (z - origin[2])) / normal[1]


def _inside_xz(ring: np.ndarray, x: np.ndarray, z: np.ndarray) -> np.ndarray:
    inside = np.zeros(len(x), bool)
    for index in range(len(ring)):
        (x1, z1), (x2, z2) = ring[index], ring[(index + 1) % len(ring)]
        crosses = (z1 > z) != (z2 > z)
        with np.errstate(divide="ignore", invalid="ignore"):
            inside ^= crosses & (x < x1 + (z - z1) * (x2 - x1) / np.where(z2 == z1, 1e-12, z2 - z1))
    return inside


def invisible_bottoms(polygons: list, stats, log: dict) -> list:
    """Drop the down-facing faces of MM9's invisible collision brushes that sit less than the party's height above
    the floor under them. They are the flat undersides of the invisible ramp wedges laid over stairs (LithTech
    "Default" and Invisible.dtx brushes) and of other helper brushes resting on a floor: as invisible ceilings 0-8 LT
    over the treads they stopped the party on the stairs (Temple of Honk, 2026-10-31), and no party fits under them, so
    they block nothing the brush's sides do not. A down-facing invisible face higher above its floor than the party
    is tall (or with no floor under it) is kept: a lid over a shaft or a hall (Klusos House's 1568 LT, Thjorad Mine's
    232-856 LT, Lich Lab's 580-600 LT). The gap is the largest over the face's centre and its corners pulled 40 % in,
    to the highest up-facing static or invisible face below each point. Returns the polygons kept; the dropped are in
    log["invisible_bottoms"] (LT centre, gap, texture)."""
    ups = [p for p in polygons if p.role in ("static", "invisible") and p.normal[1] > 0.3]
    lows = np.array([p.points.min(0) for p in ups]) if ups else np.zeros((0, 3))
    highs = np.array([p.points.max(0) for p in ups]) if ups else np.zeros((0, 3))
    kept, dropped = [], []
    for polygon in polygons:
        if polygon.role != "invisible" or polygon.normal[1] > -0.3:
            kept.append(polygon)
            continue
        centre = polygon.points.mean(0)
        samples = np.array([centre] + [centre + 0.6 * (point - centre) for point in polygon.points])
        floor = np.full(len(samples), -np.inf)
        near = np.nonzero((lows[:, 0] <= samples[:, 0].max() + 0.01) & (highs[:, 0] >= samples[:, 0].min() - 0.01)
                          & (lows[:, 2] <= samples[:, 2].max() + 0.01) & (highs[:, 2] >= samples[:, 2].min() - 0.01)
                          & (lows[:, 1] <= samples[:, 1].max() + 0.5))[0]
        for index in near:
            up = ups[index]
            inside = _inside_xz(up.points[:, [0, 2]], samples[:, 0], samples[:, 2])
            height = _plane_height(up, samples[:, 0], samples[:, 2])
            below = inside & (height <= samples[:, 1] + 0.5)
            floor = np.where(below & (height > floor), height, floor)
        gap = float((samples[:, 1] - floor).max())
        if gap <= PARTY_HEIGHT_LT:
            dropped.append(polygon)
            log.setdefault("invisible_bottoms", []).append(
                {"centre_lt": centre.round(1).tolist(), "gap_lt": round(gap, 1),
                 "texture": polygon.texture.replace("\\", "/").split("/")[-1]})
        else:
            kept.append(polygon)
    stats["invisible_bottoms_dropped"] = len(dropped)
    return kept


RAMP_FOOT_LT = 1.0              # a sloped floor whose lowest corner is this close to a flat floor's height rises from it
# A sloped top narrower than the party (2 x its 37-unit radius) across its slope is no ramp it walks onto: a diagonal
# beam or a stair stringer, whose floor cut showed a strip of sky under it (Sturmford City, 2026-11-07)
RAMP_MIN_WIDTH_LT = 74 / 2.56


def cut_floors_under_ramps(polygons: list, stats, log: dict) -> list:
    """A flat floor running on under a ramp that rises out of it (MM9 lays the hall's floor slab under the solid ramp
    block standing on it: Thjorgard's throne room, 2026-11-01) is cut where the ramp is less than the party's height
    over it. There both faces are under the party's feet at the ramp's foot, the engine keeps the flat floor (nearest
    the feet) and the party walks on under the ramp instead of onto it. A ramp is a static sloped floor (UP <= normal y
    < HORIZONTAL) of the same room whose lowest corner is at the flat floor's height; the floor's part under the ramp's
    plan where the ramp is lower than PARTY_HEIGHT_LT over it is dropped (convex pieces by the plan's edges)."""
    ramps = [p for p in polygons if p.role == "static" and p.label > 0 and UP <= p.normal[1] < HORIZONTAL]
    if not ramps:
        return polygons
    flats = [p for p in polygons if p.role == "static" and p.label > 0 and p.normal[1] >= HORIZONTAL]
    # each flat floor's room, mean height and plan box once (the per-pair tests of every ramp against every flat floor
    # took 100 s of a region's build); the loop below tests only the flats these let through, in order
    flat_labels = np.array([flat.label for flat in flats])
    flat_heights = np.array([float(flat.points[:, 1].mean()) for flat in flats])
    flat_lows = np.array([flat.points[:, [0, 2]].min(0) for flat in flats]).reshape(-1, 2)
    flat_highs = np.array([flat.points[:, [0, 2]].max(0) for flat in flats]).reshape(-1, 2)
    replaced = {}
    for ramp in ramps:
        foot = float(ramp.points[:, 1].min())
        plan = ramp.points[:, [0, 2]]
        rise = np.array([ramp.normal[0], ramp.normal[2]])
        if np.linalg.norm(rise) > 1e-9:
            across = np.array([-rise[1], rise[0]]) / np.linalg.norm(rise)
            if np.ptp(plan @ across) < RAMP_MIN_WIDTH_LT:
                continue
        low, high = plan.min(0), plan.max(0)
        normal = ramp.normal
        offset = float(normal @ ramp.points[0])
        # the plan ring counter-clockwise (x, z), its edges' outward planes
        ring = plan if np.cross(plan[1] - plan[0], plan[2] - plan[0]) > 0 else plan[::-1]
        near = np.flatnonzero((flat_labels == ramp.label) & ~(np.abs(flat_heights - foot) > RAMP_FOOT_LT)
                              & ~((flat_lows >= high).any(1) | (flat_highs <= low).any(1)))
        for k in near:
            flat = flats[k]
            pieces = replaced.get(id(flat), [flat])
            height = float(flat_heights[k])
            kept, changed = [], False
            for piece in pieces:
                remaining = piece
                outside = []
                for index in range(len(ring)):
                    a, b = ring[index], ring[(index + 1) % len(ring)]
                    edge = b - a
                    out = np.array([edge[1], 0.0, -edge[0]])
                    length = np.linalg.norm(out)
                    if length < 1e-9:
                        continue
                    out /= length
                    front, back = clip(remaining, out, float(out @ np.array([a[0], 0.0, a[1]])), "rampcut")
                    if front is not None:
                        outside.append(front)
                    remaining = back
                    if remaining is None:
                        break
                if remaining is not None and normal[1] > 0:
                    # where the ramp is higher than the party over the floor, the floor stays
                    rise = np.array([normal[0], 0.0, normal[2]])
                    rise_length = np.linalg.norm(rise)
                    if rise_length > 1e-9:
                        level = offset - normal[1] * (height + PARTY_HEIGHT_LT)
                        under_low, under_high = clip(remaining, rise / rise_length, level / rise_length, "rampcut")
                        if under_high is not None:
                            outside.append(under_high)
                        remaining = under_low
                if remaining is None or remaining.area < 1.0:
                    kept.append(piece)
                    continue
                changed = True
                for part in outside:
                    part.label = piece.label
                kept += [part for part in outside if part.area >= 0.01]
                stats["floor_area_cut_under_ramps_lt2"] += round(remaining.area)
            if changed:
                replaced[id(flat)] = kept
                log.setdefault("floors_cut_under_ramps", []).append(
                    {"ramp_centre_lt": ramp.points.mean(0).round(1).tolist(), "floor_height_lt": round(height, 1)})
    if not replaced:
        return polygons
    stats["floors_cut_under_ramps"] = len(replaced)
    result = []
    for polygon in polygons:
        result += replaced.get(id(polygon), [polygon])
    return result


OVERLAY_LT = 4.0                # a walkable face this close over a parallel floor lies on it (a carpet, a rug)


def cut_floors_under_overlays(polygons: list, stats, log: dict) -> list:
    """A floor under a walkable face lying on it (a carpet or rug 1-4 LT over the floor or ramp, parallel: MM9 lays
    them as polygons of their own) is cut away under that face. The two are both under the party's feet, and on a
    slope the engine's floor choice (the face nearest the feet) alternates between them every few movement steps: the
    party bounced up a 3-unit stack 32 times a second (Thjorgard's throne room carpet, 2026-11-02). The cut part is
    hidden under the overlay anyway. Static floors (normal y >= UP) of one room, normals within 2.5 degrees, the
    overlay 0.2-OVERLAY_LT over the floor's plane; the floor is clipped by the overlay's edges taken along its normal
    and the part inside dropped. A skirt along each edge of such an overlay, down to the floor's plane, closes the slit
    under its edge."""
    floors = [p for p in polygons if p.role == "static" and p.label > 0 and p.normal[1] >= UP]
    replaced, skirt_gaps = {}, {}
    if not floors:
        return polygons
    # Each floor's normal, first point, label and plan bounds once: a region of terrain has 20 000 floors, and testing
    # every pair with normals rebuilt per test took over half an hour (Sturmford, 2026-11-02). The candidates below are
    # exactly the pairs the tests in the loop accept.
    normals = np.array([f.normal for f in floors])
    firsts = np.array([f.points[0] for f in floors])
    labels = np.array([f.label for f in floors])
    lows = np.array([f.points.min(0) for f in floors])
    highs = np.array([f.points.max(0) for f in floors])
    for overlay_index, overlay in enumerate(floors):
        normal = normals[overlay_index]
        centre = overlay.points.mean(0)
        edges = []
        for index in range(len(overlay.points)):
            a, b = overlay.points[index], overlay.points[(index + 1) % len(overlay.points)]
            out = np.cross(b - a, normal)
            length = np.linalg.norm(out)
            if length < 1e-9:
                continue
            out /= length
            if out @ (centre - a) > 0:
                out = -out
            edges.append((out, float(out @ a)))
        low, high = lows[overlay_index], highs[overlay_index]
        gaps = (firsts[overlay_index] - firsts) @ normal
        candidates = np.flatnonzero(
            (labels == overlay.label) & (normals @ normal >= 0.999) & (gaps >= 0.2) & (gaps <= OVERLAY_LT)
            & ~((lows[:, [0, 2]] >= high[[0, 2]]).any(1) | (highs[:, [0, 2]] <= low[[0, 2]]).any(1)))
        for floor_index in candidates:
            if floor_index == overlay_index:
                continue
            floor = floors[floor_index]
            kept, changed = [], False
            for piece in replaced.get(id(floor), [floor]):
                remaining, outside = piece, []
                for out, offset in edges:
                    front, back = clip(remaining, out, offset, "overlaycut")
                    if front is not None:
                        outside.append(front)
                    remaining = back
                    if remaining is None:
                        break
                if remaining is None or remaining.area < 1.0:
                    kept.append(piece)
                    continue
                changed = True
                for part in outside:
                    part.label = piece.label
                kept += [part for part in outside if part.area >= 0.01]
                stats["floor_area_cut_under_overlays_lt2"] += round(remaining.area)
            if changed:
                replaced[id(floor)] = kept
                previous = skirt_gaps.get(id(overlay), (overlay, 0.0))[1]
                skirt_gaps[id(overlay)] = (overlay, max(previous, float(gaps[floor_index])))
    if not replaced:
        return polygons
    stats["floors_cut_under_overlays"] = len(replaced)
    result = []
    for polygon in polygons:
        result += replaced.get(id(polygon), [polygon])
    # The overlay's edge now stands over nothing: a skirt from its edge down to the floor's plane closes the slit the
    # view slipped through (lines of sky along every rug's border, Thjorgard 2026-11-02): the rug's thickness, in its
    # own texture.
    for overlay, gap in skirt_gaps.values():
        normal, centre = overlay.normal, overlay.points.mean(0)
        for index in range(len(overlay.points)):
            a, b = overlay.points[index], overlay.points[(index + 1) % len(overlay.points)]
            if np.linalg.norm(b - a) < 1.0:
                continue
            ring = np.array([a, b, b - normal * gap, a - normal * gap])
            if np.cross(ring[1] - ring[0], ring[2] - ring[0]) @ ((a + b) / 2 - centre) < 0:
                ring = ring[::-1].copy()
            skirt = Polygon(ring, [("overlayskirt", tuple(np.round(point, 2))) for point in ring], overlay.texture,
                            overlay.mapping, overlay.flags, overlay.model, "static", notes=dict(overlay.notes))
            skirt.label = overlay.label
            result.append(skirt)
            stats["overlay_skirt_faces"] += 1
    return result
