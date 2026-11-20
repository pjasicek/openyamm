"""MM9's destructible brushes and props as the scene's `destructibles` (devdocs/INDOOR_DESTRUCTIBLES.md).

A DestructableBrush whose faces stay static gets a face cog of its own (COG_BASE + its DAT object index, unless a map
hook gave its faces one); a DestructableProp's decoration gets a SetSprite key (the same number, unless a map hook gave
it one: content.Content.props). Each becomes one scene entry keyed by its DAT object index, the id map Lua uses
(evt.DamageDestructible(index, n), evt.DestroyDestructible(index), evt.SetDestructibleDamage(index, on),
evt.IsDestructibleDestroyed(index)), with MM9's HitPoints (at least 1), CanDamage and TriggerDestroyOnly, its CustomSound
or its debris material's, and that material's breaking effect at its centre, sized to it. A map hook binds map events
to its death and damage: `destructible_events(build)` -> {DAT name: (destroyed event, damaged event)} (0: none); MM9's
Death/DamageTrigger messages are each map's own to translate.

Brushes that become movers (a map's door rules) keep that route: no entry. A rule `motion: break` (overrides.yml
models) is the breakable route for a brush a map used to drop as a click mover (build_breakables): the brush keeps the
mover's place in the plan (not solid in the voxel pass, its `doorway` portal), its faces are static faces of its owner
room carrying its cog, and it is a scene entry like any other; `click` (default true) keeps the old click as a second
route, CLICK_EVENT_BASE + its index, which deals it a killing blow (evt.DamageDestructible, so CanDamage and
TriggerDestroyOnly still hold: a TriggerDestroyOnly brush takes no click), or names a map event of its own instead.

MM9's own break consequences, where the map hook gives no destroyed event (objects.py writes the Lua): a DestructableProp
whose SpawnObject is a TreasureBag drops it (Bathhouse's and Beethoven's urns: `spawned_loot_containers`,
evt.SpawnLootContainer), an `Exploding` one deals ExplodeDamage within DamageRadius, and a Death/DamageTrigger "off"
to a PerceptionBrush the shared hints placed turns that hint off for good (`on_break`).
"""

from __future__ import annotations

import numpy as np

from . import source as _source  # noqa: F401 (puts the MM9 import tools on sys.path)
from transcode_mm9_dat_to_odm import normalize_mm9_sound_name  # noqa: E402

COG_BASE = 20000
CLICK_EVENT_BASE = 38000        # a `break` brush's click: 38000 + its DAT index (objects.py: 30000 own, 34000 damaged)
CLICK_DAMAGE = 1000000          # the click's blow: more than any MM9 HitPoints
EFFECT_SIZE = 200.0             # native units across the breaking effects are authored for
EFFECT_SCALE_RANGE = (0.5, 1.5)
SOUNDS = {"stone": "Events/stonecrumble.wav", "wood": "Events/shatterwood02.wav", "glass": "Events/glass_smash.wav",
          "metal": "Events/metalbreak03.wav"}
SOUND_WORDS = (("glass", "glass"), ("crate", "wood"), ("wood", "wood"), ("metal", "metal"), ("stone", "stone"),
               ("rock", "stone"), ("rubble", "stone"), ("pottery", "stone"))


def material(properties: dict, prop: bool) -> str:
    """The debris an object breaks into: its sound's word, else its debris flags, else wood for a prop (crates and
    barrels) and stone for a brush."""
    sound = normalize_mm9_sound_name(properties.get("CustomSound")).lower()
    for word, kind in SOUND_WORDS:
        if word in sound:
            return kind
    flags = {key for key in ("Stone", "Stone2", "Stone3", "Metal", "Glass", "Glass2", "Wood", "Wood2", "Wood3")
             if properties.get(key)}
    stone = bool(flags & {"Stone", "Stone2", "Stone3"})
    if flags & {"Glass", "Glass2"} and not stone:
        return "glass"
    if flags & {"Wood", "Wood2", "Wood3"} and not stone:
        return "wood"
    if "Metal" in flags:
        return "metal"
    if stone:
        return "stone"
    return "wood" if prop else "stone"


def tag_brushes(build, polygons: list) -> None:
    """Static and invisible faces of each DestructableBrush carry its cog (an invisible one is MM9's RayHit box, hit while
    the destructible stands); build.destructible_brushes: DAT name -> its polygons."""
    objects = {o["name"].lower(): o for o in build.source.objects if o["class"] == "DestructableBrush"}
    build.destructible_brushes = {}
    for polygon in polygons:
        source = objects.get(polygon.model.lower())
        if source is None or polygon.role not in ("static", "invisible", "glass"):
            continue
        polygon.notes.setdefault("cog", COG_BASE + source["index"])
        build.destructible_brushes.setdefault(source["name"], []).append(polygon)


def build_breakables(build) -> None:
    """The `motion: break` brushes (module docstring): static faces of the owner room (TRIGGER_cog<cog>_<room>, an
    invisible part TRIGGER_cog<cog>i_<room>) carrying the brush's cog, with the click's trigger;
    build.destructible_brushes gets them for scene_entries and build.shared['break_clicks'] the click handlers."""
    from .package import room_id
    from .rooms import mover_groups
    clicks = build.shared.setdefault("break_clicks", {})
    brushes = getattr(build, "destructible_brushes", None)
    if brushes is None:
        brushes = build.destructible_brushes = {}
    for group, members in mover_groups(build.plan).items():
        rule = build.plan["movers"][members[0]]
        if rule["motion"] != "break":
            continue
        for name in members:
            rule = build.plan["movers"][name]          # each brush its own rule (its click)
            source = build.source.by_name[name.lower()]
            if source["class"] != "DestructableBrush":
                raise SystemExit(f"{name}: `motion: break` is for DestructableBrush models, not {source['class']}")
            properties = source["properties"]
            cog = COG_BASE + source["index"]
            polygons = build.source.polygons(name)
            points = np.concatenate([p.points for p in polygons])
            owner = room_id(build.rooms.owner(rule.get("owner_lt", (points.min(0) + points.max(0)) / 2)))
            click = rule.get("click", True)
            event = 0
            if click is True and not properties.get("TriggerDestroyOnly"):
                event = CLICK_EVENT_BASE + source["index"]
                clicks[source["index"]] = name
            elif click not in (True, False):
                event = int(click)
            for polygon in polygons:
                polygon.notes["cog"] = cog
                invisible = polygon.role == "invisible"
                node = f"TRIGGER_cog{cog}{'i' if invisible else ''}_{owner[5:]}"
                build.package.add_polygon(node, polygon, build.stats)
                if node not in build.package.room_nodes[owner]:
                    build.package.room_nodes[owner].append(node)
                    surface = {"id": node[8:], "source_node": node, "flags": ["invisible"] if invisible else [],
                               "cog_number": cog}
                    if event:
                        surface["trigger"] = {"event_id": event, "type": "click"}
                    build.package.metadata["surfaces"].append(surface)
            brushes[source["name"]] = polygons
            build.stats["breakable_brushes"] += 1


def prop_cog(source, entry: dict) -> int:
    """A props.json entry's SetSprite key when it is a DestructableProp, else 0."""
    if entry.get("class") != "DestructableProp" or "source_object" not in entry:
        return 0
    return COG_BASE + int(entry["source_object"])


def entry(source: dict, cog: int, decoration_cog: int, centre, size: float, events: tuple, prop: bool) -> dict:
    properties = source["properties"]
    kind = material(properties, prop)
    hp = max(1, int(round(float(properties.get("HitPoints") or 0))))
    record = {"id": source["index"], "name": source["name"], "hp": hp,
              "damage_enabled": bool(properties.get("CanDamage", 1)),
              "trigger_destroy_only": bool(properties.get("TriggerDestroyOnly", 0)),
              "sound": normalize_mm9_sound_name(properties.get("CustomSound")) or SOUNDS[kind],
              "effect": f"openyamm:fx/destructible/{kind}",
              "effect_scale": round(float(np.clip(size / EFFECT_SIZE, *EFFECT_SCALE_RANGE)), 2),
              "center": [round(float(v)) for v in centre]}
    if cog:
        record["cog"] = cog
    if decoration_cog:
        record["decoration_cog"] = decoration_cog
    if events[0]:
        record["destroyed_event"] = events[0]
    if events[1]:
        record["damaged_event"] = events[1]
    return record


def glass_cog_overrides(build, scene: dict) -> set:
    """A breakable pane's glass faces (their own STATIC_glass<k>_c<cog>_ nodes, build.py) take its cog through the
    scene's face overrides (a glass node carries no surface record); returns the cogs so set."""
    import yaml
    groups = yaml.safe_load((build.runtime / f"{build.project.stem}.faces.yml").read_text()) or []
    overrides = scene.setdefault("initial_state", {}).setdefault("face_attribute_overrides", [])
    by_face = {entry["face_index"]: entry for entry in overrides}
    cogs = set()
    for group in groups:
        node = group["source_node"]
        if not node.startswith("STATIC_glass") or "_c" not in node:
            continue
        cog = int(node.split("_c", 1)[1].split("_")[0])
        cogs.add(cog)
        for face in group["face_ids"]:
            entry = by_face.get(face)
            if entry is None:
                entry = {"face_index": face}
                overrides.append(entry)
                by_face[face] = entry
            entry["cog_number"] = cog
    return cogs


def on_break(build, out: list[dict], hooked: set) -> None:
    """The shared break consequences (module docstring): each entry without a map event that spawns a bag or explodes
    gets the destroyed event objects.OBJECT_EVENT_BASE + its id; build.shared['broken'] holds what its handler does,
    and the scene's `spawned_loot_containers` the bags."""
    from .objects import DAMAGED_EVENT_BASE, OBJECT_EVENT_BASE, _number, exploding, spawn_sources, spawned_records
    from .perception import HINT_COG_BASE
    from .source import SCALE
    bags = spawn_sources(build)
    hints = set(build.shared.get("hints") or {})

    def hint_off(properties: dict, kind: str) -> list:
        target = str(properties.get(f"{kind}TriggerTarget") or "").lower()
        message = str(properties.get(f"{kind}TriggerMessage") or "").strip().lower()
        brush = build.source.by_name.get(target)
        if message != "off" or brush is None or brush["class"] != "PerceptionBrush":
            return []
        return [HINT_COG_BASE + brush["index"]] if HINT_COG_BASE + brush["index"] in hints else []

    def light_off(properties: dict, kind: str) -> list:
        """A Death/DamageTrigger "off" to a PerceptionLight (Thjorad Mine's torch holder and cart blocker)."""
        from .lights import PULSING_LIGHT_KEY_BASE
        target = str(properties.get(f"{kind}TriggerTarget") or "").lower()
        message = str(properties.get(f"{kind}TriggerMessage") or "").strip().lower()
        light = build.source.by_name.get(target)
        key = PULSING_LIGHT_KEY_BASE + light["index"] if light is not None else None
        if message != "off" or light is None or light["class"] != "PerceptionLight" or key not in lights:
            return []
        return [key]
    lights = set(build.shared.get("perception_lights") or {})
    broken, damaged, skipped = {}, {}, []
    for record in out:
        index = record["id"]
        properties = build.source.objects[index]["properties"]
        action = {}
        if index in bags:
            action["spawn"] = bags[index]
        if exploding(properties):
            action["explode"] = {"centre": record["center"], "radius": int(round(_number(properties.get(
                "DamageRadius")) * SCALE)), "damage": int(round(_number(properties.get("ExplodeDamage"))))}
        if hint_off(properties, "Death"):
            action["hints_off"] = hint_off(properties, "Death")
        if light_off(properties, "Death"):
            action["lights_off"] = light_off(properties, "Death")
        if (hint_off(properties, "Damage") or light_off(properties, "Damage")) and not record.get("damaged_event"):
            record["damaged_event"] = DAMAGED_EVENT_BASE + index
            damaged[index] = {"name": record["name"], "hints_off": hint_off(properties, "Damage"),
                              "lights_off": light_off(properties, "Damage")}
        if not action:
            continue
        if record["name"] in hooked:
            skipped.append(record["name"])
            continue
        record["destroyed_event"] = OBJECT_EVENT_BASE + index
        broken[index] = dict(action, name=record["name"])
    build.shared["damaged"] = damaged
    if skipped:
        print(f"note: the map's own destroyed events stand for {skipped} (no shared bag or explosion)")
    build.shared["broken"] = broken
    bag_records = spawned_records(build, {i for i, action in broken.items() if action.get("spawn")})
    if bag_records:
        build.shared["spawned_loot_containers"] = bag_records
    build.stats["destructible_bags"] = len(bag_records)
    build.stats["destructible_explosions"] = sum(1 for action in broken.values() if action.get("explode"))


def sealed_passages(build) -> list[dict]:
    """The `static` DestructableBrushes with a different room on either side and no portal over them: built solid,
    they seal their rooms from each other, and breaking one leaves a hole the engine treats as a wall (no sight, no
    monster path, the room beyond not drawn through it: Thronheim City's prison wall). Such a brush wants the `break`
    route with a doorway (`motion: break, doorway: true`). Its sides are probed along its thin axis, a voxel and a
    half beyond its faces, on labelled air."""
    breakable = {name.lower() for name, rule in build.plan["movers"].items() if rule.get("motion") == "break"}
    voxel = build.grid.size
    found = []
    for name, polygons in sorted(getattr(build, "destructible_brushes", {}).items()):
        if name.lower() in breakable:
            continue
        points = np.concatenate([p.points for p in polygons])
        moments = np.zeros((3, 3))
        for polygon in polygons:
            moments += np.outer(polygon.normal, polygon.normal) * polygon.area
        axis = np.linalg.eigh(moments)[1][:, -1]
        along = points @ axis
        centre = (points.min(0) + points.max(0)) / 2
        centre = centre + axis * ((along.max() + along.min()) / 2 - centre @ axis)
        reach = (along.max() - along.min()) / 2 + 1.5 * voxel
        sides = []
        for sign in (1.0, -1.0):
            point = centre + sign * reach * axis
            cell = build.grid.index(point[None])[0]
            near = build.rooms.distance[cell[0], cell[1], cell[2]] <= 1.5
            sides.append(build.rooms.owner(point) if near else 0)
        if 0 in sides or sides[0] == sides[1]:
            continue
        low, high = points.min(0) - voxel, points.max(0) + voxel
        if any(np.all(np.asarray(portal["centre"]) >= low) and np.all(np.asarray(portal["centre"]) <= high)
               for portal in build.portals if "centre" in portal):
            continue
        found.append({"name": name, "rooms": sides, "centre_native": build.project.native(centre).round().astype(int)
                      .tolist()})
    return found


def scene_entries(build, scene: dict) -> list[dict]:
    """The scene's `destructibles`: brushes whose cog faces made it into the map, and the placed destructible props."""
    hook = getattr(build.hooks, "destructible_events", None)
    events = hook(build) if hook is not None else {}
    built_cogs = {surface.get("cog_number") for surface in build.package.metadata["surfaces"]}
    built_cogs |= glass_cog_overrides(build, scene)
    out = []
    for name, polygons in sorted(getattr(build, "destructible_brushes", {}).items()):
        cog = polygons[0].notes["cog"]
        if cog not in built_cogs:
            continue
        points = build.project.native(np.concatenate([p.points for p in polygons]))
        low, high = points.min(0), points.max(0)
        out.append(entry(build.source.by_name[name.lower()], cog, 0, (low + high) / 2, float((high - low).max()),
                         events.get(name, (0, 0)), prop=False))
    for index, (cog, position) in sorted(getattr(build.content, "destructible_props", {}).items()):
        source = build.source.objects[index]
        # a prop is about a man's height; its centre half that above its feet
        centre = (position[0], position[1], position[2] + 48)
        out.append(entry(source, 0, cog, centre, 96.0, events.get(source["name"], (0, 0)), prop=True))
    on_break(build, out, {name for name, (destroyed, _) in events.items() if destroyed})
    sealed = sealed_passages(build)
    build.stats["destructible_sealed_passages"] = len(sealed)
    for passage in sealed:
        print(f"destructible {passage['name']} seals rooms {passage['rooms']} (native {passage['centre_native']}): "
              "no portal over it, so its hole stays a wall once broken; give it `motion: break, doorway: true`",
              flush=True)
    build.stats["destructible_brushes"] = sum(1 for record in out if "cog" in record)
    build.stats["destructible_props"] = sum(1 for record in out if "decoration_cog" in record)
    return sorted(out, key=lambda record: record["id"])
