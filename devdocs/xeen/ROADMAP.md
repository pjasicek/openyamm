# Xeen: roadmap to a finished world

Written 2026-11-20. This is the production plan for turning the Xeen design (README and the documents it lists) into
a finished world of MM6/MM7 quality: every map built, every house lived in, every quest wired, travel and fast travel
working, monsters and treasure on the MM6–MM8 curve. It is written for one orchestrator session, eight lane sessions
and an optional 3D session working in parallel. It replaces PRODUCTION.md §4–5 (mock-ups and phases); PRODUCTION's
id ranges, engine list and content routes stay valid where this file does not change them.

Read first: README (decisions), WORLD_DESIGN, MAPS §0, QUESTS, MONSTERS_AND_ITEMS, CHANGES_FOR_BUILT_MAPS,
ACT2_BUILD (how the last five maps were built and what went wrong), `devdocs/map_studio/HANDOFF_LEAD.md` §2 and §5
(the user's preferences), `openyamm-studio/README.md`.

## 0. The goal

"Finished" means a player can start a new Xeen game and play to the ending with no stand-in, no placeholder and
nothing that tells them the world is unfinished, and the world feels as full as MM7. Concretely:

| Area | The bar | Source of the numbers |
| --- | --- | --- |
| Maps | 13 surface ODMs, 3 sky maps, 4 planes, the finale, Shangri-La, 58 dungeons, Bosco's Hall, the arena (82 maps) | WORLD_DESIGN §3, MAPS |
| Monsters | 66 Xeen families as their own rows (no MM7 stand-ins), one row per named boss; about 4,200 monsters; kill XP per act within 15 % of MAPS §0 | MONSTERS_AND_ITEMS §2–3 |
| Treasure | Treasure levels and chests on the MM6–MM8 table; gems as a second currency; about 15 fixed artifacts and relics, MM6–MM8 artifacts in level-6 loot | MONSTERS_AND_ITEMS §4 |
| Towns | Every service house open with its own name, owner and stock; every residence with 1–3 named residents (portrait, profession or topic); 300–380 named NPCs, two thirds with topics | WORLD_DESIGN §5; MM7: 446 NPCs, 247 in houses, 332 with topics |
| Teachers | About 120 offers, three per skill (Expert, Master, Grandmaster in different towns, Grandmaster late or remote), in houses and on the road | WORLD_DESIGN §5.3; MM7: 145 offers |
| Training | Halls and caps as WORLD_DESIGN §5.1 | adopted 2026-11-14 |
| Quests | 42 main steps, 54 side quests, about 20 promotion quests; each with a journal line, an autonote per step, a reward on the curve | QUESTS; MM7 77 journal lines |
| Systems | Newcastle and Castle Kalindra stages, five cursed towns that open, obelisks (13), wells, fountains and shrines (about 45), the arena, the carnival, gemsmiths, seers | QUESTS §4 |
| Travel | Map edges, stables, boats, the mirror network, the travel pyramids, Lucio's sky boats; Town Portal (6 towns per face), Lloyd's Beacon, a Dimension Door entry | WORLD_DESIGN §3.3 |
| Presentation | Own new-game card, loading screens, minimaps, music per area, ambient sounds, sky presets per face, weather, lighting bakes, NPC portraits, completion certificate | PRODUCTION §2–3 |
| Tests | A playthrough chain from a new game to the ending (`tests/playthrough/xeen/`), one scenario per side quest, every map's playtest, MM6–MM9 unchanged | `tests/playthrough/PLAYBOOK.md` |

The per-map bars are in §5.1 (maps), §5.2 (textures), §5.5 (towns) and §5.7 (quests).

## 1. State on 2026-11-20

- **Design:** complete as a proposal; decisions of 2026-11-13 and 2026-11-14 applied; ten open questions remain (§2.2).
- **Built:** 11 of 82 maps: X1, X2, XD-01 to XD-06, XD-12, XD-21, XD-27. They are installed in the scratch root
  `output/studio_play/xeen_root` and played with `--world mm7`. All Xeen-specific content is stand-ins:
  - houses open MM7 Harmondale and Erathia rows under Xeen names, with MM7's residents and teachers;
  - monsters are MM7 kinds, and bosses are ordinary rows;
  - quest items are MM7 items;
  - the stables and the dock open MM7 routes, and the mirror, the pyramid and Nystor's boat are messages or teleport
    events.

  CHANGES_FOR_BUILT_MAPS lists their design corrections; none is applied.
- **Map Studio** (`openyamm-studio/`, committed 2026-11-17, merge 40) builds the following:
  - geometry, doors, movers and chests;
  - monster placement and relations;
  - events compiled to Lua;
  - atmosphere;
  - the map's stats, bolster and travel rows.

  It authors no houses, NPCs, teachers, dialogue, items, journal, boats, stables or mirrors.
- **Engine:** no Xeen work since 2026-11-16. A fifth world mounts as content, but these parts assume four worlds or
  only MM9: the new-game cards, the Town Portal groups, Dimension Door, the world tables that only load for MM9 (E1),
  the terrain tileset choice, and the saved map state identity. §7 has the full list with file references.
- **No world package:** there is no `assets_dev/worlds/xeen`. House, NPC, quest-bit and map-stats rows can only go into
  the engine's shared tables today, which would mix the uncommitted world into tracked files.

The central lesson of the last week: building maps before the world exists produces maps that must be relinked later
(houses, monsters, items, quest bits, travel). From here on **no map is built against stand-ins**.

## 2. Decisions

### 2.1 Taken (the user, 2026-11-20)

- The world lives where it belongs, in `assets_dev/worlds/xeen/`. That folder is git-ignored for now (`.gitignore`),
  so nothing of it is committed until the user says so. Engine and tool changes are tracked as usual.
- One orchestrator, eight lane sessions, optionally one more session for 3D models (§3).
- Lanes may call Codex image generation for textures wherever it makes the result better, inside the texture budget
  of §5.2: a bit more than MM7/MM8, never several times more.
- The goal is the whole game at MM6/MM7 quality with every OpenYAMM system the world needs (progression curves,
  quests through OpenYAMM's quest route, travel, vendors, teachers, promotions, Town Portal and the rest).

### 2.2 Open: work proceeds on the default

Since 2026-11-20 every design question, these included, is decided by a new Opus decider agent rather than the user
([DECISIONS.md](DECISIONS.md), "How a question is decided").

The orchestrator puts these to the user in one batch at its first start. Until answered, the default stands. The
"cost of changing later" column says what a late change breaks.

| # | Question | Default | Cost of changing later |
| --- | --- | --- | --- |
| Q1 | Fly (restricted on sky maps and story castles) or MM9's Fleet Foot | Fly, with WORLD_DESIGN §3.4's rules | Low: the restrictions drop |
| Q2 | Interleave Darkside from about level 14, or play the faces in sequence | Interleave | High after phase 3: levels of D1–D3 |
| Q3 | Full plan or the lean variant | Full; decided for good at gate G1 | Medium: X3/D5/sky/planes merge |
| Q4 | Light/Dark promotion per character or per party | Per character (engine O2) | Low |
| Q5 | Artifacts: MM9's black-chest rule or MM6–MM8 random level-6 drops | MM6–MM8 random (existing MM6–MM8 artifact rows), plus the fixed Xeen quest artifacts and relics as new rows | Low |
| Q6 | NPC portraits and monster references from Xeen's own sprites | Xeen sprites are references only; portraits are generated new in the MM7 portrait style | Medium: re-run portrait batches |
| Q7 | Gems as a second currency | Yes (Lua, E13) | Medium: vendor scripts |
| Q8 | Xeen's Barbarian class and Gnome race | Left out | Low |
| Q9 | Music | MM6–MM8 tracks by area, by number (E10); since U-10 (2026-11-22) also Xeen's own eight themes, tracks 92001–92008 (MUSIC.md) | Low |
| Q10 | One world with two faces | Yes (D1) | Very high |
| Q11 | Indoor and outdoor disagree on whether a peaceful group or a relation row wins (ACT2_BUILD, end) | The relation row wins on both, as outdoors | Low |
| Q12 | HANDOFF §0 "not reconciled" (L dungeon size, outdoor density bands) | The adopted table (L 70–80 plus bosses; outdoor 90–135) | Medium: XP budget re-run |

## 3. Team and ownership

| Session | Owns | Never touches |
| --- | --- | --- |
| **O, orchestrator** | `devdocs/xeen/STATUS.md` (the tracker, §9), `assets_dev/worlds/xeen/world.yml`, `source/maps.yml` (the map registry), id ranges, assignments, merge points, the user's decisions and reviews, gate checks, handoffs, this roadmap | Map projects, engine code (asks A1) |
| **A1, platform and integration** | Engine and game code (`game/`, `engine/`, `core/`), `openyamm-studio/` (unless a Map Studio lead session runs in parallel; then A1 sends it the requests), the `build-xeen/` build tree, `tools/xeen/` checks, packaging, the playthrough runner, regressions on MM6–MM9 | Content |
| **A2, data and balance** | `source/monsters.yml`, `source/items.yml`, `source/treasure.yml`; the generator driver `tools/xeen/build_world.py`, its shared table writer `tools/xeen/xeenlib.py` and its modules `gen_monsters.py`, `gen_items.py`, `gen_maps.py` (map_stats, travel and bolster rows from `maps.yml`); item icons; the balance recount `tools/xeen/balance.py`. A3 and A4 own their own modules (`gen_quests.py`, `gen_towns.py`), which the driver calls | Map projects |
| **A3, story and quests** | `source/quests/`, `source/npcs/` topics and texts, `worlds/xeen/events/common/`, journal, autonotes, awards, books and scrolls, promotions, obelisk lines, the original-lines ledger, the playthrough segments' quest steps | House rosters (A4), map geometry |
| **A4, towns, services and travel** | `source/towns/<map>.yml` (houses, residents, teachers, shop stock, guild spells, hours, training caps), transport (stables, boats, mirrors, pyramids, sky boats), Town Portal and Dimension Door pages and art, the Adventurer's Inn roster, hirelings, house pictures, NPC portraits | Quest logic (A3) |
| **A5, outdoor lane 1** | Its assigned surface and sky maps (§6): `devdocs/xeen/briefs/<key>/`, `output/studio_cal/<key>/` | Other lanes' maps |
| **A6, outdoor lane 2 and art direction** | Phases 0–1: world and material boards, the building and dungeon kits and their texture families, `source/textures.yml`. Later: its assigned surface, sky and plane maps | as A5 |
| **A7, dungeon lane 1** | Its assigned dungeons (§6) | as A5 |
| **A8, dungeon lane 2** | Its assigned dungeons (§6); phase 0 also the dungeon graphs (MU-6) of the next act | as A5 |
| **S, 3D (optional)** | New creatures and their colour tiers, new decoration props, ground models of new item bases (§5.3); installs through `tools/install_model.py --world xeen` | Tables (sends A2 the model names) |
| **MX, MAW in Xeen** (added 2026-11-21 by the fourth orchestrator, the user's request) | `devdocs/maw/XEEN_SUPPORT.md`, `assets_dev/engine/rulesets/maw/worlds/xeen/`, the Xeen columns of MAW's tables (`data/promotions.yml`), `tools/maw/xeen_*`, the MAW guide's Xeen parts (`tools/maw_site/`); E2's "MAW rules" and phase 7's MAW balance file | Xeen's own tables, quests and maps (requests to their owners); MAW's MM6–MM9 behaviour without the user |

Rules that keep nine sessions out of each other's way:
- **One owner per file.** Generated tables are written only by their generator, and source files only by their
  owner. A request for a change in someone else's file goes to that owner with `SendMessage`. Name sessions by role
  (`xeen-o`, `xeen-a1` …) so messages need no lookup.
- **Map files** are installed into `assets_dev/worlds/xeen/maps/` by the lane that owns the map, with the studio's
  world install (A1, phase 0). That install writes only the map's own files; its table rows (map_stats, travel,
  bolster) come from `source/maps.yml` through the generator.
- **The binary.** A1 builds `build-xeen/` (the game, the unit tests, `oymap` into `openyamm-studio/build-xeen/`) only
  at merge points that O announces. No other session builds anything, and nobody uses `build/`, which other work
  rebuilds without warning (ACT2_BUILD: binaries replaced mid-check). The game for every Xeen run is
  `build-xeen/game/openyamm`.
- **Design questions** go to O under `DECIDE:`; O routes each to a new Opus decider agent and records the answer in
  [DECISIONS.md](DECISIONS.md). The user is not asked; the user reviews by playing.
- **Handoffs.** Each lane keeps `devdocs/xeen/lanes/<lane>.md` current: state, next step, open requests. A fresh
  session continues from that file plus STATUS.md.

## 4. The world package

```text
assets_dev/worlds/xeen/            git-ignored; mounted as world "xeen"
  world.yml                        O; identity, start, idRanges, tableContributions, rules (Fly, rim, faces)
  source/                          authoring sources; never mounted, never packaged (A1 excludes it)
    maps.yml                       O; every map: stem, id, face, name, music, treasure level, bolster, rules, TP flag
    monsters.yml  items.yml  treasure.yml                       A2
    towns/<map>.yml                A4; houses, residents, teachers, stock, transport per town
    npcs/<map>.yml                 A3; topics and texts of the NPCs A4 places (keyed by NPC id)
    quests/<id>.yml                A3; one file per quest (§5.7)
    textures.yml                   A6; every new texture: name, family, area, maps that use it, who made it
  data_tables/                     generated by tools/xeen/build_world.py; never edited by hand
  maps/                            map lanes, through the world install
  events/common/xeen_common.lua    A3; hand-written world helpers (mirrors, gems, stages, sky by qbit, rim fall)
  events/maps/<stem>.lua           written by the studio build of each map; never edited directly
  journal/  dialogue/              generated
  textures/  textures_x4/          A6 and map lanes (new textures only; shipped ones are referenced)
  models/  icons_x2/  terrain_materials/  terrain_decorations/  music/  ui/  rendering/
```

**Id ranges** (PRODUCTION §1, plus the domains the old plan missed; checked free on 2026-11-20 against the engine
tables: `house_data` ends at 1607, `npc.txt` at 1224, `quests.txt` at 1719, `autonote.txt` at 696, `map_stats` at 9080,
`transport_locations` at 101). A1 confirms each against MAW, the solo archetypes and any staged world before recording
it in `world.yml`:

| Domain | Range | | Domain | Range |
| --- | --- | --- | --- | --- |
| qbits | 110000–119999 | | houses | 4001–4999 |
| items | 12000–12999 | | NPCs | 4001–5999 |
| objects | 22000–22999 | | NPC topics and texts | 40000–49999 |
| monsters | 11000–11999 | | autonotes | 4001–4999 |
| vendors | 31000–31999 | | awards | 401–499 |
| decorations | 4001–4999 | | transport routes | 401–499 |
| sounds | 62000–63999 (16-bit monster sound columns; was 70000–79999) | | map_stats rows | 9101–9199 |

The 11 built maps' provisional ids (map_stats 9130–9140, items 12001–12299, qbits 110010–110599) are inside these
ranges. They stay as they are and are entered in the registries.

**Table contributions.** A world can already add rows to these tables: items, readable scrolls, item effects and sets,
random items, monster data and descriptors, sounds, decorations, vendors, service venues, trainer places, and MM9's
map transitions, teacher schedules, transport routes, skill trainers and hirelings. Xeen also needs these (A1, phase 0):
- houses: `house_data`, `house_animations` (residents), `house_exits`, `house_movies`;
- NPCs: `npc`, `npc_topic`, `npc_topic_text`, `npc_greet`, `npc_news`, `roster`, `teacher_topics`;
- quest state: `quests` (qbits), `autonote`, `awards`;
- maps and travel: `map_stats`, `bolster_maps`, `outdoor_travels`, `map_navigation`, `transport_index`,
  `transport_locations`, `town_portal_switch`;
- `chest_data` if new chest kinds are added, and `continent_settings`.

## 5. Content pipelines

### 5.1 Maps

The route is Map Studio's, unchanged: briefs L1 to L4 in `devdocs/xeen/briefs/<key>/` (tracked), generators and work
files in `output/studio_cal/<key>/`, the procedures `devdocs/map_studio/REBUILD_PROCEDURE.md`,
`OUTDOOR_REBUILD_PROCEDURE.md` and `TOWN_FEEL.md`, the models XD-01 to XD-05, XD-06, XD-12, XD-21, XD-27, X1 and X2
(their NOTES.md). What changes: every map is built with `world: xeen` against the world's own rows, from its first
L4. Sky maps, planes, the finale and Shangri-La use the open-air BLV route (`devdocs/INDOOR_OPEN_SKY.md`, MM9's
`level_generation/projects/mm9r_common/outdoor_blv.py`) through the studio where it can, by script where it cannot.

Before geometry, each map has its approved mock-ups (PRODUCTION §4): MU-3 plan and MU-4 eye-level concepts for an
outdoor map, MU-6 graph for a dungeon. O collects them for the user per act in one review page (§8) instead of one
by one.

**A map is done when** (each item a line in STATUS.md):

1. It builds clean: `validate`, `build`, `audit --reach --solve` with no dead handler and every key and lever
   reachable; `fmt --check`.
2. Its size and counts are inside its class bands (MAPS, Dungeons; WORLD_DESIGN §6), and its monster levels, groups
   and treasure level follow MAPS §0 with real Xeen rows. Bosses have their own rows.
3. Its textures are inside the budget (§5.2). One texture family per area. Props follow the dressing rule (the user,
   2026-11-20; `formats/DRESSING.md`): nothing blocks a door, doorway or passage; barrels, sacks and crates stand
   against walls or in corners, barrels mostly in pairs, clumps only in storerooms.
4. Outdoor maps:
   - all of MAPS's outdoor sheet checklist (one obelisk, 20–50 POIs, encounter areas, at least a third of the land
     quiet, chests with a reason, relief, the first fight 2,000–6,000 from each map-edge arrival and the new-game start; town arrivals
     keep the town buffer instead, D-15);
   - `town_feel` (with `--small` for a town of 9 services or fewer) with no figure out of range, or each one kept
     with a reason line under "Town feel exceptions" in NOTES.md (D-20).
5. Every house door opens a Xeen house with its residents (§5.5); every quest hook on the map is wired to its quest
   file (§5.7); every exit and arrival leads to the real neighbour.
6. At least three short original lines from its source map, with their `aaze` reference.
7. Presentation:
   - music by number;
   - ambient sounds;
   - sky preset and weather (outdoors);
   - minimap and terrain materials (outdoors);
   - a fresh lighting bake (`tools/lighting/stale_bakes.py` lists nothing for it).
8. Its playtest passes 4 of 4 (dungeon) or 2 of 2 (outdoor) from `assets_dev` with `--world xeen`, and its
   `playtest_hostility.yml` passes.
9. The lane has looked at its own screenshots (tours) and fixed what looks wrong before reporting.
10. NOTES.md says what was built, the measurements, the words the studio lacked, and what the user should look at.

### 5.2 Textures

Lanes may generate any texture that makes a map better with Codex (one `codex exec` worker per image, the route of
`level_generation/textures_xeen/README.md` and `level_generation/textures_x4/PLAYBOOK.md`: the family's x4 masters as
references, one gain for brightness, seamless tiling checked in a 3×3 repeat). Shipped MM6–MM8 textures come first;
a new texture is made when no shipped one fits the area's family, or a sign, picture or set piece needs its own.

Distinct face textures per map, measured on 2026-11-20 with `util/map_export.py`:

| | MM7 median / p90 / max | MM8 median / p90 / max | Built Xeen | **Xeen cap** | New textures per map |
| --- | --- | --- | --- | --- | --- |
| Dungeon S | all BLVs: 23 / 46 / 88 | all BLVs: 18 / 41 / 62 | XD-21 18, XD-27 14 | **30** | ≤ 4 |
| Dungeon M | | | XD-02 48, XD-04 49, XD-06 24 | **45** | ≤ 8 |
| Dungeon L | | | XD-12 45 | **70** | ≤ 14 |
| Outdoor ODM | 103 / 126 / 142 | 71 / 103 / 151 | X1 60, X2 52 | **120** | ≤ 12 beyond its kit |

World total: MM7 uses about 535 distinct textures indoors and 469 outdoors. Xeen's new textures stay **at or below
450** across the world: the six kits at no more than 30 each (about 180) plus each map's own (about 270). XD-01 (57)
and XD-03 (62) are over their caps; their rebase trims repeats of one family where it is cheap, and is not blocked by
it. `tools/xeen/texture_budget.py` (A1) counts each installed map against its cap and the world against 450. A6 keeps
`source/textures.yml`, the list of every new texture, so a second lane reuses a texture instead of making its own.

### 5.3 Monsters

- **Data (A2):** `source/monsters.yml` holds the 66 families with A/B/C tiers and named bosses (MONSTERS_AND_ITEMS §2
  levels; HP = L²/10 + 3L, XP = L(L+10), AC and damage by level from `devdocs/mm9_rework/BALANCE_PLAN.md` §7.1,
  resistances, special attacks, spells). It also holds per-family `relations` (the hostility rules of ACT2_BUILD
  made world data, so map lanes stop writing relations per map), `modifiers.yml` entries for bosses and signature
  monsters, and actor scripts where the source has a trick (breeder slimes split, the Megadragon). The generator
  writes `monster_data`, `monster_descriptors` and `relations.yml`. Rows are made one act ahead of the maps that use
  them.
- **Models (S, or A2 when there is no S):**
  - About 52 families reuse installed models through colour tiers
    (`level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`).
  - New creatures in the order the acts need them: Act I–II the toad, the swarm, the witch, the sprite; Act II–III the
    magic constructs (Flying Feet, Guardian, Carnage Hand: the most Xeen monsters), the mole, the female caster;
    Act III–IV the arthropod rig (scorpion, electrapede, mantis), the sabertooth, the sand worm and armadillo, the
    octopod; optional the tusked orc and the ninja.
  - Every new creature follows CLAUDE.md's creature rules (five HD masters first, the playbooks, the texture quality
    pass).
  - Until a family's model exists, its row points at the nearest installed model, listed in `monsters.yml` as
    `model_stand_in`. That is data, not a map stand-in, and goes away when the model is installed.

### 5.4 Items, artifacts and treasure (A2)

- New bases (about 60–90 rows: katana, scimitar, flamberge, naginata, glaive, pike, bardiche, great axe, flail,
  sling, robes, scale/ring/splint mail, the amulet-slot variants) with the material ladder as names, standard
  enchants (MONSTERS_AND_ITEMS §4.2), icons through the icon pipeline, ground models through the 3D ground-item
  playbook.
- About 15 artifacts and relics (MONSTERS_AND_ITEMS §4.2 table) as new rows with their effects. MM6–MM8 artifacts
  appear in level-6 loot by default (Q5).
- Quest items for every quest file: keys, the Megacredits, the Energy Disks, the Yak Stone, the Pyramid Sigil, the
  Soul Box and the rest, each with an icon and a readable description.
- Gems: the existing gem items in random loot at all levels; vendors that take gems are Lua (E13).
- `random_items` rows for the new bases by tier; treasure levels per map from `source/maps.yml`.

### 5.5 Towns, houses, teachers, vendors (A4)

One `source/towns/<map>.yml` per surface map (and per town BLV). Each house has:
- a type (one of the MM6–MM8 services, a residence, a guild or a hall);
- a name and its opening hours;
- its residents: 1 usually, 2 or 3 where the source or the story has them, each with a portrait, profession or role,
  greeting, and topic keys that A3 fills;
- teacher offers: skill, mastery, price;
- shop stock tier and item kinds;
- guild spell lists;
- the training cap, temple services, bank, tavern food and rumours;
- transport routes (destination, days of the week, price, travel days).

The generator writes `house_data`, `house_animations`, `house_exits`, `house_movies`, `npc`, `npc_greet`,
`teacher_topics`, `trainer_places`, vendors and `transport_*`. A4 also places the street townsfolk, guards and
hirelings (MM7/MM8 street peasants and the Adventurer's Inn roster), and makes the house pictures and NPC portraits
(Codex, the dense64 batching route of `level_generation/ui/hud_inventory/BATCHING_DENSE64.md`).

Checks (`tools/xeen/towns.py`, A4):
- every house door on every built map has a row, and every row is on a map;
- residences per town are inside WORLD_DESIGN §5's numbers;
- teacher offers world-wide come to about 120, three per skill in three towns, with every Grandmaster in a late or
  remote place;
- the services per town match its role (start and hub complete, regional 6–9, wilderness 0–3, cursed towns before
  and after their quest);
- every named resident has a portrait and either a profession or a topic.

### 5.6 Travel and fast travel (A4, with A1 for the engine side)

| Link | How |
| --- | --- |
| Map edges | `source/maps.yml` neighbours → `outdoor_travels` (5 days, 7 in the wilderness) |
| Stables and boats | Transport houses with MM6–MM8 routes, 1–3 departures a week (WORLD_DESIGN §3.3: Vertigo, Rivercity, Burlock, Castleview, Sandcaster, Kalindra stage 4; Nystor's boat, the Lakeside ferry) |
| Mirrors | Free transport houses whose list holds every mirror the party has touched on that face (qbits), Darkside's after Kalindra stage 4. Built on E1's generalised `map_transitions` or as Lua over `evt.MoveToMap`, whichever A1 delivers first |
| Travel pyramids | Lua at the pyramid (X1 ↔ D1 after M7; Shangri-La ↔ Alamar late); "the moons are not aligned" before |
| Sky | Tower roofs one way up, falls one way down (E4); Lucio's celestial boats as a transport house after M30 |
| Town Portal | 12 destinations (6 per face, WORLD_DESIGN §3.3) on two face pages, each unlocked by touching that town's mirror; art from Codex in the Obsidian style |
| Lloyd's Beacon | Works everywhere except the maps with `noTeleportMaps` |
| Dimension Door | One more destination for Xeen |

### 5.7 Quests, dialogue, journal, promotions (A3)

One `source/quests/<id>.yml` per quest (M1–M42, Q-C1 to Q-C28, Q-D1 to Q-D28, Q-F1 and Q-F2, promotions T1-A to T1-E,
the Light/Dark tier and the racial ones). Each file holds:
- id, act, giver, maps;
- prerequisites (qbits, items, level);
- its steps (qbit, journal line, autonote);
- the items given and taken;
- rewards: experience by QUESTS's rules, gold, items by treasure level;
- the topic texts of every NPC involved;
- the map hooks the map lanes wire (`hook: q-c3.tiara_vault`);
- the answer-giver of any password or riddle (README 2026-11-13);
- its playthrough step for the chain.

The generator writes `quests`, `autonote`, `awards`, `npc_topic`, `npc_topic_text` and `npc_news`, and a hook table
the studio projects reference by name. World helpers are hand-written in `events/common/xeen_common.lua`:
- the mirror list and gem payment;
- staged maps by qbit (Newcastle, Kalindra, cursed towns, the sky presets of the failing sun);
- the rim fall;
- time-of-day gates;
- the promotion dialogue.

The promotion dialogue follows MM9's composite model (`assets_dev/worlds/mm9/dialogue/promotions.yml`) with the
Light/Dark split per character (Q4).

Text follows WORLD_DESIGN §1's voice: short lines; original MM4/MM5 lines quoted where they are short; English in the
tables, `Engine::tr()` keys for any C++ text; language packs at the end (phase 7).

**The quest audit** (`tools/xeen/quests.py`, A3) proves, from the quest files and the maps' hooks, that:
- the main path is solvable in the designed order (both orders of Act V);
- every qbit has a writer and a reader, and every given item has a use;
- every hook a quest names exists on its map;
- quest experience per act stays within its budget (MAPS §0).

### 5.8 Presentation

| What | Who | How |
| --- | --- | --- |
| New-game card, start, party creation | A1 (code), A4 (art) | E2; continent card art by Codex |
| Loading screens per face | A4 | Codex, as MM9's |
| Music by area | O decides per map in `maps.yml`; town districts in `world.yml` `musicAreas` | MM6–MM8 track numbers and Xeen's 92001–92008 (Q9, U-10) |
| Ambient sounds | map lanes | Placed sounds (studio), ODM emitters after E9 |
| Sky presets | A6 | Cloudside presets from the shipped set; `xeen_darkside_day`, `_fading`, `_failing`; the sky maps' cloud sea (`level_generation/lighting/SKY_RENDERING.md`) |
| Weather | outdoor lanes | `weather.yml` per map (rain, snow on X5, ash on X7 and D6) |
| Lighting bakes | map lanes | `tools/lighting/` (outdoor and indoor) |
| Minimaps, terrain materials, grass | outdoor lanes | `tools/terrain_materials.py`, meadow and grass docs |
| Completion certificate | A4 | `world.yml` `completion` (phase 6) |
| Language packs | A3 | `tools/l10n.py` (phase 7) |

### 5.9 Balance (A2)

`tools/xeen/balance.py`, the successor of `output/xeen_review/combat/proposed.py`, reads the installed maps and the
tables and reports per map and per act:
- monsters at load, their levels and kill XP;
- quest XP and gold;
- treasure levels and chests;
- artifacts placed.

Each is reported against MAPS §0 and QUESTS's budgets. It runs at every gate; an act more than 15 % off is trimmed
before the next phase. The MAW balance file for Xeen comes in phase 7.

### 5.10 Tests (A1 runs, owners write)

- Map playtests and hostility scenarios (map lanes), as now.
- The playthrough chain `tests/playthrough/xeen/` (`tests/playthrough/PLAYBOOK.md`, MM9's as the model). A3 writes
  each act's segments with its quests; A1 keeps the runner and runs the chain at each gate, with `--reload`.
- One scenario per side quest (`tests/scenarios/xeen/side_quests/`, A3).
- Regressions at every merge point (A1): unit tests, MM6–MM9 start, travel, Town Portal and a save/load of each, and
  the release scenarios. None of the Xeen tests go into CI while the world is git-ignored.

## 6. Phases, gates and the map allocation

Each phase ends in a gate: A1 runs the checks, A2 the balance report, O assembles one review page with play commands,
and the user plays. The next phase's map lanes start their mock-ups while the gate is open. Since 2026-11-20 a
mock-up is approved by a decider agent (DECISIONS.md), which checks it against the shipped references and the user's
known preferences, and its open questions are decided the same way; geometry starts once that decider has approved
it. The user judges the results by playing at the gates and may overrule any decision.

### Phase 0: the world exists (no new maps)

| Lane | Work |
| --- | --- |
| O | Ask Q1–Q12; create STATUS.md, `world.yml`, `source/maps.yml` with all 82 maps (ids, stems, faces, neighbours, music, treasure levels); lane files; announce merge point 1 |
| A1 | The world package mounts as `xeen`. In order: table contributions (§4); tileset for a new world (`TerrainTileData.cpp:111`); saved map state identity (`MapLayoutIdentity.cpp:254`); E2 (new-game cards, portrait filter, continent id, Dimension Door); Town Portal groups and buttons driven by data; E1 (the seven MM9-only loaders); `oymap install` into a world (map files only); `build-xeen/`; packaging excludes `xeen` and `source/`; `texture_budget.py`; the playthrough runner for `--world xeen` |
| A2 | `build_world.py` with `monsters.yml` and `items.yml` for Acts I–II (the families of X1–X4 and their dungeons, the bosses, the quest items of those acts); relations and modifiers; `balance.py` |
| A3 | The quest file format; Act I's quests in full (M1–M4, Q-C20–Q-C22, T1-A), Act II's outlined; `xeen_common.lua` first helpers; the hook table |
| A4 | The town file format; Vertigo and Rivercity in full (houses, residents, teachers, stock, guilds, training caps, stables, the dock); the Adventurer's Inn roster; the Town Portal page design; the first portrait batch |
| A5 | Rebase X1: CHANGES_FOR_BUILT_MAPS X1-1 to X1-13 and the move to `world: xeen` as soon as A1's install lands; then X2's rebase |
| A6 | Art direction: MU-1 world boards, MU-2 material boards, MU-5 house kit boards; the six kits' texture families; `source/textures.yml` |
| A7 | Rebase XD-01 to XD-05 (CHANGES A1–A7 and per map) |
| A8 | Rebase XD-06, XD-12, XD-21, XD-27; MU-6 graphs for Act II's new dungeons |
| S | Act I–II creatures: toad, swarm, witch, sprite; colour tiers for Act I–II's reused families |

**Gate G0:**
- a new Xeen game starts in Vertigo from the new-game screen;
- X1 and its five dungeons are installed in `assets_dev/worlds/xeen` with no MM7 stand-in;
- Vertigo's houses open their Xeen residents;
- Town Portal shows the Xeen page;
- MM6–MM9 are unchanged (A1's regressions).

### Phase 1: Act I finished (the vertical slice, now for real)

Everything Act I needs at the bar of §0:
- X1 and XD-01 to XD-05 complete;
- Vertigo's NPCs, teachers and shops;
- Joe's scam;
- the orc outposts burnable;
- the Crusader title and T1-A;
- the pyramid's "the moons are not aligned";
- stables to X2 and the boat;
- the playthrough segments from a new game to the Crusader title;
- Act I's creatures;
- music, ambience, bakes.

Map lanes finish the rebases of X2, XD-06, XD-12, XD-21 and XD-27, and draw Act II's mock-ups.

**Gate G1 (the verdict):** the user plays Act I from a new game. O records:
- the verdict;
- the measured cost per map and per kind of content (tokens and hours);
- the full or lean decision (Q3).

O then re-plans phases 2–6 on those numbers.

### Phases 2–6: one act each

| Phase | Act | A5 outdoor 1 | A6 outdoor 2 | A7 dungeons 1 | A8 dungeons 2 |
| --- | --- | --- | --- | --- | --- |
| 2 | II Cloudside (7–20) | X4 Burlock Savannah, X3 Lifeforce Lagoon | X5 Winterkill Tundra (XD-09 and XD-10 stand on it), X8 Cloudreach (sky) | XD-07 Castle Burlock, XD-25, XD-26, XD-13 Newcastle Keep (staged), XD-08 | XD-09 Golem Dungeon, XD-10 Cave of Illusion, XD-11 Tower of High Magic |
| 3 | III The Land Below (18–30) | D3 Sandcaster | D1 Castleview Vale, D2 Sprite Forest | XD-22, XD-23, XD-24, DD-06, DD-13, DD-11 (3 pockets) | DD-01, DD-04, DD-02, DD-09, DD-10 (3 pockets), DD-18, DD-03 Castle Kalindra (staged) |
| 4 | IV Unmasking (30–42) | X6 Desert of the Sphinx | D4 Lakeside and Blackfang | XD-14, XD-15, XD-20 Warzone, DD-23, DD-07 Eastern Tower (moved by D-9.3) (XD-12 finished in phase 1) | DD-05, DD-20, DD-12, DD-14 Castle Blackfang, DD-19 |
| 5 | V Two Thrones (42–55) | X7 Mount Firestone, X9 Clouds of Xeen (sky), XD-17 Shangri-La (open air) | D5 Desert of Doom, D6 The Forbidden Zone | XD-19 Castle Xeen (L), XD-16, DD-24, DD-16 | DD-15 Great Pyramid (L), DD-17 Castle Alamar (L), DD-08, DD-21, DD-25 Bosco's Hall |
| 6 | VI One World and optional (55–70) | P5 Clouds of the Ancients; outdoor polish from the gates | D7 The Skyroads, P1–P4 planes | FD-02, FD-03, XD-18 Dragon Cave, FD-04 | FD-01, DD-22, DD-26 |

In every phase:
- A2 makes the act's rows one phase ahead, A3 the act's quests and segments, A4 the act's towns, travel and Town
  Portal entries, and S the act's creatures.
- A1 closes the engine items the act needs (§7) and the studio's words; from phase 2 on, it also takes over map work
  O gives it when its queue is short.
- Each gate is the user playing the act through the playthrough chain's save at its start.

### Phase 7: release quality

- The balance pass over the whole world.
- Lighting bakes re-run (`stale_bakes.py` empty).
- Language packs.
- The MAW balance file (`rulesets/maw/worlds/xeen/`).
- The completion certificate.
- The full playthrough chain with `--reload`, and every side-quest scenario.
- Packaging config for the day the user decides to commit and ship the world.

## 7. Engine and tool work (A1)

From the code audit of 2026-11-20 (line numbers as of that day; `GameApplication.cpp` was being edited then). Phase is
when it must land.

| # | Work | State | Phase |
| --- | --- | --- | --- |
| W1 | Table contributions for houses, NPCs, quests, autonotes, awards, map_stats, travel, Town Portal, roster (§4) | missing | 0 |
| W2 | Terrain tileset for a world other than MM6/MM7 (`TerrainTileData.cpp:111-125` sends it to MM8's) | missing | 0 |
| W3 | Saved map state identity for a new world (`MapLayoutIdentity.cpp:254`) | missing | 0 |
| E2 | New-game cards (`NewGameScreen.cpp:2559`, `continent_selection.yml`), portrait filter, world → continent id, Dimension Door columns, MAW rules | missing | 0 (MAW: 7) |
| W4 | Town Portal groups and buttons driven by data (`GameplayUiRuntime.cpp:146`, `GameplayOverlayTypes.h:400`); two face pages | partial | 0 |
| E1 | The seven world-table loaders that return early unless the world is MM9 (`GameDataLoader.cpp:2755-3047`) | missing | 0–1 |
| W5 | `oymap install` into a world (map files only, `world: xeen`), and the studio reading the world's tables | missing | 0 |
| W6 | Packaging, CI and the texture cook skip `xeen` while it is git-ignored, take it when it ships | missing | 0 / 7 |
| E14 | Boss rows (data, A2); custom names for placed monsters outside MM9 (`ActorNameResolver.cpp:19`) | partial | 1 |
| Q11 | Hostility order indoors and outdoors | differs | 1 |
| E5 | World-rim fall: an outdoor trigger volume that runs an event (`OutdoorSceneYml.cpp:956-980` has damage, destroy, remove only) | missing | 1 |
| E4 | Sky-map fall-through: the same trigger plus a Lua helper that maps the position to the surface map below | partial | 2 |
| E7 | `allow_fly` per map (sky and story castles); the studio writing `no_spells` | partial | 2 |
| E9 | Outdoor ambient sound emitters | missing | 2 |
| E6 | Staged maps: faces, actor groups and sky by qbit already work through Lua; a declarative form only if Lua proves fragile | works in Lua | 2 |
| O2 | Light/Dark promotion per character | missing | 3 |
| E11 | The weapon in the damage hook, and the hook outdoors (Lord Xeen and the Slayer Sword) | partial | 5 |
| E10 | Music by name | missing | optional (numbers work) |
| O1 | Energy and Magic weapon enchants; golem, insect, beast slaying | missing | optional |
| E12, E13 | Time-of-day gates, gem payment | work in Lua | — |

Studio words still open from the built maps (`devdocs/map_studio/briefs/SCHEMA_GAPS.md` and every NOTES.md "Words
needed"): actor behaviour hooks, rotating and riding movers, backdrop rooms and vistas, more than one arrival per
dungeon, outdoor destructible camps ("burn the camp", QUESTS §4.3), small surface words. A1 takes them in the order
the next act's maps need them; a map lane uses a written workaround meanwhile and records it.

## 8. Working rules for the sessions

- Read this file, STATUS.md and your lane file at every start; update your lane file before you stop.
- Never commit, stage, stash or reset. The world folder is git-ignored; tracked files (briefs, tools, engine) stay
  unstaged for the user.
- No stand-ins in a map that claims to be done. If a row, model or quest is missing, ask its owner and wait, or mark
  the line in STATUS.md as blocked.
- Game runs:
  - `build-xeen/game/openyamm`, with `--world xeen` and `--isolated <unique>`, minimised;
  - at most two game processes per lane;
  - wait on exact PIDs.
- Analyses run with at most two workers and a memory cap (a twelve-worker pool once killed the session).
- Distances in game units.
- Codex: one `codex exec` per image; raw returns kept; the budget of §5.2 checked before a map is reported.
- Look at your own pictures before reporting. The user reviews results by playing, not by being asked for
  screenshots.
- The user's reviews are relayed by O as marks per map; a lane answers each mark in its NOTES.md.
- Background agents inside a lane: one folder or one concern each, never two agents on one file.

### Review pages

O publishes one review page per gate as an Artifact (private), updated in place. It shows:
- what changed;
- play commands for each map;
- the before and after pictures;
- the balance report;
- the open decisions;
- what the user should look at.

## 9. STATUS.md

O keeps one table with a row per map and these columns:
- lane, phase;
- briefs (L1–L4);
- mock-ups approved;
- built and installed in the world;
- textures in budget;
- rows real (monsters, items);
- houses and residents;
- quests wired;
- travel linked;
- presentation (music, ambience, bake, minimap);
- playtest;
- playthrough segment;
- user-reviewed.

Below the map table are the content tables:
- A2's families and items (rows made, models real);
- A3's quests (written, wired, audited, segment);
- A4's towns (rosters, teachers, stock, portraits);
- A1's engine items.

A cell is a date or "blocked: <owner>".

## 10. Risks

| Risk | What keeps it small |
| --- | --- |
| Volume: 71 maps to build, 11 to rebase, two games of text | Phase 1 measures it; the lean variant at G1; one-act-at-a-time gates |
| Content lags behind maps again | No map is done without its houses, rows and quests (§5.1); the content lanes work one phase ahead |
| Texture sprawl | Caps per map and world (§5.2), `textures.yml`, A6 as the reuse point |
| Experience runaway | `balance.py` at every gate, trims before the next phase |
| Lanes colliding in one working tree | One owner per file; generated tables only by generators; `build-xeen/` rebuilt only at merge points |
| The user reviewing too much at once | One page per gate, mock-ups batched per act |
| Regressions in MM6–MM9 from engine work | A1's regression set at every merge point |
| Riddles nobody can answer | The quest audit lists every password and its answer-giver |

## 11. Starting the sessions

Orchestrator:

> You are the Xeen orchestrator (`xeen-o`). Read `devdocs/xeen/ROADMAP.md`, then README, HANDOFF and STATUS.md. Put
> §2.2's questions to the user in one batch. Create or update STATUS.md, `world.yml` and `source/maps.yml`, write
> each lane's file in `devdocs/xeen/lanes/`, then start the lanes for the current phase with their lane files as
> their briefs. Keep the gate checklist of the current phase, merge points with `xeen-a1`, and the review page.

Lane:

> You are `xeen-<lane>`. Read `devdocs/xeen/ROADMAP.md` (§3, §5 for your content, §6 for your phase, §8), STATUS.md
> and `devdocs/xeen/lanes/<lane>.md`, then the documents your lane file names. Work only in the files you own. Report
> to `xeen-o` when an item meets its definition of done, with its STATUS.md line.
