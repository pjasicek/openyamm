#!/usr/bin/env python3
"""
Footstep sounds by floor texture for an MM9 map built as a BLV open to the sky (devdocs/INDOOR_OPEN_SKY.md
"Footsteps"): the scene's `footstep_sounds`, written from the MM9 source texture behind each face texture alias. A BLV
without the block keeps the stone hall sound on every floor (every MM6-MM8 map, the dungeons).

    footsteps.apply(build, scene)        # a map's `scene` hook, after the BLV is compiled

The surface is MM9's own surface type of the source texture (the DTX user flags, `dtx_surface_flag` in the map's
material aliases; devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md: 10/11 wood, 12 stone, 13 earth, 14 grass, ...). A texture
without one (0, or a value with no step sound) takes the first rule whose word occurs in its file name (lower case); a
texture no rule matches is stone. Terrain rock is rough ground, structure floors are stone.
"""

from __future__ import annotations

import sys
from collections import Counter

from dungeon.source import ROOT

# game/audio/SoundIds.h: (walk, run)
SOUNDS = {
    "grass": (93, 54), "ground": (95, 56), "dirt": (92, 53), "stone": (98, 59), "wood": (103, 64),
    "water": (101, 62), "snow": (97, 58), "ice": (94, 55), "sand": (91, 52), "carpet": (89, 50),
}
# MM9's surface types (DTX user flags) with a step sound: metal and glass floors ring as stone, cloth as carpet.
SURFACE_FLAGS = {
    8: "stone", 9: "stone", 10: "wood", 11: "wood", 12: "stone", 13: "dirt", 14: "grass", 15: "stone",
    16: "water", 18: "carpet", 19: "carpet", 21: "snow",
}
RULES = [
    ("water", "water"), ("ocean", "water"),
    ("grass", "grass"), ("ashrock.", "grass"),          # the isle's green scrub (ashrock; ashrock2 is rock)
    ("dirt", "dirt"), ("mud", "dirt"),
    ("snow", "snow"), ("ice", "ice"), ("sand", "sand"), ("desert", "sand"),
    ("wood", "wood"), ("plank", "wood"), ("carpet", "carpet"), ("rug", "carpet"),
    ("cliff", "ground"), ("rock", "ground"), ("terrain", "ground"),
]


def surface(source_texture: str, surface_flag: int = 0) -> str:
    if surface_flag in SURFACE_FLAGS:
        return SURFACE_FLAGS[surface_flag]
    name = source_texture.replace("\\", "/").lower()
    stem = name.rsplit("/", 1)[-1]
    for word, kind in RULES:
        if word in stem or (word == "terrain" and "/terrain/" in name):
            return kind
    return "stone"


def apply(build, scene: dict) -> None:
    """The scene's footstep_sounds for every texture of the compiled BLV's walkable faces."""
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(build.runtime / build.project.map)["payload"]
    overrides = {entry["face_index"]: entry.get("texture_name")
                 for entry in scene.get("initial_state", {}).get("face_attribute_overrides", [])}
    alias_entry = {entry["alias"].lower(): (source, int(entry.get("dtx_surface_flag") or 0))
                   for source, entry in build.source.aliases.items()}
    textures = {(overrides.get(face["index"]) or face["texture_name"]).lower()
                for face in blv["faces"] if face["facet_type"] in (3, 4) and not face["is_portal"]}
    groups: dict[str, list[str]] = {}
    for texture in sorted(textures):
        source, flag = alias_entry.get(texture, (texture, 0))
        groups.setdefault(surface(source, flag), []).append(texture)
    scene["footstep_sounds"] = [{"texture_names": names, "walk_sound_id": SOUNDS[kind][0],
                                 "run_sound_id": SOUNDS[kind][1]} for kind, names in sorted(groups.items())]
    build.stats["footstep_surfaces"] = dict(Counter({kind: len(names) for kind, names in groups.items()}))
