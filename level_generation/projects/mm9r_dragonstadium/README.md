# MM9 rework: Dragon Stadium (`dragonstadium.blv`)

MM9's Dragon Stadium (the Dragon King's arena: a rock bowl open to the sky at the end of a tunnel from Lindisfarne,
three ruined pillars of stacked stone, two chests, three skeletons) converted from its DAT world into a native indoor map
(BLV: sectors, portals, lights, one exit volume) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for one MM9 decoration row
([props project](../../props/mm9_dragonstadium_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry (3 rooms from 2 archway cuts), 21 breakable pillar levels as static faces
hidden by a click, the Dragon King as an immobile boss with Dragon.scr's trigger, mutant spawns and reward, 2 chests,
5 decorations, MM9's sun in the bake, the sky opening as the engine's projected sky, baked lighting calibrated to MM9's
DAT lightmaps. The boss behaviour beyond standing and fighting in place is unmatched (below).

## Build and review

```sh
python3 level_generation/props/mm9_dragonstadium_claude/scripts/props_table.py     # props.json (props project README)
python3 level_generation/projects/mm9r_dragonstadium/convert.py --plan            # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_dragonstadium/convert.py                   # build, compile, install (25 s)
python3 level_generation/projects/mm9r_dragonstadium/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_dragonstadium/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_dragonstadium
python3 level_generation/projects/mm9r_dragonstadium/make_tour.py v02 [--original]   # lighting<n>: the lighting subset
bash level_generation/projects/mm9r_dragonstadium/work/run_tours.sh v02 [--set video.lightmaps=false]
bash level_generation/projects/mm9r_dragonstadium/work/run_tour_original.sh v02      # view_distance=unlimited
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v02 <project>/review/v01_original
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_dragonstadium/bake.py
python3 level_generation/projects/mm9r_dragonstadium/calib_lightmaps.py 1.0 0.45     # recompose + zones vs DAT lightmaps
python3 level_generation/projects/mm9r_dragonstadium/work/walls_vs_lightmaps.py      # walls / slopes / floors vs DAT
```

Run `bake.py` again after every `convert.py` that changes the BLV (the game ignores a stale bake); `convert.py` also
rewrites the profile's `shadowless_faces` (the pillar faces' indices).

## Numbers

- Frame: the old map's (`offset` 0; LT x -1 536..3 392, z -3 200..2 464 fits int16).
- DAT: 767 source polygons (PhysicsBSP), 595 merged; 4 dropped as having no air in front (the shell's outer backs: three
  rough_cliff faces and one skymarker). `thin_walls` on; no thin partition in the dropped list.
- BLV: **1 480 faces**, 908 vertices, **4 sectors** (3 rooms), **2 portal faces**, **0 movers**, **3 lights**, faces per
  sector max 1 204 / median 167. 32 sky faces, 411 pillar faces (21 levels). The outline limit is far away.
- Content: 5 decorations (3 skeletons, 2 chests), 2 chests, 1 actor (the Dragon King). No pads (DragonTrigger is a
  polled box), no movers, no NPCs.
- Lights: 3 MM9 `Light`s in the tunnel (67/95/118 and 92/131/163, BrightScale 0.15, radius 375-450 LT), all in the BLV
  (at most 2 per floor point). `DirLight0` (StaticSunLight) is a bake-only sun (Baked lighting), `ObjectLight0` (objects
  only) a model-lighting stand-in. No fog (`EnableFog` 0).

## Rooms

The map is one air volume: the bowl, the tunnel from the start into its south side, and a winding side tunnel climbing
east from the exit. Two archway cuts: `arena_mouth` (axis z through LT (780, 60, -2000), span 700: the tunnel is roofed
there, 190 LT high; at z -1 700 the bowl's air is over it and the cut failed) and `side_tunnel` (axis x at LT 1 100,
span 200). 3 rooms, 0 portals without two rooms, 0 LT² of floor under another room's air; 9 faces mixed over two rooms
without a portal (the bowl's rim faces over the tunnel mouth; drawn whole in the arena).

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world (`VisBSP` has no UserPortals) |
| `skymarker` faces (5 ceiling, 27 wall: MM9's sky box over the bowl) | `sky04` faces drawn as the engine's projected indoor sky (`IndoorSky` set at load by the scene's `face_attribute_overrides`; a planar sky04 mapping streaked on the box's vertical faces). The BLV keeps them ordinary faces |
| `p1/p2/p3 level 1..7` (DestructableBrush, HitPoints 200, Stone; each level's DeathTriggerTarget `destroy`s the level above) | static faces, one `TRIGGER_pillar_<p>_<k>` node per level with cog 300 + 7p + k-1 and click event 70 + 7p + k-1, and scene destructible `id` = its DAT index (200 hp, level 7 TriggerDestroyOnly; 2026-11-06). Weapons break a level, a click deals it a killing blow (`evt.DamageDestructible`); a broken level is invisible and untouchable (the faces keep their baked light; a mover dropping the top levels out of sight would travel 2 950 native, over the 1 024 baked-mover limit). Level 1 of each pillar is a rock mound with 45-degree slopes the party walks up |
| `DragonKing0` (Dragon.scr, ScriptParams 1) | actor 0, row 9212 `MM9 212 Dragon King`, at its DAT place on the floor (native 1 864, 737, -164), facing south, MM9's body (radius 512, height 1 700), `immobile`, hidden and dormant until DragonTrigger (Scripted objects) |
| `WingedMutantCache` (CacheOnly) | not placed (MM9 only preloads it for Dragon.scr's spawns); its row 9160 `MM9 Winged Mutant B` is what the spawns summon |
| `MutantMarker0/1` (Marker, LT y 1 273-1 278: high over the bowl) | the spawn points of Dragon.scr's :SpawnMutants |
| `DragonTrigger` (Trigger, Dims 300 x 96 x 50 across the bowl's mouth) | a box polled four times a second by the map Lua (Chasm of the Dead's route; fires on any part of the party, as MM9's): a pressure plate did not fit the mouth's faceted floor |
| `TreasureChest0/1` (BlackChest) | chests 0 and 1 (events 41, 42), loot from the shared MM9 item sources (treasure level 6, trap 20) |
| `Prop0-2` (BonePile, SkeletonLaying x1.5) | decorations `mm9_skeletonlayingprop_x150` (new row 2452) |
| `InvisibleBrush0` | invisible collision box round the exit tunnel's end (ExitTrigger0 inside it) |
| `ExitTrigger0` | MM9 positioned transition volume to Lindisfarne (`DragonStatiumExit`, MM9's spelling; AskPlayer) |
| `StartPoint0` | start 0, in the tunnel facing north into the bowl; Lindisfarne's ExitTrigger2 arrives there |
| `Light0-2` | BLV point lights (colour x BrightScale 0.15; model lighting `light_scale` 6.67 restores MM9's full colour for models) |
| `DirLight0` (StaticSunLight, 255/255/244, straight down) | bake-only sun (`bake.py`) |
| `ObjectLight0` (white, BrightScale 0.8, radius 3 500 LT, FastLightObjects) | added to the model lighting's ambient (Baked lighting) |
| `TOD_Sky0`, `SkyBox0`, `SkyPointer0`, `WorldProperties0`, `AmbientSound` x5 | not built (sky helpers; ambient sound is a later pass) |

## Scripted objects (`worlds/mm9/events/maps/dragonstadium.lua`, written by `convert.py`)

| MM9 | Objects | Native |
| --- | --- | --- |
| `Dragon.scr` :Main / :HideSetup (ScriptParams 1 = bFlyInOnTrigger) | DragonKing0 | placed with the Invisible bit and `dormant` |
| `Dragon.scr` :OnTrigger (`RemoveTrigger`, visible, solid, Land, Taunt, :NormalSetup) via DragonTrigger's `Trigger` | DragonTrigger, DragonKing0 | event 60 (from the poll, timer 96): map variable `DragonAwake`, `evt.SetMonGroupBit(1, Invisible, false)`, `evt.WakeActor`, a landing thump (`animsounds/dragonredhop.wav`: MM9's `dragon\land.wav` is not in the review root's audio). Once only |
| `Dragon.scr` :SpawnMutants (`Wait 22, SPAWN_INTERVAL` from :NormalSetup, the interval doubling each time: 45 s, then 90, 180, ...; `Spawn` "WingedMutant MoveToFloor 0" at MutantMarker0 and 1) | DragonKing0, MutantMarker0/1 | timer 97, a one-shot re-armed by itself (`evt.StartTimer(97, interval)`): `evt.SummonMonstersById` row 9160 at each marker, group 2; stops when the dragon dies (his script stops with him). After a reload the current interval restarts from the load |
| `Dragon.scr` :OnDeath (killed by a player: `GiveKey 472`, `GiveItem 577`) | DragonKing0 | monster-killed hook 95: map variable `DragonDead`, `MM9.giveKey(472)` (QBit 90472), item 577 "Super Guber Award" (10577) into the active member's packs |
| DestructableBrush death chain (`DeathTriggerTarget` `pN level K+1`, `destroy`) | the 21 pillar levels | scene destructibles; clicks 70-90 deal a killing blow; destroyed events 130-150 set `Pillar<p>_<k>`, puff `mm9:smoke` and `evt.DestroyDestructible` the level above (the chain; the destructible plays `events/stonecrumble.wav` and stone dust); the saved destructible state keeps broken levels hidden |

**Unmatched (Dragon.scr; user decision 2026-10-30: grounded boss script is later work):** the fly-in from above and the
`Land`/`Taunt` clips (he appears in place; the model has the clips for a boss script), any movement (MM9 has no ground
walk for him; he stands at his DAT place: `immobile`), the script's target switching and priorities, the wing attack's
push-back, the breathing smoke (`dragon smoke` ClientFX every 2.5 s), the growl and floor-hit model-key sounds. His
attacks come from his monster row (fire bolt, breath spell). **Pillars:** MM9 breaks them by damage (HitPoints 200,
the party's weapons and the dragon's fire); natively the party's weapons and a click do (monsters' fire damages no
destructible), and their `ExplodeDamage` 100 in a 200 LT radius and the falling debris are not applied.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`bake.py` = the shared `../mm9r_common/dungeon/lighting.py` + MM9's sun. Profile
`tools/lighting/baked_indoors/profiles/mm9_dragonstadium.yml`: 128 samples, 1 bounce (MM9's lightmaps hold no bounce),
`direct_scale` 1.0, `ambient_scale` 0.45, `max_lighting` 1, `dirlights` true, no emitters, `shadowless_faces` (the 411
pillar faces). Sector minimum light 20, the arena room 18 (the open bowl's sky light, below). About 2 minutes of Cycles through `bake_slot.sh`. `stale_bakes.py --assets
output/mm9_rework/assets_dev --check` does not list the map.

- **The sun.** The arena's DAT lightmaps come from `DirLight0`, a StaticSunLight pointing straight down, which only fed
  MM9's lightmap bake (the shared bake reads `DirLight` objects). `bake.py` adds it as one bake-only point light 25 000
  native over the sky box with a radius of 250 000: the runtime window `(1 - d²/r²)²` stays within 4 % over the bowl and
  the bake has no inverse-square falloff, so it lights like a parallel sun. The sky faces are `IndoorSky` in the
  exported bake scene (the scene override), which the bake takes out of casters and emitters, so the sun comes in through
  the open top only: a sunlit patch on the floor under the sky box's ceiling, the rest of the bowl in shade, exactly
  MM9's pattern (DAT lightmaps: floor centre 0.79, outer floor 0.17-0.21, walls 0.17).
- **No pillar shadows (shared tool change, opt-in).** MM9's pillars are world models, which cast no shadow in its
  lightmaps; a baked shadow would also stay on the floor after a pillar breaks. `tools/lighting/bake_indoor.py` takes a
  new profile key `shadowless_faces` (face indices whose bake material is transparent to shadow rays; empty by default,
  so every other profile bakes as before; documented in `devdocs/INDOOR_BAKED_LIGHTING.md`). `convert.py`
  `write_shadowless` rewrites the list after each build. With pillar shadows the floor's centre came out at 0.50 of
  MM9's 0.79.
- **Light colours.** The three tunnel lights are written as colour x BrightScale 0.15 (MM9's weight); the tunnels'
  light is mostly the ambient floor, B/R 1.06 as MM9's.
- **Models.** `model_lighting` with WorldInfo's ambient 45, ModelAdd 30, `light_scale` 6.67, plus `ObjectLight0`'s mean
  over the placed objects (linear `1 - d/r` at MM9's full colour: 0.81 x 255 = 207) in the ambient: 252. MM9's models
  in the arena are lit near full by that light; ours draw at their texture's brightness. Both readings of the light
  (with or without its BrightScale 0.8) saturate.

**Walls, face by face (orchestrator review 2026-10-31).** The review found our rock walls near black in the tour views
against the capture's evenly lit grey-blue rock, while the mixed "arena walls" zone said x1.10. That zone mixed the
bowl's vertical walls with its slopes, the sunlit mound faces and our pillar faces (MM9's pillars are not PhysicsBSP).
`work/walls_vs_lightmaps.py` compares by face group instead: faces within 20 degrees of vertical (|up| < 0.35), slopes
(0.35-0.7) and floors (> 0.7), pillar faces and MM9's sky polygons left out, area-weighted, ours / MM9's DAT lightmaps:

| Zone, faces | MM9 | before (v02, one ambient) | after (v03, arena level 18) | B/R MM9 / ours |
| --- | --- | --- | --- | --- |
| bowl, vertical walls | 0.196 | 0.167 (**0.85**) | 0.195 (**0.99**) | 1.00 / 1.00 |
| bowl, slopes | 0.161 | 0.97 | 1.15 | 1.00 / 1.00 |
| bowl, floors | 0.369 | 1.01 | 1.06 | 1.00 / 1.00 |
| entrance tunnel, walls | 0.176 | 1.04 | 1.04 | 1.04 / 1.04 |
| entrance tunnel, floors | 0.186 | 0.93 | 0.99 | 1.08 / 1.06 |
| side tunnel, walls | 0.161 | 0.99 | 0.99 | 1.00 / 1.01 |
| side tunnel, floors | 0.171 | 0.96 | 0.96 | 1.03 / 1.03 |

MM9 lights the open bowl's walls 11 % above its roofed tunnels' (0.196 against 0.16-0.18): sky light the bowl gets and
the tunnels do not. More bounce did not give it (bounce 2 and 3: bowl walls 0.87, 0.88, the entrance tunnel's walls
past MM9 at 1.07, 1.09). The arena room's sector minimum light level 18 (the map's 20 elsewhere; `convert.py`
`ARENA_LEVEL`, revert with `None`) raises the bake's ambient floor there by x1.18.

**MM9's walls are dark, not ours alone.** The rock texture (`ROUGLU1WPL`, rough_cliff_t) averages luma 72.4; MM9 draws
texture x lightmap x1 (`devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`), so its bowl walls render at 72.4 x 0.196 = 14
and its tunnel walls at 12-13. Ours render at 15.0-16.0 (wall crops of views b03, b06, a01, a04). The capture shows the
same walls at 79-92, brighter than the texture itself: the old import under the outdoor renderer, which the brief rules
out as a target. MM9's player light (`PlayerLightOn` 1) brightens the rock round the party in the real game and is not
reproduced (the darkest view is 13.0, over the 10-12 floor, so no stand-in was added). A capture-matched look would
need wall lightmaps over x1 (fullbright and more): not offered as an alternative.

Mixed zones (`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`; ours / MM9) after the change: arena floor 1.07,
entrance tunnel 1.02, side tunnel 0.96, floor centre under the opening 0.79 (both clipped at x1; its box takes in some
shade on our side), floor west / east of it 0.90 / 1.37 (the sunlit patch's edges fall differently in the boxes).
No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`).

Screen brightness of the 26 tour views (centre crop, mean RGB): **MM9 original capture 74.5, native unbaked 27.6,
baked v02 22.1, baked v03 23.8** (0.32 of the capture; information only). Darkest baked views: the tunnels 13.0-16.3;
the shaded bowl 15-20; the sunlit patch views 25-48.

## Checks (quality gates)

1. Every DAT world model has a rule (21 pillar levels `skip` in overrides and built by `convert.py`, the two sky boxes
   skipped, `InvisibleBrush0` static).
2. Sealed air: `leaked_to_border` 0, one air component, 4 dropped faces (the shell's outer backs).
3. Every portal joins two rooms: 0 without two rooms, none skipped.
4. No holes in the 26 views; floor under another room's air 0 LT²; 9 mixed faces (Rooms).
5. Review sheets: `review/v03_compare.jpg` (MM9 original | native baked, 26 eye-level views: tunnels, exit, the bowl
   from nine sides, each pillar from two sides, the chests, the skeletons, the dragon's place; the current bake),
   `review/lighting_compare_v03.jpg` (original | baked v02 | baked v03, 12 views), `review/v02_compare.jpg` and
   `review/lighting_compare.jpg` (original | unbaked | baked v02, before the review), `review/v01_compare.jpg` (unbaked, the
   first build with the streaking sky), `review/dragon_sheet.jpg` (the Dragon King after the trigger),
   `review/pillars_sheet_a.jpg`/`_b.jpg` (intact | p1 broken whole, p2 from level 4: loaded from a scenario save
   `work/saves/ds_pillars_broken.oysav`). All looked at.
6. Walkability (`work/walkability.json`, `work/floor_map.png`): 12 steps, 4 flights, 2 unreachable regions (0.40 M and
   0.13 M units²), 1 pit (0.59 M). All are on the bowl's sloped outer walls (narrow ledges up the rock, 33-40 and
   65-127 rises) and the pillar mounds' feet and tops; the bowl's floor, both tunnels, the chests, the skeletons, the
   dragon and the start are one connected floor. No walking monster uses them: the Dragon King is immobile and the
   Winged Mutants fly. Not tested in game per region (no content there).
7. Scenarios: `scenario_doors_exits.yml` PASS (a walk from the start raises ExitTrigger0's transition; on p1's mound a
   walk east stops at the column; a real click on the mound sets `Pillar0_1..7`; the same walk then crosses where the
   column stood and a walk north crosses the mound's place on the arena floor; a real click on p3 level 2 from p3's mound
   breaks levels 2-7 and leaves level 1 and p2 intact; 199 console damage leave p2 level 1 standing, one more breaks it and the chain brings down p2's levels 2-7; 2026-11-06). `scenario_chests.yml` PASS (both chests open by interact).
   `scenario_scripted.yml` PASS (the dragon hidden at load; a walk into the trigger box shows and wakes him; no mutants
   at 40 s, two at 46 s; he has not moved; killed: `DragonDead`, QBit 90472, item 10577 in the packs; no more mutants
   in the next 95 s). A probe with the party in his sight (headless) keeps him at his place.
8. Starts: StartPoint0 on the tunnel floor facing north into the bowl (tour view a01); Lindisfarne's arrival row lands
   on it (native 1 802, -5 734, -163).
9. Compiler unit tests: `openyamm_indoor_source_tests` 21/21 pass.
10. Lights: at most 2 per floor point; bake current.

**Finding (shared collision, not changed):** from the south the party gets about 240 units into the foot of p1's column
before inner faces stop it: the column's south walls lean back 15 degrees (normal z 0.14-0.27) and do not hold the
party; its upright west face stops it at once. A probe build with the pillar faces as plain room faces behaved the
same, so it is the indoor collision against leaning walls, not the pillars' trigger nodes.

## Not checked

- The pillars broken by a real desktop click (the scenarios click headless; the desktop sheet loads a save written by
  the scenario's events).
- The fight itself in the desktop game (the dragon's attacks and the mutants' flight from the markers were not watched;
  the headless spawn count and positions are asserted).
- The unreachable ledges in game.
- Sound (no sound runs tonight).

## Package and shared changes

- `tools/lighting/bake_indoor.py`: opt-in profile key `shadowless_faces` (above), with its doc in
  `devdocs/INDOOR_BAKED_LIGHTING.md`. No converter change.
- `assets_dev/worlds/mm9`: decoration row 2452 `mm9_skeletonlayingprop_x150` (sprite 26253, indoor binding) under the
  decorations lock.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:01:56 (convert.py from the current shared converter, end 15:02:07): 3 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 1477 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
