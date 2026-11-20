# MM9 final rebuild: the work (2026-11-05)

The user (2026-11-05): "do if you have a delta list for the engine for the MM9 which we lack + all this stuff then do
it". The list comes from [FINAL_REBUILD_GAPS.md](FINAL_REBUILD_GAPS.md) (the three sweeps); its section 4 (cutscenes,
camera shake, spinners, moving or animated decorations beyond what a phase below needs, NPC-to-NPC talk, walking NPCs,
the other minigames) stays later work: each touches a few maps and reconverts only those. This file is the checklist;
mark each item when done and verified, and note where.

Rules: AGENTS.md/CLAUDE.md; never git add/commit/stash/reset; one heavy job at a time (no map conversion beside a game
build); the review roots (output/mm9_rework/assets_dev, isleofashes_blv_root) stay the place maps are built into until
the final install.

## Phase 1: engine (one build, unit tests)

- [x] E1 Linear doors and lifts auto-close: **no engine change needed** (a `mover` block without `rotation` already
      carries `auto_close_seconds`); the converter writes it (dungeon/movers.py `linear_mover`: CloseWaitTime, not
      Sticky, not start-open; bodies reverse with ReopenOnContact, else hold).
- [x] E2 Touch-to-open Doors: converter-only, a 4 Hz poll of the party's feet against each TouchToOpen door's box grown
      by the party radius (dungeon/lua.py `Script.touch_doors`, event 900, started on load). **Deferred**: 1000 Terrors'
      14 WeightedLifts (MM9 keeps them down while weighted: the engine's auto-close timer runs regardless; static now,
      the water hall's floor stands, no route blocked).
- [x] E3 A click on an MM9 actor without a dialogue runs its 53000 + object event (IndoorGameView). Whack-a-honky needs
      no prop motion: raised geese shown and hidden by SetSprite (M1).
- [x] E4 Ambient sounds switched by the named map variable `AmbientSound<key>` (1 on, 2 off; saved with the map;
      game/audio/WorldAmbientSounds `worldAmbientSoundSwitch`, unit test).
- [x] E5 `evt.KillMapActor(index)` (ISceneEventContext::killMapActor, indoor: the normal dying state; no party xp).
- [x] E6 world.yml `partyDeath` (map, position, yaw, movie; ContentManifest, GameApplication respawn and cutscene):
      MM9 -> arslegardcity.blv StartPoint0, `MM9LoseGame` (worlds/mm9/videos/Cutscenes/MM9LoseGame.ogv from
      mm9/game/Movies/LoseGame.bik). Before: MM9 defeats fell through to MM8's Ravenshore.

## Phase 2: shared data and Lua

- [x] D1 Promotions: the approved quest -> line table (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Promotions And
      Classes") as `MM9.Promotions` (worlds/mm9/events/common/mm9_common.lua); `MM9.promoteParty` promotes every
      eligible member (`MM9.canPromote`, `MM9.promotionTarget`); every map's promotion handler calls it (Drangheim,
      Guberland, Thjorgard, Frosgard and Sturmford cities, Guberland and Frosgard regions, Lindisfarne; the Lich is
      Lich Lab's own) without keys 401-448. **Open, runtime only (no reconversion)**: MM9's promotion topics still
      show by their quest keys, not by whether a member is eligible; a quest done with no eligible member gives its
      reward and no class.
- [x] D2 Skills separate (same document, "Skills And Mastery"): generate_mm9_skill_trainers.py without composites
      (Blade: Sword, Dagger, Axe; Cudgel: Mace, Staff; Armor: Leather, Chain, Plate; Elemental: four schools), one
      lesson per skill through the shared single-skill training (GameplayDialogController; composite group training
      and the runtime's hard-coded payload mapping removed). Mind and Body by the Spirit trainers, Stealing by Disarm
      Trap, Regeneration by Body Building, Alchemy by Identify Item: every skill at Expert, Master and Grandmaster;
      the audit's `coverage` gate fails on an untaught one. Python tests; doctests `MM9 RUDE trainer topics*`,
      `MM9 skill trainer*`, `MM9 world data loads*`. **Open**: Blaster and the racial abilities (two proposed Thjorgard
      trainer NPCs, not placed); MM9 skill books still composite at Normal.
- [x] D3 The MM9 ending: world.yml `completion` (qbit 90109 = key 109, art `9winbg` = WINBG.pcx at 1280 x 960 in
      worlds/mm9/icons_x2, MM9's text; layout `draw_headline: false`, a new option: the art has its title painted).

## Phase 3: shared converter (mm9r_common)

- [x] C1 Flat letters: dungeon/content.py `flat_letter` (BookLetter.scr bDown 1 on an upright `mm9_scroll*` ->
      `mm9_scrollflat*`, same scale; 36 letters, all scale 1; Thjorgard City's scrollp90 stay); model installed
      (worlds/mm9/models/mm9_deco_scrollflat.glb), row 2806 by props/mm9_outdoor_regions_claude/scripts/converter_rows.py.
- [x] C2 Bone and trash piles: content.py `props` (class BonePile -> event 30000 + DAT index), the scene's
      `searchable_loot_props` from the shared item sources, `evt.SearchLootProp` (dungeon/objects.py). Checked on
      Drangheim Prison (scratch: 13 piles, Lua compiles).
- [x] C3 Perception hints: dungeon/perception.py (cog 23000 + DAT index, translucent two-sided, .spr frames; poll event
      901 by each brush's PerceptionValue; `HintOff<cog>` turns one off; destructibles' Death/DamageTrigger "off" to a
      brush turns it off). Maps with their own hints (11 dungeons) keep them.
- [x] C4 Always-on fires: dungeon/objects.py `place_fires` (Fire On 1, Fire 1, not named by any object or script: the
      gate fire's flames at FireScale / 12 unless a burning prop stands under it (the log piles), its SoundFile as an
      ambient sound, its light where no MM9 Light is within LightMaxRadius); rows mm9_gatefire_x25 / x208 added.
- [x] C5 Ladders: overrides `ladders` for Boot Camp 3-5, Sturmford 0/1, Lindisfarne 0/1, Drangheim 5, Sturmford City
      2-6 (Ladder3 the shaft to Beethoven's grate), 1000 Terrors 7 (measured against the static geometry).
- [x] C6 Urns and explosions: dungeon/destructibles.py `on_break` (TreasureBag -> `spawned_loot_containers` +
      `evt.SpawnLootContainer`; Exploding -> ExplodeDamage fire to the party within DamageRadius and to the other
      exploding destructibles; event 30000 + index) where the map hook gives no destroyed event.
- [x] C7 Start-open doors: dungeon/movers.py `start_open` (rule, else MM9 StartOpen: Ta'Sar's Switch/Switch1, Wizard's
      Lab's Closet2Door1/2). Disabled exits: engine gate `Mm9ExitDisabled<idx>` (main session); Afterworld 105 and
      Thjorgard 486/114 in their regionlua; Dark Passageway, the Training Hall and Yanmir's gate theirs.
- [ ] C8 **Swimming: shared rule done 2026-11-06 evening, per-map work partly open.** The user: MM9's volumes are
      the authority, one shared converter rule for every map (DUNGEON_PLAYBOOK.md "Water volumes and swimming";
      `dungeon/water.py` `swimming` (on unless `swim: false`), `surface_polygon` + `Beds` (liquid surfaces non-solid
      where a bed is under them), `drawn_surfaces` (ShowSurface tops), `swimmer_foot`; `Build.water_checks`;
      `dungeon/swim_check.py` writes a per-map swim scenario). Reconverted into the review roots and checked by
      scenario: 1000 Terrors, Bathhouse, Dark Passageway, Temple of Honk, Lich Lab, the Guberland region, Frosgard
      City (its sea stays a solid wading floor: no seabed built), Sturmford City's well (scenario_well.yml: in, up, out
      by the chain), Training Hall (pole room bed built), Yanmir's Fort, Chasm of the Dead (Acid0 swum; the Lua lift
      to the rim stays, `swim_check_skip`), Drangheim Prison, Arslegard City, Guberland City. Converter changes in,
      rebuild queued and untested at 22:30 (heavy.lock starved, game binary missing mid-build): Beethoven (shaft walls
      to MM9's depth), Dook's Castle (chest on the lake bed, Ladder0's foot under the surface), Dungeon of Secrets
      (the tunnel swum, the sink stand-in gone), Inventa Storca (the pad gone; cavern, channel, well), Thjorad Mine
      (bed unchecked), Training Hall and Guberland City (`own_water_surfaces`); run
      `scratchpad/swim/test_map.sh <map>` after each. Decorative (they wade): Arslegard City's 4 fountains, Drangheim
      Prison's sink, trough and lava, Guberland City's fish tank, Beethoven's baths, Chasm's channel and pool. The
      regions' far seas and Frosgard City's sea have no built seabed (their surfaces stay solid). The click breakables
      (sink/slide movers with scripted consequences in 13 maps) are still open.
- [x] C9 Linear door auto-close and touch-to-open (E1, E2; main session).
- [x] C10 Ambient switches: dungeon/objects.py `ambient_triggers` (dungeons' plain touch Triggers: 1000 Terrors
      Rumble0, Dungeon of Secrets' rats, Training Hall creak1; poll event 903); door/switch links in Verhoffin
      (waterfill), Lich Lab (PanelOn0/1), Dark Passageway (magic elevator sound), Training Hall (exsound0-3);
      ambient.py LoopCount 1 -> once per switch-on; cities' and regions' links listed for their scripts.
- [x] C11 **Cutscenes** (2026-11-06; the next free number, C10 being the ambient switches): engine, format, shared
      emitter (`mm9r_common/cinematics.py`, `cutscenes.py`) and camera gate (`camera_gate.py`, strict in
      `dungeon/build.py` after the install; overrides.yml `cinematics_gate`) done ([MM9_CUTSCENES.md](MM9_CUTSCENES.md)
      sections 3-10). Every cutscene is in its converter, with play and skip scenarios in its project, tested in the
      scratch root `output/mm9_rework/cinematics_pilot_root` (no conversion): isleofashes `book_sinking` (the islet
      a `dat` mover, the boat gliding), thronheimcity `council_argument` (+ Knut's rant as Lua), yorwick
      `battlefield_sven`, afterworld `afterworld_guilt`, frosgardcity `break_ice` and `bob_and_doug` (ambient),
      arslegardcity `gate_fate` and `gate_writ`, 1000terrors `njam_freeze_win`, `njam_taunt`, `chess_capture_<k>`,
      hallofthegods `gods_epilogue`, wizardslab `summoning`, bathhouse `ebora_escape`, thjoradmine `ebora_free`,
      yanmirsfort `yanmir_death`, guberland `newgame_talk` and drangheimcity `dwarves_and_humans` (ambient); shakes in
      ruinedtemple, thjoradmine, bathhouse, 1000terrors. The 228 cinema voices are imported (worlds/mm9/audio/
      voices/cinema). **Takes effect at each map's conversion (R1)**; the projects' regenerated `scenario_scripted.yml`
      (arslegardcity, 1000terrors, hallofthegods) expect the converted maps and fail against today's review root until
      then. Not carried: Njam's freeze skins, MM9's missing subtitle texts, Kira's sword prop, Yorwick's dead Bjarni and
      Tryggva figures (no decoration rows). greatgate's `lose_game` is the MM9LoseGame movie (E6).
- [x] B1 Quest XP caps in the converters (2026-11-06, BALANCE_PLAN.md 3.1): every rework award through
      `mm9r_common/quest_xp.py` (mm9_quest_xp_profile.yml by key and original, else script and routine), 110 sites in
      31 converters, 69 capped; `quest_xp_audit.py` -> `quest_xp_audit.json` (58 of 59 profile entries paid; Forad
      Darre's death not carried); Mountain Pass's 14,000 pays once. Converters import cleanly; no map reconverted:
      takes effect at the next conversion (R1).
- [x] B2 Pack growth in the converter (2026-11-06, BALANCE_PLAN.md 3.6): `dungeon/density.py`, run by
      `dungeon/build.py` for every map (dungeons, cities, regions) after the actors, the scene hook and the map Lua.
      Each pack of `density_anchors.json` (openyamm-95's frozen targets) gets `add` copies of its ordinary members,
      appended after every existing actor (anchors `<member>_grow<k>`, in content.json with `copy_of`); a copy is the
      member's whole record without npc_id, RUDE id, source object index or unique name. Not copied: members with an
      identity, hidden, `mm9_can_receive_damage: false`, passive, or whose index the map Lua names (a conservative
      scan: actor calls, kill-hook tables, constants and loop tables); 1000 Terrors' ACTOR directory is exempt
      (`Hooks.density_lua_directories`; the copies are added to it, also by its `--lua` rerun), and Yanmir's Fort's
      `PLACED` moves past the copies (`Hooks.grown`). Placement on the compiled BLV: 120-600 units from the member,
      its floor (24 units) and sector, reached without a wall or pit, clear of walls, actors, doors (their travel),
      ladders, event faces and water; seeded by map, anchor and copy, so reconversions agree; other members next.
      Redistribution (openyamm-95, option b): a pack's unplaced copies (no free spot, or only scripted members) move
      one at a time to the map's other growable packs (the add > 0 packs of density_anchors.json with ordinary
      members), the most room left first (`capacity` less the size after growth), never past capacity; the rest stay
      unplaced with their reason. Report: build_report.json `density` and work/density.json: `target_total`
      (counted_today + wanted adds), `placed_total`, `wanted_adds`, `placed_adds`, `moved_adds`, `unplaced_adds`,
      `unplaced_reasons`; per pack placed, moved_in, room_left, skipped members, refused reasons. Off per map with
      overrides.yml `map: {density: false}`, per run with `convert.py --no-density`. Tests: `test_density.py` (9).
      Dry check on the installed maps (`density_dry_check.py`, nothing converted), placed of target: Bathhouse 44 of
      44 (8 moved from the hidden spore packs), 1000 Terrors 465 of 465 (60 moved, from the packs whose only members
      trigger spawns on death), Sturmford 78 of 78, Temple of Honk 29 of 35 (the Accountant's 6: the other packs are at
      capacity); all 43 maps 2,717 of 2,723 (adds 1,241 of 1,247, 169 moved). Takes effect at the next conversion (R1).
      2026-11-07: scripted members were still copied (Lich Lab's LichSummoner: group 70 held three, so its kill check
      never passed). Also not copied now: a DAT ScriptName (KingKong breakers, summoners, Training Hall's orcs and
      Trellborgs, Dook's captains, Temple of Honk's geese, Frosgard's jumpers, the Isle's Mac), ShouldRepopulate 0,
      a unique DAT name (the Isle's JK, Thjorgard's IckyRecon), the unique boss rows, mm9_ai `boss`, a group the
      Lua addresses (group bits, wakes, group kill checks), an `MM9.receives` receiver or a quoted DAT name, the
      walk/clip/alive calls, and the cinematics' actors (`References`, `test_density.py` 10). Maps that had such
      copies were reconverted: Lich Lab, Training Hall, Beethoven, Dook's Castle, Anskram Keep, Bathhouse,
      Verhoffin Ruins, Temple of Honk, Isle of Ashes, Thjorgard, Frosgard.
- [x] B3 MM9 CanDamage (2026-11-06, [MM9_ACTOR_PROPERTY_AUDIT.md](MM9_ACTOR_PROPERTY_AUDIT.md) section 1): 412
      placed actors in 25 maps have `CanDamage 0` (townsfolk, gods, Afterworld heroes, Baron Dook, Ebora and her
      bathmate, Yanmir, 1000 Terrors' critters, Isle of Ashes' Yrsa/Forad/sea monster, Beethoven's coffin mummies,
      Invent-a-Storca's basilisks). Engine: the scene flag `mm9_can_receive_damage` is now enforced indoors too (it was
      parsed and saved but unchecked; outdoors it already was): no melee, missile, spell, area, reflected or monster
      hit hurts, stuns or debuffs it; `evt.SetMm9ActorCanReceiveDamage(index, on)` indoors and outdoors, wrapped as
      `MM9.setCanDamage` (mm9_common.lua); openyamm_runtime_tests `*CanDamage*` (IndoorActorFactionRuntimeTests,
      MonsterModifierWorldTests) pass.
      Converter: `Content.actor()` writes `mm9_can_receive_damage: false` for CanDamage 0 (pack growth skips them);
      Beethoven's `mummy(k)` turns its mummy damageable when it kicks free (COFFINMUMMY.scr :OnPostDestroy). The other
      seven switching scripts need nothing (audit table). Takes effect at the next conversion (R1). The flag blocks all damage, not only physical as MM9's: the user, 2026-11-06.
- [x] B4 `ShouldRepopulate 0` (42 actors, 13 maps: retainers, bank orbs, quest NPCs, Kluso's House's Count, Wizard's
      Lab's Evil Grand Sorcerer), 2026-11-06: scene actor `respawns_on_refill: false` (default true: MM6-MM8
      unchanged), written by `Content.actor()`; at a refill (timed or forced) the engine keeps such an actor's saved
      record when the saved map has the same placement at that index (name and monster): indoors
      `keepActorsThroughRefill` (game/maps/MapDeltaData), outdoors its saved MapActorState (GameApplication). Unit
      test in MapDeltaDataTests. The flag is scene data, read at each refill; the kept state is saved as before.
- [x] B5 `Visible 0` actors placed visible, 2026-11-06: `Content.actor()` places every DAT Visible 0 actor hidden.
      Shows at MM9's moment: the Afterworld heroes and Forad by the existing Lua (SixFires.inc :Confession,
      :Retribution), Guberland's Nicolai and Alvar by the region load (NPC414.scr, Retainer.scr :Init); the Isle's
      Lich summoner stays unseen (story.lua spawns for it); Thjorgard's four jumpers appear after JumperTrigger (0 at
      once, 1 after 1-2.5 s, 2 after 10-25 s, 3 after 30-45 s; mm9r_thjorgard_blv/regionlua.py `jumperTick`).
- [ ] B6 `Solid 0` (56 actors: the critter flocks of 1000 Terrors and Lich Lab, the Forest Giants, Thjorgard's actors):
      the engine has no non-solid actor (a scene `solid: false`), later.
- [x] B7 `ExecuteScript 0` (12 actors), 2026-11-06: object.lto's AI ReadProp (0x1000cf34) starts the placement's
      ScriptName only with ExecuteScript set (default 1); other scripts start some later (Guberland City's peasant2,
      the Dark Passageway adventurer, the Invent-a-Storca guard), nothing starts Drangheim Prison's PatrolGuard1 and
      Guard6 or Yanmir's children. `Content.actor()` (dungeon/content.py) drops the script's movement from their
      `mm9_ai` (wander, path, stops, waits, leash): the prison guards stand at their posts.
- [x] B8 Death and damage triggers, 2026-11-06: Thjorgard region `Jumper0/1 -> Jumper2/3 BuddyDead` (a kill hook
      shows the partner at once; regionlua.py), Lich Lab `SkeletonMaster1 -> SkeletonMaster52 Resurrect` (a damage
      hook shows the buried one, hostile; convert.py `DAMAGE_TRIGGERS`), Verhoffin Ruins `BustWraith0-3 ->
      BreakOutDust0 On` (a damage hook puffs mm9:smoke at the Fire, once per bust; `DUST_ON_HIT`).
- [ ] B9 `AutoDeactivate 0` set pieces (109 actors): check that the Temple of Honk procession, Kluso's House patrol and
      Wizard's Lab ritual keep going with the party far away.
- [ ] B10 `CheckForAIBarrier`: MM9 holds only its 413 flagged walkers at AIBarrier volumes; the rework's barriers hold
      every walker. A per-actor flag only if a map needs it.
- [ ] B11 `FadeOnDeath 1` (Beethoven's 16 Lobbers): the corpse fades; cosmetic.
- [ ] B12 `WanderPathStart` (5 path walkers): the first marker (then 1, 2 ...); cosmetic.

## Phase 4: maps

- [x] M1 Thjorgard: whack-a-honky and arm wrestling (main quest key 94); the boat race reachable. Written
      (regionlua.py: Switch0 a rotating lever, geese shown/hidden by SetSprite cogs 440-443, timers 302/303; the
      captain placed by overrides.yml `outdoor.people`, event 53000 + 117); scenario_games.yml to run.
- [x] M2 Afterworld: Forad Darre placed (mm9_monster_legacy_replacements.tsv row 252 -> 9252 hostile, class
      ForadDarre in Afterworld's monster_classes only; the Isle keeps its story NPC); ExitTrigger1 only at key 390.
- [x] M3 Hall of the Gods: the trip to afterworld.blv (convert.py `afterworld_arrival`: Afterworld's StartPoint0).
- [x] M4 Thjorgard: the adult Magreeb (class Magreeb in monster_classes; regionlua's Scholarpromo hook).
- [x] M5 Drangheim region: tm_Hardrock as the bandits' kill counter (key 129; regionlua.py `HARDROCK`, event 601).
- [x] M6 Isle of Ashes: Yrsa does not leave early: already so (story.lua: hidden only with keys 29 and 28); the
      pilot README's stale warning corrected.
- [x] M7 Yanmir's Fort: exit trigger 777. Its volume floats over the floor (z 39-325, the floor at 1): the engine
      tested the party's feet as a point. Now the party's body touches the volume, as MM9's TouchNotify does
      (Mm9PositionedTransitionRuntime `bodyTouches`, unit test); every MM9 exit trigger benefits, no reconversion.
- [x] M8 Thjorgard -> Training Hall exits and the other disabled-at-start exits (with C7). Engine: an exit trigger is
      skipped while the named map var `Mm9ExitDisabled<source index>` is non-zero (unit test). Thjorgard's
      ExitTrigger3/6 (486, 114) on with key 301, Afterworld's ExitTrigger1 (105) with key 390 (their regionlua); the
      shared StartOn 0 rule is C7's.
- [x] M9 Monster wake-ups: the Isle's BoneThrasher0 rises on Trigger1 like the bunker's (story.py STORY_TRIGGERS).
      Frosgard's Yeti6-9, Thjorgard's Jumper0-3 and the Isle's Peter stay ordinary monsters that see the party
      (Jumper.inc's leap off the cliff is AI motion, section 4).
- [x] M10 Shooters: Frosgard City's cannon (Shooter0 under the ice: eight FireBolts at Shoot0-5 from the barrel's
      blast, citylua.py T_CANNON; the night test and Shooter5's test shot not carried: no quest); Wizard's Lab's
      apprentices' lightning (ShooterSummon<k> -> SummonLocation beams at each conjure).
- [x] M11 Sturmford City's magic shop ceiling. Not a leak: the shop's air is all its own room. Its ceiling polygon
      (16 vertices, running out over the walls to the street's outer faces) voted 226 street to 124 shop samples
      because the face vote's fan sampling gave each zero-area triangle between its edge (T-junction) vertices a full
      triangle's samples, so most votes sat on the edges over the walls. Converter fix, opt-in: `map: {corner_samples:
      true}` (dungeon/rooms.py `NearestRoom.front`, geometry.py `corner_ring`; DUNGEON_PLAYBOOK "Corner samples"), set
      in Sturmford City only; reconverted and lightmaps redone.
- [ ] M12 Trainers for Blaster and the racial abilities (D2's proposal: two Thjorgard NPCs, own dialogue rows).
- [x] M13 Normal skills in the venues (user decision 2026-11-06): `learn_skills` columns in vendors.txt and
      service_venues.txt (generate_mm9_vendors.py), HouseTable parses them, MM9 shops show "Learn Skills";
      lists in MM9_RUDE_SCR_INTEGRATION.md "Skills And Mastery".
- [ ] M17 3D actors drawn at the wrong size (user 2026-11-06: Sturmford City's townsfolk too small, Thjorgard's dwarves
      too big): the engine sizes a 3D model by actor height / descriptor height (WorldFxSystem.cpp ~1515, since 1.2) and
      the converter writes MM9's collision body into the height (bodies.py). Fix agreed with openyamm-19 and the user:
      scene actor `draw_scale` (engine: openyamm-19; replaces the ratio when present) and the converter writes it for
      every MM9 row actor (content.py, bodies.draw_scale: DAT Scale / row Scale, 1.0 for most). Engine and converter
      done (openyamm-19: `draw_scale` > 0 replaces the ratio, saved; MM9_MONSTER_COLLISION_RE.md "Placed actors").
      **Left: every MM9 map's reconversion** (the conversion hold).
- [ ] M18 Seated figures float over their seats (user 2026-11-06, Sturmford City's tavern). Cause: the props projects
      stood every MoveToFloor posed figure with its feet on the surface under its DAT position, and under the seated
      townsfolk that is MM9's PhysicsBSP blocker over the bench, pew or throne step (the tavern's 19804, the room floor
      19757) or the Arena stand's step they sit on: feet on the seat, the figure a seat height (35-50 units) over it.
      MM9 puts the bottom of the object's dims box there (pos = hit + dims.y + 0.1 LT), and the seated libraries' dims
      (PeasantSeated / MP_2s: half height 20, origin -15 LT) end at the thighs, 19 LT over the feet. Fix (rule and
      measurement in mm9_sturmfordcity_claude/scripts/seats.py: the figure's seat plane on the seat model's top, 2
      units in, else on the MoveToFloor surface): **bindings, in effect now** (seated_offsets.py --apply: z_offset
      -40 to -50 on the tavern/pew peasants, Ercc and the Arena's 11 spectators, written to
      worlds/mm9/models/indoor_decorations.yml and both review roots; work/seat_offsets.json, which Sturmford's and the
      Arena's tables.py now emit). Shared mm9_peasantms2dlisten: -45.2, the mean of Halfdan's bench (-41.3) and the
      Arena step (-49.1). **Bjarni (Sturmford's throne) needs the reconversion**: his model sits right on Thronheim's
      chair, so placements.py lowers that placement (props.json z 19799 -> 19762.7, patched; the generator reads the
      archived ODM now that sturmfordcity.odm is a BLV). Unchanged: Ludwig and the man on the bar stool (MoveToFloor 0,
      MM9's own height), the standing Bartender, Thronheim's council (on their chairs; hidden at start, not looked at in
      game), Afterworld's heroes (sit on the ground by design). Shots: mm9_sturmfordcity_claude/review/seated_fix/.
      **Left: Sturmford City's reconversion** (R2), then a look at Bjarni.
- [ ] M16 MM9's own tree models on the cities and dungeons (user 2026-11-06: "the ugly mm9 ones"): Sturmford City 29,
      Arslegard City 28, Dark Passageway 25, Guberland City 10, Lindisfarne Monastery 4. **Converter done, conversions
      not yet** (the user: wait for the other session's monster density changes): dungeon/trees.py swaps every
      `mm9_treeNN[_xS]` prop for the regions' `mm9v_<ours>_<height>` tree (vegetation.py's species, weights and MM9
      height; tree01b added as tree02's pine), 8 units into the ground; content.py `props` calls it; the 4 missing rows
      (mm9v_6tree18_500/1100/1200/1550) written by `trees.py` into assets_dev and both review roots. The Green Man's
      tree and the Tree of Life stay. Next: reconvert the five maps (with lightmaps) and check a screenshot each.
- [ ] M15 Frosgard City's 14 path walkers (NPC181-NPC199.scr include only globals.inc and pledge.inc, no wander
      logic): in MM9 they may stand still, the converted scene makes them walk (openyamm-19, 2026-11-06). Check their
      scripts and the DAT, then fix the city's placement (frosgardcity overrides) at its next conversion. The next
      conversion of any map also picks up openyamm-19's path marker stops (mm9_ai_placement.py `path_stops`).
- [x] M14 MM9 inns and banks (user 2026-11-06): RUDE -7 opens the inn as an MM6-MM8 tavern (room, food by the inn's
      value = merchant base × 10, Learn Skills as the general stores), -6 the shared bank; 14 rows more in
      service_venues.txt. Sturmford City's scenario_shops checks the inn. Open: hire/dismiss (-10/-11), item combine
      (-13), town portal (-15); table in MM9_RUDE_SCR_INTEGRATION.md "Services".

- [x] B13 Chest balance in the converter (openyamm-95, user 2026-11-06): dungeon/build.py calls
      mm9_chest_balance.balance_loot_containers(stem, scene loot_containers) before the scene is written (black chests a
      guaranteed level-7 artifact or relic, level-0 random chests the map's usual level, `random_records` 3 for every
      ordinary random chest: MM7's average; the user, 2026-11-06: MM9's fewer chests are not made up with fuller ones). The game needs a rebuild to read random_records (touch game/maps/MapItemSourceData.h first). After the
      conversion: devdocs/mm9_rework/balance_prototypes/chests.py (installed) against --planned (~460 items, 15
      artifacts).
- [ ] R2 The final rebuild (user 2026-11-06): all 44 maps with M16 trees, M17 draw_scale, M18 Bjarni's seat, B1 XP
      caps, B2 pack growth, B3 CanDamage, B13 chests, M21's actor fixes, the 1000 Terrors Hall of the Gods move,
      Forad's death award and the hireling story Lua. **Blocker (found 2026-11-06, M21)**: P1 deleted
      `assets_dev/worlds/mm9/maps/<stem>.material_aliases.yml`, which every converter's `Source()` reads
      (dungeon/source.py `Project.aliases`; also terrain_textures.py, terrain_blend.py, Invent-a-Storca's verhoffinruins
      read): conversions stop with FileNotFoundError. Copies: the review root, promotion_backup_20261106,
      assets_editor_dev (5 of those differ in the statistics header);
      installed into assets_dev (not only the review roots), then openyamm-95's gate
      (`mm9_balance_report.py --gate --mm9-source scenes`, needs build/tools/openyamm_balance_probe) and chests.py.

      Blocker fixed (2026-11-06): P1 deleted the old import's side files from assets_dev, which the converters and
      the props generators read (material_aliases, raw_objects, odm, model_assets, mm9.yml, render, nav, the native
      textures); every such read now goes to assets_editor_dev/worlds/mm9 (the import's complete copy, not
      shipped): dungeon/source.py, terrain_blend.py, terrain_textures.py, real_context.py, the Inventastorca and
      Isle of Ashes converters and the props projects' placements/props_table scripts. Bath House --plan passes.
- [x] M19 Actors left out by `monster_classes` (2026-11-06; audit: every non-CacheOnly DAT object with MM9 AI
      properties against each map's work/content.json and props.json). Converter: `Content.monster_bases(npc_rows=
      True)` (dungeon/content.py `npc_row_base`) gives a class without a monster replacement its own MM9 row 9000 + N
      when mm9_npc_actor_rows.tsv lists it (3D model bound in worlds/mm9 actors.yml): by the NPC resolver, else by the
      runtime row's name. Opt-in: outdoor_blv.py (every region) and the Temple of Honk; Drangheim Prison and Ta'Sar
      Academy keep their own animal records. Added to `monster_classes`: Boot Camp Goat x7 (9268), Cow x4 (9267),
      BrownCow x4 (9297, the cow model's COWBROWN tier); Yorwick Ewe x1 (9272); Temple of Honk Fish x6 (9227, friendly,
      no Honk group, placement Scale 0.4-0.7 as draw_scale) and its two geese (9293, already listed: now resolve, in the
      Honk group as DumbGoose.scr includes HonkHostility.inc). Side effect: Afterworld's ForadDarre0 resolves to 9252
      hostile again (row 252 is no longer in mm9_monster_legacy_replacements.tsv: M2 would otherwise lose him).
      Left out on purpose: Thronheim City's council (Argument cinema stage, not built: the README); Drangheim Prison's
      DwarvenSmith1 (DrangheimSmith.scr removes it); Chasm's GhostSpawner, 1000 Terrors' 64 chess squares, Anskram's
      ImpGateSpawner0-7 (invisible script holders, the map Lua carries them). Gaps: Hall of the Gods DragonAzure x2 (MM9
      ships no model); Guberland's AtliGuard (WealthyTownGuard1: no own MM9 row or model; regionlua stands in by the
      party's position); Thjorgard's Hjarrand (ShopkeeperElfFemaleB8, TownDwarfMaleA 9010: placed by `npcs()` but no
      floor under him, `npcs_without_floor`: a geometry item, not a class). Takes effect at the final rebuild (R2).
- [x] M20 MM9's animals wander as their scripts make them (openyamm-19, 2026-11-06, mm9_ai_placement.py
      `placement_ai` by the effective script): cat.scr/dog.scr always (the placement's leash/wait/time), wander.inc
      (pig, hen, rooster) aimless near their start, farmanimal.inc (cow, goat, brown cow) only with WanderON 1. Takes
      effect at the final rebuild. Open (later, engine or per-actor Lua behaviours): cats/dogs sitting with townsfolk,
      dogs chasing cats, the pig/hen pause clips, a tipped cow wandering (MM9_MONSTER_AI_PLAN.md "Animals").

- [x] M21 Actor completeness (user 2026-11-06: "I dont want any missing npcs or actors"):
      [MM9_ACTOR_COMPLETENESS.md](MM9_ACTOR_COMPLETENESS.md), re-run with `mm9r_common/actor_completeness.py`.
      2 376 character objects: 2 121 placed actors (25 from the next conversion), 104 placed props, 39 scripted, 108
      excluded with MM9's reason, 4 missing (M22, M23; done since). Converter fixes, effective at R2: Yanmir's children RUDE 433
      (was 432, the Questioner) and their dialogue on a click; Guberland's AtliGuard placed (outdoor.people
      `{name, monster_id}`, Guard row 9111) and hidden at key 197; the Afterworld's SixFires.inc spawns (Retribution's
      12 Horde, Absolution's and Rebirth's undead); LesserDemon.scr p0 1's Greater Demon for Bathhouse LesserDemon0 and
      1000 Terrors LesserDemon13/14. RUDE: 433 was the only unreachable dialogue an MM9 object hosts.
- [x] M22 Boot Camp's museum demonstration (BC_Manager.scr "SpawnLoc0 SpawnLoc1 SpawnLoc2", 2026-11-06; regionlua.py
      `museum_lines`, overrides.yml monster_classes + the three CacheOnly classes, never placed). Switch0 ("fight"):
      an Evil Grand Sorcerer (9158, facing +x) and an Oculus (9230, facing -x) out of `mm9:mist` at SpawnLoc0/1, the
      party's friends and each other's enemies (`evt.SetMonsterRelation` to the party 0, to each other 4: MM9's rows
      are the party's enemies by the table), no loot; 120 s (ForceEndFight) or one dead, then the other mists and is
      gone 2 s later; the switch springs back and works again. Switch1 ("open"): a Reverend Monk (9125) at SpawnLoc2
      walks after 1.1 s to TreasureChest4, 3 and 0 (`evt.MoveActorTo`, stopping 70 LT short of each), each opening
      to MM9's crowd sound, the next walk when it ends (cheer01 4.7 s, cheer02 6.2 s); the black chest's trap
      ("1"): column of fire, doorlatch, killed 1 s later (`evt.KillMapActor`), gone 2 s after; "open" works again.
      A load ends a show under way. Not carried: the chests' lid animations, the monk's castspell3 clip. **Engine**
      (shared, MM6-MM8 unchanged): `evt.MoveActorTo(actor, x, y, z[, arrivalEvent[, run]])`, `evt.StopActorMove`,
      `evt.IsActorMoving` (EventRuntimeState::scriptedActorMoves, runtime only; game/gameplay/ScriptedActorMoves
      `applyScriptedActorMoves` in both world runtimes, AI `AI_ScriptedMove`: the path planner's walk or run, over
      the actor's own AI and an immobile placement, not in turn-based hold; the arrival event runs at the next world
      update with the hook context's actor); `evt.SummonMonstersById` also returns the spawned actor indices and takes
      `yawDegrees`. Actor-against-actor hostility needed nothing new (`evt.SetMonsterRelation`, map-local, saved).
      Unit tests `*evt.MoveActorTo*`, `*applyScriptedActorMoves*`, `*evt.MoveActorTo walk*`. Headless on a scratch
      root with the generated Lua spliced in: the two fight (the sorcerer hurt), the monk opens all three chests and
      dies by the trap, the show re-arms. Takes effect at R2.
- [x] M23 Thronheim City's breakout completed as MM9 (citylua.py, 2026-11-06). The prison wall is the scene
      destructible it is in MM9 (overrides.yml PrisonWall static: crumble sound and dust, path map rebuilt; no
      longer a slide mover). The breakout: the Terror walks to BadAssWander1 and breaks the wall, runs to Shmoe and
      kills him, then is loose (`evt.MoveActorTo` arrivals 262/263; Ben runs to BenMarker, then to Guard1; a walk not
      done in 12 s or a load mid-breakout finishes it at once). The guards drop their peasant ally (ChangeGroupAlly 0,
      still the party's friends) so relations.yml's mm9_guards hate the Terror; before, the placed guards' ally 118
      kept them out of every guard relation (the old `SetMonsterRelation(9107, 9238)` matched only spawned guards).
      Thronheimcity_Guard.scr :OnDeath (kill hook 264): every dead Guard1/Guard2/ExtraGuard and every guard sent sends
      a new PoorTownGuard1 (9107, group 4, no loot, the party's friend) from GuardSpawn0 that runs for the Terror
      (GetBadAss, renewed each second until within 640). MM9 has no end but the Terror's death (GetBadAss then finds
      no BadAss): none come after it, and at most 12 in all (`GUARDS_SENT_CAP`), since MM9's HitPoints 250 / AC 20 at
      the breakout are not carried. Headless on a scratch root: see the report of this item's session.
- [x] M24 1000 Terrors (convert.py, 2026-11-06): (a) the spawned "LesserDemon ScriptParams 1" (Spawner8/13's
      DefaultSpawn; SpawnMgr.scr's LESSERDEMON for SpawnLoc0/1/3, `spawned_greater_on_death`) are marked by the
      spawn's returned indices (map var `Greater<index>`) and the kill hook gives them the placed ones' Greater Demon.
      (b) ChessBase.inc :PawnToQueen: ChessPiece1 (square 51) attacks 58/60 on the last rank; stepping there, after the
      2 s slide the pawn's faces hide (`PAWN_FACES`) and a Terror (MONSTERS.txt "Terror", row 164 -> 9164, HitPoints
      1069 by hpScale, `mm9:fireblue`) appears on the square; squares only a queened pawn attacked stop hurting. The
      pieces stay static, so ChessPiece0 (square 35, two moves from the last rank) never queens; AC 80 not carried.
      Headless on a scratch root (Lua from work/lua_state.pkl): Spawner8's demon releases a Greater Demon; the pawn
      queens. Takes effect at R2.

## Phase 5: the rebuild

- [ ] R1 Tell openyamm-cf (memory), refresh both review roots, reconvert all 44 maps one at a time with
      `lighting.py --layout-only` + `lightmap_transfer.py --install` each; load checks (no Lua errors), the maps'
      scenarios; MM6-MM8 regression (unit tests, tests/scenarios).

## Phase 6: install

- [x] P1 Promotion into assets_dev (user 2026-11-06: "assets_dev ... still ships the old import's 45 ODMs - it
      SHOULDNT", "you can delete those"). Each map's files from the root it was converted into (B =
      isleofashes_blv_root for the 11 regions and Afterworld, A = output/mm9_rework/assets_dev for the other 32):
      220 per-map files (44 x `.blv`, `.scene.yml`, `.lighting`, `.bake.json`, `events/maps/<stem>.lua`) and 2 054
      shared ones the roots own (textures_x2/x4 1 002 each, 23 liquid bitmaps, 25 terrain materials, 2 spell sounds),
      written with temp file + rename. Merged tables, MM6-MM8 and engine rows checked unchanged by diff:
      map_stats.txt (44 MM9 rows name the BLV, nothing else changes; Great Gate's row removed), map_transitions.txt
      (105 rows: each row's source side from the source map's root, destination side from the destination map's; the
      Arslegard chasm row 638 added), transport_routes.txt (47 rows' arrival side from the destination's root),
      texture_frame_data.txt (10 MM9 groups added), liquids.yml (27 MM9 liquids), ui/maps/catalog.yml (the 20 painted
      maps of the cities and regions in their BLV frames; the 24 dungeon entries dropped). world.yml: assets_dev's (the
      roots' copies are older), start map guberland.odm -> guberland.blv. Deleted (1 135 files): the old import's
      45 ODMs with every sidecar (`.render`, `.nav`, `.mm9.yml`, `.raw_objects.yml`, `.events.yml`, ...), the four
      `_authored` scene overlays and three `_authored.lua` (they would run as overlays on the new maps), 45 script IRs,
      the 45 stale map Lua copies directly under `worlds/mm9/events/`, Great Gate entirely (never rebuilt: an unused
      cutscene copy) and 543 `worlds/mm9/textures` bitmaps that nothing kept names (the BLVs searched byte-wise).
      Backup of every replaced or deleted file, MANIFEST.txt and the script (`promote.py`, plan.txt):
      `output/mm9_rework/promotion_backup_20261106/`. Both review roots refreshed (owned files untouched; the
      conversions still install there, so a map reconverted later is promoted again: its files and table rows as
      above). Not promoted: the Isle of Ashes ODM pilot's terrain materials and the 12 ODM liquid edge masks. Left in
      assets_dev: the dungeons' painted minimaps (`ui/maps/*.pcx`, no catalog entry now), the MM9 models and sprites.
      Checks: all 44 maps load headless from assets_dev with no Lua error and the same warnings as from the roots;
      the 125 map scenarios 123 pass, the same two failing against the roots (Bath House and Yanmir's Fort
      scenario_scripted: actor HP expectations); tests/scenarios/mm9 43 of 44 on both (ai/spell_conditions fails);
      `tools/lighting/stale_bakes.py` 0 stale; tests/scenarios 8 of 9 (mm8_right_click_portrait_item as before);
      unit tests: 7 tests read the old import's files, updated to the rebuilt maps (Bootcamp dialogue actors from the
      BLV scene, catalog bounds in the BLV frame, bootcamp.blv map stats, 105 transitions with row 638, MM9's shallow
      liquids) or cut where their subject is gone (Drangheim's ODM fog overlay, Thjorad Mine's ODM CaveIn
      destructible: a Lua door now); 2 678 of 2 681 pass, the 3 known failures. **Open**: 1000 Terrors' win handler
      moves the party to `hallofthegods.odm` at z 563 (mm9r_1000terrors/convert.py line ~719, the old frame and name;
      broken in the roots too): fix the converter, reconvert after the hold.

## Log
- 2026-11-11 final reconversion before the release: all 44 maps rebuilt (`level_generation/projects/mm9r_common/
  rebuild_all.sh`: convert, layout-only lighting base, lightmap transfer, 6 at a time through `lane.sh`; 44 ok),
  promoted (`output/mm9_rework/promotion_final_20261111/`: the 234 per-map files, tables unchanged, backup there).
  Before it, both review roots' owned tables (map_stats, transitions, transport, frames, liquids, catalog) reseeded
  from assets_dev: since `world.yml`'s openAirMaps each root failed to load the other root's maps as BLVs. MAW pack
  reserves rerun for the 7 maps whose scenes changed. Checks: `check_mm9_map_lua.py` 0, `stale_bakes.py` 0,
  `mm9_balance.py --check` clean, Android cooks current; 246 of 262 map and MM9 scenarios pass, the 16 others fail
  the same with the pre-promotion files (the current binary: other sessions' engine work); the main playthrough,
  the promotion chain (segment 50 once flaky, passes on rerun) and the 16 side quests pass; release scenarios 12/12.
- 2026-11-05 18:00: phase 1 built (openyamm, unit tests: my areas pass; 3 failures elsewhere: MM9 chest icons under
  the retired icons path, an MM9 sword equip offset, Hesper staged missiles: other sessions' work).
- 2026-11-05 19:40: engine build with the exit-trigger changes (body touch, `Mm9ExitDisabled<idx>`), unit tests pass.
  Thjorgard, Afterworld, Drangheim converted; scenarios pass: mm9r_thjorgard_blv/scenario_games.yml (whack-a-honky
  won by whacks, the arm wrestler, the hall exits off), mm9r_afterworld_blv/scenario_retribution.yml,
  mm9r_drangheim_blv/scenario_yobboes.yml, mm9r_yanmirsfort/scenario_doors_exits.yml (exit 777).
- 2026-11-05 19:50: 1000 Terrors stopped converting: the pending item import excludes MM9's spell books and scrolls
  (item_import_report.yml "excluded MM9 Magic family") and the genie lamp's GiveRandom pool named them.
  tools/mm9_import_discovery/mm9_item_sources.py: a random pool keeps its imported items and lists the excluded ones
  without blocking (blocking only when nothing is left); 37 of the lamp's items remain; its tests pass.
- M11 findings: the shop box is closed in MM9 (walls x 1536/2048, z 7250/7730 LT, ceiling `sturmtavernceiling` at
  y 7870), yet its front air is the street room 56 (mixed_faces.json: the ceiling 226 samples in 56, 124 in 61):
  a leak of the street air into the shop at the 16 LT voxels (the door's slice or a window), so the ceiling and the
  upper walls belong to the street sector and are not drawn from inside. Next: a `--plan` run with a voxel probe,
  then a seal (overrides `portals` slice) and Sturmford City alone reconverted after R1.
- 2026-11-05 20:30: Phase 3 done but C8 (the agent's report in this file). City/region sound triggers: overrides.yml
  `map: {ambient_triggers: true}` (dungeon/build.py) on Guberland City, the Sturmford and Thjorgard regions;
  Thjorgard's wall break hides PerceptionBrush6's hint. Not carried: Wizard's Lab's scripted super eye sounds and
  Closet1Door1's hint. Promotions corrected by the user (racial classes promote once, by tier-2 quests; no
  Necromancer). R1 started.
- 2026-11-05 18:35-19:52 R1: both review roots refreshed, all 44 maps converted, laid out and lightmap-transferred
  (scratchpad rebuild_all.sh; logs in the session scratch `rebuild/`). Two stops, fixed and rerun:
  lightmap_transfer.py `--install --root output/mm9_rework/isleofashes_blv_root` asserted (it knew only the main
  root; main() now points review_root at the isle root), and Dragon Stadium's WingedMutantCache (CacheOnly, now
  `monster_bases(cache_only=True)`). Lowest MM9 lightmap coverage: Mountain Pass 0 % (6 lightmapped polygons in its
  DAT), Drangheim City 22 % (56), the Drangheim region 65 %, Guberland 77 %: MM9 lights most of them per vertex,
  which stays vertex-lit. Load check: all 44 maps load headless and run 2 s with no Lua error.
- 2026-11-05 21:00: the 14 failing scenarios triaged, all pass. Engine: a mover's body rule no longer stops on the
  party's own floor (a plate or lift rising under it, a grate sliding away) or on a face the body is behind
  (game/indoor/IndoorMovers indoorMoverFaceBlocksBody, IndoorSceneRuntime applyMoverBodyRules; tests/IndoorMoversTests).
  Converter: klusossleeper.scr dormancy `trigger`, not `disturbed` (mm9_ai_placement.py); 1000 Terrors' genie lamp heal
  `AddValue(HP, ...)`; both maps reconverted with their lightmaps. The rest were scenario expectations against MM9's
  own behaviour (AITriggerable monsters reopening doors, ReopenOnContact, start-open closets, the swimmer fleeing a
  party on land): their generators fixed. Door and mover unit tests 384/384; MM6-MM8 tests/scenarios unchanged (8/9).
  Questions for the user in the session report.
- 2026-11-06 07:10 M11: Sturmford City reconverted with `corner_samples` (the shop ceiling in the shop's room 61;
  mixed faces over 20 % 570 -> 545, floor area under other rooms 150 668 -> 142 765 LT², dropped faces 280 unchanged;
  other houses' ceiling and wall pieces leave the street too), `lighting.py --layout-only --no-install` and
  `lightmap_transfer.py --install` (coverage 0.988); its four scenarios pass with no Lua errors; engine shots from
  inside the shop show the ceiling (session scratch `m11/shots/`). Other maps unchanged (the setting is off there).
