# MM9 rework: Bathhouse (`bathhouse.blv`)

MM9's Bathhouse in Arslegard, Gostaf's bathhouse taken over by the succubus Ebora, converted from its DAT world into a
native indoor map (BLV: sectors, portals, linear and rotating movers, a ladder, lights, an exit volume) on the shared
dungeon converter ([`../mm9r_common/dungeon`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the two new prop
models ([props project](../../props/mm9_bathhouse_claude/README.md)). Status 2026-10-30 (overnight run): geometry,
rooms, sliding and rotating doors, the ladder, lights, the exit, 63 decorations, 4 chests, 20 actors, MM9's scripts
(Ebora and her concubines, the furnace, the drain, the steam vents, the spores, the letters) and baked lighting. Since
2026-11-06 the party swims and dives in MM9's 12 water volumes (below, "Water"). No textures x4: the project's last step.

## Build and review

```sh
python3 level_generation/projects/mm9r_bathhouse/convert.py --plan    # rooms only: work/rooms_<storey>.png (10 s)
python3 level_generation/projects/mm9r_bathhouse/convert.py           # build, compile, install (15 s)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_bathhouse                           # bake (64 samples)
python3 level_generation/projects/mm9r_bathhouse/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_bathhouse/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_bathhouse
python3 level_generation/projects/mm9r_bathhouse/make_tour.py v02 [--original]     # 38 eye-level views
level_generation/projects/mm9r_bathhouse/run_tours.sh v02 --original               # both maps, in parallel
level_generation/projects/mm9r_bathhouse/run_tours.sh v02_unbaked --set video.lightmaps=false
python3 level_generation/projects/mm9r_bathhouse/pages.py v02 v02_original         # review/pages_v02_NN.jpg
python3 level_generation/projects/mm9r_bathhouse/calib.py v02 v02_original         # brightness per view
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_bathhouse
```

Helpers: `analyse.py` (world models' boxes; `--obj <names>` full object properties), `boxpolys.py` (polygons in an LT
box), `floors.py` (floor heights), `section.py` (vertical sections with the water volumes, `work/section_*.png`),
`slice.py` (horizontal voxel slices, `work/slice_*.png`), `diagnose_seeds.py` (seeds in air that reaches the border),
`montage.py`, `pages.py`, `calib.py`, `hue_zones.py`.

## Files

- `overrides.yml`: every DAT world model's rule, 11 archway cuts, 2 window portals, the ladder, seeds and exclusions;
  `convert.py`: the water, the population and the scripted objects (a `dungeon.Hooks` subclass).
- `props.json`: 59 placements (from the props project's `placements.py`).
- `make_scenarios.py`, `scenario_*.yml`, `make_tour.py`, `review_tour_*.yml`, `review/`.
- `source/`, `work/`: `build_report.json`, `doors.json`, `lights.json`, `content.json`, `population.json`,
  `walkability.json`, `dropped_faces.json`, `mixed_faces.json`, `rooms_<storey>.png`, `runtime/`.
- `tools/lighting/baked_indoors/profiles/mm9_bathhouse.yml`: the bake.

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) × 2.56`, no offset (the old map's frame) |
| Storeys | the baths (floors -119 to 0: the great hall's pool -119, the hall -110, the south pools' rooms -95 to 0), the drained room and the corridors east of it (-427 to -320), the chamber under the hall and the switch room (-492), the flooded tunnels (-592) |
| Geometry | 2 527 polygons (PhysicsBSP + static world models) → 2 214 merged → **2 462 native faces** (22 portal faces), 5 124 vertices; the walls round the wading floors cut at their height; 296 faces without air dropped (between brushes, the outsides of the hall's clerestory, the furnace's inner plates behind its grilles, small vent fittings) |
| Air | sealed, no leak; 0.94 M voxels of 16 LT; 9 lights MM9 buried in the rock left out (`skip_lights`) |
| Rooms | **25 rooms + sector 0**, median 51 faces, largest 625 (the great hall) |
| Portals | **22**: 8 MM9 UserPortals (the sliding doors), 12 archway cuts, 2 window portals (the iron grilles between the furnace room and pools A and B); every portal joins two rooms |
| Floor check | 421 LT² of the furnace room's floor under pool A's air: the sill of the window portal |
| Movers | **20**: 10 sliding doors (`Door0`-`Door9`, MM9's MoveDir and MoveDist at 50 LT/s), 4 rotating (the gas valve `GasRelease0` 180°, the drain `Switch0` -80°, the propeller `WaterProp`, the vent flap `RotatingDoor0` 90° with MM9's 10 s auto-close), 4 pistons (`PistonUp/Down0/1`), 2 water movers (the drained room's surface and its stairs) |
| Ladders | **1** (`Ladder0`, the switch room's floor to the switch's shelf) |
| Lights | 87 `Light` → **73 BLV lights** (23 dimmed by BrightScale, below); 9 in the rock left out, 5 over four per floor point bake-only; the 20 `DirLight`s bake-only (`dirlights: true`); at most 4 per floor point |
| Decorations | **63**: 59 from `props.json`, 4 furnace fires |
| Chests | **4**: 3 `Chest5`, the `BlackBox`; MM9's loot records from the shared item sources |
| Actors | **20**: 7 Colloidal Warriors (one the boiled pal), 1 Soldier, 1 Guardian, 3 Jellyspores, 1 Lesser Demon, 3 Concubines, Ebora, and 4 hidden Jellyspores (SpawnMgr.scr) |
| Pads | 4: 3 spore triggers, Ebora's gossip trigger (the 6 dives only with `swim: false`) |
| Water | 12 volumes (scene `water_volumes`, BlueWater2 on the FloodWater movers); 12 non-solid see-through surfaces at the volumes' tops, 2 drained-room surface movers (two-sided), see Water |
| Exit | `ExitTrigger0` (DAT object 199) to Arslegard City (`Bathhouseexit`); arrival `StartPoint0` facing east into the baths |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP` | static world; `VisBSP` only for its UserPortals |
| `Door0`-`Door9` | MM9's sliding doors (`dat`): a click slides them; `Door6/7` locked until the drain (`Locked 1`, `Switch0` sends `unlock`) |
| `GasRelease0` (RotatingDoor, BathFurnace.scr) | the furnace's gas valve: a click turns it 180° at 20°/s and back; below |
| `PistonDown0/Up0/Down1/Up1` | the furnace's pistons: pump while the valve is open |
| `Switch0`, `WaterProp` | the drain switch (authored thrown open: one click throws it) and the propeller it spins |
| `RotatingDoor0` | the flap over the first steam vent: a click swings it 90°, back after 10 s |
| `WorldObject1/5` (iron_window.dtx with invisible collision) | the furnace room's two grilles; window portals |
| `WorldObject0` | Ladder0's rungs (invisible collision) |
| `FurnaceWarning` | the warning plate on the furnace: faces carrying a click event |
| `InvisibleBrush0` | invisible collision at the entrance |
| `BlueWater*`, `WaterthatBoils*` (13 volumes) | water: below |
| `DamageBrush0-3` (SteamVentDB.scr) | polled hazard boxes of the steam vents |
| `Light` (87), `DirLight` (20) | above |
| `Prop`, `DestructableProp`, `TreasureChest` | 3D decorations, chests |
| `Fire1-4` | flame cards in the furnace (Fire2/3 always, Fire1/4 with the valve) |
| `Fire` `BoilingSteam0-9`, `SteamVent0-3` (smoke only) | `mm9:smokestack` puffs near the party (the vents' while they blow; pools A/B's with the valve) |
| monster classes | placed actors on the floor under them, MM9 body sizes (ABC extents x MONSTERS.txt Scale x object Scale x 2.56) |
| `Trigger` `StepTrigger0-2`, `EboraGossip` | pressure pads |
| `ScriptObject` `SpawnMgr`, `SpawnLoc0/1` | 4 hidden Jellyspores (2 per location) |
| `ExitTrigger0`, `StartPoint0`, `Ladder0` | the exit volume, the start, the ladder |
| `Camera` `EboraCam1`, `EarthQuake` `EffectsMgr`, `Marker`s, `AmbientSound`, `OutsideDef`, sky objects | not built (below) |
| `Trigger` `TriggerEffects`, `TriggerFloodTrigger` | outside the map in MM9; `TriggerEffects` is the valve's rumble (a sound), `TriggerFloodTrigger` targets `TriggerFloodImp`, which does not exist |
| `Door` `DragonDoor1` | no world model in the DAT (a leftover): nothing |

## Water

**Swimming (2026-11-06, C8).** The shared water rule (`../mm9r_common/dungeon/water.py` `swimming`, on for every map;
[design](../../../devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md)) writes MM9's 12 volumes as the scene's
`water_volumes` (BlueWater0/1/2/4/6/7/8/9/10/14, WaterthatBoilsA/B; Deathwater2 has no brush): the party falls into
the boiling pools, dives down their shafts (1382 and 1551 deep), swims the flooded tunnels to the chamber under the
hall and on to the switch room's pool, as in MM9; breath and drowning are the engine's. `convert.py` with swimming:
every surface it builds (`WATER`) is non-solid at its volume's top (the wading floors and the wall splits at their
height go), the six dives (`DIVES`, pads and `evt.MoveToMap` handlers) are not built, and `BlueWater2`'s volume takes
the FloodWater movers' door (`mover_door_id`), so its top sinks with the drain (`own_water_surfaces`: the shared rule
draws no static face for it). Checks (`work/build_report.json` `water`): 0 room mismatches (the tunnels joined the
pools' rooms: 20 rooms), 0 bed holes; the audit gets the party out of every volume. Liquids: the 14 surfaces are
see-through (`lqw115o21`, `lqw115o70`), beds under all of them.
- **Deviation**: over pools A and B's basin floors (128-133 under the surface, MM9's 56 LT) the party's feet touch the
  bed with the eye out, so it wades and cannot climb the basin wall (the engine wades a grounded body: design
  "Deviations"); it leaves by a surface jump over the shaft, the pools' deep part. MM9's Current and Viscosity are not
  carried (all zero here but the viscosity); DP2waterdamage.scr is never switched on in MM9 (Scripted objects).
- `scenario_swim.yml`: into pool B's shaft, under, down to its bed (-1515), up to the surface (breath full) and out by a
  surface jump; the drained room swum on its floor before `Switch0` (event 91) and dry after the 30 s drain; a
  Jellyspore spawned in the shaft runs from the dry party and stays in pool B's water (at -83, the surface -15).

The state before swimming (overrides.yml `map: {swim: false}` rebuilds it), kept for reference:

MM9's Bathhouse is built round its swims:
the boiling pools A and B sit over 400 LT shafts into flooded tunnels; the tunnels lead to a dry chamber under the great
hall (with a letter on its floor) and on to the dry switch room, where `Switch0` drains the flooded room east of the
baths and unlocks `Door6/7` to the chests and the Lesser Demon. The conversion (`convert.py` `WATER`, `DIVES`,
`FLOOD_PARTS`; all of it to revert when diving lands):

- **Non-solid surfaces** (the party wades on the bottom): the great hall's pool (6 LT deep) and Ebora's tub (43 LT,
  sloped sides). MM9 draws a volume's `ShowSurface` with `SurfaceAlpha` 0.5 (the drained room 0.7) over Water115.spr,
  whose frame carries its own alpha (DTX PREFER4444; mean 0.42, 52-255): the ripples. The literal product (0.5 x 0.42 =
  0.21; the first build used 0.6 x 0.42 = 0.25) read as the tinted mosaic alone; the faces now take opacity 1, so the
  texture's alpha (mean 0.42, about MM9's 0.5) draws the visible blue, rippled surface (orchestrator review).
- **Wading floors** (solid, opaque, flush with the floor round them, as Beethoven's cavern): the south-west pool (40 LT,
  no steps out), pools A and B (56 LT basins over the shafts), the switch room's pool with the tunnel mouth in its
  corner, and the channels along the chamber. A few LT under the floor would leave a strip of basin wall facing the sealed
  water, which no room draws (seen as black bands in v01).
- **Dives**: a pad on the wading floor over each shaft or tunnel mouth moves the party (`evt.MoveToMap`, same map) to
  where MM9's swim surfaces: pool A or B → the chamber under the hall; the chamber's south channel ends → back to pools
  A and B; the chamber's east tunnel mouth ↔ the switch room. A status line says where it swam.
- **Liquid shader (2026-10-31).** The 14 visible Water115 surfaces (the great hall's pool, Ebora's tub, the wading
  floors, the drained room's two surface movers) draw with the engine's liquid shader (`water115_mm9`, `depth: shallow`,
  [shared helper](../mm9r_common/liquids.py) from the `scene` hook: the faces take the texture `lqw115mm9`, and they leave
  `translucent_faces`): animated, rippling, reflecting water instead of Water115's still frame. It is opaque: the pool's
  mosaic no longer shows through, and the drained room's surface seen from under it is an opaque water ceiling that sinks
  with the drain as before. Collision and dives are unchanged. The 10 invisible Water115 faces are untouched. Sheets:
  `review/liquid/before_after_p1-4.jpg` (before | after).
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the great hall's pool and Ebora's tub (`BlueWater0/6`: SurfaceAlpha 0.5 x
  Water115.spr 0.42 = 0.21, `lqw115o21`, 6 faces) and the drained room's two surface movers (`BlueWater2`: 0.7 x
  Water115flowing, which has no alpha = 0.7, `lqw115o70`) are see-through: the mosaic shows through rippling,
  reflecting blue water. The six wading floors stay opaque (`lqw115mm9`: sealed water under them). Sheets
  `review/liquid/see_through_p1-4.jpg` (MM9-look | opaque | see-through).
- **Volume sides.** MM9's water volumes are `Visible 0` (all 13): MM9 draws only their `ShowSurface` tops. The old
  import's capture draws their box sides too, which is the blue wall seen through the propeller's housing from the
  switch shelf (view `switch_shelf`): `BlueWater2`'s west side at x 3704. The native map shows the housing behind it, as
  MM9 does; the drained room's surface, which MM9 does draw, is the sinking mover.
- **The flooded tunnels** stay built under the wading floors (a sealed room of their own, seeded in `overrides.yml`),
  for the day diving lands; out of reach.
- **The drained room** (`BlueWater2`, DrainWater.scr): MM9's stairs lead down under its surface (-126); the party walks
  its bed. The surface is a translucent, two-sided, non-solid mover (two pieces: the room and the foot of its stairs)
  that sinks to the floor at MM9's 10 LT/s (30 s) when `Switch0` drains the room. MM9's 13 volumes' `Current` and
  `Viscosity`, the underwater tint and fog and the breath limit are not carried.

## Scripted objects (`worlds/mm9/events/maps/bathhouse.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Ebora** (EboraBath.scr), `Concubine1-3` (EboraConcubine.scr) | Ebora stays in her tub, friendly and immobile, and cannot be hurt (CanDamage FALSE: a damage hook sets her damage to 0); each dead concubine (OnDeath → `DeadConcubine`) brings a taunt; the third sends her off in the cinematic `ebora_escape` (below, Cinematics): she vanishes and a party on Gostaf's errand (key 348, NPC339.rude) gets key 349 and 80 000 experience with the quest sound, else key 350 (Gostaf's dialogue reads both). Saved in `EboraGone` |
| `EboraGossip` (OnGossip) | a pad by Door5: up to four taunts |
| **The furnace** (BathFurnace.scr on `GasRelease0`) | a click opens the valve: the big fires (Fire1/4) light, the pistons pump (PistonUp's `repeat`), steam rises over pools A and B, the first opening quakes (EffectsMgr's quake: below, Cinematics), and 2 s later Ebora's fat pal `BigColWinPool2` in pool A is boiled (KillFatc → Fatc.scr `Die`: he vanishes). A second click closes it and puts the fires out |
| `FurnaceWarning` (furnacewarning.scr) | a click shows the warning |
| **The drain** (`Switch0` → `WaterProp` Use, `BlueWater2` Drain, `Door6/7` unlock; DrainWater.scr) | one click throws the switch: the propeller turns for the 30 s of the drain, the room's surface sinks, `Door6/7` open on a click from then on (before: "The door is locked.") |
| **The steam vents** (`SteamVent0-3`, SteamVent.scr; `DamageBrush0-3`, SteamVentDB.scr) | 3 s on, 3 s off; a party in a blowing vent's box takes 20 fire damage a second (MM9's DamageBrush 200 is on MM9's hit points); steam puffs while they blow |
| **The spores** (`StepTrigger0-2` → `SpawnLoc0/1` `spawn` twice; SpawnMgr.scr '1 1 JellySpore', SpawnLoc.scr) | the first trigger stepped on shows its location's two hidden Jellyspores, hostile; the triggers are spent |
| `Prop8`, `Prop7` (BookLetter.scr DoLetter 500, 501) | a click shows MM9's texts: the Invoice and the Scrap of Paper (BOOK AND SCROLL TEXT.csv) |
| `RotatingDoor0` | the vent flap (no script): click |

Unmatched, with the reason:

- EboraBath.scr `OnFoundPlayer` (launch, rollover 14). The gossip, taunts, warning and escape line are MM9's own
  RolloverText rows (MMIXSCRIPTTEXT.csv: 2-5, 9-10, 1, 11; mm9r_common/script_text.py, 2026-11-06). `DeadPal` is never sent
  (Fatc.scr's OnDeath trigger is commented out in MM9).
- Fatc.scr `MoveIt` / `EboraArrive`: sent only from commented-out or unused paths of EboraBath.scr.
- DP2waterdamage.scr (`WaterthatBoilsA`, `Deathwater2`): `DamageOn` is never sent, so the boiling water never hurts in
  MM9 either. DP2steam.scr `FireOn`/`FireOff`: never sent.
- ImpHenchman.scr (two room Jellyspores): wander and `Help`, which nothing sends: ordinary actors.
- BATHHOUSE.scr (Gostaf's quest check): attached to no object in this DAT; the keys come from Ebora's escape.
- EboraConcubine.scr's random Siren skins: actor art (the concubines draw untextured until their models land).

## Cinematics (2026-11-06)

MM9's cutscene and quake as an in-engine cinematic and `evt.CameraShake`
([MM9_CUTSCENES.md](../../../devdocs/mm9_rework/MM9_CUTSCENES.md)). `bath_cinematics.py` builds both (one function,
`scenes(ebora_actor)`, for `convert.py` and the test); `convert.py` appends `cutscenes.lua_block` to the map Lua and
installs `worlds/mm9/maps/bathhouse.cinematics.yml` after a conversion.

- **`ebora_escape`** (EboraBath.scr :DeadConcubine → EscapeTheTub; EboraCam1.scr): the third concubine's death (the
  kill hook, 98) calls `MM9Cinematic.start("ebora_escape")`. One 3.9 s shot from `EboraCam1` (its DAT pose, yaw snapped
  toward Ebora by FaceObject 0, pitch kept, fov 73.7). Timing from EBORA.abc: `launch` 0.9 s, `Castspell` 1.5 s, then
  the script's waits (ClearMe 1 s, TurnCameraOff 1.5 s). Cues (presentation): fade in 1 s (TurnCameraOn's
  ScreenFadeIn 1), the subtitle (RollOverText 11, "Ebora: NO!!  You have ruined my bath!"), Ebora's
  clips `Launch` then `AttackRanged` (the GLB's Castspell). Steps (map events, also on a skip): **36001** at 2.4 s
  (`:DitchTheJoint`: the `mm9:column_of_fire` effect at her, which plays column03 itself; `EboraGone`; key 349 and
  the experience with key 348, else key 350), **36002** at 3.4 s (`:ClearMe`: she is removed); done event **36000**.
  The old `escape()` (status line, eqhammerimpact.wav) is gone.
- **The quake** (EffectsMgr.scr via `TriggerEffects`, ActivationCount 1): the valve's first opening (`Quaked`) runs
  `evt.CameraShake(0.5, 18)` (QuakeWeak 6 / 12; DurationLong 12 s + 6 / DecayRate 1; the quake object sits on the
  party, so no point) and plays `eqhammerpostimpactloop.wav` four times back to back (the poll counts 14 ticks per
  3.49 s loop). Later openings do not quake.

Test without a conversion: `python3 cinematics_pilot.py` writes the cinematics file and the installed Lua with the
same changes into `output/mm9_rework/cinematics_pilot_root`; then from `output/mm9_rework/cinematics_pilot_run`
`build/game/openyamm --world mm9 --headless-run-scenario <abs>/cinematic_ebora_escape_play.yml` (and
`cinematic_ebora_escape_skip.yml`, `quake_valve.yml`): all pass (2026-11-06). Captures:
`output/mm9_rework/cinematics_pilot_run/captures_ebora_escape/` (`sheet.jpg`; `tour.yml`, the party in the tub room).
Engine note: the indoor renderer starts the portal walk from the party's eye sector, not the cinematic camera's
(`IndoorRenderer::buildVisibleSectorMask`): with the party outside the tub room the shot draws a void
(`captures_ebora_escape/probe2/`). In play the party kills the concubines in the tub room, so it frames correctly.

## MM9 visual properties ([list](../../../devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md))

| Property (count in the DAT) | Here |
| --- | --- |
| Translucent surfaces (9) and SurfaceAlpha of the water volumes | the non-solid water surfaces translucent (opacity 1 x Water115's alpha 0.42 for MM9's SurfaceAlpha 0.5, the drained room two-sided); the wading floors opaque (sealed water under them) |
| `glass` (2: `iron_window.dtx`) | the grilles: binary alpha cut-out, drawn with their portals |
| FullyBright (13: the sky box and the hall's skymarker faces) | the skymarker faces draw MM9's Clouds1 sky (`CLOUVKSJD0`) and are the bake's sky emitter |
| `DirLight` (20) | bake-only spot lights |
| Prop `Scale` (54) | a decoration row per scale |
| `.spr` water (Water115, Water115flowing, Water2) | the liquid shader on every visible surface (`water115_mm9`, see Water) |
| `LIGHTDEFS`, `Pan`, glow, fog, `Transparent`/`Chromakey`/`TintColor` props | none in the map |

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_bathhouse.yml`: 64 samples, 3
bounces, `direct_scale` 0.42, `bounce_scale` 6, `ambient_scale` 0.68, `max_lighting` 1 (MM9's lightmaps clip at x1),
`sky_scale` 0.1, `dirlights: true`; one 4096 × 852 page, 3.5 M texels, 1 922 charts, a 5 MB sidecar, about 2 min of
Cycles; passes in `output/mm9_rework/bakes/bathhouse`. From the 73 BLV lights and 25 bake-only lights (the 5 over the
four-per-point cap and the 20 `DirLight`s). The great hall's 5 skymarker faces (`CLOUVKSJD0`) are the sky emitter.
Mover faces are lightmapped. Bake again after any `convert.py` that changes the BLV.

**MM9's dim lights** (`convert.py dim_lights`): MM9 authors 23 of the 73 kept lights below the map's typical BrightScale
(0.7: 0.3, 0.4, 0.5); a BLV light has no brightness, so their colour is scaled by BrightScale / 0.7, as the bake-only
lights' strength already was. `LIGHT_TRIM` takes the yellow Light108 at the east corridor's north end a further x0.45
(that end's brightest texels are teal in MM9's lightmaps, B/R 1.49; ours were yellow, 0.78, 76 degrees off).

**Calibration: against MM9's own DAT lightmaps** (AGENT_BRIEF, 2026-10-30 22:25: the old-import capture is far too bright
and grey against real MM9). `hue_vs_lightmaps.py` with `hue_zones.py`, texel luminance ours / MM9 and chroma per zone
(`lightmap_ratio.py`, `work/hue_final.txt`, `work/lightmap_ratio.txt`):

| Zone | Luminance ours / MM9 | Hue |
| --- | --- | --- |
| great hall | 0.442 / 0.337 = 1.31 | matches (x1.02) |
| north rooms | 0.343 / 0.350 = 0.98 | matches (x0.84) |
| north-east | 0.377 / 0.325 = 1.16 | matches (x0.94) |
| south pools | 0.321 / 0.315 = 1.02 | matches (x1.24) |
| east hall and corridors | 0.438 / 0.382 = 1.15 | matches (x1.10) |
| drain room | 0.277 / 0.306 = 0.91 | too neutral (x0.53): lit by MM9's white Light71, its yellow-green comes from DirLights |
| east corridor | 0.322 / 0.322 = 1.00 | matches (x0.83) |
| chamber and switch room | 0.353 / 0.393 = 0.90 | matches (x0.99) |
| drained room's stair foot | 0.351 / 0.313 = 1.12 | MM9 neutral there |
| east corridor's north end | 0.358 / 0.366 = 0.98 | too neutral (x0.39), no longer yellow |

Suggested light-colour multiplier over the coloured zones x1.10 (not applied). The great hall stays 31 % over: it is lit
by its own many lights (the sky emitter at 0.1 barely moves it).

**The capture, as information only** (`calib.py`, centre crops of the 38 views, `work/calib_v02.txt`): MM9 original
capture 132.0, unbaked 82.0, baked 55.1 (x0.42 of the capture, as Verhoffin's lightmap-matched bake). The earlier
builds of this map were matched to the capture (126.7 to 130.6) and came out grey or blown out: a `max_lighting` 1 /
`ambient_scale` 2.3 bake matched it to -1 % but clipped nearly every texel to white (every zone "too neutral", the great
hall at x0.16 of MM9's chroma), and at `max_lighting` 1.5 the pale plaster at the drained room's stair foot burnt white.

Review sheets: `review/pages_v02_01-04.jpg` (38 eye-level views, MM9's old map left, the native BLV right) and
`review/lighting_v02_p1-6.jpg` (MM9 original | unbaked | baked), all looked at; `review/water/` (the drained room's
surface from below, the stairs' water, the chamber channel), `review/flames/` (the furnace from four sides).

## Checks

- `scenario_doors_exits.yml` passes (32 steps): Door0 shut stops the party, a real click on it slides it aside, the party
  walks through into the south-west pool's room; `ExitTrigger0` raises the transition to Arslegard City (source 199);
  Ladder0 from the switch room's floor to the switch's shelf (top exit); `Door6/7` clicked from the drained room say
  "The door is locked." and stay shut; `Switch0` clicked from its shelf throws it (`Drained` 1); then a click opens both.
- `scenario_chests.yml` passes: the four chests open by interact from in front of their models.
- `scenario_scripted.yml` passes (90 steps): a click on the gas valve lights the furnace, `BigColWinPool2` vanishes 2 s
  later, the valve opens fully in MM9's 9 s; the warning plate answers a click; a second click closes the valve;
  `Switch0` sinks both water movers in 30 s; (without swimming) each of the six dive pads moves the party to its far
  end; `SteamVent1` hits a party in its blast (the fire damage itself can be
  resisted, so the hit is asserted); `StepTrigger2` shows its two spores, hostile, and leaves the other two hidden;
  the gossip pad; Ebora keeps her full hit points under five party attacks; with key 348 the three concubines' deaths
  give key 349 (not 350) and Ebora vanishes; both letters read by a click.
- Walkability (`work/walkability.json`): 103 step findings, all edges of MM9's floors: the great hall's sunken pool
  and its pillar bases (39-49), the tub's and the furnace room's ramps and the ramp between the south-west pool and pool B
  (sides of ramps, 8-16 long), the drained room's terraces (sides of its ramps). 0 flights. One unreachable region of
  0.05 M units², the sealed furnace pocket (no actor there). 18 mover notes: the valve, the flap, the switch, the
  propeller and the sliding doors' leaves. 0 actor notes.
- Monster reach (`work/reach/`, `results.md`): no region with monsters reads cut off. Probes anyway: pool B's colloidal
  walks off its wading floor to the party (real); the concubines never move from the tub, and neither does a Concubine
  spawned on the plain floor of the east hall (control): their row 9302 (and Ebora's 9301) is `Stationary` in the MM9
  monster table (they cast Sparks and Lightning Bolt), so the tub is not the cause.
- Thin walls: `work/dropped_faces.json` holds no partition (the furnace's inner plates, the clerestory's outsides, vent
  fittings); `thin_walls` stays off.
- Load: no Lua errors in the scenario logs; 20 actors (16 textured, 4 without a model: Ebora and the concubines).
- Compiler tests (`build/tools/openyamm_indoor_source_tests`): 21 of 21 cases, 205 assertions pass.
- Sealed air, every world model ruled, every portal joins two rooms, at most 4 lights per floor point; the bake is
  current (`tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map).

## Deviations from MM9 and why

- **Water**: above. Swum as in MM9 since 2026-11-06; the party cannot climb out of the pools' basins over their floors
  (it surface-jumps out over the shafts).
- **The furnace's interior**: its plates face inward around a sealed pocket; MM9 shows the coals through the side
  grilles, and so does the native map, but the inner plates are dropped (no air in front: the pocket is sealed). The
  furnace fires' flame cards sit inside it and are hardly seen (FireScale 1 and 4: 11 and 44 units).
- **Steam**: MM9's Fire objects with white smoke have no native emitter indoors (the decoration smoke flag is outdoor
  only); script-spawned `mm9:smokestack` effects near the party stand in.
- **Ebora's escape** without its cinema (camera, letterbox, column of fire).
- **Urns**: MM9's 21 `DestructableProp` urns break and drop a TreasureBag (TreasureLevel 5); here they are decorations
  (no breakable decorations yet, as Beethoven's barrels).
- **Doors**: MM9's sliding doors close themselves after 10 s and open on touch (`TouchToOpen`, Door3/4); native linear
  doors open and close on a click. Monsters do not open doors (MM9 `AITriggerable`).
- **No ambient sound** (18 `AmbientSound`): a later pass for all maps.
- MM9 touch volumes are pressure pads (they fire when the party stands on them).

## Open items

- Swimming: a headless walk through the flooded tunnels (pool A or B to the chamber and the switch room) and an
  underwater visual check; a lighting rebake (light now reaches the beds through the see-through surfaces).
- Art for the colloidals, the spores, the concubines and Ebora; Ebora's escape effect.
- Textures x4, last. A density and pack pass (PLAN.md: later).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:03:03 (convert.py from the current shared converter, end 15:03:36): 2 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 2460 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.

## Rebuild 2026-11-06: swimming

Reconverted 19:59 into the review root (convert, `lighting.py --layout-only --no-install`, `lightmap_transfer.py
--install`, coverage 0.998; not promoted) with the shared water rule: 12 volumes, 0 room mismatches, 0 bed holes, 20
rooms, 2590 faces; the 8 floor-crack warnings are the drained room's door sills. Scenarios: `scenario_swim.yml`,
`scenario_doors_exits.yml`, `scenario_chests.yml`, `scenario_scripted.yml`, `cinematic_ebora_escape_play/skip.yml`,
`quake_valve.yml` pass, no Lua errors. `make_scenarios.py` reads Ebora's hit points from `convert.ebora_hp()` (the
constant it named was gone since the balance pass).
