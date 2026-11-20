"""
CityHooks: the dungeon converter's hooks for an MM9 city (../CITY_PLAYBOOK.md). A city project's convert.py
subclasses it instead of dungeon.Hooks:

- extra_portals: the open air's sectors (structure.py: roof line, street cuts, top portals);
- scene: the sky faces (MM9's skymarker polygons, aliased in overrides.yml `textures`) get IndoorSky by
  `face_attribute_overrides`, and the scene opens to the sky (`sky: {mode: open}`, devdocs/INDOOR_OPEN_SKY.md:
  the Enhanced outdoor sky behind them, with the time of day), unless overrides.yml `city: {open_sky: false}`;
  `city: {weather: rain | snow | rain_and_snow}` gives it the outdoor weather (apply_weather; none by default);
  and with `city: {daylight: true}` (opt-in) the scene's `daylight` from MM9's data (Source.daylight): the sun and
  sky light on the sectors open to the sky, by the time of day;
- edit_polygons: invisible half steps up MM9's 50-66 unit raised floors where the party can stand on them
  (`half_steps`, below; opt-in: `city: {half_steps: true}`, ../CITY_PLAYBOOK.md "Raised floors");
- report: the structure report (`build_report.json` "city").

The painted minimap and the outline pass are converter settings (`map: {painted_minimap: true}`).
"""

from __future__ import annotations

import sys

import numpy as np

import dungeon
from dungeon.geometry import Polygon
from dungeon.source import ROOT, SCALE

from . import structure

INDOOR_SKY = 0x00400000             # game/FaceEnums.h FaceAttribute::IndoorSky
# MM9's placed thunder recordings (AmbientSound objects under Sounds\ambient\thunder: Sturmford 13, Thjorgard 14, the
# Afterworld 7), left out of a scene with weather: its storms play the same recordings with their lightning, and only
# while it rains (devdocs/INDOOR_OPEN_SKY.md "Weather").
THUNDER_SOUND_PREFIX = "ambient/thunder/"


def apply_weather(scene: dict, weather: str) -> None:
    """The outdoor weather over the scene's open sky (devdocs/INDOOR_OPEN_SKY.md "Weather"): `sky: {weather}`; the sky
    follows the weather instead of a fixed preset, and MM9's placed thunder gives way to the storms'."""
    if "sky" not in scene or weather in (None, "none"):
        return
    scene["sky"]["weather"] = weather
    scene["sky"].pop("preset", None)
    if scene.get("ambient_sounds"):
        scene["ambient_sounds"] = [s for s in scene["ambient_sounds"]
                                   if not str(s.get("sound", "")).lower().startswith(THUNDER_SOUND_PREFIX)]
        if not scene["ambient_sounds"]:
            del scene["ambient_sounds"]


PARTY_STEP = 50                     # native units the party steps up (IndoorMovementController.cpp MaximumRise)
HALF_STEP_MAX = 66                  # native: higher edges are walls, counters, platforms MM9's player cannot climb
HALF_STEP_DEPTH_LT = 20             # how far a half step reaches out (51 native: past a monster path step of 40)
SAMPLE_LT = 8
HALF_STEP_MIN_AREA_LT2 = 20000      # raised floors at least this big (a sidewalk, a stage): none onto counters, tables
STAND_IN_LT = 32                    # the raised floor must go on this far behind the edge (82 native: a party's width)
STAND_CLEAR_LT = 16                 # with no wall this close to that point (41 native: the party's radius is 37)
WALL_BODY_LT = (2, 60)              # walls that stand this high over the raised floor block standing there
STEP_OUT_LT = 2                     # from just outside the edge: a wall standing on the edge itself blocks too


def _flat_floors(polygons: list) -> list:
    return [p for p in polygons if p.role == "static" and p.normal[1] > 0.99]


class _FloorIndex:
    """The flat floors' plan boxes and heights as arrays: the half-step search asks 110 000 times (Thjorgard City) for
    the highest floor under a point, and testing every floor's box in Python took 26 s."""
    def __init__(self, floors: list):
        self.floors = floors
        self.low = np.array([p.points.min(0) for p in floors]).reshape(-1, 3)
        self.high = np.array([p.points.max(0) for p in floors]).reshape(-1, 3)
        self.height = np.array([float(p.points[0, 1]) for p in floors])

    def height_under(self, x: float, z: float, below: float) -> float | None:
        """The highest flat floor at (x, z) lower than `below` (LithTech)."""
        candidates = np.flatnonzero((self.low[:, 0] <= x) & (x <= self.high[:, 0]) & (self.low[:, 2] <= z)
                                    & (z <= self.high[:, 2]) & (self.height < below))
        for index in candidates[np.argsort(-self.height[candidates], kind="stable")]:
            pts = self.floors[index].points
            inside = False
            for i in range(len(pts)):
                x1, z1, x2, z2 = pts[i, 0], pts[i, 2], pts[(i + 1) % len(pts), 0], pts[(i + 1) % len(pts), 2]
                if (z1 > z) != (z2 > z) and x < x1 + (z - z1) / (z2 - z1) * (x2 - x1):
                    inside = not inside
            if inside:
                return float(self.height[index])
        return None


def _wall_segments(polygons: list) -> tuple[np.ndarray, np.ndarray]:
    """Plan footprints (x0, z0, x1, z1) and height ranges (y0, y1) of the solid and invisible walls (LithTech)."""
    segments, heights = [], []
    for p in polygons:
        if p.role not in ("static", "invisible") or abs(p.normal[1]) > 0.5:
            continue
        flat = p.points[:, [0, 2]]
        across = np.array([-p.normal[2], p.normal[0]])
        if np.linalg.norm(across) < 1e-6:
            continue
        along = flat @ (across / np.linalg.norm(across))
        segments.append(np.concatenate([flat[int(np.argmin(along))], flat[int(np.argmax(along))]]))
        heights.append((p.points[:, 1].min(), p.points[:, 1].max()))
    return np.array(segments, float).reshape(-1, 4), np.array(heights, float).reshape(-1, 2)


def _point_segment_distance(point: np.ndarray, segments: np.ndarray) -> np.ndarray:
    a, b = segments[:, :2], segments[:, 2:]
    ab = b - a
    t = np.clip(np.einsum("ij,ij->i", point - a, ab) / np.maximum(np.einsum("ij,ij->i", ab, ab), 1e-9), 0.0, 1.0)
    return np.linalg.norm(a + ab * t[:, None] - point, axis=1)


def _segments_cross(p: np.ndarray, q: np.ndarray, segments: np.ndarray) -> np.ndarray:
    a, b = segments[:, :2], segments[:, 2:]

    def side(o, u, v):
        return (u[..., 0] - o[..., 0]) * (v[..., 1] - o[..., 1]) - (u[..., 1] - o[..., 1]) * (v[..., 0] - o[..., 0])

    d1, d2 = side(a, b, p[None]), side(a, b, q[None])
    d3, d4 = side(p[None], q[None], a), side(p[None], q[None], b)
    return (d1 * d2 < 0) & (d3 * d4 < 0)


def half_steps(polygons: list) -> list:
    """Invisible half steps (a top and a riser) along the edges of flat floors that stand 50-66 native (19.5-26 LT)
    over the flat floor beside them: MM9's player steps up 40-48 LT, the party 50 native, so a 24 LT terrace shuts the
    party out (Dook's Castle's and Thjorad Mine's invisible steps, applied by rule). Each step is HALF_STEP_DEPTH_LT
    deep at half the rise. Only where the party can stand on the raised floor behind the edge: the floor goes on
    STAND_IN_LT behind it, no wall crosses that way (from just outside the edge: a wall on the edge counts) and
    none stands within STAND_CLEAR_LT of its end. MM9's building
    plinths (a 61-unit base whose walls stand 4 LT behind its edge, Sturmford's palace ring and north streets) and
    the fountains' rims get none."""
    floors = _flat_floors(polygons)
    under = _FloorIndex(floors)
    invisible = next((p for p in polygons if p.role == "invisible"), None)
    if invisible is None:
        return []
    wall_segments, wall_heights = _wall_segments(polygons)
    reach = STAND_IN_LT + STAND_CLEAR_LT + HALF_STEP_DEPTH_LT
    out = []
    for high in floors:
        if high.area < HALF_STEP_MIN_AREA_LT2:
            continue
        pts, h = high.points, float(high.points[0, 1])
        centre = pts.mean(0)
        standing = (wall_heights[:, 0] < h + WALL_BODY_LT[1]) & (wall_heights[:, 1] > h + WALL_BODY_LT[0])
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            edge = b[[0, 2]] - a[[0, 2]]
            length = float(np.linalg.norm(edge))
            if length < SAMPLE_LT * 2:
                continue
            along = edge / length
            normal = np.array([along[1], -along[0]])
            if normal @ (a[[0, 2]] - centre[[0, 2]]) < 0:
                normal = -normal
            lo = np.minimum(a[[0, 2]], b[[0, 2]]) - reach
            hi = np.maximum(a[[0, 2]], b[[0, 2]]) + reach
            near = standing & (np.maximum(wall_segments[:, 0], wall_segments[:, 2]) >= lo[0]) \
                & (np.minimum(wall_segments[:, 0], wall_segments[:, 2]) <= hi[0]) \
                & (np.maximum(wall_segments[:, 1], wall_segments[:, 3]) >= lo[1]) \
                & (np.minimum(wall_segments[:, 1], wall_segments[:, 3]) <= hi[1])
            walls = wall_segments[near]
            run, runs = None, []
            ts = np.arange(SAMPLE_LT / 2, length, SAMPLE_LT)
            for t in ts:
                point = a[[0, 2]] + along * t + normal * (HALF_STEP_DEPTH_LT / 2)
                low = under.height_under(point[0], point[1], h - 1)
                rise = None if low is None else (h - low) * SCALE
                ok = rise is not None and PARTY_STEP < rise <= HALF_STEP_MAX
                if ok:
                    # Another floor at this height beyond the edge (a riser inside a building's floor, over the
                    # street polygon under it) is no edge.
                    beside = under.height_under(point[0], point[1], h + 0.5)
                    ok = beside is not None and abs(beside - low) < 0.5
                if ok:
                    edge_point = a[[0, 2]] + along * t
                    inner = edge_point - normal * STAND_IN_LT
                    on_top = under.height_under(inner[0], inner[1], h + 0.5)
                    ok = on_top is not None and abs(on_top - h) < 0.5
                    if ok and len(walls):
                        ok = not _segments_cross(edge_point + normal * STEP_OUT_LT, inner, walls).any() \
                            and _point_segment_distance(inner, walls).min() >= STAND_CLEAR_LT
                if ok and run is not None and abs(run[2] - low) < 0.5:
                    run[1] = t
                elif ok:
                    if run is not None:
                        runs.append(run)
                    run = [t, t, low]
                elif run is not None:
                    runs.append(run)
                    run = None
            if run is not None:
                runs.append(run)
            for t0, t1, low in runs:
                t0, t1 = max(t0 - SAMPLE_LT / 2, 0.0), min(t1 + SAMPLE_LT / 2, length)
                if t1 - t0 < SAMPLE_LT:
                    continue
                mid = (low + h) / 2
                e0, e1 = a[[0, 2]] + along * t0, a[[0, 2]] + along * t1
                o0, o1 = e0 + normal * HALF_STEP_DEPTH_LT, e1 + normal * HALF_STEP_DEPTH_LT
                top = np.array([[e0[0], mid, e0[1]], [e1[0], mid, e1[1]], [o1[0], mid, o1[1]], [o0[0], mid, o0[1]]])
                riser = np.array([[o0[0], low, o0[1]], [o1[0], low, o1[1]], [o1[0], mid, o1[1]], [o0[0], mid, o0[1]]])
                for ring, want in ((top, np.array([0.0, 1.0, 0.0])), (riser, np.array([normal[0], 0.0, normal[1]]))):
                    face = Polygon(ring, [tuple(np.round(q, 1)) for q in ring], invisible.texture, invisible.mapping,
                                   invisible.flags, "CityHalfStep", "invisible")
                    if face.normal @ want < 0:
                        face = Polygon(ring[::-1].copy(), [tuple(np.round(q, 1)) for q in ring[::-1]],
                                       invisible.texture, invisible.mapping, invisible.flags, "CityHalfStep",
                                       "invisible")
                    face.notes.update(invisible.notes)
                    out.append(face)
    return out


class CityHooks(dungeon.Hooks):
    # the city and region scripts (citylua.py, regionlua.py) switch their AmbientSounds from their own trigger polls
    shared_ambient_triggers = False

    def edit_polygons(self, build, polygons: list) -> list:
        # The merged top portals look for sky faces over the roof line (structure.sky_over_roof_line).
        build.city_polygons = polygons
        # Opt-in (`city: {half_steps: true}`); proof and rules in CITY_PLAYBOOK.md "Raised floors".
        if not structure.settings_of(build.project).get("half_steps", False):
            return polygons
        steps = half_steps(polygons)
        build.stats["city_half_step_faces"] = len(steps)
        # Each step's top: centre (native), length along the edge (native), for probes (CITY_PLAYBOOK "Raised floors").
        build.stats["city_half_steps"] = [
            {"centre": [round(float(v)) for v in build.project.native(face.points.mean(0))],
             "length": round(float(np.ptp(face.points[:, [0, 2]], axis=0).max()) * SCALE)}
            for face in steps if face.normal[1] > 0.5]
        return polygons + steps

    def extra_portals(self, build) -> list:
        return structure.city_portals(build)

    def scene(self, build, scene: dict) -> None:
        settings = structure.settings_of(build.project)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        sky_alias = settings.get("sky_alias", "sky04").lower()
        sky = [f for f in blv["faces"] if str(f.get("texture_name", "")).lower() == sky_alias and not f["is_portal"]]
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f["index"], "legacy_attributes": int(f["attributes"]) | INDOOR_SKY} for f in sky)
        build.stats["sky_faces"] = len(sky)
        if settings.get("open_sky", True):
            block = {"mode": "open"}
            if settings.get("sky_texture"):
                block["sky_texture"] = settings["sky_texture"]
            # sky_preset: an Enhanced sky preset (the outdoor maps' high-definition skies: cloudy, fair, ...);
            # outdoor_view: the view as an outdoor map's, its view distance and the sky's haze instead of the scene
            # fog (devdocs/INDOOR_OPEN_SKY.md "Outdoor view"; 2026-11-01, the user's choice for the cities).
            if settings.get("sky_preset"):
                block["preset"] = settings["sky_preset"]
            if settings.get("outdoor_view"):
                block["view"] = "outdoor"
                # view_distance_scale: the share of the player's view distance setting (16 192 by default) the city
                # sees; 0.5 is 8 096 at the default (the user's choice, 2026-11-01).
                if settings.get("view_distance_scale"):
                    block["view_distance_scale"] = float(settings["view_distance_scale"])
            scene["sky"] = block
            # weather: rain | snow | rain_and_snow (the user's decision 2026-11-06: weather on the cities too)
            apply_weather(scene, settings.get("weather", "none"))
        # Opt-in (`city: {daylight: true}`): the sun and sky light on the sectors open to the sky, from MM9's data
        # (CITY_PLAYBOOK.md "Daylight and fog").
        if settings.get("daylight", False):
            scene["daylight"] = build.source.daylight()
            # With fog too, the fog colour (and so a fogged sky) darkens with the open air's light by the time of day
            # (scene fog `follow_daylight`, devdocs/INDOOR_FOG.md "Fog by the daylight"; 1 at noon): MM9 keeps its fog
            # and lighting the same at every hour, our daylight darkens the streets at night.
            if isinstance(scene.get("fog"), dict):
                scene["fog"]["follow_daylight"] = True
        # Footsteps by MM9's surface of each floor texture (footsteps.py): cobbles, earth, grass, wooden floors.
        import footsteps
        footsteps.apply(build, scene)

    def report(self, build) -> dict:
        return {"city": getattr(build, "city_report", None)}
