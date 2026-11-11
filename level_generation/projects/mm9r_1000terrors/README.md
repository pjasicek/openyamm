# MM9 rework: Thousand Terrors (`1000terrors.blv`)

MM9's Thousand Terrors (Njam the Meddler's dungeon under Arslegard: the sorceress statues, the button-puzzle walls,
the water hall, the gear lift, the chess board, the wind maze and Njam's hall with the win switch) converted from its
DAT world into a native indoor map (BLV: sectors, portals, rotating and linear movers, lights, two exit volumes) on the
shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the
isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows
and the prop models ([props project](../../props/mm9_1000terrors_claude/README.md)). No x4 textures yet.

Status 2026-10-31 (overnight run): geometry of all three storeys, 19 rooms, 121 movers (the button walls, the gear
lift, the plates, the gates and doors), 379 BLV lights, both exits, 402 decorations (117 of them the translucent candle
orbs), 114 monsters, 14 chests, MM9's trigger, shooter, spawner and death-trigger links through one Lua dispatcher, the
three button puzzles, the chess board, Njam's appearances and taunt, the win switch, baked lighting. One shared-converter
change (`tables.transitions_text`, below in Checks and the playbook); no engine change.

Update 2026-10-31 (floor holes, [`SPIRAL_STAIR_PATHING.md`](../../../devdocs/mm9_rework/SPIRAL_STAIR_PATHING.md)
option A1): the shared converter's floor rules (`dungeon/floors.py`, playbook) restore the spiral stair's 8 missing tread
tops and weld the 3-unit crack between the top landing and the exit floor and a 4-5.5-unit crack in the crypts; monks
and Lesser Demons now chase up and down the stair (probes below). `StairGate0` opens (event 369, below). Rebuilt,
rebaked, scenarios rerun; work files in `work/floor_holes/`.

## Build and review

```sh
python3 level_generation/projects/mm9r_1000terrors/convert.py --plan     # rooms only: work/rooms*.png (3 min)
python3 level_generation/projects/mm9r_1000terrors/convert.py            # build, compile, install (10 min)
python3 level_generation/projects/mm9r_1000terrors/convert.py --lua      # only the map Lua, from the last build's state
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_1000terrors
python3 level_generation/projects/mm9r_1000terrors/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_1000terrors/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_1000terrors
python3 level_generation/projects/mm9r_1000terrors/make_tour.py v02 [--original]     # also lighting<n>
level_generation/projects/mm9r_1000terrors/work/run_tour.sh v02 [original] [--set video.lightmaps=false]
level_generation/projects/mm9r_1000terrors/work/zone_ratio.sh     # recompose + ours/MM9 lightmaps per zone
```

`work/run_tour.sh` wraps `./tools/run_game.sh --isolated` (minimized, `SDL_AUDIODRIVER=dummy`, the original with
`--set video.view_distance=unlimited`). `outlines.py` estimates the compiler's outline count (below).

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Three storeys: the crypts and the wind
  maze (floors -1270 .. -750 LT), the entrance level (about 0: the sorceress rooms, the water hall, the tombs, the
  button-puzzle rooms) and the upper halls (900 .. 1200: the foyer, the demon hall, Njam's hall). The spiral stair
  (53 steps, -698 .. -74) joins the crypts to the entrance level; the **gear lift is the only way up** to the upper
  halls (no floor between 100 and 880 LT outside it), as in MM9.
- 16 936 source polygons of the built models (the DAT has 28 009 in all: AI tracks, the visibility hull, ladders,
  perception brushes, sky objects, water volumes and the 117 orb brushes are not geometry) -> 16 319 merged ->
  **17 779 native faces**, 25 959 vertices; 1 384 faces with no air in front dropped (`work/dropped_faces.json`: the
  outsides of the dungeon's shell and faces between brushes; `thin_walls` is on); 8 restored tread tops and 2 welded
  cracks (`work/floor_holes.json`; floor-hole check: 0 holes, 0 cracks left).
- **19 rooms** (+ sector 0), one air component, no leak (24 seeds excluded: touch boxes centred in the void above a
  ceiling and a column of lights sealed in a pillar, `seed_exclude`). The lower crypts are one large room (4 754 faces).
- **20 portal faces** (MM9's UserPortals; `TrapDoorPortal` and `WGPortal2` are not portals: the pit and the water hall
  join their neighbours round them). Floor check 20 342 LT² (door sills and the trap-door pit's rim).
- **121 movers** (doors.yml): 38 `rotate` (door leaves, levers, pivots, the trap doors), 83 `dat` (48 puzzle blocks, 16 plates, gates, the lift, the pulls, the secret bricks, the hidden button).
- **379 BLV lights** of MM9's 533 (+154 over the four-per-point cap light the bake only; 81 DirLights in the bake).
  Light coverage: at most 4 per floor point. BLV lights carry colour x BrightScale.
- **402 decorations** (props project: 265 props incl. 117 water orbs, 115 torches and TerrorLights, 7 braziers, 14 chests,
  the chess note), **14 chests**, **114 actors** (no monster omitted), 0 pads (MM9's Triggers are polled boxes).
- **Outline budget.** The compiler keeps at most 7 000 outlines (the 875-byte seen-lines bitset). Thousand Terrors has
  11 986 (`outlines.py`, which reproduces the compiler's count exactly on Lindisfarne Monastery and the Chasm of the
  Dead): convert.py moves the fewest smallest up-facing faces (1 870 of 3 354, at most 146 units² each: pillar caps,
  trims, stair nosings, coffin lids) to `TRIGGER_detail_*` nodes compiled invisible (estimate 6 295), and the scene
  draws them again at load (`face_attribute_overrides`, 1 909 faces); they keep their collision and are only missing
  from the minimap. The non-solid webs' up-facing faces go the same way (`TRIGGER_detailns_*`, invisible and untouchable).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, the static `WorldObject`s (chess board squares `BoardObj0-63`, chess pieces, pillars, trims), `InvisibleBrush0-5`, `DestructableBrush0-4`, `KnightObject0`, `ElevatorGear1/2` (RotatingBrush) | static world (invisible collision for the invisible brushes); the gears stand still (below) |
| `WeightedLift0-15` (the water hall's 14 stones: 0, 1, 3-11, 13-15) | `dat` movers (2026-11-08): MM9's MoveDir and MoveDist (160 LT down, 410 native), Speed/ClosingSpeed 30 LT/s, auto-close after CloseWaitTime 2 s, bodies `push` (scene hook: a rising stone lifts what is over it); touched by the map Lua's polled boxes (`LIFTS`, below) |
| `SpawnPiece0-3` (DestructableBrush: the four demon statues of the upper hall) | static faces hidden (invisible, untouchable) by the map Lua when SpawnTrigger0-3 "destroy" them (`evt.SetFacetBit` by face index) |
| 117 translucent `WorldObject`s (Alpha 0.4, `water123.spr`, 84 polygons each: the blue orbs over the invisible candles) | **decorations** `mm9_waterorb` (props project, alpha 0.4): as 9 828 translucent BLV faces they broke the desktop renderer (one render batch per translucent face) |
| `WorldObject16`-style webs (Alpha 0.7, `web3.dtx`), `WorldObject0` (Ocean3.spr, the water pit) | non-solid faces; the webs translucent (0.7, scene `translucent_faces`) |
| `skymarker` (the five faces over Njam's hall) | `sky04`, a weak bake emitter |
| `RotatingDoor` pairs `LowerDoor3-18`, `FoyerDoorSouth1/2`, `EDoor3/4`, `RotatingDoor0/1`, `MiddleDoor4/5` | `rotate` movers, MM9's pivot, angle, speed, open-away and auto-close; doorway portals at their UserPortals (EDoor has none: a plain mover pair) |
| `RotatingDoor` `TrapTrigger0-5`, `SecretDoor2`, `TreasureDoor/0`, `Rotating Lever 16-18`, `LowerLever/0`, `TrapDoor1/2` | `rotate` movers; the trap doors over the water pit `bodies: push, carry: true` with their owner the lever room |
| `Door` gates (`CoffinGate1/2`, `ToWindMazeGate`, `StairGate`, `WaterGate0-2`, `ToLowerTombGate`, `IronDoor0`), `SBrick0/1`, `Door0/1`, `Pull1-3`, the 13 `ShooterPlate`s, `FireballPlate/2`, `FoyerShooterPlate`, `HiddenButton1` (Button), `GearElevator` (Lift, 912 LT) | `dat` movers with MM9's MoveDir, MoveDist and speeds; doorway portals where MM9 has a UserPortal (WGPortal2 has the water hall on both sides: not a portal) |
| `PuzzleDoor0-15`, `PuzzleDoorB0-15`, `PuzzleDoorC0-15` (the three 4 x 4 button walls) | `dat` movers (MM9's 16 LT push), hidden until their trap (below) |
| `BlueWater0-6` | the scene's `water_volumes` (the shared water rule, 2026-11-06): the water hall (BlueWater0, 300 deep, fog), the sea monster pool (BlueWater2, 410, fog; its ShowSurface Ocean4 top a drawn non-solid face), the chess pool (BlueWater3, 369, fog) and the entrance pools (BlueWater1/4/5/6, 369); the surfaces (WorldObject0-2) stay non-solid; 0 room mismatches, 0 bed holes; the two Sea Monsters float in BlueWater2 (`scenario_swim_check.yml`) |
| `Prop`, `CandleProp` (TerrorLight1), `Torch`, `Brazier`, `TreasureChest` | 3D decorations (props project: 402 placements); the 117 invisible `Candle.ABC` anchors are not placed (their orbs are) |
| monster classes (`DesertTerror`, `LesserDemon`, `Oculus`, `Orbus`, `ReptilianTerror`, `Eye`, `SeaMonsterMale`, `GreaterDemon`, `AmphibiousTerror`, `FlyingIcky`, `NjamtheMeddler`) | 114 actors at their DAT positions; the 19 flying critters dormant until their trigger; both Njams hidden and friendly until the script shows them |
| `StartPoint0`, `ExitTrigger0` | start 0 by the Arslegard exit; MM9 positioned exit to Arslegard City (442) |
| `ExitTrigger1` (to the Hall of the Gods) | its row (444) stands as MM9 has it, outside every floor: only the win switch's script reaches it (`evt.MoveToMap` to the row's arrival) |
| `Trigger` (55), `Shooter` (29), `Spawner` (14), `ScriptObject` (24), `Marker` | the map Lua (below) |
| `AIRail` (363), `AIBarrier` (5, AI only), `AmbientSound` (28), `Fire` (21 smoke and flame emitters), `Camera` (11), `Lightning` (2), `EarthQuake`, `OutsideDef0`, `SkyPointer0`, `TOD_Sky0`, `SkyBox0`, `DirLight` (81, bake only) | not built (AI helpers, cutscene cameras, effects, sky); the DirLights light the bake |

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_1000terrors.yml`: **direct 2.0,
bounce 0.5, ambient 1.1** with `ambient_colour` (0.75, 0.875, 1.0) (WorldInfo `AmbientLight 30 35 40`), 128 samples,
`dirlights: true` (MM9's 81 DirLights light the upper halls), `max_lighting: 1`, the 154 capped fill lights bake-only,
the five sky faces (`sky04`) a weak emitter. BLV lights carry colour x BrightScale (convert.py `bright_scale`): MM9 weights
its dim warm and green fills (BrightScale 0.15-0.25) down against the blue candle lights (0, 39, 196) x 0.9 and fills
(0, 38, 70) x 0.75. Bounce is low because MM9's lightmaps hold direct light only: at bounce 3 the brown marble trims
greyed the blue rooms (B/R 1.6-2.0 against MM9's 2.5-4.1). Sector minimum light 31 (`map.ambient`); props and actors
use MM9's model lighting (`map.model_lighting: {light_scale: 1.2}`, below). `stale_bakes.py --check` does not list
the map.

## Brightness

**Lightmap-matched, plus a player-light floor** (no real MM9 screenshot of this map exists; MM9 draws walls as texture x
lightmap x1). Lightmap texel luminance, ours / MM9's DAT lightmaps per zone (`hue_zones.py`, `work/zone_ratio_final.txt`):
entrance x1.28, central corridor x1.38, sorceress rooms x1.18 / x1.05, water hall x1.31, east tombs x1.40, south halls
x1.30, crypts x1.16, wind maze x1.13, crypts east x1.35, foyer x1.17, demon hall x1.37, Njam's hall x1.41. Every zone is
over 10 %: the ambient floor (1.1; 0.7 gives x0.74-1.13, `work/zone_ratio_draft.txt`) is the stand-in for MM9's player
light (`PlayerLightOn`), which our engine lacks: at 0.7 eight review views were luma 7-10 (brief, "No pitch-black rooms");
at 1.1 the darkest is 10.7 (the puzzle wall's corridor). Hue: MM9 B/R 0.9-4.1, ours 1.0-3.2 (the blue rooms a little
less blue, the halls as MM9).

Screen means (centre crop, 37 views, `work/brightness_v02.txt`): old-import capture 19.5, **native baked 21.0** (x1.08;
19 views more than 10 % off the capture, from x0.76 (the chess hall) to x1.56 (the win switch's alcove)); the lighting set
(`work/brightness_lighting01.txt`, 13 views): capture 21.2, unbaked 17.3, baked 21.2. This dungeon is dark in MM9 itself
(its DAT lightmaps average 0.16-0.32).

**Props** (`review/ml_new_compare.jpg`: old path | model lighting on nine prop views): the old path (sector minimum 31,
no model lighting) drew the skull head black and the coffins tinted by the room's light; MM9's model lighting
(`light_scale` 1.2 for the BrightScale-weighted BLV lights) draws the skull, the coffins and the statues lit and neutral.
Kept: model lighting.

Sheets (looked at): `review/v02_compare.jpg` (37 views, MM9 original | native baked), `review/lighting01_compare.jpg`
(original | unbaked | baked), `review/v01_compare.jpg` (the unbaked first build), `review/ml_new_compare.jpg` (props, old
path | model lighting), the props' `../../props/mm9_1000terrors_claude/review/props_sheet.png`.

## Scripted objects (`worlds/mm9/events/maps/1000terrors.lua`, written by `convert.py`)

MM9's object messages are carried as data: every `Trigger` (its box, `StartOn`, `TargetName<n>`/`MessageName<n>`), every
mover's `OpenTriggerTarget<n>`/`CloseTriggerTarget<n>`, every `Shooter` (ProjectileName, DamageAmt, ShootInterval),
`Spawner` (DefaultSpawn), the spawn script objects and the monsters' `DeathTriggerTarget` go into Lua tables, and one
dispatcher `send(target, message)` runs them as MM9 does (`on`, `off`, `trigger`, `open`, `close`, `use`, `toggle`,
`lock`, `unlock`, `go`, `stop`, `spawn`, `default`, `destroy`, `settrap`, `reset`). The trigger volumes are boxes polled
four times a second (any part of the party in the box, as MM9's; the Chasm of the Dead's route); MM9's `Wait` is a small
scheduler on the same poll.

| MM9 | Native |
| --- | --- |
| **Sorceress statues** `1000T_SorcStatues.scr` + `1000t_CircleShooter.scr` (SorceressStatue0-5, Sorc*Shooter, TrigSorcStatueOn/Off*, TrapTrigger0-5) | the trigger swings its TrapTrigger pivot (`Use`); its OpenTrigger sets the statues going: each statue's shooter fires five FireBolts (DamageAmt 50) at the party, then triggers its stop trigger (MM9 moves the shooter round five markers; here it fires from the statue); the statue (cog 1390 + k, the skinned `mm9_sorcererstatue`) plays fidget2 once on load and, while casting (`StatueCasting<name>`, Go to Stop), fidget2 and taunt in turn, chained on the poll (2026-11-11) |
| **Lightning statues** `1000t_LightningShooter.scr` (SorceressStatue6/7, TrigSorcStatueOn3/Off3, MiddleDoor4/5) | TrigSorcStatueOn3 unlocks and opens the middle doors; MiddleDoor5's open sets statues 6 and 7 going: Lightning bolts at LightningMarker0/1 every 0.8 s until Off3 |
| **Skeleton head** `1000T_SkeletonHead.scr`, `1000t_SkHeadShooter.scr` (TrigSkelHeadOn0-2) | TrigSkelHeadOn0's `Go` to the SkeletonHead prop (kind `skull`, `SKULLS`: its ScriptParams' two shooters) turns it about (1 s, ignored while turning) and then sends SkelHeadShooter0/1 `Go`: five bolts each, one a second (2026-11-06; before, the dispatcher had no SkeletonHead kind and they never fired); the head's half turn (Rotate 0, 1, 0, 180, 180: clockwise from above, 1 s) is shown with `evt.AimDecoration` (cog 1380, `SkullTurns` counts the turns, map load restores the facing; 2026-11-10); `Stop` sends them `Go` at once (:TurnOff, as MM9); SkelHeadShooter2/3 (DragonBreath2) fire while TrigSkelHeadOn1 has them on, until TrigSkelHeadOn2 |
| **Shooter plates** (Trigger3-17, FoyerShooterTrigger: ShooterPlate1-14, FireballPlate/2, FoyerShooterPlate) | the trigger sinks its plate and turns its shooters on; after the plate's CloseWaitTime (3-4 s) it rises and its CloseTriggers turn the shooters off and the trigger on again |
| **Button puzzles** `ButtonPad.scr` + `ButtonPuzzle.scr` (ButtonTrigger/0/1, PuzzleDoor/B/C0-15, TriggerPuzzleDoor0-2, Pull1-3) | the 4 x 4 walls are hidden (faces invisible and untouchable: MM9 lifts them 128-140 LT into the ceiling, `Main2`) until the party steps into the room's trap trigger (`SetTrap`: every block shut, `stonedoorslam.wav`); a click on a block pushes it and its four neighbours in or out (`ButtonPushed`, MM9's 16 LT push); all sixteen in opens the wall for good (`MoveAway`: hidden again after 0.8 s); the pull shuts every block (`Reset`). B and C start Locked as MM9's |
| **Demon statues** (Trigger18 -> SpawnTrigger0-3, SpawnLoc0-3 `SpawnLoc.scr`, SpawnPiece0-3, Rumble0) | four demons appear at the statues (Lesser, Lesser, Greater, Lesser as SpawnLoc's params), each location once; the statues crumble (hidden faces, `stonecrumble.wav`) |
| **Spawners** (Trigger0-2 -> Spawner5/6/7/10/11; deaths -> Spawner8/13, TP4/TP5; TP0-3 `SpawnGeneric.scr`) and **EndCount** `EndCount.scr`, `EndCountTrigger.scr` | each spawns its DefaultSpawn monster at its place (`evt.SummonMonstersById`, hostile); the end hall's third counted spawn brings a Greater Demon at EndDemonMarker (EndDemon.scr: `mm9:GreaterDemon` effect at the marker; its returned index marked `EndDemon<i>`, whose death in the kill hook opens Door0 and Door1, the gate before the win switch, and sets `EndDemonDead`: EndDemon.scr :OnDeath 25-33; its Spawn clip and HP x 10 are not carried); the "LesserDemon ScriptParams 1" of Spawner8/13 and SpawnLoc0/1/3 (SpawnMgr) are marked by the spawn's returned actor indices and release a Greater Demon at death, as the placed LesserDemon13/14 (LesserDemon.scr p0 1, the kill hook) |
| **Flying critters** `1000T_FlyingCreature_.scr` (TriggerFlyingCritters/0) | the 19 FlyingIcky stand dormant until their trigger's `Go` wakes them (their flight paths are not carried: the AI wanders the stops); MM9's `:OnTraverseDone` removes each at its list's last marker (`RemoveObject`), so each is removed (`MM9.removeActor`) after its flight's time, the path from its place through its stops at `FlyVel 900` LT/s (4.4-5.5 s, `FLY_LEAVE`; 2026-11-08) |
| **Gear lift** (LowerLever, LowerLever0 Open/CloseTriggers -> GearElevator `toggle`) | a click on either lever toggles the lift (912 LT up at 200 LT/s); the gears do not turn |
| **Hidden button** (HiddenButton1, Button: OpenTriggers TreasureDoor, TreasureDoor0 `open`) | a click opens both treasure doors and locks the button |
| **Trap doors** (Rotating Lever 17 OpenTrigger0 TrapDoor1 `open`) | the lever drops the two trap doors over the water pit; Levers 16 and 18 name `Upper Chomper 1/2`, which the DAT does not have: they only swing |
| **Tomb gate** `DoorLock.scr "599"` (ToLowerTombGate) | opens only for a party carrying item 599 |
| **Stair gate** `StairGate0` (Door, `Locked 0`, `PushOpen`, `AITriggerable`, `DoorLock.scr "600; 1"`; no object sends it a message) | a click opens it (event 369), with or without the Stairs Key: with the key (item 600 from TreasureChest5) in the packs, DoorLock's :OnUse takes it (bTakeKey) and the door's own use goes on (the DAT leaves the gate unlocked); it shuts by itself after its CloseWaitTime (10 s), and the script's open flag clears 25.4 s after an opening (open, wait, close), so a later click opens it again; a hostile monster beside it pushes it open (the poll, once a second: on the landing, or south of it once `StairGate` is open). `StairGate` (Door, no `PushOpen`): only LesserDemon0's death opens it; it is locked at every load while shut, so a click says "Locked" (2026-11-08; before, a click opened it) |
| **Chess board** `ChessSquare.scr` (64 Fish squares), `ChessPawn/Knight/Bishop.scr` (ChessPiece0-5) | stepping onto a square a piece attacks (pawn diagonals, knight moves, bishop diagonals, from the pieces' DAT squares) hurts the party (60, `doorslidestone.wav`) while one of its attackers is still on the board; ChessPiece1 (square 51) attacking 58/60 on the last rank queens 2 s later (ChessBase.inc :PawnToQueen): its faces hide and a Terror (row 9164, HitPoints 1069, `mm9:fireblue`) stands on the square. MM9 slides every piece onto the square it attacks: the pieces are static here, so ChessPiece0 (square 35) never reaches the last rank |
| **Njam** `SpawnNjam.scr` (TriggerNjam0-7, NjamSpawnMarker0-7; key 108) | with key 108 each trigger shows Njam (NjamtheMeddler0) at its marker for 20-60 s, hostile while shown (Njam1000.scr AddEnemy Player: `MonsterBits.Hostile` on group 1; njam.lua's hunt mode targets the party; Njam1000.inc :Init CanDamage FALSE is the scene's `mm9_can_receive_damage: false`, so no hit of any kind hurts him and he leaves on the timer, 2026-11-06; the taunt cinematic makes him friendly again); without it the triggers are off (`:Init`) |
| **Taunt** `TauntMan.scr`, `NjamTaunt.scr` (Trigger19; key 108 without 497) | the cinematic `njam_taunt` (below, Cinematics): key 497, Door0 opens, Njam walks to TauntMarker, Door0 shuts (not once the end demon is dead: the gate then stays open), he vanishes (`mm9:GreaterDemon`, `teleport.wav`); his two lines are subtitles from MMIXSCRIPTTEXT.csv (RolloverText 15, 16; `mm9r_common/script_text.py`) |
| **Win switch** `WinMan.scr` (WinMan, Switch03) | nothing from beyond the wall (TELP: party LT z below -3680); each use, and WG_Shot2Cam's `switch` on camera in the cinematic, flips the wheel as `:onSwitch` (bUp FALSE plays `up`, TRUE `down`; bUp starts FALSE on a wheel at rest, so the first use only twitches it in MM9 and shows nothing here, the second turns it down; `WinWheel`, cog 1370, `evt.PlayDecorationClip`, a wheel left down is shown again on load; 2026-11-10); without key 108 it only throws the lightning (Lightning1/2 arc beams for 7 s, thunder); with it the cinematic `njam_freeze_win` (below): the experience (without key 109), the quest sound, up to 10 monsters within 1024 LT removed (DestroyMonsters), Njam's run, panic, lightning and freeze, then key 109 and the change of level to the Hall of the Gods (ExitTrigger1's arrival, `evt.MoveToMap`) |
| **Foyer doors** (WinMan.scr `:Init`, TELP 1.3) | FoyerDoorSouth1/2 stay shut and locked without key 108 |
| **Genie lamp** `GiveRandom.scr` | once: gold 100-1000, experience 100-1000, an item of its list (37 of its 61 have an OpenYAMM item yet), healing 100-1000, or experience for MM9's GiveAttribute |
| **Chess note** `BootGive.scr "598"` (ChessNote0) | item 598, and the scroll is gone (also on later loads) |
| Chests (14 `TreasureChest`) | MM9's loot from the shared item sources; a click opens each |

**Unmatched** (not carried, with reasons): the shooters' flight along their marker lists (they fire from where they
stand); the statues' casting smoke (`Fire` objects CastingSmoke0-7); the flying critters'
paths; the gears' spin; the chess pieces' moves (and so ChessPiece0's queening); `FlyRange.scr` (Oculus7/9 hover range); Njam's
freeze skins (Njam1-7.dtx: no skin swap in the engine; the Purify sounds and his Twitch/Frozen clips stay) and the
invisible `LeverHand` (WG_hand.scr never shows it); ChessCamera.scr's push of the party 160 LT down (the board is solid
here); `AmbientSound` (28); the orbs' damage (MM9 brushes deal 10 per second on touch);
`TriggerSmokeOn/Off` (the genie's smoke).

## Cinematics

MM9's three cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md), built by `cinematics_1000t.py`
(convert.py's map_script appends its Lua block and installs `1000terrors.cinematics.yml` and the cues' MM9 sounds):

| Id | Trigger | Shots, timing | Steps (events) / cues |
| --- | --- | --- | --- |
| `njam_freeze_win` (36.7 s) | the win switch (event 370) with key 108 | party view (fade out), NjamCam's two moves (100, FaceDir 70 with the script's point-as-direction, 130), Shot2Cam (switch), Shot3/4/5 on njam_wingame's CameraSwitch/2 keys (`abc_animation('NJAM', ...)`: 1.69, 2.41, 2.94, 4.65), Shot5's back-up, Shot6 0.6 s, Shot5 3 s, Shot5CamB, Shot7's path at 75; Njam's RunTo at 200 LT/s | 36001 win (experience, DestroyMonsters), 36002 lightball, 36003 Lightning1/2 beams 7 s, 36004 key 109 + Hall of the Gods; done 36000. Cues: fades, 15 sounds, Njam show/run (up the ramp, then the hall)/Running, WinGame, Twitch, Frozen clips, the Earthquake as shakes (1/12, chained to 11.6 s) |
| `njam_taunt` (18.8 s) | Trigger19's Start (event 379), key 108 without 497 | party, TauntCam, TauntCamB on Njam's arrival (WalkTo at 75 LT/s), TauntCam, party | 36051 key 497, 36052 Door0 open, 36053 Door0 close (unless `EndDemonDead`), 36054 vanish effect; done 36050. Cues: fades, Njam place/show/walk/face (FaceObject TauntCamB 10), Conv/Conv1 with RolloverText 15/16 as subtitles, hide, sounds |
| `chess_capture_<k>` (2 s each, 27) | the poll, when a piece attacks the party's square (`MM9Cinematic.chessCapture`), once per square | the square at ChessCam's height, aimed at its first attacker for the slide's 2 s | no steps (the hit stays the poll's); done 36100 + i |

Test without a conversion: `python3 level_generation/projects/mm9r_1000terrors/cinematics_pilot.py` (the scratch root
`output/mm9_rework/cinematics_pilot_root`), then in `output/mm9_rework/cinematics_pilot_run` the headless
`cinematic_{njam_freeze_win,njam_taunt,chess_capture}_{play,skip}.yml` (all PASS 2026-11-06, and
`scenario_scripted.yml` regenerated for the cinematics: PASS on the scratch root). Captures:
`output/mm9_rework/cinematics_pilot_run/captures_njam_dense/` (Shot2-Shot5CamB with the lightning),
`captures_njam_freeze_win/`, `captures_njam_taunt/`, `captures_chess_capture/` (each with `sheet.jpg`).
Njam's RunTo ends where Lightning1/2 strike (their EndPos, 60 LT before NJamMarker: Shot3Cam's close-up and Shot5Cam's
back-up frame him there) and climbs the ramp from his place first (a place under the floor is refused). Key 109 (the
world's completion) is given in the last step, with the change of level, as before.

## Checks

- **Scenarios** (rerun 2026-10-31 on the floor-fix build: all three **PASS**; `scenario_scripted.yml` now begins with
  `StairGate0`: a real click from the landing opens it while `StairGate` stays shut, its event shuts it, a hostile Lesser
  Demon spawned beside it pushes it open; a door click with a monster within 1 500 of it (was 500) is proved by its leaf
  starting to open, since the crypt's Terrors now reach LowerDoor17 while the party clicks it)
- **Scenarios** (all on the final build; real clicks for the doors, levers, the lift lever, a puzzle block, the pull,
  the win switch, the genie lamp and the chess note): `scenario_doors_exits.yml` **PASS** (a walk from StartPoint0 raises
  ExitTrigger0 to Arslegard City; LowerDoor3/4 shut stop a walk, open on a click and are walked through; every clickable
  door group opens on a real click from a pose `make_scenarios.py --probe` found (`work/click_poses.json`); a group with a
  monster standing beside it is proved by its leaf starting to open), `scenario_chests.yml` **PASS** (the 14 chests by
  real clicks), `scenario_scripted.yml` **PASS** (puzzle A: hidden until its trap volume, all blocks shut, a real click
  pushes block 5 and its neighbours in and out again, MM9's lights-out solution opens the wall; puzzle B's trap and Pull2's
  reset; LowerLever sends the gear lift up 912 LT; HiddenButton1 opens both treasure doors; Lever 17 drops the trap doors;
  Trigger5 sinks ShooterPlate1, its shooters fire and it rises after 4 s; Trigger18's four demons spawn and the statues
  crumble; GreaterDemon1's death trigger counts for EndCount; a chess square under attack hurts the party; the win switch
  without key 108 only throws the lightning; with key 108 TauntMan's Trigger19 gives key 497, opens Door0 and shows Njam
  at TauntMarker; the win switch then gives key 109 and the level change; the genie lamp; the chess note; the
  skeleton head's Go starts both eye shooters after its 1 s turn), `scenario_finale.yml` **PASS** (2026-11-06: with
  key 108, a walk north through Door0 stops at the shut gate; the three counted deaths (GreaterDemon1, the TP5
  sender, Oculus9) bring the end demon at EndDemonMarker, its death opens Door0/Door1, the party walks through
  Door0's opening to the switch's side of the wall and a real click on WinMan plays njam_freeze_win: key 109 and
  the arrival in hallofthegods.blv).
  The free-door rule (mm9r_common/dungeon/movers.py `free_door`: PushOpen, unlocked, no sender) gives EDoor,
  SecretDoor2, WaterGate2 and Rotating Lever 16/18 a click (events 119-123); the doors scenario clicks them (Lever
  16/18 and WaterGate2 by their events: no headless pose picks them in the scenario's run).
  Three click targets have no headless hit from any probed pose and run their event: Pull2, HiddenButton1 (a 3 LT button
  at the water's edge) and Rotating Lever 17.
- **ExitTrigger1** lies outside every floor (MM9 triggers it only from WinMan's script): not walked; the win switch's
  `evt.MoveToMap` is asserted through key 109 and the Won variable (the move itself is applied by the frame loop).
- **Walkability** (`work/walkability.json`, `work/audit.log`): 368 steps, 1 flight, 10 unreachable regions, 2 pits, 45 mover
  notes, 28 actor notes. The steps are MM9's: 155 of 41-64 units (dais and coffin plinths, stair landings, door sills),
  56 of 33-40, 157 of 65-127 (the plinths of the statues, coffins and chests, the weighted lifts' edges (static, 160 LT
  sinking platforms in MM9), pool rims): none is a way the party must take; the spiral stair's 53 steps rise 30 units each.
  The flight is a 56-unit rise within one path step at (6644, -13433) (the entrance level beside the lift shaft). The pits: the trap-door water pit (MM9's: Lever 17 drops the party into it; its way
  out rises 1 936 in the audit's terms, the pit's walls) and a 0.17 M units² sump.
  **Unreachable regions** ("monsters cannot walk to the party start"): the upper halls (5 walkers: GreaterDemon1 and its
  guard) are **real and MM9's**: the gear lift is the only way up and monsters do not ride lifts. The crypts and the wind
  maze (11 walkers): the audit treats the shut StairGates as walls, and both start shut in MM9 too (`StairGate` opens
  when LesserDemon0 dies). The old probe (`work/reach/probe_spiral.yml`) stopped at the shut gate, not at the stair. With
  the floor fix (2026-10-31) the stair itself works for the crypts' small walkers: the investigation's probes
  (`work/pathing_investigation/{up,down}_{demon,monk}.yml`, logs `work/floor_holes/probes/`: the monster sees the party,
  the party then stands at the far end) bring a Lesser Demon (radius 65) from the crypt corridor onto the landing in about
  10 s and down to the well's doorway in 8 s, a monk in 10 s and 6 s, each stopping 350-370 from the party as the
  plain-floor controls do (before: stalled at the tread holes for 22-26 s). The Terrors (radius 160-190 in our tables) do
  not fit the well's 246-wide doorway and keep to their level; MM9's own Terror body is radius 64 (`Terror.abc` extents
  25 LT x Scale 1), which would fit: see the investigation's Done section. The south halls (5), the sea-monster pool (2) and four small
  groups were not probed one by one; a spawn on the water hall's floor (`probe_open.yml`) stalled within 100 units
  among the weighted-lift platforms and channels, so the water hall probably cuts the south halls off the same way.
  28 actor notes: flyers (Eye, Orbus, Oculus: radius 144-153) placed within their radius of
  a wall, two walkers overhanging a plinth edge, and Njam (hidden, immobile) under a 1-unit ceiling clearance at his DAT
  place: all MM9's placements.
- **Faces**: `work/mixed_faces.json` (73, 66 with a minority over 20 %): the long walls and floors along room borders; no
  hole seen in the 37 review views.
- **Shared row**: map_transitions row 444 (this map's ExitTrigger1 into the Hall of the Gods) keeps both ends converted
  (`1000terrors.blv` -> `hallofthegods.blv`) after this map's last install (package change above).
- Compiler unit tests not rerun (the compiler is unchanged).

## Deviations from MM9 and why

- **The candle orbs are decorations** (`mm9_waterorb`, alpha 0.4), not BLV faces: 117 translucent 84-polygon brushes
  were 9 828 translucent faces, one render batch each, and the desktop renderer refused the map. No touch damage.
- **The button-puzzle walls appear** (faces shown) instead of sliding down from the ceiling, and vanish instead of
  sliding up when solved: one linear mover cannot also carry MM9's second (vertical) motion; the blocks' own 16 LT push
  is MM9's.
- **Shooters fire from where they stand** (the circle shooters do not travel round their five markers); burst counts,
  intervals, projectiles and damage are MM9's.
- **The chess pieces do not move** onto the attacked square (nor queen): the square hurts the party instead.
- The gears do not turn, the skeleton head does not turn, the cutscenes and cameras are not carried (decorations and
  static brushes do not move).
- **Njam** appears and vanishes at his markers and at TauntMarker without walking there; his taunt lines are not shown.
- **The win switch** moves the party straight to the Hall of the Gods after its rewards (no cutscene).
- **ChessNote0** lies 16 units further from ToLowerTombGate than MM9 drops it: at MM9's place a click meets the gate.
- **StairGate0's monster push**: MM9's monsters push it open; ours cannot open doors, so a poll opens it for a hostile
  monster beside it.
- **The flying critters are removed after their flight's time** (2026-11-08): their marker flight is not carried, so
  awake they wandered the corridors, invulnerable (`mm9_can_receive_damage: false`) and solid, and stopped walks in
  the central corridor (the MM9 playthrough, segment 11). MM9 removes each at its last marker; here each is removed
  that long after its `Go` (and at a load once flown), keeping them dormant until then.
- **The ambient floor** (bake `ambient_scale` 1.1, the WorldInfo AmbientLight's hue) stands in for MM9's player light
  (`PlayerLightOn`): without it eight views were under luma 10 (7.1-9.5). It lifts the lightmaps to x1.0-1.4 of MM9's
  stored texels; `ambient_scale` 0.7 reverts to x0.74-1.13 (`work/zone_ratio_draft.txt`).
- **Bounce light low** (`bounce_scale` 0.5): MM9's lightmaps hold direct light only; our bounce off the brown marble
  trims turned the blue rooms grey (B/R 1.7-2.0 against MM9's 2.5-4.1).

## Open items

- Ambient sounds (28), the torches' and orbs' flicker sounds, the demons' spawn effects, the earthquake.
- Monster reach in the south halls (above); the Terrors' body: MM9's is radius 64, ours 160-190 from the MM8 Behemoth stand-in rows, so they cannot take the spiral stair (a table decision, not applied); MM9's monster models (the stand-ins draw MM6-MM8 sprites).
- ~~A density and pack pass~~: done 2026-11-09 (below, "Pack growth"); x4 textures last.

## Not checked

- Riding the gear lift up with the party on it (the lift's mover opens in the scenario; the ride is not walked) and the
  upper halls reached that way on the desktop.
- Combat: the shooters' bolts hitting the party (ShotsFired counts missiles started), the spawned demons fighting, the
  chess damage beyond the hit count; monster reach in the south halls one region at a time.
- The translucent orbs' look in game from close up (the review views show them small, blue and glowing), flames of the
  sconces and braziers from the side.
- Arrival from Arslegard City by walking its ExitTrigger1; the move to the Hall of the Gods after the win switch on the
  desktop; save/load mid-puzzle; sounds (dummy audio driver); Android.
- Pull2, HiddenButton1 and Rotating Lever 17 by a real click (headless picking finds no target from any probed pose).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:22:21 (convert.py from the current shared converter, end 15:28:05): 15 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 17764 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
Stair probes (`scenario_stair_probes.yml`, `../mm9r_common/stair_probes.py`): 4 walks up the ramps over dropped bottoms, before / after (xy, z native): [208.272, 0.0] / [208.272, 0.0]; [54.272, 0.0] / [54.272, 0.0]; [208.076, 0.0] / [208.076, 0.0]; [54.076, 0.0] / [54.076, 0.0]; 0 walk farther after the rebuild.
Blocker probes: 2 walks into helper brushes resting on the floor stop short of them, 2 identical before and after (their sides still block).
This map was rebuilt last, after the monster-size change (14:37) and the converter fix; any later BLV rebuild (the planned monster-size work here) changes faces again: its lighting stays classic until the end-of-integration lighting pass, and a lightmap transfer, if run then, must run after the last rebuild.

Rebuilt 2026-11-06 20:12 (the shared water rule, Njam's CanDamage, the end demon's spawn-in): 7 water volumes, 0 room
mismatches, 0 bed holes, 4 drawn surfaces (BlueWater2); `scenario_swim_check.yml` (`../mm9r_common/dungeon/swim_check.py`:
the party on each volume's bed and up to its surface; the Sea Monsters stay in BlueWater2) pass; finale, doors/exits,
chests, stair probes pass. The end demon and LesserDemon.scr p0 1's Greater Demons are summoned with `mm9 =
{script_params = "1"}` (EndDemon.scr forces the spawn-in: hidden, Spawn clip, Aware; a scratch check sees it hidden at
0.3 s and shown at 2.8 s). `scenario_scripted.yml` stops at step 81 (the gear lift, LowerLever): `ElevatorGear1/2`
became members of the `GearElevator` group in overrides.yml (20:07, the spinner work), so the lift's OpenTriggers
(`ElevatorGear1 toggle`) toggle their own group without end (a Lua stack overflow); for the spinner session to fix.

## Update 2026-11-08: stair gates and flying critters (MM9 playthrough)

Map Lua only (`convert.py --scratch`: the runtime Lua differs from the installed one by this change alone; installed
into `assets_dev` and the review root). StairGate opens only by LesserDemon0's death (locked at load while shut);
StairGate0's open flag clears when the mover has shut again (`openGate0`, also the monster poll; a later change of the
same day withdrew a Stairs Key requirement: MM9's DoorLock takes the key but the unlocked gate opens without it); the 19 flying critters are removed after their flight's time (`FLY_LEAVE`). Headless check
(`prep_c/tombfix.yml` of the playthrough prep): a click on StairGate says "Locked" and leaves it shut, StairGate0
opens without the key, opens with it and takes it, is shut again 28 s later and opens on the next click,
LesserDemon0's death opens StairGate; the critters are hidden 8 s after the party walks into TriggerFlyingCritters.

## Update 2026-11-08: the water hall's weighted lifts move (MM9 playthrough)

MM9's `WeightedLift0-15` (14 stones in the water hall; DAT: TouchToOpen, PushOpen, AITriggerable, MoveDir (0, -1, 0),
MoveDist 160 LT, Speed and ClosingSpeed 30 LT/s, MoveDelay 1 s, OpenWaitTime and CloseWaitTime 2 s) were built
static. They are now `dat` movers (overrides.yml): a stone sinks 410 under its resting top (-128 to -538, under the
water's surface at -251, BlueWater5/6/1/4), waits 2 s (the mover's auto-close) and rises at 77 a second. The dais'
WeightedLift15 sinks 164 (64 LT).
- **The touch** is the map Lua's 4 Hz poll of a box per stone (`LIFTS`, `touchLift`): the stone's top footprint grown
  by 40 (the party's radius 37 and a little), from 200 under its sunk top up to 10 over its resting top. So a party
  standing on it, or swimming against it, touches it. After MoveDelay (1 s) it opens (sinks), and it takes no new
  touch until it is back up (13.7 s; 7.3 s for the dais). The shared TouchToOpen poll (`lua.touch_doors`) is turned
  off for them in `map_script`: it opens at once and reopens a stone a swimmer floats over, so a stone would never
  rise under a swimmer.
- **Rising lifts a swimmer**: the scene hook sets the stones' mover `bodies: push`. The plain linear rule without
  ReopenOnContact is `hold`, which stopped a rising stone under a body. That is MM9's way out of the pool: swim
  against a stone, float over it while it is down, ride it up.
- Monsters that touch a stone sink it too (AITriggerable, the scene's `ai_open`). The hall's flyers did so in tests
  that did not kill them first.
- **Two monsters MM9 places on the stones** were dropped to the pool's bed by the floor snap, which reads static floors
  only. The scene hook puts them back on the stone's top: Eye2 (actor 84) on WeightedLift6, Orbus8 (actor 100) on
  the dais.
- **The rebuild changed only this**: 14 new doors (ids 124-137), 25 more faces, the face indices that follow them in
  the scene and Lua (PADS, PIECES, barriers, translucent faces, detail overrides), and one treasure marker that moved
  128 because the walk graph no longer counts the stones as floor. The other 123 doors are identical apart from
  their face and vertex ids. The installed `1000terrors.lighting` (16:30 today) was baked for the old geometry, so the
  game ignores it as stale ("baked for other geometry") and the map renders unbaked. It was left in place for the
  end-of-integration lighting pass (README "Baked lighting": re-transfer onto the new BLV). The pre-change files are
  in `work/before_lifts_20261108/` (with the check `check_lifts.yml`).
- **Headless check** (`work/before_lifts_20261108/check_lifts.yml`, hall's monsters killed first):
  - A party standing on WeightedLift1 is at -231 2.6 s after the touch and at -538 at 7.1 s, then back at -128 with
    the stone shut at 14.3 s.
  - A party set into the water beside WeightedLift3 touches it, swims over it while it is down, and is lifted from
    -392 through -315 and -238 onto its top at -128, with the stone shut.
  - The playthrough's northbound crossing (segment 61) still passes, with each running jump following the landing at
    once.

## Update 2026-11-09: the lightning corridor's doors stay open; the tomb gate's click

A player's save had the party shut in the treasure room south of the lightning corridor (room_r05, TreasureChest9),
whose only way out is MiddleDoor4. MiddleDoor4/5 lock themselves as they open and as they close (Open/CloseTrigger
`Lock`); TrigSorcStatueOn3 unlocks and opens them and TrigSorcStatueOff3 unlocks and shuts them. MM9 never closes a
locked door (MM9_DOOR_OPEN_RE.md §3), but our auto-close (CloseWaitTime 5) shut the door 5 s after it opened, and the
lock then refused the click from inside. The shared converter now gives a door that locks itself as it opens no
auto-close (`movers.locks_itself`, DUNGEON_PLAYBOOK "Package change: a door that locks itself as it opens never
auto-closes"): both doors stay open while the party is in the corridor and its two rooms.

ToLowerTombGate's click (event 367) toggled the script's open flag (`useGroup`), which the gate's own auto-close never
cleared: after it shut, the next click did nothing and only a second one opened it. The gate has no Open/CloseTriggers;
its click now triggers the gate itself.

Rebuilt (`convert.py --scratch`): BLV identical; the scene differs by MiddleDoor4/5's `auto_close_seconds`, the Lua by
handler 367; installed into `assets_dev` and the review root. A loaded save made before this resets the map's state
(the scene changed) and starts the party at the start point. Checks (headless): through TrigSorcStatueOn3 both doors
open and lock and are still open 9.5 s later; a party in either treasure room for 12 s finds its door open and walks
out; TrigSorcStatueOff3 shuts both; a second pass through On3 opens them again. With the Maze Key the tomb gate opens
on a click, shuts by itself and opens on the next click. `scenario_chests.yml` passes; `scenario_doors_exits.yml`
(step 82, LowerDoor9 still opening) and `scenario_scripted.yml` (step 16, StairGate0 opens on its event since the
2026-11-08 change) fail at the same steps with the files from before this change: stale since 2026-11-08, not rerun past them.

Not changed: DestructableBrush4, a breakable panel beside MiddleDoor4 between the corridor and that room, has no portal
over it (the converter's "seals rooms [9, 5]" note), so once broken the view through its hole is not drawn.

## Pack growth (2026-11-09)

Now at 2x (the user, 2026-11-09 evening: the finale's 5x piled ten times the monsters into the open halls): 93 copies,
186 monsters, all placed (38 moved to other packs); at most 6 within 400 units. The first run's numbers below were at 5x.

The shared pack growth (`../mm9r_common/dungeon/density.py`) now grows the Tomb: 319 of the 372 copies its targets want
(113 of them moved to other packs), 412 monsters against the target of 465 (`work/density.json`). It placed none
before for two reasons, both fixed here:
- the map Lua names every actor in `KIND` (`"actor"`, for `send`'s dispatch) as well as in `ACTOR`: `KIND` is now a
  `density_lua_name_tables` entry (a table that names actors without scripting them; it takes no copies);
- two loops walk every actor with a variable called `index` (the StairGate0 check and the win switch's DestroyMonsters,
  `cinematics_1000t.py`), and the Lua scan, which does not tell scopes apart, followed that name through every other
  `index` of the script (913 indices): both loops now use `scan`.
The only actors the map's messages name are the 19 fly-past critters (dormant, TRIGGERS' `go`, FLY_LEAVE): they stay
scripted and are never copied, so no copy needs waking or removing with its member. The DEATH table's monsters stay
scripted too. Forced arrivals (`overrides.yml` `density_arrivals`): StartPoint0 (the walk-in from Arslegard City, 2
copies within 2 400) and the trap-door drop into the water pit (1 copy). The 53 unplaced: 36 of packs with only
scripted members, 17 with no free spot. Clusters: at most 11 actors within 400 units (height doubled; p90 10), no copy
in water, none added near the win switch. Installed 2026-11-09 21:28 (review root, then the scene and the Lua copied into `assets_dev`; BLV, lighting, bake and
cinematics unchanged). The 28 treasure markers moved with the guards (`treasure.py` places by the monsters near).
MAW's pack reserve then adds 106 copies, up to x1.25 (`tools/maw/mm9_pack_reserve.py 1000terrors`).

