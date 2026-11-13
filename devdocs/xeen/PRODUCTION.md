# Xeen: production plan

Proposal, 2026-11-12. Part of the [Xeen world design](README.md). What has to exist in the engine, how each kind of
content is made, which mock-ups come before any geometry, and in what order. Effort figures are from this repository's
track record (`research/MAP_CRAFT_CALIBRATION.md` §5.3, `research/MM678_CALIBRATION.md` §6).

## 1. World package

`assets_dev/worlds/xeen/`, built like MM9's (`assets_dev/worlds/mm9/world.yml`, 249 lines) with the layout listed in
`research/MM678_CALIBRATION.md` §6 (maps, events, journal, dialogue, data_tables, icons_x2, models, terrain_materials …).

Proposed id ranges, after MM9 and the staged Hesper world (`output/hesper_stage/.../worlds/hesper/world.yml`). Check
again against any other world staged by the time this starts:

| Domain | MM9 | Hesper | **Xeen** |
| --- | --- | --- | --- |
| qbits | 90000–99999 | 100000+ | **110000–119999** |
| items | 10000–10999 | 11000–11999 | **12000–12999** |
| objects | 20000–20999 | 21000–21999 | **22000–22999** |
| monsters | 9000–9999 | 10000–10999 | **11000–11999** |
| vendors | 30000–30999 | 9300–9499 | **31000–31999** |
| decorations (rows) | 2001–2999 | 3001–3999 | **4001–4999** |
| sounds | 50000–59999 | 60000+ | **70000–79999** |
| map_stats rows | 9001–9080 | — | **9101–9199** |

Engine-side rows the world adds in `assets_dev/engine/` (the same list as MM9): map_stats rows, continent_settings,
the new-game card in `character_selection.yml`, small rows in character_data, chest_data, object_list and
monster_projectiles, Town Portal pages, and later `tools/packaging/packs.yml` and MAW's `rulesets/maw/worlds/xeen/`.

## 2. Engine work

Nothing here is large; most of it removes MM9-only assumptions so that any third world can use what MM9 already built.

### 2.1 Required

| # | Work | Why | Notes |
| --- | --- | --- | --- |
| E1 | **Generalise MM9's world-local table loaders** (`GameDataLoader::loadMm9*`: map_transitions, teacher_schedules, transport_routes, skill_trainers, hirelings) to any world that declares them in `tableContributions` | Outdoor teachers, the mirror network and Lucio's boats use them | The calibration note counts 28 `== "mm9"` checks; only the ones about these shared features change |
| E2 | **Remove the four-continent hard-codes** (new-game cards, the party sheet's portrait filter, Dimension Door, world → continent id, MAW item rules) | A fifth world | `research/MM678_CALIBRATION.md` §6 lists the five places |
| E3 | **Two faces in one world**: Town Portal page, loading screens, death map and default sky per face | WORLD_DESIGN D1 | Probably a second continent id owned by the same world. Investigate first; pick whichever needs the fewest special cases |
| E4 | **Fall-through on sky maps**: a fall below the cloud floor moves the party to the surface map underneath at the matching position | Sky maps (X8, X9, D7) and the plane entrances | A trigger volume or floor face with an event plus one shared Lua helper that maps positions; check what `evt.MoveToMap` and the open-air BLV already allow |
| E5 | **World-rim falls** on ODMs: walking off the rim cliff kills (or teleports) the party | WORLD_DESIGN D9 | A rim-side trigger strip; the visual is data (`below_horizon: sky`) |
| E6 | **Staged maps**: show and hide BModel groups, faces and actor groups by qbit at map load, and open or close houses by qbit | Newcastle, Castle Kalindra, five liberated towns | `SetFacetBit`, `SetMonGroupBit` exist in `game/events/EventRuntime.cpp`; verify outdoor BModel visibility and house gating |
| E7 | **Per-map rules**: no Fly on open-air sky and plane maps; no spellcasting in Darzog's Tower; local always-overcast weather for Nightshadow | WORLD_DESIGN §3.4, XD-12 | Small map flags if they do not exist |
| E8 | **`xeen_darkside_dusk` sky preset** and the world's `terrain_materials/world.yml` (snow mapped onto an MM8 tile family; verify) | Visual identity | Data only, per `level_generation/lighting/SKY_RENDERING.md` |
| E9 | **ODM ambient sounds** (lava, waterfalls, wind at the rim) | Map craft | BLV has them, ODM not (MAP_CRAFT §4.3) |
| E10 | **A music table for the world** (track names to numbers), or numeric tracks on every map card | The Act I briefs name tracks (`cave`, `tower_dark` …), and the game refuses a map whose music is not a number ("invalid redbook track") | Found by the briefs' test builds, 2026-11-12 |

### 2.2 Optional

| # | Work | Benefit |
| --- | --- | --- |
| O1 | Energy and Magic damage weapon enchants; golem, insect and beast slaying | Xeen's item flavour (MONSTERS_AND_ITEMS §4.2) |
| O2 | Light/Dark promotion choice per character in the promotion dialogue | QUESTS §3.2 (otherwise per party, MM7 style) |
| O3 | Gem payment in dialogue vendors (talking skulls, dragon tax, gemsmiths) | Can be plain Lua over gem items |

## 3. Content routes

| Content | Route | Reference | Effort basis |
| --- | --- | --- | --- |
| Surface ODMs (13) | Building kit at native scale, planned terrain and road graph, headless build, terrain materials, minimap, bake, tours | Brackenford (`level_generation/OUTDOOR_CALIBRATION.md`, `VISUAL_CALIBRATION.md`), Hesper out1 | 1–2 days and 3–5 user review rounds each |
| Open-air BLVs (3 sky, 4 planes, finale, Shangri-La) | MM9's outdoor BLV route | `level_generation/projects/mm9r_common/outdoor_blv.py`, `devdocs/INDOOR_OPEN_SKY.md` | about 1 day each; smaller than ODMs |
| Dungeons (~54) | Hesper's BLV kit and plans, walkability audit | `design/kreegan_world/DUNGEON_PLAYBOOK.md`, `hesper_stage/blv_kit.py` | 0.5–1 day each once a kit and its textures exist |
| Building and dungeon kits | Six style kits: Cloudside town (half-timber), royal castle (white stone), witch/wizard towers (dark timber, slate), Darkside town (low slate stone), Sandcaster sandstone, Ancient tech (Alamar, pods, Castle Xeen machines; Hesper's sci-fi kits are the starting point) | Surface textures through `level_generation/textures_x4/PLAYBOOK.md` style generation | — |
| Creatures (10–13 new + ~41 recoloured families) | creature-to-3D (HD master references, Meshy, playbooks, colour tiers) | `.agents/skills/creature-to-3d`, the playbooks in CLAUDE.md | per creature project |
| Decorations | Reuse engine `mm6_/mm7_/mm8_deco_*` models; new props (rim crystals, cloud-stone, Ancient machinery, sundials, gongs, pedestals) through the prop route; world rows in the world package | `devdocs/WORLD_DECORATION_CONTRIBUTIONS.md` | — |
| Items (60–90 rows, ~15 artifacts) | Data rows + icons through the icon pipeline | MM9 items as the pattern | — |
| NPC portraits | Restored from Xeen's own face sprites (`sprites/*/` portraits) or generated, through the dense64 portrait route | `level_generation/ui/hud_inventory/BATCHING_DENSE64.md` | — |
| Text | 300–380 named NPCs, ~45 side quests, ~42 main steps; English source, localisation keys per `devdocs/LOCALIZATION.md` | — | the largest writing job |
| Music | Xeen's music is in a custom sequence format and is not usable directly; reuse MM6–MM8 tracks per area or commission new ones | — | user decision |

**What may ship.** The source's art, music and text are references. The world ships new maps, generated or restored art
and rewritten text, the same principle as the rest of this repository; whether restored Xeen portraits or sprites may be
used is the user's call (README, open questions).

## 4. Mock-ups before geometry

The user asked for good mock-ups of the designed things before they are built. Each item below is reviewed and
approved before its map is authored. They are cheap compared with a rejected map (Brackenford v1 failed on scale and
art after passing every functional test; MAP_CRAFT §5.1).

| Stage | Deliverable | Made with | Approves |
| --- | --- | --- | --- |
| MU-1 | **World boards**: a painted map of each face (with the rim and the sky layer), and the schematic of WORLD_DESIGN §3.1 | Codex image generation; SVG | Region arrangement, biomes, landmark positions |
| MU-2 | **Material boards per biome**: the Xeen native ground tiles beside the proposed library materials and the dressing palette (trees, rocks, plants) | Swatches from `terrain_materials`; native tiles from the extraction as reference only | Ground and dressing look per map |
| MU-3 | **Map plans**: per ODM, a to-scale plan on the 128 × 128 grid: height bands, water, road graph, town footprint, POIs, encounter areas, quiet places, arrival points, the signature view's sightline | SVG generated from a plan YAML that later drives the build | Composition, scale, density (MAPS sheets + the not-bland checklist) |
| MU-4 | **Eye-level concepts**: 2 per ODM (arrival view, signature view), 1 per sky map, 1 signature room per L dungeon | Codex image generation, from the plan's camera positions | Mood and silhouette |
| MU-5 | **House kit boards**: per kit, 6–10 house types in front elevation at native scale (128 × 256 doors), roof and wall textures, signs | SVG/blocked renders from the kit script, then a painted pass | Kit scale and variety (13 forms per 44 homes, HOUSE_VARIETY) |
| MU-6 | **Dungeon graphs**: room graph, state graph (keys, levers, stages), size class | From the plan YAML | Loops, set pieces, length |
| MU-7 | **Creature HD masters** | Codex, per the HD master reference step | Each new creature |

The review page linked from [README.md](README.md) already has MU-1 schematics and MU-3 first-pass plans for X1 and D1.

## 5. Phases

| Phase | Content | Proves | Rough size |
| --- | --- | --- | --- |
| **0. Decisions and groundwork** | User answers the open questions. E1–E3, E6, E8; world package skeleton; MU-3/MU-6 plans in Map Studio's shared `plan.yml` schema (`devdocs/map_studio/`; Xeen's needs in [PLAN_YAML_NEEDS.md](PLAN_YAML_NEEDS.md)), no separate Xeen plan tool | The world mounts and starts | days |
| **1. Vertical slice: Act I** | X1 Vertigo Meadows with Vertigo; XD-01 to XD-05; 8 families (orcs, toads, snakes, skeletons, zombies, slimes, mad dwarves, goblins/witches); M1–M4, Q-C20–Q-C22; promotion T1-A; Adventurer's Inn | Map craft at Xeen's look, a town, a dungeon kit, quests, a promotion. **Stop for the user's verdict before scaling up** | 1 ODM, 5 BLVs |
| **2. Cloudside** | X2–X7, X8, X9; Cloudside dungeons; Acts II, IV (Cloudside half), V (Castle Xeen); Newcastle; liberated towns; tier-1 promotions | A complete Clouds game ending at Lord Xeen. The pyramid says "the moons are not aligned" until phase 3 | 6 ODMs, 2 sky, ~22 BLVs |
| **3. Darkside** | D1–D7; Darkside dungeons; Acts III–V Darkside half; Castle Kalindra; tier-2 promotions; pyramid opens at M7 | The interleaved middle | 6 ODMs, 1 sky, ~26 BLVs |
| **4. Finale and polish** | P1–P5, FD-01 to FD-05; balance pass (`tools/` density and level audits like MM9's); playthrough tests under `tests/playthrough/xeen/` per act; side-quest scenarios; MAW balance file; lighting bakes | The ending; release | 5 small maps, 5 BLVs |

For scale: Hesper built 22 maps in about 10 days with many parallel agents and is still unfinished; this world is
roughly three to four Hespers of maps plus two games of writing. Phase 1 is the honest estimate-maker: measure it,
then re-plan phases 2–4.

### Lean variant

If the full plan is too large: merge X3 into X2 (Newcastle and Nightshadow move to Rivercity's south bank), merge D5
into D6 (the pyramid and the Northern Tower join the Forbidden Zone), one Cloudside sky map holding both X8 and X9 as
separate archipelagos, one elemental plane with four sleeper shrines, and the Dragon Tower, Dungeon of Death and
Sheltem's Pod cut. Result: 13 ODMs → **11**, sky 3 → 2, planes 4 → 1, dungeons 54 → about 45. The story is unchanged.

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| Volume: two games of maps and writing | Phase 1 slice first; the lean variant; reuse of 41 monster models and the engine decoration set |
| Maps that look empty or flat (Hesper's verdict) | MAPS checklist and MU-3/MU-4 approval before geometry; relief ≥ 2,500; every open patch has a written purpose |
| Two easy starts colliding | Interleaving (D4), Darkside's early maps raised to the open-middle band |
| Fly trivialising the sky and the castles | WORLD_DESIGN §3.4 rules; or the MM9 no-Fly rule |
| Number inflation of the source leaking in | QUESTS reward rules; no permanent levels; balance pass in phase 4 |
| MM6–MM9 regressions from engine work | E1–E3 are generalisations with tests; validate MM6–MM9 start, travel and Town Portal after each |
