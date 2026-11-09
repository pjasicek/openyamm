"""
Lights: MM9's point lights (class Light; DirLights only fed MM9's lightmap bake) as native BLV point lights, radius x
2.56, colour as authored (or x BrightScale, opt-in below), taken smallest first while no floor point is under more than
MAX_LIGHTS_PER_POINT; and the coverage check that also counts the decorations that carry a light.

BrightScale (overrides.yml `map: {bright_scale_lights: true}`, CITY_PLAYBOOK "Street lights and BrightScale"): MM9's
preprocessor bakes a Light into the lightmaps at LightColor x BrightScale (Processor.exe reads the key, LithTech
LightMapMaker `m_InnerColor * m_BrightScale`; MM9's own lightmaps rise in proportion to it, 2026-10-31), while the
runtime never reads it (models get the full colour, MM9_RENDER_LIGHTING_RE.md). A BLV light lights our faces, as the
lightmap did, so the opt-in writes the colour x BrightScale (0..255).
"""

from __future__ import annotations

import numpy as np

from .geometry import Polygon, sample_polygon
from .package import room_id
from .source import SCALE

MAX_LIGHTS_PER_POINT = 4


def floor_points(project, polygons: list[Polygon]) -> np.ndarray:
    floor_samples = np.concatenate([sample_polygon(p.points, 96) for p in polygons if p.normal[1] > 0.7])
    return project.native(floor_samples) + np.array([0, 0, 64])


def build_lights(source, polygons: list[Polygon], package, rooms, skip: set = frozenset()) -> list[dict]:
    """MM9's class Light objects as native lights, kept in order of their reach (the small torch and brazier lights
    first) while no floor point is under more than four. `skip`: light names overrides.yml leaves out."""
    project = source.project
    bright_scale = bool(project.overrides["map"].get("bright_scale_lights", False))
    floor_native = floor_points(project, polygons)
    candidates = []
    # MM9 reuses a light's name (Wizard's Lab's six "button <colour>" pairs): those take their DAT index too, so each
    # light keeps a marker node of its own
    names = [o["name"] for o in source.objects if o["class"] == "Light"]
    for o in source.objects:
        if o["class"] != "Light":
            continue
        p = o["properties"]
        radius = float(p.get("LightRadius", 300)) * SCALE
        colour = [int(round(c)) for c in p.get("LightColor", [255, 255, 255])]
        scale = float(p.get("BrightScale", 1.0))
        if bright_scale:
            colour = [min(255, max(0, int(round(c * scale)))) for c in colour]
        candidates.append({"name": o["name"] if names.count(o["name"]) == 1 else f"{o['name']}_{o['index']}",
                           "position_lt": p["Pos"],
                           "position": project.native(p["Pos"]).round().tolist(),
                           "radius": int(round(radius)), "colour": colour,
                           "bright_scale": scale})
    coverage = np.zeros(len(floor_native), np.int32)
    lights = []
    for light in sorted(candidates, key=lambda l: (l["radius"], l["name"])):
        if light["name"] in skip:
            light["kept"] = False
            light["reason"] = "left out in overrides.yml"
            lights.append(light)
            continue
        reach = np.linalg.norm(floor_native - np.array(light["position"]), axis=1) <= light["radius"]
        if (coverage[reach] >= MAX_LIGHTS_PER_POINT).any():
            light["kept"] = False
            light["reason"] = "a floor point already under four lights"
            lights.append(light)
            continue
        coverage[reach] += 1
        light["kept"] = True
        light["room"] = room_id(rooms.owner(np.array(light["position_lt"], float)))
        node = "LIGHT_" + light["name"]
        package.marker(node, np.array(light["position"], float), package.marker_material())
        package.room_nodes[light["room"]].append(node)
        package.metadata["lights"].append({"id": light["name"], "source_node": node, "color": light["colour"],
                                           "radius": light["radius"], "brightness": 31, "type": "point"})
        lights.append(light)
    return lights


def light_coverage(project, polygons: list[Polygon], lights: list[dict], decoration_lights: list) -> dict:
    """Floor points under more than four lights, counting the kept BLV lights and the decorations that carry a light
    (decoration_lights: [(native position, radius)])."""
    floor_native = floor_points(project, polygons)
    sources = [(np.array(l["position"], float), l["radius"]) for l in lights if l["kept"]]
    sources += [(np.asarray(position, float), radius) for position, radius in decoration_lights]
    coverage = np.zeros(len(floor_native), np.int32)
    for position, radius in sources:
        coverage += np.linalg.norm(floor_native - position, axis=1) <= radius
    return {"lights": len(sources), "max_per_floor_point": int(coverage.max()),
            "points_over_four": int((coverage > MAX_LIGHTS_PER_POINT).sum())}


PULSING_LIGHT_KEY_BASE = 40000


def pulsing_lights(source, project) -> list[dict]:
    """MM9's GlowingLight objects (Wizard's Lab, the Lich Lab) as the scene's `pulsing_lights`
    (devdocs/INDOOR_PULSING_LIGHTS.md): colour as authored, intensity and radius (x 2.56) between their min and max at
    their frequency and phase, MM9's StartOn; key PULSING_LIGHT_KEY_BASE + the DAT index (evt.SetLight(key, on) for
    MM9's On/Off triggers)."""
    out = []
    for o in source.objects:
        if o["class"] != "GlowingLight":
            continue
        p = o["properties"]
        out.append({
            "key": PULSING_LIGHT_KEY_BASE + o["index"],
            "position": [round(float(v)) for v in project.native(p["Pos"])],
            "color": [int(round(float(c))) for c in p.get("Color", [255, 255, 255])],
            "intensity": [round(float(p.get(k, d)), 3) for k, d in (("IntensityMin", 1), ("IntensityMax", 1),
                                                                    ("IntensityFreq", 0), ("IntensityPhase", 0))],
            "radius": [round(float(p.get("RadiusMin", 0)) * SCALE, 1), round(float(p.get("RadiusMax", 0)) * SCALE, 1),
                       round(float(p.get("RadiusFreq", 0)), 3), round(float(p.get("RadiusPhase", 0)), 3)],
            "start_on": bool(p.get("StartOn", 1)),
        })
    return [light for light in out if light["radius"][1] > 0]


def perception_lights(source, project) -> tuple[list[dict], dict]:
    """MM9's PerceptionLights (Dark Passageway 61, Thjorad Mine 10, Verhoffin Ruins 4): red hint lights of class
    PerceptionLight -> PerceptionBase, like the PerceptionBrush hints shown only to a party whose Perception reaches
    PerceptionValue, and switched by On/Off messages. Each is a scene `pulsing_lights` entry with a constant intensity
    and radius (LightRadius x 2.56), off at the start (key PULSING_LIGHT_KEY_BASE + the DAT index, the GlowingLights'
    key space); the map Lua (objects.shared_lines) switches it with evt.SetLight. A dynamic light, so a baked map keeps
    it out of its lightmaps (devdocs/INDOOR_PULSING_LIGHTS.md "Perception lights"). Returns (scene entries,
    {key: PerceptionValue})."""
    from .objects import _number
    out, values = [], {}
    for o in source.objects:
        if o["class"] != "PerceptionLight":
            continue
        p = o["properties"]
        radius = round(float(p.get("LightRadius", 0) or 0) * SCALE, 1)
        if radius <= 0:
            continue
        key = PULSING_LIGHT_KEY_BASE + o["index"]
        out.append({
            "key": key,
            "position": [round(float(v)) for v in project.native(p["Pos"])],
            "color": [int(round(min(max(float(c), 0), 255))) for c in p.get("Color", [255, 0, 0])],
            "intensity": [1.0, 1.0, 0.0, 0.0],
            "radius": [radius, radius, 0.0, 0.0],
            "start_on": False,
        })
        values[key] = int(round(_number(p.get("PerceptionValue"))))
    return out, values

