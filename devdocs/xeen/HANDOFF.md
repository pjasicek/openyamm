# Handoff: Xeen world design and the Map Studio designer role

Written 2026-11-12 by session **openyamm-fe** for whoever continues.

**Superseded as the starting point on 2026-11-20 by [ROADMAP.md](ROADMAP.md)**, which plans the whole world with an
orchestrator and eight lanes. This file stays as the record of the design work and the Map Studio designer role up
to 2026-11-14; for what happened after it (the five Act II maps, the hostility pass), see
[ACT2_BUILD.md](ACT2_BUILD.md). Since then `devdocs/xeen/` and `devdocs/map_studio/` have been committed by the user
(2026-11-16 and 2026-11-17). Never stage or commit unless asked.

This session did two jobs:
1. **Xeen world design.** A new MM6–MM8-style world on the World of Xeen story, with all-new maps. It is finished as
   a proposal and waits for the user's answers (§1).
2. **The Map Studio "designer" role.** The user delegated, through the Map Studio session, the writing and refining
   of map *briefs*: four calibration rebuilds of shipped maps, and the Xeen Act I dungeons (§2). This work is ongoing.
   It moves in rounds driven by the Map Studio session's messages, which relay the user's in-game reviews.

## 0. State on 2026-11-14: the decisions after the reviews are applied

Three reviews (`reviews/SCALE_AND_DENSITY.md`, `STORY_AND_ATMOSPHERE.md`, `COMBAT_AND_PROGRESSION.md`, 2026-11-13) led
to the user's decisions of 2026-11-14 (README, top). They are applied to WORLD_DESIGN, MAPS, QUESTS, MONSTERS_AND_ITEMS,
PRODUCTION and README's summary; nothing in `briefs/` or the built maps was changed.

- **Progression:** the combat review's per-map table is MAPS §0 (party levels, monster bands, groups, Tres, counts,
  kill XP). Acts: I 1–7, II 7–20, III 18–30, IV 30–42, V 42–55, VI 55–65 (optional to 70); about 62–65 at the end as
  played. Families split to at most 2.5× and 25 levels (66 families); MM6–MM8 treasure table; training caps; boss rows;
  bolster rows.
- **Vertigo Meadows (X1)** keeps four dungeon sites: XD-01; XD-02 with XD-03 below it (entered by XD-02's cart; its
  shaft head on X1 is a one-way exit); XD-04; XD-05. XD-06 Temple of Yak moved to X2 (fairy woods); FD-05 Dungeon of
  Death became the lower half of FD-04 Dragon Tower on X7 (FD-05 retired). X2 and X3 swapped places in the grid, so
  X1's west road leads to the hub X2 (X3 now borders X2, X4 and X5).
- **Dungeons:** 58 (24 S, 30 M, 4 L) + 2 town BLVs + the arena; 69 BLV files with the sky maps, planes and P5. S is
  6–15 sectors and 15–30 monsters; XD-03 and XD-05 are M as built; XD-01 stays the upper-bound S. L: Darzog's Tower,
  Castle Xeen, the Great Pyramid, Castle Alamar; Blackfang a large M, the Dragon Cave an M.
- **Story:** short original lines may be quoted (WORLD_DESIGN §1 Voice; MAPS lists them per map); Artemus suspects
  Darzog and no Roland spoiler before M21; Crodo's dreams in M1 and two Crodo bottles; Burlock's M35 line for the
  interleaved order; answer-givers for the source's riddles; Newcastle's deed 12,000.
- **Assumed, the user may change:** Darkside's amber days and failing sun (WORLD_DESIGN §4, PRODUCTION E8); Xeen as a
  separate world with a native party (WORLD_DESIGN §1.1); the goblin slate kept as ours (§1.2).
- **Per map:** POI budgets, day-one services on X3/X4/X5, adjacency fixes (D1–D6 road).
- **New engine items:** E11 damage from one weapon (Lord Xeen), E12 time-of-day gates, E13 gem payment (was O3),
  E14 boss rows. The jail for theft is open (recommended: drop).
- **The built maps** change later in their own passes: [CHANGES_FOR_BUILT_MAPS.md](CHANGES_FOR_BUILT_MAPS.md).

**Not reconciled** (left as stated, for the user or the lead):
- The adopted table puts 70–80 monsters in the four L set pieces; shipped L dungeons hold 120–180 (scale review §2).
  Raising them adds about 0.55M party kill XP (two to three late levels) unless something else is cut.
- The adopted table's outdoor counts (hubs 135, wilderness 110–135, trap maps 90–110) are below the scale review's
  role bands (hubs 160–220, wilderness 140–185, trap 130–170). The table wins for now (MONSTERS_AND_ITEMS §3).
- The scale review's outdoor packs of 1–3 per marker against the table's groups of 2–4 (X1's orcs 3–5): the table's
  groups are kept; the encounter-area layout rule is taken.
- The scale review's target of half S dungeons needs XD-10, DD-02 and DD-06 to become S; the adopted table keeps them
  M (the world is 41 % S).
- X1 has four dungeon sites but five BLVs (the Deep Mine below the Red Dwarf Mines). If "3–4 dungeons" counts BLVs,
  XD-03 would need its own map elsewhere, which would break the built XD-02/XD-03/X1 links.
- XD-13, XD-25 and XD-26 were missing from the combat table; their rows in MAPS §0 are computed with its rules.
- The review page (`review.html`) still shows the first grid (X2 and X3 the other way round) and the old numbers.

## 1. Xeen world design (`devdocs/xeen/`)

Start with [README.md](README.md): the index, the summary, the decisions of 2026-11-13 and 2026-11-14, and the open
questions.

| File | Contents |
| --- | --- |
| `WORLD_DESIGN.md` | Concept; decisions D1–D9; two faces (Cloudside, Darkside); 13 surface maps, 3 sky maps, 4 planes and a finale; travel; Fly; visuals; towns; teachers |
| `QUESTS.md` | Main quest M1–M42 in six acts; 54 side quests; composite promotions (5 tier-1, a Light/Dark tier 2, 5 racial); Newcastle and Kalindra; systems |
| `MAPS.md` | The adopted per-map table (§0); one sheet per outdoor map; dungeon table (XD-, DD-, FD-); original lines per map; layout sketches. The XD-01–05 rows follow the briefs |
| `CHANGES_FOR_BUILT_MAPS.md` | What X1 and XD-01 to XD-05 must change after 2026-11-14 |
| `reviews/` | The three reviews of 2026-11-13 |
| `MONSTERS_AND_ITEMS.md` | Conversion rules; 66 families (about 52 reuse installed models); density by map role; treasure on the MM6–MM8 table; items; artifacts; training caps |
| `PRODUCTION.md` | World package and id ranges; engine work E1–E14 (E10: a world music table, since names are rejected; E11–E14 from the reviews); content routes; mock-ups MU-1–7; phases; the lean variant |
| `PLAN_YAML_NEEDS.md` | What Xeen asked of Map Studio's plan format. Sent, and folded into the studio's schema |
| `review.html` | The review page, published privately at https://claude.ai/artifact/FA4PpnWpTm6b8tdr8cEV3Q |
| `research/` | The evidence. MM4 and MM5 content inventories; decoded Xeen monster, item, class and spell tables; MM6–MM9 calibration; map craft (`research/map_craft/` holds two census scripts and their JSON) |
| `briefs/xd01`–`xd05/` | Act I dungeon briefs at L1, L2 and L3 (§2) |

**Still open with the user:** README's open questions (the 2026-11-14 decisions settled text, scope of X1, progression
and dungeon sizes). These matter most:
- Fly or Fleet Foot.
- Interleaving the two faces.
- Full or lean scope.
- Light/Dark promotion per character or per party.
- Gems as a currency. The XD briefs pay out gems.
- Portraits and music.

Everything Xeen past Act I waits on these, and the Act I briefs are provisional until then.

Design decisions taken while writing the briefs, already in the docs:
- XD-03 is size M (since 2026-11-14; it was S).
- The Alacorn returns to Valia; it is not a party relic.
- The Witch Tower vat gives +2 to one random stat, which keeps Act I's permanent stat budget at about +10 per
  character.
- The X1 sheet gained a culvert, an escape-shaft head, Tam, and an orc-outpost state.
- XD-04 is a "crooked tower" (floors a quarter turn round the shaft) and XD-02's carts are scripted rides, because
  rooms cannot stack yet.

## 2. Map Studio designer work

Map Studio replaces `editor/`. It belongs to another session: docs in `devdocs/map_studio/` (start with `HANDOFF.md`,
`PLAN.md`, `CALIBRATION.md`, `REBUILD_PROCEDURE.md`), code in `openyamm-studio/`.

**Rules:**
- **Never edit `openyamm-studio/`.**
- The owner was openyamm-e2 and is now **openyamm-c5**; check `ListAgents` for the current name. Its requests arrive
  as cross-session messages. Answer with `SendMessage` to its name.
- When a session takes over from openyamm-fe, tell c5 the new name.

### State of every brief

Each level is a complete project folder (`briefs/<map>/L1`, `L2`, `L3`, `L4`). Prose briefs (L0 plus a prose L1) are
`devdocs/map_studio/briefs/<map>.md`. Each ends with correction notes from later, measured passes. The YAML always
follows the measurements.

| Brief | Levels | State |
| --- | --- | --- |
| `briefs/mm7_7d06` Temple of the Moon (indoor) | L1–L3, **L4 playable** (objects, wiring, `ids.lock.yml`) | Main focus: about ten review takes so far. **Compare 87.7 %** (shape 85.8, textures 93.9). 45 rooms. Playtest 190/190. No thickness or non-planar warnings. Details below |
| `briefs/mm6_6d16` Warlord's Fortress (indoor) | L1–L3 | Redrawn after review (doorways and connectors measured, tunnel bends smoothed). Walks end to end, all rooms reachable. **L4 not started.** Never run through `oymap compare`; do that first when work resumes |
| `briefs/mm8_out02` Ravenshore (outdoor) | L1–L3 (`sketch.yml`) | Passes `validate`, footprints in `footprint_cells`. Outdoor builds wait for the studio's S4 |
| `briefs/mm7_7out02` Harmondale (outdoor) | L1–L3 (`sketch.yml`) | Passes `validate`, same state as Ravenshore |
| `devdocs/xeen/briefs/xd01`–`xd05` (new Xeen dungeons) | L1–L3 | All valid. Headless-walked in the game: XD-01, 03, 04, 05; XD-02 by audit and probes. Map cards name music tracks (`cave` …), which the game refuses: use numbers when installing (E10) |

**`devdocs/map_studio/briefs/SCHEMA_GAPS.md`** is the running record of what the format could not say: rounds 1–6,
each with closed and open status. Add new gaps under a dated heading and mark closed ones there.

### The Temple of the Moon in detail

The rebuild is drawn in the original's x/y frame. Plan z is the original's z − 320. Built so far:

- **Caves:**
  - Non-convex outlines with rough walls.
  - 4 rock islands as pillars.
  - Full-width joins where caves meet; cave mouths 16 apart.
  - Ceilings set per room from the original, sloping where the original's do.
  - The east climb rebuilt as the original's spiral; the descent bend opens east.
- **Nave, built "inside out":**
  - The room's floor is the sunken floor (−544), and the gallery is one raised level at −416 against the walls.
  - The 6-step west flight up to the apse has raking sides (64 high, 32 thick, 7tfb11).
  - The temple stair comes down 9 steps through the east arch.
  - The dome is a narrowing ceiling level, with a collar ring, 4 raking half-ribs and a dark centre block.
- **Openings:**
  - Five pointed arches (`shape: arch`, measured `shoulders`): the stair arch, both passage mouths and both passage
    ends.
  - Openings keep `sill` 0; the builder measures from the higher floor.
  - Temple portals are 32 apart.
- **Surfaces:**
  - The original's textures by area: bands for dado, frieze and plaster; trim3_32a risers.
  - Stair run: twb1 below cwb1. Flight: twb2 walls; its ceiling slopes down to the arch.
- **Altar:** three parts on one centre (plinth, a twb1a bowl on a 64 × 128 foot, a lip), as c5 measured.
- **Library and study:** bookcases are chests with size, books on the sides and carved end panels.
- **Lighting:** `ambient: 24`; the 21 violet `torch05` torches; no other lights.
- **L4 objects:**
  - 3 doors: two double doors and the lifting wall.
  - 19 chests, 17 spawns, 23 events.
  - The scavenger-hunt items carry the original's qbits.
  - Placeholders for what cannot be built yet: the four guards and the captain's longbow, the moon floor tile, floor
    loot, the fire-bolt trap.
- **Cameras:** c5's review cameras for west-descent (−1504, 96) and north-cavern (−832, 2368) were given yaws of
  0.7854 and 1.0472. c5 sets them in its `shots.yml`.

Still not drawable, waiting on c5's queue:
- **Shape:**
  - curved dome sides and ribs;
  - twisting cave floors and sloping ceilings across a turn;
  - floor relief;
  - the pointed-vault cross-section of the stair;
  - niche hoods.
- **Surfaces:**
  - a sequence of textures along one wall (carved panels, niches);
  - threshold surfaces;
  - one-sided walls.
- **Objects:**
  - chest `top_surface` and `random_items: 0` (bookcases also roll a random item now);
  - placed actors, floor items, timed events and spell casts.

### How to work

- **Tool:** `openyamm-studio/build/oymap`. It is shared by several rebuild agents, so **do not run
  `openyamm-studio/build.sh` casually**. Rebuild only when told a feature has landed and the binary lacks it.
  - Schemas: `oymap schema plan|project|common|rooms|objects|wiring|sketch|pins`.
  - Worked examples: `openyamm-studio/examples/gatehouse_cellars/` and `shapes_gallery/`. The game walks both.
    Pictures are on `output/studio_review/index.html`.
- **Checks for every folder you touch:**
  - `oymap validate <folder> --assets assets_dev`
  - `oymap build <folder> --assets assets_dev --dry-run` (indoor). Read its warnings.
  - `oymap fmt <folder>`, last, then `fmt --check`.
- **Steering by score:**
  - `oymap compare <orig>.blv --world <w> --with <brief L4 or L3> --assets assets_dev --out <scratch dir>` takes about
    2 s. It writes `report.json` (totals, per-sector scores, the 40 worst points with a sentence each),
    `geometry.png` and `textures.png`.
  - Keep changes that raise the score; revert those that drop it unless the user asked for them visually.
  - Stop when gains fall below 0.3 twice.
  - Some worst points are sampling artefacts: points on a ledge, or ceiling seams. Check against the original before
    "fixing" them.
  - Older per-metric bands: `python3 openyamm-studio/calibration/compare.py <L3> openyamm-studio/calibration/originals/<map>.metrics.json`.
- **Review page:** `python3 openyamm-studio/calibration/review_page.py` regenerates
  `output/studio_review/index.html`. c5 retakes the in-game pairs.
- **Playtests:**
  - `oymap build` and `oymap install --mount <scratch> --assets assets_dev` into a COPY of a previous scratch setup,
    then headless with `--extra-mount`.
  - The Temple L4 already has `map_stats.id: 9706` and music 28.
  - Earlier setups (`play7c`, `play_ceil2`) are in this session's scratchpad. A reboot wipes them, so rebuild one from
    the L4 objects if needed.
- **Designer rules:**
  - Never name the target map's file or its BModels in a brief.
  - Outlines are simplified shapes from measurements, never traced vertex lists: about a dozen points, caves up to
    about 20–30 with a reason.
  - Measure with `util/map_export.py` (`parse_blv_file`, `parse_odm_file`).
  - Keep L3 and L4 geometry identical; L4 adds themes and objects.
  - `ids.lock.yml` lives only in L4 (a built project; room numbers shift down when rooms are removed, by design).
    Never leave one in L1–L3.
  - When a measurement proves a plan fact wrong, fix it in every level and add a correction note to the prose brief.
- **Agents:** most work ran through background agents with self-contained briefs, one folder or one concern each.
  Never let two agents edit the same file. If a request touches a file an agent is editing, send that agent the
  addition instead of starting a second one.

### Pending, in likely order

1. **Temple review rounds.** When c5 relays the user's marks or announces a new feature, apply it in L3 and L4, check
   with `oymap compare`, run the playtest, and report the score to c5. Redraw each queued item as it lands.
2. **Warlord's Fortress:**
   - A first `oymap compare` run.
   - Score-steered fixes.
   - Its L4 (objects and wiring, modelled on the Temple L4), when c5 asks.
3. **Stacked rooms** (R5-K1) are c5's next big shape. When they land, redraw:
   - **XD-04:** a real stacked tower, with the Alacorn bridge over the shaft.
   - **XD-02:** a full spiral and a walkable trestle.
   - **XD-03:** the gallery over the hall, and slag under the bridges.
   - **XD-01:** the cellar under the hall.

   Then update `devdocs/xeen/MAPS.md`.
4. **Outdoor follow-ups:** R6-1–8 in SCHEMA_GAPS.md, when c5 asks or when S4 (outdoor builds) arrives.
5. **Xeen beyond Act I**, after the user's answers:
   - The built maps' passes in [CHANGES_FOR_BUILT_MAPS.md](CHANGES_FOR_BUILT_MAPS.md) (X1 first: the west road
     to X2, the Temple of Yak door removed, density and POIs).
   - The Act II maps (X2 with XD-06, XD-21, XD-27; then X4, X3).

### Open with the user

- **Possible MM6 data bug, unverified.** The Warlord's Fortress quest chest (chest 11 in
  `assets_dev/worlds/mm6/maps/6d16.scene.yml`) stores item 2128 "Discharge Papers". Its event says it gives the Eagle
  Statuette (2073 in `items.txt`). It needs one in-game check. Not fixed: it is outside the brief work.
- The Xeen open questions in README.md, and the "Not reconciled" list in §0.
