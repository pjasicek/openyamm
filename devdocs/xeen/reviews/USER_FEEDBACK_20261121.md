# The user's play feedback, 2026-11-21 ~23:40 (Xeen, merge point 38)

Screenshots: `output/xeen_o4/feedback_20261121/<n>.png` (n as below). Positions are the game's debug readout
(`map`, `position=(x, y, z)`, `heading_degrees`, `pitch_degrees`).

**The user's rule for all of this (verbatim):** "these all are stuff you need to solve GENERICALLY, on the xeen world
GLOBAL level - I am 100% sure that any of these issues, the family/type of the issue IS NOT BOUND to that specific place
and location but is repeated across a LOT OF locations, dungeons, houses, and in general ... fix it STRUCTURALLY on all
similar sites." Every family below is fixed at its source (generator, kit, engine, common Lua, data) and then checked on
**every** Xeen map, house, NPC or dungeon of its kind, with a check that keeps it fixed (an audit rule, a build-time
refusal, a test). The reported spot is only the example.

## The reports, grouped into families

| F | Family | The user's example(s) |
| --- | --- | --- |
| F1 | **House screen lists the same person twice** (proprietor + the same NPC again as a resident) | Vertigo Town Hall: "Gunther, Mayor" and "Gunther" (2.png); Norman's Ironworks: "Norman, Blacksmith" and "Norman" (4.png); Chapel of the Crown: "Father Anselm" twice (14.png) |
| F2 | **Building doors**: a single leaf drawn as one half of a double opening (the other half blank wall), not centred over the stairs; should be one door or a proper double door, centred with the steps | Vertigo Town Hall door (3.png) |
| F3 | **Props at edges**: a barrel standing at/over an edge | Vertigo Meadows (-8369.7, 11561.0, 945.0), heading 129.9°, pitch 10.5° |
| F4 | **Monster projectiles spawn above the body** (doom bugs, "and maybe others") | Vertigo doom bug (5.png) |
| F5 | **No ground decorations** (grass, flowers, small plants) on Vertigo and Xeen's outdoor maps in general; MM6 New Sorpigal / Free Haven style expected | Vertigo Meadows |
| F6 | **Chests look wrong** (texture UVs or placement; not like a regular MM8 chest); check every Xeen chest | Vertigo Meadows (-17143.1, -17003.6, 769.0), heading 268.3°, pitch -38.0°; Mount Firestone chest that shows "The orcs' den" on hover (8.png) |
| F7 | **Guild / shop stock empty** | Water Guild of Vertigo (6.png), Earth Guild of Vertigo (7.png); "check also others in xeen" |
| F8 | **Cave mouths**: two extra rock wings beside the arch ("what are these?"); the entrance should be one mouth buried in the terrain with only the entrance sticking out; "can't go in?" | Mount Firestone (9884.7, -19592.4, 1834.2) h 232.9° p -25.9° and (9750.7, -20032.8, 1875.4) h 268.4° p -4.5° (can't go in); (5081.7, -13065.6, 2027.6) h 350.0° p 2.2° (9.png) |
| F9 | **Placed talking NPCs**: Sablewing the dragon hermit inspects as "Peasant", has a 3D peasant body, teaches a skill, can be killed (and the skill is then lost). Should be the right race/body (a dragon?) and unkillable like MM9's key NPCs | Mount Firestone (5805.9, -13621.1, 2040.6) h 12.4° p -25.1° |
| F10 | **Empty outdoor areas** ("ultra empty, no mobs in radius") | Mount Firestone (12816.2, -9159.9, 3486.0) h 129.5° p -13.8° |
| F11 | **Terrain material seams**: hard straight edge between two ground materials, no transition | Mount Firestone (15989.3, 2115.4, 3197.3) h 175.1° p -39.3° (10.png) |
| F12 | **Dungeon identity and exits**: "is this dungeon REALLY a dragon cave?"; a door with the wrong texture; a door whose click takes the party outside ("intended?"); lore text on an empty podium; exits should be the **black** MM6–MM8 dungeon exits, not the current exit look, "across the xeen" unless Xeen has something special | Dragon Cave (XD-18): (1251.5, -3103.8, 0) h 1.3° (theme); (1917.0, -3321.1, 0) h 269.2° (door texture); (2424.3, -3062.2, 0) h 357.7° (door → outside); (1914.5, -1883.7, 0) h 88.4° p -24.2° (empty podium lore); (715.4, -3047.1, 0) h 183.1° (exit look) |
| F13 | **Shrines, pedestals, wells, fountains open a dialogue screen**; MM6–MM8 just grant the buff with a status line | Shrine of Fire on Mount Firestone (11.png) |
| F14 | **Drops with no way back**: "if I jump in and don't have the Jump spell — am I stuck? reload?" | Robbers' Den (-69.8, 5332.4, -224.0) h 51.3° p -16.2° |
| F15 | **Quest items handed over by dialogue**: "The Robber Boss falls. A ring of heavy keys…" — just let me loot his corpse; the tiara: open the chest and loot it, the quest item placed in the chest | Robbers' Den (12.png, 13.png) |
| F16 | **Dungeon entrance prompts**: should be the normal MM6–MM8 dungeon entrance dialogue (the stairs icon at the top), not a scene picture with Yes/No | War Zone gate (15.png) |
| F17 | **Dungeons gated behind "you don't have item X" dialogues**: annoying; "some design session should solve this and like allow dungeon access to be able to fully clear the dungeons" | world-wide |
| F18 | **Town mirrors don't reflect** (asked earlier the same evening): A1 34th builds a `mirror` surface (merge point 39) | Vertigo's Magic Mirror (1.png) |

## How it is run (fourth orchestrator)

- One investigation-and-fix agent per family group, in parallel; each finds the cause, fixes it at the source, lists
  **every** affected site in the world, fixes them, and adds a check. Map edits take the per-map lock
  `flock output/xeen_locks/<stem>.lock` around edit → build → install → bake → tests, so two agents never rebuild one
  map at once. Engine changes go to A1 as exact specs (A1 is the only builder), batched into merge point 40.
- F17 (gating) and the dungeon-identity part of F12 go first to a design session (Opus), then to the lanes.
- Progress and answers: [ORCHESTRATOR_SESSION4.md](../ORCHESTRATOR_SESSION4.md) Log; each family's result is appended
  below when it lands.

## Results

(appended per family)

### F1 and F7: houses and shops (feedback agent, 2026-11-21 night, for A4 and A2)

**F7, empty guild shelves.**
- Cause: a guild sells only books of its own world (`ItemTable::spellbookItemIdForSpell`). Every MM6-MM8 book is
  flagged `World:mm6/7/8`, and Xeen had no books of its own, so all **29** built Xeen guilds sold nothing. That
  includes all four Vertigo guilds, Castleview, Sandcaster, Asp, Lakeside, Necropolis, Olympus, Shangri-La and the
  Darkside guilds. Merge point 34's pool filter is not involved: the 39 weapon, armour, magic and alchemist shops were
  all stocked (6, 8 or 12 items each). Taverns and temples have no stock in MM6-MM8.
- Fix at the source (A2): `source/items.yml` `spellbooks:`. `gen_items` writes Xeen's own book of each of the 99
  spells as ids 12901-12999. These are `World:xeen` copies of MM8's books 400-498 (MM8's books are the ones Xeen's
  maps place, D-2.2), with MM8's random-treasure weights. This is the MM9 precedent (LOOT_POOL.md: every world has its
  own books) and uses no new art (U-1).
- Each guild now sells as MM8 does: 12 slots per shelf, holding the first N spells of its school, where N is the town
  file's `guild: {spells: N}` (Vertigo 4, Castleview 7, ...).
- Side effect: Xeen chests and monsters now drop spellbooks at MM8's rates. Before, Xeen dropped no books at all.
- Checks:
  - `towns.py` errors when a built guild lacks a Xeen book for any spell its shelf sells. Before the fix: 29 errors;
    after: 0.
  - `towns.py --stock-scenario` writes `tests/scenarios/xeen/shop_stock.yml`. The scenario opens all 68 shops and
    guilds (107 stock screens) and fails on an empty one. It passes after the fix (5 s). Before the fix, the probe
    `output/xeen_fb/F1_F7/probe_all_before.log` showed 0 items at every guild.
- Captures:
  - before: the user's 6.png and 7.png;
  - after: `output/xeen_fb/F1_F7/cap/water_guild_stock_after.png` (Water Guild of Vertigo, 12 books) and
    `water_guild_lobby.png`.

**F1, a person listed twice.**
- Cause: A4's design. A proprietor who teaches, has topics or `talks: true` is written into `npc.txt` as a resident
  of his own house, so that his topics can be reached. The engine's house screen shows the house_data proprietor
  (portrait, "name, title", services) and also every resident NPC. In MM6-MM8 a proprietor never talks, so the engine
  tables have no such pair: 0 houses with the proprietor's portrait on a resident.
- Sites: **91** Xeen houses show the proprietor twice, in every town with services. Examples: Vertigo Town Hall,
  Norman's Ironworks, Lady Geraldine's Tavern, the Bank, Slime Temple, Thylon's, the Stables, Chapel of the Crown,
  the Throne Room, 13 guilds and the Olympus houses. The full list is in
  `output/xeen_fb/F1_F7/f1_sites.txt` (houses whose resident NPC has the proprietor's portrait).
- Fix: engine. Specified to A1 below. No data changes, so all 91 are fixed by the engine change.
- Checks:
  - `output/xeen_fb/F1_F7/house_proprietor_once.yml` fails today at Vertigo Town Hall ("dialog offers Gunther"). A1
    moves it to `tests/scenarios/xeen/` with the merge.
  - With the merge, `towns.py` `PROPRIETOR_TWIN_MERGED = True` and the scenario is regenerated.
- Captures: before, the user's 2.png, 4.png and 14.png. After: waits for A1.

**Spec to A1 (F1, merge point 40).**
- Where: `game/events/EventDialogContent.cpp`, in `buildEventDialogContent`'s HouseService branch and
  `collectSelectableResidentNpcIds`.
- Which resident: a resident NPC whose portrait id equals the house's non-zero `proprietorPictureId` is the
  proprietor himself.
- Lobby:
  - He is never a separate occupant portrait.
  - If he is the only selectable resident, the house opens straight to the proprietor's menu, as a house without
    residents does today.
  - Otherwise the occupant list is the proprietor portrait plus the other residents.
- The proprietor's menu: the house's service actions, followed by that NPC's topics. These are built as the NpcTalk
  branch builds them: canShowTopic, teacher topics with their labels, quest topics, and the topic's text and effect
  run as that NPC with `hostHouseId` set to the house. Greeting: the NPC's greeting where a talk would show it.
- MM6-MM9 impact: none in the MM6-MM8 tables (0 portrait matches; the three MM6 town-hall clerks have proprietor
  picture 0 and keep the resident-only lobby). A1 should confirm MM9's vendor houses.
- Test: the scenario above, plus a unit test over a house_data row and a resident NPC with the same portrait.

### F4: monster projectiles launched above the body (fourth-orchestrator agent F4/F9, 2026-11-21)

- **Cause.** A 3D-model monster without a `release` socket in `actors.yml` launches from its collision cylinder, not
  its model:
  - outdoors at max(24, 0.7 × height) (`OutdoorWorldRuntime::mapActorBodyLaunchPoint`);
  - indoors at 0.75 × height for a missile and 0.5 × height for a spell.

  The height is the descriptor's, and a Xeen family copies it from the stand-in sprites it borrows. The Doom Bug is a
  91-unit cricket that borrowed BDragonFly's 242, so its fire bolt started 169 units up, high above it. The aim point
  already uses the model (`actorTargetHeight`); the launch point does not. Shared engine code, so MM6–MM9 are exposed
  too.
- **Fix at the source.**
  - Data (A2): `source/monsters.yml` `height:` equals each drawn body's top: swarms 148 with the Doom Bug 91, night
    bats 52, air elementals 150. Regenerated with `--only gen_monsters`; only the 9 descriptor heights changed.
  - Engine (A1, F4-R1 below): the launch point follows the model the way the aim point does.
- **Sites.** `tools/xeen/check_actor_heights.py` measures every ranged Xeen row (136) against its model: its GLB bind
  pose × scale × scale_reference + z_offset, its sockets and its launch height.
  - 6 rows launched above their bodies: Doom Bug 11340 (169 over a 91 top), Insect Swarm 11341 and Stingers 11342
    (169 over 148), Whirlwind 11701 and Sleeper's Guardian of Air 11702 (168 over 148), Beholder Bat 11312 (62 over
    52). All 6 are fixed, and Night Bat A/B and Air Elemental A got the same body height.
  - The other 130 are fine: 104 launch from a socket, 26 launch inside their body.
  - Actors placed in a scene keep the height the scene was built with, until their map is rebuilt. The check warns
    for xeen_dd01, dd02, dd10a, dd10b, p2 and x3. X1 has already been rebuilt with the 91. F4-R1 fixes them before
    that.
- **MM6–MM9.** The same check with `--world mmN`:
  - MM6 ElemAir C (525, MMerge's Air Elemental): fault, launches at 168 over a 148 top. ElemAir A and B (523, 524) launch
    at 118, near the top.
  - MM7 Elemental Water A (244): borderline (126 over a 177 top).
  - MM8 and MM9: none.

  These rows are engine data; F4-R1 fixes them without data edits.
- **Check.** `python3 tools/xeen/check_actor_heights.py` exits 1 on any Xeen row that launches above its body. A new
  socketless ranged binding must pass it or get a `release` socket.
- **Captures.** Spawned at Vertigo Meadows and fired with `projectile actor last attack1 at_party`, in slow motion:
  - before: `output/xeen_fb/F4/before/*-fired.png`
  - after: `output/xeen_fb/F4/after/*-fired.png`
  - side by side: `output/xeen_fb/F4/before_after.png` (Doom Bug, Insect Swarm, Whirlwind, Beholder Bat)
  - the user's 5.png is the same fault as the before row.

**F4-R1 to A1 (merge point 40).**
- What: the body launch height of a bound 3D model is
  `min(collision height, drawn model top)`, computed as `actorTargetHeight` computes the model's top:
  `BoundClips::zOffset + bodyTop × referenceRatio × modelScale`, counted only while models are on.
- Where:
  - add `actorLaunchHeight(...)` beside `actorTargetHeight` in `game/maps/ActorModelManifest.cpp`;
  - outdoors, `OutdoorWorldRuntime::mapActorBodyLaunchPoint` uses it (it becomes a member, like
    `mapActorTargetHeight`);
  - indoors, `IndoorWorldRuntime.cpp` around line 7936 uses it in place of `collisionHeight × factor`.
- Release sockets are unchanged.
- MM6–MM9 impact: the four rows listed under MM6–MM9 above. MM6 ElemAir A/B/C launch at 104, not 118/118/168; MM7
  Elemental Water A at 124, not 126. MM8 and MM9 are unchanged.
- Test: a unit test of the helper, and a headless check that MM6's Air Elemental C bolt starts at most 0.7 × 148
  above its feet.

### F9: placed talking NPCs as killable "Peasants" (agent F4/F9, 2026-11-21)

- **Cause.** Each map lane places a talking NPC on any monster row; the generic peasant rows (350–377) are the cheap
  pick.
  - **Name.** `ActorNameResolver` names an actor by its placed name, then its row's name ("Peasant"). MM6–MM8 (and
    OpenEnroth's `Actor::GetDisplayName`) name an actor with an NPC id by its NPC. Engine fault, F9-R2.
  - **Death.** Only maps whose lanes added `SetMm9ActorCanReceiveDamage` by hand protected anyone (Corak, Randon, the
    P5 couple: 9 maps, by actor index).
  - **Body.** Sablewing's portrait (npc14720) is a gold dragon, but X7 placed him on peasant row 368.
- **Fix at the source.**
  - Unkillable world-wide: `tools/xeen/key_npcs.py --write` reads the installed scenes and writes
    `events/common/xeen_key_npcs.lua` (generated; the world's common Lua loads it on every map).
    - It covers every placed figure: an NPC id, or a `characters:` row.
    - A global load event and a 1-second timer apply `SetMm9ActorCanReceiveDamage(actor, hostile)`.
    - A peaceful figure takes no damage from blows, missiles, spells or areas, and no hit turns it hostile.
    - A figure its own story turns hostile can be fought: Yog's "Battle!", Graalg's, Hobstadt's and the People's
      relation rules, the Master Thief.
    - The 9 maps' own per-index calls are now redundant; their lanes may drop them.
  - Sablewing has his own row: character 11927 "Sablewing" on MM6's Gold Dragon (A2). S binds it on `xeen_cdr1` skin
    `cdr1_c`, about 245 tall, and X7's `places.py` places him on it (map lane; X7 rebuild below).
  - Names: F9-R2 to A1 (below). It fixes the 25 NPC actors on generic rows, and MM6–MM8's own.
- **Sites (71 placed figures on 32 maps; `key_npcs.py --list`).**
  - 48 actors have NPC ids; 23 are character rows without one (Crodo, the DD-09/DD-20 prisoners, the Voweless Knights,
    Slick, the griffin and others). All 71 are protected.
  - Names: 46 already show their own name (own rows, trees, ghost, druidess). 25 show "Peasant" until F9-R2: Derek,
    Orothin, the Spring Druid, 4 Plague Cult members and Celia (X1); Danulf (X2); Mirabeth (X3); Adam, Eve, Joe the
    Merchant and the Autumn Druid (X4); Randon and Freeda (X5); Arie, Saul and the Summer Druid (X6); Sablewing (X7,
    fixed by his own row); Joe and Justine (D1); Cornelius (D3); Naomi and Ector (D4).
  - Bodies against the portraits:
    - Sablewing: fixed.
    - The Autumn Druid (4321, a woman) stands on a male peasant, and the Winter Druid (4529, a bearded man) on
      Druidess A. X4's and X5's generators call them "his" and "her", so either the bodies or the portraits are
      swapped (DECIDE).
    - The rest match: Mirabeth the mermaid and Asp's scaled Adam and Eve on human peasants, Cornelius the leprechaun on
      a man, Danulf the faery king on a man (an elf body would read better).
- **Check.** `python3 tools/xeen/key_npcs.py` exits 1 on any of these:
  - the Lua list no longer matches the installed scenes (run `--write` after any map install);
  - a figure that cannot show its own name even with F9-R2;
  - a body that breaks the audited expectations.

  The scenario `tests/scenarios/xeen/key_npcs_unkillable.yml` passes on X1's Derek, who has no map event of his own:
  - 30 blows (13 hits, 0 applied) and a Fireball leave his 6 HP whole;
  - he stays peaceful and still talks.
- **Captures.** Sablewing before: `output/xeen_fb/F9/shots/sablewing_before.png` (a peasant at the cave mouth).
- **Sablewing on X7: installed with its bake at 00:15:05 (2026-11-22)** by `output/xeen_fb/F9/x7_job.sh` under `xeen_x7.lock`
  and `bake.lock`. The scene places actor 10 on row 11927 with height 245. `key_npcs.py --write` was rerun and its
  check passes (0 errors).
  - The X7 hostility test passes 2/2.
  - `playtest.yml` fails 2/2 at step 67, the XD-05 back gate (event 41 no longer moves the party). This is not from
    Sablewing, whose change is one monster id: the same build's audit reports `entrance.question` errors on events 38
    and 40. This is most likely the entrance-prompt work (F16) on X7.
  - After capture: `output/xeen_fb/F9/shots/sablewing_after.png`. The gold dragon stands at the cave mouth where the
    peasant stood.

**F9-R2 to A1 (merge point 40).**
- What: in `game/data/ActorNameResolver.cpp`, `resolveMapDeltaActorName` returns, for an actor with an NPC id and no
  placed name, the NPC's name as its dialogue title shows it ("Derek, Ranger"). This goes after `uniqueNameIndex`
  and before the row's display name. It needs the NPC table (pass it in, or resolve in the callers that have it:
  `OutdoorWorldRuntime.cpp:2910`, `IndoorWorldRuntime.cpp:3324/17232/21211`, `IndoorRenderer.cpp:588`,
  `MapAssetLoader.cpp:3124`).
- MM6–MM9 impact: every MM6–MM8 placed NPC actor on a peasant row shows its own name instead of "Peasant", as in the
  original games. MM9's RUDE people already show theirs.
- Test: the scenario above, with an assert that actor 75's name is Derek.

### F13, F15, F16 (interactions; feedback-fix agent, 2026-11-21 night, acting for A3 and the map lanes)

**F13, touch effects in a window. Cause:** a quest hook's text was always `evt.SimpleMessage` (a window) unless the
hook said `status: true`; the Shrine of Fire, the wells, fountains, thrones, brews, scrolls and the planes' sources
were all written without it. The studio's own `text:` already goes to the status line; some maps wrote
`evt.SimpleMessage` in their own `lua:` beside the buff.
**Fix at the source:** `gen_quests.py` writes a `status: true` hook's line held by its length (the studio's
statusLine rule, `evt.StatusText(text, seconds)`), `XeenQuests.statusLine` does the same for else/fail lines;
QUESTS_FORMAT.md §7 states the rule (touch effects `status: true`, `window: "<why>"` only for a long text or a
choice's answer). **Check:** `tools/xeen/quests.py` `check_touch_sites`: a hook that gives a party effect itself or is
called from a map event that gives one (read from the installed map Lua) must say `status: true` or `window: <why>`;
a map event that gives a party effect and opens its own window is an error (the 41 sites below are listed as open
until their maps are rebuilt; any new one is an error).
**Sites (129 found):**
- **88 hooks fixed** (source files in `source/quests/`, `source/npcs/`; `xeen_quests.lua` regenerated): status line on
  D5's shrine, Fountains of Might and Energy, Last Water, munchies; D6's Books of the Dead; DD-18's brews and members
  line; M17's sorcerer book; M29's alien device; M33's power juice; the planes' font, geode, singing stones, tide
  pool; Q-C8's 13 scrolls; Q-C9's four thrones; Q-D10's dark water and kettle drink; Q-D13's troll juice; Q-D14's two
  potions; Q-D17's emotion thrones and euphoria; Q-D18's fantastic book, fountain, minimal fountain; Q-D19's Prince
  Book and Manual; Q-D22's cauldrons; Q-D23's dead food; Q-D6's four fountains; Q-F1's potion, well, tome, crystals;
  X6's sun stones and caravan cairn; X7's Shrine of Fire and Well of Speed (11.png); X8's explorer statue (each with
  its "again" line). **Kept as windows with a reason (19):** M17's book's cost (276 characters), the Dragon's three
  visions (Q-F1 balls, 200+), the seven vowelless books' answers (a riddle asked first), Wardoz's four scarabs and the
  genie's three angry answers (a choice's answer).
- **41 map events, left for their map lanes** (each writes `evt.SimpleMessage` in its own `lua:` beside the stat;
  the fix is `evt.StatusText(text, seconds)` in its generator, then a Lua-only install): DD-02 book_elec, book_fire;
  DD-03 knights_brew, queens_brew; DD-09 fountain_air/body/fire/water; DD-12 cage1-3, 5-7; X4 quintain,
  standing_stone, crest_cairn_w, crest_wind_stone; XD-06 yak_pool; XD-07 black_liquid, well; XD-08 the seven juices;
  XD-11 the six brews; XD-12 the six stat books; XD-13 well. Not done here: eleven rebuilds with different toolchains
  (dress.py, hand L4) did not fit this session; `quests.py --open` lists them.
**Tests:** about 100 dialog asserts on these lines turned into status-line checks (`status()`) in the side quests,
the hook scenarios and the L4 playtests; `quest_stub.py` 19/19.

**F15, quest items handed over by message. Cause:** chests whose hook gave the item by script
(`AddValue(InventoryItem)`) with a window, which also closed the chest (XD-21's strongbox had been made to run the hook
alone on its first click for that reason). The Robber Boss already carried the ring of keys as corpse loot
(`carries: ring_of_keys`); only his death line was a window.
**Fix at the source:** a chest's quest item is the chest's item (`objects.yml` `items:`), the hook says `map_gives`
(no `gives`), runs after `OpenChest` and only sets its bit (or a status line); a monster's quest item is its
`carries:`. QUESTS_FORMAT.md §7 says so. **Check:** the audit's item rule counts `map_gives` as given; no new
`gives:` hook at a chest passes review (no automatic refusal yet: see DECIDE).
**Sites:** 55 hooks give items. **Chests (7): 6 converted and installed** (scene, studio and Lua only; BLVs byte for
byte; MAW reserves rerun): XD-21 the tiara (13.png) and the Robber Boss's line on the status line (12.png); XD-06 the
Elixir; XD-11 the Skeleton Key; DD-20 the Necropolis pass; DD-06 the Eastern Tower key (after the password); XD-01
Joe's invoice (its text stays a window over the open crate: a note to read). **Left (1):** X2's sorceresses' strongbox
(an outdoor `crate` with an ambush; the sketch's `chest: {items: [12152]}` and an outdoor rebuild, A5).
**Monsters:** all quest items monsters hold are already `carries` (XD-21 ring of keys, XD-03 clan king key, XD-06
Megacredit, XD-11 librarian key, XD-27 larder key); none given by a death script. **Not chests (47):** finds at a spot
(nests, rubble, alcoves, a rack, a desk, the planes' gems, booths, prompts answered), left as scripted finds (DECIDE).
**Tests:** Q-C3, Q-C12, Q-D19 side quests, segments 17 and 55, XD-21's and DD-06's playtests, the stub (`give:` steps).

**F16, dungeon entrances as a scene picture with Yes/No. Cause:** every Xeen move into a BLV writes
`MoveToMap(..., 0, 0, map)` (D-24/D-72: move at once, or the map's own question first), so the engine's entrance window
never shows; 12 ODM entrances (X6's War Zone gate, 15.png) and 32 BLV-to-BLV ways ask their own Yes/No. The engine
shows the MM6–MM8 window (the map's name, the Ticon picture, "Do you wish to enter X?", OK/Close) for any MoveToMap
with a non-zero picture, in every direction. **Fix:** needs the studio (outdoors `screen` requires a house id;
`leave` ignores `screen`): spec to A1 below. No map changed; 133 entrances listed (70 ODM→BLV in 12 outdoor maps, 61
BLV→BLV), exits unchanged. After A1's change every map is rebuilt Lua-only and the map lanes drop the 44 Yes/No
prompts; test steps `answer_input: Yes` become `select_topic: {match_label: "OK"}` (already used at XD-21's exit).

**Runs (F13/F15, 23:00):** main chain 01–99 pass except 21 (XD-07, rebuilt at 22:52 by another lane: the walk sticks
at (1099, 3291) near actor 4; passed at 22:40 before that install); promotions 81 and 89 pass; side quests 70 of 71
pass (q-f1 sticks walking in FD-04, rebuilt at 22:55 by another lane, after every F13 step); hook scenarios pass
except `hooks_fd02` (m40's chair window, not changed here) and `hooks_fd03` (the roof hatch open before P5, not
changed here); the L4 playtests of DD-02/05/06/07/08/09/11B/16/18/19/20, XD-01/06/10/11/13/14/15/21 pass.
`quests.py` 0 errors (52 open), `build_world.py --check` clean, `xeen_balance.py --check` clean. Bakes: the chest items
changed four scenes, so XD-21, XD-06, XD-11 and DD-20 read stale; their rebakes are queued behind the program's bake
lock (`output/xeen_fb/f13_f15_f16/bake4.sh` installs each and logs to `bake4.txt`). Before: the user's 11.png, 12.png,
13.png, 15.png; no after captures (the checks are the scenarios' status-line and loot asserts).

### F2 and F8: building doors and cave mouths (feedback-fix agent, 2026-11-21 night, for A6 and the map lanes A5/A6)

**F2 cause.** Xeen's houses use shipped house-door pictures that are one wing of a double door: MM7's rich kit door
`7hhr1d2` (the studio's kit table, Vertigo Town Hall), MM8's `t06a03`/`t06b03` (D1, D4 boulder houses), `t09a03a` (D1,
D4, D6 ashlar services) and `t07b03c` (D3 Sandcaster). Hung alone on a 128 bay they show half a door beside blank wall
(3.png: the door bay *was* centred on the steps, the picture's leaf is not). The texture classes did not know these as
wings, so `oymap audit`'s door check (and its 192-wide half-wing rule) never saw them; two D6 doors were pairs squeezed
into one 128 bay (64-wide leaves).

**F2 fix at the source.** `tools/xeen/house_doors.py` (A6's kits, used by every outdoor generator): `double_doors_sketch`
turns every door whose picture is a wing into a double door: `leaves: 2` on a 256 bay in the middle of the door's wall
(each leaf 128, the left wing, the second mirrored), the wall's other bays listed round it in 128 panels (window by the
door, post at the end), a window over the pair's middle above. Hooked into X1, D1, D4, D6 (and D3, X6, X7 for F8). Kits
with a single door of their own use it instead: D3's adobe kit `t07a03a`; D1's gremlin burrow `hhp1d`; D3's stall
`tentdor7a` (the 128 version of the 256-wide `tentdor7`). 16 shipped wings registered as twins in
`tools/xeen/texture_classes_overrides.yml` (7hhr1d1/2, t06a03/b03, t06c03/d03, t07a03c/d, t07b03c/d, t07c03c/d,
t09a03a/b); `texture_classes.py` rerun (measure dir `output/xeen_a1/fit/measure`; other diffs only new textures).

**F2 check.** `tools/xeen/door_check.py <stem | built .odm>` (in `output/xeen_fb/f2/pipe.sh`'s build step):
`doors.lone_wing` (a wing with no leaf beside it), `doors.part_picture` (a door picture shown < 0.75 across its leaf),
`doors.narrow_pair` (a pair < 192 wide), `doors.off_steps` (a door > 32 off the middle of `..._steps` before it). The
same rules in `oymap audit` are A1's (REQUESTS). Shipped calibration (`output/xeen_fb/f2/shipped/`): 166 paired wing
leaves; lone wings 96+ wide: 5 (MM8 elemf `gnecdr4l` x4, MM7 7out02 `hhm1d2` x1).

**F2 sites** (door_check on the installed maps; before: `output/xeen_fb/f2/before/door_check.txt`, sketch inventory
`before/inventory.txt`, 339 house doors):

| Map | Before | After | What |
| --- | --- | --- | --- |
| X1 | 1 | 0 | Vertigo Town Hall: 7hhr1d1 pair on the tower, centred on the steps (+0) |
| D1 | 35 | 0 (build) | 29 houses/services t06/t09 pairs, 4 drawkcab, the gremlin burrow (hhp1d) |
| D3 | 11 | 0 (build) | 10 adobe houses (t07a03a single), the second stall (tentdor7a) |
| D4 | 12 | 0 (build) | 11 houses/shops t06 pairs (the guild already a pair) |
| D6 | 5 | 0 (build) | market, embalmer, tavern pairs; guild and temple pairs widened from 128 to 256 |
| X6 | 4 | 4 | the Sphinxes' `egydrlgl` (256 wide) shows half per leaf: needs A1 (REQUESTS 2) |
| X2-X5, X7, D2, D5 | 0 | 0 | single doors or proper pairs; D6's Alamar blast doors (one `swdoora` split half and half) pass |
| X8, X9, D7 (BLV) | 0 | 0 | `oymap audit --doors` |

**F8 cause.** The studio's `cave_mouth` is a shell as wide as its footprint (1024; X5 and XD-18 1536) round a mouth of
256-768: the shell between the rim and the footprint's sides is the two rock "wings", and the land under the
footprint's side edges is pulled to the floor (`shapeOutdoorCaveLand`), so no hill can hide them. "Can't go in?" at
(9750.7, -20032.8): that is X7's `thing:orc_den` (the gate pickets' den, F6's "The orcs' den" chest in front of it), a
cave mouth with no `into`: a dark entrance that leads nowhere and said nothing; Sablewing's cave (9.png) and the miner's
adit the same.

**F8 fix.** `house_doors.bury_mouths_sketch`: a mouth into a hill (not `free`) is only as wide as its mouth and a rim of
64, so the hill beside it covers the shell's sides; `blind_mouths_sketch`: a mouth with no `into` says so when clicked
("The cave ends a few paces in, in bare rock. There is no way on."); a rock back a short way in was tried and read as a
solid lump (`output/xeen_fb/f2/caps/x7_compare1.jpg`). Barrows on level land (`free`: X3's tomb, X5's warren, X6's den)
stay mounds. Check: `door_check.py --sketch <sketch.yml>`: `caves.wings`, `caves.blind_mouth`. The dome over a mouth
whose hill is lower than its crest still shows (XD-18): the land round the shell is the studio's (REQUESTS 3).

**F8 sites** (15 cave mouths on 9 maps; every real entrance is in its map's walk playtest):

| Map | Mouth | Way in | State |
| --- | --- | --- | --- |
| X7 | Sablewing's cave, orc den, miner's adit | none | prepared and previewed (bury + click lines), not installed: the X7 lock was held by F9's job (NEXT) |
| X7 | XD-16, XD-17 cleft, XD-18 | yes | prepared and previewed (bury + click lines), not installed: the X7 lock was held by F9's job (NEXT) |
| D4 | DD-23 lair | yes | narrowed 1024 -> 640, installed 0 (build)_TIME |
| D6 | DD-10C adit | yes | narrowed 1024 -> 640, installed 0 (build)_TIME |
| X6 | werewolves' den (free) | none | click line, built; install by the finisher |
| X1 | Red Dwarf Mines, Orc Caves | yes | not rebuilt (NEXT) |
| X2 | Ogre Lair | yes | not rebuilt (NEXT) |
| X4 | Gargoyle Eyrie | yes | not rebuilt (NEXT) |
| X5 | Cave of Illusion north and south | yes | not rebuilt (NEXT); the warren (free) unchanged |
| X3 | Tomb (free, door form) | yes | unchanged |

Captures: `output/xeen_fb/f2/caps/` (`x1_before/`, `x1_after/`, `d1_before/`, `d6_before/`, `*_after/`, `x7_before/`,
`x7_preview/`, `sheet_before*.jpg`, `x7_compare1.jpg`). Pipeline: `output/xeen_fb/f2/pipe.sh`, logs `output/xeen_fb/f2/run/`.

State at the agent's stop (about 23:30): X1 installed with its bake 22:58, walk and hostility pass. D1, D4, D6, D3 and X6 built and checked (audit 0 errors, door_check 0 except X6's Sphinxes), their installs with bakes, walk and hostility runs and the after-shots are done by the detached `output/xeen_fb/f2/finish.sh` (the bake queue had 9 waiters), which releases each map's lock when done; its log `output/xeen_fb/f2/run/finish.log` ends with FINISHED.

### F12 (exits, doors, lore) and F14 (drops), 2026-11-21 ~23:50-, agent `xeen-fb-f12` (fourth orchestrator)

Scratch `output/xeen_fb/f12_f14/` (`tools/cycle.sh <key>` the whole per-map cycle under the map lock, `run/<key>/` its
logs: steps, snapshot of L4 and installed files, L4 diff, audits before/after, bake, MAW, tests; `queue.out` one line
per map; `spec.json` the edits).

**F12(a) black exits.** Cause: every exit face of the studio was given a picture by its map's generator: daylight views
(`xodaylt`, `xddaylt`, `xdcraglt`, `sky_clo1`, `snow`, rock), or a door picture (the studio's exit surface defaults to
the room's door surface). MM7 and MM8 draw nearly every dungeon exit as a black face (7solid01 in 51 of MM7's 100 exit
faces, solid01 in 28 of MM8's 61; measured with `oymap things` over every shipped BLV). Fix at the source: each map's
generator (68 items in 45 scripts, `gen_patch_result.txt`; xd01, xd02, xd03, xd04 and xd20 have no live generator,
their L4 is the source) and the L4 (`objects.yml` exits' `surface.texture: 7solid01`); the shut double doors that are
exits (DD-08's gate, DD-15's green doors) show 7solid01 on their front. Check: `tools/xeen/check_exits.py`
(`exits.not_black`, `exits.door_leaf`, a SPECIAL list with one reason a line). Special exits kept: ladders (DD-01
hatch, DD-18 and DD-20 shafts), DD-01's outfall grate, DD-26's grate, XD-01's river, XD-04's cloud stair, P1's way up,
the sky falls of the open-air maps (D7, P2, P5, X8, X9: cloud floor at z -6000), XD-07's old throne, the doors into a
tower from an open-air map (X9 Dragon Tower, P5 Darkstone Tower, already black).

**F12(b) door textures.** Audit of every clicked door leaf of the 69 BLVs against the texture classes
(`texture_classes.yml` `door`): 170 door events whose leaf picture has no door class; most are by design (secret
walls, cages, webs, boulders, hides, bars). Doors titled as doors with a non-door leaf: plank-strip leaves (7trimd 27,
trim9_32 9, bemvwal 7, 7trimda 5, trim9_32a 3) and stone slabs after the Temple of the Moon (twb1 in DD-20 x7 and
XD-04 x2, twb1a DD-14 x2, t4s1fl XD-06, egywle XD-15 x3): left as built, DECIDE. The reported Dragon Cave door
(1917, -3321, h 269) is the Dragon Tax Office's house door (gkp103a|gkp103b, the dungeon's own door pair): no fault
found in its texture; the user should say what is wrong with it.

**F12(c) doors that lead outside.** Every door-looking face whose click leaves: 46 exit panels with a door picture
(now black, list in `exits_before.txt`), DD-08's gate and DD-15's green doors (black), and XD-18's inner door, the tax
throw (D-57 Q2, D-63 4): kept, F17's design session.

**F12(d) lore on empty stands.** 98 clicked platforms whose text names a thing on them (`podiums_flagged.txt`); 20
lecterns, desks and stands whose top is plain wood or stone while the text speaks of a book, ledger, note or scroll
(`tops_deferred.json`). XD-18's lectern (Dragon Lore 1) and ledger stand now show the open book `xnpbook` (128 x 128 on
the 128 grid). The other 18 wait for A1: the studio's `fit` does not reach a platform's `top_surface`
(`textures.feature_cut` on a fitted 96 x 160 top), REQUEST below.

**F14 drops.** `tools/xeen/check_drops.py <map.blv>`: floors of the built map, joined where their outlines touch, the
party's step up 50 and any drop, ladders joined; a pocket reached from the start but not left on foot is reported with
its depth and any exit, teleport, lever or lift in it. Before: 44 pockets in 29 maps (`drops2_before/`). Fixed:
Robbers' Den (the race in the sluice and the undercroft, 224 deep, the quay drain 96) and Dragon Cave's steaming pool
(64) with ladders (the studio's `ladders`, in the generators too). Left (REQUESTS to A7/A8): the liquid channels of
DD-01 (4), DD-16 (lava), DD-18, DD-20 (3), XD-01, XD-06, XD-10, XD-11 (lava), XD-12; the dry pits and ledges to check by
hand (DD-05, DD-14, DD-22, FD-03, FD-04, XD-08 x2, XD-10, XD-15, XD-25); the large pockets that are one-way drops by
design or reached by lifts the check does not ride (DD-14, DD-19, DD-21, FD-01, FD-02, FD-04, XD-02, XD-03, XD-05,
XD-09, XD-17). Outdoor pits not covered (ODM).

**State at the agent's stop (about 23:35, context limit).** Two background jobs keep running, started by this agent:
`output/xeen_fb/f12_f14/tools/queue.sh` (pid in `queue.pid`; each map's cycle under its map lock: edit, build, install
from a private root, audits, MAW reserve and `xeen_balance.py --check`, playtests 4 times; one line a map in
`queue.out`, "queue done" at the end) and `tools/bake_worker.sh` (`bake_worker.pid`; bakes each installed map from
`bake_todo.txt` under the map lock and `bake.lock`, `bake.out`). The bake lock was held by A5's outdoor bakes, so bakes
lag the installs: `stale_bakes.py --check` is not 0 until the worker is done. Done when this was written: DD-03, DD-04,
DD-05, DD-06, DD-07, DD-10A-C, DD-11B, DD-11C, DD-12 installed (tests 4 of 4 except DD-05, DD-06 and DD-07, which fail
on lines of other families' concurrent hook changes: DD-05 a fountain no longer opens a dialog (F13), DD-06 "no
Eastern Tower key", DD-07 Ellinger's letter dialog (F15); not the exits). DD-08 and DD-09 installed, tests not run
(`tools/tests_one.sh dd08`, `dd09`). Refused by the baseline gate (the L4 as found does not build to the installed
map; somebody's change not installed): DD-02 (only actor heights, now accepted: rerun `tools/cycle.sh dd02`),
DD-11A and DD-13 (BLV differs: their lanes first). DD-14 nothing to do (its tops wait). XD-18 is last in the queue
(black exit, the two book tops, the pool ladder); XD-21 (ladders) in the queue.

### F5 and F11: ground plants and terrain material seams (feedback-fix agent for A6/A5, 2026-11-21 ~23:20)

**F11 cause.** Not a missing blend: X7 and D6 gave their ash (`wasteland`) and edge cinder (`edgedirt`) the same
`reference_tile` (`6voltyl`). `tools/terrain_materials.py` splits a transition tile's pixels between its two materials by
those colours, so every `7wstdrt*` tile split 0/0 (NaN); the edge blur spread the NaN and the PNG stored zero weights
(X7 443,376 texels, D6 975,312). A texel with no weight draws one layer unblended, so where zero weights met real ones
the ground changed in a straight line along a cell edge (the user's spot is exactly the row 957/958 boundary). A
second, milder kind: D3's spring pool, a BModel water face whose floor sand ended in a straight line at the face's
edge (14 texels), and the same at small pools on X1 and D1.
**F11 fix at the source** (`tools/terrain_materials.py`): transition tiles are split by the world's own materials'
colours, never a map's look override (X5's ice edges are now split by the sand tile, not `7snow`); `weights` refuses
two materials of one colour and any texel whose weights do not sum to one; a water face's floor sand blends out over
the edge softness. **Check:** `tools/terrain_materials.py check --world <world> [--map ...]` (each texel sums to one;
no straight run of hard switches, both texels at 0.9+ of different layers, longer than 4 texels); A5's
`terrain_swap.sh` runs it before every swap, so no Xeen install can swap such weights in. MM6, MM7, MM8, MM9 and every
Xeen map pass; MM7 7out01 and MM8 out06 regenerate byte-identical.

**F5 cause.** Xeen had no `worlds/xeen/terrain_decorations/` at all: the engine grows plants only from a per-map
decoration file, MM6-MM8's were written once by `decoration_rollout/`, and nothing in the studio or the Xeen install
chain wrote one. **Fix at the source:** a hand-written `assets_dev/worlds/xeen/terrain_decorations/plants.yml` (what
grows on each ground material, per map; MM7's plant families, since Xeen stands on MM7's tiles) and
`tools/terrain_materials.py plants`, which `weights` also runs: one rule per tile and growing material, transition masks
from the same colour split as the weights (96-99 % agreement with MM7's reviewed masks), no plants on the water part of
shore tiles, grass tints times the map's ground shade. `terrain_swap.sh` swaps the files, so every later rebuild of a
Xeen outdoor map keeps its plants (X1, X2, X3, X4 and X7 were in fact re-weighted by other lanes' installs with the
new tool while this ran). Biomes: X1 New Sorpigal's meadow (density 1, near 3072, tall 0.12); X2 Free Haven's
(0.75); X3 woodland grass and reed beds; X4 dry meadow, dead tufts on the waste; X6 and D5 sparse dry tufts on sand,
dead tufts on cracked ground; D1 dry meadow, D2-D4 woodland grass under their darker Darkside shades, D3's sands
dry tufts; X5 (snow, ice), X7 and D6 (ash, cinder, lava) none, with the reason in their files. Open-air BLVs: only
XD-17 Shangri-La has terrain ground: its grass file is written and `xd17/tools/gen.py` names it (atmosphere
`ground.grass`); X8, X9, D7, P1-P5 have no terrain ground.
**Cost:** X1's town meadow, visible runs grass off/on: GPU p50 3955 -> 4170 us, render_world CPU 800 -> 879 us.

**Sites:** 13 outdoor ODMs + 1 open-air BLV with ground. Weights: X7, D6 (NaN), D3 (pool line) fixed and installed;
X5 re-split; X1, X2, X3, X4, X6, D2, D5 regenerated (no seam); D1 (two pool lines, 3 texels, under the check's limit)
and D4 wait for F2's locks (see below). Plants installed: X1-X7, D2, D3, D5, D6 (X5, X7, D6 disabled by design).
**Captures** (`output/xeen_fb/f5_f11/cap/`): `sheet_xeen_x7_seam.jpg` (the user's pose before/after),
`sheet_xeen_x1.jpg`, `sheet_xeen_x3.jpg`, `sheet_xeen_x6.jpg`, `sheet_xeen_d5.jpg` (before left, after right).
Docs: `level_generation/terrain/MEADOW.md` "Plants by material", `level_generation/terrain/materials/README.md` step 2.

### F6 (chests) and F3 (props at edges): feedback-fix agent, 2026-11-21 ~22:30–23:40

**Cause.**
- **F6 look.** Outdoors the studio's chest (`OutdoorThings::raiseChest`) is a 9-face box with one plank picture
  (`7gt002a`) tiled over all four sides and `7gt002b` over the lid. The shipped MM7/MM8 chest (7out01 `chest_N`,
  out02 `chest_S`) is 19 faces: sides cut end 16, middle 64, end 16 (`b a b`), ends `c` with a `g` strip, lid
  slopes `b e b` / `b a b`. Indoors the studio already lays the shipped faces (`chestKindOf`, `addChestFaces`), so
  every outdoor chest was affected: 86 on X1–X7 and D1–D6, now 90 with other lanes' additions. Indoors, 15 chests
  had been given a wall texture as their `surface` (`swgirder`, `gtrlrf3`, `egytrmc`, `gt002b`).
- **F6 placement.** X7's "The orcs' den" was the chest's own hover title, a place name copied from the source's
  "Pillage?" den. The chest stood on the den mouth's line, 437 in front of its dark door face. X6's werewolf den
  chest stood the same way, 552 in front.
- **F3.** Three things put props at edges:
  - Dressing coordinates on terrace lips and slopes. X1's town hall barrel and cask stood exactly on the terrace's
    south edge row, half their footprint over the drop.
  - The studio stands things on a **bilinear** height (`LoweredOutdoorMap::storedHeightAt`), but the game's
    terrain is two triangles per cell split north-west to south-east. Props therefore float up to ~32 on uneven
    cells.
  - Non-steep scatter puts radius-52 bone piles where the ground under them drops 49–57.

  Indoors, props stood on ledges, shelves, crates and hatch rims, or inside walls.

**Check added.** `tools/xeen/check_props_support.py` runs over the installed maps (or `--file` a build). Its rules:
- `support.overhang`, `support.edge`, `support.floating`. A container's footprint must be level within 24, with no
  drop over 64 within 48 of it. Indoors other props on furniture only count past a 128 drop. Outdoors non-containers
  get 48 and 96 on hillsides. A wall between the prop and a lower floor is not a drop. Hung decorations
  (`hanging_decorations` in the studio sidecar), trees, plants and rocks are skipped.
- `chest.look`: only shipped chests pass.
- `chest.entrance`: 320 in front of / 192 beside an opening outdoors, 192 indoors, and a cave mouth's opening reaches
  256 further. The A7 sub-agent added a rule for a cupboard room with one opening that is too shallow.
- `chest.title`: a warning.
- `--regrounded` judges outdoor props as the studio will stand them after F6-R2.

The rule text is in `formats/DRESSING.md` ("Support under props and the chests"). Moving it into `oymap audit` is
F6-R4.

**Sites (82 maps, first run 22:40).** 296 findings in all, the 90 outdoor look errors among them. Fixed at the
generator or L4, rebuilt, installed, baked and played under each map's lock:

| Map | Site | Before → after | Tests |
| --- | --- | --- | --- |
| X1 | town hall barrel + cask (the user's F3 barrel) | (47.25, 41.0)/(47.15, 40.7) on the terrace lip → (47.27, 40.3)/(47.27, 39.95) against the hall's west wall | walk 419, hostility 64 pass |
| X1 | dirt heap 7dec11 | (61.7, 41.6) on the terrace's east slope → (60.3, 39.6) | |
| X2 | Ogre Lair skull heap 7dec20 | (25.3, 31.6), 380 down the slope, 53 over → (24.3, 31.5) on the ledge, off the mouth's line | walk 455, hostility, Danulf ring pass |
| X3 | Emerson's yard hay bale | (77.6, 38.0), 76 over → (78.2, 37.8) on the rise | walk 692, hostility pass |
| X7 | "The orcs' den" chest (8.png) | (83.0, 102.6) on the mouth's line → (84.4, 102.7) beside it, titled "The orcs' stash"; walk point moved | installed with its bake 00:09:38 (after: `output/xeen_fb/F6/caps/x7_after/`); hostility passes; the walk fails at step 67: the back gate (event 41, unchanged) no longer moves straight into XD-05, so the walk needs the new entrance window (F16/D-72), not this change |
| X6 | werewolf den chest | (52.3, 31.75) on the mouth's line → (53.6, 31.4) beside it | installed with its bake 00:12:03; hostility passes; the walk fails at step 59: the caravan cairn (event 42) no longer opens a window (F13); its L4 audit shows two `entrance.question` errors on events 80 and 83 (the F16 rule; those events are untouched) |
| X5 | giant's grave goods chest | (50.4, 87.4) on the cairn's crag, 78 drop → (51.2, 88.05), the cairn's level south-east foot | installed with its bake 00:02:54; hostility and Randon pass; walk fails at step 315: the Holy Book (event 108) no longer opens a window. That is the F13/F15 hand-over change, not this one; the walk needs updating |
| XD-01, XD-02, XD-03, XD-07, XD-24, FD-03, FD-04 | 12 sites (A7 sub-agent): buckets over a ledge, bench and table edge; crystals in walls; the hoard on the mound's lip; a skull shelf and a plinth set off their walls; a skull on a stall wall; chest:loft built of gt002 pieces → `kind: gt002`; chest:stash 156 from the sacks' door → 360 | details in `lanes/A7.md` Log | all pass except XD-01's walk, which sticks at step 128 in the culvert, away from the change (3/8 from assets_dev; 3/3 on a 22:46 copy of the assets: something installed later) |
| DD-22, FD-01, XD-18, FD-02 | 13 chests of `swgirder`, `gtrlrf3`, `egytrmc` (A8 sub-agent) | `kind: gt002`, backs to walls (FD-02's had stood on the alcove roof, 1,024 up) | 22 of 22 pass |
| XD-12, X9 | store barrels by a 128 drop; 14 bones and skulls at hatch rims; X9's rocs' hoard half on a spur (1,088 over) | on the floor, ≥ 48 from the rims; the hoard on the aviary floor | XD-12 5/5; X9 7/8 (`playtest_dragon_clouds` step 15 expects the old well window: F13's change, not this) |

Left, with reason:
- **90 outdoor chests (`chest.look`): F6-R1 to A1.** The generators need no change: after R1, the next rebuild of
  each ODM gives the shipped chest.
- **Outdoor props floating 25–36 over triangle ground** (X1's mine barrels, D1/X2/X5/X6 bone piles, chests on
  slopes): F6-R2. `--regrounded` shows them all clean after R2, except two scattered bone piles (X5, X7) waiting on
  F6-R3.
- **XD-04's cabinet:** a checker false positive, now handled by the cupboard rule.
- **Warnings:** D4's six `dec60` set pieces on a ledge, D2's food bowls, X7's and D3's titles, and XD-04's two
  skulls. These are set pieces for their lanes; X7's title is fixed with the queued X7 install.

**Captures.**
- `output/xeen_fb/F6/caps/x1_{before,after}/`: the user's barrel view, the user's chest view (the tiled plank chest,
  to compare after R1), the moved pair.
- `output/xeen_fb/F6/caps/x7_before/`: the den chest.
- `output/xeen_fb/F6/a7/`, `output/xeen_fb/F6/a8/`: before and after for every indoor site.

**Requests to A1 (merge point 40).**
- **F6-R1, outdoor chests as shipped.**
  - Move `ChestKind`, `chestKindOf` and `chestKindList` from `core/IndoorLowering.cpp` into a shared
    `core/ChestKinds.{h,cpp}`.
  - In `OutdoorThings::raiseChest` lay the kind's 19 faces with `OutdoorModelBuilder::addFace` (texels per corner),
    as `addChestFaces` does indoors. Match 7out01 `chest_N`: 96×64, body 64, 45° lid to a 32-deep top at 80.
  - Kind: an optional `kind` (`ch1`–`ch5`, `7gt002`, `gt002`, `ch001`–`ch006`). The default follows the style
    world: mm8 `gt002`, mm7 `7gt002` (Xeen's), mm6 `ch1`.
  - `turn` as now. A `textures` override keeps the box and warns "not a shipped chest". Crates are unchanged; they
    already match.
  - Test: a studio unit case, one chest giving 19 faces {a 4, b 10, c 2, e 1, g 2} and `chest_N`'s texel ranges.
  - MM6–MM9: no change, since only studio builds are affected.
  - Afterwards A5 and A6 rebuild X1–X7 and D1–D6 with bakes.
- **F6-R2, things stand on the game's ground.**
  - Add `LoweredOutdoorMap::groundHeightAt`, using the game's triangle split (as `Game::outdoorNativeTerrainHeight`).
    Use it for `kind: decoration`, actors, spawn points, chests and crates; structures keep `storedHeightAt`.
  - A chest or crate stands at the lowest `groundHeightAt` of its four footprint corners.
  - Test: `groundHeightAt` equals the game's height on a random heightmap, and a chest on a slope stands at its
    lowest corner.
  - MM6–MM9: none.
- **F6-R3, scatter.** Non-steep scatter rejects a spot where the triangle ground under the decoration's radius varies
  by more than 48.
- **F6-R4, the checks in `oymap audit`.** Move the six checks of `tools/xeen/check_props_support.py` into
  `core/Audit`, for world xeen and `--dressing`, with the same constants.
- **F6-R5, chest facing in the README.** Indoors a chest's `facing` is its long axis and the front is 90°
  anticlockwise of it. The lanes wrote it as "where the front points", so many chests show an end or a back to the
  room. Document this in `openyamm-studio/README.md`, and add `chest.front` to the audit: a chest whose front is
  within 64 of a wall.

**Notes.**
- MM6–MM8 chests are BModels; there is no lid that opens. Only MM9's chest decorations open, so "lids opening" does
  not apply.
- Other agents' edits to the generators were already in the files when the maps were rebuilt under their locks, so
  they were installed with this change. These are F12's black exits (DD-22, FD-01, XD-12, FD-02, XD-18, XD-07, XD-24,
  FD-03, FD-04) and F14's XD-18 ladder; all of them built and tested clean.

### F17 (gating, D-89) and the D-90 follow-ups (A3 session 34, 2026-11-22 ~01:40-, for A3, A3-side, A3-promo)

**Cause:** dungeon doors were quest hooks with `needs`/`requires` (a key handed over in conversation, a quest bit), and
nothing checked how many dungeons stood behind one: 32 of 66 BLVs (D-89 §1.1). Finds, experience touches and monster
deaths were message windows because a hook's line was a window unless it said `status: true`.

**Fix at the source:**
- `tools/xeen/gen_quests.py`: `entrance:`, `sealed:` and `gate:` keys (listed in `quest_hooks.yml` for the map lanes);
  every hook gets Lua, so a door whose condition went still returns true (no "Unknown hook"); a `found: <item>`
  condition compiles to `HasEverOwnedItem(id)` (D-90 5); a `gives:`/`map_gives:` hook shows its lines on the status line
  by default, `window: "<why>"` keeps a window (D-90 1). `quest_stub.py` knows `HasEverOwnedItem`.
- Quest files: the 10 outer locks gone (XD-04, XD-06, XD-08, XD-09, XD-15, DD-02, DD-06, DD-07, DD-08, DD-09) and
  their keys no longer given (Valia, Mirabeth, Ebenezer's two stones, Arie's amulet, Nadia, Thaddeus, the Ali Baba
  chest, Nibbler, Bosco; rewards re-pointed: Nadia 1,500 gold, Nibbler a treasure-3 item, the givers name the
  dungeons); the Sandcaster pass gone (DD-18, DD-19); XD-07's cellar unlocked; four locks moved inward (XD-11
  `m13.study_door`, XD-18 `q-c25.king_door` with the inner door open, DD-12 `m24.songbird` needs Megan's key, DD-15
  `m28.antechamber_door`); 21 sealed outer doors each with `sealed:` and a refusal line naming the way in (XD-01 the
  rain barrel, XD-07 Valia, XD-12 the Tower of High Magic, XD-24 the signs, DD-05 the rope, Necropolis the Lakeside
  witches, FD-04 Castle Alamar); XD-24 without the night condition; 66 conditions inside dungeons tagged.
- D-90: 82 hooks to the status line (experience touches, finds' answers, deaths: Rooka, Blackfang, Darzog (shortened),
  Draco, ...), 15 keep a window with a reason (Crodo, Roland, Corak's stasis, Rosebud, Tam, Sheltem, the ending, Lord
  Xeen, Sandro, three long answers of choices, the Lord Xeen Machine, the scepter's question, Joe's invoice); the
  47 (in fact 49) spot finds sorted in `output/a3_s34/d90_finds.md` (a 29, b 5, c 7, d 8); `found:` on M12's topic
  (the Skeleton Key) and Q-D22's pass topic.
- QUESTS_FORMAT.md §4.2, §7: the rules. ORIGINAL_LINES.md: the four changed source lines marked.

**Check:** `tools/xeen/quests.py` (0 errors): a condition on an outer door (`entrance:`) off the `SEALED` list is an
error, a sealed door needs its reason and pointer line, a new seal needs a decider; a map-Lua scan of every event that
moves into a dungeon (a direct qbit/item test or a conditional hook not on the sealed lists and not a bit the dungeon
sets itself is an error); a refusal branch that moves the party to another map is an error; a condition inside a
dungeon without its `gate:` tag is an error; a death hook or a touch hook (experience counts) showing a window without
`window:` is an error. Map sites waiting for their lanes are listed as open (`D89_MAP_SITES_OPEN`: X2's Yak door, XD-18's
throw, DD-17's arrival throw; seven X4/X5 camp experience windows added to `F13_MAP_SITES_OPEN`). `--open` prints the
sealed doors with their refusal lines.

**Sites:** outer doors 74 entrance events read; 13 opened or moved inward by hooks (no map rebuild needed except X2's
Yak door, XD-07's cellar door event, XD-11's study, XD-15 none, XD-18's King's door, DD-15's antechamber), 21 sealed,
6 shortcuts. Left for map lanes (REQUESTS in A3.md session 34): X2 Yak door, X3 coffin's night test, X1 key on the
barrel, XD-07 cellar test, XD-18 throw and King's door, XD-04 cloud stair bit, XD-11 study door, DD-15 antechamber,
DD-17 arrival throw (found by the new scan; D-89 had missed it), DD-06 chest's old key, the D-90 (b)/(c) conversions.

### F10: empty outdoor areas (feedback-fix agent, 2026-11-21 night, for A2, A5, A6)

**Cause.** This is not one map. Xeen's outdoor maps leave larger stretches of land with no monster than MM6–MM8 do.
Per map, the average land matches MM6–MM8 (median distance to a monster about 3,000; MM6–MM8 3,300). The difference is
the size of the largest empty stretch. The shipped maps' largest stretch has a median of 228 tiles (p75 522), mostly at a
map's edge. Xeen's had a median of 738, and 7 of 13 maps were over 700 tiles.
Several have it in the middle of walked land: X7's south slopes 2,043 tiles, X3's east 1,208, D1's south-west quarter
1,417 at 22,313 deep. The maps put their monsters in a few encounter areas, as the design asks: "a third of the land
quiet", D-40's "Red Dwarf Range ... quiet by design", and L1 plans marking whole regions `safe`. D-85's 5,888 discs
round givers widened the quiet parts further. On X7 the empty stretch ran along the road the party walks: road tiles were
a median 7,762 from a monster (MM6–MM8 3,400).

**The check.** New `tools/xeen/empty_zones.py`, with `tools/xeen/empty_zones.yml` listing the places a decision keeps
quiet.

- **What it measures.** On each outdoor map, walkable land is the play square without water, lava, slopes the party
  cannot climb, or the Xeen rim. Towns (three house doors within 3,000) and the decided places are left out. For each
  land tile it measures the distance to the nearest spawn marker or placed hostile.
- **Calibration.** `--calibrate` measures 37 MM6/MM7/MM8 maps the same way. An empty zone is land farther than 6,000
  from every monster. A zone deeper than 12,000 (the shipped median largest) or larger than 520 tiles (the shipped p75)
  is "larger than MM6–MM8's typical one".
- **Use.** `--check` exits 1 on such a zone. `--scene/--odm/--lua` measures a build folder; X7's `vw.sh` runs it. Each
  run is a few seconds per map.

**Sites (13 outdoor ODMs; the sky BLVs X8, X9 and D7 are not measured).** Before the fix, 12 failed; X4 passed. Three
are fixed and nine are left. The largest zone on each is below; every one is listed by
`python3 tools/xeen/empty_zones.py`.

| Map | Before: largest zone (tiles, deepest) | Now | What happened |
| --- | --- | --- | --- |
| X7 Mount Firestone (the report) | 2,043, 13,451; roads 7,762; land > 6,000 31 % | 239, 8,519; roads 5,436; 5 % | Fixed. See below |
| X3 Lifeforce Lagoon | 1,208, 15,194; roads 7,768 | 133, 10,073; roads 4,129; 5 % | Fixed by a sub-agent. See below |
| D1 Castleview Vale | 1,417, 22,313; 27 % | 227, 9,474; 9 % | Fixed by a sub-agent. See below |
| D5 Desert of Doom | 1,276, 20,123 at tile [107, 24] (north-east); 26 % | — | Left |
| X5 Winterkill | 890, 11,535 at [79, 54] | — | Left |
| D3 Sandcaster | 765, 16,804 at [20, 20] (north-west corner) | — | Left |
| D6 Forbidden Zone | 738, 12,715 at [24, 24]; second zone 422 at [107, 73] | — | Left |
| D2 Sprite Forest | 663, 13,994 at [26, 103]; second zone 340, 12,112 at [107, 20] | — | Left |
| X6 Desert of the Sphinx | 601, 11,192 at [45, 57]; second zone 429 at [65, 98] | — | Left |
| D4 Lakeside | 592, 13,921 at [20, 63] (west edge) | — | Left |
| X2 Rivercity | 203, 12,998 at [20, 103] (corner); second zone 502 at [107, 103] | — | Left |
| X1 Vertigo | 465, 12,731 at [31, 58] | — | Left. Act I is at 1.147, so markers can only move, not be added |
| X4 Burlock | 254, 10,012 | passes | — |

The nine maps left are reported for their lanes. Each is the same kind of fix: one map lock, bake and test each. A5
owns X1, X2 and D3; A6 owns D2, D4, D5, D6, X5 and X6. Several are corner or edge zones, which MM6–MM8 maps also have,
but larger here.

**X7 fix, at the source.**

- `source/map_rows.yml` X7: orcs `count: [1, 2]`, was [2, 3]. `--only gen_maps` changed only map_stats row 9105.
- `output/studio_cal/x7/tools/gen_l1.py` AREAS: the south now has 13 orc markers, was 8. They are spread over six
  areas: west slopes 4 (now down to the X1 edge), red river 3 (the basin's south half), and four new areas: east range
  3, gap south 1, south hills 1, pony ridge 1. The Red Dwarf Range's plan text drops "quiet by design".
- `gen.py`: the south's slot-1 markers are placed one by one, not in pairs.
- `places.SOUTH_MARKERS` is 13. Copies of the old files are `*.pre_f10`.
- Kill XP is the same: 19.5 orcs from markers, against 20 before. Act I is 1.1468; a 14th marker gave 1.1504, so the
  count stops at 13.
- Kept clear: Sablewing's 5,888 (D-85) and the dwarves' watch (L1/D-40), both listed in `empty_zones.yml`.
- First fights are 4,845 from the X1 arrival and 5,485 from X4 (D-15 band); Sablewing's nearest monster is 8,930.
  D-85/D-87: 0 errors.
- The map's 6,000 rule now has 3 rim-corner tiles at (103, 108) at 6,614 (it had none before); left as they are.
- Installed with its bake at 23:18:45; X7 is not in the stale list.
- Tests: hostility passes (`output/xeen_fb/F10/x7_host.log`). The walk passes once 6 stale dialog checks are taken
  out (`x7_walk_iter.log`, edited scenario `x7_walk_nodialog.yml`). Those checks expected a dialog after the shrine,
  the well and the Lava Rock, which F13 replaced with a status line. `gen_walk.py` needs F13's rule.
- Capture after, at the user's pose: `output/xeen_fb/F10/x7_after_user_pose.png`. There is no "before" capture: the
  map was reinstalled before one was taken.

**X3 fix (sub-agent).**

- `x3/tools/gen_l1.py`: 7 single markers added in the north vale, the reedbeds and the east ridge; 3 markers moved from
  the fen and shore.
- The approved L1 marked the north vale and reedbeds `safe`; they are now sparse wild land. The obelisk knoll, the
  causeway head and the X8 landing stay quiet.
- Kill XP: X3 1.025, Act II 1.083.
- D-11.1 distances stay within 5,000–6,500, D-15 first fights are kept, D-85/D-87 0 errors.
- Installed with its bake at 23:33. Hostility passes.
- The walk passes after two door-refusal steps that D-89 made stale are removed (`output/xeen_fb/F10/x3/walk3.log`).
- Captures: `output/xeen_fb/F10/x3/before.png` and `after.png`.

**D1 fix (sub-agent).**

- `d1/tools/gen.py`: six markers moved, none added. They now stand on the rim headland, the south bank and the river
  bank below the south wall, and the pair nearest Luna was shifted, which clears her D-85 warnings.
- Kill XP unchanged (D1 0.968, Act III 1.018). First fights stay in the band.
- Luna's 5,888 and Kalindra's forecourt (2,500) are listed in `empty_zones.yml`.
- Installed with its bake at 23:53. Hostility and the daily scenarios pass.
- The walk fails at steps 121 and 189 because of D-89/m14 hook changes; steps 1–188 pass.
- Captures: `output/xeen_fb/F10/d1/before_sw.png` and `after_sw.png`.

**Keeping it fixed.** Run `python3 tools/xeen/empty_zones.py --check` before calling an outdoor map done; it currently
fails on the nine maps listed above. Add each map's own pipeline line as X7's `vw.sh` has it. A new quiet place goes
into `empty_zones.yml` only together with the decision that keeps it quiet.

**F12/F14 queue end (23:59).** Installed with black exits: DD-03, DD-04, DD-05, DD-06, DD-07, DD-08, DD-09, DD-10A-C,
DD-11B, DD-11C, DD-12, DD-15, DD-16, DD-17, DD-19, DD-20, DD-21, DD-24, DD-25, XD-01, XD-02, XD-03, XD-05, XD-06,
XD-08, XD-09, XD-10, XD-11, XD-13, XD-15, XD-21 (ladders; `check_drops` 0), XD-27. Already installed black by another
session's rebuild from the patched generators: DD-22, FD-01, FD-02, FD-03, XD-07, XD-12, XD-18 (book tops and pool
ladder in; `check_drops` 0), XD-24. Refused by the baseline gate (their L4 or Lua was changed after the last install by
someone else; rerun `output/xeen_fb/f12_f14/tools/cycle.sh <key>` once that is installed): DD-11A, DD-13, DD-23,
XD-04, XD-14, XD-16, XD-17, XD-19, XD-20, XD-22, XD-23, XD-25, XD-26; FD-04 and DD-02 see `queue.out`. Tests 4 of 4 on
most; failing scenarios to look at (logs `run/<key>/tests/`): DD-05, DD-06, DD-07 (other families' hook changes),
DD-17, DD-19, DD-20, DD-21, DD-24, XD-01, XD-09, XD-11, XD-13, XD-27. Bakes: `bake.out` (the worker bakes every
installed map; the bake lock is shared with A5's outdoor bakes).

### A7 26th session: the dungeon follow-ups of A7's maps (2026-11-22 ~00:20-, fourth orchestrator)

Scratch `output/studio_cal/a7/s26/` (`cyc.sh` per-map cycle, `bakew.sh` bake worker, logs per map `<key>/r<time>/`).
- **F12's 13 refused maps:** not someone's uninstalled change. `diag.sh` built each L4 as found with merge point 40's
  oymap: the BLVs differ only in face order and UVs (same face count and texture histogram), the Lua only in MP40's
  entrance window (MoveToMap picture 1 into a BLV), DD-23/XD-20 only in the studio revision. The 12 that are A7's
  (DD-11A, DD-13, DD-23, XD-04, XD-14, XD-16, XD-19, XD-20, XD-22, XD-23, XD-25, XD-26) rebuilt with the black exits
  (each gen.py already had F12's patch; XD-04/XD-20 by `black_exits.py`), installed, baked. XD-17 is A5's.
- **A3's A7 requests:** XD-18 inner door opens to all (no throw), the King's door on `q-c25.king_door`; XD-07's cellar
  door without 116080; XD-04's ward and cloud stair on `head_witch_slain` (110046), refusals on the status line;
  DD-06's Ali Baba chest without the Eastern Tower key; D-90: XD-13 sword in a chest on the rack, XD-14 the Scroll of
  Insight in a writing box (chest) on the desk, DD-07 Ellinger's letter in a chest on the desk, the Golden Griffin in
  a chest on the last case, the Jewel of Ages a ground item on its stand; the five hooks switched to `map_gives`
  (else-texts dropped, `build_world.py --only gen_quests`); XD-24's vault door at any hour (the outer door's rule);
  F13 status lines on XD-07 (well, Black Liquid), XD-08 (seven juices), XD-13 (well). `quests.py` open rows for XD-07,
  XD-13 and XD-18 removed (0 errors); `check_exits.py` lost XD-18's throw line.
- **F16:** Yes/No dropped on DD-06/DD-07 (roof trapdoors), FD-03 (hatch to P5), FD-04 (hatch to X9): the standard
  window; trans rows on XD-02's Deep Line (5003, also the cart's own Lua) and XD-16's way to XD-17 (5017); test steps
  `select_topic: OK` where a move now shows the window (XD-02/03/04/16/19, DD-06/07, FD-03/04).
- **Tests:** about 30 dialog asserts whose line is now on the status line (A3's F13/D-89 hooks) turned into status
  checks (`statusconv.py`, and in the generators of XD-16, XD-18, DD-07, FD-03, FD-04 so they stay); F1's houses
  (`house_dialog` false) on XD-02/XD-13. Generators that had reverted F13's hand edits (XD-16, XD-18, DD-07) fixed.
- **D-89 identity, XD-18:** a real cave (NOTES "Twenty-sixth session"): cut corners up to 12 sides, rough walls, uneven
  floors and vaulted roofs in 16 cave rooms, stalactites, the office and library cut into the rock, a charred passage,
  the King on a mound of gold, stars in the starwell; `identity: {shape: cave, family: d17}`, no `identity.cave_shape`
  warning (floor uneven 9 % -> over 30 %). Before/after `output/studio_cal/a7/s26/xd18/before_sheet.jpg`,
  `after_sheet.jpg`. **XD-13's identity rebuild not started.**
- **Left:** F14 pockets on XD-01, XD-02, XD-03, XD-05, XD-08, XD-15, XD-25, DD-16, FD-02, FD-03, FD-04 (not touched);
  plank-strip door leaves; `xfgrid` (FD-04's crossword cells, 4 `feature_repeated` errors) wants `class: tile` (A6).

### A7 27th session: tests, XD-13 and FD-03 identity, F14 pockets, chest fronts, plank doors (2026-11-22 ~01:00-)

Scratch `output/studio_cal/a7/s27/` (`cyc.sh` per-map cycle under the map lock with bake, MAW, exits, drops, tests 4
rounds; `q*.sh` the queues and their `.out`; `drops/` the F14 check before/after on every A7 map).
- **Tests:** FD-03's seal refusal is a window (A3's failText without `fail_status`): asserted as a window again,
  20/20. FD-04: Alister's name is "Alister, Druid" (merge point 41, F9-R2), the egg's else line, the Minor shrine and
  "CODE ACCEPTED" are status lines (`status()` reads a line once: the answer is checked in the logging read), 36/36.
- **F14, the check (`tools/xeen/check_drops.py`, fixed):** an edge also joins the floor it stands over (blocks and
  stairs on a continuous floor: the blind spot), sampled every 64 along it; an edge under or within 68 of a block on
  its face (a parapet) is not walked off unless the block hangs with room under it; no join through a ceiling; the
  way back follows the joins one way or both. On A7's 31 maps: before 14 pockets on 11 maps, after the fix and XD-01's steps 6
  on 2 (XD-02, XD-15), each checked by hand. **Sites:** XD-01 drain pool (64 in slime behind a 24 lip): two steps, installed and
  baked. XD-02 trestle chasm and the car's deck slivers (a mover ride, gated at both ends) and XD-15 sun disc shaft (a
  mover over it; the wrong name drops you by design onto a heap that leads on): NOTES lines. False before, gone now:
  XD-03, XD-05, FD-02, FD-04 large pockets (stairs on a continuous floor), XD-08 pits x2 and XD-25 pit (steps inside),
  DD-16 lava and FD-03 well foot (parapets), FD-04 eggs' rock. No new pocket on any A7 map.
- **chest.front:** XD-02 (two footlockers, the strongbox), XD-23, XD-26, DD-11B, DD-11C (two), DD-23 turned 180
  degrees, FD-04's tome chest moved to the wall south of its door; all installed with bakes, the warning gone.
- **Plank-strip leaves titled Door (F12(b), door pictures from the family):** DD-06 six doors (MM8's plank pair
  `gkp103a/b`, one wing a leaf, doorways 256 high), XD-04 six pairs (7d12's `hwr1dl/dr`), XD-03 three pairs and the
  back stair (the mines' stone door `cvdor1`; "Plank door" titles now "Door"), XD-25 three (the troll-home kit's
  `gkp103a/b`, two leaves, the keeper's doorway 256). XD-15's three `egywle` slabs left (the pyramid's sliding slabs, as
  MM6's pyramid has them): DECIDE.
- **D-89 identity:** XD-13 (the ruined 7d29 hall: base and string courses, ruin stone above, the roof broken open on
  the sky, a breach in the corner, rubble mounds, a fallen rafter; a working laboratory; a two-leaf steel vault door)
  and FD-03 (dark rubble walls and iron ceilings, steel pairs). Before/after `output/studio_cal/a7/s27/xd13/` and
  `fd03/` (`before_sheet.jpg`, `after_sheet.jpg`).
- **DD-07:** `jewel_found` (113361) dropped from `project.yml` and the plan's goal (A3 35th); studio file only.

### A7 28th-29th sessions: D-89's cave set and family drift (2026-11-22 ~01:50-02:50, fourth orchestrator)

- **Cause:** the dungeon generators drew caves as boxes (level floors, square corners, flat roofs, straight walls),
  and some drifted off their assigned shipped family (XD-23 in MM7 dirt instead of d13).
- **Fix at the source:** `tools/xeen/cave_shape.py`, one pass every cave generator calls after writing L4 (corner
  cuts, rough walls, floors that rise and fall with everything standing pinned level, vaulted roofs, stalactites;
  `path_rough` for level tunnels). XD-23 retextured to d13 as d13 uses it.
- **Sites (A7's cave set, 8):** XD-05, XD-16, XD-23, XD-26, DD-11A, DD-11B, DD-11C, DD-23: all over the audit's cave
  numbers (floor uneven >= 0.30, ceiling spread >= 80, rough >= 0.18), installed, baked, all tests pass. Left: XD-05's
  drum-hall bowl (orchestrator: later polish), XD-26's nests on every ledge, DD-11's family (DECIDE in A7.md).
- **Check added:** `tools/xeen/check_identity.py` (family share >= 50 % and the cave numbers, every brief with
  `identity:`), beside the audit's `identity.cave_shape`. Its first run also fails other lanes' DD-09, DD-10B/C,
  DD-14, XD-09, XD-10 (reported to the orchestrator).
- **Captures:** name test of the eight maps, `output/studio_cal/a7/s29/names/names_sheet.jpg`; before metrics
  `output/studio_cal/a7/s28/met/<key>.json`.

### House signs: the Adventurer's Inn hung the tavern's mug (A4, 2026-11-22 ~08:45-)

- **Cause:** the town generators pick each house's sign by hand (X1 `town.py`, D1 `gen.py`): X1's inn had the tavern
  mug `7sgtvrn`, D1's a lettered board `xlinn`. MM6-MM8 (measured on every shipped ODM) hang the key and heart
  `sginn` on the Adventurer's Inn (Ravenshore, Dagger Wound, Tatalia, MM6's outc2). A second fault on the way: every
  map's kit dropped the sign of a `cottage` silently (banks, Asp's shrine and armourer, D1's jail, storage, body
  guild, jetty), and X1's and X2's temple shapes dropped theirs.
- **Fix at the source:** `tools/xeen/house_signs.py` (kind -> MM7/MM8 boards plus Xeen's own of that kind); X1 and D1
  inns `sginn`, D1's jetty `sgdock`; the 13 kits hang a cottage's sign and refuse one on a round hut; X1/X2 temples
  hang theirs. **Check:** `towns.py` runs `house_signs.py` on every built town sketch: a sign not of its house's kind
  is an ERROR, a service of a signed kind with none a WARN; TOWNS_FORMAT section 5.
- **Sites:** wrong 3 (X1 inn, D1 inn, D1 jetty), all fixed; dropped 10 (X1 bank, temple; X2 bank, temple; X4 4171,
  4174; D1 bank, body guild, jail, storage), all fixed; X1, D1, X2, X4 rebuilt with bakes, every check and L4
  playtest passes. Unsigned services left as WARN for their lanes (13): X3 4103, 4108; X5 4251, 4254; D2 4551, 4552;
  D3 4649; D4 4651, 4655; D6 4751, 4753-4755.
- **Captures:** `output/xeen_a4_signs/shots/inn_signs_compare.jpg` (Ravenshore, X1 inn, D1 inn, X1 tavern), per map
  `shots/x1c/`, `shots/d1/`, `shots/x2/`, `shots/x4/`, Ravenshore `shots/out02/`.

### F19: town walls closed and flush (A4 for A5/A6, 2026-11-22 ~09:30-11:30)

The user: Burlock Savannah's village wall ended short of the castle's tower, leaving a walkable gap ("the walls should
close off the city"); Vertigo's end tower stood on the creek bank ("move to the water so that person cant just walk
around it"); Vertigo's culvert and the walls beside it met with slits and steps; "these are likely generic rules".

**Cause.** The generators drew each wall from its own numbers with nothing that checked how pieces end: a circuit could
stop on walkable land (X4, X1's open creek side, X6's coach yard), pieces of different thickness or height met without
a cover piece (X1's culvert between quay walls proud of it, D3's four city walls of different tops, D1's corners as two
separate walls), and ends stopped at a plot's edge instead of the body inside it (slits of 8-66 at D1's gate leaves,
D3's gate towers and quarter walls, D6's gatehouse and energy fields, X2's terrace faces at the Great Bridge).

**Check (new).** `tools/xeen/wall_check.py` with the enclosure list `tools/xeen/town_walls.yml`, run by
`towns.py --strict` (an ERROR) and by each F19 map job before install. On the built ODM as the game collides:
- `walls.open`: a flood fill at the party's radius (37 + 16) from each enclosure's inside, its gates sealed: water tiles,
  slopes the game refuses and every upright model face over body height block; reaching the box's edge is an error
  naming the narrowest point on the way out.
- `walls.loose_end`: a circuit wall's end on walkable land (not water, cliff, map edge, tower or building).
- `walls.slit`: a wall end with another piece under 96 in front of it.
- `walls.step`: a wall end partly covered by the piece it meets and partly open (over a tenth, more than 32 across and
  up); a tower or building round the joint covers it. `joints_ok` exempts pieces proud by design.
The joint rules run on every wall of every built outdoor map; the closure rules on the 13 enclosures listed. Before:
13 maps, 60 errors (after calibration against captures); after: 13 maps, 13 enclosures, 0 errors.

**Sites (enclosures found: 14).**
- X1 Vertigo: open along the creek (both end towers on the bank). Fixed: `town.py` runs a wall from each end tower
  0.75 into Pitchfork Creek (`thing:creek_wall_1/2`); the bridge is the way in. Culvert: one 2,560 headwall the
  quay's whole length (`gen.py`, quay walls removed; dark face kept 128 behind the front for XD-01's arrival).
- X4 Burlock: open at both north ends (970 to the castle, the rise's flanks walkable). Fixed: `places.py` village wall
  climbs to the castle's south corner towers, its top following the land (one piece, no joint).
- X6 Warzone coach yard: open round both ends of the gate wall (the barred gate could be walked round). Fixed:
  `places.py` yard wall from the north rim's cliff down the west side and along the south into the back cliff, top
  following the land.
- D1 Castleview: closed; corners (53, 44) and (73, 44) were two walls proud of each other (one line each now), north
  gate leaves 384 in a 512 passage (512 now). `gen.py`.
- D3 Sandcaster: closed; corner towers over the three joints of walls of different tops, the south gate's walls end
  inside its towers, the quarter's retaining walls run into the city wall, the precinct walls are one piece each with
  a following top. `places.py`. The gorge's rock faces are exempt (`joints_ok`: a cut, not a town wall).
- D6 Castle Alamar: closed; the ring ends and the energy fields run into the gatehouse and pylons. Necropolis closed.
  `gen.py`.
- X2 Rivercity (no town wall): the terrace faces end 16 inside the Great Bridge's sides (`gen.py`).
- Closed and flush already: X5 cloister, X7 watch post, D2 both palisades, D4 Blackfang, D5's Doom barrier.
- Left: X3 Newcastle (its walls are staged, untouchable and hidden until built; not an enclosure yet). D1's jetty
  bastion stands proud of the wall line on purpose (`joints_ok`).

**Rebuilt** (each under its map lock, through `tools/heavy.sh`): X4 10:46, X6 10:52, X2 10:55, D1 11:00, D6 11:03,
X1 11:06, D3 11:09, all installed with bakes; per map: L4 gate (only wall things changed), wall_check on the build 0,
audit 0 errors, door_check/check_exits 0, D-85 0 (X6 by its own 5,120 run in vw.sh), key_npcs written, actor heights
0, empty zones and props support pass, every L4 playtest passes from assets_dev. Scripts and logs:
`output/xeen_walls/` (`map_job.sh`, `queue.sh`, `run/<map>/`).

**Captures.** Before: `output/xeen_walls/caps/before/{x1,x4}/` (the user's poses and their mirrors) and
`caps/flags/<stem>/` (every flagged end); after: `caps/after/{x1,x4}/`, `caps/after_flags/<stem>/`; plans
`plan_before/`, `plan_after/`; contact sheet `output/xeen_walls/sheet_before_after.jpg`.

### F20: villagers in every settlement, each town its own people (A4 for A5/A6, 2026-11-22 ~11:40-, D-96)

**The report.** Lifeforce Lagoon at (17602, -2965, 2139), yaw 251°, pitch -37°: "no villagers in the village? + do
we want like all the villagers the same type in all the cities? ... diversity." The spot is Nightshadow's square (X3).

**Cause.** Street villagers were hand-placed, map by map, by whoever built the map; nothing required them. Of the 17
settlements with streets (plus three indoor towns), 9 had none (Nightshadow, Ebenezer's camp, Winterkill,
Castleview, the treehouse village, Lakeside, Necropolis, Olympus, Shangri-La), Asp had 3 for 17 doors, Kai Wu's
monastery 2 novices, and the rest (Vertigo, Rivercity, Castle Burlock, Sandcaster, the Crossroads, Sphinx Wells) all
used the same MM7 human peasants (rows 350-377); Rivercity (0.38 per door) and Sandcaster (0.26) were thin.

**Measured (MM6-MM8, placed peaceful townsfolk within 1,536 of a town's house doors, per door;
`output/xeen_villagers/data/ref.txt`):** New Sorpigal 0.88, Free Haven 0.62, Castle Ironfist 0.89, Silver Cove 0.47;
Harmondale 0.96, Tatalia 0.6-1.0, Steadwick 0.52, Pierpont 0.77, Emerald Isle 1.18, Deyja 0.4-0.56; Ravenshore 0.62,
Alvar 0.35, Shadowspire 0.42, Dagger Wound 1.19. Hamlets of 2-6 doors: 1-2 per door. Kinds: MM8 one people per town
(Ravenshore and Alvar dark elves, Shadowspire vampire folk, Dagger Wound lizardmen; Balthazar's minotaurs), MM7 3-6
human or elf kinds (Pierpont elves, Deyja goblins), MM6 3-4 (peasants, merchants, nobles).

**Fix at the source (D-96).**
- `assets_dev/worlds/xeen/source/towns/villagers.yml`: every settlement of the town files, with a palette of 3-5 kinds
  from the MM6-MM8 townsfolk rows that have a 3D model, a count (about 0.7 per door) and a group; or an exemption with
  its reason (lone houses in the wild, castle interiors, one-house dungeons).
- `tools/xeen/villagers.py --place <map>` writes `villagers_spots.yml` (generated) from the built map: street points
  inside the settlement, at least 640 from every house door (closed cursed doors too) and 900 from every talking NPC,
  never on a model (walls, houses, platforms, bridges) or a decoration, spread by farthest-point picking with roads
  preferred.
- Every outdoor generator places them through `villagers.sketch_actors()` / `villagers.fill()` and
  `villagers.relations()` (peaceful: `hostile: false` and friendly to the party; wandering by their rows' Long
  movement). `fill()` puts them into the list places of the earlier hand-placed townsfolk (`villagers.slots(n)`), so
  every other actor keeps its scene index (the first X2 pass moved Danulf's index and broke its playtests; reinstalled).
- The check: `villagers.py`, run by `towns.py --strict`: a built settlement with no villagers, below its floor (0.45 per
  door, at least 3; hamlets 2), with one kind; a palette outside 3-5 kinds, a row that is not townsfolk or has no
  model; neighbours sharing two kinds; a villager starting hostile, by a door or by a giver: ERROR. Indoor towns whose
  lane places them (`placed_by`): WARN.

**The palettes, race first** (the user, during this work: "make sure we dont use villagers race which doesnt fit the
city/village"). Each settlement's races and their source are in `villagers.yml`; a row's race comes from its picture
and the check fails a race the settlement does not allow. The first palettes (MM8 vampire folk in Nightshadow,
lizardfolk in Asp, dark elves in Sandcaster, goblins in Lakeside, dwarves in Winterkill, Castleview and Ebenezer's
camp, elves in the treehouse village, ogre/troll/minotaur traders at the Crossroads and Sphinx Wells) were replaced
and the maps rebuilt again. Diversity now comes from clothing, trade and age (neighbours share at most one kind):

| Settlement | Map | Races (source) | Kinds | Villagers before -> after |
| --- | --- | --- | --- | --- |
| Vertigo | X1 | human (WORLD_DESIGN 5.1; 50 named NPCs human) | MM7 Human2 men A/B, Human1 women A/B | 23 (6 by doors or Mylo) -> 23 |
| Rivercity | X2 | human (57 NPCs human, one elf guest, a ghost) | MM6 peasants M1, F1, F2, merchants | 18 -> 30 |
| Nightshadow | X3 | human (15 NPCs human, 3 gnomes: no gnome row) | ragged folk (MM8 bedraggled), Human1 woman C, man C, Moon acolytes | 0 -> 12 |
| Ebenezer's camp | X3 | human (its NPCs) | workmen: Human1 men A/B, Human2 man C | 0 -> 4 |
| Castle Burlock | X4 | human (14 NPCs human) | MM7 and MM8 Sun clerics, Human2 women A/C, Human1 man B | 10 -> 10 |
| Asp | X4 | human (16 NPCs human; the curse is on humans) | Human2 woman B, man C, ragged folk | 3 -> 11 |
| Winterkill | X5 | human (18 NPCs human) | MM6 peasants M1, F2, Human2 woman C, ragged folk | 0 -> 12 |
| Kai Wu's monastery | X5 | human (its monks) | MM6 and MM7 monks, a Sun cleric, a pilgrim | 2 -> 4 |
| Sphinx Wells | X6 | human (4 NPCs human) | merchants, Human2 man B, woman B | 4 -> 6 |
| Castleview | D1 | human (44 NPCs, one elf) | Human1 men A, women B, Human2 women C, Drawkcab's monks | 0 -> 30 |
| the treehouse village | D2 | sprite (its 5 NPCs sprites) | none: no sprite townsfolk row (request A2/S) | 0 -> 0 (WARN) |
| Sandcaster | D3 | human (39 NPCs, one elf) | merchants, Human2 men B, women A, MM6 peasant women | 10 -> 28 |
| Crossroads | D3 | human (6 NPCs human) | a merchant, MM6 peasant men, Human1 woman C, Human2 man A | 4 -> 6 |
| Lakeside | D4 | human (19 NPCs; the vampire Queen apart) | fisherfolk (Human1 woman A, man C, MM6 F2), the coven's robed women (druidess) | 0 -> 12 |
| Necropolis | D6 | human, vampire (7 undead NPCs, 5 human) | Moon acolytes, ragged pilgrims, Human2 man C, MM8 vampire folk | 0 -> 8 |
| Olympus | D7 | human (13 NPCs) | Sun clerics of two orders, monks, Human2 women | 0, pending (A6) |
| Shangri-La | XD-17 | human (18 NPCs, one orc guest) | monks, Moon acolytes, Human1 man B, Human2 woman B | 0, pending (its lane) |
| Bosco's Hall | DD-25 | dwarf (6 NPCs dwarves) | A8's dwarves | 3, pending (A8) |

**Rebuilt and installed with bakes, one map at a time under its lock** (`output/xeen_villagers/tools/map_job.sh`: L4
gate that only the sketch's actors and relations change and no other actor's index moves; audit, door_check,
check_exits, D-85/D-87, key_npcs --write, actor heights, empty zones, props, house signs, villagers, every L4
playtest): X3 11:57, X2 12:09, X5 12:15, X6 12:18, D1 12:21, D2 12:24, D4 12:27, X1 12:34 (after WATER END DONE),
D3 12:38, D6 12:41, X4 12:47; after the race rule again (palettes only) X3 12:56, X4 12:59, X5 13:02, X6 13:05,
D1 13:09, D2 13:12, D3 13:15, D4 13:19 (VILLAGER RACES DONE 13:20). Every L4 playtest passes. After: `towns.py
--strict` 0 errors (WARN: the treehouse village, D7, XD-17, DD-25), `stale_bakes.py --check` 0,
`build_world.py --check` 0 differ. X6's one D-85 ERROR (Arie 4608, two melee spawn
markers, no disabler) was there before (`output/xeen_walls/run/x6/d85.txt`, D-87's melee warning case).

**D-95 on X4 (the orchestrator's addition):** Asp's undercroft stair (`thing:xd25_stair`) is now a sunken entrance
(`SunkenEntrance`: floor nodes x 41-42 on row 81, 224 under the square; ramp to row 82; 448-thick revetments, the
house east of it stands at x 43.0; cap behind). Event, window and XD-25's arrival (41.5, 82.45, on the square south of
the ramp's top) unchanged; the rule stone moved off the cut to (43.2, 83.0). The kit's headwall and cap now follow the
revetments' thickness (identical output for X1's culvert).

**Captures.** `output/xeen_villagers/caps/before/`, `after/` (the user's pose, two street views per settlement, the
stair), `close/` (two shots at villagers per settlement, after the race rule); contact sheets
`output/xeen_villagers/contact_sheet.jpg` (before | after) and `output/xeen_villagers/closeups_sheet.jpg`.

### F21 roofs: sky over enclosed walks (D-97), and Castle Xeen's monsters (D-98), 2026-11-22 ~14:30-16:00

Agent for A7/A8 (fourth orchestrator); scratch `output/xeen_roofs/` (cycle `cyc.sh`, tours `tours/`, captures
`before/`, `after/`).

- **Reports:** Castle Xeen (XD-19) at (-4837, -1367, 640): "I dont see the roof"; Castle Blackfang (DD-14) at
  (-145, 1352, 1280): "should there be roof?"; Castle Basenji (XD-14) at (-28, -2037, 640): the same.
- **Cause:** the studio builds every room with walls up to its ceiling; `sky: true` only swaps the ceiling for sky. A
  narrow room under sky with full-height walls on both sides is a corridor with its lid off. No castle or keep kit
  default: each map's generator gives its open rooms a `theme:sky`/`theme:walk` with a sky ceiling; the ones that read
  open had a low opening (DD-14's parapets over the courtyard) or walls drawn as sky (XD-22's moon gallery, XD-11).
- **Rule (D-97):** sky only over places a brief names as outdoors (courtyard, battlements, wall walk, terrace, shaft,
  pit, ravine, bridge, arena, ruin, open ground, canopy, skylight); a walk opens on at least one side; another open
  room opens on a side or is at least 0.75 times as wide as its walls are high; a skylight is at most 35 % of its
  room's floor. Every enclosed room or corridor has a ceiling.
- **Check:** `tools/xeen/check_open_sky.py` (data `tools/xeen/open_sky.yml`, in lanes/README's map checks): an
  undeclared sky sector, a walk closed on both sides, a roofless enclosure or an oversized skylight is an ERROR. On
  the maps as they were it flags exactly the reported family: XD-19's four wall walks, XD-14's battlement walk (the
  Basenji pose) and roof walk. Now: 57 sky sectors on 33 BLVs, 0 errors (`survey_before.txt`, `survey_after.txt`).
- **Survey (57 sectors; sky in walls, the views out, counted apart):** kept open: DD-03 yard, DD-14 courtyard and four
  walks (battlements over the courtyard), DD-19 court, XD-19 aviary (1,920 wide under 1,536), XD-20 arena, DD-12 ruined
  tower, XD-13 breach, XD-11 roof terrace and stairway, XD-12's roofs, sky stair, well and outside, XD-17 valley and
  ravine passage, XD-22 moon gallery, FD-01 shaft, the open-air maps (D7, P1-P5, X8, X9); skylights (sky 4-34 % of the
  floor): DD-09 crown, DD-11A/B/C pits, DD-13 smoke holes, DD-22 viewport, DD-23 crack, DD-24 smoke hole, FD-03/FD-04
  hatches, XD-13 fallen roof; canopy: DD-09 limb walk. **Fixed (7 sites):** XD-19 `wall_ws`, `wall_wn`, `wall_es`,
  `wall_en`; XD-14 `battlements`, `roof_walk`, `moon_tower`: the outer wall drawn as sky over a 160-high parapet (the
  wall stays solid). Nothing was roofed: every sky sector is named open by its brief.
- **DD-14:** the user stood in the north wall walk (not the coffin landing): battlements, its inner parapet (sill 224)
  open over the courtyard; kept (`before/dd14/03-user_level.png`, `04-user_south.png`).
- **D-98 (Castle Xeen):** 72 -> 98 monsters (1.9 per sector, 0.64 per M units²: upper half of Castle Gloaming,
  The Pit, Castle Lambent, Darkmoor, MM8's Necromancers' Guild); the throne room has Lord Xeen and six Xeen's Guards in
  two ranks, freed with him. DD-17's Command Central has no boss fight: unchanged.
- **Builds:** XD-19 and XD-14 rebuilt from their generators, installed, baked; MAW reserves + balance check, exits,
  drops, doors, key NPCs, actor heights, identity, open sky all 0; audits 0 errors; playtests XD-19 4/4, XD-14 3/3;
  side quest q-c8 PASS; main segment 83 PASS after its Lord Xeen index (25 -> 37); `stale_bakes --check` 0;
  `build_world.py --check` 0 differ.
- **Captures:** `output/xeen_roofs/sheet_roofs_a.png` (XD-19 and XD-14 user poses and every fixed walk, before and
  after), `output/xeen_roofs/sheet_xd19_monsters.png` (throne room, nave, stair hall, west aisle), DD-14
  `output/xeen_roofs/before/dd14_sheet.png` (unchanged map).

### F23 bright interiors: The Sphinx too bright with the torch (D-100), 2026-11-22 ~14:50-15:55

Agent for A7/A8 and the lighting side (fourth orchestrator); scratch `output/xeen_bright/` (tools `tools/`, captures
`caps/`, contact sheet `F23_contact_sheet.jpg`: per map without and with Torch Light (Expert), before and after, and
the MM6-MM8 references; brightness tables `brightness_before.tsv`, `brightness_after.tsv`).

- **Report:** XD-15 The Sphinx at (-88.5, 5641, 0), yaw 0.551: "WAY too bright (with torch)".
- **Measured** (game screenshots, HUD off, mean Rec. 709 luma 0-255 / share with a channel at 250+; the torch is
  Expert, the user's warm torch): the user's pose 186 / 29 % without the torch, 210 / 58 % with it; six Sphinx views
  202 / 37 % and 224 / 73 %. References: MM6 Tomb of VARN (pyramid.blv) 45 / 75 with the torch, MM7 Tidewater Caverns
  30 / 45, MM7 Grand Temple of the Sun (t03, the brightest original found) 110 / 3 % and 184 / 35 %, MM8 Troll Tomb
  (d13) 38 / 87, MM8 Temple of the Sun (d22) 41 / 111. The Sphinx drew brighter without a torch than MM7's brightest
  temple with one.
- **Cause: the bake, not the torch.** Every Xeen profile was the same copy (direct 2.0, bounce 5.0, ambient 0.9,
  `max_lighting` 1.5; seven maps had been hand-lowered after earlier "washed out" reviews). `bounce_scale` 5 suits dark
  textures; Cycles' bounce grows with albedo, and on the Sphinx's sandstone (texture luma 146) it was 0.65 of the direct
  light, so the composed bounce was 3.2 times the direct (median raw light 2.9 against the 1.5 ceiling): nearly every
  texel sat at the ceiling, a flat floodlit 1.5 x a pale texture. The torch then adds its 0.76 x texture as in MM6-MM8
  (unchanged engine; additive like the originals) and blew the rest out. Lights (92) and textures are not the fault:
  DD-15, the Great Pyramid, uses the same egy* textures and drew at 112 on its hand-lowered profile.
- **Fix (D-100), shared:** `tools/lighting/bake_indoor.py` profile key `rendered_limit` (opt-in; MM9 profiles
  unchanged), in all 60 `profiles/xeen_*.yml` as `{"mean": 90, "ceiling": 0.85}`: per texel no texture mean colour
  is drawn over 0.85 per channel, and a map drawing over a mean of 90 has all its light scaled to 90 (devdocs/
  INDOOR_BAKED_LIGHTING.md "Rendered limit"). Guard: `python3 tools/lighting/indoor_bake_brightness.py --world xeen
  --check` (no Blender, seconds; fails a map over 95): 0 over now.
- **Maps** (every Xeen BLV rebaked under its lock from the map as it stood; scaled maps, rendered mean before ->
  after by the check tool): XD-15 The Sphinx 201 -> 93, XD-20 The Warzone 176 -> 92, FD-02 Southern Sphinx 120 -> 90,
  DD-26 Olympus Sewer 119 -> 92, DD-07 Eastern Tower 114 -> 93, DD-15 Great Pyramid 112 -> 92, DD-03 Castle Kalindra
  112 -> 93, DD-06 Southern Tower 102 -> 93, DD-05 Western Tower of Mok 98 -> 92, DD-08 Northern Tower 96 -> 93. The
  other 50 maps were under 90 and only lost texels over the ceiling (pre-torch white, a few % in lamp pools).
- **After, in game:** the user's pose 117 / 0 % without, 171 / 6 % with the torch; the six Sphinx views 119 / 0 % and
  176 / 14 %; FD-02 164 / 23 % -> 133 / 7 % and 211 / 60 % -> 196 / 38 %; DD-15 143 -> 123 and 196 / 34 % -> 178 /
  25 %; DD-26 91 -> 69 and 145 / 16 % -> 127 / 8 %. With the torch the sandstone now reads like MM7's t03 under the
  torch (184 / 35 %), not white.
- **Left:** FD-02's library wall (a contrasty pale texture: the ceiling works on the texture's mean) still draws 191
  without the torch; the torch on any pale stone adds about +55 (the original game's behaviour; DECIDE in the report).
  `stale_bakes.py --check` 0. Playtests: XD-15 4/4, XD-20 3/3, FD-02 5/5, DD-15 4/4, DD-07 4/4, DD-03 5/5, DD-06 4/4,
  DD-05 3/3, DD-08 4/4, DD-26 5/6 (`playtest_in` step 10: the sewer grate's dialog lacks "Descend into the sewer?",
  an event text, not lighting; for A8). XD-20 cannot be started by `run_game.py` (its preparation save fails), so it
  has no captures.

### F22 chest facing: chests turned and placed by D-99 (A1 42nd session for A7/A8, 2026-11-22 ~14:40-16:30, merge point 47)

The user: "lots of times there is wrong rotation of the chests (in dungeons) based on the position to the doors"
(Darkstone Tower, FD-03, at (-1798, 11, 864)) and "chest in front of stairs/entrance to another room" (the Sphinx,
XD-15, at (169, 5843, 0)).

**Cause.** An indoor chest's `facing` is the direction of its width and its front lies a quarter anticlockwise of it
(F6-R5); the lanes' generators wrote it as the front's direction, so chests stood end-on to the wall they were set
against (FD-03's library chest: end-on to the west wall, its front north along it) or with their front to it. F6-R5's
`chest.front` only probed 64 straight out of the front. Chests are geometry, not decorations, so the D-7 dressing rules
(doorways, walking lines) never saw them: XD-15's vault chest stood on the line from the belly hall to the dungeon stair,
104 from the stair's doorway.

**Rule: D-99** (DECISIONS), measured on MM7 (7d29 Castle Harmondale, the barrows, 7d08, 7d11, 7d12: 27 of 32 chests back on
a wall, none end-on) and MM8 (13 dungeons: 33 of 49 back on a wall, every free one with its front within 83 degrees of
its nearest doorway): back to the wall it stands by, out of a niche, free toward its room's entrance from the party's
start; its footprint 128 (a party's width and a margin) clear of every doorway and door, 64 off the line between two of
its room's ways.

**At the source (Map Studio, merge point 47).** A chest without `facing` is turned by the rule (`chestRuleDegrees`:
the room's walls less its doorways, the entrance by a walk over the openings from the start; a sloping lid by whole
quarters); a given `facing` still wins. Build warnings `chest.facing` and `chest.placement` (they replace
`chest.front`). **Check:** `oymap audit` `chest.facing` and `chest.placement` (errors; Xeen, other worlds with
`--dressing`) on the built map, indoors and on outdoor models, by the same functions (core/ChestKinds.h). Through it the
shipped maps keep three faults among about 45 chests (7d12's two vault chests, d06's one), the stricter side on purpose.
Studio tests "D-99: a chest without facing ..." and "D-99's checks ...", 512/512.

**Sites.** Survey with the new audit on all 82 installed maps (`output/xeen_chests/survey_before2/`): 118 faults on 50
BLVs, 112 facing and 6 placement; while rebuilding the final audit found two more (XD-12). Per map (facing/placement):
DD-01 3/0, DD-02 3/0, DD-03 4/0, DD-04 3/0, DD-05 4/0, DD-06 1/0, DD-07 3/0, DD-08 4/0, DD-09 2/0, DD-10A 2/0, DD-10C 1/0,
DD-11A 1/0, DD-12 4/2, DD-13 3/0, DD-14 1/0, DD-15 4/1, DD-16 2/0, DD-17 2/0, DD-18 2/0, DD-19 1/0, DD-20 2/0, DD-21 2/1,
DD-23 1/0, DD-24 2/0, DD-26 2/0, FD-03 4/0, FD-04 4/0, P5 1/0, XD-02 1/0, XD-03 4/0, XD-04 2/0, XD-05 1/0, XD-06 1/0,
XD-08 2/0, XD-09 1/0, XD-10 5/0, XD-11 3/0, XD-12 1/0 (+2), XD-13 1/0, XD-14 0/1, XD-15 2/1, XD-16 1/0, XD-19 4/0,
XD-21 1/0, XD-22 2/0, XD-23 2/0, XD-24 3/0, XD-25 2/0, XD-26 1/0, XD-27 4/0. The 13 ODMs: none (their chests are the
19-face kind faces standing by houses; none end-on, none at a house door). All 120 fixed: `facing` dropped in the L4
and the generator (the rule turns them); six moved off their ways (DD-12 negative and reserve, DD-15 strongbox, DD-21
box, XD-14 dormitory, XD-15 vault: the user's chest, now by the north wall east of the stair, 176 from its doorway);
three given the `facing` the audit passes where the rule cannot see what is beside them (XD-02 lamp_room, XD-12
guard_hall and quarters). Per-chest lists in lanes/A7.md and lanes/A8.md (42nd-session blocks); P5's gift chest is the
P5 lane's (its `facing` dropped in `gen_objects.py` and the L4).

**Rebuilt:** 51 maps (the 50 and XD-01, whose cabinet gives no `facing`), one at a time under each map's lock
(`output/xeen_chests/cyc.sh`): validate, record, build, install, audit (0 chest errors, no new error), install into
assets_dev, MAW reserve, exits (0), drops (only the known XD-02, XD-12, XD-15 pockets), bake, playtests (all pass but
four entrance-window tests that start on the overworld: DD-26, XD-06, XD-21, XD-27 `playtest_in`/`playtest_way_in`, for
F16). After: the audit finds 0 chest faults on all 82 maps (`survey_after/`); key_npcs --write, check_actor_heights,
door_check, check_identity, xeen_balance --check clean; stale_bakes --check 0; build_world --check 0 differ.

**Captures.** The user's poses: `output/xeen_chests/before/user_fd03.png` -> `after/user_fd03.png` (the lock now faces
the room) and `before/user_xd15.png` -> `after/user_xd15.png` (the stair head is clear); `output/xeen_chests/sheet_user.png`.
One chest per fixed map, before and after from its room: `output/xeen_chests/shots/`, contact sheet
`output/xeen_chests/sheet.png` (the before maps were built from each run's `objects.before.yml` into a mount and drawn
with the new bake, so their light may be off).
