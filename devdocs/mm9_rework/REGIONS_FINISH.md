# MM9 maps: finishing the regions, Wizard's Lab, and the install (task file)

Task from the user, 2026-11-04 ("do what you recommend"), after the outdoor BLVs (OUTDOOR_BLV_ALL.md) and their props
(DECORATIONS_AND_GRASS.md): finish the MM9 maps. Order: the regions' people and map scripts, then Wizard's Lab (built
like the cities, user: "ok sure"), then installing every rebuilt map into the game. This file is the durable state.

## Rules

- AGENTS.md/CLAUDE.md. One heavy job at a time: never a game build beside a map conversion (out of memory, 2026-11-04);
  other sessions build too (`pgrep -f "^cmake --build build"` before converting).
- Map Lua is written by each map's converter (never edit generated Lua). A map's scripted objects become native Lua
  handlers, each citing its .scr, from a behaviour spec of every script (`work/scr_spec.md`), as the cities did
  (`mm9r_<city>/citylua.py`, CITY_PLAYBOOK.md).
- Posed figures stay out until the other session's NPC work is accepted (user, 2026-11-04).

## State at the start (2026-11-04 evening)

- 43 of 45 MM9 DATs rebuilt: 7 cities and 24 dungeons in `output/mm9_rework/assets_dev`, the 12 outdoor maps (11
  regions and Afterworld) in `output/mm9_rework/isleofashes_blv_root`. Great Gate skipped (an unused cutscene copy);
  Wizard's Lab not built. assets_dev still holds the old imports: nothing rebuilt is in the game yet.
- The regions place only MM9's monster classes: **no NPCs** (old imports had 1-27 per region, 99 with RUDE dialogue;
  Thronheim, Frosgard and Afterworld's old imports placed no actors) and **no map Lua** except the Isle of Ashes.
- Scripted objects on the regions (about 70 scripts; work list below): NPC dialogue scripts (npcNN.scr, shopkeepers,
  retainers, Forad, the Green Man), quest props (plough, doll, books, herbs, Atli's wagon), the mini-games of Thjorgard
  and Guberland (stones game, mastermind, whack-a-honky, boat race, arm wrestling, the bell), Boot Camp's tutorial
  (givetake, bootgive, bc_manager, bc_treasurechest), cutscene cameras (battlecam1, afterworldcam1), scripted monsters
  (jumper Yetis, Mountain Pass imp, the isle's), stat stones, locked doors (doorlock), Sturmford's destructon.

## Plan

1. **People on the regions** (shared, outdoor_blv.py): every NPC of a region's DAT as a friendly, immobile actor with
   its RUDE dialogue and MM9 body, as the cities place their townsfolk (old import record where there is one, else
   the DAT object's RUDE id). Shops work through RUDE.
2. **Map scripts, region by region**: a `regionlua.py` per region (pilot: Drangheim, small: four NPC scripts, the
   quest props, a locked door), then the rest; the mini-games and Boot Camp's tutorial last and largest.
3. **Wizard's Lab** as a city (CityHooks, daylight, sky; no terrain block).
4. **Install**: the rebuilt maps into assets_dev in place of the old imports, MM6-MM8 regression checks, scenarios.
5. **Engine features the maps need** (user, 2026-11-04): destructible walls and props with binding to map events
   (Lua triggers and observes destruction), if not there yet; check diving works; check and integrate what is missing
   of animated creature skins and skin swaps, pulsing lights, ambient sounds and lava damage. Not here: the monster
   AI (another session), walking NPCs and followers (after the real NPCs are in).

## Progress log

- 2026-11-04 18:40: plan written; starting step 1.
- 2026-11-04 19:30: step 1 code: `outdoor_blv.py` `npcs()` places every `DoRude 1` non-monster object (not CacheOnly)
  as a friendly immobile actor with its RUDE id (old import's record, else a stand-in peasant row and the DAT's RUDE
  id), MM9 body; ~108 people on the regions. Drangheim region rebuilt: 7 people with dialogue (Svein, Ivsar x2,
  Ragnheid, Hring, Tyock, Iosobail). The other regions get them with their next conversion.
- Engine audit (step 5): destructibles exist only on ODM (OutdoorDestructible, scene `destructibles`, trigger outputs,
  projectiles and melee, save state); BLVs have none, and Lua cannot trigger or observe a destruction. Diving works
  for the party (water_volumes, breath, drowning, underwater view; open: damage volumes and currents, Water Walk on a
  volume, more maps). Lava floors burn (FaceAttribute::Lava or lava textures); lava volumes do nothing (Drangheim
  Prison's Lava0: MM9 10). Missing: pulsing/flickering indoor lights (and GlowingLight objects are dropped),
  positional ambient sounds (no SoundFX handling, DecorationEntry.soundId unused), runtime skin swaps and animated
  creature skins (MM9_VISUAL_PROPERTIES gaps 2-3).
- 2026-11-04 20:30: step 2 base and pilot. `outdoor_blv.py` `map_script`: every region gets the shared doors (a new
  hooks flag `all_doors_click`: before, only doorway doors had click events, so no region door opened on a click),
  locked doors (MoveDist 0: "The door is locked."), keyed doors (`KEYED_DOORS` {group: item}, doorlock.scr), chests,
  ForadWorld.scr (location key 1024-1033, shop night key 5017 by a timer), one load event calling
  `handlers.regionLoad`, then the region's `regionlua.py` (`extend(hooks, build, script)`, optional
  `prop_events(build)` -> ({DAT name: click event}, {DAT name: SetSprite key}), `KEYED_DOORS`). Fixed
  `dungeon/lua.py`: a door named with a space ("cottage door") broke the whole map script (`lua_key`).
  Pilot: `mm9r_drangheim_blv/regionlua.py` (the promotion quest's plough, herbs and doll, the great book, Hring's,
  Ragnheid's and Tyock's rewards, the keyed door); converted, loads in game without errors.

- 2026-11-04 21:10: agent done: `regionlua.py` + `work/scr_spec.md` for Sturmford (hatch keys, ak_disable on-load
  drawbridge), Thronheim (Bikki), Frosgard (Green Man, Druid promotion), Lindisfarne (book sound, hired healer
  hidden), Yorwick (letters, Prop2, Mary, battlefield key 97 without the cutscene); events 330-334, SetSprite 400.
  Shared follow-ups it raised (not done yet): (1) MM9-locked swing doors with no key or unlock trigger open on a click
  (Sturmford RotatingDoor7/8, Lindisfarne BlacksmithDoor1/2, InnDoor1): treat them as locked, as the cities do;
  (2) `npcs()` should also place DoRude.scr objects (dialogue id = first script parameter; Lindisfarne's Monk0);
  (3) Sturmford's drawbridge and portcullis open on a plain click (MM9: chains and lever); (4) Sturmford's defences
  reward waits for BLV destructibles (the two chains destroyed + the portcullis).
- 2026-11-04 21:35: agent done: Guberland `regionlua.py` (Thorir, Ivan, the hag's hair, the Mercenary promotion with a
  timed guard stand-in and spawned bandits, tickets, the bell via evt.StopDoor, the runes by decoration swap, arm
  wrestling, Nicolai/Alvar); events 330-340, SetSprite 400-405, timers 600-602. Skipped: the stones game (no clickable
  squares or piece-size stones), whack-a-honky (no geese, props can't move from Lua), the opening conversation, walks.
  Shared follow-ups: `npcs()` places people whose dialogue id comes from their script (the hag NPC132 has no DoRude;
  the stones player gets id 0). Check after converting: the bell/runes sections exist only if Strikeplate1, Riser1 and
  Switch get click events.
- 2026-11-04 21:50: agent done: Bootcamp (Givetake/BootGive scrolls, Grandpa, key 473 on leaving), Afterworld (most of
  Skraelos' Six Fires: clicks 53094, greeting 56094, failure/guilt/confession/suffering/retribution/absolution, rebirth
  on leaving by ExitTrigger1, Forad Darre's death key 387), Mountain Pass (MountainPass.scr triggers by a poll);
  events 330-343, timers 600-601, SetSprite 400-413, extra hooks via `script.hooks` (map leave, monster killed).
  Shared follow-ups: (1) HIGH: Bootcamp's dock Trigger0 fires ExitTrigger0 far out at sea; transition
  `mm9:transition/bootcamp/217` uses ExitTrigger0's own box, so the party may be unable to leave: dungeon/tables.py
  should use the linked Trigger's volume; (2) Afterworld: ForadDarre0 not placed (add ForadDarre to
  monster_classes; row 9252); ExitTrigger1 is always open (MM9: only at key 390); the Hall of the Gods' `toAfterworld`
  still targets afterworld.odm; (3) found-player events (56000 + index) are raised only outdoors
  (OutdoorWorldRuntime::updateMm9FoundPlayerEvents): the BLV runtime should raise them too.
- 2026-11-04 22:00: agent done: Thjorgard `regionlua.py` (tickets and win rules, the stones game with a bot, the runes,
  the boat race by clicks, the bell, Hjarrand, the night robbers, the Magreeb ambush key 202); timers 300-301, clicks
  600-645, SetSprite 400-439. Skipped: whack-a-honky, arm wrestling, the training-hall wall (destructibles), jumpers.
  Shared follow-ups: (1) IMPORTANT: add `Magreeb` to Thjorgard's `monster_classes` (overrides.yml), else the Scholar
  promotion is blocked (check it does not attack: MM9's flees); (2) `npcs()` reads the stones player's dialogue id
  (428) from his script; (3) goose decoration + clickable Switch0; (4) the arm-wrestling captain as a friendly actor and
  click events for actors without a dialogue id; (5) normal-size yellow/blue stones; (6) toggleable FireCorrect flames.
- 2026-11-04 22:05: step 5 engine work in progress: BLV destructibles (devdocs/INDOOR_DESTRUCTIBLES.md: scene
  `destructibles`, IndoorWorldRuntime damage/destroy, melee on faces and decorations, party missiles on faces, Lua
  evt.DamageDestructible/DestroyDestructible/SetDestructibleDamage/IsDestructibleDestroyed, effects
  openyamm:fx/destructible/{stone,wood,glass,metal}, converter dungeon/destructibles.py, regions' BARRED_DOORS: Yorwick's
  gate); lava volumes burn the party (IndoorPartyRuntime).
- 2026-11-04 23:10: step 5 engine work (built and unit-tested up to destructibles + pulsing lights; ambient sounds,
  skinned flipbooks and indoor FoundPlayer written, building after the conversions):
  - BLV destructibles verified in Yorwick (desktop run: the gate board breaks, its death opens CTgate, board0 takes two
    hits; `destructible <id> destroy|damage <n>` console command; effects tuned by captures).
  - Lava volumes burn the party (IndoorPartyRuntime). Diving: works (no change).
  - Pulsing lights (devdocs/INDOOR_PULSING_LIGHTS.md): Wizard's Lab's 37 and the Lich Lab's GlowingLight.
  - Ambient sounds (devdocs/AMBIENT_SOUNDS.md): scene `ambient_sounds`, WorldAmbientSoundRuntime; 1214 of MM9's 1378
    placements have their file.
  - Animated creature skins: `openyamm_flipbook` now works on skinned materials (MM9_VISUAL_PROPERTIES gap 2 done).
  - Indoor MM9 FoundPlayer greetings (56000 + index), as outdoors: Bootcamp's Grandpa, Afterworld's Skraelos.
  - Shared converter fixes from the agents: `npcs()` places DoRude.scr / script-id people (Monk0, the hag, the stones
    player: `script_rude_id`); MM9 `Locked` doors with no key or unlock trigger say they are locked
    (`locked_models`); regions' `BARRED_DOORS`.
  - Not done: runtime skin swaps / node hiding (gap 3: Banshee decay, Ebora's sirens; waits for those creatures'
    3D work), Lua switching of ambient sounds, missiles on props, Magreeb in Thjorgard's monster_classes (hostility
    check needed), Bootcamp's exit trigger volume (tables.py), Afterworld ExitTrigger1 gating and ForadDarre0.
  - Reconversion of all 11 regions (pass 4) running with NPCs, scripts, destructibles, lights, sounds.
- 2026-11-04 23:40: step 3 drafted by an agent: `level_generation/projects/mm9r_wizardslab/` (convert.py, overrides.yml,
  citylua.py, README.md, work/scr_spec.md). Sky only through the tower top's five 0x10-flagged faces (retextured to the
  sky marker), city daylight, no terrain, swim on, 10 monster classes (ReverendMonk excluded: Robinssen, RUDE 55).
  Scripts: teleporters, the summoning ritual, the super eye, cell levers, Robinssen, letters/books/relic. Open: props
  need a props project (level_generation/props/mm9_wizardslab_claude/, Drangheim City route; the relic's DAT name
  "barrel"), the camera cutscene, six sounds not imported, the starfield-vs-daylight question, Robinssen's cage reach.
  Shared suggestions: structure.city_portals without street_top_lt, sky faces by flag in CityHooks, a shared
  teleporter helper, lua.Script.finish's fixed header. Conversion queued after the regions' checks.
- 2026-11-05 00:30: pass 4 done: all 11 regions reconverted (people, region scripts, destructibles, locked/barred
  doors, ambient sounds; Bootcamp's exit at the dock trigger), the build and 70 unit tests pass, every region loads in
  a desktop run with no Lua or scene errors. Wizard's Lab converted (16 sectors, 90 doors, 0 warnings; fix:
  dungeon/lights.py gives MM9's reused light names their DAT index) into output/mm9_rework/assets_dev; loads in game
  (start: the arrival portal corridor). Still without props (needs level_generation/props/mm9_wizardslab_claude/).
  Next: Wizard's Lab props and a walk-through of its scripts; step 4 install.
- 2026-11-05 00:50: Wizard's Lab sky: starfield at every hour (user: "definitely starfield"): new sky preset
  `night_stars` (always_dark with stars 1.0), city daylight off; reconverted, checked in game (tower top at 09:03:
  stars and the Milky Way).
- 2026-11-05 03:00: user play-test round. (1) Yorwick props break fine. (2) Sturmford chains could not be hit: they are
  invisible RayHit boxes; now a destructible's invisible faces take missiles and blows while it stands
  (destructibleFaceMask), the converter tags invisible brush faces (`TRIGGER_cog<N>i_`), event missiles damage too;
  Sturmford reconverted. (3) Lag: broken props no longer bump indoorLightRevision unless lit; destroyed faces update
  in place in the renderer (updateFaceAttributeChanges: 345 ms -> 1.5 ms); door clicks no longer invalidate the whole
  runtime geometry (only a door left standing still does); PathMap spatial grid built from one sorted list, huge
  facets kept out of the cells (the remaining 110-250 ms door-settle spike; measuring once the tree builds: another
  session's OutdoorWorldRuntime WIP breaks the build). Door-move render ~50-100 ms still open. (4) MM9 doors: RE
  (devdocs/mm9_rework/MM9_DOOR_OPEN_RE.md): the player opens doors only by Use; monsters open AITriggerable PushOpen
  doors by walking into them; TouchToOpen (7 doors + 14 WeightedLifts) opens on any contact (not done yet). City door
  sounds: the rebuilt scenes carry MM9's sounds (check whether the user ran the old import). (5) City windows: glass
  panes cannot carry a destructible cog yet (todo).
- 2026-11-05 01:10: built and checked: all 337 path/indoor/destructible tests pass; door settle on Sturmford now
  ~75-110 ms (was 170-280; path build ~50 ms, the rest the monsters' re-plans); breakable city windows work
  (Sturmford City reconverted: 29 destructibles, 26 glass panes; a pane vanishes in game). PathMap: huge facets
  (> 4096 cells) are tested by bounds instead of being listed per cell (a test pins cell-order ties for smaller ones).
  Next for the spike: build the path map off the main thread.

## Final plan (user, 2026-11-05)

1. Now: the door work (path map built off the main thread, TouchToOpen/ReopenOnContact doors and lifts, the
   drawbridge jump and the chains by arrow). No reconversions yet.
2. Wait for the monster work (session openyamm-cf; "almost entirely done"), consult it, then reconvert every MM9 map
   for good: complete props, complete NPCs and monsters (the new monsters), complete lighting including lightmaps
   (MM9's lightmaps transferred, or adapted/baked where their quality is low).
3. Install every rebuilt map into assets_dev: remove all old MM9 map imports, keep only the rebuilt ones.
4. Move everything from the MM9 review roots (output/mm9_rework/assets_dev, isleofashes_blv_root) into assets_dev:
   one place for the playable game, no other roots afterwards.
- 2026-11-05 01:50: openyamm-cf: every MM9 actor row has an approved 3D model (only triangle reductions still run;
  heights and bindings unchanged). Its one ask done: townsfolk/uniques/town animals in
  tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (118) are placed on 9000 + row (content.Content.actor), not the
  MM6-MM8 stand-ins. Tell openyamm-cf before the full reconversion (it drops to 3-4 agents for memory).
  Door work: monster path map rebuilt off the main thread (IndoorWorldRuntime m_pendingPathMap, adopted at the next AI
  update; door settle on Sturmford ~40-65 ms, mostly re-plans; tests pass). TouchToOpen left out: 14 WeightedLifts in
  1000 Terrors (built static) and Bathhouse Door3/4 (click) would need linear-door auto close and wall-touch triggers;
  ReopenOnContact already works on rotating doors.

Handoff for the next session: [HANDOFF_MAPS_FINAL.md](HANDOFF_MAPS_FINAL.md) (2026-11-05).
