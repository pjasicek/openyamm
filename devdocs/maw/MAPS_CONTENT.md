# MAW mod: map geometry, map scripts, quests and NPC topics

Status: investigation only (2026-10-22). Built since (2026-10-24): the MAW ruleset in `game/rules/maw/` and
`assets_dev/engine/rulesets/maw/`; what is left is in [GAPS.md](GAPS.md), the deliberate differences in
[DEVIATIONS.md](DEVIATIONS.md). This document completes the content part of the MAW analysis ([README.md](README.md)
§2.9, [UI_CONTENT.md](UI_CONTENT.md) §3–4) with real diffs of the edited maps, event-by-event notes on every MAW map and
quest script, and how each item would be expressed on top of OpenYAMM's generated events. The per-map operations are
drafted as data in [data/map_overlays.yml](data/map_overlays.yml).

Sources:

- MAW: `/home/pjasicek/github/Maw-Mod-MMMerge` at `ef23ee17` (`Data/zMaw.games.lod`, `Scripts/Maps`,
  `Scripts/Global`, map-related `Scripts/General`).
- Base maps: `reference/mmerge_data_forus/Data/{mm6,mm7,mm8}.games.lod/` (already extracted directories).
- Base scripts: `reference/mmmerge/Scripts` (Rodril nightly), GrayFace decompiles in
  `reference/mmext-scripts/Decompiled_Scripts`.
- OpenYAMM: `assets_dev/worlds/{mm6,mm7,mm8}/maps/*.{odm,blv,scene.yml}`, generated events in
  `assets_dev/worlds/*/events/maps/*.lua`, overlays `*_mmmerge.lua`, `*_1.lua`, shared code in
  `assets_dev/engine/events/` and `assets_dev/engine/scripts/common/event_support.lua`.

---------------------------------------------------------------------------------------------------------------------

## 0. Headline findings

1. **Only three of the twelve edited maps carry new content: the teleporter sites.** New Sorpigal (oute3) gets eight
   decorations and a few terrain cells, Ravenshore (out02) and Harmondale (7out02) get exact translated copies of
   existing bmodels with a few face events changed, plus terrain. Nothing in the teleporters is new geometry.
2. **The other nine maps have no geometry change.** Their byte differences are MMEditor re-save noise (renamed
   bmodels, renumbered vertices, compacted face-extra tables, dropped zero-vertex faces, re-ordered door slots, editor
   attribute bits). The real edits are in the delta (DDM/DLV) part and the spawn list: boss actors in d04, d18,
   mdt09, out05, d08, 7d33, d12; spawn points in d18, d12, elemf; five ethereal faces in d42; one lava flag in elemf.
   UI_CONTENT §4.1 reads the file-size changes as geometry edits; that is wrong (see §6).
3. **OpenYAMM's copies of all twelve maps are byte-identical to base MMMerge except `oute3.odm`**, where OpenYAMM
   added a five-piece ship (bmodels 85–89, event 29) in place of the `SHP` decoration. OpenYAMM did the same to
   outc2, outd1, outd2, outd3, oute1 and oute2. All OpenYAMM bmodels are appended, so base bmodel and face indices
   stay valid and do not collide with MAW's edits.
4. **Teleporter events** are 1777 "Antagarich", 1888 "Jadame" and 2666 "Enroth" in all three maps (map events) and,
   unused, again as global events in `Global/GLOBAL.lua`. Destinations depend on QBits 527 and 93; Survival mode
   sends to Emerald Island.
5. **MAW drops more base fixes than the earlier documents list**: besides 7out02, 7d24, 7d29 and d19, MAW's dungeon
   entrance rewrite (`General/zzMaw-Maps.lua`) drops the Hive's post-ending lock (outa1 event 90) and sends
   Barrow VII (out11 event 505) to the wrong map; 6d05 drops the Snergle door lock and key consumption; 7d32 drops
   its quest check; 7d34 drops a counter guard; with non-Redone data 7out01 drops the Emerald Island no-Arcomage
   filter.
6. **MAW bugs found**: the znwc potion seller's 50-purchase cap never stops sales (missing `return`); Dimensional
   Maps takes The Seer's topic slot A and hides "Pilgrimage", which is the only thing that clears shrine QBit 1230,
   so after the first stat shrine no shrine pays out again; the eight Ravenshore obelisk copies keep the real
   obelisk's event 150 (free obelisk message #7); the Harmondale shrine copies keep the Land-of-the-Giants altar
   (event 221); the insanity trade-item list has `1946` for `1496`.
7. **MAW fixes worth taking into the Standard ruleset**: Galvinus' Pure Accuracy quest QBits (132/133 instead of
   133/134, which clobbered Isthric's topic), the 7d11 pillar doors (onLoad resets the key counter), the d26
   Sarcophagus duplicate after a map refill, the 7d12/7d37 book switches whose clickable face had the wrong event,
   and the Saving Goobers loop precedence (when that quest is ported; OpenYAMM has no Saving Goobers yet).
8. **NPC 413 is Judge Grey, not an oracle.** MAW's respec and Dimensional Maps topics sit on 314 (Oracle,
   Ravenshore), 413 (Judge Grey, Harmondale) and 794 (The Seer, Free Haven). MAW also drops Judge Grey's base death
   logic; OpenYAMM keeps it, so a port must pick another Antagarich NPC.
9. **MMExt and OpenYAMM map-variable numbers differ by two**: MMExt `MapVarN` (GrayFace and MAW) is OpenYAMM
   `MapVar(N+2)` (checked in outb1, pyramid, 7d11, 7d20, d26). MAW `mapvars.x`/`vars.x` map to
   `evt.GetMapVar/SetMapVar(name)` and `evt.GetGlobalVar/SetGlobalVar(name)` (or `MM7.GetCrossVar`).
10. Expressing MAW content in OpenYAMM needs a few engine additions: ruleset-scoped overlay mounting and load order,
    scene-overlay operations for entity removal, terrain height/tile overrides and bmodel instancing, indoor actor and
    spawn overrides, a summon-by-monster-id call (MAW's `pseudoSpawnpoint`), extra PlaceMon names, and a hook before
    `evt.MoveToMap` for the dungeon reset prompt (§2.5, §3.0).

---------------------------------------------------------------------------------------------------------------------

## 1. Method

- `zMaw.games.lod` ("GameMMVI", one `maps` directory of 24 entries of 32 bytes) was unpacked with a throwaway lister:
  each map entry has a 16-byte header and a zlib payload. All 24 files are MM8-layout ODM/BLV/DDM/DLV (MMMerge stores
  every world's maps in the MM8 format).
- Base files come from the extracted forus LODs. `cmp` against `assets_dev/worlds/*/maps/` shows OpenYAMM's
  ODM/BLV are the decompressed base files except `oute3.odm` (§2.4). OpenYAMM has no DDM/DLV; the delta is in
  `*.scene.yml`.
- Delta comparison: `tools/export_outdoor_scene_yml.py` and `tools/export_indoor_scene_yml.py` were run on both base
  and MAW files into a scratch folder. The base export reproduces OpenYAMM's scene files exactly for ten maps
  (oute3 and out02 differ by OpenYAMM's own edits, §2.4), so MAW-versus-base export diffs are MAW-versus-OpenYAMM
  diffs. Actors, sprite objects, chests (decoded items), doors (matched by door id), map variables, face and
  decoration flags were compared field by field.
- Geometry comparison: a scratch parser of MM8 ODM (bmodel headers, vertices, 0x134 faces, entities, spawns,
  terrain maps) and BLV (vertices, 0x60 faces, face extras, sectors, decorations, lights, spawns, outlines), checked
  by consuming every file to its last byte. Bmodels were matched by position and face count, faces by vertex
  coordinates plus texture, so renumbering does not count as change. Face attribute bits that MMEditor rewrites on
  save were ignored: `0x80000000` IsPicked, `0x8000`/`0x20000`/`0x1000`/`0x8` texture alignment, `0x10000`
  Outlined, `0x80` SeenByParty. Door attribute bit `0x2` (set on every door by the editor) was ignored too.
- Coordinates are world units. A terrain cell `(cx, cy)` covers `x = (cx-64)*512 .. +512`,
  `y = (64-cy)*512 .. -512`; terrain heights are cell values times 32.
- Scratch scripts and reports (not kept in the repo):
  `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/maw_maps/`
  (`scripts/{lod,geo,diff,scenediff,entrances}.py`, `reports/*.txt`).

---------------------------------------------------------------------------------------------------------------------

## 2. The twelve edited maps

### 2.1 Summary

| Map | Name (world) | Real changes in MAW | Editor-only noise | OpenYAMM copy |
|---|---|---|---|---|
| oute3 | New Sorpigal (mm6) | **Teleporters:** +8 decorations, −4 trees, 13 terrain height cells | DDM grew by the 4 extra decoration flags | ODM differs from base: OpenYAMM ship (§2.4) |
| out02 | Ravenshore (mm8) | **Teleporters:** +10 bmodel copies, +8 `dec57`, 83 height + 125 tile cells | 37 bmodels renamed with `_N` suffixes; fog header 0→4096 | = base (scene differs only by 15 decoration names) |
| 7out02 | Harmondale (mm7) | **Teleporters:** +4 bmodel copies, 58 height cells | fog header | = base |
| elemf | Plane of Fire (mm8) | −4 monster spawns; `0x4000` (animated) cleared on 4 lava door-step faces | fog header | = base |
| out05 | Garrote Gorge (mm8) | 3 Dragon actors: HP 1667→800, radius 300→200, one moved | 16 bmodels renamed; fog | = base |
| d12 | Ogre Fortress (mm8) | 3 spawns removed / 2 added near the entrance; 2 Ogre actors radius 100→90 | face extras 2833→657, door slots | = base |
| d18 | Naga Vault (mm8) | +19 monster spawns net; 4 Naga actors → "Naga Empress" (NameId 205, HP 1500); journal scrap object 1→77 | 39 zero-vertex faces dropped; 14 door slots; light type 0→5 | = base |
| d08 | Dire Wolf Den (mm8) | Pack Master actor: speed 200→300, attribute `0x200000` cleared | 180 unused vertices; door attrs | = base |
| d42 | Arena (mm8) | 5 faces made ethereal, 1 TriggerByTouch flag cleared, at the south gate | door slots | = base |
| d04 | Temple of Baa (mm7) | All 35 actors re-tiered and renamed (NameId 211–214), HP raised | door slots | = base |
| 7d33 | Castle Gryphonheart (mm7) | 6 guard actors no longer carry item 806 (Graceful Sword) | door slots | = base |
| mdt09 | Wromthrax's Cave (mm7) | Wromthrax's stored stats: level 90→55, gold dice 44→100, attack dice 14→8 and two more stat bytes | none | = base |

No map has new or removed chests, chest contents, map variables or face-attribute overrides in the delta.

### 2.2 Teleporter sites

As built (2026-10-24, the user's design, DEVIATIONS 49): each town has one pedestal (`ped06` under a `dec57` orb,
event 1777) at New Sorpigal (-7592, -1203, 1044), Ravenshore (18472, -543, 65) and Harmondale (-16635, 14521, 711),
which opens the dimensional travel destinations (`evt.OpenDimensionDoor()`). Since Verdant's removal (2026-11-09) the
pedestals are every ruleset's: `worlds/<world>/maps/<map>_dimensional_travel.scene.yml` and event 1777 in the world's
`<map>_mmmerge.lua`, no quest gate, beside MMerge's town fountains (New Sorpigal 140, Ravenshore 104, Castle
Harmondale's courtyard water 65031). The sites and events below are MAW's own.

All three sites use the same three events. Each map overlay must register them (event ids 1777, 1888 and 2666 are
free in our generated oute3, out02 and 7out02 events):

| Event | Hint | Target |
|---|---|---|
| 1777 | "Antagarich" | Survival mode (oute3 only): `7out01.odm (12567, 1728, 1)` dir 512. Else QBit 527 ("Able to use boat to get off Emerald Island"): `7out02.odm (-16832, 12512, 372)` dir 0; else `7out01.odm (12552, 800, 193)` dir 512 |
| 1888 | "Jadame" | QBit 93 ("You have entered out02.odm"): `out02.odm (10219, -15624, 265)` dir 0; else `out01.odm (3560, 7696, 544)` dir 0 |
| 2666 | "Enroth" | Survival mode (7out02 only): `7out01.odm (12567, 1728, 1)`. Else `oute3.odm (-9729, -10555, 160)` dir 512 |

All moves except the Survival ones use icon 3 and house 0. MAW's `vars.SuvivalMode` (sic) is set at new game when
`Game.Mode == 1`.

**oute3, New Sorpigal (decorations only).** A plaza along `y = -1024`, `x -12100 .. -7327`:

- West, Antagarich: `ped06` pedestal (decoration list id 12) at `(-11775, -1024, 864)` facing 1522, event 1777,
  flags 1; `dec57` "path marker" (id 300, light radius 96) on top at `(-11775, -1024, 1024)` facing 558, event 1777,
  flags 1; `Corinth` columns (id 149, no event) at `(-12100, -1024, 864)` facing 482 and `(-11400, -1024, 864)`
  facing 518.
- East, Jadame: `ped06` at `(-7702, -1024, 896)` facing 1522, event 1888; `dec57` at `(-7702, -1024, 1050)`
  facing 558, event 1888; `Corinth` at `(-8027, -1024, 896)` and `(-7327, -1024, 896)`.
- Removed: `6tree05` at `(-10912, -1736, 670)`, `(-11504, -344, 876)`, `(-12256, -688, 796)`, `(-7392, -760, 825)`.
- Terrain: 13 height cells in `x 40..50, y 65..67` set to 27 (west, z 864) and 28 (east, z 896).
- OpenYAMM notes: `ped06` and `dec57` already have outdoor model bindings in `engine/models/decorations.yml`;
  `corinth` is bound only in `indoor_decorations.yml` and needs an outdoor binding. Our ship (bmodels 85–89 near
  `(2100, -10224)`) is far from the plaza.

**out02, Ravenshore (bmodel copies).** A plaza east of town, `x 19531..21793, y -3911..-1151`, terrain flattened to
height 2 (z 64): 83 height cells and 125 tile cells in `x 100..111, y 64..77`. Every new bmodel is an exact
translated copy of a base bmodel (same face order):

| New bmodel | Source (base index, position) | Offset | Face changes |
|---|---|---|---|
| 125 `Out02Temple_N_4` at `(20000, -1620, 64)` | 108 `Out02Temple_N` (Sanctum piece) `(20704, -18944, 1536)` | `(-704, 17324, -1472)` | faces 0–11 (`t14c01b`, `x 19776..20288, y -1876..-1364, z -320..448`): event 186 → **2666** |
| 128 `d28entrance_1` at `(20700, -2882, -400)` | 73 `d28entrance` (Tomb of Lord Brinne) `(19272, 12592, 1088)` | `(1428, -15474, -1488)` | faces 8–15 (`t14a05`, `x 19740..20252, y -3138..-2626, z -208..560`): event 405 → **1777** |
| 121–124, 126, 127, 129, 130 `Obelisk_*` | 65 `Obelisk` `(16760, 21632, 640)` | to `x 19600/20400 × y -1220, -2020, -2480, -3280`, z 64 | none: all keep event 150 |

Plus eight `dec57` markers (no event, flags 0) on the obelisk tops at `(19600|20400, -1220|-2020|-2480|-3280, 800)`.

Side effects carried over by copying: the temple copy keeps event 186 (hint "Sanctum", no action) on 46 faces; the
tomb copy keeps hint 405 "The Tomb of Lord Brinne" on 50 faces and the event 506 face ("Enter the Tomb of Lord
Brinne" → `d28.blv`) at `x 19740, y -2946..-2818, z -1488..-1232`, below the plaza (probably unreachable); each
obelisk copy keeps event 150 (obelisk message #7, autonote 14, QBit 187), so the first click on any of them gives the
obelisk reward of the real obelisk in the far north-east.

**7out02, Harmondale (bmodel copies).** Two copies of the Land-of-the-Giants shrine (base bmodel 71 `Shrine_` at
`(7600, -5248, 224)` and its roof, bmodel 70 `Shrine__1` at `(7704, -5248, 320)`):

| Site | Bodies | Offset | Teleport faces |
|---|---|---|---|
| Enroth (2666) | 114 `Shrine__4` `(-16091, 16709, 1048)` + roof 116 `Shrine__5` | `(-23691, 21957, 824)` | faces 42–49 (`Hhp2b2` pedestal, `x -16043..-15979, y 16677..16741, z 952..1144`): 221 → **2666** |
| Jadame (1888) | 117 `Shrine__2` `(-15803, 7970, 780)` + roof 115 `Shrine__3` | `(-23403, 13218, 556)` | faces 42–49 (`x -15755..-15691, y 7938..8002, z 684..876`): 221 → **1888** |

Each body keeps four "Altar" faces (`Hhp1b`, event 221), which move the party to `out12.odm` (Land of the Giants)
once QBit 758 is set, and 52 "Shrine" faces (222, hint only). Terrain: 58 height cells in `x 29..37, y 30..38`
(`x -17920..-13312, y 12800..17408`) reshaped around the Enroth shrine; the arrival point `(-16832, 12512)` and the
Jadame shrine lie just outside that area.

### 2.3 The other nine maps

- **elemf, Plane of Fire.** Spawns removed (all `type 3` monster, `index 1`, radius 32, z 0): `(2848, -18720)`,
  `(384, -20416)`, `(-3392, -20640)`, `(4384, -21184)`, near the southern arrival area. The `LavTyl` door-step face
  of four houses (bmodels 17, 25, 27, 29; events 12, 18, 20, 22) loses `0x4000` (animated texture); purely visual.
- **out05, Garrote Gorge.** Actors 0–2 (monster info 72 Dragon, NameId 3 "Dragon Hunter Pet", ally 15): HP
  1667→800, radius 300→200; actor 1 moved from `(-6112, -9376, 288)` to `(-6001, -8685, 586)`. Actor 3 unchanged.
  MAW recomputes monster HP at runtime anyway (COMBAT.md), so only position and radius matter.
- **d12, Ogre Fortress.** Spawns (group 10, radius 32, monster) removed `(-3456, 768, 0)` index 1,
  `(-3456, -640, 0)` index 3, `(-3968, 768, 0)` index 3; added `(-4398, -561, 0)` index 1, `(-3968, 768, 0)` index 1.
  Ogre actors at `(-17408, -2176, -1088)` and `(-13952, 512, -848)`: radius 100→90 (unsticking).
- **d18, Naga Vault.** Spawns 18→37: removed `(-556, -954, -112)` i1, `(-224, -892, -112)` i1, `(-640, -768, 0)` i2,
  `(-1024, -1024, 0)` i2; added 23 (index 1 ×4, 2 ×6, 7 ×2 "M2a", 10 ×7 "M3a"), listed in the YAML. The four Naga
  actors (monster info 171) at `(1154|1842, -1242|-1666, 760)` become bosses: NameId 205 (`zSERIOUSMAW.lua` names it
  "Naga Empress"), HP 467→1500, speed 200→235, radius 100→90, attribute `0x200000` cleared. The journal scrap on
  the floor `(2048, 368, -128)` (item 737) changes object type 1 (longsword sprite) to 77 (scroll); no effect in
  OpenYAMM, which draws ground items as models.
- **d08, Dire Wolf Den.** The single pre-placed actor (Pack Master, NameId 11, monster info 39) gets speed 200→300 and
  loses attribute `0x200000`. Geometry identical (180 unused vertices dropped).
- **d42, Arena.** South gate, sector 1: the two lintel faces `Gcst2cel` at `x 3552|4128, y 2560..3072, z 448..512`,
  the top face `Gcst2cel` at `x 3552..4128, y 3072, z 448..512` and the two `Gcst2flr` slabs at `z 448` and `z 512`
  over `x 3552..4128, y 2560..3072` gain `0x20000000` (ethereal); `Gcst2-bs` at `x 3968..4096, y 2560, z 192..448`
  loses `0x80000` (trigger by touch). MAW's Endless Arena spawns monsters at the north end, so the change most likely
  stops monsters snagging on the gate structure.
- **d04, Temple of Baa.** Every actor changes in place (positions, groups, sprites kept):

  | Base (info, NameId, HP) | MAW (NameId, HP) | Count | MAW name (`zzMaw-Monsters.lua:3634`) |
  |---|---|---|---|
  | 214 "Cleric Moon A", 111, 40 | 211, 252 | 19 | Cleric of Baa |
  | 215 "Cleric Moon B", 111, 100 | 212, 370 | 8 | Priest of Baa |
  | 216 "Cleric Moon C", 111, 180 | 213, 508 | 7 | Cardinal of Baa |
  | 216, 112, 180, carries 1332 (Cloak of the Sheep) | 214, 508 | 1 | High Cardinal |

  The exporter's `monster_id` field (`0x7C`) scales with HP in both versions (200→1251 …); it is a stored stat,
  not an id.
- **7d33, Castle Gryphonheart.** Six actors (monster info 260 "Fighter Plate B", group 55, NameId 110 "guard") stop
  carrying item 806 (Graceful Sword), removing a farmable drop.
- **mdt09, Wromthrax's Cave.** Only stored stats inside the one actor record change (level 90→55, treasure dice
  44→100, attack dice 14→8, two later bytes). The scene exporter does not keep these fields; MAW's runtime monster
  stats override them anyway.

### 2.4 OpenYAMM's own copies

- `assets_dev/worlds/mm6/maps/oute3.odm` (git `856f27d96` and earlier): five ship bmodels `mm6_ship_477_0..4`
  appended as bmodels 85–89, the boarding face on `mm6_ship_477_2` carries event 29, and the `SHP` decoration at
  `(2100, -10224, 0)` (event 29, flags `0x40`) is blanked. `oute3.scene.yml` holds the matching interactive faces;
  `oute3.scene.1.yml` overrides actor 37's position. OpenYAMM made the same ship change to outc2, outd1, outd2,
  outd3, oute1 and oute2 (not MAW maps).
- `out02.scene.yml`: 15 nameless entities with decoration id 13 are stored as `"null"`/0
  (`tools/remap_mm8_scene_decorations_to_mmerge.py`). `out02_1.scene.yml`, `out05_1.scene.yml` add weather;
  `d42_1.scene.yml` holds the arena configuration (party position `(3849, 5770, 1)`, 20 monster positions).
- Everything else of the twelve maps is base. Because OpenYAMM only appends bmodels, the base indices MAW uses (and
  that `map_overlays.yml` cites) are valid in our files.

### 2.5 How the map edits would be expressed

Existing scene overlays (`game/maps/OutdoorSceneYml.cpp:2495`, `IndoorSceneYml.cpp:1380`; files
`<map>.scene.N.yml` or `<map>_*.scene.yml`, loaded in sorted order from `Data/games`) support:

- outdoor: `environment`, `terrain.attribute_overrides` and `footstep_sound_overrides`,
  `bmodel_faces.interactive_faces` (per-face attributes and event ids, merged), `authored_content` (append
  entities, spawns, actors, sprite objects, chests), `initial_state.actor_position_overrides` and
  `actor_npc_id_overrides`;
- indoor: `runtime_restrictions`, `arena`, `initial_state.face_attribute_overrides`.

| Need | MAW maps | Status |
|---|---|---|
| Append decorations with events | oute3, out02 | supported (`authored_content.entities`) |
| Remove decorations | oute3 (4 trees) | **missing**: an `entity_removals` list (name + position) |
| Terrain height and tile cells | oute3, out02, 7out02 | **missing**: only attribute overrides exist |
| New bmodels | out02, 7out02 | **missing**. Options: (a) `bmodel_instances` (source bmodel index, offset, face event overrides) — matches MAW exactly, every copy is a translation; (b) GLB props bound as decorations; (c) ship edited ODMs per ruleset, which conflicts with base updates |
| Face events/attributes on new bmodels | out02, 7out02 | supported once (a) exists (`interactive_faces` by bmodel/face index) |
| Outdoor spawns | none | — |
| Outdoor actor HP/radius/position | out05 | position supported; radius/HP not (and HP is ruleset math anyway) |
| Indoor spawn add/remove | d12, d18, elemf (outdoor removal) | **missing** for indoor; outdoor removal missing |
| Indoor actor overrides (NameId, HP, carried item, speed, radius) | d04, d18, d08, 7d33, d12, mdt09 | **missing**: add `actor_overrides` by actor index to both overlay kinds |
| Indoor face attributes | d42 | supported (`face_attribute_overrides`) |
| Face event override | 7d12/7d37 book fix (§3.4) | **missing** for indoor |

Recommendation: express teleporters as (a) bmodel instances plus terrain cells, keep everything else as overlay data
(named `<map>_zz_maw.scene.yml`, which sorts after `<map>.scene.N.yml` and `<map>_1.scene.yml`), and gate all of it on
the ruleset (the overlay loader mounts by file name today; a MAW-only overlay needs to live in a
ruleset package that is mounted only for MAW games, see §3.0).

---------------------------------------------------------------------------------------------------------------------

## 3. Map scripts, event by event

### 3.0 Conventions for an OpenYAMM port

- **Never port MAW's whole files.** MMExt map scripts run beside the compiled EVT; `Game.MapEvtLines:RemoveEvent(n)`
  plus `evt.map[n] = …` is a replacement of one event. In OpenYAMM that is `ReplaceMapEvent(n, hint, fn)` in an
  overlay; new events are `RegisterEvent`, load-time code `RegisterMapOnLoadEvent`, timers
  `RegisterMapTimerEvent(id, seconds, fn)` (interval in game seconds; one MMExt `const.Minute` is 60), NPC hooks
  `RegisterNpcExitHook`, kill hooks `RegisterMonsterKilledHook` (all in `event_support.lua:1583–1640`).
- **File placement and order.** `GameDataLoader.cpp:319` appends every `events/maps/<map>_*.lua` (and `<map>.fixup.lua`)
  in sorted order; `AssetFileSystem::enumerate` sorts names. `oute3_maw.lua` would load *before*
  `oute3_mmmerge.lua` and lose any conflicting replacement. Use a name that sorts last (`<map>_zz_maw.lua`) or,
  better, a ruleset package mounted only for MAW games with an explicit order after world overlays. Global content
  goes to `engine/events/Global_zz_maw.lua` under the same rule.
- **Variables.** MMExt `MapVarN` = OpenYAMM `MapVar(N+2)` (`support.mapVar` adds `0x7B`); `mapvars.name` →
  `evt.GetMapVar("name")`/`evt.SetMapVar` (`MM8.GetMapFlag` wraps it); `vars.name` → `evt.GetGlobalVar`/
  `SetGlobalVar` or `MM7.GetCrossVar` for cross-continent state; `Party.QBits[n]` → `IsQBitSet(QBit(n))`.
- **Missing runtime pieces** used by many MAW scripts:
  - `pseudoSpawnpoint{monster, x, y, z, count, powerChances = {A, B, C}, radius, group, transform}` summons a
    Monsters.txt id with tier weights and then edits the actor (HP multiplier, `NameId`, spell, carried item,
    velocity, hostility). `evt.SummonMonsters` only takes a map-stats encounter slot. Needed: a
    `SummonMonstersById` call with tier weights and an actor-override table (name index, HP scale, item, speed,
    spell, hostile).
  - PlaceMon names 205, 211–214, 300, 301 (and MAW's 220–299 boss name pool): our `place_mon.txt` has 162 rows.
  - `Game.ShowStatusText`, `Message`, `Question` exist as `evt.StatusText`, `evt.SimpleMessage`/`SetMessage`,
    `evt.Question`; party position as `evt.GetPartyPosition`.
- **MAW multiplayer code** (`mawmapvarsend`, `Multiplayer.*`) is dropped everywhere.

### 3.1 MM6 maps

- **outb1 261 Shrine of Cold, 262 Shrine of Fire; outb2 261 Magic; outc1 261 Endurance; outc2 261 Accuracy; outc3 261
  Speed; outd1 261 Personality; outd2 261 Might; outd3 261 Electricity; oute1 261 Poison; oute2 261 Intellect; oute3 261
  Luck**
  - MAW: Same body without the `MonthIs` check: any shrine, any month, while QBit 1230 is clear; first visit +10, later
    +3 (stat QBits 1231–1242). Seven of them lose the "+3 … permanent" status text
  - Base: `if not IsAtLeast(MonthIs, N) then "You pray" return end`, then identical (`outb1.lua` etc.). QBit 1230 is
    cleared by The Seer's "Pilgrimage" (global 1354 in `Global_mm6_mmmerge.lua:139`), once per calendar month
  - Port: `ReplaceMapEvent(261/262)` calling one shared `MAW.PrayAtShrine{qbit, stat, texts}` helper. Note the MAW bug
    in §4.3: Pilgrimage must stay reachable
- **outb1 101 Drink from Well**
  - MAW: `-5000 gold, +5000 XP` through `addExpNoBolster` (bypasses MAW's XP scaling); uses MapVar0; adds a monthly
    `RefillTimer` setting it to 10
  - Base: same exchange through the normal XP path, `MapVar(2)` set to 10 by event 65535 on map refill
  - Port: Replace 101 (XP flagged "unscaled" for the MAW XP rule); add a monthly refill via `RegisterMapRefillHook`
    or a 28-day timer
- **outb3 92 (to znwc)**
  - MAW: Doom (`vars.Mode == 2`): "Access have been destroyed"; else allowed if party member 0 level ≥ 255 or difficulty
    (`Game.BolsterAmount`) ≤ 100, otherwise "You must prove your worth first"
  - Base: Plain move to `znwc.blv (-640, 512, -416)`
  - Port: Replace 92 with ruleset checks
- **oute3 104**
  - MAW: Doom: `outb3.odm (-9477, -13062, 129)` dir 0; else unchanged `(12808, 6832, 64)` dir 512
  - Base: Plain move
  - Port: Replace 104
- **oute3 1777/1888**
  - MAW: Teleporters (§2.2)
  - Port: Register 1777, 1888
- **oute3 30**
  - MAW: Redone only: `evt.HouseDoor(30, 560)` "Tarent Hovel"
  - Port: Skip (OpenYAMM data is not Redone)
- **pyramid 12 (timer, 1.5 min)**
  - MAW: Radiation: 5 damage of Phys/Water/Earth/Air/Fire/Body; Crystal Skull (2086) on the *current* member protects
  - Base: Water/Fire/Air/**Magic**/Physical/Body; skull checked on `ForPlayer(6)`
  - Port: Replace 12 only if MAW's element set matters; otherwise keep base
- **znwc 61 Potions for sale**
  - MAW: Counts purchases in `mapvars.reagentsLooted`; at 50 prints "empty" **but still sells** (no `return`); otherwise
    same items/prices
  - Base: Same items and prices
  - Port: If ported, fix the cap (`return` after "empty")
- **6d05 9 Door (Snergle)**
  - MAW: Key 2108 opens door 9 and summons 18 BDwarves (6 groups of 3, tiers B/C, around `(-556..420, 8507..8721)`);
    **key not removed, no QBit 1051 check**
  - Base: Same summons, but refused when QBit 1051 (axe returned) and the key is consumed
  - Port: Drop it (exploit) or port only "door re-openable after the axe" without repeat summons
- **6d18 35 Lever**
  - MAW: Also toggles facet 2255 (`vlcwl3a`, door 53's lava wall, `x 1019..1157, y ~4608`) invisible+untouchable; MP
    mapvar nosync
  - Base: Toggles doors 43 and 53
  - Port: Fix door 53's face set or add an index-based facet-bit call; candidate for Standard if the wall really blocks

### 3.2 MM7 maps

- **7out02 1000 (timer 0.5 min)**
  - MAW: Goblin ambush once (`mapvars.ambush`) when the party is in `x 17390..19429, y -20015..-19454, z < 800`: Goblin
    (271) ×2 at `(19613, -17760, 1595)`, ×2 `(19307, -18344, 1568)`, ×2 `(18344, -18861, 1666)`, ×8 `(16201, -21635,
    3022)` r1400; tiers 60/30/10
  - Port: `RegisterMapTimerEvent` + party-position box + summon-by-id
- **7out02 load + 1001 (timer 5 min)**
  - MAW: Once per map: Ogre Mage Apprentice (106) named "Goblin's Lieutenant" (NameId 301) at `(8200, 4098, 385)`, HP
    ×3, spell 100 %, speed 0. While not killed and party within 2000: 4 Goblins (271) per tick at `(6613, 2546, 122)`,
    `(6601, 5690, 122)`, `(9765, 2500, 122)` ×2; stops after 10 ticks or the lieutenant's death
  - Port: On-load summon, `RegisterMonsterKilledHook` on name 301, timer
- **7out02 2666/1888**
  - MAW: Teleporters (§2.2)
  - Port: Register
- **7out02 303/304/305, hint 217**
  - MAW: Redone only: Emerald Island/Evenmorn teleportal keys and Harmondale hub
  - Port: Skip
- **7out02 (dropped)**
  - MAW: MAW's file is an old base copy: **drops** Judge Grey's 6-month death (event 211 removal,
    `HarmondaleRebuiltDate`) and the Arbiter messenger (QBits 646, 665, NPC moves 406/407/414–417)
  - Base: `7out02_mmmerge.lua` keeps both (`MM7.UpdateJudgeGreyDeath`)
  - Port: Keep ours; add MAW content only
- **7out05 1000/1001 (timers 5 min)**
  - MAW: Deyja nights: warning "The night is dark…" from 21:30; between 22:00 and 04:00 a 10 % chance per check (forced
    after 23:54) starts 10 spawn rounds of Rotted Corpse (427, tiers 50/35/15, hostile, speed 350) around the party:
    first round 5 at the party r4000 + 8 at `±4000` offsets; each round 3 + 8
  - Port: Two timers, `CurrentGameMinutes()` time of day, summon-by-id at party offsets
- **7out05 505**
  - MAW: Redone only: Erathia portal key 1472
  - Port: Skip
- **7out01 (whole file)**
  - MAW: Everything is inside `if isRedone then` (detected by item 1466 being named "Emerald Island"): tavern topic
    filter, `Map.Monsters[20].NameId = 0`, wells 221/222 rewritten, event 223 "return to EI" invasion of ~130 Giant Bats
    (205) + Cristalyn (NPC 1184)
  - Base: Base file: only the no-Arcomage tavern filter (`7out01_mmmerge.lua`)
  - Port: Nothing to port; with non-Redone data MAW **drops** the base tavern filter
- **7d06 load**
  - MAW: Once per map: Skeleton Warrior (397) ×3 tier A + ×1 tier B at `(-3954, 5878, -95)`
  - Base: Mechanism fixes (in our exporter, `MMERGE_INITIAL_MECHANISM_STATE_FIXUPS`)
  - Port: On-load summon
- **7d11 load**
  - MAW: Opens doors 1 and 2 if MMExt MapVar15–17 (our 17–19, the three pillar keys) are all set
  - Base: Event 1 (onLoad) resets the key counter `MapVar(20)` to 0, so keys inserted across visits never reach 3 and
    doors 1/2 stay shut
  - Port: **Standard fix**: `RegisterMapOnLoadEvent` opening doors 1/2 when `MapVar(17..19) ≥ 1`
- **7d20 196 Wine Rack**
  - MAW: Same probabilities; gives items 225/229/230/224/240 (MM8 potions: Cure Disease, Heroism, Bless, Cure Weakness,
    Might Boost) instead of 1025/1029/1030/1024/1040 (MM7 reagents)
  - Base: Our `MapVar(6)` = MAW `MapVar4`
  - Port: Replace 196 only if MAW's alchemy wants potions here (MAW renames 224–240, ITEMS.md)
- **7d21 1000/1001 (timers 1 min)**
  - MAW: "It's a trap!": party in `x -1183..526, y 10342..12144` → Troglodyte Drone (412) ×8 (70/30/0) at `(-3723, 9579,
    1)`. Then "Queen Arrived!" in `x -5321..-4316, y 8514..9882` → ×10 (70/30/0) + 1 tier C with HP ×2 at `(-6396, 6862,
    1)`
  - Port: Two timers with boxes; summon-by-id
- **7d24 1000/1001 (timers 1 min)**
  - MAW: "Monsters swarming..." in `x -8205..-7060, y 6216..7546`: 4 Troglodytes (412, 50/35/15) at
    `(-7532, 7495, -1535)`, then one more per game minute for 19 minutes and on the 20th a Manticore (296, tier B)
    boss: HP ×2.5, no missile, spell 6 at 100 % skill 3, speed 400, carries item 410 (Incinerate) if
    `bolsterLevel > 25` else 405 (Fireball)
  - Port: Timers; summon-by-id with overrides
- **7d24 (dropped)**
  - MAW: **Drops** event 416 throne-room check by QBit 647 and the Dwarf King exit hook clearing QBit 658
  - Base: `7d24_mmmerge.lua` keeps both
  - Port: Keep ours
- **7d29 1000 (timer 1 min)**
  - MAW: When group 56 is dead (once per game, `vars.goblingKing`): "Noises from the throne room"; Goblin (271) tier C
    named "Goblin King" (NameId 300), HP ×3, speed 400 at `(-5110, 2852, 65)`; 2 tier B at `(-5122, 2219, 1)`; 3+3 tier
    A at `(-4423, 1456, 1)` and `(-5937, 1456, 1)`
  - Port: Timer + `CheckMonstersKilled` + summon-by-id
- **7d29 (dropped)**
  - MAW: **Drops** `Quest_CrossContinents.ContinentFinished[2]` on load when QBit 633
  - Base: `7d29_mmmerge.lua` (`MM7.MarkCrossContinentAntagarichIfComplete`)
  - Port: Keep ours
- **7d32 4**
  - MAW: Always opens door 7
  - Base: Opens door 7 only with QBit 547 (Elven Treasury quest)
  - Port: Replace 4 only if intended; it drops a quest gate
- **7d34 151**
  - MAW: Toggles doors 1 and 2 unconditionally
  - Base: Same, guarded by `Counter(4) < 1`
  - Port: Replace 151; drops the guard
- **7d37 load**
  - MAW: Once per map: Necromancer (307, tier A) at `(-25, 1312, -31)`, HP ×2.5, no missile, hostile, spell 30 % skill
    1, carries wand 174 (Necrotic Wand of Shrapnel) if `bolsterLevel > 25` else 171 (Serpent Wand of Clouds), 66 charges
  - Base: Portrait fix in `7d37_mmmerge.lua`
  - Port: On-load summon

### 3.3 MM8 maps

- **out02 2666/1777**
  - MAW: Teleporters (§2.2)
  - Port: Register
- **out02 (MP)**
  - MAW: Breach/Alvar travel broadcast
  - Port: Skip
- **out01 463 (timer 10 min)**
  - MAW: Same pirate and lizardman respawns; in Insanity stops once `mapvars.piratesSpawned > 25` (counts pirate groups
    10/11 only)
  - Base: Same spawns, no cap (`out01.lua` 463)
  - Port: Replace 463 with a counter and an Insanity check
- **out03 197 Merchant Guildhouse**
  - MAW: Alliance step when QBit 63 (Overdune's quest done) and not QBit 59, **without Overdune in the party**; same
    rewards (10000 XP, award 5, QBits 13–18 and 59, 4000 gold, topics on NPCs 5/13); always enters house 773
  - Base: Requires `HasPlayer(4)` and Overdune in party
  - Port: done, `out03_maw.lua` (MAW players expect it)
- **d05 63/110/45**
  - MAW: MP rewrite: floor-trap timer watches lights 1–8 instead of `MapVar(12)`, button 45 no longer resets
    `MapVar(33)`
  - Base: Base timer 110
  - Port: Skip (multiplayer only)
- **d07 load**
  - MAW: Wererats: hostile branch no longer makes group 8 visible
  - Base: `d07_mmmerge.lua` event 1 sets group 8 visible when hostile
  - Port: Optional one-line change in a MAW overlay
- **d19 15 Door, 131 transformer**
  - MAW: Door opens only with Dyson (roster 34) able to act, or NPC 11's topic D = 634; transformer destroyed only with
    Dyson. **Drops** QBit 19 (Necromancer alliance) and the invisibility path, and the transformer relaxation
  - Base: `d19_mmmerge.lua` keeps the relaxed version
  - Port: `d19_maw.lua` adds only the topic path (Dyson's join offer opens the door without him, read with
    `evt.GetNPCTopic`); the alliance paths and the transformer stay ours
- **d22 5 (load), 452**
  - MAW: `mapvars.mapAffixes` (dimension-map run): clerics hostile and secret button (facet 5) shown; door 452 opens
    with QBit 28 **or** affix run; MAW also drops the Dyson requirement for both (its MP timer still checks Dyson)
  - Base: Base requires Dyson in the party for the button and door
  - Port: done, `d22_maw.lua` (QBit 28 without Dyson; a run needs neither)
- **d26 131 Sarcophagus**
  - MAW: Once per game (`vars.sarcophagus`)
  - Base: Guard QBit 81, which is set only when the party holds 612 and 627; a map refill shows the facet again and
    allows a second Sarcophagus
  - Port: **Standard fix**: guard on a global var set at pickup
- **BrBase**
  - MAW: MP maze sync; monster level filter commented out (any level in the Breach maze)
  - Port: Skip; OpenYAMM has no Breach maps

### 3.4 Map rules in General scripts

- **Dungeon entrances (`General/zzMaw-Maps.lua:285–751`).** `addDungeonEntrance` replaces 110 entrance events on 36
  outdoor maps with "offer a reset if this dungeon is completed, then `MoveToMap`", and 10 more are rewritten by hand
  (out02 504 Escaton's Crystal, out07 504, out13 503/506, 7out03 504, 7out04 503, 7out05 503, outb1 90/100,
  oute3 101); the hand-written ones keep their conditions. Compared with our generated events:
  - outa1 90 (The Hive) **drops** `if IsQBitSet(QBit(1261)) then return end` (sealed after the MM6 ending);
  - out11 505 ("Enter Dwarven Barrow", Barrow VII) goes to **`mdr01.blv`** instead of `mdk01.blv` (MAW bug);
  - out01 503 and out03 502 change the arrival direction, out01 504 house 346→345;
  - most others differ only in the transition picture (house id/icon from a newer MMMerge numbering); keep ours.

  OpenYAMM should not rewrite entrance events. The reset prompt belongs in one ruleset hook before `MoveToMap`
  (keyed by destination file, completion state per map file). The existing `MapTransition` hook
  (`GameplayDialogController.cpp:1280`) fires only for outdoor edge travel, so a new hook kind is needed.
- **Respawn**: outdoor maps (MapStats 1–8, 13, 62–70, 72–74, 99, 100, 140, 141, 143–151) get `RefillDays = 10^9`
  (no respawn); in Insanity every map. Map-stats data, not events.
- **Barrels** (MM6 events ≥ 20000): a barrel that changed a stat is remembered per map in `vars.usedBarrels` and
  becomes "Empty Barrel" (event 19999) after reload or refill.
- **MM6 sprite restore**: MapStats 137–203 rename `rock01..14` → `Rok1..9`, `flower01..13` → `6Flower01..13`,
  `Corpse..Corpse19` shifted by one. Check against our MM6 decoration aliases before porting; likely obsolete.
- **Book switches** (`General/zzMaw-BookSwitches.lua`): 7d12 face 1817 and 7d37 face 896 get the door events 3 and
  10 instead of bookcase event 200. Our 7d12/7d37 have the same bug. **Standard fix** (needs an indoor face-event
  override).
- **Trainers** (`Global/zzMAW_MoveTrainers.lua`, `enableAllTrainers`): 64 `evt.MoveNPC` calls on load of 19 maps
  (oute3, outc2, outa2, d17, 7out02, 7out03, 7out04, 7out13, out01–out07, out09, out10, out13, out14). Several NPCs are
  listed on more than one map (172, 175, 178, 214–216, 530–538), so such a trainer lives in the house of the map
  the party loaded last. In OpenYAMM this is better as a ruleset table "extra residents per house" than as moves.

### 3.5 Base behaviour MAW drops (consolidated)

| Where | Dropped | OpenYAMM today |
|---|---|---|
| 7out02 | Judge Grey dies within 6 months; Arbiter messenger | kept (`7out02_mmmerge.lua`) |
| 7d24 | Throne room by QBit 647; Dwarf King QBit 658 unstick | kept (`7d24_mmmerge.lua`) |
| 7d29 | Cross-Continents Antagarich completion | kept (`7d29_mmmerge.lua`) |
| d19 | Necromancer-alliance and invisibility paths; transformer without Dyson | kept (`d19_mmmerge.lua`) |
| 7out01 (non-Redone) | No Arcomage in Emerald Island taverns | kept (`7out01_mmmerge.lua`) |
| outa1 90 | Hive sealed after the ending (QBit 1261) | kept (generated) |
| out11 505 | Barrow VII destination | kept (generated) |
| 6d05 9 | Door locked after the axe is returned (QBit 1051); key consumed | kept (generated) |
| 7d32 4 | Door 7 only with QBit 547 | kept |
| 7d34 151 | `Counter(4)` guard | kept |
| d22 5/452 | Dyson required for the secret button and door | dropped as MAW does (`d22_maw.lua`) |
| out03 197 | Overdune in the party | dropped as MAW does (`out03_maw.lua`) |
| d19 15 | Dyson in the party for the inner door | also opens on his join offer (`d19_maw.lua`) |
| d07 | Group 8 visible when hostile | kept (`d07_mmmerge.lua`) |
| The Seer slot A | "Pilgrimage" topic (hidden by Dimensional Maps) | kept |

### 3.6 MAW fixes worth adopting in the Standard ruleset

1. 7d11 pillar doors (§3.2).
2. d26 Sarcophagus once per game (§3.3).
3. 7d12/7d37 book switches (§3.4).
4. Galvinus Pure Accuracy QBits 132/133 (§4.1); our `Global.lua` 244/246 still sets 133 and 134.
5. Saving Goobers loop precedence (§4.6), once the quest exists in OpenYAMM.
6. Not MAW but found on the way: our `Global.lua` potion quests 181/203/212/234/240/246 accept only MM8 reagents
   (200–214); MMMerge's `PotionHuntQuest` (`StdQuestsFunctions.lua:491`) accepts every reagent of the right colour
   from all three games through `ReagentSettings`. OpenYAMM lacks that base behaviour.

---------------------------------------------------------------------------------------------------------------------

## 4. Global events, quests and NPC topics

NPC topics in OpenYAMM are slots A–F of `npc.txt` (`# A`..`# F`), set at runtime with `evt.SetNPCTopic(npc, slot,
event)` from a `RegisterGlobalNpcEnterHook`, visibility with `RegisterCanShowTopic`, handlers with
`RegisterGlobalEvent`. MAW uses MMExt `Quest{NPC, Slot, …}`, which shows its topic *in place of* the slot's own
event while its `CanShow` is true (`MMExtension/Scripts/Structs/After/LocalizationAndQuests.lua:745`). New QBits
must come from a declared MAW range at 10000+ (AGENTS.md); MAW reuses empty base bits.

### 4.1 `Global/GLOBAL.lua` (new, 803 lines)

- **Quest reward scaling** (`:5–75`): when an NPC topic gives both gold and experience to member 0, extra gold
  `gold*partyLevel/100 + 250*partyLevel` is added. Needs a "topic reward" hook (gold and XP before/after) in
  OpenYAMM; there is none.
- **Insanity one-time trades** (`:39–49`): handing one of items 643–651 or 1494–1499 to an NPC on screen 13 clears
  the NPC's topic A. The list has `1946` (Deadly Swarm) where `1496` (Crate of Tularean Wood) is meant.
- **Teleport globals** 2666/1777/1888 (`:77–97`): same targets as the map events, without the Survival branch.
  Nothing references them; skip.
- **Potion quests** (`:99–293`, replaces global 181, 203, 212, 234, 244, 246; `zzMAW_PotionQuests.lua` removes the
  base MMMerge `PotionHuntQuest` handlers that would run as well):

  | Event | NPC | QBits (given → done) | Reagents red/blue/yellow | MAW reward | Base reward (our Global.lua) |
  |---|---|---|---|---|---|
  | 181 | 68 Thistle (Dagger Wound) | 113 → 114 | 4/2/1 | item 254, 1000 XP | 265 Pure Speed, 1000 XP |
  | 203 | 74 Rihansi (Alvar) | 115 → 116 | 2/3/3 | item 254, 5000 XP | 264 Pure Luck |
  | 212 | 78 Talion (Ironsand) | 121 → 122 | 2/4/1 | item 254, 5000 XP | 267 Pure Endurance |
  | 234 | 83 Kelvin (Shadowspire) | 123 → 124 | 1/2/4 | item 253, 5000 XP | 266 Pure Intellect |
  | 244/246 | 77 Galvinus (Ravage Roaming) | **132 → 133** | 2/1/4 | item 252, 5000 XP | 269 Pure Accuracy; QBits 133 → 134 |

  Reagent colours accept MM8 200–204/205–209/210–214, MM7 1002–1006/1007–1011/1012–1016 and MM6 1764/1763/1762.
  Reward ids are MAW's renumbered potions (252 Pure Power, 253 Pure Wisdom, 254 Pure Resilience in MAW's
  `ITEMS.txt`), so in a MAW game they come from the MAW item table (ITEMS.md). 244 gets `CanShow` "not 132 and not
  133", 246 "132 or 133" (old saves).
- **Rust potions** 207, 571–576 (NPC 84 Pole, QBits 142–149): identical logic, but potion item 249 (MAW's "Elemental
  Resistance") instead of 256 Fire Resistance; completion XP 7500 at house 1, 1500 elsewhere, as base.
- **Circus trades** 1442–1447 (NPCs 1109 Najat Ramadi, 1165 Kerman Murian, 1166 Irbil Baktarian; houses 1603–1605):
  as base (Golden Pyramid 2092 → strength-6 armour/weapon/misc; Keg of Wine 2093 → strength 4) but capped at 10
  pyramid and 10 keg trades per circus map state (`mapvars.circusLootStrong/Weak`): "We have no more items to
  trade…".
- **Doom mode**: `evt.MoveNPC` 1109, 1165, 1166 to house 0 (circus traders gone).

### 4.2 Respec (`Global/zzMAWRespec.lua`)

- NPCs 314 Oracle (Ravenshore, house 757), 413 **Judge Grey** (Harmondale, house 1165), 794 The Seer (Free Haven,
  house 450); slot D (3). Greeting replaced by "If you seek to pursuit a new path…".
- Topic "Skill reset info" → text → topic "I want to reset". Cost `1000 × level` of the current member. Every skill
  above 1 except Alchemy returns `s(s+1)/2 − 1` points and drops to 1; MAW's shared magic skills for Shaman, Seraph,
  Death Knight and Assassin classes (skills 12–22) are refunded level by level from the highest; custom skills 50–53
  likewise. Masteries are remembered in `vars.oldPlayerMasteries` and restored when the skill grows back. Skill
  points are then raised to at least `Σ(4 + floor(i/10 + 1))` for levels 2..L minus Alchemy spend (merc fix).
  Austerity: Identify Monster GM for everyone.
- OpenYAMM: free slots — 314 D/E, 413 D/E, 794 D/E/F (`npc.txt`). Because OpenYAMM keeps Judge Grey's death, use a
  different Antagarich host (for example a Harmondale temple NPC). Implementation is ruleset C++ (skill and point
  rules, SKILLS_SPELLS_ALCHEMY.md) with a Lua topic.

### 4.3 Dimensional Maps (`Global/zzMaw_DimensionalMapsQuest.lua`)

- Topic "Dimensional Maps" on 314 slot E, 413 slot E, **794 slot A**. On The Seer that slot holds "Pilgrimage"
  (global 1354), and MAW's quest has no `CanShow`, so Pilgrimage is hidden for good. Pilgrimage is what clears shrine
  QBit 1230, so in MAW the MM6 stat shrines pay out once in total. Use slot D/E/F on 794 in a port.
- Tiers by highest member level: 100, then +20 below 140, +15 below 200, +10 after; `Done` at 500. Below the tier:
  "…Return to me when one of you has reached level N." Otherwise gives item 290 (MAW "Map"; our 290 is "Protection
  from Magic" — needs the MAW item table) with a seeded dungeon (MapStats index in `BonusStrength`), 2–4 affixes
  (70/20/10 %), power `min(floor((tier−20)/10), MaxPower)`. Completion is detected on leaving a map that was entered
  with that map's affixes and is `mapvars.completed`; the reward is `level × 1000` gold and XP.
- State: `vars.dimensionalMapsQuest` → one global var table; no QBit.

### 4.4 Druid Circlet (`Global/zzMAW_DruidCircletQuest.lua`)

- Giver 41 Dantillion (Murmurwoods, house 613), slot B (A holds base topic 27). QBit 299 (empty in our
  `quests.txt`; use a MAW 10000+ bit). Item 638 Druid Circlet of Power, chest 3 of d23 (Druid Circle) in our
  `d23.scene.yml`.
- Topic "Druid Circlet"; texts quoted in the file. Reward 3000 gold, 10000 XP and an identified generated amulet of
  strength 5 (MAW rolls rarity). Journal text "Find the Druid Circlet of Power in the Druid Circle and bring it to
  Dantillion in Murmurwoods."
- OpenYAMM: `RegisterGlobalNpcEnterHook` on 41 + `SetNPCTopic(41, 1, <new event>)`, `RemoveItem(638)`,
  `evt.GiveItem(5, ItemType.Amulet)`; works in the Standard ruleset too (pure content).

### 4.5 Dragon Hatchling (`Global/Quest_DragonHatchling.lua`)

- NPC 396 Baby Dragon. MAW adds feedback "Yum! The dragon ate 5 food. Eaten so far: N of 100.", "Grrr! … needs 5
  food", days left after 100 food (28-day wait), a dialog refresh fix, a "Release the dragon" topic (slot B, Y/N,
  removes him for good), and sends a grown dragon who joined as a character to the Adventurer's Inn of every
  continent instead of back into NPC followers.
- OpenYAMM has its own simpler port (`worlds/mm7/events/Global_mm7_mmmerge.lua:36–106`: global event 789, cross vars
  `DragonFood`, `DragonFirstFeedMinutes`, `DragonGrown`, `DragonJoined`; the grown dragon joins as follower NPC 396).
  The feedback texts, days left and Release topic port directly; the inn part does not apply.

### 4.6 Saving Goobers (`Global/Quest_SavingGoobers.lua`)

- Step "SG_ActivateTheTele" on Verdant (OpenYAMM `CrossContinents.Config.VerdantNpcId = 803`), slot C, QBit 466:
  Philosopher's Stones (219 or 1021) needed 10 → **1**. The loop is fixed to
  `while left > 0 and (take(219) or take(1021))`; base `take(219) or take(1021) and left > 0` keeps eating stones
  past zero.
- OpenYAMM has no Saving Goobers implementation (no Telelocator logic; QBit 466 empty). Port the base quest first;
  the precedence fix is Standard, the stone count is MAW.

### 4.7 Endless Arena (`Global/zzMaw_Arena.lua`)

- NPC 313 Arena Master; slot B "Endless Arena" (A is base topic 704). Explains the mode,
  then "Start Level N" with N = `vars.highestArenaWave + 1`; starting hides slots A/B and moves the party to
  `d42.blv (3850, 5776, 1)` dir 512.
- Level L spawns 3 waves; each wave has six states: 8–10 / 6–8 / 4–6 / 3–4 / 2–4 monsters with tier weights
  80/20/0, 65/25/10, 50/30/20, 35/35/30, 20/40/40, then one tier-C boss (`generateBoss`). Monster kind cycles
  through MAW's level-sorted pool `monTbl` (`zzMaw-Maps.lua:774`). 14 spawn points (z 1): `(3850|4600|3100, 9350)`,
  `(5500, 8600)`, `(2200, 8600)`, `(6500|1200, 7600|6600|5600)`, `(6500, 3600)`, `(1200, 4600|3600)`. Corpses drop
  nothing. Clearing a level pays `L × 20000` gold and records the wave. Buffs are restored after the reload.
- OpenYAMM has a native arena (`d42_1.scene.yml`, `runtime_restrictions.arena`); Endless Arena is a new arena mode
  for that runtime (C++), not a map script. The d42 gate faces (§2.3) belong with it.

### 4.8 Bounty hunts (`General/BountyHunt.lua`)

- MM6 town-hall topic 1712 (OpenYAMM C++: `EventDialogContent.cpp:28`, `IsTotalBountyInRange`). MAW: reward
  `round(baseLevel + getPartyLevel(4)) × 100` from MAW's base monster level; the target is drawn from MAW's pool
  `monTbl`, spawned and turned into a MAW boss (`generateBoss`, name from the 220–299 pool; old saves fall back to
  name 299); the text names the map; a free map note is used; a new hunt is only
  offered once the current map is `mapvars.completed` ("You need to clear the area COMPLETELY first."); in Insanity
  the hall also lists unfinished hunts on other maps.

### 4.9 Other content touching NPCs

- `General/NPCFollowers.lua`: Doom mode refuses hiring except in houses 1466 and 1486 (both "House", map 144).
- `General/NPCMercenaries.lua`: Beyond Madness disables the Adventurer's Inn mercenaries (UI_CONTENT §3).
- `Global/ExtraArtifacts.lua` ships empty (MAW computes artifacts itself, ITEMS.md); `zzMAWPotions.lua` and
  `zzMaw_Legendaries.lua` are item rules (ITEMS.md, SKILLS_SPELLS_ALCHEMY.md); `zzzzzMaw_Damage.lua` registers the
  damage pipeline (COMBAT.md).

### 4.10 Id mapping summary

| MAW id | Kind | OpenYAMM id / note |
|---|---|---|
| NPC 41, 68, 74, 77, 78, 83, 84, 313, 314, 396, 413, 794, 803, 1109, 1165, 1166 | NPC | same row numbers in `engine/data_tables/npc.txt` |
| Global events 181, 203, 207, 212, 234, 244, 246, 571–576, 1442–1447 | topic events | same ids in `engine/events/Global.lua`; override with `ReplaceGlobalEvent` |
| New topics (respec, dimension maps, circlet, arena, release dragon) | events | allocate a MAW global event range (MMExt used free events 995–1000 dynamically) |
| QBits 113–149 | quest bits | same |
| QBit 299 (circlet), MAW-only flags | quest bits | new MAW range ≥ 10000 |
| Items 249, 252–254, 290 | MAW item ids | MAW `ITEMS.txt` meaning; Standard ids differ |
| PlaceMon 205, 211–214, 300, 301 | names | add rows (ruleset `place_mon.txt`) |
| Monsters 106, 205, 271, 296, 307, 397, 412, 427 | Monsters.txt ids | same names in `monster_data.txt` and MAW `MONSTERS.txt` |
| MMExt `MapVarN` | map variable | `MapVar(N+2)` |

---------------------------------------------------------------------------------------------------------------------

## 5. Corrections to existing docs

Not edited here; to be applied to the named documents.

1. **UI_CONTENT §4.1 / README §2.9.** "out02/7out02/oute3 grew (teleporters), d12/d18/d08/d42 shrank
   (geometry/object edits), 7d33/out05/d04/mdt09 same size (attribute/event edits)": the shrinkage is editor re-save
   (face-extra compaction, unused vertices, zero-vertex faces), and no map besides out02 and 7out02 gains geometry.
   oute3's teleporters are decorations plus terrain, not faces. 7d33, d04, mdt09 and out05 change only actors; d12,
   d18 and elemf spawns; d42 face flags. "Teleporters … map geometry edits" should read "bmodel copies (out02,
   7out02) and decorations (oute3)".
2. **UI_CONTENT §3 Maps table, 6d05.** The key requirement and the 18 summoned guards are base behaviour. MAW's change
   is dropping the QBit 1051 lock and the key consumption, which makes the summons repeatable.
3. **UI_CONTENT §3, znwc.** "capped at 50 purchases" is not true: after 50 the seller says "empty" and still sells.
4. **UI_CONTENT §3, NPCs/quests.** "Seer/Oracle NPCs 314, 413, 794": 413 is Judge Grey (Harmondale). Dimensional
   Maps uses slot E on 314/413 but slot A on 794, hiding Pilgrimage (§4.3).
5. **UI_CONTENT §3, 7out01.** With non-Redone data (OpenYAMM's) the whole file is inert and the base no-Arcomage
   tavern filter is lost; it is a dropped base fix, not a MAW feature.
6. **UI_CONTENT §3, outb1.** The Kriegspire well (−5000 gold, +5000 XP) is base content; MAW only exempts its XP
   from MAW's XP scaling and adds a monthly refill.
7. **UI_CONTENT §3, pyramid.** The Crystal Skull protection is base; MAW changes the damage elements (Magic → Earth)
   and checks the skull on the current member.
8. **UI_CONTENT §3, 7d34.** Event 151 is base; MAW removes its `Counter4` guard. **7d32**: base required QBit 547.
9. **UI_CONTENT §3, d22.** Also drops the Dyson Leyland requirement for the secret button and door 452.
10. **UI_CONTENT §3 / README §2.9, d19.** Besides the invisibility path, MAW drops the Necromancer-alliance (QBit 19)
    path and the transformer relaxation.
11. **UI_CONTENT §3, zzMaw-Maps.lua.** The dungeon-reset rewrite also drops the Hive lock (outa1 90) and sends
    Barrow VII to `mdr01.blv` (out11 505).
12. **UI_CONTENT §3, MoveTrainers.** 64 moves on 19 maps, not "~60 on 18"; NPCs listed on several maps follow the
    party.
13. **UI_CONTENT §3, NPCs/quests** omits GLOBAL.lua: potion quest rewards changed to MAW potion ids, Galvinus QBit
    fix, MM6/MM7 reagents accepted, Rust potions use item 249, circus trades capped at 10, Doom removes the circus
    traders, quest gold scaled by party level.
14. **README §4.2 item 9** ("teleporter sites can be decorations with event faces"): true for oute3; out02 and
    7out02 copy whole buildings, so either bmodel instancing or new props are needed (§2.5).

---------------------------------------------------------------------------------------------------------------------

## 6. Not covered

- **Exact meaning of a few stored actor bytes** (mdt09 stats beyond level/treasure/attack, attribute `0x200000` in
  d08/d18). They are runtime-recomputed in MAW; not decoded further.
- **Sector, BSP and outline data** were compared by count only (geometry faces matched individually). Light records
  in d18 change type 0→5 only.
- **Redone-only branches** (7out01, 7out02 303–305, 7out05 505, oute3 30) and the Redone maps they need.
- **Multiplayer code** in out02, d05, d22, 6d18, BrBase and `Modules/Multiplayer`.
- **BrBase / Breach**: OpenYAMM has no Breach maps.
- **`zMaw.T.lod` mapstats.txt** (monster pictures, counts, treasure levels on ~50 maps; UI_CONTENT §4.1) and
  Monsters.txt: data tables, not diffed per map here.
- **Dimension-map runtime** (`zzMaw-Maps.lua:752–1196`, `zzMaw_Mapping.lua`: affixes, pools, map item use) and
  dungeon completion rules: COMBAT.md §on maps.
- **In-game verification**: nothing was run in OpenYAMM or MMMerge; coordinates and effects come from files only.
- **Item 290 / potion id conflicts** between the MAW and Standard item tables: ITEMS.md.
