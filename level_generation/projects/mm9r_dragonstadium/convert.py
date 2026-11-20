#!/usr/bin/env python3
"""
Dragon Stadium, MM9 rework: MM9's DRAGONSTADIUM.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_dragonstadium/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_dragonstadium/convert.py --plan     # rooms only: work/rooms*.png

The Dragon King's arena: a rock bowl open to the sky at the end of a tunnel from Lindisfarne, three ruined pillars, two
chests, three bone piles. overrides.yml holds the model rules, the two archway cuts and the sky texture; this file adds:
- the pillars (DestructableBrush `pN level K`, K = 1 at the floor .. 7 on top; each level's DeathTriggerTarget destroys
  the level above): static faces, one TRIGGER_ node per level with a cog and a click event, and a scene destructible
  per level (dungeon/destructibles.py: MM9's HitPoints 200, level 7 TriggerDestroyOnly). Weapons break a level, a
  click deals it a killing blow; its destroyed event destroys the level above (the chain; broken faces keep their
  baked light);
- the Dragon King (Dragon.scr, ScriptParams 1: hidden until DragonTrigger's "Trigger"): an immobile boss at his DAT
  position, hidden and dormant until the party enters the trigger box in the arena's mouth (polled); Dragon.scr's :SpawnMutants (two
  Winged Mutants at MutantMarker0/1, 45 s after he lands, then every 90, 180, ... s) and :OnDeath (key 472, item 577
  "Super Guber Award" to the party) as native Lua;
- the props and chests (props.json from ../../props/mm9_dragonstadium_claude).
README.md lists what is unmatched (the dragon's flight, landing, taunt, target switching and wing push; damage on the
pillars and their explosion).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))

import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.geometry import merge_coplanar  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402

PROPS = PROJECT / "props.json"
SKY_TEXELS_PER_LT = 0.2              # the sky faces: sky04 stretched to a tile about 1 300 LT wide (Chasm's route)
INDOOR_SKY = 0x00400000              # FaceEnums.h IndoorSky: the engine's projected indoor sky
# The open bowl's sky light (orchestrator review 2026-10-31, README "Baked lighting"): MM9's lightmaps put the bowl's
# vertical walls at 0.196, its roofed tunnels' walls at 0.16-0.18; with one ambient floor ours were 0.167 (x0.85) and
# 0.16-0.18. The arena room's sector minimum light level drops from the map's 20 to ARENA_LEVEL, which the bake turns
# into an ambient floor (31 - level) / 31 x 0.97 x ambient_scale: 18 is x1.18 of 20. Revert: ARENA_LEVEL = None.
ARENA_LEVEL = 18
OBJECT_LIGHT = "ObjectLight0"        # MM9's light for objects only (FastLightObjects: linear 1 - d/r into the base)

PILLARS, LEVELS = ("p1", "p2", "p3"), range(1, 8)
EV_PILLAR = 70                       # 70 + 7 * pillar + (level - 1): a click on that level
EV_PILLAR_BROKEN = 130               # 130 + 7 * pillar + (level - 1): that level's destroyed event
CLICK_DAMAGE = 1000000               # a click's blow: more than MM9's HitPoints (dungeon/destructibles.py's)
PILLAR_COG = 300                     # the same numbering for the faces' cogs
EV_DRAGON_TRIGGER = 60               # DragonTrigger (pressure plate in the arena's mouth)
EV_KILLED, T_TICK, T_SPAWN, EV_LOAD = 95, 96, 97, 1
TICKS_PER_SECOND = 4                 # the poll of DragonTrigger's box (its ticks run about 0.27 s: not a clock)
PARTY_RADIUS, PARTY_HEIGHT = 37, 170
GROUP_DRAGON, GROUP_MUTANTS = 1, 2
DRAGON, TRIGGER = "DragonKing0", "DragonTrigger"
MARKERS = ("MutantMarker0", "MutantMarker1")
SPAWN_FIRST, KEY_DRAGON, ITEM_AWARD = 45, 472, 577    # Dragon.scr SPAWN_INTERVAL, :OnDeath GiveKey / GiveItem
LAND_SOUND = "animsounds/dragonredhop.wav"           # MM9's dragon\land.wav is not in the review root's audio


def pillar_name(pillar: str, level: int) -> str:
    return f"{pillar} level {level}"


def pillar_index(pillar: str, level: int) -> int:
    return PILLARS.index(pillar) * 7 + level - 1


class DragonStadium(dungeon.Hooks):
    generator = "mm9r_dragonstadium"

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons) -> list:
        """The sky faces over the arena (MM9 draws its sky box through them): one sky04 tile about 1 300 LT wide."""
        for polygon in polygons:
            if "skymarker" in polygon.texture.lower():
                origin = np.asarray(polygon.mapping[0], float)
                polygon.mapping = (origin, np.array([SKY_TEXELS_PER_LT, 0.0, 0.0]),
                                   np.array([0.0, 0.0, SKY_TEXELS_PER_LT]))
        return polygons

    def destructible_events(self, build) -> dict:
        """Each pillar level's destroyed event (EV_PILLAR_BROKEN + its index): its DeathTrigger destroys the level above."""
        return {pillar_name(p, k): (EV_PILLAR_BROKEN + pillar_index(p, k), 0) for p in PILLARS for k in LEVELS}

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, project, source = build.content, build.project, build.source
        if PROPS.exists():
            content.props(PROPS)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        self.place_pillars(build)
        self.scale_lights(build)
        self.arena_room = content.owner(np.array(source.properties(DRAGON)["Pos"], float) + [0, 100, 0])
        write = build.package.write

        def write_with_level(*args, **kwargs):
            for room in build.package.metadata["rooms"]:
                if ARENA_LEVEL is not None and room["id"] == self.arena_room:
                    room["min_ambient_light_level"] = ARENA_LEVEL
            return write(*args, **kwargs)
        build.package.write = write_with_level
        # DragonTrigger as a polled box (Chasm of the Dead's route): MM9 fires it on any part of the party in the box;
        # a pressure plate does not fit the arena mouth's faceted floor. Dims are half extents; native box, grown by the
        # party's radius by the poll.
        trigger = source.properties(TRIGGER)
        pos, dims = np.array(trigger["Pos"], float), np.array(trigger["Dims"], float)
        corners = project.native(np.array([pos - dims, pos + dims]))
        self.trigger_box = [corners.min(0).round().astype(int).tolist(), corners.max(0).round().astype(int).tolist()]
        self.markers = {m: project.native(np.array(source.properties(m)["Pos"], float)).round().astype(int).tolist()
                        for m in MARKERS}

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale; the three tunnel lights (67/95/118, 92/131/163) are at 0.15. The BLV
        carries colour x BrightScale (Ruined Temple's route; the bake's direct_scale stands on that) and the model
        lighting's light_scale (overrides.yml) restores MM9's full colour for models."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            record["color"] = [int(round(c * scale.get(record["id"], 1.0))) for c in record["color"]]
        for light in build.lights:
            light["colour_in_blv"] = [int(round(c * light["bright_scale"])) for c in light["colour"]]

    def place_pillars(self, build) -> None:
        """Each pillar level's polygons as TRIGGER_pillar_<p>_<k>: drawn, solid, a cog and a click event (README)."""
        content, package, source, project = build.content, build.package, build.source, build.project
        self.pillars = {}
        for pillar in PILLARS:
            for level in LEVELS:
                name = pillar_name(pillar, level)
                polygons = merge_coplanar(source.polygons(name))
                node = f"TRIGGER_pillar_{pillar}_{level}"
                for polygon in polygons:
                    # the level's cog makes it a scene destructible (destructibles.scene_entries)
                    polygon.notes["cog"] = PILLAR_COG + pillar_index(pillar, level)
                build.destructible_brushes[name] = polygons
                for polygon in polygons:
                    package.add_polygon(node, polygon, build.stats)
                points = np.concatenate([p.points for p in polygons])
                centre = (points.min(0) + points.max(0)) / 2
                top = np.array([centre[0], points.max(0)[1] + 24, centre[2]])
                owner = content.owner(top)
                package.room_nodes[owner].append(node)
                k = pillar_index(pillar, level)
                package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": [],
                                                     "cog_number": PILLAR_COG + k,
                                                     "trigger": {"event_id": EV_PILLAR + k, "type": "click"}})
                self.pillars[name] = {"node": node, "cog": PILLAR_COG + k, "event": EV_PILLAR + k, "room": owner,
                                      "polygons": len(polygons),
                                      "centre": project.native(centre).round().astype(int).tolist(),
                                      "hit_points": source.properties(name).get("HitPoints")}
        build.stats["pillar_levels"] = len(self.pillars)

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """The Dragon King, hidden and dormant (Dragon.scr :HideSetup) and immobile (no ground walk: user decision,
        README). WingedMutantCache is CacheOnly: its row is kept for the spawns, it is not placed."""
        content, source = build.content, build.source
        bases = content.monster_bases(cache_only=True)      # WingedMutantCache's row (only the Dragon is placed)
        out, self.bodies = [], {}
        self.mutant_row = bases["WingedMutantCache"]["monster_id"]
        self.mutant_body = {k: bases["WingedMutantCache"][k] for k in ("radius", "height")}     # the row's (MM9's)
        for o in source.objects:
            if o["name"] != DRAGON:
                continue
            p, base = o["properties"], bases[o["name"]]
            # MM9's body: the row's, or at the DAT's own Scale
            changes = placed_body(base["monster_id"], p) or {k: base[k] for k in ("radius", "height")}
            self.bodies[o["name"]] = changes
            actor = content.actor(o, base, sector_of_room, group=GROUP_DRAGON, hidden=True,
                                  floor_query_lt=p["Pos"][1] + 24, **changes)
            actor["dormant"] = True
            actor["immobile"] = True
            actor["mm9_source_object_index"] = o["index"]
            self.dragon_index = actor["actor_index"]
            out.append(actor)
        self.placed_actors = len(out)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Dragon Stadium")
        pillars = ", ".join(
            f"{{id = {build.source.by_name[pillar_name(p, k).lower()]['index']}, "
            f"at = {lua.point(self.pillars[pillar_name(p, k)]['centre'])}}}"
            for p in PILLARS for k in LEVELS)
        markers = ", ".join(lua.point(self.markers[m]) for m in MARKERS)
        script.lines += [
            "local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end",
            f"local PILLARS = {{{pillars}}}   -- p1 level 1..7, p2 level 1..7, p3 level 1..7",
            f"local MARKERS = {{{markers}}}",
            f"local DRAGON = {self.dragon_index}",
            f"local TRIGGER_BOX = {{{lua.point(self.trigger_box[0])}, {lua.point(self.trigger_box[1])}}}   -- DragonTrigger",
            f"local function inBox(b, x, y, z) return x + {PARTY_RADIUS} >= b[1][1] and x - {PARTY_RADIUS} <= b[2][1] "
            f"and y + {PARTY_RADIUS} >= b[1][2] and y - {PARTY_RADIUS} <= b[2][2] and z + {PARTY_HEIGHT} >= b[1][3] "
            "and z <= b[2][3] end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "",
        ]
        script.chests()
        lines = [
            "-- The ruined pillars (DestructableBrush 'pN level K', HitPoints 200, Stone, level 7 TriggerDestroyOnly; each",
            "-- level's DeathTriggerTarget 'destroy's the level above): scene destructibles. Weapons (and the dragon's fire",
            "-- in MM9) break a level; a click deals it a killing blow. Its destroyed event marks it, puffs smoke and",
            "-- destroys the level above, so a broken level brings down everything over it (faces hidden, walk-through).",
            "local function pillarBroken(pillar, level)     -- pillar 0..2, level 1..7",
            "    set(\"Pillar\" .. pillar .. \"_\" .. level, 1)",
            "    local at = PILLARS[pillar * 7 + level].at",
            "    evt.SpawnWorldEffect(\"mm9:smoke\", at[1], at[2], at[3], 3)",
            "    if level < 7 then evt.DestroyDestructible(PILLARS[pillar * 7 + level + 1].id) end",
            "end",
        ]
        registrations = []
        for p in PILLARS:
            for k in LEVELS:
                info = self.pillars[pillar_name(p, k)]
                index = PILLARS.index(p) * 7 + k
                lines.append(f"handlers[{info['event']}] = function() evt.DamageDestructible(PILLARS[{index}].id, "
                             f"{CLICK_DAMAGE}) end   -- {pillar_name(p, k)}: a click")
                lines.append(f"handlers[{EV_PILLAR_BROKEN + pillar_index(p, k)}] = function() "
                             f"pillarBroken({PILLARS.index(p)}, {k}) end   -- {pillar_name(p, k)} destroyed")
                registrations.append((info["event"], "Pillar", "Pillar"))
                registrations.append((EV_PILLAR_BROKEN + pillar_index(p, k), "Pillar destroyed", None))
        lines += [
            "",
            "-- The Dragon King (Dragon.scr, ScriptParams 1 = bFlyInOnTrigger): hidden and not solid until DragonTrigger",
            "-- sends 'Trigger' (:OnTrigger: visible, solid, Land, Taunt, then he fights). Natively he appears in place and",
            "-- wakes; he stays where MM9 lands him (no ground walk: README, unmatched).",
            "local function dragonUp()",
            f"    evt.SetMonGroupBit({GROUP_DRAGON}, MonsterBits.Invisible, false)",
            "    evt.WakeActor(DRAGON)",
            "end",
            f"handlers[{EV_DRAGON_TRIGGER}] = function()       -- DragonTrigger (PlayerTriggerable; :OnTrigger RemoveTrigger)",
            "    if var(\"DragonAwake\") == 1 then return end",
            "    set(\"DragonAwake\", 1)",
            f"    set(\"MutantInterval\", {SPAWN_FIRST})",
            f"    evt.StartTimer({T_SPAWN}, seconds({SPAWN_FIRST}))      -- :NormalSetup Wait 22, SPAWN_INTERVAL, SpawnMutants",
            "    dragonUp()",
            f"    sound(\"{LAND_SOUND}\")",
            "end",
            "",
            "-- :SpawnMutants: SPAWN_INTERVAL doubles each time (45 s, then 90, 180, ...); a Winged Mutant at each marker",
            "-- (MutantMarker0/1, high over the arena: 'WingedMutant MoveToFloor 0'). It is the dragon's Wait 22, which",
            "-- a dead AI's script still runs (scr_audit README, Implicit engine semantics): the spawns go on after",
            "-- his death.",
            "local function spawnMutants()",
            "    for _, m in ipairs(MARKERS) do",
            f"        evt.SummonMonstersById({{monster = {self.mutant_row}, x = m[1], y = m[2], z = m[3], radius = 16, "
            f"group = {GROUP_MUTANTS}, count = 1}})",
            "    end",
            "    set(\"MutantsSpawned\", var(\"MutantsSpawned\") + 2)",
            "end",
            f"handlers[{T_TICK}] = function()                  -- four times a second, until the trigger",
            f"    evt.StartTimer({T_TICK}, seconds({1 / TICKS_PER_SECOND}))",
            "    if var(\"DragonAwake\") == 1 then return end",
            "    local x, y, z = evt.GetPartyPosition()",
            f"    if x ~= nil and inBox(TRIGGER_BOX, x, y, z) then handlers[{EV_DRAGON_TRIGGER}]() end",
            "end",
            f"handlers[{T_SPAWN}] = function()                 -- one-shot, armed by the trigger and by itself",
            "    if var(\"DragonAwake\") == 0 then",
            f"        evt.StopTimer({T_SPAWN})",
            "        return",
            "    end",
            "    local interval = var(\"MutantInterval\") * 2",
            "    set(\"MutantInterval\", interval)",
            f"    evt.StartTimer({T_SPAWN}, seconds(interval))",
            "    spawnMutants()",
            "end",
            "",
            f"-- :OnDeath: killed by the party, the dragon gives key {KEY_DRAGON} and item {ITEM_AWARD} (Super Guber Award).",
            f"handlers[{EV_KILLED}] = function(context)",
            "    if context.actorIndex ~= DRAGON or var(\"DragonDead\") == 1 then return end",
            "    set(\"DragonDead\", 1)",
            f"    MM9.giveKey({KEY_DRAGON})",
            f"    give({ITEM_AWARD}, \"dragonstadium:DragonKing0\")",
            "end",
            "",
            f"handlers[{EV_LOAD}] = function()      -- map load: the pillars' and the dragon's state",
            "    if var(\"DragonAwake\") == 1 then",
            "        if var(\"DragonDead\") == 0 then dragonUp() end",
            f"        evt.StartTimer({T_SPAWN}, seconds(var(\"MutantInterval\")))   -- the current wait, from the load",
            "    else",
            f"        evt.StopTimer({T_SPAWN})",
            "    end",
            f"    evt.StartTimer({T_TICK}, seconds({1 / TICKS_PER_SECOND}))",
            "end",
        ]
        registrations += [(EV_DRAGON_TRIGGER, "Dragon trigger", None), (T_TICK, "Dragon trigger poll", None, "timer"),
                          (T_SPAWN, "Dragon mutant spawns", None, "timer"),
                          (EV_LOAD, "Map load", None)]
        script.add(lines + [""], *registrations)
        script.hooks.append(f"RegisterMonsterKilledHook({EV_KILLED}, \"Monster killed\", handlers[{EV_KILLED}])")
        return script.finish(on_load=[EV_LOAD])

    def scene(self, build, scene) -> None:
        """The sky faces (MM9's skymarker box over the arena: 5 ceiling and 27 wall faces, sky04) draw the engine's
        projected indoor sky: IndoorSky set at load by face_attribute_overrides (Chasm of the Dead's route). A planar
        mapping streaks on the box's vertical faces. The BLV keeps them ordinary faces, so the bake still takes them
        as its sky emitters (bake_indoor.py reads the BLV's attributes)."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        sky = [f for f in blv["faces"] if f["texture_name"].lower() == "sky04"]
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f["index"], "legacy_attributes": int(f["attributes"]) | INDOOR_SKY} for f in sky)
        build.stats["sky_faces"] = len(sky)
        self.write_shadowless(build, blv)
        self.object_light_stand_in(build, scene)

    def write_shadowless(self, build, blv) -> None:
        """The pillar levels' BLV faces (cogs PILLAR_COG..+20) into the bake profile's `shadowless_faces`: MM9's pillars
        are world models, which cast no shadow in its lightmaps, and a broken level must leave none behind
        (devdocs/INDOOR_BAKED_LIGHTING.md). Face indices change with the BLV, so every build rewrites the list."""
        params = blv["face_params"]
        cogs = {PILLAR_COG + k for k in range(len(PILLARS) * 7)}
        faces = sorted(f["index"] for f in blv["faces"]
                       if f["face_param_index"] < len(params) and params[f["face_param_index"]]["cog_number"] in cogs)
        build.stats["pillar_faces"] = len(faces)
        if not build.project.install:
            return
        profile = ROOT / "tools/lighting/baked_indoors/profiles/mm9_dragonstadium.yml"
        data = json.loads(profile.read_text())
        if data.get("shadowless_faces") != faces:
            data["shadowless_faces"] = faces
            temporary = profile.with_suffix(".yml.tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n")
            temporary.replace(profile)

    def object_light_stand_in(self, build, scene) -> None:
        """MM9 lights every object in the arena with ObjectLight0 (white, BrightScale 0.8, radius 3 500 LT, objects only,
        FastLightObjects: linear 1 - d/r into a model's base light), which the model lighting does not reproduce
        (devdocs/INDOOR_MODEL_LIGHTING.md). Its mean over the map's placed objects (props, chests, the Dragon King) at
        MM9's full colour goes into the block's ambient, on top of WorldInfo's AmbientLight."""
        o = build.source.properties(OBJECT_LIGHT)
        centre = np.array(o["Pos"], float)
        radius = float(o["LightRadius"])
        points = [np.array(build.source.properties(e["anchor"])["Pos"], float)
                  for e in build.content.report["decorations"]] + [np.array(build.source.properties(DRAGON)["Pos"], float)]
        falloff = float(np.mean([max(0.0, 1 - np.linalg.norm(p - centre) / radius) for p in points]))
        block = scene.get("model_lighting")
        if block is None:
            return
        added = [int(round(c * falloff)) for c in o["LightColor"]]
        block["ambient"] = [min(255, a + b) for a, b in zip(block["ambient"], added)]
        self.object_light = {"falloff_mean": round(falloff, 3), "added": added, "ambient": block["ambient"]}

    def report(self, build) -> dict:
        ids = {name: build.source.by_name[name.lower()]["index"] for name in self.pillars}
        return {"scripted": {"pillars": self.pillars, "destructible_ids": ids, "trigger_box": self.trigger_box,
                             "markers": self.markers,
                             "dragon_index": self.dragon_index, "bodies": self.bodies, "mutant_row": self.mutant_row,
                             "mutant_body": self.mutant_body},
                "object_light_stand_in": getattr(self, "object_light", None),
                "arena_room_level": [self.arena_room, ARENA_LEVEL]}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, DragonStadium()))
