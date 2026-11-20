#!/usr/bin/env python3
"""
Wizard's Lab, MM9 rework: MM9's WIZARDSLAB.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md), as the user
chose for it (2026-11-04, devdocs/mm9_rework/REGIONS_FINISH.md step 3: "built like the cities").

    python3 level_generation/projects/mm9r_wizardslab/convert.py --plan     # rooms only: work/rooms*.png
    python3 level_generation/projects/mm9r_wizardslab/convert.py            # build, compile, install (review root)

Wizard's Lab is a structure with no terrain: the lab floor, the cell block and its pool under it, the cloud room and
the summoning tower, whose top is MM9's only open sky (five sky faces, flags 0x111, texture "Default", round the
tower top). So it is a dungeon with the city's sky: CityHooks gives the sky faces IndoorSky and the scene the open sky
and daylight; there are no streets, so no roof line, street cuts or top portals (`extra_portals`), and nothing
outdoor (no terrain block, no outdoor view, no weather) (README "The sky, daylight and no terrain").

overrides.yml holds the model rules, the sky marker alias and the city settings; this file adds the lab's
population (props.json from a props project, when there is one: README "Props"; MM9's monsters with their bodies,
the friendly summoners, Robinssen with his dialogue) and the scripted objects as native Lua (citylua.py), each citing
its .scr (README "Scripted objects"; behaviour spec: work/scr_spec.md). The summoning's camera cinema is the cinematic
`summoning` (citylua.cinematic_scenes), installed as worlds/mm9/maps/wizardslab.cinematics.yml (README "Cinematics").
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from transcode_mm9_dat_to_odm import read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402
import cutscenes  # noqa: E402

PROPS = citylua.PROPS
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/wizardslab.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"

# MM9's animated translucent station surfaces: (texture, opacity: the brush Alpha, two-sided) (scene()).
SPR_SURFACES = [("sprites\\water\\water115flowing.spr", 0.5, True),   # the teleporter sheets (7 faces)
                ("sprites\\water\\water123.spr", 0.65, False)]       # the 30 crystals (180 faces)

PEACEFUL_ALLY = 118                 # a peasant family's monster type: lends peaceful relations (Thronheim City)
# Robinssen's actor when the old import's record is missing: its Reverend Monk row (9125) as the old import placed it.
ROBINSSEN_FALLBACK = {"name": "Robinssen", "attributes": 0, "hp": 525, "hostility_type": 0, "monster_info_id": 9125,
                      "monster_id": 9125, "radius": 44, "height": 157, "move_speed": 0}


class WizardsLab(CityHooks):
    generator = "mm9r_wizardslab"
    mover_events = citylua.MOVER_EVENTS
    # Every door group opens on a click (the drawers, closets and the dresser, not only the doorway pairs); the cells
    # (their levers open them) and the force field (the super eye's death) have `click: false` in overrides.yml.
    all_doors_click = True

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        # MM9 marks the sky faces here by the surface flag (0x10) only: the five round the summoning tower's top carry
        # "Default", as 18 ordinary solid slivers do. The shared build has already given the flagged ones the sky
        # marker (Source.sky_flagged_as_sky; overrides.yml `textures`: alias sky04), so CityHooks.scene finds them.
        if not build.stats.get("sky_flagged_retextured"):
            print("WARNING: no sky-flagged polygons: the scene opens to the sky with no sky faces")
        return super().edit_polygons(build, polygons)

    def extra_portals(self, build) -> list:
        """No street structure (city/structure.py): the lab has no streets under a sky lid, only the tower top's open
        air, one room behind its doorways like any dungeon room. structure.city_portals needs a roof line
        (`street_top_lt`) and would divide nothing here."""
        build.city_report = {"structure": "none: no streets; the tower top's open air is one room"}
        return []

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            build.content.props(PROPS, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build))
        else:
            print("note: props.json is missing; no decorations or chests placed (README \"Props\")")

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """MM9's monsters at their DAT places with MM9's bodies (the row's, or at the DAT's own Scale). The seven
        summoners (WizardSummoner.scr, WizardMaster.scr: AddFriend Player) are friendly with their row's engagement
        type kept, each apprentice in a group of its own, so the ritual's Lua can turn one hostile and tell which are
        dead; Robinssen (ReverendMonk0, NPC55.scr) is a friendly, immobile dialogue actor (RUDE 55) on the old import's
        Reverend Monk record. An actor with no floor under it is left out and listed (work/build_report.json)."""
        content, source = build.content, build.source
        bases = content.monster_bases()
        chain = {name: citylua.GROUP_SUMMONER + k for k, name in enumerate(citylua.CHAIN)}
        out, self.actor, self.objects, self.left_out = [], {}, {}, []
        for o in source.objects:
            name, p = o["name"], o["properties"]
            if name not in bases or o["class"] not in build.project.monster_classes:
                continue
            base = bases[name]
            group, friendly = 0, False
            if name in chain:
                group, friendly = chain[name], True
            elif name == citylua.MASTER:
                group, friendly = citylua.GROUP_MASTER, True
            try:
                actor = content.actor(o, base, sector_of_room, group=group, friendly=friendly,
                                      floor_query_lt=p["Pos"][1] + 24, **placed_body(base["monster_id"], p))
            except SystemExit as error:
                self.left_out.append({"anchor": name, "index": o["index"], "reason": str(error)})
                print(f"WARNING: {error}: left out")
                continue
            if friendly:
                # Friendly, with the row's engagement type: evt.SetMonGroupBit(Hostile) makes one fight (Thronheim's
                # Desert Terror), and the demon's relations make them fight it.
                actor["hostility_type"] = base["hostility_type"]
            actor["mm9_source_object_index"] = o["index"]
            self.actor[name], self.objects[name] = actor["actor_index"], o["index"]
            out.append(actor)
        out.append(self.robinssen(build, sector_of_room))
        missing = [name for name in (*citylua.CHAIN, citylua.MASTER, "EvilGrandSorcerer1", "Oculus0")
                   if name not in self.actor]
        if missing:
            raise SystemExit(f"scripted actors not placed: {missing}")
        return out

    def robinssen(self, build, sector_of_room: dict) -> dict:
        """NPC55.scr's Mad Wizard Robinssen (RUDE 55, voice NPC_055): the old import's record (it placed him as a
        hostile Reverend Monk, row 9125), friendly and immobile, named as NPCNAME.rude names RUDE 55."""
        o = build.source.by_name[citylua.NPC_ROBINSSEN.lower()]
        base = dict(ROBINSSEN_FALLBACK)
        if OLD_SCENE.exists():
            old = {a["mm9_source_object_index"]: a for a in
                   yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
                   if "mm9_source_object_index" in a}
            record = old.get(o["index"])
            if record is not None:
                base.update({key: record[key] for key in ("hp", "monster_info_id", "monster_id", "radius", "height")})
        base["name"] = read_mm9_npc_names(NPC_NAMES).get(citylua.RUDE_ROBINSSEN, base["name"])
        p = o["properties"]
        actor = build.content.actor(o, base, sector_of_room, group=citylua.GROUP_NPC, friendly=True,
                                    floor_query_lt=p["Pos"][1] + 24, **placed_body(base["monster_id"], p))
        actor["ally"] = PEACEFUL_ALLY
        actor["immobile"] = True
        actor["move_speed"] = 0
        actor["mm9_source_object_index"] = o["index"]
        actor["mm9_rude_id"] = citylua.RUDE_ROBINSSEN
        self.actor[citylua.NPC_ROBINSSEN], self.objects[citylua.NPC_ROBINSSEN] = actor["actor_index"], o["index"]
        return actor

    # --- map script -------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """MM9's animated, translucent .spr surfaces of the stations (flags 0x4000 + 0x8, MM9_VISUAL_PROPERTIES.md): the
        teleporter sheets (`teleporter effect*`, water115flowing.spr, brush Alpha 0.5, seen from both sides) and the
        30 crystals (`yellow0` .. `blue5`, water123.spr, Alpha 0.65), drawn translucent and as their frame
        sequences (the user, 2026-11-10: the portal and the buttons were static and opaque). The faces are found in
        the compiled BLV by texture; the frames go to the texture frame table (perception.install_frames)."""
        super().scene(build, scene)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        from dungeon import perception
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        for texture, opacity, two_sided in SPR_SURFACES:
            alias = build.source.aliases[texture]["alias"].lower()
            faces = sorted(f["index"] for f in blv["faces"]
                           if not f["is_portal"] and str(f.get("texture_name", "")).lower() == alias)
            if not faces:
                raise SystemExit(f"no faces with {texture} ({alias}) in the BLV")
            scene.setdefault("translucent_faces", []).append(
                {"faces": faces, "opacity": opacity, "tint": [1.0, 1.0, 1.0], "two_sided": two_sided})
            build.stats[f"translucent_{alias}"] = len(faces)
            if build.project.install:
                perception.install_frames(build, texture)

    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": self.actor, "objects": self.objects,
                                                     "left_out": self.left_out})


if __name__ == "__main__":
    hooks = WizardsLab()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv) and getattr(hooks, "scenes", None):
        # The summoning's camera cinema (citylua.cinematic_scenes): the engine loads it beside the map
        print(f"cinematics installed: {cutscenes.install('wizardslab', hooks.scenes)} (summoning)")
    sys.exit(code)
