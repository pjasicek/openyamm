#!/usr/bin/env python3
"""
Isle of Ashes, MM9 rework: MM9's ISLEOFASHES.dat as a native BLV open to the sky. The pilot of converting MM9's
outdoor maps the way the cities are (../mm9r_common/CITY_PLAYBOOK.md) instead of resampling their terrain onto an ODM
height grid (../mm9r_isleofashes/, superseded): MM9's terrain mesh, tunnel and structures become faces of one open-air
sector, unchanged. The shared part is ../mm9r_common/outdoor_blv.py.

    python3 level_generation/projects/mm9r_isleofashes_blv/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_isleofashes_blv/convert.py --plan     # rooms only: work/rooms*.png

**Its own review root.** This build installs into output/mm9_rework/isleofashes_blv_root (a hard-linked copy of the
review root, created by README.md's steps), next to the ODM pilot in output/mm9_rework/assets_dev.

**The story** is hand-ported like every region's (regionlua.py, loaded by ../mm9r_common/outdoor_blv.py
`map_script` after the shared doors, chests and ForadWorld.scr): Forad Darre, Yrsa, the dragonflies, the bunker, the
Lich's summons, the book's cinema and Annud Redeye's passage, each handler citing its .scr. Here the story's NPCs and
monsters are placed first, from the old import's records (../mm9r_isleofashes/story.py `story_actor_sources`), the
bunker and hut doors are this BLV's doors (their clicks are the scripts' Use events), the fort walls the cinema
breaks are faces carrying their DAT object index as cog, and the book, lectern and boat carry the scripts' events.
The cinema itself is isleofashes.cinematics.yml (story.py `Story.cinematics`, the shared emitter
../mm9r_common/cinematics.py; devdocs/mm9_rework/MM9_CUTSCENES.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import review_root  # noqa: E402

# This pilot's own review root (see the docstring): every install goes through review_root, so redirect it first.
review_root.ASSETS = review_root.REVIEW / "isleofashes_blv_root"
review_root.OWNED = review_root.REVIEW / "isleofashes_blv_owned.txt"

import dungeon  # noqa: E402
import outdoor_blv  # noqa: E402
import terrain_blend  # noqa: E402

sys.path.insert(0, str(PROJECT.parent / "mm9r_isleofashes"))
import story as isle_story  # noqa: E402

TRANSFORM = {"scale": 2.56, "sea_level_lt": -64.0, "offset_x": -7168, "offset_y": -512}   # overrides.yml offset
# The structures the scripts break (IsleAshesBook.scr: the bunker's FortWall, the islet's FortWall0): cog faces
COG_MODELS = ("FortWall", "FortWall0")
# The door groups whose clicks are the scripts' Use events (DoorLock.scr on the bunker pair, the hut door):
# regionlua.py handles them (outdoor_blv.py leaves a group with the map's own event to it)
DOOR_GROUP_MODELS = {"BunkerDoor": "BunkerDoor1", "RotatingDoor8": "RotatingDoor8"}


class IsleOfAshes(outdoor_blv.OutdoorBlvHooks):
    generator = "mm9r_isleofashes_blv"

    def __init__(self, project_dir: Path):
        super().__init__(project_dir)
        self.story = isle_story.Story(TRANSFORM)
        objects = self.story.objects
        self.mover_events = {group: (isle_story.OBJECT_EVENT_BASE + objects.named(model)["index"], "click")
                             for group, model in DOOR_GROUP_MODELS.items()}
        self.exclude_sources = set(self.story.story_actor_sources())

    # --- geometry: the breakable fort walls as cog faces ------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        cogs = {name: self.story.objects.named(name)["index"] for name in COG_MODELS}
        for polygon in polygons:
            if polygon.model in cogs:
                polygon.notes["cog"] = cogs[polygon.model]
        return super().edit_polygons(build, polygons)

    # --- actors: the story's NPCs and monsters first, then MM9's other monsters -------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, story = build.content, self.story
        by_index = {o["index"]: o for o in build.source.objects}
        out, story.actor_by_source, story.actors = [], {}, []
        for source in story.story_actor_sources():
            record = story.old_actors[source]
            o = by_index[source]
            base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                 "monster_id", "radius", "height", "move_speed")}
            if source in story.NPC_ROWS:
                base["monster_info_id"] = base["monster_id"] = story.NPC_ROWS[source]
            actor = content.actor(o, base, sector_of_room, floor_query_lt=o["properties"]["Pos"][1] + 24)
            if o["class"] in isle_story.FLYER_CLASSES:
                # flyers keep MM9's height, at least FLYER_CLEARANCE over the floor
                z = isle_story.to_map(o["properties"]["Pos"], TRANSFORM)[2]
                actor["position"]["z"] = int(round(max(z, actor["position"]["z"] + isle_story.FLYER_CLEARANCE)))
            # The facing stays content.actor's (90 - ry, MM9's DAT Rotation): the old import's -ry turned Forad and
            # Yrsa a quarter turn away from the party (user play-test 2026-11-06)
            for key in ("mm9_rude_id", "mm9_civilian", "mm9_guard", "mm9_can_receive_damage", "npc_id",
                        "immobile", "group", "ally"):
                if key in record:
                    actor[key] = record[key]
            actor["mm9_source_object_index"] = source
            story.actor_by_source[source] = actor["actor_index"]
            story.actors.append(actor)
            out.append(actor)
        return out + super().actors(build, sector_of_room)


if __name__ == "__main__":
    if not review_root.ASSETS.exists():
        sys.exit(f"{review_root.ASSETS} is missing: create it first (README.md)")
    hooks = IsleOfAshes(PROJECT)
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        project = dungeon.source.Project.load(PROJECT)
        print(f"boat arrivals rewritten: {outdoor_blv.rewrite_transport(project)}")
        print(f"indoor decoration bindings added: {outdoor_blv.bind_indoor_decorations(project.work / 'props.json')}")
        print(f"story sounds installed: {hooks.story.install_sounds(review_root) or 'none'}")
        # The book's cinema (story.py Story.cinematics): the engine loads it beside the map
        review_root.install("worlds/mm9/maps/isleofashes.cinematics.yml", hooks.story.cinematics_text().encode())
        print("cinematics installed: worlds/mm9/maps/isleofashes.cinematics.yml (book_sinking)")
        import camera_gate
        maps = review_root.mirror_path("worlds/mm9/maps")
        for line in camera_gate.gate_installed("isleofashes", maps / "isleofashes.cinematics.yml",
                                               maps / "isleofashes.blv", maps / "isleofashes.scene.yml",
                                               project.overrides.get("cinematics_gate") or {}, strict=True):
            print("camera gate: " + line)
        print(terrain_blend.install(PROJECT))
    sys.exit(code)
