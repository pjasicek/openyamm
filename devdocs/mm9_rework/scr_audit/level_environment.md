# MM9 behaviour gap audit, part 1 of 4: level and environment (2026-11-06)

The user's request (2026-11-06): go through every MM9 `*.scr` and check that the rework handles it, identifying gaps that
could leave doors unopened or locked, where the engine already has the behaviour and only the data plumbing is missing.
This part covers the 217 level and environment scripts (scratch list `cat_level_environment.json`). It also covers the object
classes and messaging that act without a script: doors, locks, exits, destructibles, triggers, lights, sounds, quakes,
weather, wells, chests, the Trigger/Death/Damage/Open/Close message targets, and script `trigger <handle> <msg>`.

**Method.** I dumped every DAT object of the 45 maps (`assets_editor_dev/worlds/mm9/maps/*.raw_objects.yml`: 32 288
objects) and built the message graph: 4 933 links, from TargetName/MessageName 1-10, Open/CloseTriggerTarget 0-3,
Death/DamageTriggerTarget, TriggerTarget, and the `getobjecthandle`/`trigger` pairs of each object's script. Every
door-like object (1 830) was checked against the installed map Lua (mover ids, click events, other references, MM9
senders). Each item was traced to the converter (`level_generation/projects/mm9r_*`, `mm9r_common`) and to the
**installed** `assets_dev/worlds/mm9/events/maps/<stem>.lua` and `maps/<stem>.scene.yml` (promoted 2026-11-06
12:12). Important chains were run headless against `assets_dev` (the `SDL_AUDIODRIVER=dummy ./build/game/openyamm
--asset-root assets_dev --headless-run-scenario` runs are cited by scenario name). The rebuild converting now into
the review roots was read, not written. "R2" marks converter work that is written but not yet in the installed maps.
The helper scripts and scenarios are in the session scratch folder `scr_audit/` (`dump_objects.py`, `wiring.py`,
`doors.py`, `transitions_check.py`, `sc_*.yml`).

Status legend: **OK** handled (how it was verified is given). **PARTIAL** handled with something missing.
**MISSING_DATA** the engine supports it and only converter or data plumbing is missing. **MISSING_ENGINE** needs
an engine feature. **NOT_NEEDED** unused, editor-only or cosmetic, checked against MM9.

## Summary

Rows group repeated objects (ten axe traps are one row), so the counts are rows, not objects. The 217 scripts make 213
rows: some share a row (BookLetter, coffins, Darkp_*).

| Section | OK | PARTIAL | MISSING_DATA | MISSING_ENGINE | NOT_NEEDED |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scripts, dungeons A (G1: 1000 Terrors ... Dungeon of Secrets) | 39 | 10 | 3 | 0 | 4 |
| Scripts, dungeons B1 (G2a: Hall of the Gods ... Ta'Sar) | 20 | 8 | 0 | 1 | 0 |
| Scripts, dungeons B2 (G2b: Temple of Honk ... Yanmir's Fort) | 25 | 8 | 0 | 0 | 9 |
| Scripts, cities, Lindisfarne Monastery, Wizard's Lab (G3) | 35 | 3 | 1 | 0 | 1 |
| Scripts, regions and Afterworld (G4) | 19 | 9 | 1 | 1 | 0 |
| Scripts used in several groups (shared) | 11 | 3 | 0 | 0 | 2 |
| **Scripts, all** | **149** | **41** | **5** | **2** | **16** |
| Wiring without a script, per map (G1-G4) | 126 | 36 | 9 | 4 | 18 |
| Object classes, all maps (shared) | 12 | 5 | 3 | 1 | 3 |

Many OK script rows become OK only with R2 (cinematics, camera shakes, CanDamage, the 1000 Terrors win move): re-run
the projects' scenarios after the rebuild.

## Cross-cutting findings

1. **Exits and arrivals of the regions are in the old frame (P1, every region).** The 12 regions and Afterworld were
   rebuilt with an x/y offset (`level_generation/projects/mm9r_<map>_blv/work/transform.json`: Sturmford -2519/35,
   Guberland -11399/219, Thronheim -33607/15, Afterworld 9082/14021, Boot Camp 25646/1777, ...). Their rows in
   `assets_dev/worlds/mm9/data_tables/map_transitions.txt` were never moved: `mm9r_common/dungeon/tables.py`
   `transitions_text` keeps "frame unchanged" and subtracts no `project.offset` from CenterX/Y or ArrivalX/Y (only
   Arslegard City's and Connecting Tunnels' own wrappers do). 49 exit volumes in 15 maps and 48 arrivals into 11 maps
   disagree with "original - offset" (scratch `transitions_check.py`). Verified headless on the installed maps:
   - Sturmford's ExitTrigger2 to Anskram Keep does not fire at the keep's gate (15421, 16656); it fires 2 519 units
     west, at the old-frame point (scratch `sc_exit_new.yml` fails, `sc_exit_old.yml` passes).
   - Guberland's gate to Guberland City (the new game's first map) does not fire with the party standing in it
     (6131, -9194, z 1411); the old-frame point (-5268, -8975) fires it after the party falls to z -819
     (`sc_gexit_new.yml`, `sc_gexit_old.yml`).
   - Thronheim's exits lie at x -50913, -56023, -43638: outside the BLV's int16 frame, never reachable.
   Arrivals land 2.5-33.6 k units from their start points. Fix: MISSING_DATA. `transitions_text` must subtract the
   destination's offset from ArrivalX/Y and the source's from CenterX/Y (relay volumes are already native), then
   reconvert or patch the rows of the 13 maps. The boat routes (`transport_routes.txt`, outdoor_blv.py
   `rewrite_transport`) are right (47 of 47 at their start points).
2. **The rebuild now running offsets Arslegard City and Connecting Tunnels twice (P1, regression).** Their wrappers
   (`mm9r_arslegardcity/convert.py:274`, `mm9r_connectingtunnels/convert.py:179`) read "the original" rows from
   `assets_dev/worlds/mm9/data_tables/map_transitions.txt`, which since the promotion (P1) already holds the offset
   rows. The review root's table (`output/mm9_rework/assets_dev/...`, 16:43 today) has Arslegard's exits at CenterY
   25254 instead of 5254, arrivals into Arslegard from 1000 Terrors, the Bath House and the Hall of the Gods at y
   13458 instead of -6542, and Connecting Tunnels' exits and arrivals 17 000 too far west. Fix: read
   `mm9r_common/original_tables/map_transitions.txt` (tables.ORIGINAL_TABLES) in both wrappers before those rows are
   promoted.
3. **Weapon breakables that break only on a click (P2, 9 maps).** The user's report ("I shoot the chains and nothing
   happens") is this class in other maps. Sturmford's chains themselves work in the installed map:
   `destructible 316 damage 5` plus a Fire Bolt at DestructableBrush0 opens the drawbridge (mechanism 11), headless
   (scratch `sc_drawbridge.yml`). A real bow arrow from the courtyard breaks chain 315 too (G4 `sc_g4_chain_arrow.yml`). Why the user saw nothing: the chains visible in front of the gate are Drawbridgechain, undamageable in MM9 as here (CanDamage 0, broken by the script after the inner pair); the breakable DestructableBrush0/1 run behind the gate wall over the courtyard; and a shot with no actor under the crosshair goes to the nearest hostile (P2 #2). Maps that built their
   DestructableBrushes as click `sink`/`slide` movers (dungeon/destructibles.py gives a mover no entry) never take
   weapon damage: Thjorad Mine (db12-db23 for key 36, CaveWall0-4, BustOutBrush0-2, the stalactite, torches, cart),
   Connecting Tunnels (rock fall), Dragon Stadium (21 pillar levels), Invent-a-Storca (DestructableBrush0-3), Ruined
   Temple (DestructableBrush0-5), Ta'Sar ("door crack"), Verhoffin (the bolt DestructableBrush12), Yanmir's Fort (six
   supports) and Training Hall (skylights). Frosgard City's floes are script-only in MM9 (BreakIce), so movers are right there. Fix: MISSING_DATA: static cog
   faces plus scene `destructibles` with the existing handlers as `destroyed_event` (and `damaged_event` where MM9
   reacts to OnDamage), keeping the click as an extra route. This is FINAL_REBUILD_WORK C8's "click breakables".
   Engine side (INDOOR_DESTRUCTIBLES.md "Not yet"): missiles do not damage destructible **props** and area spells
   reach no destructible, so Frosgard City's powder barrel (DestructableProp0, which MM9 breaks with any hit) breaks
   by melee or click only: MISSING_ENGINE.
4. **Converter work not yet installed.** C11 cinematics and camera shakes, B3 CanDamage (Yanmir takes damage today),
   B8 damage triggers, the 1000 Terrors win move (installed `1000terrors.lua:481` still names `hallofthegods.odm`,
   verified headless) and M19 actors are in the converters and arrive with the running rebuild (R2). Re-run the
   projects' scenarios afterwards.

## Prioritised gaps

### P1: gameplay-blocking (doors, locks, exits, quest progress)

| # | Gap | Maps | Fix | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Exit volumes and arrivals of the regions are in the old ODM frame: exits do not fire at their gates, arrivals land 2.5-33.6 k units off, and Thronheim's exits are outside the map | Afterworld, Boot Camp, Drangheim, Frosgard, Guberland (the start map), Isle of Ashes, Lindisfarne, Mountain Pass, Sturmford, Thjorgard, Thronheim, Yorwick; plus every map with an exit into them | MISSING_DATA: `mm9r_common/dungeon/tables.py` `transitions_text` must subtract the source's offset from CenterX/Y and the destination's from ArrivalX/Y; then rewrite those rows | `transitions_check.py` (49 volumes, 48 arrivals); `sc_exit_new/old.yml`, `sc_gexit_new/old.yml` |
| 2 | The running rebuild offsets Arslegard City's and Connecting Tunnels' exits and arrivals a second time | Arslegard City, Connecting Tunnels, 1000 Terrors, Bath House, Hall of the Gods, Thronheim, Yorwick (their arrivals) | MISSING_DATA: both wrappers must read `mm9r_common/original_tables/map_transitions.txt`, not `assets_dev/...` (`mm9r_arslegardcity/convert.py:274`, `mm9r_connectingtunnels/convert.py:179`); check before promoting R2 | the review root's table: Arslegard CenterY 25254 instead of 5254 |
| 3 | Pledge.inc's reward (key 277) is never given, so the Green Man's last row (279) never shows: the Druid promotion is blocked | Frosgard City (and the Frosgard region's NPC221) | MISSING_DATA: the pledge NPCs' dialogue-exit handlers in `mm9r_frosgardcity/citylua.py` (with key 265, without 277, at most one of 269-276 missing): key 277, 5 000 xp | G3 |
| 4 | Secretdoor0 has no click event: the room under the loft, Ladder2 and TreasureChest0 are sealed | Thronheim City | MISSING_DATA: overrides.yml `Secretdoor0: {..., doorway: true}`, or the shared rule in P3 #13 | G3 headless walk (`g3_secret*.yml`) |
| 5 | The win switch moves the party to the deleted `hallofthegods.odm` (key 109 set, no move) | 1000 Terrors | fixed in the converter (`hall_of_gods_arrival`), installed with R2; verify afterwards | G1 `sc_g1_win.yml` |
| 6 | Mary's sheep cannot be brought to Mary (key 466, side quest) | Yorwick | MISSING_DATA: the Ewe's click (53000 + object, E3; placed by M19 at R2) plus `evt.MoveActorTo` to Mary and the 466 award on arrival; a true follower is MISSING_ENGINE | G4 |

### P2: visible behaviour (and optional progression)

| # | Gap | Maps | Fix |
| --- | --- | --- | --- |
| 1 | Weapon breakables break only on a click (built as `sink`/`slide` movers, so no scene destructible): Thjorad Mine's hard rock (key 36), cave walls, cages, stalactite, torches, cart; Connecting Tunnels' rock fall; Dragon Stadium's 21 pillar levels; Invent-a-Storca's DestructableBrush0-3; Ruined Temple's DestructableBrush0-5; Ta'Sar's door crack; Verhoffin's bolt; Yanmir's six supports; Training Hall's skylights | 9 dungeons | MISSING_DATA: static cog faces plus scene `destructibles` (DAT HitPoints, CanDamage), the existing handlers as `destroyed_event`/`damaged_event`, the click kept as an extra route (FINAL_REBUILD_WORK C8 "click breakables") |
| 2 | A party ranged attack with no actor under the crosshair goes to the nearest visible hostile (`GameplayActionController.cpp:596` `chooseFallbackRangedTarget`), not to the destructible the crosshair is on. This is the likeliest cause of "I shoot the chains and nothing happens" (the visible outer chain, Drawbridgechain, is also undamageable in MM9; the breakable pair is over the courtyard) | every map with destructibles | MISSING_ENGINE: prefer the crosshair's world hit when it is a standing destructible face |
| 3 | Missiles do not damage destructible props, and area spells damage no destructible (INDOOR_DESTRUCTIBLES.md "Not yet"): Frosgard City's powder barrel breaks by melee or click only; Thjorgard's racing boats are won by clicks | Frosgard City, Thjorgard, every DestructableProp | MISSING_ENGINE |
| 4 | The torch chains never destroy the exploding barrels DB_Barrel0-9: hidden by SetSprite, so no explosion; 0/1 untouched | Thjorad Mine | MISSING_DATA: `evt.DestroyDestructible` in MM9's order (timers 203/204) |
| 5 | The skeleton-head trap never fires (no SkeletonHead kind in the dispatcher) | 1000 Terrors | MISSING_DATA: convert.py `kinds`: SkeletonHead `go` -> shooterOn on its two shooters after 1 s |
| 6 | Celldoor18 is a static open leaf; lever17 does nothing | Drangheim Prison | MISSING_DATA: an `authored_open` build for `rotate` movers (dungeon/movers.py) |
| 7 | Whack-a-honky (key 7113) and the stones game (7110) do nothing | Guberland | MISSING_DATA: port Thjorgard's regionlua code (M1) |
| 8 | The Six Fires never light (script-named Fires are not placed) | Afterworld | MISSING_DATA: place them hidden with SetSprite keys and show them by stage keys |
| 9 | Town Portal keys 95011-95016 are given, but no destination table reads them | six cities | MISSING_DATA: a Chedian table in `town_portal_switch.txt` (each city's TownPortal start in the BLV frame) |
| 10 | No swimming on 13 wet maps (wading faces) | 1000 Terrors, Bath House, Beethoven, Chasm, Dark Passageway, Dook's, Invent-a-Storca, Thjorad Mine, Training Hall, Yanmir, Dungeon of Secrets, Frosgard City, Sturmford City | MISSING_DATA (C8, known); Dark Passageway fixed 2026-11-06 (4 volumes, the tube swum, ShaftExit at its open bottom; `mm9r_darkpassageway/scenario_swim.yml`) |
| 11 | Converter work waiting for R2: C11 cinematics and camera shakes, B3 CanDamage (Yanmir takes damage today: `mm9r_yanmirsfort/scenario_scripted.yml:66`), B8 damage triggers, M19 actors, Verhoffin's dust | many | none: verify with each project's scenarios after R2 |

### P3: cosmetic or minor

| # | Gap | Maps | Fix |
| --- | --- | --- | --- |
| 1 | Five letters (BookLetter.scr: items 488 x4, 489) have no click | Anskram Keep | MISSING_DATA: `evt.SimpleMessage` handlers from BOOK AND SCROLL TEXT.csv, as the other maps |
| 2 | The Portcullislever is static (a click on the portcullis raises it; DoorChain4 moves on its own); the lowered drawbridge can be raised again | Sturmford | MISSING_DATA: the lever as a mover driving Portcullis + DoorChain4; the barred door opens only |
| 3 | PerceptionLights not switched (61 + 10 + 4) | Dark Passageway, Thjorad Mine, Verhoffin | **fixed 2026-11-06 (night)**: `evt.SetLight` switches BLV point lights only on vertex-lit faces (a bake keeps them), so they are scene pulsing lights shown by Perception (shared, dungeon/lights.py `perception_lights`, objects.py event 904), Off/On from the maps' handlers (INDOOR_PULSING_LIGHTS.md "Switched lights") |
| 4 | RotatingBrush spinners (gears, saws, wheels) | Training Hall, 1000 Terrors, Dungeon of Secrets, Ruined Temple, Verhoffin | **fixed 2026-11-06 (night)**: scene `mover.spin` and `evt.SpinMover` (INDOOR_ROTATING_MOVERS_AND_LADDERS.md "Continuous spinners"); movers.py `spin_block`, riding the AttachTo parent; the maps' On/Off/Reverse |
| 5 | WeatherMan/Fog switching by triggers (the scenes keep the StartOn and night states) | Frosgard and the fog maps | **fixed 2026-11-06 (night)**: `evt.SetFog` / `evt.ClearFog` (INDOOR_FOG.md "Fog from Lua"); the shared weather triggers (objects.py `weather_triggers`): Frosgard's pass. No other WeatherMan is switched by anything in the DAT |
| 6 | Wells, cauldrons, cook pots, clovers give no bonus | 23 maps' objects (cities and regions) | **fixed 2026-11-06 (night)**: RE in [MM9_BONUS_PROPS_RE.md](../MM9_BONUS_PROPS_RE.md); shared click events (content.py `BONUS_CLASSES`, objects.py `bonus_call`), world Lua `MM9.useWell/useCauldron/useCookpot/useClover` |
| 7 | DungeonJukebox's random creepy sounds | Anskram Keep | MISSING_DATA (a timer and `evt.PlaySoundName`) |
| 8 | Fire smoke on triggers, statue casting and skull turns | 1000 Terrors | MISSING_DATA for the smoke (Verhoffin's DUST_ON_HIT route); clips MISSING_ENGINE |
| 9 | Lich Lab: the engine lever's `Fix` is replaced by key 296 (works); Glow1 not switched; engine clips | Lich Lab | Glow1 **fixed 2026-11-06 (night)** (on while the pod is shut, handlers 200/251); clips MISSING_ENGINE |
| 10 | The genie's RUDE does not open by itself; WO_CounterBalance does not fall on damage; dust under the cave-in | Ruined Temple | MISSING_DATA (auto-open dialogue: MISSING_ENGINE) |
| 11 | Kluso's guard alarm relay; Ta'Sar's Switch1 self-lock; Training Hall skylights (glass route); the Arena crowd sounds never switched on (`AmbientSound103..122`) | Kluso's House, Ta'Sar, Training Hall, The Arena | MISSING_DATA |
| 12 | Sturmford City's 11 temple windows give no key 5002 (Beathag's charge); Tryggva/Ercc barks; Wizard's Lab Closet1Door1 hint; Frosgard City's cannon test shots; LoseMan's later-death scene | Sturmford City, Wizard's Lab, Frosgard City, Arslegard City | MISSING_DATA; the barks **fixed 2026-11-06 (night)** (sturmfordcity citylua: Trigger1/2 once each, Tryygva01-04, ercc01/02 with key 113) |
| 13 | Unlocked MM9 doors built as movers without a click (not doorways): Thjorgard City BembgateL/R, Arslegard CounterDoor (also Thronheim's Secretdoor0, P1 #4) | cities | MISSING_DATA: a shared rule in dungeon/movers.py: a DAT door that is not Locked, with no sender and no map event, gets the click event |
| 14 | Walks and set pieces: Atli and the bandits (Guberland), Mountain Pass's Imply0 | Guberland, Mountain Pass | MISSING_DATA (`evt.MoveActorTo`) |
| 15 | Moving or animated decorations, skin swaps, scripted flights, leaps, thrown props, AIBarrier switching, the museum chest lids, mirror/carpet/fireflies, the sargent's walk | 1000 Terrors, Bath House, Dark Passageway, Dook's, Invent-a-Storca, Lich Lab, Chasm, the regions, Boot Camp | MISSING_ENGINE (FINAL_REBUILD_GAPS section 4) |
| 16 | The genie lamp's pool has 37 of 61 items (MM9's spell books and scrolls excluded by the item import) | 1000 Terrors | data (item import) |

## Detail by map group

The group sections below were written per map group (scratch `frag_*.md`). "See shared: transitions frame" refers to cross-cutting finding 1.

### Dungeons A: 1000 Terrors, Anskram Keep, Bath House, Beethoven, Chasm of the Dead, Connecting Tunnels, Dark Passageway, Dook's Castle, Dragon Stadium, Drangheim Prison, Dungeon of Secrets

Evidence base: the installed `assets_dev/worlds/mm9/events/maps/<stem>.lua` and `maps/<stem>.scene.yml` (converted
2026-11-05/06), each project's `README.md` "Scripted objects" table and `convert.py`. Two maps carry MM9's messaging
as data with one dispatcher `send(target, message)`: 1000 Terrors (`TRIGGERS`, `ON_OPEN/ON_CLOSE`, `KIND`, `DEATH`
tables, `mm9r_1000terrors/convert.py` `map_script` ~l.327-560) and the Dungeon of Secrets (`DOOR`, `TRIGGER`,
`SHOOTER`, `DAMAGE`, `TOUCH`); the other nine are hand-wired per chain. "R2" = written in the converter, not yet in the
installed files (no `*.cinematics.yml` in `assets_dev/worlds/mm9/maps`, no `MM9Cinematic`/`CameraShake` in the
installed Lua): takes effect with the running rebuild. Headless checks (scratch `sc_g1_*.yml`) are cited where run.

#### Scripts
| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| 1000t_circleshooter.scr | 1000terrors (Sorc0/1Shooter, Sorc*Shooter0-2) | ListMaker over 5 markers: moves round them firing, then triggers its stop trigger (params 5) | SHOOTERS `burst = 5, stop = ...` (1000terrors.lua l.~45-60, convert.py l.385); fires from the statue, no marker flight | PARTIAL |
| 1000t_flyingcreature_.scr | 1000terrors (FlyingCritter0-18) | dormant until `Go`, then flies its marker path | KIND actor, `go` -> `evt.WakeActor` (lua `send`); path not carried (README "Unmatched") | PARTIAL |
| 1000t_lightningshooter.scr | 1000terrors (Sorc0Shooter1, Sorc1Shooter3) | lightning at LightningMarker while on | SHOOTERS `target = marker`, MiddleDoor5's open turns them on | OK |
| 1000t_skeletonhead.scr | 1000terrors (SkeletonHead "SkelHeadShooter0 SkelHeadShooter1") | `:Start` on `Go`: rotate 180, `:TurnOff` triggers both shooters `Go` | TrigSkelHeadOn0 sends `{"SkeletonHead","go"}` (lua l.133) but `KIND` has no SkeletonHead and `send` has no branch for it: nothing happens (README claims the bolts) | MISSING_DATA |
| 1000t_skheadshooter.scr | 1000terrors (SkelHeadShooter0/1 "TrigSkelHeadOn0 5") | on `Go`: 5 shots (1/s) at its target | SHOOTERS entries exist (`burst = 5`), only reachable through the head's `Go`: never fire | MISSING_DATA |
| 1000t_sorcstatues.scr | 1000terrors (SorceressStatue0-7) | `go`/`stop` turn the statue's shooter on/off; casting anim + CastingSmoke | KIND statue -> shooterOn/Off(STATUES[...]); no anim, no smoke | PARTIAL |
| ak_giantimp.scr | anskramkeep (GiantImp) | appears with guards when the gates are done | TriggerGiantImp pads (event 90): slabs fall, ExitStairs rises, Imp + guards shown (README; scenario_scripted passes) | OK |
| ak_impgate.scr | anskramkeep (ImpGateSpawner0-7 "Imp 5 killed ImpGateFire<k>") | 5 Imps one after another, fire out, key 510-517 | pads 170-183, kill hook 95, keys 90510-90517 / 90039, SetSprite 200+k | OK |
| anskrammainline.scr | anskramkeep (Killed) | counts gates, quest key 39 | the last gate gives 39 (README "Killed") | OK |
| alarmcontrol.scr | drangheimprison (AlarmControl) | pass/alarm keys 5007/5006, guard hostility | damage/killed hooks ring alarmbell.wav, set 5006 | OK |
| bathfurnace.scr | bathhouse (GasRelease0) | valve: fires, pistons, steam, quake, boils Fatc | click handler (README "The furnace"); quake `evt.CameraShake` at R2 (bath_cinematics.quake_lua) | OK |
| bottlefollow.scr | beethoven (BottleNW/NE/SW/SE) | the start's bottle drifts the marker lists to the manuscript | `evt.SpawnWorldModel` mm9_bottlefloat, pads 170+k | OK |
| buttonpad.scr / buttonpuzzle.scr | 1000terrors (ButtonTrigger/0/1, PuzzleDoor/B/C0-15) | SetTrap, 4x4 lights-out push, MoveAway, Reset | PADS table, setTrap/pushBlock/resetPad (lua l.~255-295); B/C start Locked | OK (both) |
| coffinmummy.scr / coffinraise.scr | beethoven (PetrifiedMummy0-7, CoffinRaised3-9,15) | Raise: lid anim, Awaken mummy; mummy kicks the coffin (destroy), CanDamage on | pads 150+k, mummy shown hostile, `Coffin<k>`; destructibles `CoffinRaised*` trigger_destroy_only (scene); B3 `mummy(k)` CanDamage at R2 | OK (both) |
| cronakiga.scr | chasmofthedead (CronaKiga) | click: awaken PetrifiedMummy16 chain, item 390, 10 000 xp, key 48/169 | README "Crona Kiga" | OK |
| darkp_bridgepuzzle/bridgereset/canyonswitch/raisingbridge/raisingswitch/warrior.scr | darkpassageway (PuzzleManager0, SwitchCreature0-5, Bridge0-4, ColloidalWarrior0) | 5-bit bridge state machine -> TeleportDoor0; banshee-eye canyon; warrior's death unlocks TeleportDoor1 | README table; lua handlers 221 (`PuzzleSolved`), 218 (`WarriorDead` from the kill hook l.181) | OK (6) |
| dc_sargent.scr / dooksleepgaurd.scr | dookscastle (SleepCaptain, HallwaySleeper0-3) | the sargent walks to each sleeper and wakes it; sleepers cower/fidget | SleepTrigger event 73, timer 200 wakes one every 3 s; no walk, no anims | PARTIAL (both) |
| dp2steam.scr | bathhouse (Fire1-4) | FireOn/FireOff | never sent in MM9 (README "Unmatched") | NOT_NEEDED |
| dp2waterdamage.scr | bathhouse (Deathwater2, WaterthatBoilsA) | DamageOn | never sent in MM9 | NOT_NEEDED |
| drangheimprisoner.scr | drangheimprison (InterrPrisoner0-2) | Use: 500 xp once without the pass, dialogue 431 | events 54067-54069 | OK |
| dungeonjukebox.scr | anskramkeep (DungeonJukebox) | every 2-8 min a random creepy sound (door creak, owl, distant thunder ... 10) behind the player | not in convert.py, README or Lua | MISSING_DATA |
| eborabath.scr | bathhouse (Ebora) | immune, taunts, third dead concubine -> escape, keys 349/350 + 80 000 xp | installed Lua `escape()` l.153 gives the keys; cinematic `ebora_escape` at R2 | OK |
| eboraconcubine.scr | bathhouse (Concubine1-3) | random Siren skins, OnDeath -> DeadConcubine | kill hook 98 counts; skins not carried | PARTIAL |
| effectsmgr.scr | bathhouse (EffectsMgr, EarthQuake) | QuakeOn on the first valve opening | `evt.CameraShake(0.5, 18)` + loop sound at R2 | OK |
| endcount.scr / endcounttrigger.scr | 1000terrors (EndCount; Spawner8/13) | third counted spawn brings a Greater Demon | COUNTS / END_DEMON (lua spawn()) | OK (both) |
| fatc.scr | bathhouse (BigColWinPool2) | KillFatc -> Die | boiled 2 s after the valve | OK |
| furnacewarning.scr | bathhouse (FurnaceWarning) | click: warning text | click faces | OK |
| giverandom.scr | 1000terrors (Genielamp) | once: gold, xp, an item of 61, heal, attribute | handler 371; 37 of 61 items exist (GENIE_ITEMS) | PARTIAL |
| imphenchman.scr | bathhouse (ColSInRoomA0, ColGInRoomB0) | wander, `Help` | `Help` never sent; ordinary actors | NOT_NEEDED |
| lichinstructions.scr | chasmofthedead | click: key 296, item 447 | README | OK |
| ludwigsmanuscript.scr | beethoven (Manuscript) | item 248, key 16 / 110 | event 90 | OK |
| magiccarpet.scr | darkpassageway (ElevatorObj "0") | rises 500 LT/s, drifts where the party faces to the ledge | linear lift + invisible plank (README Deviations): reachable, not steerable | PARTIAL |
| mummyawaken.scr | chasmofthedead (39 mummies) | dormant until awaken/hit, chain p0/p1 | README "Mummies" | OK |
| njamfreeze.scr | 1000terrors (Njam) | OnPanic/OnFrozen, Njam1-7.dtx freeze skins | inside `njam_freeze_win` (R2); skins: no runtime skin swap | PARTIAL |
| njamtaunt.scr / tauntman.scr | 1000terrors (NjamtheMeddler0, TauntMan) | Trigger19: taunt scene, key 497, Door0 | `njam_taunt` (R2); installed: handler 379; lines RolloverText 15/16 not extracted | OK (both) |
| offrailtrigger.scr | chasmofthedead (Shooter0 "Trigger") | PurpleThingy once off the AI rails | one-shot pad on the dais | OK |
| passagegemstone.scr / passagelaser.scr | darkpassageway (Gemstone, GemLight0, LightBeam0-3) | beams, cage doors, DesertDoor0 | `evt.Beam`, Door1-6 + DesertDoor0 open | OK (both) |
| passagemirror.scr | darkpassageway (Mirror0-3) | a click rotates the mirror 10 degrees | counter + status text, beams show the aim; the model does not turn | PARTIAL |
| steamvent.scr / steamventdb.scr | bathhouse (SteamVent0-3, DamageBrush0-3) | 3 s on/off, 200 damage box, steam | polled boxes, 20 fire/s, mm9:smokestack | OK (both) |
| wg_hand.scr | 1000terrors (LeverHand) | never shown by WinMan | nothing | NOT_NEEDED |
| wg_njamcam/shot2cam/shot5cam/shot7cam.scr | 1000terrors (NjamCam, WG_Shot2/3/5/7Cam) | the win cutscene's cameras | shots of `njam_freeze_win` (cinematics_1000t.py l.7-10, 94-130); R2 | OK (4) |

#### Wiring and objects without a script
| Map | Chain or object | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- | --- |
| 1000terrors | WinMan (Switch03) with key 108 -> ChangeLevel ExitTrigger1 (Hall of the Gods) | the win moves the party to the Hall | **installed** handler 370 `evt.MoveToMap(..., "hallofthegods.odm")` (lua l.481; that ODM was deleted by P1): headless `sc_g1_win.yml` gives key 109 but no transition, the party stays. convert.py `hall_of_gods_arrival()` (l.65) and the cinematic's step 36004 fix it at R2 | PARTIAL (P1 until R2) |
| 1000terrors | 16 actor DeathTriggerTargets (Eye/Orbus/... -> Spawner0-13, TP0-5; LesserDemon0 -> StairGate open) | spawns, the stair gate | `DEATH` table (lua l.113), kill hook -> `send` | OK |
| 1000terrors | Trigger -> Shooter/Spawner/door/trigger chains (55 Triggers, 29 Shooters, 14 Spawners) | MM9 messaging | `TRIGGERS` + `send` dispatcher; scenario_scripted passes (FINAL_REBUILD_WORK P1) | OK |
| 1000terrors | Trigger -> Fire SpawnSmoke0-3 / GenieSmoke `on/off` | smoke puffs | `send` ignores kind Fire | PARTIAL |
| 1000terrors | Trigger18 -> SpawnTrigger0-3 -> SpawnPiece0-3 `destroy` | the demon statues crumble | `send` hides the faces with `evt.SetFacetBit` (lua l.339), not `evt.DestroyDestructible`; the scene also lists SpawnPiece0-3 as damageable destructibles (500 hp), so their saved state stays "standing" | OK (P3 note) |
| 1000terrors | LowerLever/LowerLever0 -> ElevatorGear1/2 (RotatingBrush) toggle/reverse | gears spin with the lift | the gears ride the lift (AttachTo) and spin while it moves (mover spin, `lift()` on, reverse + off on arrival; 2026-11-06 night) | OK |
| 1000terrors | WeightedLift0-15 (TouchToOpen, sink 160 LT under the party) | water hall floor sinks | built static (FINAL_REBUILD_WORK E2 deferred); no route blocked | PARTIAL |
| 1000terrors | Rotating Lever 16/18 -> `Upper Chomper 1/2`; Fan15-23, Wind15-23 on/off | targets absent from the DAT | nothing | NOT_NEEDED |
| anskramkeep | airlock (SwitchLever0, PanelLever, Switch0/1, Outerdoor0/1, Innerdoor0/1 lock/unlock/toggle) | one gate after the other | events 71-74; both at once (README Deviations); scenario_scripted passes | OK |
| anskramkeep | ShooterPlate5-10, CeilingCrushPlate1-3, PivotWallTrap1-3/PivotButton1-3 and their Trigger relays | traps | events 60-88, timers 150-161 | OK |
| anskramkeep | Floordoor2/3 DeathTrigger -> GiantImpGuard0/1 `appear`; TriggerGiantImp -> FloorDoor1-4 `destroy` | slabs break, guards appear | slabs are `slide` movers, guards shown by event 90 | OK |
| anskramkeep | Outerdoor0 open -> Portaltrigger0 on/off; RoundDoorLeft0-3 -> OuterWheel0-3 | portal visibility; wheels absent from the DAT | engine portals; nothing | NOT_NEEDED |
| bathhouse | Switch0 -> WaterProp Use, BlueWater2 Drain, Door6/7 unlock | drain, doors | one handler; Door6/7 locked until it (README) | OK |
| bathhouse | StepTrigger0-2 -> SpawnLoc0/1 spawn | 4 Jellyspores | hidden spores shown once | OK |
| bathhouse | TriggerFloodTrigger -> TriggerFloodImp; DragonDoor1 -> DragonDoor2 | targets absent | nothing | NOT_NEEDED |
| beethoven | Lever5/6 -> SDoor11/12 open + lock | the great door | event 91, stays open | OK |
| beethoven | Trigger0-7 -> CoffinRaised* Raise | coffins | pads 150+k | OK |
| chasmofthedead | ShooterPlate/HSP/SDU/HS, CWPlate, SpikeRow1-14 wave, CeilingCrush3/4, Pendulum1/2 (+PendulumWhoosh1/2 sound leaves, not built), Gratetrap0, PivotWallTrap1 | traps | README "Scripted objects" (all hand-wired); Door auto-close now in the scene (68 `auto_close_seconds`), the README's "not carried" is stale | OK |
| chasmofthedead | PivotWallTrap1 open/close -> AIBarrier21 on/off | monsters kept off the turned trap | actor barriers are static | PARTIAL |
| chasmofthedead | Trigger2-6 RESURRECT (AutoResurrect, 21 zombies), Trigger0/1/7, CKTrigger awaken | buried zombies, mummies | README "Buried zombies", "Mummies" | OK |
| chasmofthedead | Apparition13-25 -> GhostSpawner spawn | 13 apparitions | README "Apparitions" | OK |
| chasmofthedead, anskramkeep | TreasureChest TriggerTarget `TreasureShooterTrigger1` (16 chests) | target absent from the DAT | nothing | NOT_NEEDED |
| connectingtunnels | coffin door right -> TreasureChest1 unlock/lock (Locked 1) | grave chest | `CoffinOpen` gates chest event 42 | OK |
| connectingtunnels | DestructableBrush0 (HitPoints 10) DeathTrigger -> DestructableBrush1 Destroy | rock fall breaks by damage | `slide` movers dropped on a **click** (event 61, overrides.yml l.28-29); no scene `destructibles` | PARTIAL |
| darkpassageway | exit room chain ExitTrigger0-3 (one on at a time), ExitRiser/ExitRamp, Switch -> ExitReset, magic elevator sound | the way out | README "The exit room"; ambient switch (C10) | OK |
| darkpassageway | SpikeTrigger1 -> SpikeDoor1-4 open + lock; Spikes1 PropDamager 100 one-time | pit trap | flaps tip, damage by the fall only | PARTIAL |
| darkpassageway | Painting open -> DoubleDoorL40 open, PerceptionBrush1 off; SeaMonsterFemale0 death -> DB_TeleporterCage0 Destroy; TriggerDoor0/TriggerAttack0 -> ForestDoor0 | doors, cage | README; lua l.162-181 | OK |
| darkpassageway | Door0 (Locked, MoveDist 0, nothing unlocks) | never opens | static | NOT_NEEDED |
| darkpassageway | PerceptionLight0-60 (red 100 LT lights at PerceptionValue 20) | trap lights shown to a perceptive party | scene pulsing lights shown by Perception (shared check, event 904; scenario_lights.yml; 2026-11-06 night) | OK |
| darkpassageway | Teleporter x10, CClientFX fireflies x7 | teleports; particles | polled boxes + `evt.MoveToMap`; fireflies not built | OK / PARTIAL (fireflies, P3) |
| dookscastle | Tempbutton (behind Sheild0) -> doorslide open -> DOOK_HOSTILITY remove; doorslide close -> `temp button` (absent) | secret door, militia hostile | event 70, `Hostile` var | OK |
| dookscastle | ScurryTrigger0/1 -> ScurryBasilisk0-5 Hide | they run to HideMarker | removed where they stand | PARTIAL |
| dragonstadium | `p1/p2/p3 level 1..7` (DestructableBrush HitPoints 200; each DeathTrigger destroys the level above) | pillars break by damage, the levels above fall | `TRIGGER_pillar_*` faces broken by a **click** (events 70+, `evt.SetFacetBit`); no scene `destructibles` | PARTIAL |
| dragonstadium | DragonTrigger -> DragonKing0 Trigger | the dragon's fly-in (Dragon.scr) | grounded boss, later work (README) | out of scope (monster AI part) |
| drangheimprison | lever0-28/blever0-2 -> Celldoor* unlock/use/close/lock | cell doors by their levers | events 200-222, locked cells say so (230) | OK |
| drangheimprison | lever17 -> Celldoor18 | MM9 opens and shuts it | Celldoor18 static, standing open (needs `authored_open` for `rotate`, README Deviations) | PARTIAL |
| drangheimprison | Lid1 <-> LidWheel1 use; Door1/Door3 -> DwarvenSmith on/off; TriggerBeatings0/1; NagGuardTrigger0 | well lid, smith, interrogation, guards | events 240/241, smith sounds, beatings, `SetMonsterRelation` | OK |
| drangheimprison | SecretDoor0 open -> TreasureChest2 unlock | chest is not Locked in the DAT | chest opens on a click | NOT_NEEDED |
| dungeonofsecrets | the whole course (123 Triggers, 80 Shooters, 24 knockback DamageBrushes, axe doors/traps, timer levers, gauntlet, double axe, gates, water grate, elevator) | MM9 messaging | `DOOR`/`TRIGGER`/... tables + `send` (README); doors.json "not a mover" rows are name-key misses (names with spaces) | OK |
| dungeonofsecrets | saw8a/b, saw9, Blade (RotatingBrush spin; Blade 1080 deg) | saws spin | the saws ride gtrap8a/b and gtrap9 and spin by the dispatcher's on/off (mover spin, non-solid); Blade one turn | OK (Blade PARTIAL) |
| all 11 | AmbientSound (512 objects) | placed loops | scene `ambient_sounds` in every map but Drangheim Prison (it has none in its DAT) | OK |
| all 11 | water volumes (C8: Bath House, Beethoven, Chasm, Dark Passageway, Dook's Castle, Dungeon of Secrets, 1000 Terrors) | swimming | solid wading faces, dive boxes and sink-in teleports instead (scene `water_volumes` 0 in all) | PARTIAL; Dark Passageway OK 2026-11-06 (swum; README "Water") |

#### Gaps
- P1 — 1000terrors: the installed win switch (handler 370) moves to the deleted `hallofthegods.odm`; verified headless
  (`sc_g1_win.yml`): key 109 is set, no transition. Fix: MISSING_DATA, already in the converter
  (`hall_of_gods_arrival()`, cinematic step 36004); confirm after R2 with the same scenario asserting
  `map_transition_requested` to `hallofthegods.blv`.
- P2 — 1000terrors: the skeleton head trap never fires (SkelHeadShooter0/1). Fix: MISSING_DATA: convert.py `kinds`
  must give SkeletonHead (1000T_SkeletonHead.scr) a kind whose `go` calls `shooterOn` on its two ScriptParams after the
  180-degree turn's 1 s (and `stop` -> shooterOff); the README row is wrong.
- P2 — connectingtunnels, dragonstadium: rock fall and the 21 pillar levels break on a click instead of by damage.
  Fix: MISSING_DATA: emit them as scene `destructibles` (shared dungeon/destructibles.py: drop their `slide`/TRIGGER
  rules) with `destroyed_event` handlers that `evt.DestroyDestructible` the DeathTriggerTarget (the chain).
- P2 — 7 wet G1 maps: no swimming (C8 open): wading faces, dive boxes. Fix: MISSING_DATA (`swim: true`, remove the
  wading faces per map; the engine swims).
- P2 — drangheimprison: Celldoor18 is a static open leaf; lever17 does nothing. Fix: MISSING_DATA (an `authored_open`
  build for `rotate` movers in dungeon/movers.py, as linear movers have).
- P3 — anskramkeep: DungeonJukebox's random creepy sounds. Fix: MISSING_DATA (a timer of 120-480 s playing one of the
  ten sounds with `evt.PlaySoundName`).
- P3 — darkpassageway: 61 PerceptionLights. Fix: MISSING_DATA (BLV lights switched by `evt.SetLight` from the shared
  perception poll, dungeon/perception.py).
- P3 — 1000terrors, dungeonofsecrets: RotatingBrush gears/saws/Blade do not spin. Fix: MISSING_ENGINE (continuous
  spinners, FINAL_REBUILD_GAPS section 4).
- P3 — 1000terrors: Fire smoke on triggers (SpawnSmoke0-3, GenieSmoke, the statues' CastingSmoke); statue casting and
  skull turn anims. Fix: MISSING_DATA for the smoke (an effect at the Fire on `on`, Verhoffin's DUST_ON_HIT route).
- P3 — 1000terrors: shooters' marker flight, flying critters' paths, WeightedLifts static. Fix: MISSING_ENGINE
  (moving decorations / weighted lifts held down while weighted).
- P3 — chasmofthedead: AIBarrier21 switched by the pivot trap. Fix: MISSING_ENGINE (a Lua switch for an
  `actor_barriers` entry).
- P3 — bathhouse, 1000terrors: Siren skins, Njam's freeze skins. Fix: MISSING_ENGINE (runtime skin swap).
- P3 — darkpassageway, dookscastle: mirror model rotation, steerable carpet, spike pit's 100 damage, fireflies,
  scurrying basilisks, the sargent's walk and sleepers' anims. Fix: MISSING_ENGINE (moving/rotating decorations,
  walking NPCs) except the spike damage (MISSING_DATA: a pad hit on the pit floor).
- P3 — 1000terrors: GiveRandom pool 37 of 61 items (MM9's excluded spell books/scrolls). Fix: data (item import).
COUNTS scripts: OK=39 PARTIAL=10 MISSING_DATA=3 MISSING_ENGINE=0 NOT_NEEDED=4
COUNTS wiring: OK=22 PARTIAL=12 MISSING_DATA=1 MISSING_ENGINE=0 NOT_NEEDED=6 (plus 1 out of scope: Dragon.scr)

### Hall of the Gods, Invent-a-Storca, Kluso's House, Lich Lab, Ruined Temple, Ta'Sar Academy (G2a)

Verification: the maps' own scenarios were run headless against the installed `assets_dev` (2026-11-06, logs in the
scratch folder `g2a_runs/`). `scenario_doors_exits.yml` passed on all six maps, and `scenario_scripted.yml` passed on five.
Hall of the Gods' `scenario_scripted.yml` fails at step 22 (`cinematic list` lacks `gods_epilogue`). That is expected
until R2: its generator already expects the cinematic, and the installed map still has the 90 s timer route.
Lich Lab's scenario passed all 80 steps, including the elixir, the engine, the transformers, the shooting range, the
summoner, the cages and the ickies. Ta'Sar's covers the whole library puzzle (key 9516, the door, the Book of Rules).

#### Scripts
| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| blackheart.scr | klusoshouse (Blackheart 247) | :OnUse giveitem 29, givekey 223, removeobject, alarmbell.wav; :Init removes the dagger once key 223 is held | `klusoshouse.lua` handler 75 (item 29, key 223, SetSprite 300 off, alarm bell, `linkBroken` wakes the hidden guards and the sleepers); handler 1 re-hides it; scenario_scripted pass | OK |
| bookofrules.scr | tasaracademy (BookRules 697; podium Prop162 by PropTrigger.scr) | :Onuse: with key 57 and without 59, key 59; else, without 166, key 166; either way item 391, 5000 exp, quest.wav, the book removed | `tasaracademy.lua` handler 270 (same keys, item 391, exp, sound, SetSprite 420 off), re-hidden on load; scenario step "Book of Rules on Ludwig's errand" pass | OK |
| colloidalgenie.scr | ruinedtemple (Genie 336) | :Appear, 2 s, then 3 s later :OfferWish `DoRude 435` by itself; :GrantWish by keys 5022-5025: 5000 gold, 5000 exp, an item, or GiveAttribute 0 +10; disappears 3 s later | `ruinedtemple.lua` 409 (shown), 50336 (the wish on RUDE close), 410 (removed); actor 13 `mm9_rude_id: 435` in the scene. The dialogue opens on a click, not by itself | PARTIAL (P3: no automatic DoRude) |
| converter.scr | lichlab (SkeletonTransformer 1652, SkeletonTransformer0 1687) | `create`: spawns a CommonerHuman2MaleA at MarkerSpawn that walks into the chamber; `convert` (from TriggerUnlock): shooters' effects, then the peasant is replaced by a Skeleton | `lichlab.lua` 202-205, 252-255: a switch shuts the chamber; 5 s later arc beams and `SummonMonstersById` 9135 (a Skeleton); 1 s later the door rises. Since 2026-11-06 the conscript too: with the door down a Commoner (9050) appears at the marker, walks in (`evt.MoveActorTo`), cowers and is turned where he stands (PeasantTransformee.scr) | OK |
| elixircook.scr | lichlab (Prop18) | hasitem 378, then takeitem 378, giveitem 561 | handler 222; scenario pass | OK |
| geniecrystal.scr | ruinedtemple (Lamp 338) | use (once): trigger the genie `appear` | handler 241 then timer 409 | OK |
| giveelixir.scr | lichlab (Prop17) | 358 + 561 give 246 | handler 223; scenario pass | OK |
| ilshealerroom.scr | lichlab (PromoTrigger 1088) | :Onclickon (after the pod `close`, 3 s) acts only while `nWorking`, which :OnFix sets, and **RotatingDoor1, the engine lever, sends `Fix`** (its OpenTriggerTarget3 is PromoTrigger, OpenTrigger3 `Fix`); with the party in PromoVol1: 63000 exp, quest.wav, and GivePromo Lich for each holder of keys 433-436 (never granted in MM9), key 299; Lightning0 off | handlers 200, 250, 251: the lich switch closes the pod, it strikes 3 s later, then `transmute()`: key 296 (Lich Instructions) plus a carried Elixir and a Wizard or Necromancer gives the Lich, 63000 exp and key 299 (a user-approved design). The lever (201) only swings. The README's claim (line 277) that "nothing sends Fix" is wrong | PARTIAL (P3: the lever's Fix is not required; working by design) |
| ilsshootingbook.scr | lichlab (firebook2/3/4) | use: OpenBook, then the shooter `On` (a second use Off/On); `Done` (the target's DeathTrigger) closes the book | 206-208 and timers 256-258: a FireMissile every 1.5 s; 10 hits sink the target and end the book; scenario pass | OK |
| is_ficky.scr, is_fickyflock.scr | inventastorca (BirdIntheSky0, BrettBird0-4) | BirdTrigg `scatter`: the flock flies up the shaft to the FlockM markers and dies | handlers 194/195 `scatter()`: woodcreak sound and `MM9.removeActor` x5; no flight | PARTIAL (P3: they vanish instead of flying off) |
| is_killinglich.scr | inventastorca (LKToKillGreenParty0 682) | `Kill` (from DoubleDoorL9's open or SpookTrigger5): Fidget2, then RAttack1, then `Trigger GreenPartyDude0 Destroy`, then BaseMelee | `lichKills()` (120, 201): mutual hatred between 9207 and 9111, group 10 hostile and awake; the dying adventurer dies only if the fight kills him | PARTIAL (P3) |
| lichengineprop.scr | lichlab (Lichengine 1515) | `start`: startup anim, then spincycle loop; `finish`: shutdown (sent by RotatingDoor1's Open/CloseTriggers) | not carried: the engine prop is static (README line 95: "MM9: engine start/finish animation") | MISSING_ENGINE (P3: decoration animation clips driven from Lua) |
| ll_flyingcreature.scr | lichlab (Lobby/RightWing/LeftWing Icky0-7, 24) | hang (LoopAnim Hang) until `Go`, then fly the LISTNAME marker list | handlers 233-238: each wing's group (60/61/62) turns hostile on its trigger; no hang clip and no flight path | PARTIAL (P3) |
| orb.scr | inventastorca (Prop0-6) | :OnUse giveitem 252, quest.wav, removeobject; :Init removes all when key 337 is held | ORBS 210-216, `takeOrb`; load hides when 337 is held; scenario pass | OK |
| rt_cavein.scr | ruinedtemple (CaveInLeft/Right/LeftB/RightB) | `Fall`: wait p2, destroy the rail or ceiling brush (and the floor slab), MoveToPos the marker at 220 | caveIn timers 405-408: the rail or ceiling brush moves out, then the rock drops (sink movers); the floor slabs are not built (coplanar) | OK |
| rt_counterbalance.scr | ruinedtemple (WO_CounterBalance) | `Fall` **or OnDamage**: MoveToPos at 300, then destroy DB_Crypt0 | handler 220 (PrisonButton2) and 404 (crypt open); damage does not drop it | PARTIAL (P3: OnDamage not carried; the button works) |
| skillbook.scr | tasaracademy (Prop5/88/89/90/91/94) | GiveItem (a named book, or random 285-306), removeobject | 280-285 (MM9.random 285-306, Blade 285); items 10285-10306 are in worlds/mm9 items.txt; scenario pass | OK |
| spook.scr | inventastorca (SpookObject) | `Play`: a random sound from its list; a random loop every 2-8 min | 196-200, 251 (8 sounds, re-armed 120-480 s; not positional) | OK |
| suntemplebuttons.scr | ruinedtemple (MainButton) | symbol flags; MainButton sends MainElevator `open` only on Star1, !Star2, !Diamond1, Diamond2, !Moon1, !Moon2 | 210-217 `symbol()`/`sendLift()` (MoonButton1 is wired to Star1 as in MM9); scenario pass | OK |
| switch.scr | lichlab (lichswitch "Engineglass1 toggle") | up/down anim; trigger p0 with message p1 | handler 200 (the pod's lid and glass close) | OK |
| tasarbook.scr, tasartable.scr | tasaracademy (20 books, 6 tables) | the book order keys 9517-9519; the tables' keys 9501-9504; :CheckAllKeys gives 9516 and LibraryDoor unlock/use/lock | 220-249 `takeBook`/`placeBooks`; 9516 opens the LibraryDoor group, reopened on load; scenario pass (all four tables, key 9516, door open) | OK |
| tasarchalice.scr | tasaracademy (Prop145-152) | the "Right" one: GiveAttribute 0 10 0 288000, givekey 9500 | 210 (Might +10, key 9500, once per character), 211 (the others) | OK |
| treeoflife.scr | ruinedtemple (Treeoflife 5) | :Onuse without 256: item 241, key 256, removed, TriggerCaveIn1 on; :Main TriggerCaveIn1 off, removed once 256 is held | 240 (`CaveIn1Armed`), load re-hides it | OK |
| wg_npc334/335/336.scr | hallofthegods (Hanndl 127, Krohn 149, Skraelos0 150) | the end-game cinema's cast: :Loop hides, :OnStart shows; WalkTo HanndlMarker; voice lines, then :End (WinMan) | installed: handler 1 shows the cast and puts Hanndl at HanndlMarker; timer 260 gives the Writ (394) after 90 s and hides the cast. At R2: `gods_epilogue` (convert.py map_script, cinematics_hall.py; README "Cinematics") | OK (the cinema at R2) |
| wg_scene7cam1.scr | hallofthegods (WG_Scene7Cam1 163) | the cinema camera (MoveToPos Scene7MK1) | not in the installed map; `gods_epilogue`'s shots at R2. The Hall's scenario_scripted fails until then | OK (R2) |

#### Wiring and objects without a script
| Map | Chain or object | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- | --- |
| hallofthegods | ExitTriggerHall; ExitTrigger0 (scripted) | an exit to Arslegard City; ExitTrigger0 only by `trigger ExitTrigger0 trigger` | positioned exit; Skraelos' 50125 `toAfterworld()` (afterworld.blv); doors_exits pass | OK |
| inventastorca | DoubleDoorL1-14 OpenTrigger -> `AxeTrap` toggle | no AxeTrap object in the DAT | nothing (README line 188) | NOT_NEEDED |
| inventastorca | DoubleDoorL9 open / SpookTrigger5 -> LKToKillGreenParty0 `Kill` | the Lich King kills the adventurer | 120 and 201, then `lichKills()` | OK |
| inventastorca | FallingBookcaseSwitch -> FBR1 -> ... FBR5 relays -> FallingBookcase1-6 (+ itself locked, PerceptionBrush5Level10 off, the last one's AITrk100 off) | a one-a-second domino | 170 and timer 250 `DOMINO` (relays folded into the bookcases); scenario pass | OK |
| inventastorca | SecretSwitch/0/1 -> SecretPanel/0/1 toggle or open, self lock, hint off | secret niches | 171-173 | OK |
| inventastorca | DeskDrawer/0, LadderDoor, SecretPanel1 Open/Close -> PerceptionBrush7/8/9/10 off/on | hints follow the furniture | 154-156 `hintOff` | OK |
| inventastorca | DestructableBrush0-3 death -> PerceptionBrush0/1/2 off; DB2 -> "Tom Needed A Trigger1" -> AITrk47 on, PerceptionBrush3 off | walls broken by weapon damage (stonecrumble) | 180-183: **a click** breaks the wall (sink mover) and turns the hint off; no scene `destructibles` (the installed scene has none) | PARTIAL (P2: click, not damage) |
| inventastorca | BustOutTrigger0/1 -> BustOutLich0 ForceBreak (DestructableBrush4), BustOutLichKing0 ForceFall + DestructableBrush5 destroy; DeathTrigger to BreakInSmoke0/1 (absent) | the cage wall bursts, and the Lich King drops through the ceiling | 190/191 (brush sinks, rock_crush, actors placed, then WakeGroup) | OK |
| inventastorca | ScurryTrigger0/1 -> ScurryBasilisk0-5 `Hide`; BirdTrigg0/1 -> scatter; SpookTrigger0-4 -> Play | the critters run off, the flock flies away, sounds play | 192-200 (removeActor, sounds) | OK |
| klusoshouse | GuardTrigger -> LowerPatrol0/1 (and UpperPatrol0/1, absent) `charge`, sent by KlusosPatrol.scr AlertOthers | an alarm relay, aware2.wav | not built (README line 74); native AI pursues on sight | PARTIAL (P3) |
| klusoshouse | the Blackheart's object link -> LowerTimed0-6 (KlusosHidden) and UpperSleep0-7 (KlusosSleeper) | the theft reveals or wakes the guards | 75 `linkBroken()`; scenario pass | OK |
| klusoshouse | 26 RotatingDoor leaves (13 groups), none locked | a click | 101-112 and 120; doors_exits pass | OK |
| lichlab | RotatingDoor1 (engine lever) open -> Lichengine `start`, PromoTrigger `Fix`; close -> `finish` | the lever fixes and spins the engine | 201: the lever swings only; the Fix is replaced by key 296 (see ilshealerroom) | PARTIAL (P3) |
| lichlab | Enginedoor1 Open/Close -> PromoTrigger Close/open; Engineglass1 Open/Close -> Glow1 (GlowingLight) on/off | the pod's state; the pod glows while shut | the pod state is in Lua vars (200/251); Glow1 on while the pod is shut (evt.SetLight, 2026-11-06 night) | OK |
| lichlab | TransformSwitch0-3 -> skeletondoora/0 open, both switches lock, PanelOn0/1 (AmbientSound) on/off; the doors' Close -> switches unlock; TriggerUnlock/0 -> ShooterTransform0-5 shoot + door close | the transformers | 202-205, 252-255 (AmbientSound vars 1655/1690, beams, a Skeleton); scenario pass | OK |
| lichlab | SkeletonMaster1 DamageTrigger -> SkeletonMaster52 `Resurrect` | a hit raises the buried master | not in the installed Lua; convert.py:57 `DAMAGE_TRIGGERS` writes the damage hook (FINAL_REBUILD_WORK B8) | OK (R2) |
| lichlab | TriggerExplodeL/R -> 4 critters ForceBreak (KingKong) -> cage brushes; DB1/DB2 death -> breakwindow1/2 destroy -> ExplodeSmoke3/0; RotatingDoor167/168 death -> ExplodeSmoke1/2 | the cages burst, the fires flare | 231/232 `bustCages()` (cage groups sink, SetSprite 320-323), fires hidden until then | OK |
| lichlab | DestructableBrush6/16/19 (straw targets) death -> firebook `Done` | the book closes | the timers stop after 10 bolts and the target group sinks | OK |
| lichlab | DestructableBrush1 death -> TriggerLock (absent) | no target | none | NOT_NEEDED |
| lichlab | Lobby/RightWing/LeftWingBatTrigger0/1 -> 8 ickies `Go`, the paired trigger on/off | flight | 233-238 (group hostile) | OK |
| lichlab | TriggerLich -> LichSummoner `startup`; GhostPool0-3 -> SpawnMgr | ghosts rise while the summoner lives | 230 and the kill hook 95 (10 ghosts); scenario pass | OK |
| lichlab | Enginedoor2-4, Engineglass2-4 (pods 2-4), RotatingDoor58 (StartOpen, Sticky) | nothing opens the pods; door 58 stands open for good | the pods are static and shut; door 58 is left out (README lines 93, 96) | NOT_NEEDED |
| ruinedtemple | SunButton/2/3/4 -> HiddenDoor/2 open + self lock; HiddenDoor/2 Close -> buttons unlock; HiddenDoor2 open -> LeftDoor unlock; HiddenButton/2 -> HiddenDoor3 | hidden doors on a 10 s close; the LeftDoor lock | 201-207, 401-403 (LeftDoor locked until 204); scenario pass | OK |
| ruinedtemple | Star/Diamond/MoonButton Open/Close -> MainButton (SunTempleButtons) -> MainElevator; SecondButton -> MainElevator | the combination lift | 210-217, 412 | OK |
| ruinedtemple | PrisonButton2 -> WO_CounterBalance Fall -> DB_Crypt0 destroy -> TriggerHostile0 -> DBEffectsTrigger0 (quake, dust) | the crypt opens | 220/404; quake and dust in convert.py `QUAKES`/`DUSTS` (R2) | OK |
| ruinedtemple | DestructableBrush0-5 (packed dirt, 20 HP) death -> PerceptionBrush4-9 off | dug by weapon damage | 230-235: **a click** breaks the plug | PARTIAL (P2: click, not damage) |
| ruinedtemple | PrisonButton3 -> DoorCryptEscape0 Unlock+Use (and PrisonButton1, absent) -> PrisonDoor Unlock+Open | the escape to the Tree of Life | 221/411 | OK |
| ruinedtemple | Trigger0/Trigger1 -> DestructableBrush6 + glass1-8 destroy, each other trigger, off | the entrance floor collapses | VOLUMES poll, then `collapse()` (EntranceFloor group sinks) | OK |
| ruinedtemple | TriggerCaveIn0/1 -> CaveIn Fall + QuakeObject0/2; DB_Rail/DB_Ceiling death -> DBEffectsTrigger1/2 -> DBQuakeObject + DustObject0-2 | cave-ins with shake and dust | caveIn 405-408; shakes and smoke at R2 (convert.py:97-105, scenario_shakes.yml) | OK (R2) |
| ruinedtemple | DBFloor/DBFloor0-2 death -> DustObject3-6 | the floor slabs shatter with dust | not built (coplanar copies; README line 91) | PARTIAL (P3: no dust) |
| ruinedtemple | AltarDoor, UpDoor, PrisonEntrance/2 CloseWaitTime 5-6 s | linear doors auto-close | the installed doors toggle; E1 `linear_mover` writes `auto_close_seconds` at R2 | OK (R2) |
| tasaracademy | Switch/Switch1 (StartOpen) Open/Close -> SecretDoor1/0 toggle, PerceptionBrush1/0 off; Switch1 locks itself | secret doors | 202/203; the doors also open on their own click (119/120: MM9 leaves them unlocked); Switch1's lock after its second swing is not carried | PARTIAL (P3) |
| tasaracademy | BookButtonFront1/Back1 -> RotatingBookcase1 toggle, the buttons' lock/unlock from the bookcase | the rotating bookcase | 201/152; scenario pass | OK |
| tasaracademy | PitDoorTrigger1 -> PitDoorRight1/Left1 toggle, self off, hint off; the leaves' Close -> trigger on | a trap door over spikes | VOLUMES `trapDoors` (re-arm), Spikes 40 damage | OK |
| tasaracademy | "door crack" (25 HP) DamageTrigger -> "door crack 2" destroy; DeathTrigger -> PerceptionBrush3 off | broken by a weapon | 204: **a click** breaks it | PARTIAL (P2: click, not damage) |
| tasaracademy | Trigger0-3 -> GuardCaptain0 Fight -> Hate Student0-3, DooksGuardCaptain0/1 | sparring | `sparring()` relations | OK |
| tasaracademy | Trigger4 -> DestructableProp0 Destroy (SpawnObject "Dagrell Scale 0.75") | the crate bursts, a Dagrell inside | `smashCrate()` (group 3 shown, hostile) | OK |
| tasaracademy | TaSarTable x6 -> LibraryDoor (Locked) unlock/use/lock | opened only by the puzzle | 220-225 and 200 ("locked" until 9516); scenario pass | OK |

#### Gaps
- P2 — inventastorca (DestructableBrush0-3), ruinedtemple (DestructableBrush0-5), tasaracademy ("door crack"): MM9's
  weapon-breakable walls and plugs are sink movers broken by a click. Their DeathTrigger chains work; only the means
  of breaking differs. Fix: MISSING_DATA. Each map's convert.py should emit these brushes as scene `destructibles` (the
  shared dungeon/destructibles.py route: DAT HitPoints, CanDamage, CustomSound) with `destroyed_event` = the existing
  handler (180-183 / 230-235 / 204), instead of `sink` movers and click events. This is FINAL_REBUILD_WORK C8's "click
  breakables".
- P3 — lichlab: the engine lever's `Fix` (RotatingDoor1 OpenTrigger3 -> PromoTrigger) and the Lichengine
  start/finish animations are not wired. Key 296 replaces the Fix, a user-approved design that works. Fix:
  MISSING_DATA. Optionally require the lever too (a `set("EngineFixed", 1)` in 201, tested in `transmute`), and correct
  the README's claim (line 277) that nothing sends Fix. The animation is MISSING_ENGINE (Lua-driven decoration clips).
- P3 — lichlab: Engineglass1 -> Glow1 (GlowingLight) on/off is not switched. MISSING_DATA: a pulsing light
  switched from 200/251, if the scene's `pulsing_lights` can be switched by Lua.
- P3 — ruinedtemple: the genie's RUDE opens on a click, not by itself (DoRude 435); WO_CounterBalance does not fall
  when damaged; DustObject3-6 under the cave-in slabs are missing. MISSING_DATA (an auto-open dialogue needs an engine
  call: MISSING_ENGINE).
- P3 — inventastorca and lichlab: the flocks and ickies vanish or turn hostile instead of flying their marker lists;
  the Lich King's scripted killing blow is a fight. MISSING_ENGINE (scripted flight paths and actor attack clips).
- P3 — klusoshouse: GuardTrigger's `charge` alarm relay is not built. MISSING_DATA (on the first patrol seeing the
  party: WakeGroup 2 and the alarm sound).
- P3 — tasaracademy: Switch1's self-lock after its second swing is not carried. MISSING_DATA.
- Note (no gap): the Lich Lab damage-resurrect (B8), the Ruined Temple shakes and dust, linear-door auto-close (E1)
  and the Hall's `gods_epilogue` are in the converters and arrive with R2. Hall of the Gods' scenario_scripted fails
  until then.
- No P1 gap in this group: every door, lock, exit and quest key traced here is reachable in the installed maps, and
  the maps' scenarios confirm it.

COUNTS scripts: OK=20 PARTIAL=8 MISSING_DATA=0 MISSING_ENGINE=1 NOT_NEEDED=0
COUNTS wiring: OK=32 PARTIAL=8 MISSING_DATA=0 MISSING_ENGINE=0 NOT_NEEDED=3

### Temple of Honk, The Arena, Thjorad Mine, Training Hall, Verhoffin Ruins, Yanmir's Fort (G2b)

Verification: all 27 project scenarios of these six maps were run headless against `assets_dev` (2026-11-06, logs in
the scratch `scr_audit/g2b/`): 26 pass; `mm9r_yanmirsfort/scenario_scripted.yml:66` fails (Yanmir has 850 of 945 HP
after five party attacks: MM9 makes him immune, see Yanmir row). "(R2)" means the converter already emits it, but the
installed map was converted before that code went in, so it takes effect at the final rebuild that is running now. The
installed `thjoradmine`/`yanmirsfort` have no `cinematics.yml` and no `evt.CameraShake` yet.

#### Scripts

| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| dumbgoose.scr | templeofhonk (BigHonk1, Goose) | :InitDumbGoose 5 s after load: HonkHostility.inc, then :RunLoop runs to a random point every 2 s | overrides.yml:7 `monster_classes` has Goose (M19: row 9293, Honk group) **(R2)**: the installed scene has 16 Honks and no geese. The running loop is not carried | PARTIAL |
| dumbgoose2.scr | templeofhonk (BigHonk0) | as dumbgoose; plus :TurnHostilityOn (HP 10, BecomeHostile), which nothing triggers | as dumbgoose | PARTIAL |
| mine.scr | thjoradmine (Bin2) | :Onuse `exit`s on its first line (dead quest code; TELP 1.3) | nothing (README "Unmatched") | NOT_NEEDED |
| spikedoora.scr, spikedoorb.scr, spikedooropen.scr | thjoradmine (BarWall1, BarWall0, ABDoorBoards0) | :OnePulled counts; at 6, unlock + use; :OnUse before 6 does nothing | thjoradmine.lua:56-59, events 64-66 (jiggle before the sixth spike, open after it); scenario_machinery passes | OK |
| boardspike.scr | thjoradmine (Spike0-17) | :OnUse plays metalwood04, sends OnePulled to its door (param), removes itself | events 70-87 (spike hidden, counter) | OK |
| thjoradquake.scr | thjoradmine (QuakeObject) | :ExecuteQuakeLoop: every 300-600 s a quake at the party, 3-8 s, ShakeAmount 2-5 | convert.py:146-175 `AMBIENT_QUAKE`, timer T_QUAKE 207 **(R2)** | OK |
| tm_minecara.scr | thjoradmine (MineCarA) | `OnDamage MoveToMarker` (line 59): a hit rolls the cart, which destroys MCarBlocker1/ABMineBoards0 | event 110 **on a click** (thjoradmine.lua:537-575); the cart is swapped for a twin, not moved; hits do nothing | PARTIAL |
| tm_fallingtorch.scr, tm_firstfallingtorch.scr | thjoradmine (FallingWallTorch0/1) | `AddTrigger Hit` / `OnDamage MoveToMarker`: the torch is hit and falls to its marker | events 108/109 **on a click**; the torch drops out of sight | PARTIAL |
| tm_torchflame.scr, tm_firstfallingflame.scr | thjoradmine (FallingTorchFire0/1) | :StartSequence/:Barrel1-8: `Trigger DB_Barrel0..8, Destroy` one after another (the barrels are Exploding destructibles); DB_Barrel9 for the first torch | timers 203/204 hide DB_Barrel2-8 by `evt.SetSprite` with a column of fire; **DB_Barrel0/1 are never touched**, and no barrel is destroyed, so their ExplodeDamage (scene destructibles 658-667, handlers 30658-30667 `explode()`) never fires | PARTIAL |
| tm_steamwater.scr | thjoradmine (BlueWater0) | MoveWater: the jet runs down the pipe and smashes ABMineBoards1 | event 68 + timer 205: the boards break after 1 s; the jet is not drawn | OK |
| blowuptheboards.scr | thjoradmine (DB_Barrel6/7 "ABMineBoards3/2") | HitMe: sounds, `Trigger <blocker> destroy` | timer 203 opens ABMineBoards2/3 at those barrels | OK |
| slagextractor.scr, slagbase.scr | thjoradmine (slag, WorldObject0) | :OnUse gives item 398 and key 9512; the base with item 399 sends Show: 5 000 xp, key 37, SetModelFilenames | events 130/131, `showSlag()` sprite swap, restored on load (thjoradmine.lua:605-633) | OK |
| eboramines.scr | thjoradmine (Ebora) | :FreeAtLast (on the tenth hard rock or OnDamage): camera, taunt, column of fire, removed | convert.py:188-, 622, 640 cinematic `ebora_free` (MM9_CUTSCENES.md:94) **(R2)**; damage hook 196 | OK |
| traininghallexit.scr | traininghall (ExitTrigger0) | :OnTouch `exit`s before the reward (line 20; TELP 1.3 moved it to TrainingEnter.scr) | the exit is a plain MM9 exit trigger | NOT_NEEDED |
| th_meantrellborg.scr | traininghall (MeanTrellborg) | Go/Stop: taunts, then `Trigger hSwitch, Use` to launch the horse and resets it | README:111; scenario_scripted (launch 4 s after TriggerTrellborgOn0, stop on Off0, ends on his death) | OK |
| th_lobbyghouls.scr | traininghall (GhoulInSauna0/1) | Go: run up the stairs along Ghoul*Marker0-2; Drop: drop onto the water | README:110: set at the last marker (no run), Drop drops them and shuts the dragon door; scenario passes | OK |
| th_targetmgr.scr, th_targetring.scr | traininghall (TargetMgr, Rank* x16) | a ring's OnDamage: key KEY_WON, `hit` to the manager, which pays PRIZE in gold and lays the target down for good; openall/closeall | README:113; rings are opacity-0 faces with click and missile (TriggerByObject) events; scenario: bullseye pays 8 000 once | OK |
| th_trainingorcs, th_trainingorcobserver, th_trainingorccommander, th_orcsgossip, th_jousttrellborg, th_lookouttrellborg | traininghall (OrcStudent0-3, TrainingObserver, TrainingCommander, BoxOrc0/1, OrcGossip*, JoustVictim/Witness/LookOut Trellborg) | idle animation loops (drills, gossip, taunts) and walks between markers until the party is seen (TrainingHostility.inc) | README:118 "Unmatched": the actors stand and fight with the native AI | NOT_NEEDED (cosmetic) |
| fakebook.scr | verhoffinruins (Book) | :Onuse: keys 281, 290, item 242, removed; :deletecheck removes it with 281 or 282 | README:100, verhoffinruins.lua | OK |
| writ.scr | verhoffinruins (writ); yanmirsfort (DoorTeleportLeft) | after key 99: item 392, 162 000 xp, key 100; hidden until Capstone's `init`. Appended TELP 1.3 block: :Init sets DoorTeleportLeft's DoubleDoorName | Verhoffin README:99; Yanmir README:101 (the converter pairs the leaves) | OK |
| placecapstone.scr, capstone.scr | verhoffinruins (HeadsmanBlock1, Capstone "verhoffin") | with key 98 and item 396 the block sends `place`: key 99, 154 000 xp, capstone shown, writ `init`, item taken; appended TELP block :placed unlocks PrisonDoor2 once DestructableBrush12 is gone | README:98; the bolt handler unlocks PrisonDoor2 (verhoffinruins.lua:79-92) | OK |
| pentagrampuzzle.scr | verhoffinruins (PentagramPuzzle) | :Init closes and locks TortureChamberDoor0/1; start; five steps in order; :OnFailure resets; :UnlockDoor unlocks both, opens only Door1 (`Trigger NULL, open`) | verhoffinruins.lua:166-200 | OK |
| yanmir.scr | yanmirsfort (Givekey) | Use and Trigger do nothing (:GiveEeps is YanmirBase's) | nothing | NOT_NEEDED |
| yanmir_camera.scr | yanmirsfort (YanmirCamera) | ON/OFF; :OnLinkBroken turns it off 3 s after Yanmir is gone | convert.py:460, 764 cinematic `yanmir_death` (MM9_CUTSCENES.md:95) **(R2)** | OK |
| yanmir_endofworld.scr | yanmirsfort (EndOfWorldTrigger) | :HandlePlayer -> PlayerExit (to Frosgard City); :HandleYanmir removes him | `BOX.EndOfWorld` poll, `evt.MoveToMap` frosgardcity.blv FallingStart (README:97) | OK |
| yanmirhidden.scr | yanmirsfort (ForestGiant0-3) | hidden while Yanmir lives | hidden actors, shown on the load after his fall (README:98) | OK |
| yanmirkey.scr | yanmirsfort (Yanmir'sKey) | GiveItem 570, GiveKey 7001, :UnlockCages unlocks the teleporter doors and RotatingDoor61-67 | events 211-226 (README:99) | OK |
| yanmirtrap.scr | yanmirsfort (YanmirTrap) | counts SupportBroken (six DestructableBrush supports, HitPoints 1, broken by **hits**), then TriggerYanmirTrap on | events 200-205 **on a click**, `TrapArmed`; hits do nothing | PARTIAL |
| yf_explodingfloor.scr, yf_fallingfloor.scr | yanmirsfort (YanDstruct0, FallingFloor0) | Fall/Disappear: the floor chunk goes to CaveInMarker0, destroys Planks0 and Xbeams0 | sink movers dropped by the trap's steps (README:96) | OK |

#### Wiring and objects without a script

| Map | Chain or object | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- | --- |
| templeofhonk | HButton/OButton/NButton/KButton (Locked; DoorTrigger `unlock`) -> *CornerStone open -> DoorTrigger h/o/n/kPressed -> SecretDoor, SecretDoorMover | the accountant's key unlocks the buttons; H-O-N-K opens the secret door | `press(letter)` (templeofhonk.lua:72-119; buttons through `letter .. "Button"`, which doors.py does not see); scenario_scripted passes | OK |
| templeofhonk | DoubleDoor13 locked by Honk.scr (key 343); UnlockDoorTrig -> SecretDoor | | event 130 "The door is locked." without 90343; handler 70; scenario_doors_exits passes | OK |
| templeofhonk | TriggerStartCeremony0-2 -> HONK_CEREMONY `remove` | no script listens (convert.py:68-71) | not built | NOT_NEEDED |
| thearena | Arena.scr doors, pens, PlayerInTheHouse, kill hooks | (NPC/quest scope) | scenarios fight, bout, lord, sven, doors_exits pass | OK |
| thearena | WinCheerTrigger0 -> CrowdCheer0-9 `on`, LooseBooTrigger0 -> CrowdBoo0-9 `on` | positional crowd sounds (StartOn 0) | placed as ambient_sounds keys 103-122 with `start_on: false` and never switched; the Lua plays a non-positional `crowdnoise-cheer01.wav` instead (thearena.lua:153, 193, 234, 299, 305) | PARTIAL |
| thjoradmine | Door2 (Locked, no unlocker) | never opens | handler 60 jiggles (doorlock02) | OK |
| thjoradmine | handletrigger05 -> switch05 -> deadbolts -> slidingdoor05; Switch2-5 <-> Door0/1 | refinery door, lift gates | events 61-63; scenario_machinery passes | OK |
| thjoradmine | db12-db23 (DestructableBrush, 1 HP) -> dw `OneDown` (tm_hardrock 10 36 5000; their DamageTrigger turns a hint off) | broken by weapon hits; the tenth gives key 36 and frees Ebora | slide movers, events 90-101 **on a click**; not scene destructibles, so missiles and melee do nothing | PARTIAL |
| thjoradmine | CaveWall0-4 (10 HP), BustOutBrush0-2, DestructableBrush0 (stalactite) -> Stalagtite `toggle`, TorchHolder0/1 | broken by hits | events 102, 107, 111-113 on a click | PARTIAL |
| thjoradmine | Trigger7 -> CaveIn DamageOn/Destroy -> CaveInControl (key 35); TriggerHardRock -> gnolls ForceBreak; TriggerLocation*/SpawnMarker* | | events 140, 141, 150-167 | OK |
| thjoradmine | DBEffectsTrigger0-5 -> DBQuakeObject*/DustObject* (barricades, boards, falling board, stalactite -> TunnelQuake2) | camera quakes and dust | dust as `mm9:smoke`; quakes `quake(name)` convert.py:141-175 **(R2)** | OK |
| thjoradmine | TriggerSpawn -> TriggerLocation1-5; BustOutBrush0-2 -> DwarvenGuard0 FreakOut; TorchHolder1 -> DustOjbect5 | the target names exist in no object (MM9 sends to nothing) | not built | NOT_NEEDED |
| thjoradmine | PerceptionLight0-9 on/off (DamageTrigger plightofftrigger, DB triggers) | red hint lights switched off by the machinery | scene pulsing lights shown by Perception; the machinery's handlers put them out (LIGHTS_OFF, 2026-11-06 night) | OK |
| thjoradmine | DB_Barrel0-9 (Exploding destructibles, HP 10 000, destroyed by the torch scripts) | each one blows up (ExplodeDamage within DamageRadius) | scene entries 658-667 with `explode()` handlers exist but nothing destroys them: the torch timers only SetSprite DB_Barrel2-8 and 9; 0/1 stay | PARTIAL |
| traininghall | dropsequence -> cracktrigger1-5 -> droptrigger -> DestructableBrush6 destroy -> drop open | the chandelier falls with the party | README:109; scenario_scripted | OK |
| traininghall | d2lever <-> Trigger2/3 <-> dummy2door; d4lever0 -> dummy4guide/dummy4door -> woodexplosion, upperbreak1 -> Trigger8/9 -> lowerbreak1/2, upperbreak2; Trigger6/7 -> d4lever0 unlock | the joust and the horse through the wooden wall | README:111-112; scenario_scripted | OK |
| traininghall | DestructableBrush0-5, 8 (crate, 25/100 HP) -> PerceptionBrush2-8 off, crateopentrigger | broken by hits | click or missile (TriggerByObject) breaks a board (README:137-152) | OK |
| traininghall | DestructableBrush12 death -> TrainingTrigger `Break` (TrainingEnter.scr) -> ExitTrigger0 | key 301, the end door | click or missile; scenario_doors_exits: bar broken, QBit 90301, `mm9_exit_trigger:221` | OK |
| traininghall | DestructableBrush7/9/10/11 (trainingglass, 75 HP) | skylight panes that missiles break | static translucent panes (README:91) | PARTIAL |
| traininghall | resetlever1-4 (Locked, no unlocker) | never open | click says locked | OK |
| traininghall | TriggerLobbyGhouls/GhoulsAttack/ShutDoor -> ghouls Go/Drop, `dragonroom door` Use | | README:110; scenario_scripted | OK |
| traininghall | 32 trigger links to RotatingBrush d2w1-4/d4w1-4 (spin, reverse, off); dummy2door -> TriggerHorseGo | the horses' wheels spin | Horse2's wheels spin while it rides (on + reverse, reverse + on, off on arrival); Horse4's get on and off in one moment in MM9 (2026-11-06 night) | OK |
| traininghall | TriggerOrcTraining/OrcsStop/GossipOn/Off/BoxOrcsOn/Off -> the orcs' idle scripts | idle loops | not built | NOT_NEEDED |
| traininghall | exsound0-3 ambient links | | C10: installed Lua sets `AmbientSound<k>` (4 sites) | OK |
| verhoffinruins | DestructableBrush12 (bolt, 50 HP) death -> PrisonDoor2 `unlock`; damage -> PerceptionBrush0 off | broken by hits | sink mover, event on a **click** (verhoffinruins.lua:79-92); PrisonDoor2's click checks `BoltBroken` | PARTIAL |
| verhoffinruins | Door5 (DoorLock.scr "559 1"); DD10 L/R, TortureChamberDoor6/7, WaterRoomButton1 (Locked, no unlocker) | | handler 207 with item 559; handler 200 `locked` | OK |
| verhoffinruins | TortureChamberDoor0/1 open -> DoorShooter0/1 on/off; pentagram triggers | | verhoffinruins.lua:166-200 | OK |
| verhoffinruins | WaterNozzle0-3 open -> waterfill, PerceptionLightOff; TriggerWaterLock/Unlock -> nozzles lock/unlock, DD5 | the water trap | handlers 210-214 (`"WaterNozzle" .. k`, missed by doors.py); scenario_scripted, scenario_swim | OK |
| verhoffinruins | SawBladeTrigger1 -> saw damage trigger 1/2 -> saw damage (DamageBrush), AI barrier; SawBladeArm1 close -> TriggerTimer1; PaddleTrigger -> Paddle/SwingPaddle | traps | Lua saw and paddle (README:104-105) | OK |
| verhoffinruins | BustTrigger0/1 -> BustZombie0/BustWraith0 ForceFall; BustWraith0-3 damage -> BreakOutDust0 On | the bust monsters appear; dust on hits | events for ForceFall; `DUST_ON_HIT` convert.py:106, 534 **(R2)** | OK |
| verhoffinruins | 16 CloseTrigger links + nozzles to PerceptionLight0-3; the pentagram fires' coloured lights | switched lights | PerceptionLight0-3 out while the trap fills, on again as it drains (2026-11-06 night); the pentagram fires' lights not switched | OK (fires PARTIAL) |
| yanmirsfort | DestructableBrush0-5 (supports, HitPoints 1) death -> Trigger0-5 -> PerceptionBrush2-7 off + YanmirTrap SupportBroken | broken by hits | events 200-205 on a **click** | PARTIAL |
| yanmirsfort | TriggerYanmirTrap (AIOnly) -> Yanmir TimeToDie; TriggerTrapForReal -> YanDStruct0, Planks0, Xbeams0 destroy, GiveKey; SquishTrigger0/1 -> Yanmir Squish | the trap, key 69 or 173 | Yanmir's position polled against the box once armed (README:96); `wakeYanmir()` | OK |
| yanmirsfort | Yanmir0 (DAT CanDamage 0, YanmirBase :Reset CanDamage FALSE) | immune: only the trap kills him | the installed damage hook does not stop the damage: scenario_scripted.yml:66 fails (850 of 945 HP after 5 attacks). B3 writes `mm9_can_receive_damage: false` for CanDamage 0 **(R2)**. Killing him meanwhile still gives the key (:OnDeath kept) | PARTIAL |
| yanmirsfort | Trigger6-10 -> Spawner0/1/2/4/6 `default`; nine Yetis' DeathTriggerTarget -> Spawner0/2/3/4/5; IceLobbercicles' death -> Respawn0-3 RespawnMe | spawns and respawns | `SPAWNERS`, `DEATH_SPAWN`, `BUG_RESPAWN` (yanmirsfort.lua:157-200); scenario_scripted's spawn steps pass | OK |
| yanmirsfort | Yanmir'sKey -> DoorTeleportLeft/Right, RotatingDoor61-67 unlock; Secretdoor open -> lock | | events 211-226; the secret door opens for good | OK |
| yanmirsfort | YanDstruct0/FallingFloor0 death -> CaveInDust0/4 On; Planks0 -> AITrk234 off; PlayerRanAway/0 -> Yanmir | dust; his patrol path | not built (README:108-111) | NOT_NEEDED |
| yanmirsfort | EndOfWorldTrigger -> PlayerExit | to Frosgard City | `evt.MoveToMap` (README:97) | OK |

#### Gaps

No P1 gap in this group: every door, lock, exit and quest chain is reachable in the installed maps (26 of 27 project
scenarios pass; the failing one is Yanmir's immunity, below).

- P2 — thjoradmine, verhoffinruins, yanmirsfort: MM9's breakables that need weapon hits are broken **by a click only**
  (they are sink/slide movers with a click event). Shooting or hitting them does nothing, which is the same symptom as
  the user's drawbridge report: Thjorad Mine db12-db23 (key 36, Ebora), CaveWall0-4, BustOutBrush0-2, DestructableBrush0
  (the stalactite), TorchHolder0/1, the MineCarA cart and the falling torches (OnDamage/Hit); Verhoffin's bolt
  DestructableBrush12; Yanmir's six supports. Fix: MISSING_DATA. Build them as static cog faces plus scene
  `destructibles` (hp, damage_enabled from the DAT, `destroyed_event` = the existing handler's event, and
  `damaged_event` for the cart and torches, whose MM9 trigger is OnDamage) instead of movers, keeping the click handler
  as an extra route. dungeon/destructibles.py skips any brush a map turns into a mover, so each map's `models` rules must
  change. FINAL_REBUILD_WORK C8 lists this as "click breakables".
- P2 — thjoradmine: the torch chains never destroy the exploding barrels (TM_TorchFlame.scr :StartSequence/:Barrel1-8
  destroy DB_Barrel0-8; TM_FirstFallingFlame DB_Barrel9). The Lua hides DB_Barrel2-8 and 9 with `SetSprite`, so no
  ExplodeDamage reaches the party, and DB_Barrel0/1 are never touched. Fix: MISSING_DATA. convert.py's timers 203/204
  should call `evt.DestroyDestructible(665, 666, 667, 664 ... 658)` in MM9's order (and 659), which fires the shared
  `explode()` handlers, instead of `sprite(..., false)`.
- P2 — yanmirsfort: Yanmir takes damage today (scenario_scripted.yml:66). B3 fixes it at R2: re-run the scenario after
  the rebuild.
- P2 — thjoradmine, yanmirsfort, verhoffinruins, templeofhonk: converter-only items that the installed maps still lack:
  the `ebora_free` and `yanmir_death` cinematics, Thjorad's ambient quake and DB quakes, Verhoffin's bust dust (B8) and
  the Temple's geese (M19). Check each after R2 (cinematic_*.yml, quakes_shake.yml).
- P3 — traininghall: skylight panes DestructableBrush7/9/10/11 (75 HP) do not break. Fix: MISSING_DATA, the glass
  destructible route (`glass_cog_overrides`).
- P3 — thearena: the crowd's CrowdCheer0-9/CrowdBoo0-9 are placed `start_on: false` and never switched; the Lua plays
  one 2D cheer. Fix: MISSING_DATA. Set `AmbientSound103..122` to 1 where the Lua cheers or boos (the E4 switch).
- P3 — thjoradmine (PerceptionLight0-9), verhoffinruins (PerceptionLight0-3, the pentagram's coloured lights): switched
  point lights. Fix: MISSING_ENGINE (runtime light on/off).
- P3 — traininghall: the horses' wheels (RotatingBrush, 32 links) do not spin. Fix: MISSING_ENGINE (continuous
  spinners, GAPS section 4).
- P3 — cosmetic, not carried: the geese's random running, the training orcs' and Trellborgs' idle loops, Yanmir's patrol
  and bug hunt, dust Fire objects (CaveInDust, BreakOutDust1), the steam jet, the mine cart and torches moving
  (swapped or dropped out of sight).

COUNTS scripts: OK=25 PARTIAL=8 MISSING_DATA=0 MISSING_ENGINE=0 NOT_NEEDED=9
COUNTS wiring: OK=23 PARTIAL=8 MISSING_DATA=0 MISSING_ENGINE=3 NOT_NEEDED=4

### Cities, Lindisfarne Monastery, Wizard's Lab (arslegardcity, greatgate, drangheimcity, frosgardcity, guberlandcity, sturmfordcity, thjorgardcity, thronheimcity, lindisfarnemonastery, wizardslab)

State checked: the installed `assets_dev/worlds/mm9/events/maps/<stem>.lua` / `maps/<stem>.scene.yml` (12:12, before
the cinematics, M23 and the other 2026-11-06 converter work) and the converters (`level_generation/projects/mm9r_<stem>/
citylua.py`, `convert.py`, `overrides.yml`), which R2 emits. Arslegard City is already reconverted in the review root
(`output/mm9_rework/assets_dev/.../arslegardcity.lua` 16:38, with `arslegardcity.cinematics.yml`): its cinematic
wiring is confirmed there. "R2" = takes effect at the running final rebuild. Great Gate is never rebuilt (no
transition names it, MM9_CUTSCENES.md section 2): its FateMan/LoseMan/Hanndl/LoseCam copies are carried by Arslegard
City's (gate scenes) and by world.yml `partyDeath` (death to arslegardcity.blv + the `MM9LoseGame` movie, E6).

#### Scripts

| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| fateman.scr | arslegardcity (Fateman, Fateman0), greatgate | `:OnLose` (also `wait 1 .1 OnLose` at start, `:Main` 458) without key 98: key 98, LoseCam4/2/3 shots, peephole Door0 `use` (`:Scene4` 81-82, `:Close` 100), Hanndl Speak9-15 with the party's lines, `:ExitIN` 121-123: `trigger ExitTrigger2`, 46 000 xp | cinematic `gate_fate` (gate_cinematics.py; citylua.py 285 `MM9Cinematic.start`), steps: key 98, Door0 open/shut, xp (capped), ExitTrigger2's move; review-root Lua 104-111 + cinematics.yml | OK (R2) |
| hanndl.scr | arslegardcity (Hanndl), greatgate | Hanndl's speech animations/voices `:OnSpeak9-17`, `:OnVoice9-17`, `Done`/`Close` callbacks to the directors; no keys | the cinematics' actor clips and voice cues (README "Cinematics": Sc4Hanndl09-15, Sc5Hanndl16/17 at their Speak keys) | OK (R2) |
| losecam1/2/3.scr | arslegardcity (Losecam1-5, CameraMarker0/2), greatgate | `Play`: MoveToPos to its marker, on arrival `trigger <director> Cam2/Cam3` | the cinematics' shots (camera_gate moved Losecam3 48 back) | OK (R2) |
| loseman.scr | arslegardcity (Loseman), greatgate | on the engine's `Lose` (party death; `:Main` 113): LoseCam1-3, peephole (63-64, 83-84), Hanndl's "You again" (Speak1), fade; leaves the party in Arslegard | death flow = world.yml `partyDeath` (arslegardcity.blv, MM9LoseGame movie); the arrival poll then runs FateMan as MM9 (first death without 98). Hanndl's "turned away" scene (Hanndl07/08) not carried (README 167) | PARTIAL (P3) |
| njamchase.scr | arslegardcity (NjamtheMeddler0; Trigger0 "Chase") | `:OnChase` with 108, not 470: `Njamdoor` Unlock, key 470, 226 000 xp; `OnDamage Chase`; `:Init` removes him with 470 | Lua `njamChase` (handlers 240 pad, 241 damage hook), door 232 opens with 470, load removes actor 34 | OK |
| writman.scr | arslegardcity (Writman) | with key 100, not 9515: the writ scene, `RotatingDoor0/1` Unlock + use, Hanndl removed, 170 000 xp | cinematic `gate_writ` (citylua.py 293), gate door 233 opens with 9515 (installed and review root 53-55) | OK (R2) |
| arg_bjarni/forad/kira/markel/sigmund/sven/tryygva.scr (7) | thronheimcity (the council actors and Sven prop on MM9's stage under the city) | the war council's actors: Sc2_* animations, voice lines, `Done` callbacks to Argueman (scr_spec.md "ARG_KIRA ..." 106); no keys/items in any of them | the cinematic `council_argument` (council.py, citylua.py 184): actors moved into Kira's hall, hidden; :War keys 184, 40, 85, 93, 26 500 xp at :Cam3; installed (pre-cinematic) gives the same keys on KiraDoor1/2's click (handlers[232] -> war()) | OK (R2; installed: keys only) |
| arg_unhide.scr | thronheimcity (ScriptObject 213) | council props Visible with 90+91 until 94; Markel's prop gone after 40 | citylua load handler (README "ARG_Unhide") | OK |
| arg_yrsa.scr | thronheimcity (YrsatheTroll0, RUDE 1) | appears 7 s after :End2 with FX/teleport sound; RUDE 1 | click gives 93 + RUDE 1, exit 185 and she vanishes (installed 89-95) | OK |
| arguecam1.scr, arguetreaty.scr | thronheimcity (Camera0; Prop7/9/16) | camera move to CameraMarker0 at 40 -> Done; treaty prop MoveToPos/anim | cinematic shots and decoration cues | OK (R2) |
| kirashield.scr | thronheimcity (Shield) | 214 without 216: key 216, item 375; prop removed | citylua (README "KiraShield") | OK |
| thronheimcity_badass.scr | thronheimcity (BadAss; BadAssTrigger/0 "Breakout"; GuardSpawn0/1) | `:OnBreakOut` once: walk to BadAssWander1, break PrisonWall (hp 2000), Shmoe killed, guards spawn while he lives | installed: minimal (wall mover, hostile, Shmoe); R2 (M23): PrisonWall a scene destructible, `evt.MoveActorTo`/`KillMapActor`, guard respawns capped 12 (citylua.py, 5 MoveActorTo) | OK (R2) |
| battleman.scr | frosgardcity (BattleMan; Trigger0 "Fight2") | `:Init` with 104, not 377: Forad/Tamur appear, Horde at Atlimarker/BadGuys, soldiers at GoodGuys; Fight2 a second wave | Lua `battle()`, `summon`, `clansAgainstHorde` (installed 226-258), the Trigger0 pad | OK |
| breakice.scr | frosgardcity (BreakIce "39 72 5000"; the 35 DestructOn floes; Shooter1-4) | after the barrel's death: cinema, floes `DamageOn`+`destroy` in waves, `:GivePoints` 72 or 174 + 8 000 xp; `:Init` with 72 all gone | installed: five waves on the 1 s poll, floes slide under the sea (movers), keys/xp; R2: cinematic `break_ice` (citylua.py 218) | OK (R2 adds the camera) |
| icecam1.scr | frosgardcity (Camera0) | the BreakIce camera move | `break_ice` shots (Camera1 shifted 400 units, Camera2 override) | OK (R2) |
| frosgardshooter.scr | frosgardcity (Shooter0 "Shoot"; Shooter5 "Test 1") | Shoot: eight FireBolts at Shoot0-5; Test: the powder seller's test cannon (DestructableProp1's death, Shooter6 nightly 22-04 via NPC215) | Shoot carried (M10: citylua T_CANNON, installed 98-117); Test and Shooter6 not carried (installed 119-121) | PARTIAL (P3) |
| changemodel.scr | frosgardcity (Prop0 "268 Maypole") | with 268 the new maypole model | cogs 401/402 by key 268 | OK |
| pledge.scr (+ PLEDGE.inc via NPC190/191/193/195/196/197/199) | frosgardcity (217, 218 and the NPC19x townsfolk) | `:OnRude` -> PLEDGE.inc `:Pledge`/`:CheckAllNPC`/`:reward`: with 265 and at most one of the eight pledges 269-276 missing: **key 277**, 5 000 xp, quest sound | **not carried** (README 176, installed 175-176 "Pledge.inc's pledges are left out"); the pledges 269-276 come from RUDE natively; no Lua anywhere gives 277 (grep of events/ and converters). Key 277 is required by the Green Man's "We have completed your tasks" row (dialogue/rude/NPC221.rude: needs 268, 277, 278 -> 279), and 279 is the Druid promotion (mm9r_frosgard_blv/regionlua.py NPC221 :Promo, key 280, 63 000 xp) | MISSING_DATA (P1) |
| greatbookkey.scr | thjorgardcity (BookKey) | shown only after an `appear` message (gives 375); use with item 243: items 560, 244, 347, key 374 | carried as MM9 (installed 207-217, cog 400 by 375/374); no MM9 object or script sends `appear` (grep of SCRIPTS: only GreatBookKey itself) | OK (faithful: unreachable in MM9 too) |
| orbtrigger.scr | thjorgardcity (Barrel) | use: `trigger Orb Placed`; no object named Orb in the DAT | not built | NOT_NEEDED (target missing in MM9) |
| lindisfarnebell.scr, lindisfarnebellcontroller.scr | lindisfarnemonastery (Bell1-5, Rope1-5 OpenTrigger0 `use`, BellControl) | rope or bell use rings (`OnDamage OnUse` too); the order Bell1..5 -> `:Finish`: 2 000 xp, key 9507, Thjorad `TurnOn`, ThjoradMonk1-4 `GoToPray`, the peal | ropes (handlers 91-95 press+ring), bells, order and Finish, peal (installed 119-158) | OK |
| thjorad.scr | lindisfarnemonastery (thjorad) | on (TurnOn: bells or hostility): with 2 not 31 key 31, else 162; item 197, 1 000 xp, removed; `:Init` | installed 99-100, 256 (load) | OK |
| thjoradmonk.scr | lindisfarnemonastery (ThjoradMonk1-4) | RUDE until `GoToPray` (walk to their marker); `OnDamage` turns Thjorad on | dialogues gated by AtPrayer, set at their markers (no walk), hostility hook | OK (walk cosmetic) |
| relic.scr | wizardslab (barrel, idx 877) | use: with 338 not 340 item 368 + 340, else 339; removed | citylua (README 131; prop `barrel_877`) | OK |
| teleportermulti.scr, teleporterswitch.scr | wizardslab (TeleporterAt* x6; 30 crystals) | crystal sets the station's destination; touch sends the party | 4 Hz poll + crystal clicks (README 120-121; scenario_teleporters.yml) | OK |
| wizardeffect.scr, wizardmaster.scr | wizardslab (ShooterSummon0-6; SummoningGuy3) | the apprentices' beams; the master's summon, banishing at six deaths | README 124-125 (M10 beams) | OK |
| wizardlabcamera.scr | wizardslab (CameraSummon) | the summoning camera at DestinationPurple | cinematic `summoning` (citylua.py 450) | OK (R2) |
| townportal.scr | drangheimcity, frosgardcity, guberlandcity, sturmfordcity, thjorgardcity, thronheimcity (TownPortal0) | use: key 5011-5016 (the city's Town Portal destination) + the clean skin | each city gives its key on a click (installed: one `giveKey(501x)` each); the skin swap not carried; **no Town Portal destination reads the keys**: engine `town_portal_switch.txt` has a `TPChedian4` entry (uncommitted working-tree edit) but no Chedian sub-table with the six cities gated by QBits 95011-95016 | PARTIAL (P2) |

COUNTS scripts: OK=35 PARTIAL=3 MISSING_DATA=1 MISSING_ENGINE=0 NOT_NEEDED=1

#### Wiring and objects without a script

Sources: links.json, doors.json (refs re-checked by hand: doors.py counts the `DOORS = {["name"] = ..}` line as a
reference, so maps with quoted door keys showed false "other refs"), the installed Lua and scenes.

| Map | Chain or object | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- | --- |
| arslegardcity | Fateman/Loseman -> Door0 `use` (peephole) | opened and shut by the gate scenes | cinematic steps (gate_fate 14.1/69.2 s, gate_writ 13.7/18.9 s); Door0 has no click, as MM9 | OK (R2) |
| arslegardcity | Fateman -> ExitTrigger2 `trigger` (out of reach) | the scene's end moves the party to the Dark Passageway | `gate_fate` final step = ExitTrigger2's move | OK (R2) |
| arslegardcity | NjamDoor0/1 (DoorLock.scr 576), Njamdoor (Unlock by NjamChase), RotatingDoor0/1 Great Gate (Unlock by WritMan, `Lock` self close-trigger) | keyed / unlocked by script | handlers 231 (item 576), 232 (key 470), 233 (key 9515); locked click says so | OK |
| arslegardcity | NjamBackDoor0, ClankDoor1/2 (Locked, no unlocker) | never open | locked click (installed 40) | OK |
| arslegardcity | CounterDoor (library counter flap: RotatingDoor, Locked 0, PushOpen, Sticky) | the party pushes it open | `rotate` mover without `doorway` -> no click event (overrides.yml 98; scene surface has none) | MISSING_DATA (P3) |
| arslegardcity | ExitTrigger3 chasm catch (row 638) | a fall lands in Thjorgard | `add_catch_row` (README 144-150) | OK |
| frosgardcity | DestructableProp0 death -> Shooter0 `Start` -> BreakIce | the powder barrel broken by any damage fires the cannon and the ice cinema | installed: a click on the barrel; R2: `barrel_death_lua` binds its destroyed event 30607 to the same handler (citylua.py 588-605). Props break by melee/Lua only, not missiles (INDOOR_DESTRUCTIBLES "Not yet") | OK (R2) |
| frosgardcity | DestructableProp1 death -> Shooter5 `Start` (test shot); 215 -> Shooter6 On/Off (night test); Shooter5/0 -> Shooter7 `on` | cosmetic cannon tests | DestructableProp1 explodes (shared event 30045); the shots not carried | PARTIAL (P3) |
| frosgardcity | 35 DestructOn.scr floes (DestructableBrush14-45, 6-9: CanDamage 0, Exploding) | made damageable and destroyed by BreakIce's waves | not scene destructibles: movers sliding 120 LT under the sea in the waves (installed 75-97, `iceGone` on load with 72) | OK |
| frosgardcity | Bankdoor `open` -> Banker `bank` | the hatch opens the banker's dialogue | handler 231 + banker events 53553/50553 | OK |
| frosgardcity | Trigger0 -> BattleMan `Fight2` | second wave | pad in `battle` | OK |
| frosgardcity | Door0-23 facade doors (Locked, no unlocker), Bankwindow (MoveDist 0) | never move | locked click / static | OK |
| guberlandcity | Gate1-8trigger -> Gate<n>L `toggle` (+ `off` self, Gate<n>L close -> trigger `on`) | the quarter gates open as the party walks up | 0.25 s poll `gates()` (installed 76-93) + click | OK |
| guberlandcity | Trigger0/1 -> blacksmith_sounds, Bell TriggerOn/Off0-3 -> BellRing, OceanTrigger0/1 -> Ocean0-4 (AmbientSound on/off) | ambient switching | shared ambient triggers (overrides `ambient_triggers: true`, poll event 903, `AmbientSound<key>` map vars) | OK |
| guberlandcity | RotatingDoor3 (sickroom; `unlock`/`Open` from NPC142 and the shopkeeper's scripts) | unlocked by the apothecary quest | handler 231 + exit 50871 | OK |
| sturmfordcity | Jaildoor (Hatlati's `close`/`lock`; self `Lock`) | Hatlati locked in / let out | `jailHatlati`, handler 231, exit 51323 | OK |
| sturmfordcity | 11 temple windows WorldObject1/2/37-45 (DestructableBrush, hp 0) DeathTrigger -> Healer (Beathag.scr) `break` | breaking one gives key 5002; Beathag's RUDE exit then charges 700 gold | the windows are scene destructibles now (hp 1, no destroyed_event); Beathag's payment branch carried (installed 111-116) but nothing gives 5002 | MISSING_DATA (P3) |
| sturmfordcity | Trigger1/2 -> RUDEProp0/RudeProp1 `blabber` (TryggvaSpeech, ErccSpeech) | voiced barks | citylua barks: once each, Tryggva one of Tryygva01-04, Ercc ercc01 then ercc02 with key 113 (2026-11-06 night) | OK |
| sturmfordcity | Hatlati5 (Marker) `GoHome` -> Hatlati | NPC walk home | not carried (no walking NPCs) | PARTIAL (P3; NPC fork) |
| sturmfordcity | 44 locked facade doors, vaultdoor, RotatingDoor16/18 (Locked, no unlocker); RotatingDoor33 (RotationAngles 0) | never open | locked click; RotatingDoor33 static (overrides.yml 138) | OK |
| thjorgardcity | BembgateL/R (University garden gate: RotatingDoor, Locked 0) | the party opens it | `rotate` without `doorway` (overrides.yml 159-160) -> no click; headless walk (scratch g3_bembgate*.yml): blocked both ways at the gate, both sides reachable around it | MISSING_DATA (P3) |
| thjorgardcity | BembStudy3 | an object with no world model in the DAT | nothing to build | NOT_NEEDED |
| thronheimcity | **Secretdoor0** (secret door to the room under the loft: RotatingDoor, Locked 0, PushOpen, Sticky, no script, no sender) | the party pushes it open; behind it Ladder2 climbs to the loft and TreasureChest0 | `rotate` mover (overrides.yml 97) without `doorway` -> mover event 0, no click (work/doors.json door 30/31); headless (scratch g3_secret*.yml): from Ladder2's foot the party is stopped 338 units north at the door, east/west walls at 147, south is only the ladder: the room is closed off, so the loft chest is unreachable (scenario_chests.yml starts the party inside the room) | MISSING_DATA (P1) |
| thronheimcity | KiraDoor2 `open` -> Argueman `start` | the council | handler 232 -> war() / R2 cinematic | OK |
| thronheimcity | BadAssTrigger/0 -> BadAss `Breakout`; BadAss/Guard1/2 -> GuardSpawn0/1 `Default` (Spawner) | the breakout and guard waves | plane poll; R2 MoveActorTo + spawned guards (M23) | OK (R2) |
| thronheimcity | 13 locked groups (Door1-4, safe, guard house, inn 2, cells, vault) | never open | locked click (README 120) | OK |
| thronheimcity | Clear / Foggy WeatherMan (StartOn 0) | MM9's weather presets | not carried (README 101) | see generic WeatherMan (parent) |
| lindisfarnemonastery | Rope1-5 `open` -> Bell<n> `use`; 25 organ key Doors (MoveDist 2) | rope/bell/organ notes | handlers 91-95, 130-154 (`press`, notes; renamed Organ<k> movers, so doors.json listed the DAT names as static) | OK |
| wizardslab | EvilGrandSorcerer1 death -> `super eye trigger` (GlowingLight0 off, force field `super eye door` open, DoubleDoorL25/R18 close+lock all four) ; Oculus0 death -> `super eye trigger0` (unlock) | the sorcerer's death seals the hall until the super eye dies | installed 63-85 (handlers 201/202 locked until OculusDead); force field opens | OK |
| wizardslab | Switch15-28 -> Cell15-28 open/toggle (+ AITrack on/off) | cell levers | handlers 210-223; AI rails not carried (cosmetic) | OK |
| wizardslab | TriggerNotify0-2 -> SummoningGuy0 `start`, TriggerSwitchTo1-3 | the summoning chain | the cinematic / summoning Lua (README 123-125) | OK |
| wizardslab | Closet1Door1 open/close -> PerceptionBrush0 off/on | the closet's trap hint | not carried (FINAL_REBUILD_WORK log 2026-11-05) | PARTIAL (P3) |
| wizardslab | DoubleDoorL10/R10 (Lift, Locked, no unlocker); DresserDoorL1/R1 | never open; dresser doors' pivot 6 500 LT away | locked click (installed 60); static (README 75-77) | OK |
| wizardslab | QuakeSummon (EarthQuake, StartOn 0) | nothing sends it | not built | NOT_NEEDED |
| all | Wells, Clovers, Cauldrons, Cookpots, HidingPlaces, PropDamager Spikes2 (frosgardcity), Fires, WeatherMan, Ladders | class behaviour without script | see the parent's generic classes; ladders present in every map that has Ladder objects (arslegard 2, drangheim 3, sturmford 6, thronheim 2, lindisfarne 7) | — |

COUNTS wiring: OK=23 PARTIAL=4 MISSING_DATA=4 MISSING_ENGINE=0 NOT_NEEDED=2 (plus 2 rows deferred to the generic classes)

#### Gaps

- P1 — frosgardcity (and frosgard): Pledge.inc's reward is not carried, so key 277 is never given; the Green Man's
  final row (NPC221.rude "We have completed your tasks": needs 268, 277, 278 -> 279) never shows, and 279 is the
  Druid promotion (frosgard regionlua NPC221 :Promo: key 280, 63 000 xp). Fix: MISSING_DATA: mm9r_frosgardcity/
  citylua.py RUDE-exit handlers (50000 + object) for the pledge NPCs (NPC190/191/193/195/196/197/199 objects and
  217/218 Pledge.scr): with key 265, without 277, and at most one of 269-276 missing (PLEDGE.inc `:CheckAllNPC`):
  `MM9.giveKey(277)`, 5 000 xp through quest_xp.py, quest sound.
- P1 — thronheimcity: Secretdoor0 (the secret door into the room under the loft) has no click event, so Ladder2 and
  the loft's TreasureChest0 are unreachable (headless walk). Fix: MISSING_DATA: overrides.yml `Secretdoor0: {group:
  Secretdoor0, motion: rotate, doorway: true}` (any rule that gives the group a click event), reconvert.
- P2 — six cities: Town Portal to the MM9 cities: TownPortal.scr keys 95011-95016 are given, but no Town Portal
  destination uses them (town_portal_switch.txt has only a `TPChedian4` entry in the working tree, no Chedian table).
  Fix: MISSING_DATA: a Chedian sub-table (six rows: each city's `TownPortal` StartPoint in the BLV frame, QBit
  95011-95016), plus the icons; no converter change.
- P3 — thjorgardcity BembgateL/R, arslegardcity CounterDoor: unlocked MM9 rotating doors built as movers without a
  click (not doorways); nothing is cut off (gate: reachable around). Fix: MISSING_DATA: shared rule in
  dungeon/movers.py: a mover whose DAT door is not Locked, has no sender and no map event gets the click event even
  without `doorway` (would also cover Secretdoor0), or per-map `doorway: true`.
- P3 — sturmfordcity: the 11 breakable temple windows (DeathTriggerTarget Healer `break`) give no key 5002, so Beathag
  never charges for them. Fix: MISSING_DATA: Sturmford City hooks `destructible_events` -> a destroyed event that
  gives 5002 (generic: translate a destructible's DeathTrigger to an actor whose script `AddTrigger`s that message).
- P3 — arslegardcity: LoseMan's "You again" scene on later deaths (Hanndl07/08, LoseCam1-3) not carried; the
  MM9LoseGame movie stands in. Fix: MISSING_DATA: a third gate cinematic in gate_cinematics.py started by the
  partyDeath arrival when key 98 is held.
- P3 — frosgardcity: the cannon test shots (Shooter5 by DestructableProp1, Shooter6 at night) not carried. Fix:
  MISSING_DATA: citylua FireBolts as T_CANNON.
- P3 — sturmfordcity Tryggva/Ercc barks (Trigger1/2 `blabber`), wizardslab Closet1Door1's PerceptionBrush0 on/off,
  frosgardcity TownPortal clean skin. Fix: MISSING_DATA (voice on a touch pad; hint on/off in the door handler; cog swap).
- Note (outside G3 scripts): R2 is what makes the cinematics (gate_fate, gate_writ, council_argument, break_ice,
  summoning), the full Thronheim breakout (M23) and Frosgard's barrel death live; the installed 12:12 maps still run
  the pre-cinematic Lua.

### Regions: afterworld, bootcamp, drangheim, frosgard, guberland, isleofashes, lindisfarne, mountainpass, sturmford, thjorgard, thronheim, yorwick

Evidence base: installed `assets_dev/worlds/mm9/events/maps/<stem>.lua` and `maps/<stem>.scene.yml` (promoted 2026-11-06
12:12), the region projects `level_generation/projects/mm9r_<stem>_blv/` (regionlua.py, overrides.yml, work/scr_spec.md),
`mm9r_isleofashes/story.py` + `story.lua`, shared `mm9r_common/outdoor_blv.py` (`map_script`: doors with
`all_doors_click`, `KEYED_DOORS`, `BARRED_DOORS`, `locked_models`, ForadWorld, stat stones). "R2" = written by the
converter, not yet in the installed map (takes effect at the final rebuild now running): every cinematic (no
`*.cinematics.yml` is in assets_dev yet; they are in `output/mm9_rework/cinematics_pilot_root`), C10 ambient triggers,
M19/M22 placements, B5/B8 jumpers. The scr_spec.md files of Guberland, Thjorgard and Sturmford predate M1, C3, C6 and
the BLV destructibles in places ("skipped: destructible brushes"); the installed Lua is newer.

Headless checks (scenario files in the scratch folder, all against assets_dev):
- `sc_drawbridge.yml` (parent) and `sc_g4_chain_ground.yml`: from the courtyard floor (Abandonedfortfront, z 1152) two
  event Fire Bolts aimed at DestructableBrush0/1 (z 2043) break both chains and open the drawbridge (mechanism 11).
- `sc_g4_chain_arrow.yml`: a new party (Archer, Hunting Bow equipped), posed at the same spot and pitched at the chain,
  `press_action: attack` looses an arrow (`projectiles: {source: party, min_count: 1}` passes) and it breaks chain 315.
- `sc_g4_yorwick_gate.yml`: Yorwick gateboard (15 HP) broken -> CTgate (mechanism 1) opens; Thjorgard's training-hall
  wall DestructableBrush7 broken -> key 301 (TrainingEnter reward, handler 370).

**Sturmford drawbridge, why "nothing happens"**: the chain wiring works end to end in the installed map. The visible
chains outside the gate are `Drawbridgechain` (x 13793-14500, z 1782-2079, from the raised bridge into the wall):
MM9 gives it `CanDamage 0`; DestructOn.scr only enables and destroys it after ak_disable.scr :OnDraw counts both inner
chains, so shooting it does nothing, in MM9 as here (scene `damage_enabled: false`). The chains that break are
DestructableBrush0/1: two horizontal chains 10 LT thick at z 2038-2048 running from x 14868 to 16200, i.e. *behind* the
gate wall, over the inner courtyard (marked by the red hints Drawchainperc/Portchainperc, PerceptionValue 5). They are
reached from inside (the Anskram Keep exits Anskramkeepback/Abandonedfortfront; see shared: transitions frame for where those exits fire today), not from in front of the drawbridge.
Two other ways a real shot can miss although the data is right: (a) the party's ranged attack with no actor under the
crosshair takes `chooseFallbackRangedTarget` (game/gameplay/GameplayActionController.cpp:596, nearest visible hostile
within 5 120) before the crosshair ray, so a visible monster (the basilisks 3 000-5 000 east) steals the arrow;
(b) a game binary or assets from before 2026-11-06 12:12 (the ODM import had no BLV destructibles).

#### Scripts
| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| ak_disable.scr | sturmford (defense 203) | :OnDraw counts two "Drawbridge" (chain deaths) -> DamageOn+destroy Drawbridgechain, open drawbridge, bDrawbridge; :ONPortcullis (Portcullis OpenTrigger0 "Portcullis"); :Award both -> key 47 (on quest 44) else 372, 10 000 xp; :Init with 47/372 -> :Setup (all down/open; "Portaclis" misspelt) | sturmford_blv/regionlua.py `extend`, BARRED_DOORS; sturmford.lua 46-55 (360 barred), 77-93 (regionLoad, defencesAward, barredOpened), portcullis wrap 104; verified headless (3 scenarios) | OK |
| afterworldcam1.scr | afterworld (Camera9) | AfterMarker0 at 100, then Skraelos "Done" (Guilt) | afterworld_blv/regionlua.py cutscenes.Scene `afterworld_guilt` (C11); installed Lua does the key part (50094 :Guilt) | OK (R2) |
| battlecam1.scr | afterworld (Camera0-8), yorwick (Camera0-8) | cameras MoveToPos marker at speed, then "Done" to Sven | yorwick_blv/regionlua.py `battlefield_sven` (C11, key 97 + 114 000 xp at Sven04); Afterworld's copies belong to the SixFires/SvenShowTake tableau (same cinematic family) | OK (R2) |
| atliwagon.scr | guberland (Cart 89) | Init: gone at 127; @3:30 bandits at SpawnMarker (BanditAttack.scr run to Atlimarker0); @6:00 Atli `summon` (walks to the dock) | guberland.lua 79-112: poll 600 gives 126 at 6:00, summons 3+3 bandits once, ship hidden on 127; the bandits' run to Atlimarker0 carried 2026-11-06 (evt.MoveActorTo, stopped on sight); Atli's walk not carried | PARTIAL |
| bc_manager.scr | bootcamp (BC_Manager 543) | museum: Switch0 "fight" (sorcerer vs oculus), Switch1 "open" (monk opens three chests, trap kills him) | bootcamp_blv/regionlua.py `museum_lines` (M22: SummonMonstersById, SetMonsterRelation, MoveActorTo, KillMapActor); not in installed bootcamp.lua | OK (R2) |
| bc_treasurechest.scr | bootcamp (TreasureChest0-4) | "open": lid anim; param 1 trap: column of fire, kill opener | M22 (trap and kill carried); the lid animations not carried | PARTIAL |
| bellweight.scr + dingthebell.scr | guberland, thjorgard (Riser1, Strikeplate1) | bell game: ticket, ding/timing, Riser1 rises 360 x height, ring -> win | guberland.lua 173-202 (timer 601), thjorgard.lua 307-334 (timer 301) | OK |
| boatjudge.scr | thjorgard (BoatJudge 669) | key 7003 on use; exit with 7004 + ticket: countdown, race | thjorgard.lua 254-306 (53669, 50669) | OK |
| racingboat.scr | thjorgard (RacingBoat0-3) | boats move a tenth per hit (OnDamage: shot from the bank); rivals at random speed; submerge and return | rules only: a click on RacingBoat0 (event 645) is the hit; boats static; reach of the click from the bank unverified (scr_spec "Unsure") | PARTIAL |
| dolly.scr, herbs.scr, plow.scr | drangheim (Dolly, Herbs, Plow) | promotion props (key 128): give items 370-372, keys 130-132 | drangheim.lua regionLoad SetSprite 400-402, handlers 330-332 | OK |
| realbook.scr | drangheim (Capstone0) | with item 244: items 347, 560, keys 283, 290, prop gone | drangheim.lua 333 | OK |
| huckstermod.scr | guberland (TicketMaster "1"), thjorgard ("0") | tickets 5 / 40 gold, rule book 594 | guberland.lua 147 (50324), thjorgard.lua 83 (50673) | OK |
| ia_camera2.scr, ia_island.scr, is_boat.scr, isleashesbook.scr | isleofashes (Camera2, Terrain3, Boat, Book) | the book cinema: cameras, pan, islet sinks 1000 (SinkSpeed), boat sails to BoatMarker, FortWall/FortWall0 destroyed, shooters, ExitTrigger1 | mm9r_isleofashes/story.py `cinematics` (`book_sinking`, islet a `dat` mover, `evt.MoveDecoration` boat, C11); installed isleofashes.lua still logs `[MM9Unsupported]` for cameras/islet/boat (1408-1418) while the story effects (keys, walls, shooters, exit) run | OK (R2) |
| isle_islandexplosion.scr | isleofashes (ExplosionEffect0-4) | "explode": five blasts 1-2 s apart, smoke, mist | isleofashes.lua 1348 (story.lua) | OK |
| isle_seamon.scr | isleofashes (SeaMonsterMale0) | BaseSwim wander; pauses beyond 5 000 of the player | swimmer AI (outdoor_blv.py SWIMMER_CLASSES); the far-pause is an optimisation | OK |
| isle_skull.scr | isleofashes (TheBone0/1) | PropLauncher.inc: skulls Jeff throws at the player | not carried (props static) | MISSING_ENGINE |
| isleofashesactor.scr | isleofashes (Mac, Jeff) | Mac taunts and runs to MacRunAwaySpot, his death/sighting sends Jeff GoThrowBones and JK GetPlayer; Jeff throws TheBone props | ordinary monsters (story.py STORY_TRIGGERS comment); no taunt/run/throw | PARTIAL |
| jumper.scr | frosgard (Yeti6-9) | Jumper.inc: wait on the cliff, leap at the party on Trigger0 GetPlayer/WaitGetPlayer | ordinary Yetis (frosgard_blv/regionlua.py:11, M9) | PARTIAL |
| marysheep.scr | yorwick (Ewe0) | Use: the ewe follows the party, tells Mary "Target"; near Mary (512) she sends RuntoMe and gives key 466 (needed for 467/468, 20 000 xp) | not carried; Ewe0 placed only from R2 (M19, row 9272); yorwick_blv/regionlua.py:24-26 "key 466 cannot be earned yet" | MISSING_DATA |
| mastermind.scr | guberland, thjorgard (Mastermind) | runes game; FireCorrect<k> fires light by right stones | both regions' Lua (guberland.lua 203-293, thjorgard.lua 185-253); flames told in the status line (Fire objects named by a script are not placed by C4) | PARTIAL |
| mastermindcolor.scr, mastermindspace.scr | guberland, thjorgard (ColorButton0-4, ColorSpace0-3) | current colour; update + skin swap | clicks 332-340 / 636-644, SetSprite swaps | OK |
| mountainpass.scr | mountainpass (Mountain 120) | Trigger0/1 send Use once each; at two: key 80 (with 79) else 176, 14 000 xp | mountainpass.lua 22-45 (0.5 s poll 600, PASS_TRIGGERS) | OK |
| mp_imp.scr | mountainpass (Imply0) | walk to ImpMarker1; on sighting run to ImpMarker2, `help`, attack | ordinary monster | PARTIAL |
| stonespiece.scr + stonessquare.scr | thjorgard, guberland (Piece0-35, Square0-35) | 6 x 6 stones game vs TronPlayer | Thjorgard: thjorgard.lua 98-184 (clicks 600-635, St0-35); **Guberland: nothing** (guberland_blv/regionlua.py has no stones code; guberland.lua lacks stReset) | PARTIAL |
| thorgard_actor.scr | thjorgard (Ken1-3, MagreebBaby0, Jim, Dean, Walter, Dummy x2, Jumper0-3) | Kens hidden until RobPlayer at night; ambush hidden while 201 without 202, baby within 1 800 -> 202; jumpers leap on JumperTrigger, BuddyDead | thjorgard.lua 417-448 (robberTick, magreebTick, KensOut, MagreebGone); jumpers hidden/shown by `jumperTick` and BuddyDead kill hook (B5/B8, R2); leaps, chase and taunts not carried | PARTIAL |
| yrsa.scr | isleofashes (Yrsa 46) | dialogue hooks, bunker key, leaves with Forad | isleofashes.lua 508, 667 (compiled OnRudeExit/DoRudeUse); M6 | OK |

#### Wiring and objects without a script
| Map | Chain or object | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- | --- |
| sturmford | DestructableBrush0/1 (HP 0, CanDamage 1) death -> Defense "Drawbridge"; damage -> Drawchainperc/Portchainperc "off"; Drawbridgechain (CanDamage 0) death -> drawbridge "toggle" | two broken chains drop the bridge | scene destructibles 315/316 hp 1, destroyed_event 360, damaged 34315/34316 (hints 23202/23201 off); 317 damage off; 360 opens door 11 and calls barredOpened (destroys 317); click says "It is barred." before; verified by event bolts and a party bow shot from the courtyard | OK |
| sturmford | drawbridge open -> drawbridge "lock" | once down it stays down | the barred handler 111 toggles after the chains are gone: a click raises it again | PARTIAL |
| sturmford | Portcullislever (Switch, StartOpen 1) open/close -> Portcullis toggle, DoorChain4 open/close, lever lock; Portcullis open -> Defense "Portcullis", unlocks the lever | the lever raises the portcullis and winds its chain | lever built static (overrides.yml `Portcullislever: static`); a click on the Portcullis (104) toggles it and sets bPortcullis; DoorChain4 has its own click (101) and does not follow | PARTIAL |
| sturmford | Weakwall (HP 100) death -> Weakwallperc off | breakable wall, hint off | destructible 199, 30199 hint off | OK |
| sturmford | SoundTrigger0 -> WerewolfHowl0, ThunderCrash0 on, self off | one-shot ambient sounds | overrides.yml `map: {ambient_triggers: true}` -> dungeon/objects.py `ambient_triggers` (C10); no 903 poll in installed sturmford.lua | OK (R2) |
| sturmford | RotatingDoor7/8 (Locked, no unlocker); Hatch1/2 (DoorLock 596) | never open; open with item 596 | lockedDoor 109/110; keyed 102/103 | OK |
| thjorgard | DestructableBrush7 death -> tomneededatrigger1 -> ExitTrigger3 on, PerceptionBrush6 off; TrainingEnter.scr (ScriptObject1) ExitTrigger0/6 on, reward | the training-hall wall opens the hall's exits | destroyed_event 370: Mm9ExitDisabled486/114 cleared, hint 23056 off, key 301, +5/+5, 20 000 xp; regionLoad gates the exits by 301; verified | OK |
| thjorgard | DestructableBrush8-13 death -> PerceptionBrush5/7-11 off | boards, hints off | 30480-30485 | OK |
| thjorgard | DistantTrigger0 -> WolfHowl0, DayNoise0 on | ambient | C10 ambient_triggers | OK (R2) |
| thjorgard | Jumper0/1 death -> Jumper2/3 BuddyDead; JumperTrigger -> Jumper0-3 GetPlayer/WaitGetPlayer; RobPlayerTrigger -> Ken1-3 | ambush timing | B8 kill hook, B5 jumperTick (R2); robberTick | OK |
| thjorgard | Switch -> Mastermind check; Strikeplate1/Riser1 lock/ring/toggle; Switch0 -> Honky0 start, Honky1-3 reset | the fair games | handlers 103, 102/101/301, 104 + 646-649 (M1) | OK |
| thjorgard | mine cart door left/right (Locked) | never open | lockedDoor 106 | OK |
| guberland | Switch0 (Switch, MoveDist 0) -> Honky0 start, Honky1-3 reset; Honky0-3 geese (in props.json) | whack-a-honky (win key 7113) | `Switch0: static` (overrides.yml:73), no Lua; Thjorgard's M1 code not ported | MISSING_DATA |
| guberland | FireCorrect0-3, thjorgard FireCorrect0-3 (Fire, On 0) | the runes' right-stone flames | not placed; status line | MISSING_DATA |
| yorwick | gateboard (15 HP) death -> CTgate "open" | the boarded gate | BARRED_DOORS -> 360; verified headless | OK |
| yorwick | board0-4 (10 HP, no wiring); drangheim DestructableBrush0 | plain breakables | scene destructibles 18-22, 57 | OK |
| yorwick | Sven -> AmbientSound0-7 off/on, Camera0-8 On/Play/Off | the battlefield cutscene | `battlefield_sven` cinematic, AmbientSound<k> map vars (E4) | OK (R2) |
| yorwick | Ewe0 -> CommonerChildHuman2ChildA0 (Mary) "Target"; Mary -> ewe "RuntoMe" | the sheep quest | see marysheep.scr | MISSING_DATA |
| isleofashes | FortWall0 (TriggerDestroyOnly, Exploding) death -> TriggerEffects -> ExplosionEffect0-4 explode, LichSummoner destroy; Book -> FortWall/FortWall0 destroy, Shooter/Shooter0 on, Terrain3 open/sinkspeed, Boat move, ExitTrigger1 trigger | the book's cinema chain | story.lua 1277-1430 (`on`/`send` message table); shared explode handler 30007/30520 also fires | OK |
| isleofashes | Trigger1/Trigger2 -> BoneThrasher0 / 1-3 RESURRECT, self off; TriggerStarters -> LichSummoner spawn; 12 flyers death -> KillControl OneDown (tm_Hardrock "8 27 200") | ambushes, kill counter | story.lua 1297-1340 (STORY_TRIGGERS, Isle.deathTriggers) | OK |
| isleofashes | Trigger0 -> Peter GetPlayer | wake an ordinary Skeletoid | ordinary AI sees the party | NOT_NEEDED |
| isleofashes | BunkerDoor1/2 (Locked, DoorLock "568 1"), RotatingDoor8 | turret key; Yrsa's hut | story.lua useBunkerDoor (1518-1550) | OK |
| drangheim | Bandit0/1, Burgler0-4 death -> YobboeMan OneDown | key 129 at six | kill hook 601 (M5) | OK |
| drangheim | Door0 (Locked, MoveDist 0); RotatingDoor0 (DoorLock 244) | never / item 244 | lockedDoor 101; keyed 102 | OK |
| afterworld | ForadDarre0 death -> RetributionCounter OneDown; Skraelos -> ExitTrigger0 trigger (:Failure); ExitTrigger1 StartOn 0 + PropTrigger "Skraelos0 Reborn" | Six Fires progression | kill hook 601 (key 387), 50094 :Failure MoveToMap, Mm9ExitDisabled105 until 390, onLeave 600 (keys 391, 102) | OK |
| afterworld | Skraelos -> GuiltFire..RebirthFire "On" (Fire objects, On 0) | each fire lights as its penance is done | not placed (C4 skips script-named fires); only comments in afterworld.lua | MISSING_DATA |
| bootcamp | Trigger0 (dock) -> ExitTrigger0 trigger, CommonerHuman2MaleA0 Leave | the boat out, Grandpa's key 473 | dungeon/tables.py `relayed_exits` (the exit row gets the relay's box); onLeave 600 key 473 | OK |
| bootcamp | Switch0/1 -> BC_Manager fight/open, self close | museum show | M22 (R2); installed: plain door clicks 112/113 | OK (R2) |
| bootcamp | SwitchLever0, Portcullislever, timer lever 03a (-> "axe trap 03": no such object), Button1 | museum exhibits | static, no wiring in this DAT | NOT_NEEDED |
| frosgard | Trigger0 -> Yeti6/9 GetPlayer, Yeti7/8 WaitGetPlayer | the yeti leap | ordinary Yetis | PARTIAL |
| frosgard | Trigger2/3 -> WeatherMan0 on (Fog0: 1-6 500), Trigger1/4 -> off (Fog1: 8 000-15 000) | thick fog in the pass | shared weather triggers (objects.py, event 905): evt.SetFog Fog0 in 1 s, evt.ClearFog in 8 s (2026-11-06 night) | OK |
| mountainpass | Trigger0/1 -> Mountain Use, self off | quest step | poll 600 | OK |
| lindisfarne | BlacksmithDoor1/2, InnDoor1 (Locked, no unlocker) | never open | lockedDoor 101-103 | OK |
| all G4 | 44 ExitTriggers (StartOn 0: afterworld 105, thjorgard 114/486) | exits | every one has a map_transitions.txt row naming a rebuilt BLV start, and the StartOn 0 ones are gated by `Mm9ExitDisabled<idx>`; the volumes' positions are wrong: see shared: transitions frame (rows still in the old ODM frame, no transform.json offset) | PARTIAL (see shared) |
| thronheim | no wiring, no scripts of this category | | | NOT_NEEDED |

#### Gaps
- P1 — yorwick: Mary's sheep (MarySheep.scr, key 466 -> Mary's reward 467/468, 20 000 xp) cannot be done. Fix:
  MISSING_DATA: with Ewe0 placed (M19, R2), its click (53000 + 249, E3) faces/keys the sheep and `evt.MoveActorTo`
  sends it after the party or straight to Mary (CommonerChildHuman2ChildA0), the arrival (or the party with the ewe
  within 512 of Mary, polled) gives 466. A true follower (FollowPlayer.inc) is MISSING_ENGINE. Side quest only.
- P2 — guberland: whack-a-honky (win key 7113) and the stones game (7110) do nothing: Switch0 static, no Lua.
  Fix: MISSING_DATA: port mm9r_thjorgard_blv/regionlua.py's honky (Switch0 as a `rotate` mover, geese SetSprite cogs,
  timers) and stones code (Piece/Square clicks, St0-35) to mm9r_guberland_blv/regionlua.py with Guberland's win keys
  (HucksterMod "1"). Not blocking: any game can be repeated for the six random prizes (Thorir's capstone, key 188).
- P2 — afterworld: the Six Fires never light (GuiltFire..RebirthFire, On 0, switched "On" by SixFires.inc). Fix:
  MISSING_DATA: place script-named Fires hidden with a SetSprite key each (C4's place_fires skips them) and show them in
  regionLoad by the stage keys (381, 383, 491, 387, 492/389, 391) and in each stage handler.
- P2 — thjorgard: the boat race moves nothing and is won by clicking the boat (MM9 shoots it); the click's reach from
  the bank is unverified. Fix: MISSING_DATA: `evt.MoveDecoration` glides per push for RacingBoat0-3 and back on
  submerge; MISSING_ENGINE for the faithful version (party missiles hitting decorations: devdocs/INDOOR_DESTRUCTIBLES.md
  "Not yet").
- P2 — engine, all destructibles: a party ranged attack with no actor under the crosshair aims at the nearest visible
  hostile within 5 120 (GameplayActionController.cpp:596 chooseFallbackRangedTarget) rather than the destructible the
  crosshair is on; with a monster in view the Sturmford chains (and every breakable) are hard to shoot. Fix:
  MISSING_ENGINE: prefer the crosshair's world hit when it is a standing destructible face.
- P3 — sturmford: the Portcullislever does nothing (built static); the portcullis rises on its own click and its chain
  door DoorChain4 moves separately. Fix: MISSING_DATA: Portcullislever as a `rotate`/`nudge` mover whose click toggles
  Portcullis + DoorChain4 (one handler, setting bPortcullis), Portcullis/DoorChain4 click events dropped or routed to it.
- P3 — sturmford: the lowered drawbridge can be raised again by a click (MM9 locks it open). Fix: MISSING_DATA: the
  barred handler opens only (DoorAction.Open), or `BARRED_DOORS` gains a "stays open" flag.
- P3 — guberland, thjorgard: the runes' FireCorrect flames are a status line. Fix: MISSING_DATA (hidden fires with
  SetSprite keys, as the Afterworld fires).
- P3 — frosgard: WeatherMan0 fog switching by Trigger1-4 not carried. Fix: MISSING_ENGINE (a Lua call to set the
  scene fog distances, or per-region fog volumes).
- P3 — guberland: Atli's walk to the dock (the bandits' run to Atlimarker0 fixed 2026-11-06). Fix: MISSING_DATA (`evt.MoveActorTo`,
  M22). Same tool for mountainpass Imply0's walk to ImpMarker1/2.
- P3 — isleofashes, frosgard, thjorgard: AI set pieces (Mac's taunt and run, Jeff's thrown skulls via PropLauncher.inc,
  the leaping yetis and bandits). Fix: MISSING_ENGINE (actor jump/leap, an actor throwing a prop projectile).
- P3 — bootcamp: the museum chests' lid animations (BC_TreasureChest.scr). Fix: MISSING_ENGINE (decoration clip play).

COUNTS scripts: OK=19 PARTIAL=9 MISSING_DATA=1 MISSING_ENGINE=1 NOT_NEEDED=0
COUNTS wiring: OK=26 PARTIAL=4 MISSING_DATA=4 MISSING_ENGINE=1 NOT_NEEDED=3

### Shared scripts (used in more than one map group)

| Script | Maps (objects) | MM9 | Rework (where; evidence) | Status |
| --- | --- | --- | --- | --- |
| DestructOn.scr | Frosgard City 35 brushes, Sturmford Drawbridgechain, Thjorad Mine CaveIn | `:Main` AddTrigger DamageOn -> `:OnDamageOn` SetPropNumber CanDamage TRUE; `OnDamage DestroyMe` (any hit after DamageOn destroys it) | Sturmford: scene destructible 317 `damage_enabled: false`, destroyed by `handlers.barredOpened` (`sturmford.lua:89-92`); Thjorad Mine: CaveIn a mover opened by Trigger7 (`thjoradmine.lua:453-459`); Frosgard City: see the cities section | PARTIAL (per map below) |
| DoorLock.scr | 1000 Terrors StairGate0 (600; take), ToLowerTombGate (599); Arslegard NjamDoor1 (576); Drangheim RotatingDoor0 (244); Isle BunkerDoor1/2 (568); Sturmford Hatch1/2 (596); Verhoffin Door5 (559) | `:OnUse` hasitem nKey -> unlock (and take, relock) | every door: `MM9.hasItem(<key>)` gate in the map Lua (`1000terrors.lua:445,455`, `arslegardcity.lua:45`, `drangheim.lua:32`, `isleofashes.lua:1528`, `sturmford.lua:38,43`, `verhoffinruins.lua:96`); regions through outdoor_blv.py `KEYED_DOORS` | OK |
| GiveTake.scr / BootGive.scr | Afterworld swords 5, Arslegard Prop8, Boot Camp 8 + 6, Dark Passageway Prop38, Guberland Prop1, Lich Lab 11, Verhoffin Prop0, Wizard's Lab Prop26, 1000 Terrors ChessNote0 | `:OnUse` giveitem, removeobject (nGiveOnce: only without the item; `:Init` removes the prop when held) | click handlers give the item and hide the prop in every map (e.g. `darkpassageway.lua:283-293`, `arslegardcity.lua:142`); Wizard's Lab Prop26 skipped: item 386 is not in MASTERITEMLIST (`mm9r_wizardslab/README.md:132`) | OK |
| BookLetter.scr | 21 maps, 86 objects | `:OnUse` DoLetter Item_ID (a letter) or open the book, DoLetter after 1 s, close after 5 s; bDown 1: lies flat | letters as `evt.SimpleMessage` with BOOK AND SCROLL TEXT.csv in every map but Anskram Keep; flat letters C1 (dungeon/content.py `flat_letter`). **Anskram Keep's five letters (Prop3-7: items 488 x4, 489) have no click** (`mm9r_anskramkeep/work/content.json` event 0; nothing in `anskramkeep.lua`). Ta'Sar's AIRail objects with BookLetter params are rails (not readable in MM9 either) | PARTIAL (Anskram Keep MISSING_DATA) |
| Book.scr | 11 maps, 21 books | `:OnUse` cycles OpenBook / TurnPage / TurnBack / CloseBook animations; no text | cities show "Book.scr books (no text in MM9)" as a status or nothing; Lich Lab Book0, Lindisfarne Monastery Book0, Thronheim Prop8 not clickable | NOT_NEEDED (animation only) |
| ForadWorld.scr | 14 cities and regions | location key 1024-1033 by parameter, shop night key 5017 | shared outdoor_blv.py `map_script` and the cities' citylua: every map gives its key (`giveKey(1026)` etc.) and runs the 5017 timer | OK |
| TM_Hardrock.scr | Afterworld RetributionCounter "1 387", Drangheim YobboeMan "6 129 6000", Isle KillControl "8 27 200", Thjorad Mine CaveInControl "1 35 5000", dw "10 36 5000" | counts OneDown messages; at N: key, quest sound, experience; key 36 also triggers Ebora FreeAtLast | every counter in the map Lua (`afterworld.lua:150`, M5 Drangheim `HARDROCK` event 601, `isleofashes.lua:121-145`, `thjoradmine.lua:251,453`) | OK |
| AutoResurrect.scr | Chasm 21 zombies/drippers, Isle BoneThrasher0-3, Lich Lab SkeletonMaster52 | hidden, non-solid until TMSG_RESURRECT, then visible and runs its ScriptName | Chasm: hidden until each Trigger2-6 RESURRECT (`mm9r_chasmofthedead/convert.py:263-274`); Isle: story.py STORY_TRIGGERS (M9); Lich Lab: SkeletonMaster1's DamageTrigger raises it (B8) | OK (rise animation missing: P3) |
| KingKong.scr | Anskram BustOut 6, Invent-a-Storca BustOutLich/LichKing, Lich Lab Explode 4, Thjorad Mine gnolls 3, Verhoffin busts | dormant in a cage; ForceBreak/ForceFall destroys the cage brush and attacks | per-map pads/handlers in all five (`mm9r_anskramkeep/README.md:225`, `mm9r_inventastorca/README.md:98`, `mm9r_lichlab/README.md:121`, `thjoradmine.lua:657-674`, `mm9r_verhoffinruins/convert.py:87,747`); Verhoffin's ceiling slabs BreakOut0/1 stay (the monsters appear under them) | OK (Verhoffin slab P3) |
| PropTrigger.scr | Afterworld ExitTrigger1, Guberland Prop0, Isle Prop159, Ta'Sar Prop159/Prop162 | Use or touch relays `<Message>` to `<Target>` | each relayed (`afterworld.lua:140`, `guberland.lua:69-77`, `isleofashes.lua:1515`, `tasaracademy.lua:129,234`) | OK |
| DrainWater.scr | Bath House BlueWater2, Verhoffin WaterTrap | fill/drain: moves the water brush, triggers its fill/drain triggers | Bath House: FloodWater movers (`bathhouse.lua:72-78`); Verhoffin: the water trap with the nozzle locks (`verhoffinruins.lua:205-227`) | OK |
| ScurryCreature.scr | Dook's Castle 6, Invent-a-Storca 6 basilisks | on "Hide": run to HideMarker, removed | monster AI part of the audit (not a level object); no level effect | NOT_NEEDED here |
| EboraCam1.scr | Bath House, Thjorad Mine | the Ebora cutscene camera | C11 cinematics `ebora_escape`, `ebora_free` (MM9_CUTSCENES.md), effective at R2 | OK (at R2) |
| TrainingEnter.scr | Thjorgard ScriptObject1, Training Hall TrainingTrigger | Training Hall entry/exit state, exits enabled by key | M8: `Mm9ExitDisabled<idx>` in Thjorgard's regionlua (486/114 with key 301) and the Training Hall's own | OK |
| WinMan.scr | 1000 Terrors WinMan (Prop), Hall of the Gods WinMan "Part2" | the final: key 109, the move to the Hall of the Gods, :End DoHighScore | converter fixed (`mm9r_1000terrors/convert.py:67-77` `hall_of_gods_arrival`), **installed `1000terrors.lua:481` still moves to `hallofthegods.odm` (deleted)**; Hall of the Gods' certificate by qbit 90109 (D3) | PARTIAL (fixed at R2; G1 verified the current break headless) |

### Object classes and wiring that act without a script (all maps)

| Class (count) | MM9 | Rework (evidence) | Status |
| --- | --- | --- | --- |
| **ExitTrigger (105) and arrivals: map_transitions.txt frame** | the exit volume at the DAT position; arrivals at the destination's start point | **The 12 regions and Afterworld (isleofashes_blv_root maps) were rebuilt with an x/y frame offset (work/transform.json: Sturmford -2519/35, Guberland -11399/219, Thronheim -33607/15, Afterworld 9082/14021, ...), but their rows in `worlds/mm9/data_tables/map_transitions.txt` keep the old ODM frame: dungeon/tables.py `transitions_text` ("frame unchanged") never subtracts `project.offset` from CenterX/Y or ArrivalX/Y; only Arslegard City's and Connecting Tunnels' own wrappers do.** Checked: 49 exit volumes in 15 maps and 48 arrivals into 11 maps differ from original - offset (scratch `transitions_check.py`). Headless: Sturmford's ExitTrigger2 (to Anskram Keep) does not fire at the keep's gate (15421, 16656) and fires 2 519 units west (12902, 16691) (`sc_exit_new.yml` fails, `sc_exit_old.yml` passes); Guberland's gate to Guberland City (6131, -9194, the party on the floor inside the volume's z range) does not fire, the old-frame point (-5268, -8975) does, after the party falls to z -819 (`sc_gexit_*.yml`). Thronheim's exits sit at x -50913, -56023, -43638: outside the BLV's int16 frame, unreachable. Arrivals into these maps land 2.5-33.6 k units from their start points | **MISSING_DATA (P1)** |
| **Same table, the rebuild now running** | | Arslegard City's and Connecting Tunnels' wrappers (`mm9r_arslegardcity/convert.py:274`, `mm9r_connectingtunnels/convert.py:179`) read "the original" rows from `assets_dev/worlds/mm9/data_tables/map_transitions.txt`, which since P1 holds the already-offset rows: the review root's table (output/mm9_rework/assets_dev, 16:43) now has them **offset twice** (Arslegard exits CenterY 25254 instead of 5254, arrivals from 1000 Terrors, Bath House, Hall of the Gods at y 13458 instead of -6542; Connecting Tunnels exits at x 243 instead of 17243, arrivals from Thronheim and Yorwick at 324 instead of 17324) | **MISSING_DATA (P1, regression in R2)** |
| ExitTrigger StartOn 0 (6) | disabled until a trigger sends On | engine `Mm9ExitDisabled<idx>`, per map (M8, C7) | OK |
| ExitTrigger AskPlayer / TravelDays | confirmation, travel time | table columns, the engine's confirmation | OK |
| TreasureChest (163), TreasureBag (4) | loot containers | scene `loot_containers` equal to the DAT count in every map (+ spawned bags: Invent-a-Storca 2, Sturmford City 2; urns C6) | OK |
| Key items / locks (Door/RotatingDoor `Locked` 328, DoorLock.scr 11) | a locked door opens only after `unlock` or with its key | keyed doors OK (above); locked-without-unlocker doors locked (outdoor_blv.py `locked_models`, cities' LOCKED_GROUPS); per-map unlock chains in the group sections | OK / per map |
| Destructibles (DestructableBrush 261, DestructableProp 174) | break by damage (HitPoints, CanDamage), Death/DamageTrigger messages | scene `destructibles` + engine damage (INDOOR_DESTRUCTIBLES.md); Sturmford's drawbridge chains verified headless: `destructible 316 damage 5` plus a Fire Bolt at DestructableBrush0 opens the drawbridge (mechanism 11) (`sc_drawbridge.yml`). Maps that built them as click movers instead (Thjorad Mine, Connecting Tunnels, Dragon Stadium, Invent-a-Storca, Ruined Temple, Ta'Sar, Yanmir, Verhoffin's bolt, Frosgard City): see the group sections | PARTIAL (P2: click instead of damage) |
| Fire (170) | particle fire, switched by On/Off | C4 always-on fires; switched ones per map (74 links in 8 maps, group sections) | OK / per map |
| Light, ObjectLight, DirLight (5 767) | static (no message targets a Light in any DAT) | BLV lights / bake | OK |
| GlowingLight (38) | pulsing light | scene `pulsing_lights` (Wizard's Lab 37, Lich Lab 1); 3 switch links (Lich Lab Glow1, Wizard's Lab) per group | OK / per map |
| PerceptionLight (75: Dark Passageway 61, Thjorad Mine 10, Verhoffin 4) | a light shown by Perception, switched | scene pulsing lights, shown by Perception, switched by Off/On (2026-11-06 night) | OK |
| AmbientSound (1 378) | positional loops, switched On/Off by 98 links | scene `ambient_sounds` (counts match, less the sounds with missing audio: Boot Camp 20->14, Dook's 25->17, Guberland 59->46); switching E4/C10 | OK (missing audio: import) |
| EarthQuake (29 in 7 maps) | camera shake (QuakeDuration, ShakeAmount) on Trigger | C11 `evt.CameraShake` in Ruined Temple, Thjorad Mine, Bath House, 1000 Terrors: effective at R2 (no installed map calls it yet); Yanmir 10, Isle 2, Wizard's Lab 1 per group | PARTIAL (at R2) |
| WeatherMan (12), Fog (24) | fog/weather sequences, night fog (TurnOffAtNight), Frosgard region's 4 trigger switches | the scene fog takes the StartOn state and the cities' night block; trigger switching by the shared weather triggers and evt.SetFog (2026-11-06 night) | OK |
| Snow (35), Rain (1) | weather volumes | scene sky `weather` (Frosgard snow, Sturmford rain) | OK |
| Ladder (68) | climbable | scene `ladders` (C5): counts match but Thronheim City (3 -> 2, the cities section) | OK |
| StatStone (10) | timed stat bonus on use | outdoor_blv.py `stat_stones` (EV_STAT_STONE); Boot Camp's two museum stones have no bonus | OK |
| WellMMIX (10), Cauldron (11), Cookpot (8), Clover (15) | object.lto bonuses (Stat/StatType/BonusAmt/BonusSeconds/DosesPerDay; Resistance; PoisonChance) | RE: MM9_BONUS_PROPS_RE.md; shared click events and MM9.useWell/useCauldron/useCookpot/useClover (timed bonuses until rest; 2026-11-06 night) | OK |
| BonePile (77), Barrel (55) | searchable loot; stat barrels | C2 `searchable_loot_props` (counts match); stat_barrels.py | OK |
| RotatingBrush (15) | continuous spinners (gears, blades) switched On/Off/Reverse | scene mover.spin, evt.SpinMover, riding the AttachTo parent (2026-11-06 night) | OK |
| Teleporter (20) | touch teleports (TeleportDestination) | Dark Passageway `teleport()` boxes (`darkpassageway.lua:360`), Wizard's Lab per the cities section | OK / per map |
| Spawner (23), Shooter (169), DamageBrush (28), PropDamager (20), Lift (24), WeightedLift (14), Switch (19), Button (3) | traps, spawns, lifts | per map (group sections); WeightedLift: 1000 Terrors' 14 static, deferred (E2) | per map |
| PickupItem (1) | Temple of Honk's goose (Honk.scr) | G2b section | per map |
| HidingPlace (15) | flee targets | disabled in MM9 itself (MM9_ACTOR_ANIMATION_BLENDING_RE.md: `CheckForHidingPlace` exits at once); carried as `mm9_ai.hiding_places` | NOT_NEEDED |
| KeyFramer (0) | | no DAT object of the class | NOT_NEEDED |
| PortalZone (20), FastApproxArea (1), VolumeBrush (1), SkyPointer, DemoSkyWorldModel, TOD_Sky | visibility and sky helpers | skipped (OUTDOOR_BLV_ALL.md) | NOT_NEEDED |
| CClientFX (9: Dark Passageway 7, Wizard's Lab 2) | placed client effects | MM9 effect library binding (MM9_VISUAL_PROPERTIES.md "bind to the effect library"); per group | per map |
| Water (BlueWater 70, ClearWater 14, DirtyWater 6, CorrosiveFluid, PoisonGas) | swimmable / damaging volumes | `water_volumes` only in the regions, Wizard's Lab and Verhoffin; 13 wet maps wade on solid faces (FINAL_REBUILD_WORK C8, not done) | PARTIAL (P2, known) |

COUNTS shared scripts: OK=11 PARTIAL=3 MISSING_DATA=0 MISSING_ENGINE=0 NOT_NEEDED=2

