# MM9 remake: rebuilding every MM9 map as native OpenYAMM ODM/BLV content

Status: plan only (2026-10-29), with the user's first decisions recorded below. Numbers come from the transcoded
sidecars in `assets_dev/worlds/mm9/maps/` and the original `mm9/extracted/` data; Phase 0 re-measures them with a
script.

## Goal

Recreate all 45 MM9 (Chedian) maps as hand-finished MM6–MM8-style maps: classic ODM (heightmap terrain plus BModels)
for exteriors and BLV (sectors and portals) for dungeons. Layout and landmarks stay faithful to MM9; the result plays
like MM6–MM8: map size, monster density and packs, loot, terrain tiles, our skies, water, weather and lighting,
x4 surface textures, 3D decorations and 3D creatures rebuilt with our pipelines.

What is kept from the existing MM9 work: the world package's content layer (RUDE dialogue, quests and QBits 90000+,
vendors, trainers, temples, transport routes, MM9 items, music, audio). What is replaced: the generated
`bmodel_world` maps (they stay as the reference and fallback until each remade map is accepted, then retire) and the
MM9 monsters' borrowed MM6–MM8 sprites. Classic ODM/BLV also removes the desktop-only limit of the `bmodel_world`
profile, so the remade world can ship on Android.

This is a blueprint job, not an invention job: every map, building, texture, monster, NPC and script already exists in
MM9 and is measured before work starts. Hesper produced 4 ODMs and about 17 dungeons without such blueprints.

## Decisions

| Topic | Decision (2026-10-29) |
| --- | --- |
| Cities | Separate maps, as in MM9. **Format under revision (user, 2026-10-31): BLV + sky preferred over ODM** for performance (walk-in houses are sectors behind door/window portals). To be confirmed by a Sturmford City BLV pilot measuring vertices (16-bit indices), minimap lines (7 000 save-format limit), draw calls and visible sectors in the streets against an MM8 town. Engine needs, if confirmed: our outdoor sky drawn behind BLV sky faces (also upgrades the dungeons' sky faces), a time-of-day scale on static light (MM9's own `LightScale`/`NightLightScale`; confirm in the binary), weather in sectors open to the sky, and outdoor-only rules (e.g. Meteor Shower) asking "open to the sky" instead of "outdoor map". Minimap (user): MM9's painted city map (already in `worlds/mm9/ui/maps/catalog.yml` with world bounds; keep the entry for cities) drawn by the indoor minimap through an opt-in scene setting, which also lets the compiler skip the seen-lines outlines (the 7 000 limit); or an opt-in larger line-map table. Vertices (user: raising is fine): indices are `uint16_t` in the BLV and `IndoorMapData`; if a city exceeds 65 535, widen in memory and add an extended BLV variant for our compiler only (MM6–MM8 BLVs unchanged). |
| Outdoor maps | **BLV open to the sky (user, 2026-11-02)**, not ODM: MM9's terrain mesh, tunnels and structures stay faces of one open-air sector (`level_generation/projects/mm9r_common/outdoor_blv.py`; pilots Isle of Ashes and Sturmford; [the measurements](../../level_generation/projects/mm9r_isleofashes_blv/README.md)). The ODM route (`OUTDOOR_PLAYBOOK.md`) is superseded. The sea is drawn as the outdoor maps' normal sea under the outdoor view. |
| Shops | Keep MM9 walk-in shops and interiors (MM9 identity; shops hold more than the proprietor). Details below. |
| Flying | Fly is replaced by Fleet Foot in the MM9 world (a run-speed buff): done 2026-11-09, `world.yml fleetFoot` (below). |
| Dungeons | Proper indoor BLV maps, with MM9's painted maps (2× Real-ESRGAN, one image per floor by the party's height as in MM9; the MM6–MM8 line map by the Map style setting, the default since 2026-11-10; 2026-11-09, replacing the line-map decision of 2026-10-29) and our own baked indoor lighting from the map's lights (MM9's lightmaps only as a reference; 2026-10-29). |
| Monsters | Regenerated with our 3D pipelines, MM9 models as the reference. Density and packs fit the MM6–MM8 experience. |
| AI | Vanilla MM6–MM8 AI at the core; MM9 behaviours added on demand per actor (see [actor scripting](../ACTOR_SCRIPTING_INVESTIGATION.md)). Later topic. |
| Balance | Calibrated against MM6–MM8 starting areas (below). |
| Party scale | Measured: keep scale 2.56 with the default eye height (MM9 doors already match MM6–MM8 proportions). |
| Water (2026-10-30) | Diving and swimming as a new shared engine feature (the second option under [Water and diving](#water-and-diving)); swimmer monsters such as the Sea Monster and the Jellyspores move in water, not on the floor. |
| MM9 characters (2026-10-30) | MM9 skeleton and MM9 clips, grafted five-finger hands driven from MM9's finger curl, a separate head texture set (Yrsa, `level_generation/creatures/mm9_yrsa_claude/`). Never Mixamo. Applies to the Banshee, Ghost, Imp and the dungeon humanoids. |
| See-through monsters (2026-10-30) | Only the spectral ones are translucent: Banshee, Ghost, Spectre Dagrell. The Jellyspore and the other Dagrells stay opaque. |
| Dragon King (2026-10-30) | Grounded, as in MM9, by a boss script (flies only for its landing); the monster table's flier flag is overridden there. MM9 has no ground walk for the dragon (its Walking/Running are the fly loop), so the script keeps it in place between attacks unless a ground walk is authored. |
| Bird tiers (2026-10-30) | Bird A keeps the crow; Birds B and C take MM9's unused eagle skin (`BIRD.dtx`). |
| Lich promotion (2026-10-30) | The Lich Lab's Transmutation Engine works: any member one promotion from Lich (Wizard, Necromancer) with the Elixir of Defedation and the Lich Instructions. |
| Isle saves (2026-10-30) | Saving stays allowed on the Isle of Ashes; Yrsa stays until the cinema so no reload can lose the Turret Key. |

## Scope: MM9 against MM6–MM8

| | MM6 | MM7 | MM8 | MM9 |
| --- | --- | --- | --- | --- |
| Outdoor maps (ODM) | 15 | 13 | 14 | 20 exteriors: 11 wilderness regions, 7 walled cities, Afterworld, Wizard's Lab |
| Dungeons/interiors (BLV) | 51 | 63 | 47 | 25 |
| Total maps | 66 | 76 | 61 | 45 |

MM9 splits most regions into a wilderness map and a separate city map (Thjorgard + Thjorgard City, Sturmford,
Thronheim, Drangheim, Guberland, Frosgard, plus Arslegard City alone).

### Size

Party bounds on a classic ODM are ±22,528, a 45,056-unit playable square. At the existing DAT→ODM scale (2.56) the
MM9 regions already measure 42–46k across (Guberland 42×43k, Lindisfarne 45×45k, Sturmford 42×48k, Drangheim 45×54k).
The size goal mostly holds already; Drangheim and Sturmford need slight compression or trimming along one axis.
Cities are 13–28k and Bootcamp is 22×23k.

Vertical range: MM9 regions span up to ~8,200 units (Mountain Pass), right at the heightmap ceiling (255 × 32).
Cliffs steeper than the 512-unit terrain grid, overhangs and arches become BModels.

### Party scale

The MM9 world declares `partyMovement.eyeHeight: 152` (collision height 169, radius 38) against the default 176.
The options were a lower eye height per world or bigger doors (scale 2.96, which overflows the 45k bounds).

**Measured (see [checks](CHECKS.md)):** MM9 town doors are 246 × 164 at scale 2.56, which is 1.40 eye heights at the
default 176 against 1.45 for MM6–MM8's 128 × 256 doors. So neither option is needed: keep 2.56 and the default eye
height. The world's current 152 override makes MM9 doors read larger, not smaller; drop it for the remade maps.

### Monster density

| | Outdoor maps | Dungeons |
| --- | --- | --- |
| MM6 | 20–93 spawn points, about 60–390 monsters (typical ~200) | median 32 spawn points, up to 152 |
| MM7 | 11–71 spawn points, about 40–150 monsters | median 17 spawn points, up to 92 |
| MM8 | 46–112 spawn points, about 100–220 monsters | median 16 spawn points, up to 71 |
| MM9 (placed) | 0–76 monsters (Thjorgard 31, Guberland 40, Mountain Pass 76) | 0–173 (Chasm of the Dead 173, Lich Lab 147, 1000 Terrors 114) |

MM9 exteriors carry roughly a third to a fifth of an MM8 map's monsters; several dungeons are already MM-dense.
MM9's `MAPSTATS.txt` has the same random-encounter columns as ours (Enc %, M1–M3 %, monster, difficulty, appear
range); its rows are already imported, so remade maps use ordinary native spawn points (index 1–3) against them.
Target: MM8-like outdoors (about 100–180 monsters in 3–6 packs per encounter area, quiet gaps between areas, per
[wilderness calibration](../../level_generation/WILDERNESS_CALIBRATION.md)), dungeons 60–200.

### Balance calibration

MM9's real starting chapter is Isle of Ashes → Sturmford → Sturmford City, with the Sturmford sewers (Beethoven, four
entrances from the city) and Anskram Keep as the first dungeons. Bootcamp is the tutorial (4 Lobber Pods plus three
scripted L50 figures) and is not a balance reference. Verhoffin Ruins, reached from the isle, is L17–65 and belongs to
a later return.

| MM9 map (placed monsters) | Low-level content | Comparable MM6–MM8 area |
| --- | --- | --- |
| Isle of Ashes (46) | Dragonfly Mite/Dragonfly/Fire Dragonfly, Skeletoid, Bone Thrasher (L2–5), about 1,800 XP in total; also 10 Jellyspores (L15, in water), a Sea Monster (L50) and the Lich King (L65) | Emerald Island: same MM7 Dragonfly A/B/C family |
| Sturmford (56) | 28 dragonflies (L2–5), 16 Field Thralls (L8), 2 Thralls (L12), Basilisks (L15), Spores (L20–25) | New Sorpigal region: Field Thrall in the goblin role |
| Sturmford City (0) | Town, walk-in shops, sewer entrances | New Sorpigal town |
| Beethoven, the sewers (82) | Bone Thrashers (L3), Lobbers and Airborne Ickies (L7), Rotters (L9); 10 `Skeleton` rows at L40 to check | Goblinwatch, Abandoned Temple |
| Anskram Keep (47) | Imps and Nagate Hatchlings (L4–10), a few up to L19 | Second starter dungeon |

Measure each comparable MM6–MM8 area the party leaves at a known level: Emerald Island (MM7), New Sorpigal with
Goblinwatch and the Abandoned Temple (MM6), Dagger Wound Island (MM8). Per area: monsters and total experience,
quests and their experience and gold, chest and drop treasure levels, gold found, shops' stock tier, and the party
level on leaving. Then set the MM9 starting chapter to the same envelope with MM9 monster rows, density and loot.
MM9 has 143 journal quests (`NPC997.rude`) across 45 maps; Phase 0 counts quests per map on both sides to see how
much quest experience the added monsters must replace.

Phase 0 result ([inventory](INVENTORY.md); monster experience only, quests excluded):

| Starting chapter | Monsters | Monster XP | XP per monster |
| --- | --- | --- | --- |
| MM6 New Sorpigal + Goblinwatch + Abandoned Temple | ~667 | ~50,000 | ~75 |
| MM7 Emerald Island + Temple of the Moon | ~106 | ~7,100 | ~67 |
| MM8 Dagger Wound Island + Abandoned Temple | ~234 | ~25,700 | ~110 |
| MM9 Isle of Ashes (L2–15) + Sturmford + Beethoven + Anskram Keep | 229 | ~45,800 | ~200 |

The MM9 chapter is not sparse overall: with its dungeons it matches MM8's monster count and MM6's experience.
It is sparse outdoors (Isle of Ashes 46 and Sturmford 56, against New Sorpigal ~224 and Dagger Wound ~118), and its
experience comes from fewer, higher-level monsters (Sturmford runs L2–25, New Sorpigal L2–11). So the added packs
belong mainly outdoors and at low level, and the experience envelope is a choice: MM6-like (~50k for the chapter)
means low-level packs at MM9's own experience values; MM8-like (~26k) means lowering per-kill experience as density
rises.

## Walk-in shops and interiors

MM9 shops and houses are rooms inside the city map with shopkeepers, customers and other NPCs, opened through RUDE
dialogue (already wired to our shop screens over live gameplay). They stay walk-in, built as BModel interiors inside
the city ODM. Problems to solve in the Sturmford City pilot:

- Weather: rain and snow fall through roofs. The weather plan's baked roof occlusion map is a deferred TODO and
  becomes a requirement for MM9 cities (and helps every MM6–MM8 bridge and archway).
- Lighting: the outdoor bake already darkens sheltered geometry; interiors need their MM9 lights as baked local lights
  and a check that night/day sky fill does not leak through.
- Minimap, sound (ambient and reverb), and doors that read as entrances at MM6–MM8 view distances.
- Cost: city interiors add faces and actors to a map the party walks through constantly. Rebuild them at MM8 face
  budgets and measure city FPS against an MM8 town.

## Water and diving

In MM9 water is a volume over a real seabed and the party dives and swims. OpenYAMM has the MM6–MM8 model only:
water is a terrain tile at the surface, the party drowns standing in it unless Water Walk is active, swimmer
monsters exist (`MonsterKind::Swimmer`, MM8's fish schools), and a map-wide `underwater` flag changes tint and fog.
There is no party swimming, no seabed below a water surface and no breath timer.

Content that sits under water in the DAT worlds (inside water volumes deeper than about 200 units):

| What | Where |
| --- | --- |
| Jellyspore family, 24 | Isle of Ashes 10, Sturmford 5, Thronheim 5, Thjorgard 4 |
| Sea monsters, 3, plus a few other monsters in its water | 1000 Terrors 2, Dark Passageway 1 |
| Items and containers | Dark Passageway 6 world objects, chests in Dook's Castle and Verhoffin Ruins, 3 bone piles in Inventa Storca, a hiding place on Isle of Ashes, a script object in Thronheim |
| Puzzles | 1000 Terrors: 13 weighted lifts and 3 doors under water |

Depths: outdoor seas and lakes 600–1,400 units; indoor pools up to about 1,550 (Bathhouse, Dook's Castle).

Two ways:

- **MM6–MM8 water.** The seabed is flattened to the surface, Jellyspores become surface swimmers, and the few
  underwater items, chests and the 1000 Terrors puzzle move or are redesigned. Native and cheap, but it drops a piece
  of MM9's identity.
- **Diving as a new shared engine feature.** The outdoor heightmap holds the seabed and each water body gets a
  surface level above it, so the whole map rises by the water's depth (fine for most maps; Guberland is already at
  the ceiling). The engine needs a swim/dive state for the party (movement, vertical control, a breath timer),
  rendering from below the surface (the existing underwater fog and tint are a start), swimmers moving in 3D,
  underwater rules for projectiles and spells, seabed items and chests, and the same for indoor pools.

Either way the terrain converter keeps the seabed heights, so nothing is lost while this is decided: raising a
map for diving later is one height offset in its conversion.

**Chosen (2026-10-30): diving.** How MM9 does it, from its binaries (2026-10-31):
[MM9 water and swimming RE](MM9_WATER_SWIMMING_RE.md). Water is a volume brush; under water the party has no momentum,
swims at 150 LT/s (384, our walk speed) along the look direction, Jump/Crouch for up/down, sinks at 102 u/s idle, holds
its breath 15 s and then loses 1/6 of maximum HP every 2 s; ranged weapons are not fired under water; swimmers use
the flyers' class (`AISwimFly`). The integration design (scene `water_volumes`, a shared swim step through the
movement controllers' flying branch, per-volume fog and tint, swimmers bound to their volume, Verhoffin Ruins first,
outdoor last): [MM9 water and swimming design](MM9_WATER_SWIMMING_DESIGN.md).

## Build route

The remade maps are conversions of MM9's own geometry, not new designs: the original layout, buildings, rooms and
landmarks, rebuilt as native ODM/BLV and finished with what MM6–MM8 already have (x4 textures, our terrain
materials, sky, water, weather, 3D decorations and creatures). Hand work goes only where the classic formats need it
(cliffs and gating on the height grid, sectors and portals, door types, face budgets).

- **One conversion project per map** under `level_generation/projects/mm9r_<map>/`: its script reads the DAT, writes
  the terrain and the cleaned BModels (or, indoors, the sectors and portals) as an editor source package, and builds
  the native map through the editor's writer (`openyamm-editor --headless-build-map`). Manual fixes are recorded in
  the project as explicit overrides, so a rerun of the conversion keeps them.
- **Review in an isolated asset root**, then install into `assets_dev/worlds/mm9` when the map is accepted; until
  then the current `bmodel_world` map stays as it is.
- **Engine limits for BLVs** are the same as for any native dungeon; Hesper's
  [dungeon playbook](../../design/kreegan_world/DUNGEON_PLAYBOOK.md) lists them measured (linear movers only, at most
  4 static lights per draw, monster-walkable risers of at most 32, walls between rooms need a thickness).

## Geometry route

Rebuild, not raw conversion. The transcoded Bootcamp has 60,941 render faces (33,552 of them baked props); a native
MM8 ODM has several thousand BModel faces (Dagger Wound Island lists 6,740 face records). The DAT world is the layout
reference, and clean parts are reused.

**Exterior (ODM).**

1. Terrain: resample MM9's `Terrain0` world model to the 128² height grid (heights, then tile families by MM9 terrain
   texture and slope); author edges, roads, shores and liquid masks per
   [terrain materials](../../level_generation/terrain/materials/README.md). Likely new families: alpine rock and grass, snowfield rock,
   volcanic ash; check existing families first.
2. Buildings and structures: import the DAT into Blender (`mm9/io_scene_lithtech`, or the existing transcoded
   BModels) as an underlay. Clean exports (coplanar merge, drop physics hulls, AI rails, perception and visibility
   helpers) where the MM9 mesh is already simple; remodel the rest to MM6–MM8 BModel style. Planar faces, 10-character
   texture names, native winding.
3. Props: MM9 `.abc` props (braziers, carts, furniture, Chedian architecture pieces) convert through
   `convert_abc_model.py` to GLB 3D decorations (`install_model.py --engine`, `check_winding.py`), cleaned to the
   [modelling guidelines](../../level_generation/GAME_ASSET_MODELLING_GUIDELINES.md). Vegetation comes from our grass/meadow system and
   the MM6–MM8 3D tree/bush set for a consistent look.
4. Sky, water, weather: our sky presets ([SKY_RENDERING](../../level_generation/lighting/SKY_RENDERING.md)), our water, and
   `weather.yml` from MM9 `Snow`/`Fog`/`WeatherMan` objects (the weather plan currently excludes MM9; lift that per
   remade map). Outdoor lighting bake as usual.

**Dungeons (BLV).** Blender reconstruction from the DAT underlay: rooms as sectors, doorways and windows as portals,
MM9 doors as native movers. Two starting points exist: the DAT worlds contain LithTech `UserPortal` objects and BSP
leaves, and the older `tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py` already wrote 28 BLVs through
`mm9_compile_indoor_source` with grid- or leaf-cut sectors (not artist-quality portals, but a usable underlay and
compiler test). Simplify to MM8 face budgets (MM9 dungeons have 1–28k source polygons). The 1,017
rotating doors, 482 triggers, 297 script-linked invisible brushes and 68 ladders across MM9 are the main fidelity
risks.

**Textures.** MM9 surface textures are mostly 128² (1,268 of 1,721), the same as MM6–MM8, so they fit the
[x4 surface playbook](../../level_generation/textures_x4/PLAYBOOK.md) once `tex.py` learns an `mm9` world (its `WORLDS` list and
ESRGAN mapping). Codex quota is available, so textures can run alongside geometry, one region at a time.

## Creatures and NPCs

All 151 MM9 ABC models were read with `convert_abc_model.py` (all LithTech ABC v13, all parse).

**Monsters: 50 bodies.** The monster table has 134 rows over 50 models and 119 distinct skin sets. Most families are
one body with three skins (Grey/Black/Red Wolf, Dragonfly/Mite/Fire Dragonfly, Skeleton Warrior/Master), which maps
directly onto our shared texture set plus colour tiers; a few are one body under several names (Dwarven
Guard/Soldier/Commander, Skeleton/Bone Thrasher/Skull Thrower).

- Meshes: 158–1,514 triangles, low-resolution DTX skins. Reference only, not shippable.
- Rigs: every monster has its own skeleton (21–135 joints; high counts are wing, tentacle and cloth chains). No two
  monsters share a rig.
- Animations: 9–35 clips each. The common set matches MM6–MM8 roles: `stand` (40 of 50), `fidget1/2`, `walk`, `run`,
  `hattack1/2` (melee), `rattack1` (ranged), `wince1/2`, `die1/2`, `taunt`, `backpedal`, plus air variants for
  flyers, water variants for swimmers, `resurrect`, `cower`, `search`, `sleep`. Keyframe density varies (wolf walk
  29 keys per 0.9 s; Bandit stand 10 keys per 1.5 s).
- Animation events: clips carry timed events (`footstep`, `lunge`, `bite`, `RangeAttack`, `BreathAttack`,
  `WingAttack`, `playanimsound`). These give attack contact frames and charge/release timing directly, which
  `sprite_attack_timing.yml` and the `actors.yml` sockets otherwise get by hand in the timing review tool.

**NPCs: shared base rigs.** Townsfolk use a few shared skeletons with separate clip libraries:

| Skeleton | Bodies | Clip library |
| --- | --- | --- |
| Human male, 45 joints | 12 peasant variants + 7 named (Bjarni, Sven, Markel, Hanndl, Tryggva, Foraddarre, Njam) | `peasantmale` 43 clips, `peasantwork` 18 (hammer, count…) |
| Human female, 73 joints | 8 peasant variants + 7 named (Yrsa, Skraelos, Fre, Hag, three Wyrds) | `peasantfemale` 20 clips |
| Dwarf male / female | 4 + 4 | `peasantmaledwarf` 21, `peasantfemaledwarf` 10 |
| Half-orc male / female | 2 + 2 | `peasanthomale` 11, `peasanthofemale` 13 |
| Boy / girl | 3 + 3 | `peasantchildboy` 12, `peasantchildgirl` 11 |
| Seated human | seated variants | `peasantseated` 21, `peasantfseated` 8, `peasanthofs1` 5 |

Plus a few unique characters with their own rigs (Kira, Krohn, Sigmund, Scholar, Greenman; Guard, Monk and Nobleman
are monster-table bodies) and about 16 ambient animals (cat, cow, dog, goat, goose, hen, pig, rooster, sheep and ram, mouse,
fish, crow, duck, rabbit, butterfly, gopher). Named characters carry cutscene clips (`Sc2_Bjarni1a`…).

**Route.**

- HD masters (step 0 of the creature playbooks) are made from renders of the MM9 model with its skin in the five
  views, instead of native sprites.
- Non-humanoid monsters: try **MM9 rig reuse**. Model the new Meshy mesh in the MM9 bind pose, weight it to the MM9
  skeleton (transfer from the MM9 mesh, then clean up), and play the MM9 clips and events unchanged. This replaces
  procedural quadruped clips, which the user found weaker than authored ones. Pilot: the Dragonfly family (first
  enemy, a flyer with wing and air clips, three skins as colour tiers). The MM9 dragonfly is serpentine, unlike
  MM7's insect Dragonfly, which is only its current sprite stand-in. The [checks](CHECKS.md) confirm the rig and
  clips are reusable.
- Humanoid monsters and NPCs: the [humanoid playbook](../../level_generation/creatures/CLAUDE_HUMANOID_NPC_PLAYBOOK.md) (source-frame
  rig, library clips) stays the default; MM9 clips retarget for special moves (Lich resurrect, taunts, work and seated
  idles). One retarget map per shared NPC skeleton covers all its bodies. Pilots: Skeletoid/Bone Thrasher (one
  body; the separate-bone skeleton route of `mm6_ske_claude`) and the Field Thrall (first humanoid pack enemy).
- Tooling: the converter needs `pygltflib`, which the system Python lacks; the 844 GLBs the model doc mentions are no
  longer on disk. Regenerate into a scratch or reference folder, not `assets_dev`.

## Content binding

- Anchors: every MM9 script, RUDE binding and quest refers to DAT object names (`NPCNbr`, `ScriptName`, door and
  lever names). The remade map keeps those names as stable anchors (event faces, decoration names, actor and chest
  records), so the generated Lua and authored overlays rebind by name, not by face index.
- Exits: MM9 exit triggers become event faces or volumes with the existing transitions data; wilderness edges that
  connect in MM9 may use native edge travel with MM9 travel days.
- Population: NPC actors from DAT (cities hold 35–60), chests (0–16 per map) with MM9 treasure levels, then the
  added spawn points and packs per the density target.
- Unsupported MM9 behaviours (7,718 unclassified script commands, continuous rotating brushes, damage brushes,
  shooters) stay explicit audit items, as in the current package checker; each remade map lists what it implements.
- Spawns: MM9's monster rows each have their own picture (`MM9 75 Dragonfly Mite`), with no A/B/C tiers, so the
  map-stats encounter slots and native spawn points cannot resolve them (the runtime looks up "<slot picture> A/B/C").
  Each MM9 body family gets MM-style tier pictures (Dragonfly Mite, Dragonfly, Fire Dragonfly → `MM9 Dragonfly A/B/C`)
  in the world's monster data and descriptor tables, as Hesper does; then packs come from spawn points and encounter
  difficulty like MM6–MM8. Found on the Isle of Ashes pilot (its map-stats row also has difficulty 0 and no appear
  ranges).
- Fleet Foot (done 2026-11-09): MM9's `world.yml fleetFoot: true` makes Fly's slot (Air, spell 21) MM9's Fleet Foot
  (`game/party/WorldSpells.h`). The slot keeps the spell table's id, "Fly" name key (saves, quick spells, battle
  orders), Master requirement, cost and recovery; the name, texts, spellbook picture (`worlds/mm9/icons_x2`
  `sba10a/sba10b` over the engine's) and effect are MM9's: the party buff `FleetFoot` runs the party 125/150/175 % fast
  at Expert/Master/Grandmaster for 15/30/60 minutes a point of Air (MM9's `SPELL.txt` row 21), indoors too. The
  user's adaptation: the speed-up is a quarter larger in the HUD's green state (no hostile within the engagement
  range, `partyHasGreenAlert`). The MM9 book of spell 21 is named Fleet Foot (`mm9_spellbooks.py`); the HUD shows
  MM9's winged boot (`fleetfoot01-08`, `level_generation/ui/mm9_fleet_foot_20261109/`). Leaving MM9 ends the buff.
  Still to check: Jump (cliff skips), Water Walk (sea borders) and Town Portal (needs MM9 town destinations).

## Phases

**Phase 0: inventory (scripted, cheap).** One tool writes a per-map table: extents, height range, terrain texture
families, buildings and interiors with source polygon counts, prop classes, monster classes, NPCs, chests, exits and
their destinations, script bindings, lights, water, weather, and the world connection graph. It also writes the
creature table above in full (per model: rig, clips, events, skins, map usage) and the balance baselines (Emerald
Island, New Sorpigal with its dungeons and Dagger Wound Island against the MM9 starting chapter; quests per map,
chests). Output: `INVENTORY.md` here, plus a tileset and sky proposal per region.

Before Phase 1, three quick checks: the party-scale comparison, an export of the Dragonfly with its clips to check the
MM9 rig in Blender and the creature viewer, and a terrain resample of Isle of Ashes compared against the MM9 terrain.

**Phase 1: pipeline pilot, Isle of Ashes.** A full terrain map (33×41k) with shores, water and real encounters:
terrain resample, BModel rebuild, prop conversion, sky/water/weather, spawn points and packs, loot, exits, generated
Lua rebinding, isolated desktop screenshots, with the Dragonfly family and Skeletoid/Bone Thrasher as the first
creatures. Bootcamp, mostly buildings, would test the wrong things first.

**Phase 2: calibration slice, the starting chapter.** Sturmford, Sturmford City, Beethoven and Anskram Keep, with
Isle of Ashes from Phase 1 and Bootcamp rebuilt as the tutorial. Adds the first city with walk-in shops, doors and
levers, the first BLVs and the Field Thrall. Calibrates density, packs, the balance envelope against Emerald Island
and New Sorpigal, Fleet Foot and travel. The user reviews this slice before production starts.

**Phase 3: production waves by region.** One region per wave (wilderness, city, its dungeons, its monsters and
textures), in story order from the Phase 0 world graph, then Arslegard, Wizard's Lab, Afterworld and the remaining
dungeons. Each wave ends with a playable
isolated run and the user's visual review. Waves can overlap: geometry of the next region while textures and
creatures of the current one finish.

**Phase 4: world-wide passes.** Lighting bakes and the stale-bake check, minimaps, Town Portal/Lloyd destinations,
balance pass over the whole campaign, opt-in MM9 AI behaviours, Android cook, and retiring the `bmodel_world` maps
and their sidecars.

## Pitfalls

- **Script fidelity:** rebuilding geometry breaks every face- or index-based binding. Keep DAT object names as
  anchors from day one, and re-run the existing MM9 gates (transitions, vendors, quests) per remade map.
- **Heightmap limits:** 512-unit grid, no overhangs, 8,160 maximum height. MM9 canyons, cliff paths and caves under
  terrain need BModels or a cave-mouth event into a BLV.
- **Rotating doors:** BLV maps have rotating movers since 2026-10-30
  ([doc](../INDOOR_ROTATING_MOVERS_AND_LADDERS.md)). Walk-in shop doors in city ODMs need pivot BModel mechanisms; today those exist only under the `bmodel_world` scene profile, so classic
  ODM needs the same typed mechanisms enabled explicitly.
- **Interiors in outdoor maps:** weather through roofs, sky light leaking in, city frame time (see walk-in shops).
- **MM9 rig reuse:** MM9 bind poses and joint orientations are 2003 LithTech conventions; if the new mesh cannot be
  made to deform cleanly on them, fall back to our own rig and use the MM9 clips only as reference and timing.
- **Balance:** more monsters means more experience and gold; MM9 items and the MM9 economy (vendor L6 cap) were
  tuned for the sparse original. Calibrate on Phase 2 before scaling up.
- **Over-polishing a converter:** the goal is good maps, not a perfect DAT→BLV compiler. Automate measurement,
  terrain resample, prop conversion and name anchors; author the rest by hand in Blender.
- **Copyright:** converted MM9 meshes, textures and clips are original assets from the user's copy, like MM6–MM8
  content; keep them in `assets_dev`/`assets_source`, not as redistributable "own art".

## Sources and references

- MM9 import tools: `tools/mm9_import_discovery/` (DAT→ODM/BLV transcoders, `convert_abc_model.py`, monster, vendor,
  transition and quest generators, Bootcamp gate).
- MM9 design records: `devdocs/mm9/` (start with `MM9_ODM_BMODEL_WORLD_GOAL.md`,
  `MM9_WORLD_CONTENT_MIGRATION_INVENTORY.md` and `MM9_MODEL_ASSET_STRUCTURE.md`).
- Original data: `mm9/extracted/` (`WORLDS/*.dat`, `.ed` editor files for 8 maps, `MODELS/MODELS/*.abc`,
  `SKINS/SKINS/*.dtx`, `DATA/MAPSTATS.txt`, `MONSTERS.txt`, `ACTOR.txt`, `AISPAWN.txt`), `mm9/io_scene_lithtech`
  (Blender importer), `mm9/DAT-Reader`.
- OpenMM9 project docs and DAT runtime source copied to `reference/openmm9/` (git-ignored): DAT format notes,
  DAT→LTA exporter, actor navigation, flight and combat findings.
- Level generation: [README](../../level_generation/README.md), [outdoor calibration](../../level_generation/OUTDOOR_CALIBRATION.md),
  [pipeline status](../../level_generation/PIPELINE_STATUS.md).
- Engine limits measured for native dungeons: [Hesper dungeon playbook](../../design/kreegan_world/DUNGEON_PLAYBOOK.md), section 2.
