# MM9 rework: Thjorad Mine (`thjoradmine.blv`)

MM9's Thjorad Mine (the dwarves' mine under Thjorgard: the refinery and its broken slag extractor, the miners' halls,
the cave-in over the flooded cavern, the hard rock and Ebora behind it, the troglodyte tunnels and the boarded-up
abandoned mine) converted from its DAT world into a native indoor map (BLV: sectors, portals, rotating and linear
movers, lights, an exit volume) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_thjoradmine_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry (59 rooms, 59 archway cuts found automatically plus 6 by hand), 71 movers,
257 BLV lights, the exit, 371 decorations, 15 chests, 73 placed actors and 20 hidden spawns, every scripted object of
the three quests, MM9's model lighting for props and actors, baked lighting (calibrated to MM9's DAT lightmaps, zones 0.93-1.25).

## Build and review

```sh
python3 level_generation/projects/mm9r_thjoradmine/work/cuts/auto_cuts.py      # archway cuts from the air voxels
python3 level_generation/projects/mm9r_thjoradmine/work/cuts/apply_cuts.py     # into overrides.yml (+ manual.yml)
python3 level_generation/projects/mm9r_thjoradmine/convert.py --plan           # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_thjoradmine/convert.py                  # build, compile, install (5 min)
python3 level_generation/projects/mm9r_thjoradmine/make_scenarios.py
for s in doors_exits chests scripted machinery; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_thjoradmine/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_thjoradmine
python3 level_generation/projects/mm9r_thjoradmine/work/reach/make_probes.py   # + make_chase.py, probe_board_room.yml
python3 level_generation/projects/mm9r_thjoradmine/make_tour.py v02 [--original]   # lighting<n>: the lighting subset
bash level_generation/projects/mm9r_thjoradmine/work/run_tours.sh v02 [--set video.lightmaps=false]
bash level_generation/projects/mm9r_thjoradmine/work/run_tour_original.sh v02     # view_distance=unlimited
python3 level_generation/projects/mm9r_common/dungeon/sheet.py <project>/review/v02 <project>/review/v02_original
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_thjoradmine --samples 128
python3 level_generation/projects/mm9r_thjoradmine/calib_lightmaps.py <direct> <ambient> [bounce]   # recompose + zones
```

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame: x -13 760..31 290, y -19 330..9 260,
  z -3 600..2 290 fit int16). Floors: the refinery and the old halls west 0-500 LT, the entrance -352, the miners'
  tunnels about -550, the abandoned mine -480..-720, the flooded cavern's bed -1 408 under its surface at -1 152.
- DAT: 9 805 source polygons (PhysicsBSP and the world objects), 9 103 merged; 245 faces dropped as having no air in
  front (the backs of the mine's walls and beams against the rock, the flooded cavern's bed under the wading surface,
  the invisible brushes' faces against walls).
- BLV: **11 076 faces**, 18 367 vertices, **60 sectors** (59 rooms), **62 portal faces** (59 archway cuts, 3
  UserPortals), **71 movers**, **257 lights**, faces per sector max 1 346 / median 107. The outline limit was not hit.
- Content: 371 decorations (33 in the busiest room), 15 chests (mine carts, ore bins, two chests), 93 actors: 38
  Troglodytes, 11 Troglodyte Gnolls, 8 Troglodyte Wrens, 10 dwarves (four NPCs with dialogues, six miners), Ebora, 5
  cats, and 20 hidden Troglodytes for MM9's spawn manager. No pads: MM9's touch Triggers are polled boxes.
- Lights: 257 MM9 `Light` objects, all in the BLV (no floor point under more than four); no DirLights, no LIGHTDEFS
  textures, no fog (`EnableFog 0`).

## Rooms: automatic archway cuts

The mine is chambers on long tunnels, and its air is one component: the playbook's cuts by hand would have taken about a
hundred entries. `work/cuts/auto_cuts.py` finds them from the voxel air: per horizontal layer, the 2D distance of each air
voxel to the rock; chambers are the air within 7 voxels (112 LT) of a voxel at least 7 voxels from rock (an opening),
joined in 3D; every mouth of a chamber into a tunnel component of at least 3 000 voxels gets one cut 4 voxels down the
tunnel, across its direction, spanning its width. 59 cuts came out; the 6 that left both sides in one room (loops round
a pillar or a split tunnel) are dropped (`work/cuts/drop.txt`); 6 hand cuts (`work/cuts/manual.yml`) split the east
tunnel network (3 000 faces in one sector before, 1 346 the largest after). The floor check lists 20 730 LT² of floor
under another room's air: 16 LT strips along the cuts (Chasm of the Dead's note: harmless), largest 1 944 LT².

## What each DAT object became

| DAT | Native |
| --- | --- |
| `PhysicsBSP` | the static world; `VisBSP`'s UserPortals `doorportal05`, `Portal0`, `Portal1` are door portals; `Portal2` (behind the locked entrance door: nothing built there) is skipped |
| `Door2` (RotatingDoor, Locked, no key) | a `rotate` mover that only jiggles on a click (`doorlock02.wav`); the exit volume stands in front of it |
| `slidingdoor05`, `deadbolttop05`, `deadboltbottom05`, `switch05`, `handletrigger05` | the refinery's north door: `dat` movers and the rotating handle; a click on the handle or the door draws the bolts and slides the door open (object wiring) |
| `Door0`, `Door1` (Door, MoveDir +y 128) + `Switch2-5` (Switch, StartOpen) | the lift gates east and west of the refinery with doorway portals; either lever of a gate raises or lowers it, both levers swing |
| `BarWall0/1`, `ABDoorBoards0` (RotatingDoor, Locked) + `Spike0-17` (WorldObject) | barricades nailed by six spikes each; a click pulls a spike (it drops out of sight), the sixth opens the barricade |
| `FallingBoard0`, `SteamValve0`, `RotatingDoor0`, `RotatingDoor61-63` | `rotate` movers (the falling board, the steam valve, the slag extractor's hatch, three plain doors) |
| `Stalagtite` (Door) + `DestructableBrush0` | the stalactite falls (`dat`, 160 LT at 300 LT/s) when the brush over it (a scene destructible, 1 hp) is broken by a weapon or a click |
| `db12-db23` (the hard rock), `CaveWall0-4`, `BustOutBrush0-2`, `CaveIn`, `ABMineBoards0-3`, `MCarBlocker1`, `TorchHolder0/1` (DestructableBrush) | scene destructibles (`motion: break`, 2026-11-06: static faces with cog 20000 + DAT index, MM9's HitPoints, CanDamage, TriggerDestroyOnly): weapons break them, the machinery's Lua destroys them (`evt.DestroyDestructible`), and the ones MM9's party could hit keep a click (the rocks and the stalactite's brush: the shared click 38000 + index; the cave wall 102, the cage walls 111-113, TorchHolder0 108); their destroyed events are the old handlers (rocks 90-101, 107, 108, 140) and 210-224 (`Broken<name>`, MM9's DeathTrigger dust and quakes) |
| `FallingWallTorch0/1` (WorldObject) | `slide` movers dropped 1 000 LT out of sight when their torch falls |
| `DirtyWater1` (BlueWater, ShowSurface, water125.spr) | its top as a solid wading face at -1 152 LT, cut to the cavern on a 64 LT grid (18 faces), the review root's `water_mm9` liquid; the bed is not built |
| `BlueWater0` (ClearWater, the steam valve's 10 LT jet), `molten steel0` (Kato, Lava1.spr) | not built: the jet is a moving volume (TM_SteamWater.scr) whose effect is kept (it breaks ABMineBoards1); the crucible's lava volume sits inside the refinery's tank under its own MM9 faces |
| `InvisibleBrush0-5` | invisible collision faces |
| `PerceptionBrush0-14` (PerceptionValue 8) | red hints (Perception.spr, two-sided, opacity 0.35) shown to a party with Perception 8; the hard rock's go off block by block, the hatch's and the barricades' when opened |
| 240 `Prop`, 86 `DestructableProp`, 12 `Barrel`, 11 `BonePile`, 5 `CandleProp`, 15 `TreasureChest` | 3D decorations (props project); chests open containers 0-14 (events 41-55) |
| `Troglodyte`, `TroglodyteGnoll`, `TroglodyteWren` (57) | actors at their DAT positions, facing 90 − ry, MM9 bodies (ABC extents x Scale x 2.56; AB_Troglodyte5 at Scale 1.8) |
| `CommonerDwarfMaleA/B`, `PrisonerDwarfMaleA`, `TownDwarfMaleA` (10) | friendly immobile dwarves on the old import's dwarf rows (322, 323, 325), RUDE dialogues 7, 8, 9, 11 and 428 (NPCNbr) |
| `SuccEbora`, `Cat` x5 | Ebora (row 9301, friendly, immobile) and the cats (row 9294, wandering) in her chamber behind the hard rock |
| `StartPoint0` | start 0, facing north into the mine; the arrival from Thjorgard's `ExitTrigger5` |
| `ExitTrigger0` | MM9 positioned transition volume to Thjorgard (`ThjoradMineExit`), reached down to the entrance floor (`exits: bottom_lt -352`) |
| `Trigger` x29 | `Trigger7`, `TriggerHardRock` and the 18 `TriggerLocation*`: boxes polled four times a second (they fire on any part of the party, once); the `DBEffectsTrigger*`, `TorchTrigger0`, `TriggerSpawn` and `plightofftrigger` relays are folded into the events that send them |
| `AIRail` x580, `Marker` x26, `AmbientSound` x26, `Fire` x24 (dust and steam puffs), `EarthQuake` x8, `Camera`, `PerceptionLight` x10, `OutsideDef0`, `WorldProperties0` | not built (AI helpers, ambient sound later; the dust puffs are `mm9:smoke` effects in the scripts; quakes: camera shakes in the scripts, README "Cinematics") |

## Scripted objects (`worlds/mm9/events/maps/thjoradmine.lua`, written by `convert.py`)

| MM9 script | Objects | Native |
| --- | --- | --- |
| `tm_hardrock.scr` "10 36 5000" on `dw` | `db12-db23` (DeathTrigger dw OneDown; DamageTrigger: its PerceptionBrush off) | a weapon or a click breaks a block (stonecrumble.wav and dust from the destructible; its destroyed event 90-101 turns its hint off); the tenth gives key 36, the quest sound and 5 000 experience and frees Ebora |
| `EboraMines.scr` (`:FreeAtLast`, `OnDamage`) | `Ebora`, `EboraCam` | the tenth block (or her damage hook 196) starts the cinematic `ebora_free` (README "Cinematics") |
| `DestructOn.scr` on `CaveIn`, `tm_hardrock.scr` "1 35 5000" on `CaveInControl` | `Trigger7` (CaveIn DamageOn, Destroy) | the box (event 140) destroys CaveIn, the floor over the flooded cavern: the party falls in; its destroyed event 215 gives key 35, the quest sound, 5 000 experience |
| `SlagExtractor.scr`, `SlagBase.scr` | `slag`, `WorldObject0` (box02), `RotatingDoor0` (hatch) | the hatch opens on a click (PerceptionBrush0 off); a click on the broken part gives item 398 and key 9512 and hides it; a click on the base with item 399 takes it, gives key 37, 5 000 experience and the quest sound and shows the whole part (`slag_whole`, MM9's `SetModelFilenames`); the load handler restores both |
| `NPC7.scr` "Refinery" | Hjarrand the Fixer | present only with key 362 (paid in Thjorgard); after his dialogue (RUDE 7) without key 364 he steps beside the machine and gives key 364 (MM9: paces three times, walks to the Machine marker) |
| `NPC8.scr` | Gudrek the Miner | RUDE 8; with key 9510 he steps to Marker3 by the cave-in and gives key 9511 when the dialogue closes (MM9: walks there with the party) |
| `NPC9.scr`, `Shopkeeper.scr`, `DwarvenMiner.scr` | Ketil Strongpick, Njal Bjarnissen, six miners | RUDE 9, 11, 428 on a click; immobile (MM9: the miners walk between their mine and dump markers) |
| `SpawnMgr.scr` "1 1 Troglodyte TriggerSpawn", `SpawnLoc.scr` x7 | `TriggerLocation0-6C`, `SpawnMarker0-6` | each box once shows one hidden Troglodyte at its marker, hostile (TriggerLocation0: three); none once ten of them died (killed hook 197); SpawnMgr's respawn-on-death is off after TriggerLocation0 in MM9 and is not built |
| `KingKong.scr` (ForceBreak) | `TriggerHardRock`, `TroglodyteGnoll0-2`, `BustOutBrush0-2` | the box breaks the three cage walls (dragonredrattack3.wav) and wakes the dormant gnolls, hostile; a click on a cage wall breaks it too |
| `BoardSpike.scr`, `SpikeDoorA/B.scr`, `SpikeDoorOpen.scr` | `Spike0-17`, `BarWall0/1`, `ABDoorBoards0` | a click pulls a spike (metalwood04.wav); a barricade clicked before its sixth spike jiggles; the sixth opens it (dust) |
| `TM_FallingTorch.scr`, `TM_TorchFlame.scr`, `BlowUpTheBoards.scr` | `FallingWallTorch0`, `TorchHolder0`, `DB_Barrel2-8`, `ABMineBoards2/3` | a click on the torch, or TorchHolder0 broken (a hit, its click), drops it; 3 s later timer 203 destroys DB_Barrel0-8 one after another in MM9's order and waits (1, 0.5, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1 s): each an Exploding destructible prop, whose shared `explode()` (30658-30667) deals ExplodeDamage 100 within 200 LT and a fire column; DustObject6-14 dust, EQHammerImpact.wav, crate_smash.wav; DB_Barrel7/6 destroy ABMineBoards2/3 |
| `TM_MineCarA.scr`, `TM_FirstFallingTorch.scr`, `TM_FirstFallingFlame.scr` | `MineCarA`, `MCarBlocker1`, `ABMineBoards0`, `FallingWallTorch1`, `TorchHolder1`, `DB_Barrel9` | a click on the cart: Gears02.wav, the blocker drops, 9 s later (its ride at 100 LT/s) the cart stands at MCarAMarker0 (a second decoration shown), doorslammetal01.wav, ABMineBoards0 breaks, the second torch falls and 2 s later DB_Barrel9 is destroyed and explodes (timer 204); a click on that torch starts it too; a hit on ABMineBoards0 knocks the torch loose (its damaged event 109) |
| `TM_SteamWater.scr` | `SteamValve0`, `BlueWater0`, `ABMineBoards1` | the valve opens (steam_burst04.wav, smoke), a second later ABMineBoards1 breaks (timer 205) |
| (FallingBoard0 OpenTriggers) | `FallingBoard0` | falls once on a click (dust) |
| `BookLetter.scr` | `Sign0-7` | MM9's letters 572, 571, 574, 573, 573, 426, 486, 487 (`BOOK AND SCROLL TEXT.csv`, bookopen.wav), events 120-127 |
| `PropAnim.scr` "onside" | 17 pickaxes, `Bed22`, `Bed24` | the pose baked into their models (props project) |

Unmatched: `Mine.scr` on `Bin2` (TELP 1.3 made it exit at once: nothing to carry) (`ThjoradQuake.scr`, the
`EarthQuake` objects, `EboraCam1.scr` and `LetterBox` are now camera shakes and a cinematic: "Cinematics"), the miners' walks (`DwarvenMiner.scr`) and their enmity with the
troglodytes (`AddEnemy Troglodyte`: no relation is set, they stand), Hjarrand's and Gudrek's walks (they step to the
end point), the mine cart's ride (the cart is swapped, not moved), the falling torches' fall (they drop out of sight), the
steam valve's water jet, `PerceptionLight0-9` (the hint lights on the machinery: no switchable lights), SpawnMgr's
respawn on death.

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

Profile `tools/lighting/baked_indoors/profiles/mm9_thjoradmine.yml`: 128 samples, 3 bounces, `direct_scale` 1.05,
`bounce_scale` 4, `ambient_scale` 0.5, `max_lighting` 1; one emitter, the flooded cavern's water (`WATE27JPCX`, display
0.6 of a pale teal, strength 0.05: MM9 draws its water surfaces unlit). No bake-only lights (no floor point over four),
no DirLights, no LIGHTDEFS textures. Sector minimum light 20; `map: {model_lighting: true}` (devdocs/INDOOR_MODEL_LIGHTING.md:
ambient 40 40 40 from the DAT's `AmbientLight`, ModelAdd 30) lights the props and actors MM9's way, so the
sector-minimum-31 workaround is not used. Bake about 14 min through `bake_slot.sh`; `stale_bakes.py --assets
output/mm9_rework/assets_dev --check` does not list the map.

**Light colours.** MM9 weights each `Light` by its BrightScale: the mine's 140 lanterns (255/255/128) at 0.75, the old
halls' and north tunnels' 65 orange lamps (230/164/26) at 0.2-0.5. The shared converter writes the colour as authored;
the first bake (direct 1.0, ambient 0.5) measured the north-west halls at 1.57 times MM9's lightmaps and far too orange
(B/R 0.48 against 0.71). `convert.py` `scale_lights` writes colour x BrightScale / 0.75 into the BLV (the lanterns as
authored, so the model lighting keeps `light_scale` 1), and the map was rebuilt and rebaked.

Calibration (AGENT_BRIEF, Brightness: against MM9's own DAT lightmaps; `calib_lightmaps.py` recomposes and runs
`../mm9r_common/hue_vs_lightmaps.py` over `hue_zones.py`; `work/calib_lightmaps_final.txt`). Lightmap luminance ours /
MM9's per zone and hue (B/R, G/R MM9 / ours): entrance 0.93 (0.71/0.72, 0.99/0.94), refinery 0.98 (0.81/0.81,
1.00/0.96), west halls 0.99 (0.72/0.73, 0.94/0.91), north-west 1.20 (0.71/0.62, 0.91/0.84), north tunnels 1.13
(0.78/0.73, 0.93/0.88), cave-in and flooded cavern 1.13 (0.74/0.82, 0.93/0.96), east mines 1.00 (0.74/0.72, 0.99/0.94),
Ebora's chamber 1.25 (0.71/0.70, 0.91/0.91), abandoned mine 1.04 (0.75/0.73, 1.00/0.95). The first bake (MM9's
scales 0.5/0.25 from Dook's Castle) was half MM9's level everywhere (0.47-0.55). The orange-lamp zones stay a little
warm and bright; less ambient makes them warmer, less direct darkens the lantern halls (the 1.1/0.4 trial: entrance
0.84, north-west 1.05 but B/R 0.56). No real MM9 screenshot of this map exists (`overnight/real_mm9/`).

Screen means (information only: the capture is the old import in our outdoor renderer, not MM9):
`work/brightness_lighting01.txt` capture 27.7, native unbaked 46.9, native baked 27.3 (27 views);
`work/brightness_v04.txt` (70 views) capture 27.0, baked 26.0. Views off by more than 10 % (lighting01): a01 start 0.64
(the capture's bright wooden arch), a06 cave-in 1.36, a08 hard rock 1.25, a11 torch and barrels 0.79, r05 0.86, r17 0.76,
r20 0.88, r23 0.89, r40 0.87, r43 1.14, r46 0.88, r52 0.86. Props are not darker than the walls under the bake (model
lighting): the barrels, carts, bins and tables read as in the capture (v03, lighting01); the mine lanterns' bright
skin reads a little dim beside the capture's.

**Model lighting against the old path** (the orchestrator's question after Klusos House, where the mode came out
darker: there MM9's models also got the large fill lights our converter keeps out of the BLV; here no light is over the
four-per-point cap, so the mode sees every light MM9's models saw). The same bake, the scene with and without its
`model_lighting` block (sector minimum light 20, not the 31 workaround), the lighting02 views (`review/lighting02old`
against `review/v04`), `review/model_lighting_compare.jpg`, `work/model_lighting_props.txt`: whole-screen means are the
same (27.2 old path, 27.5 model lighting, capture 27.5: walls dominate). On the props, luminance of a crop against the
capture: the mine cart x1.39 old path / x0.83 model lighting, an ore bin in r05 x0.32 (black) / x1.17, the anvil in r26
x0.69 / x1.00, the barrels in a11 x0.84 / x0.72 (the boarded doorway in a11, mover geometry, x1.25 / x1.23 either
way). The old path blackens props in rooms where the bake carries the light (the frame-ambient subtraction) and
overlights others; model lighting keeps every prop within x0.72-1.17 of the capture, so the map keeps
`model_lighting: true`.

## Checks

1. Every DAT world model has a rule (the build stops otherwise); skipped classes listed above.
2. Sealed air: `leaked_to_border` false, one seeded air component (1 363 361 voxels). 21 seeds whose centre lies in the
   rock are excluded (`seed_exclude`: the relay triggers high in the rock, the TriggerLocation boxes centred under the
   floor, AB_Troglodyte24 and MineCar14 sunk into the floor; `work/leaks.py`). Dropped faces (245): the backs of walls,
   beams and planks against the rock (the largest: thjoradspriteb1 wall backs), the flooded cavern's bed under the wading
   surface, the invisible brushes' faces against walls; no partition among them (`thin_walls: true`).
3. Portals: 62, each joins two rooms (`portals_without_two_rooms` 0; Portal2 behind the locked entrance door skipped).
4. No holes: every view of v01-v04, lighting01 and lighting02old looked at (v01's a02 stood in the refinery's crucible
   and a13 faced a wall: moved in v02). **a07 (the flooded cavern) was a bad tour pose, not a black room**: in v01-v03
   its eye at LT (2053, -928, 2240) lay in the rock (in none of the build's air voxels at any height,
   `work/cuts/air.npz`), just off the cavern, where the old import shows its outside sky; v04 puts it on the pool's north
   rim (2952, -1120, 1928) looking at the water: the cavern walls and the water surface draw, mean 25.7 against the
   capture's 25.7 (`work/a07_compare.jpg`). Floor check: 20 730 LT² of floor under another room's air, the strips along the cuts. Mixed faces: 168 with
   a minority over 20 %, cave walls and tunnel floors along the cuts' planes. One look in Ebora's chamber (r32): the
   hard rock's back shows a lighter square (the blocks' inner faces), as built from the DAT.
5. Review sheets (all looked at): `review/v04_compare.jpg` (70 views, MM9 capture | native baked; v03 the same before
   the a07 fix), `review/model_lighting_compare.jpg` (capture | old path | model lighting),
   `review/lighting01_compare.jpg` (27 views, capture | native unbaked | native baked), `review/v01_compare.jpg` and
   `review/v02_compare.jpg` (the unbaked passes), `../../props/mm9_thjoradmine_claude/review/props_sheet.png`.
6. Walkability (`work/walkability.json`, run before the fence ramps; the audit does not follow invisible ramps): 0 pits;
   133 steps (22 of 33-40, 45 of 41-64, 66 of 65-127: the refinery's tank rim and stairs, frame lips, plank edges, the
   tunnels' rock lips; the party's walks in every scenario and probe cross the ones on their ways), 11 flights (below),
   37 mover notes (movers that drop out of sight and the hard rock: tops in the floor or wall once gone), 2 actor notes
   (Njal's and a spawn troglodyte's bodies overhang an edge within their radius: they stand at MM9's positions).
   8 unreachable regions: two with monsters (next section), six without: three closets behind RotatingDoor61-63
   (0.06 M units² each, a 41 lip), two ledges in the north-west halls (0.07 and 0.01 M units², 82 and 61 up) and a
   platform north of the refinery (0.07 M units², 82 up), MM9's own.
7. Scenarios: `scenario_doors_exits.yml` **pass** (the exit raises its transition; the locked Door2 stays shut on a
   click; the refinery handle opens slidingdoor05 and its bolts; the shut Door0 stops a walk, Switch3 raises it by a real
   click and the party walks through; Switch4 raises Door1; RotatingDoor61-63 and the slag hatch open on real clicks),
   `scenario_chests.yml` **pass** (all 15 by interact), `scenario_scripted.yml` **pass** (8 letters and the dialogues
   11, 9, 8, 428 by real clicks; BarWall1 jiggles shut, opens after its six spikes; ten hard-rock blocks by real clicks
   give key 36 and Ebora vanishes after her taunt and the fire column; Trigger7 drops CaveIn and gives key 35;
   TriggerHardRock breaks the cages and the gnolls turn hostile; TriggerLocation0 shows its three troglodytes, hostile;
   the slag hatch by a click, the broken part and the base by their events (headless picking does not follow the hatch's
   swing) give keys 9512 and 37), `scenario_machinery.yml` **pass** (the falling torch and the barrel chain break
   ABMineBoards2/3; the mine cart breaks MCarBlocker1 and ABMineBoards0 and sets off the second torch; the steam valve
   breaks ABMineBoards1; FallingBoard0 falls; ABDoorBoards0's six spikes open it; the stalactite falls).
8. Starts: StartPoint0 on the entrance floor facing north into the mine (the first view of every tour); the exit
   volume reached down to the floor.
9. Compiler unit tests: not rerun (no engine or compiler change).
10. Lights: no floor point under more than 4; bake current (`stale_bakes.py --check` does not list the map).

## Can the party and the monsters reach each other

- **The flooded cavern under the cave-in** (12 troglodytes and gnolls, 12.3 M units²): reported cut off. **False.** It is
  reached by falling through the cave-in and left by a long tunnel climbing to the north loop, whose steep stretches are
  the audit's 11 flights (rises 41-46 per 40-unit step). The party walks up every flight of the tunnel (`work/reach/probe_flight3-8.log`:
  90-280 units climbed each; flights 0-1 are the refinery's tank rim, walked; flight 2 is the edge of the CaveIn slab, which the audit counts as gone); hostile troglodytes spawned below the steep stretches chase a party standing above, in
  sight (`work/reach/chase_flight5_long`, `chase_flight10_long`) or first seen then moved up (`chase_lure3/4/7`): each
  climbed 40-390 units after the party; the plain-floor control (`chase_control_plain`) closed from 1 200 to 370 and
  held there, as every probe that closed in did.
- **The abandoned mine's west room** (AB_Troglodyte2-4, MineCar5, 2.6 M units²): reported cut off. **Real**, by MM9's
  design: a 72 LT plank fence (static PhysicsBSP planks) closes the tunnel; MM9's player jumps it, the party's jump is
  35 LT. Fixed with invisible ramps over the fence (Deviations): the party now walks in and back out
  (`work/reach/probe_board_room.log`: 882 and 996 units in, 970 out); the troglodytes can come out too.

## Deviations from MM9 and why

- **The flooded cavern is a wading floor.** No swimming yet: DirtyWater1's surface is a solid face the party walks on;
  the bed (-1 408 LT) under it is not built. The party falls through the cave-in onto the water.
- **Invisible ramps over the plank fence** in the abandoned mine's west tunnel (`convert.py` `RAMPS`): MM9's player
  jumps the 72 LT fence; the party's jump is 90 native (35 LT), so the room behind it (three troglodytes, MineCar5) was
  out of reach. The monsters inside can now come out too.
- **Breakables also break on a click**: MM9's party smashes the hard rock, the cage walls, the cave wall, the
  stalactite's brush and the torch holder with weapons, which work too since they became scene destructibles
  (2026-11-06); the click stays as a second route.
- Movers that MM9 destroys drop out of sight; decorations do not move (the mine cart is swapped, the falling torches
  vanish with their holders).
- The dwarves stand where MM9 places them, but the six miners (DwarvenMiner.scr) work: see "Miners" below.
- Water jet, lava volume, perception lights: not built (above). Quakes and the cutscene camera: "Cinematics".

## Cinematics (2026-11-06)

`ebora_free` (`thjoradmine.cinematics.yml`, built by `convert.py` `ebora_scenes`, installed by its `__main__` through
`../mm9r_common/cutscenes.py`; devdocs/mm9_rework/MM9_CUTSCENES.md): EboraMines.scr `:FreeAtLast`, started by
`freeEbora()` (the tenth block of hard rock, or Ebora hurt) with `MM9Cinematic.start("ebora_free")`. 13 s of fixed
waits, one shot: EboraCam at its DAT pose snapped to face Ebora (EboraCam1.scr `FaceObject Ebora 0`), fov 73.7.
Cues: Ebora turns to the camera (`FaceObject EboraCam 180`: 0.47 s), clips `Fidget2` at 0, `Taunt` at 3 with the
subtitle (RollOverText 8 from MMIXSCRIPTTEXT.csv: `script_text.speaker_line(8)`) for 7 s, `AttackRanged` at 8 (the
script's `Rattack1` is not in EBORA.abc), column03.wav at 10. Gameplay steps (run on a skip too): 36001 at 10 s, the
column of fire (EboraFree 3); 36002 at 13 s, she is removed (EboraFree 4); done event 36000. The old timer 202 is gone;
the load handler finishes the steps for a save left at EboraFree 1-2 by the old timer. The overloaded `:FreeAtLast`'s
`ScreenFadeIn 1` only undoes its turn-based guard's fade out, so there is no fade.

Camera shakes (MM9_CUTSCENES.md section 5, `QUAKES` and `quake()` in the Lua, `convert.py` `quakes_lua`): the
DBEffectsTrigger relays are triggered by what breaks (no party reaches their boxes): ABMineBoards0 (the cart) ->
DBQuakeObject0, ABDoorBoards0 -> 1, ABMineBoards2 (DB_Barrel7, with DustObject16's dust) -> 3, BarWall1 -> 4, BarWall0
-> 5; FallingBoard0 -> DBQuakeObject2 (DBEffectsTrigger2 has no sender); the stalactite -> TunnelQuake2 (7 s). Each
is felt within the object's OuterRadius. ThjoradQuake.scr is timer 207: every 300-600 s, 3-8 s at ShakeAmount 2-5 at
the party (first one 300-600 s after the map loads). MM9 set its InnerRadius to 0, so it never fired there.

Test without a conversion: `python3 cinematics_pilot.py` writes the cinematics file and the installed Lua changed as
`convert.py` now writes it into `output/mm9_rework/cinematics_pilot_root`. Then, from
`output/mm9_rework/cinematics_pilot_run`, run `build/game/openyamm --world mm9 --headless-run-scenario <yml>` on
`cinematic_ebora_free_play.yml` (no save while it plays; EboraFree 1 until 10 s, 3 at 10.5 s, 4 and hidden at
13.5 s), `cinematic_ebora_free_skip.yml` (skipped at 1 s: the steps still run; no second start) and `quakes_shake.yml`
(every shake handler runs without error). All pass (2026-11-06), and so do `scenario_scripted.yml` (its Ebora wait is
now 14 s), `scenario_machinery.yml` and `scenario_doors_exits.yml` against the scratch root. Captures:
`output/mm9_rework/cinematics_pilot_run/captures_ebora_free/` (`tour.yml`, `sheet.jpg`): Ebora framed in the tunnel
facing the camera, fidget, taunt with the subtitle, the attack, the column of fire, the party's view back.
An actor health bar still draws over Ebora during the cinematic (engine overlay, not this map).

## Shared converter changes

None. Everything is in this map's `convert.py` and `work/cuts/` (the automatic cuts write overrides.yml). The old map's
`thjoradmine_authored.scene.yml` (an outdoor overlay) and `thjoradmine_authored.lua` (whose handlers replaced ours)
are not in the shared `tables.OLD_SIDECARS`: `convert.py`'s scene hook removes them from the review root. A map with an
old `_authored` overlay (Drangheim, Thjorgard, Boot Camp) needs the same; the shared list could carry both names.

## Open items

- Not checked: a desktop playthrough with real input (the fall through the cave-in and the way back up the long
  tunnel, the barrel chain's look, the mine cart swap), save/load in the middle of the machinery, the arrival in
  Thjorgard (not rebuilt), the quest rows of Hjarrand and Gudrek with Thjorgard's keys, Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:54:18 (convert.py from the current shared converter, end 14:58:39): 1 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 11075 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_machinery.yml` pass, `scenario_scripted.yml` pass.

## Pack growth (2026-11-09)

The user's call: the mine grows 1.4x like the rest of the clans act (`MAP_FACTOR` in
`tools/mm9_import_discovery/mm9_density_targets.py`; it was an early map at 1.0x, then a few hours at 1.8x): 31 copies,
108 counted monsters, all placed, at most 8 within 400 units. MAW adds its own on top
(`rulesets/maw/worlds/mm9/balance.yml` density 2.1: about 227 at MAW difficulty).

## Miners (2026-11-11)

DwarvenMiner.scr as a routine (`convert.py` `miner_routine`): each miner (actors 6-8, 12-14) takes the pick
(`mm9_item_dwarfaxe.glb` on `Socket_RHand1`), walks to the floor in front of his MineMarker/HarvMarker, faces the rock
and plays hammer (7 in 9), rock or rub_beard; 1 in 10 he puts the pick away, walks to his dump marker, plays `dump`
and comes back. Gudrek (42) and Ketil (44) hold MM9's MonkHammer (NPC8/NPC9.scr `AttachProp` on RHand1). Desktop
captures after the axe fix (`output/held_items_check/thjoradmine/`): the pick by its handle in the right hand while
hammering, rubbing the beard and walking, hidden on the dump trip; the hammers in Gudrek's and Ketil's fists by the
handle behind the head. The routines run only near the party (the engine's active-actor range). Scenarios all pass;
playthrough segments 23, 24 and 26 pass.
