"""Expose OpenYAMM's authored YAML and PNGs to the existing preview renderer.

Coordinates and sizes are converted from OpenYAMM Z-up units to the viewer's
native MM9 Y-up units. No independent effect recipes live in the viewer.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets_dev"
DIRECTORY = ASSETS / "engine/effects/authored"


def vector(value, scale=1):
    return [value[0] * scale, value[2] * scale, value[1] * scale]


def load_authored():
    library = yaml.safe_load((DIRECTORY / "library.yml").read_text())
    bindings = yaml.safe_load((DIRECTORY / "resource_bindings.yml").read_text())
    if library["schema"] != "openyamm.effectLibrary.v1" or bindings["schema"] != "openyamm.effectResourceBindings.v1":
        raise ValueError("Unsupported authored effect schema")
    paths = {}
    for binding in bindings["bindings"]:
        if binding["status"] != "bound":
            raise ValueError("Unbound authored resource: " + binding["resource"])
        path = (ASSETS / binding["asset"]).resolve()
        if not path.is_relative_to(ASSETS.resolve()) or not path.is_file():
            raise ValueError("Invalid authored asset path: " + binding["asset"])
        if binding["resource"] in paths:
            raise ValueError("Duplicate authored resource: " + binding["resource"])
        paths[binding["resource"]] = path
    sprites, textures, effects = {}, {}, []
    for binding in bindings["bindings"]:
        if binding["kind"] != "sprite":
            continue
        resource = binding["resource"]
        descriptor = yaml.safe_load(paths[resource].read_text())
        if descriptor["schema"] != "openyamm.effectSprite.v2" or descriptor["id"] != resource:
            raise ValueError("Invalid authored sprite: " + resource)
        sprites[resource] = dict(frames=descriptor["frames"], frame_ms=1000/descriptor["framesPerSecond"],
                                logicalWidth=descriptor["logicalWidth"], logicalHeight=descriptor["logicalHeight"])
        for frame in descriptor["frames"]:
            textures[frame] = paths[frame]
    for effect in library["effects"]:
        if effect["compatibility_profile"] != "predictable":
            raise ValueError("Authored viewer expects predictable timing")
        keys = []
        for component in effect["components"]:
            kind = component["type"]
            if kind == "ribbon" or component.get("emission_distance", 0) > 0:
                # Projectile trails (ribbons, and emitters that shed by distance travelled) only draw when the effect
                # moves, which the preview does not do; it shows the rest of the effect.
                continue
            if kind not in ("sprite", "sprite_system"):
                raise ValueError("Authored preview does not yet support " + kind)
            if component.get("particle_space", "world") != "world" or "linked_component_id" in component:
                raise ValueError("Authored preview does not yet support attachments or local particles")
            if component.get("rotation_per_tick", [0, 0, 0]) != [0, 0, 0]:
                raise ValueError("Authored preview does not yet support emitter rotation")
            resource = component["sprite_resource"]
            if resource not in sprites:
                raise ValueError("Missing authored sprite: " + resource)
            p = dict(Sprite="SPR|" + resource, Offset=vector(component.get("offset", [0, 0, 0]), 1/2.56),
                     Blend=component.get("blend", "additive" if kind == "sprite" else "alpha"),
                     StretchU=component.get("stretch_u", 1), StretchV=component.get("stretch_v", 1))
            if p["Blend"] not in ("alpha", "additive", "multiply"):
                raise ValueError("Unknown authored blend")
            if component.get("alignment", "camera_facing") == "world_plane":
                p.update(PlaneRight=vector(component["plane_right"]), PlaneUp=vector(component["plane_up"]))
            if kind == "sprite_system":
                shapes = ["point", "plane", "sphere", "plane_in", "plane_out", "cone", "circle"]
                p.update(EmissionType=shapes.index(component["emission_shape"]),
                         Radius=component.get("radius", 0)/2.56, Velocity=component.get("velocity", 0)/2.56,
                         PlaneDir=vector(component.get("plane_direction", [0, 1, 0])),
                         WindDir=vector(component.get("wind_direction", [0, 0, 0])),
                         WindAmount=component.get("wind_amount", 0)/2.56,
                         EmissionInterval=component.get("emission_interval_seconds", 0),
                         SpritesPerEmission=component.get("sprites_per_emission", 1),
                         SpriteLifespan=component.get("particle_lifetime_seconds", 1))
            props = [dict(name=name, type=0, value=value) for name, value in p.items()]
            props += [dict(name="Ck", type=0, value=dict(time=k["time"],
                      rgb_transparency=k["rgb"] + [k["transparency"]])) for k in component["color_keys"]]
            props += [dict(name="Sk", type=0, value=[k["time"], k["value"] / 2.56])
                      for k in component["scale_keys"]]
            props += [dict(name="Mk", type=0, value=[k["time"], *vector(k["value"], 1/2.56)])
                      for k in component["motion_keys"]]
            keys.append(dict(id=component["id"], component_ref="Sprite" if kind == "sprite" else "SpriteSystem",
                             start=component["start_seconds"], end=component["end_seconds"],
                             repeat=component.get("repeat_count", 1), linked=False, properties=props))
        effects.append(dict(name=effect["id"], display_name=effect.get("display_name", effect["id"]),
                            source="authored", compatibility_profile="predictable", keys=keys,
                            phase_ms=effect["duration_seconds"]*1000))
    return effects, sprites, textures
