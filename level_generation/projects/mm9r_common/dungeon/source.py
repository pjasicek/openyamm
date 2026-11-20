"""
The map project and its DAT source: the per-map settings (`overrides.yml`, section `map`), the native frame, the DAT
world with its objects and texture aliases, and the classification of every DAT world model (static, mover or
skipped). See ../DUNGEON_PLAYBOOK.md.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
COMMON = Path(__file__).resolve().parents[1]
for extra in (ROOT / "tools/mm9_import_discovery", COMMON, ROOT / "util"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import lt_rotation_to_openyamm_yaw_degrees, read_dat_world  # noqa: E402

from .geometry import Polygon, poly_ring  # noqa: E402

LT_SOLID, LT_INVISIBLE = 0x1, 0x4
LT_SKY = 0x10                       # LithTech surface flag: a sky portal (MM9 draws its sky box through it)
SKY_MARKER = "textures\\skybox\\skymarker.dtx"     # MM9's sky texture; overrides.yml `textures` gives it an alias
# DAT world models that never become geometry: AI navigation tracks, the visibility hull (its UserPortals are read
# for the doorways), perception hints and ladder volumes. LadderBlocker* is kept (invisible collision).
SKIPPED_MODELS = ("AITrk", "VisBSP", "PerceptionBrush", "Ladder")
KEPT_PREFIXES = ("LadderBlocker",)
SEED_CLASSES = {"StartPoint", "Light", "TreasureChest", "Trigger"}
# MM9 editor helper textures, never drawn whatever the surface flags say: Invisible.dtx and Misc\\Firethrough.dtx (the
# magenta "FIRE THROUGH" marker of collision that lets projectiles pass; 7 of Lindisfarne's polygons carry it without
# the invisible flag, 0x109, and drew as magenta until 2026-10-31).
HELPER_TEXTURES = ("invisible", "firethrough")
# How steeply MM9's city lightmaps take their StaticSunLight (scene daylight `sun_gain`): faces turned away hold exactly
# the AmbientLight, and the unshadowed texels of nearly every face turned toward it saturate at 255, already from
# N.L 0.05-0.2 (90th percentile per polygon; Thjorgard and Sturmford City, 2026-10-31, CITY_PLAYBOOK "Daylight and
# fog"). min(1, 4 N.L) reproduces that on top of an ambient of about 0.3.
MM9_SUN_GAIN = 4.0


@dataclass
class Project:
    """One map project: its directory and the `map` section of its overrides.yml."""
    directory: Path
    stem: str
    dat: Path
    display_name: str
    starts: list
    monster_classes: set
    offset: tuple = (0, 0, 0)
    voxel: int = 16
    ambient: int = 20
    ceiling: int = 1024
    seed_classes: set = field(default_factory=lambda: set(SEED_CLASSES))
    old_map: str = ""
    overrides: dict = field(default_factory=dict)
    work: Path = None
    source_dir: Path = None
    install: bool = True

    @classmethod
    def load(cls, directory: Path, work: Path | None = None, install: bool = True) -> "Project":
        directory = Path(directory).resolve()
        overrides = yaml.safe_load((directory / "overrides.yml").read_text())
        settings = overrides["map"]
        stem = settings["stem"]
        project = cls(directory=directory, stem=stem,
                      dat=ROOT / "mm9/extracted/WORLDS/WORLDS" / settings.get("dat", f"{stem.upper()}.dat"),
                      display_name=settings["display_name"], starts=list(settings["starts"]),
                      monster_classes=set(settings.get("monster_classes", [])),
                      offset=tuple(settings.get("offset", (0, 0, 0))), voxel=int(settings.get("voxel", 16)),
                      ambient=int(settings.get("ambient", 20)), ceiling=int(settings.get("ceiling", 1024)),
                      old_map=settings.get("old_map", f"{stem}.odm"), overrides=overrides, install=install)
        project.seed_classes |= set(settings.get("extra_seed_classes", []))
        project.work = Path(work) if work else directory / "work"
        project.source_dir = (project.work / "source") if work else directory / "source"
        return project

    @property
    def map(self) -> str:
        return f"{self.stem}.blv"

    @property
    def aliases(self) -> Path:
        return ROOT / f"assets_editor_dev/worlds/mm9/maps/{self.stem}.material_aliases.yml"

    def native(self, points) -> np.ndarray:
        """LithTech (x, y up, z) to native (x, y, z up), scaled, in floats."""
        points = np.asarray(points, float)
        return np.stack([points[..., 0] * SCALE - self.offset[0], points[..., 2] * SCALE - self.offset[1],
                         points[..., 1] * SCALE - self.offset[2]], axis=-1)

    def lt_from_native(self, point) -> np.ndarray:
        x, y, z = point
        return np.array([(x + self.offset[0]) / SCALE, (z + self.offset[2]) / SCALE, (y + self.offset[1]) / SCALE],
                        float)


def lt_vector_to_native(vector) -> np.ndarray:
    return np.array([vector[0], vector[2], vector[1]], float)


def yaw_degrees(rotation) -> float:
    """The old importer's yaw (-ry): right for prop models (their bake and placements use it), a quarter turn off for
    the way an object faces."""
    return lt_rotation_to_openyamm_yaw_degrees(rotation or [0, 0, 0, 0])


def facing_degrees(rotation) -> float:
    """The native yaw an MM9 object faces: LithTech objects face +z, rotated by ry about y, i.e. (sin ry, cos ry) in
    LT (x, z) = native (x, y), so yaw = 90 - ry. Starts and actors use this (the old importer's -ry turned a south-
    facing start to the west)."""
    ry = float((rotation or [0, 0, 0, 0])[1]) if len(rotation or []) > 1 else 0.0
    return (90.0 - np.degrees(ry)) % 360.0


class Source:
    """The DAT world: models by name, objects (index, class, name, properties) and the texture aliases."""
    def __init__(self, project: Project):
        self.project = project
        self.world = read_dat_world(project.dat)
        self.models = {model.name: model for model in self.world.world_models}
        self.objects = []
        for index, world_object in enumerate(self.world.objects):
            properties = {p.name: p.value for p in world_object.properties}
            self.objects.append({"index": index, "class": world_object.name, "name": str(properties.get("Name", "")),
                                 "properties": properties})
        self.by_name = {o["name"].lower(): o for o in self.objects}
        aliases = yaml.safe_load(project.aliases.read_text())["textures"]
        self.aliases = {entry["source_texture"].lower(): entry for entry in aliases}
        # overrides.yml `textures`: MM9 source textures the old import gave no alias (sky markers), or that should
        # draw another texture: {source texture: {alias, width, height}} (an alias in worlds/mm9/textures).
        for texture, entry in (project.overrides.get("textures") or {}).items():
            self.aliases[texture.lower()] = dict(entry, source_texture=texture)

    def polygons(self, model_name: str) -> list[Polygon]:
        model = self.models[model_name]
        result = []
        for poly in model.polies:
            ring = poly_ring(poly)
            if len(ring) < 3:
                continue
            surface = model.surfaces[poly.surface_index]
            texture = model.textures[surface.texture_index]
            points = np.array([model.points[i] for i in ring], float)
            invisible = bool(surface.flags & LT_INVISIBLE) or \
                Path(texture.replace("\\", "/")).stem.lower() in HELPER_TEXTURES
            solid = bool(surface.flags & LT_SOLID)
            if invisible and not solid:
                continue
            role = "invisible" if invisible else ("static" if solid else "nonsolid")
            polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], texture,
                              (np.array(surface.uv_origin), np.array(surface.uv_u), np.array(surface.uv_v)),
                              surface.flags, model_name, role)
            alias = self.aliases[texture.lower()]
            polygon.notes.update(width=alias["width"], height=alias["height"])
            if polygon.area > 0.5:
                result.append(polygon)
        return result

    def sky_flagged_as_sky(self, polygons: list) -> int:
        """A visible polygon with LithTech's sky flag is a sky portal whatever its texture: MM9 draws its sky box
        through it. Each takes the sky marker's texture, so it becomes a sky face like the skymarker polygons. This
        applies only on a map whose overrides.yml `textures` gives the marker an alias, because that alias says how
        the map draws its sky. The flagged polygons include Thjorgard City's hillside north wall (a 5 000-unit
        thjorcolumn wall where the other sides are sky), Frosgard City's sky floor, Sturmford's and Frosgard's
        grass and terrain lids, and Wizard's Lab's "Default" tower top. Polygons whose texture already has the
        marker's alias (Guberland City's greenscreen sky shell) keep their texture. Returns the count."""
        if SKY_MARKER not in {str(k).lower() for k in (self.project.overrides.get("textures") or {})}:
            return 0
        marker = self.aliases[SKY_MARKER]
        count = 0
        for polygon in polygons:
            if not polygon.flags & LT_SKY or polygon.role == "invisible":
                continue
            if str(self.aliases[polygon.texture.lower()].get("alias")).lower() == str(marker.get("alias")).lower():
                continue
            polygon.texture = marker["source_texture"]
            polygon.notes.update(width=marker["width"], height=marker["height"])
            count += 1
        return count

    def fog(self) -> dict | None:
        """The scene's `fog` (devdocs/INDOOR_FOG.md): MM9's map-wide fog, from WorldProperties `EnableFog`, else a `Fog`
        object that starts on (a point controller, no brush: map-wide until something switches it, which only
        `WeatherMan` does). Linear near to far, LT distances x 2.56. overrides.yml `map: {fog: false}` leaves it out;
        `map: {fog: lithtech}` (opt-in, the cities) adds MM9's own fog model (`model: lithtech`: view depth, MM9's two
        passes) and the WeatherMan's night state (`night`, below)."""
        setting = self.project.overrides["map"].get("fog", True)
        if setting is False:
            return None
        settings = [o["properties"] for o in self.objects
                    if o["class"] == "WorldProperties" and o["properties"].get("EnableFog")]
        settings += [o["properties"] for o in self.objects if o["class"] == "Fog" and o["properties"].get("StartOn")
                     and o["properties"].get("FogEnable")]
        if not settings:
            return None
        p = settings[0]
        block = self._fog_state(p)
        sky_fog = bool(self.project.overrides["map"].get("sky_fog", False))
        if sky_fog and self.sky_fogged(p):
            block["sky"] = 1
        if setting == "lithtech":
            block["model"] = "lithtech"
            night = self.night_fog(p)
            if night:
                if sky_fog and self.sky_fogged(self._night_fog_properties(p)):
                    night["sky"] = 1
                block["night"] = night
        return block

    def sky_fogged(self, p: dict) -> bool:
        """Whether MM9 draws its sky box wholly in the fog colour under the fog state `p` (overrides.yml
        `map: {sky_fog: true}`, devdocs/INDOOR_FOG.md "The sky in fog"). With fog on, d3d.ren fogs the sky box's
        vertices by their depth in sky space from SkyFogNearZ (0x100092b0, the sky pass 0x10016d0c); MM9's client copies
        the state's SkyFogNearZ into both SkyFogNearZ and SkyFogFarZ (cshell.dll 0x10083433), and no binary reads
        WorldProperties `SkyFog`. The box (DemoSkyWorldModel SkyDims, the sky camera within InnerPercent of its
        centre) is at least SkyDims x (1 - InnerPercent) deep, so a state whose SkyFogNearZ is nearer leaves the whole
        sky in the fog colour (Frosgard City 48, Thjorgard City's day fog 0, box 128 x 0.9); one past it (99999) leaves
        it clear."""
        boxes = [o["properties"] for o in self.objects if o["class"] == "DemoSkyWorldModel"]
        depths = [float(d) * (1.0 - float(box.get(f"InnerPercent{axis}", 0.0)))
                  for box in boxes for d, axis in zip(box.get("SkyDims", []), "XYZ") if float(d) > 0]
        if not depths:
            return False
        return float(p.get("SkyFogNearZ", 1e9)) < min(depths)

    def _night_fog_properties(self, day: dict) -> dict:
        """The DAT properties of the night state night_fog found for `day`."""
        for o in self.objects:
            p = o["properties"]
            if o["class"] != "WeatherMan" or not p.get("StartOn") or not p.get("TurnOffAtNight"):
                continue
            on = self.by_name.get(str(p.get("FogOn", "")).lower())
            off = self.by_name.get(str(p.get("FogOff", "")).lower())
            if on is not None and on["properties"] is day and off is not None and off["class"] == "Fog":
                return off["properties"]
        return {}

    @staticmethod
    def _fog_state(p: dict) -> dict:
        return {"color_rgb": [int(round(c)) for c in p["FogColor"]],
                "near_distance": round(float(p["FogNearZ"]) * SCALE, 2),
                "far_distance": round(float(p["FogFarZ"]) * SCALE, 2)}

    def night_fog(self, day: dict) -> dict | None:
        """MM9's night fog: a WeatherMan that starts on with `TurnOffAtNight` switches from its FogOn state (the day's
        fog, `day`) to its FogOff state after dark (Thjorgard City: grey Fog0 by day, black Fog1 at night). None when
        no such WeatherMan names the day's fog, or its FogOff state has no fog."""
        for o in self.objects:
            p = o["properties"]
            if o["class"] != "WeatherMan" or not p.get("StartOn") or not p.get("TurnOffAtNight"):
                continue
            on = self.by_name.get(str(p.get("FogOn", "")).lower())
            off = self.by_name.get(str(p.get("FogOff", "")).lower())
            if on is None or on["properties"] is not day or off is None or off["class"] != "Fog":
                continue
            if off["properties"].get("FogEnable"):
                return self._fog_state(off["properties"])
        return None

    def daylight(self) -> dict:
        """The scene's `daylight` (devdocs/INDOOR_OPEN_SKY.md "Daylight", city `daylight: true`) from MM9's own data:
        `ambient_rgb` the WorldInfo string's AmbientLight (MM9's lightmaps hold exactly it in shade: Thjorgard City 82,
        Sturmford City 66 on 50 % of their street texels), `sun_rgb` the StaticSunLight's InnerColor x BrightScale (the
        lightmaps saturate at 255 where it falls; white when a map has none), `day_scale_rgb` / `night_scale_rgb` the
        WorldProperties LightScale / NightLightScale (in MM9 itself d3d.ren turns the light scale into an identity
        table, so its world light never changes with the hour; we use the authored night tint for our nights);
        `sun_direction` the StaticSunLight's direction (MM9 lit the city from there at every hour) and `sun_gain`
        MM9_SUN_GAIN."""
        match = re.search(r"ambientlight\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", self.world.world_info.properties, re.I)
        ambient = [min(255, int(round(float(v)))) for v in match.groups()] if match else [0, 0, 0]
        sun = [255, 255, 255]
        suns = [o["properties"] for o in self.objects if o["class"] == "StaticSunLight"]
        if suns:
            scale = float(suns[0].get("BrightScale", 1.0))
            sun = [min(255, int(round(float(c) * scale))) for c in suns[0].get("InnerColor", [255, 255, 255])]
        world = next((o["properties"] for o in self.objects if o["class"] == "WorldProperties"), {})
        day = [min(255, int(round(float(c)))) for c in world.get("LightScale", [255, 255, 255])]
        night = [min(255, int(round(float(c)))) for c in world.get("NightLightScale", [255, 255, 255])]
        block = {"ambient_rgb": ambient, "sun_rgb": sun, "day_scale_rgb": day, "night_scale_rgb": night,
                 "sun_gain": MM9_SUN_GAIN}
        if suns:
            # The StaticSunLight shines along its forward vector (LithTech Euler pitch, yaw: pitch down from the
            # horizon); the scene takes the direction toward the sun, in native axes.
            pitch, yaw = (float(v) for v in suns[0]["Rotation"][:2])
            forward = np.array([np.sin(yaw) * np.cos(pitch), -np.sin(pitch), np.cos(yaw) * np.cos(pitch)])
            block["sun_direction"] = [round(float(v), 4) for v in lt_vector_to_native(-forward)]
        return block

    def model_lighting(self) -> dict | None:
        """The scene's `model_lighting` (devdocs/INDOOR_MODEL_LIGHTING.md): MM9's lighting of its models for the
        decorations and actors, opt-in by overrides.yml `map: {model_lighting: true}` (or a map of `light_scale` and
        `add` to override). `ambient` is the WorldInfo string's `AmbientLight r g b` (0 0 0 when absent, as MM9's light
        table), `add` MM9's ModelAdd 30 30 30 (autoexec.cfg). Off by default."""
        setting = self.project.overrides["map"].get("model_lighting", False)
        if not setting:
            return None
        match = re.search(r"ambientlight\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", self.world.world_info.properties, re.I)
        ambient = [min(255, int(round(float(v)))) for v in match.groups()] if match else [0, 0, 0]
        block = {"mode": "mm9", "ambient": ambient, "add": [30, 30, 30]}
        if isinstance(setting, dict):
            block.update({key: setting[key] for key in ("add", "light_scale") if key in setting})
        return block

    def object_class(self, name: str) -> str | None:
        found = self.by_name.get(name.lower())
        return found["class"] if found else None

    def properties(self, name: str) -> dict:
        return self.by_name[name.lower()]["properties"]


def classify_models(source: Source) -> dict:
    """Every world model: static geometry, a mover (its group and motion), a monster barrier or skipped, with the
    reason. A model with no rule in overrides.yml stops the build (every DAT model is an explicit decision), except
    MM9's AIBarrier brushes: monster-only walls by rule (Build.actor_barriers), or skipped with
    `map: {actor_barriers: false}`."""
    overrides = source.project.overrides
    plan = {"static": [], "movers": {}, "skipped": {}, "barriers": []}
    barriers = overrides["map"].get("actor_barriers", True)
    for model in source.world.world_models:
        name = model.name
        cls = source.object_class(name)
        if name in ("PhysicsBSP",):
            plan["static"].append(name)
            continue
        if name.startswith(SKIPPED_MODELS) and not name.startswith(KEPT_PREFIXES):
            plan["skipped"][name] = cls or "helper"
            continue
        if cls == "AIBarrier":
            # One that starts off (StartOn 0: Verhoffin Ruins' saw blade barrier, the Chasm's AIBarrier21) is skipped:
            # nothing switches barriers on here
            obj = source.by_name.get(name.lower())
            if barriers and (obj is None or obj["properties"].get("StartOn", 1)):
                plan["barriers"].append(name)
            else:
                plan["skipped"][name] = cls
            continue
        rule = (overrides.get("models") or {}).get(name)
        if rule is None:
            for pattern, value in (overrides.get("model_patterns") or {}).items():
                if name.startswith(pattern):
                    rule = value
                    break
        if rule is None:
            raise SystemExit(f"world model {name} ({cls}) has no rule in overrides.yml")
        if rule == "static":
            plan["static"].append(name)
        elif rule == "skip":
            plan["skipped"][name] = cls
        else:
            plan["movers"][name] = rule
    # MM9 moves a door's DoubleDoorName partner with it (BaseDoor); a pair split over two groups opens one leaf per
    # click (Bootcamp's sliding Door0/Door1, 2026-11-07). Pairs a map script drives itself may stay split.
    split = []
    for name, rule in plan["movers"].items():
        obj = source.by_name.get(name.lower())
        other = str((obj or {}).get("properties", {}).get("DoubleDoorName") or "")
        partner = next((m for m in plan["movers"] if m.lower() == other.lower()), None)
        if partner is not None and name < partner and rule.get("group") != plan["movers"][partner].get("group"):
            split.append(f"{name}/{partner}")
    if split:
        print(f"note: DoubleDoorName pairs in different mover groups (one leaf per click unless scripted): {split}")
    return plan


def surface_column(polygons: list[Polygon], x: float, z: float) -> list[tuple[float, Polygon]]:
    """Every polygon over or under the plan point (LithTech x, z) that is not a wall, with its height there, lowest
    first (Content.actor_floor)."""
    out = []
    for polygon in polygons:
        pts = polygon.points
        if not (pts[:, 0].min() <= x <= pts[:, 0].max() and pts[:, 2].min() <= z <= pts[:, 2].max()):
            continue
        n = polygon.normal
        if abs(n[1]) < 0.02:
            continue
        inside = False
        count = len(pts)
        for i in range(count):
            x1, z1, x2, z2 = pts[i, 0], pts[i, 2], pts[(i + 1) % count, 0], pts[(i + 1) % count, 2]
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) / (z2 - z1) * (x2 - x1):
                inside = not inside
        if inside:
            out.append((float((n @ pts[0] - n[0] * x - n[2] * z) / n[1]), polygon))
    return sorted(out, key=lambda entry: entry[0])


def floor_below(polygons: list[Polygon], point_lt) -> float | None:
    """The highest floor under a point (LithTech y), for snapping starts, arrivals, actors and pads."""
    x, y, z = point_lt
    best = None
    for polygon in polygons:
        if polygon.normal[1] < 0.7 or polygon.role != "static":
            continue
        pts = polygon.points
        if not (pts[:, 0].min() <= x <= pts[:, 0].max() and pts[:, 2].min() <= z <= pts[:, 2].max()):
            continue
        inside = False
        count = len(pts)
        for i in range(count):
            x1, z1, x2, z2 = pts[i, 0], pts[i, 2], pts[(i + 1) % count, 0], pts[(i + 1) % count, 2]
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) / (z2 - z1) * (x2 - x1):
                inside = not inside
        if not inside:
            continue
        n = polygon.normal
        height = (n @ pts[0] - n[0] * x - n[2] * z) / n[1]
        if height <= y + 1 and (best is None or height > best):
            best = height
    return best


class FloorsBelow:
    """floor_below over one polygon list for many points: the floors it considers (static, normal y >= 0.7) and their
    plan boxes found once, so each point tests only the floors whose box holds it (the same tests; a map's population
    report asked once per monster and chest over every polygon: 6 s on the Lich Lab)."""
    def __init__(self, polygons: list[Polygon]):
        self.floors = [p for p in polygons if not (p.normal[1] < 0.7 or p.role != "static")]
        self.low = np.array([(p.points[:, 0].min(), p.points[:, 2].min()) for p in self.floors]).reshape(-1, 2)
        self.high = np.array([(p.points[:, 0].max(), p.points[:, 2].max()) for p in self.floors]).reshape(-1, 2)

    def __call__(self, point_lt) -> float | None:
        x, _, z = point_lt
        near = np.flatnonzero((self.low[:, 0] <= x) & (x <= self.high[:, 0]) & (self.low[:, 1] <= z)
                              & (z <= self.high[:, 1]))
        return floor_below([self.floors[i] for i in near], point_lt)
