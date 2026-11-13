# Schema v0 gaps found by the calibration briefs

Written 2026-11-12 by openyamm-fe, the designer. These are the places where the four L1 briefs could not say what
their prose L1 says (or what a builder needs). In each case the brief was not bent to fit: the content went into
`notes:`, and the gap is listed here. Each gap names the briefs where it came up:

- **R**: Ravenshore, `mm8_out02/L1`
- **H**: Harmondale, `mm7_7out02/L1`
- **T**: Temple of the Moon, `mm7_7d06/L1`
- **W**: Warlord's Fortress, `mm6_6d16/L1`

All four pass `oymap validate` and `oymap fmt --check`.

**Folder layout.** Each brief level is a complete project folder: `briefs/<map>/L1/`, and later `L2/` and `L3/`. Each
level then validates on its own, and a builder can be handed exactly one level, as the calibration rounds require.

## 1. Validator issues (tool, not schema)

| # | Issue | From |
| --- | --- | --- |
| V1 | **Outdoor projects get no cross-reference checks on `plan.yml`.** A scratch copy that pointed at a missing space, a missing neighbour and a missing named qbit still printed "no issues". | H |
| V2 | **Indoor checks miss several references.** Only `links`, `critical_path`, `entrances`, `part_of` and `mirror_of` are checked. Unchecked: space ids in `set_pieces.spaces/path`, `height_bands.spaces`, `goals.space`, `landmarks.space/seen_from`, `points_of_interest.space` and `keys`; `entrances[].neighbour` against `project.yml`; named `item`/`drops`/`gives.item`/key names against `project.items`; `treasure.shared_with` container ids. | T, R, W |

## 2. Map card (`project.yml`)

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| P1 | **`map_stats` without `reference`**: per-slot `{monster, difficulty or grade or tier, per_marker: [lo, hi], weight}` and defaults for every column | Slot tiers, group sizes and rest-encounter weights; refill, lock, trap | v0 fills these from `reference`, and a calibration card may not name its own original. With no neutral row, the build has no source for them | R, H, T, W |
| P2 | A documented **lock difficulty** field | "Lock 5" | Only `disarm_difficulty` exists, and its meaning is not documented | W, R |
| P3 | **`neighbours[].schedule`** (weekdays or `per_week`) and **`service`** (operator id) | Which ship or caravan runs which route, and how often | Only `days` exists | R, H |
| P4 | **`neighbours[].arrival_side`** (n/s/e/w) or **`arrival_hint`**, until shipped maps have anchors | "Arrive on the Tularean Forest's south side"; "in front of the fortress gate on Silver Cove"; "beside the dungeon entrance on Emerald Island" | `arrival` takes only an anchor id or coordinates, and shipped maps have no anchors | H, W, T |
| P5 | **`neighbours[].listed_only`** (or `kind: none`) | A south edge that the travel table lists but that is not a real route | No kind fits | R |
| P6 | **`neighbours[].approach`** plus **`screened: bool`** | The character of each approach, e.g. a rock cut that screens the destination | Only `notes` | R |
| P7 | **World anchors**: `rules.home_town`, `respawn`, `town_portal_anchor` (pointing at an entrance or POI) | Respawn town, home point, the fountain that sets the Town Portal point | No such keys | R, H |
| P8 | **Map extent**: terrain cells (full 128 or partial); the plan footprint of an indoor map and the direction it climbs | "Full 128-cell map"; "about 19 × 14 cells, climbing from south to north" | No field; written as `totals` strings | H, W |

## 3. Spaces

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| S1 | **`share`** (fraction of the map) for outdoor zones | Market 1/20, woods 1/6 …; all ten Harmondale zones | `size` (S–XL) is defined by indoor floor area, so every outdoor zone would be XL | R, H |
| S2 | **Indoor size classes** that match the design legend: add **XS** (closet), or allow `area` in M units² | Closet < 0.15, small 0.15–0.5, medium 0.5–1.2, large 1.2–2, great > 2 | S/M/L/XL thresholds at 0.5/1.5/3 merge closet and small, and split "large" | W |
| S3 | **Point nodes** (`kind: junction`, with `signpost: bool`) | Road junctions, bridge heads and edge exits as graph nodes | No point-like kind; written as `zone` with `part_of` | R, H |
| S4 | **Groups of spaces**: `regions` or `wings: [{id, spaces, where, footprint_cells}]` | Six wings; "the temple about 12 × 8 cells in the north-west, the caves south and east of it" | `where` exists only per space | W, T |
| S5 | **An explicit "empty on purpose"** (`empty: true`, `safe: bool or condition`, `keep_clear: [spawns, buildings, decorations]`) | 16 empty spaces; "safe until the fires are lit"; deliberate quiet approaches and open spaces | A missing `population` cannot be told apart from "not specified"; `density: open` and `rules.town_buffer` (one radius) are too coarse | T, H, R |
| S6 | **Features inside a space**: `features: [{kind: dais, alcove, colonnade, wall_slot or platform; rise; where}]` | Altar dais at +144, a raised alcove with five chests, colonnade pillars, a bed at +464, a throne dais at +768 | Only `shape` text; `islands` means walk-round loops only; `floor: [lo, hi]` mixes slopes with platforms | T, W |
| S7 | **`clear_height`** as a number, a range or a class | "Caves about 400–500, taller in the pockets" | Takes one number | T |
| S8 | **`floor`** as `{level, range}` | "−320 ± 130" | Takes a number or a range, so the typical level is lost | T |
| S9 | **Void spaces: `top` or `height_above`** | "Dome top about 1,350 above the nave floor" | `floor` and `clear_height` do not apply to a void | T |
| S10 | **`mirror_axis`** for `mirror_of` | Which way the north wing flips into the south | Not expressible | T |
| S11 | **Density details**: `coverage`, `building_gap` | "Buildings cover about 30 % of the market; nearest-building gaps about 600" | The four-step `density` enum is too coarse | R |
| S12 | **`backdrop: bool`** and **`rules.playable_square`** | Uplands as backdrop beyond the travel prompts; playable square about the middle 70 % | `rules.rim` is an untyped object | R |

## 4. Links, loops and paths

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| L1 | **`loops: [{id, spaces, closed_until: condition}]`** | The big ring that closes only after a switch; the storeroom triangle | No field; written in `totals.loops` and `notes` | W |
| L2 | **`return_path`** | The way out, through a one-sided portcullis | `critical_path` covers only the way in | W |
| L3 | **Random teleport sets**: `teleport_sets: [{sources, landings: [{space, count}], rule}]` or `link.to_any` | False doors and click spots that send the party to one of five landings, never the door's own | `link.to` takes one id, so the flow graph cannot see the one-way route into the cellar | W |
| L4 | **`link.kind: portcullis`**, and secret-wall motion (rise or sink) | The switch portcullis; three secret walls rise and one sinks | Neither exists; written as `door` and `secret_door` plus notes | W |
| L5 | **Links that cross, and links with features**: `crosses: [water ids]`, `features` (bridge, signposts, crates), `length_share` | The spine crossing the river on a bridge; a ravine bridge; the high road at about 40 % of road length | `kind` holds one value, so a road cannot also be a bridge | R, H |
| L6 | **A whole side open**: `width: full` or `kind: overlook/colonnade` | Aisles open onto the nave along their full length, 128 higher | `open` plus `rise` cannot say "the whole side" | T |
| L7 | **Shared entrances**: `entrances[].neighbours: [ids]` or `neighbours[].arrives_at` | One pier for four ship routes; one stable yard for three routes and the Arena's return | `neighbour` takes one id | R, H |
| L8 | **`entrances[]`: an offset from another entrance** (direction and rise) | "The exit is up the ramp, just behind and above the arrival" | Only `how` text | T |
| L9 | **`reached_by`** on entrances and treasure, as on POIs | The cove reached only by water or flight; rim chests reached off-road | Only POIs have it | R |

## 5. Conditions, states and set pieces

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| C1 | **`all: [condition]`**, or `item` taking a list | A door that needs both Storage Keys | `item` takes one value; worked around with `any` | W |
| C2 | **A lock group with a shared consume**: `lock_groups: [{links, consume, when: second_opened}]` | The keys are spent when the second door opens | `consume` belongs to one condition | W |
| C3 | **`condition.otherwise`** (locked, talk or another target) and **`variants: [{condition, behaviour or target}]`** on entrances and POIs | The council door gives a talk before its quest; the castle door is a quest giver, then a dungeon, then a house dialog; the Arbiter's three house variants | An entrance has one neighbour and one condition | R, H |
| C4 | **Money conditions with "at most"**: `gold`/`bank_gold: {below, include_bank}` | Fountain or well that pays only when the party is nearly broke | No such key; `stat` has only `at_least` | R, H |
| C5 | **`stat`: any-stat form and a fixed list of stat names** | "Any stat of 200" | Not expressible; stat names are free strings | R |
| C6 | **`condition.season`** (or documented month ranges) | Fruit trees that give only in spring and summer; seasonal tree swaps | `month` exists, but the seasons' boundaries are undefined | H |
| C7 | **`kills: {monster, all: true}`** | "Kill every dire wolf on the map" | `kills` takes `{group, at_least}` | R |
| C8 | **Population ids and hidden-but-present**: `population[].id`, `hostile` and `hidden_until` conditions | The peaceful town squad that is hidden and then turns hostile; a target for `kills.group` | `condition` reads "present when"; `kills.group` has no population entry to point at | H |
| C9 | **`states[]`: `lifted_by`, `locks: [building or space ids]`, `effects: [text]`** | The lockdown: locks every service and house, wipes the bank balance, lifted by killing the squad | `seals` takes ids, but buildings have no ids | H |
| C10 | **`goals[].gives` as a list**; **`goals[].handed_in_at`** | Two quest bits set by one chest; scavenger items handed in on another map | `gives` takes one condition; `story` is free text | W, T |
| C11 | **Set pieces**: `enabled_by`, `gives`, `population` (summoned waves), `emitters: [{space, end, direction}]`, `effect: {spell, level}`, `targets` | The fire-bolt trap's emitters and spell; taking the fort, which summons four waves; the towers' target sectors; a messenger that appears after the artifact is given | Only `rule` text, `path`, `period` and `disabled_by` exist | T, H |
| C12 | **NPC movement between houses** | Judges and ambassadors moving in and out of the Arbiter's hall | No field | H |

## 6. Population

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| N1 | **Group sizes**: `count`, `per_marker` or `per_pack` (a range) | "Groups of 2–5"; "1–3 per marker" | `groups` counts spawn points, not monsters | T, R, H |
| N2 | **Pack shape**: `packs`, `spacing`, `levels` | About 10 tight wolf packs, about 4,000 apart, levels 9–19; centaur singles 1,000–2,000 apart | `groups` is ambiguous between markers and packs; there is no spacing field | R |
| N3 | **Clearances**: `clear_of: [{space, distance: share of map}]` | Wolves no nearer than about 1/6 of the map to the lanes | One map-wide `town_buffer` only | R |
| N4 | **Fixed actors before a monster is chosen**: a role (swordsman, captain), `level_vs_slots`, mixed lists `actors: [{actor, count}]`, and a placed-or-spawn flag | Guards "several levels above the vermin"; a raider camp of goblins, hobgoblins and a lord, placed rather than spawned | `actor` expects one monster id; `slot` implies spawn points | T, H |
| N5 | **`rank: any`** (drawn from the map's difficulty) | Random-rank spawn groups as opposed to fixed a/b/c | The enum is a/b/c/mixed; "mixed" means something else | W |

## 7. Points of interest, treasure, landmarks

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| I1 | **`uses`**: once, n, per character or party, reset daily, weekly or never | Wells, fountain (at most twice), obelisk, fruit trees | Only behaviour text | R, H |
| I2 | **`gives`** on POIs (qbit, autonote, item, effect) and **`after_use: {shows, hides}`** | Fires that set qbits and then burn; trees that go bare when picked | Only goals have `gives` | H |
| I3 | **`count`** and **`spaces: [ids]`** on a POI | 8 fruit trees in three groups; click spots across four corridors | One `space`, no count; written as separate entries | H, W |
| I4 | **`neighbour`** on a POI | An altar that teleports to another map | Stood in for by an extra entrance | H |
| I5 | **Native rules**: `rule: native:<name>` | Obelisk riddle, buff pedestal and stat challenge use world-wide state | Not expressible; the open `additionalProperties` would accept an invented key silently | R |
| I6 | **One object in several roles** (entrance, landmark, POI) | The crystal in the square | Nothing links the roles | R |
| I7 | **Treasure contents**: `items: [lo, hi]` per container, `items: [list]`, `pool: [items]` with `once`; kinds `cabinet` and `drawers`; a named low or mid tier | "3–4 random low items"; bookcases that each give one scroll from {Torch Light, Wizard Eye}; drawers that give two keys | `count` counts containers; `item` takes one value | T, W |
| I8 | **Declared containers** for `shared_with`: `containers: [{id, kind, tier}]` | Nine footlockers sharing one inventory; three cabinets sharing another | `shared_with` points at an id that nothing declares | W |
| I9 | **Sightlines**: `sightlines: [{from, to: [ids]}]`, `landmarks[].spaces` as a list, `hidden_from` or `screened_by` | "North arrival: the river leads the eye to the bay"; hills hide the town except the castle and spire; upland walls spanning two spaces | Only `seen_from`; vistas were written as `set_pieces` | R, H |
| I10 | **Lights and fires at L1** | About 12 fires: camps, a beacon, braziers | `light` is L2 and reads as indoor | R |

## 8. Heights and landform

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| H1 | **A height datum** (`datum: arrival`, `sea_level` or a named space) | Absolute heights from sea level or low ground (market 0, headland 6,400) | `floor`, `rise` and `height_bands` are relative to "the arrival", and outdoor maps have several arrivals at different heights | R, H |
| H2 | **Height bands**: single-level bands and partial membership | "Arrival (0)"; spaces only partly in a band | Ranges only | T |
| H3 | **Landform shares**: `water_share`, `caps` (kind, share), `rim` (width share, valleys that break it) | A quarter of the map sea; white caps on the highest knolls; a hill rim broken by the exit valleys | `project.rules.rim` is about rim mechanics, not landform | H, R |

## 9. Level labels and diagrams

| # | Wanted | Brief content it carries | Why v0 does not fit | From |
| --- | --- | --- | --- | --- |
| D1 | **`buildings` at L1** (relabel it, or add services-by-count at L1); building ids and doors per building | Services by count and grouping; three joined service blocks with 3–4 services each; "8 home doors in 7 houses" | Labelled L2, and one entry has one service, which overstates the building count | R, H |
| D2 | **`diagram: {file or text}`** for L1 | The not-to-scale bubble diagram of the prose brief | `sketch` is the L3 to-scale sketch | R |

## 10. Data looked up in the originals

The agents writing the YAML went back to the original data only where the prose was ambiguous. These values are now
in the briefs:

- item, qbit and award ids;
- slot monster names;
- refill 672 days;
- Harmondale's third stable route is Tatalia;
- Warlord's Fortress: which rank each room's groups are, and two of the five landing spots in one room.

The prose briefs flag the open points they settled, so the evaluator knows what was not in the original prose.

---

# Round 2 (2026-11-12, after the schema extension)

The four L1 briefs were moved onto the new fields, and L2 was written for all four maps
(`briefs/<map>/L2/`). All eight folders pass `oymap validate` and `oymap fmt --check`. Neither level of any map names
its target map file or the target's own BModels.

## Status of the round 1 entries

| Status | Ids |
| --- | --- |
| **Closed** (used by at least one brief and sufficient) | P1–P8, S1–S12, L1–L9, C1–C3, C5–C10, C12, N2–N5, I1, I3–I6, I8–I10, H1–H3, D2 |
| **Partly closed** (the remainder is listed below) | V1 and V2 (some references are still unchecked: R2-V1), C4 (two separate money limits: R2-G2), C11 (weighted effects and directional targets: R2-G15), N1 (`markers_per_pack` was not added: R2-G4), I2 (a `gives` vocabulary beyond conditions: R2-G1), I7 (fixed contents: R2-G5), D1 (several services per building: R2-G6) |

## Validator and tool issues

| # | Issue | From |
| --- | --- | --- |
| R2-V1 | Still unchecked: treasure `item`/`pool` names and `population[].drops` against `project.items`; `goals[].handed_in_at` against neighbours; `diagram.file` existing; `rules.respawn`; `landform.rim.broken_by`. H reports `kills.group` unchecked while R reports it checked, so verify | T, W, H, R |
| R2-V2 | `oymap fmt` flattens a multi-line `diagram.text` into a one-line string full of `\n` escapes; multi-line strings should be written as `\|` blocks (T switched to `diagram.file`) | T |
| R2-V3 | `core/Install.cpp` writes the Lock column only from `disarm_difficulty`. `lock_difficulty` (now the preferred key), `map_stats.slots` and `music` are not installed, so a card using them loses those values on install | W |
| R2-V4 | `map_stats` accepts undeclared keys silently (`alert_days`, `steal_perm`, which Harmondale needs). Declare them or reject unknown keys | H |
| R2-V5 | `rules.respawn` should accept a space id (a defeated party wakes on the harbour pier), not only an entrance, POI or map | R |

## Schema gaps

| # | Wanted | Brief content | From |
| --- | --- | --- | --- |
| R2-G1 | **An effect vocabulary** for `points_of_interest[].gives`, `variants[].gives`/`uses` and `states[].effects`: `{gold, skill_points, autonote, buff: {stat, amount, duration: temporary\|permanent}, inflicts: [conditions], pick: random, item, random_item: {kind, tier}, set: {bank_gold: 0}}` | Wells (+10 Might until reset, +2 Accuracy permanent, +200 gold), a fountain that inflicts poison or paralysis, a fountain that sets the Town Portal anchor every time but pays gold only twice, reagent drops, "bank balance set to zero" | R, H |
| R2-G2 | **Condition additions**: `stat.below`, `stat.base: bool` (or a separate `bonus` reading); `bank_gold` as its own limit, besides `gold`; `since: {qbit, days_at_least}`; `opened: [link ids]` (or `lock_group: <id> opened`) for `loops[].closed_until` | The Might well works only with no Might bonus active; the buoy checks base Luck; the market well needs under 200 on hand **and** under 100 in the bank; the pirate landing two months after the leader dies; the storeroom loop closes once both double-locked doors are open | R, H, W |
| R2-G3 | **`goals[].done_when: condition`** and **staged set pieces** `stages: [{enabled_by, gives, population}]` | "Kill every dire wolf" (now a separate check set piece); the wolf check's two stages (straggler and an interim bit, then the quest bit) | R |
| R2-G4 | **Population detail**: `markers_per_pack: [lo, hi]`; `levels` on each `actors[]` entry; `waves` and `per_wave`; `behaviour: wander \| camp \| stand \| patrol`; `where` inside a space; `npc` or `name` on a fixed actor | Wolf packs of 3–5 markers; a town squad from level-4 goblins to level-24 adventurers; the fort's 4 waves of 10; peasants walking the streets; rats "in the sunken centre"; a guard captain who is the island ambushers' leader | R, H, T |
| R2-G5 | **Fixed treasure contents** `contents: [{item, count} \| {random_tier, count}]` on treasure and containers, and **`trapped: bool`** per container | Drawers with two keys; a cabinet with plate armour and a shield; wagons with 20 mushrooms and 20 phirna roots; a prize chest with an artifact and 18 gold piles; a vault with three artifacts, gems and ore; five trapped containers including decoy shared inventories | W, H, R |
| R2-G6 | **Building detail**: `services: [..]` (optionally doors per service); `kit`, `culture`, `form`, `footprint_cells: [w, d]`, `height`, `storeys`, `parts`, `facing`, `where`; `tier` as an enum; `forms: [{form, count}]` on entries with a count; documented group-id meaning for entries with a count | Joined blocks of 3–4 services; "Erathia (Steadwick) town kit, medium tier, two joined blocks"; the market's dark-elf, human and ogre houses; 44 houses in 13 forms | R, H |
| R2-G7 | **`structures: [{id, kind, space, footprint_cells, height, parts}]`** for one-off structures that are not services | Crystal cluster, tomb, seer platform, chapel, den mouth, sea-cave arch, vault door, bridges, piers, wells, the fountain | R |
| R2-G8 | **Structured palettes** `palette: [{decoration, count \| per_area, placement, cluster: [lo, hi], where, avoid}]`, checked against the decoration library | "About 50 trees of two kinds in clumps of 2–5, kept off the fort's fields of fire"; barrels in pairs at doors; bones round the den; about 8 barrels and 12 sacks in a storeroom | H, R, W |
| R2-G9 | **Ground**: `ground: [{material, role: base\|variant\|yards\|roads\|cliffs\|shore, share}]` on spaces and on `landform`, and `grass: {family, density}` | Per-zone ground shares (south-east lakes: soil 36 %, white caps 27 %, sand 16 %); meadow grass at density 0.45 | H, R |
| R2-G10 | **Themes and kits as data**: plan-level `themes: [{id, walls, floor, ceiling, trim, furniture, doors, source}]` referred to by `space.theme` and `region.theme`, and `kits: [{kit, cultures, tiers, share}]`. **Library gap:** there are no named MM6–MM8 indoor themes or kits to name from; the briefs named `textures_x4` families and engine decoration names | Cave set and temple set; the six fortress wing finishes; the market's three kits by culture and tier | T, W, R |
| R2-G11 | **Structured lights**: `lights: [{kind, colour, count, mount, radius, condition}]` per space, a defined unit for light density, defaults per region or room class, and a minimum ambient light level | 21 violet torches and 4 red point lights; 75 lights at 4.5 / 2.5 / 1.5 per M units² by room class; watch fires dark until lit; ambient 24 of 255 | T, W, H |
| R2-G12 | **Mechanism detail**: `mechanisms[].refs` (link, space, POI, building or set-piece ids), `condition`, `once`, `travel`, `speed`, `closes`, `linked_parts`, `click_faces`; and a door specification on links `door: {look, height, travel, speed}` | Double sliding doors at 160 per leaf with a seam strip, and buttresses that also open them; plank against iron-banded doors; a secret wall that uses its room's finish; about 20–23 mechanism kinds per outdoor map tied to places | T, W, H, R |
| R2-G13 | **Structured atmosphere**: sky `{preset \| theme \| ladder}`, weather `{rain, snow, fog}`, music, sound environment, ambient emitters `[{sound, where, chance, period}]`, and an explicit "none" | A cave environment with track 28; music 42 with no emitters; the world sky ladder with no theme; the horse neigh at the stable, about one time in three every 7.5 game minutes | T, W, H, R |
| R2-G14 | **States as references**: `states[].shows/hides` as validated ids, and `changes: [{building, look or parts}, {decoration_family: from → to}]` | The smuggler's ship and the crystal shown and hidden; castle parts changing at stages 2 and 3; seasonal tree swaps (needs one combined autumn-or-winter state today) | R, H |
| R2-G15 | **Set-piece effects and targets**: `effect` as a weighted list `[{spell, level, rank, weight}]`, `targets: [{space, direction, distance}]`, `emitters[].building`, `emitters[].marked_by` | Fort turrets: Fireball 3/5, Sparks 1/5, Death Blossom 1/5 into four sectors 1,500–4,500 out; a torch marks each fire-bolt emitter | H, T |
| R2-G16 | **An explicit "none"** for keys, levers, loops and lifts (as `empty` does for population) | "No keys, levers, locked doors, loops, lifts, ladders, drops or pits" | T |
| R2-G17 | **`fires` as kinds** `[{kind, count}]`; **`backdrop: partial`** or `walked: [ids]` | Camp, cook, beacon, torch ring and basin fires; uplands that are backdrop except their inner rim, a pass and the chapel spur | R |
| R2-G18 | **Overlap and position**: `over: [space ids]` for stacked spaces; `where` on POIs; `facing` on teleport landings | Only the back stair and the gallery pass over lower rooms; the axe flambeau at the north end of the hall | W |
| R2-G19 | **`npc_moves` from/to as references** (houses, neighbours) | Ambassadors to the castle throne room; judges to taverns on other maps | H |
| R2-G20 | **A fixed `totals` vocabulary** with numeric values | The metrics need comparable keys; the briefs used strings such as guard levels | T, W |

## Prose briefs against the data

Writing L2 from the original data corrected a few prose statements. The YAML follows the data; the prose briefs
carry a corrections note:

- **Temple of the Moon:** 10 library bookcases, not 11 (15 in all), as 5 Torch Light and 5 Wizard Eye, not random. The
  dormitory alcove is not raised.
- **Harmondale:** the joke fountain inflicts poison or paralysis and does not cure. One of the seven town houses stands
  north of the street. There are 25 peasants in town plus 7 in the hamlet. The third stable route is Tatalia
  (Mon/Wed/Fri).
- **Ravenshore:** MM8 has no signposts (the four wayfinding items are buoys). The "braziers" are barrels. There are 14
  fires. Only the square door of the council hall is gated. There are 78 pirates.

## Calibration policy question

At L2 the briefs name the shared texture families and engine decorations that the original itself uses, because no
higher-level theme or kit library exists (R2-G10). That is within the rules (no per-face textures). It does make the
evaluator's palette-overlap metric close to automatic. Should L2 name only styles and kits, or are library names
fine?

---

# Proposal: an outdoor L3 sketch format (2026-11-12)

Requested by c5: no outdoor sketch format exists yet, so this proposes one rather than inventing files. The Xeen
design wants the same thing for its to-scale map plans (`devdocs/xeen/PRODUCTION.md` MU-3; draft in
`devdocs/xeen/review.html`, plate 4). Nothing has been written under these names yet.

## What a designer draws at L3 outdoors

The architect's plan of a region: the land's shape, where the water is, the road lines, district and plot outlines,
where every named thing stands, where the fights and the quiet places are, and the cameras for key views. It is coarse
by design. No heightmap pixels, tile choices, decoration instances or building geometry appear in it.

## File

`sketch.yml` beside `plan.yml`. `plan.sketch: {file: sketch.yml, grid: 512}` points at it. Coordinates are **terrain
cells** of the plan grid (512 units) on the 128 × 128 map: `[x, y]` with x east and y south, origin at the north-west
corner. Integers by default; half cells only where a field says so (road centrelines, plot edges). Every id refers to
`plan.yml`.

| Layer | Content | Shape |
| --- | --- | --- |
| `frame` | Playable square (the travel-prompt bounds); each map edge's exit span and the plan neighbour it leads to; the rim or backdrop strip | rect; `edges: [{side, span: [from, to], neighbour}]` |
| `heights` | Key heights as points (peaks, passes, shore lines, plazas, the castle shoulder), band polygons tied to `height_bands` ids, **cliff lines** with a drop, and an optional coarse grid | `points: [{at, h}]`; `bands: [{band, polygon}]`; `cliffs: [{line, drop}]`; `grid: {step: 4, rows: [[h...]]}` (32 × 32, units of 64) |
| `water` | Sea and lakes as polygons with a water level; rivers as centrelines with width; fords and shores (beach, cliff, marsh) | `bodies: [{id, polygon, level, kind}]`; `rivers: [{id, line, width_cells}]`; `shores: [{line, kind}]` |
| `roads` | Centreline per plan link, with width class and surface; bridges where a road crosses water; junction points named by plan junction ids | `[{link, line, width: lane\|road\|high_road, surface}]` |
| `districts` | Footprint polygon per plan space (zone, district, open space), and inside towns the **plots**: a rectangle per building id with its facing and the road its door opens onto | `[{space, polygon}]`; `plots: [{building, rect: [x, y, w, d], facing, door_to: link}]` |
| `points` | Position of every plan entrance, point of interest, landmark, structure and arrival | `[{id, at, facing?}]` |
| `areas` | Encounter areas (population ids), keep-clear and safe areas, deliberate open spaces | `[{id, polygon \| circle: {at, r}}]` |
| `views` | Camera positions for sightlines and the review's fixed cameras | `[{id, at, height, look: [x, y] \| yaw, purpose}]` |
| `ground` | Optional coarse material zones (polygon → material id from the terrain library) | `[{material, polygon}]` |

## Checks the core could run (tier 0 and 1)

- Every id exists in `plan.yml`, and every plan entity with a location has a point or a polygon.
- Polygons are simple and inside the map.
- Plots do not overlap; they lie inside their district; the gaps between them fall within the plan's `building_gap`.
- Roads join at their junctions and reach their edge spans.
- Heights fall within their bands.
- Water levels lie below their shores.
- Areas do not overlap keep-clear areas.
- Distances such as arrival to first fight and POI spacing are reported against the bands of
  `devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` §6.

## Lowering (what a build does with it)

| Layer | Becomes |
| --- | --- |
| `heights` | A heightmap: points, bands and the grid interpolated, cliffs kept as hard breaks |
| `water` | Water level and liquid cells |
| `roads` | Road tiles and banks |
| `districts.plots` | Building placements from the plan's kits |
| `points` | Entities and anchors |
| `areas` | Spawn markers at the plan's `per_marker` and `packs` |
| `ground` | Terrain weight seeds |

Everything else (decoration scatter, tile edges, building choice inside a kit) remains the builder's work, as at the
lower levels.

## Review render

`oymap render-sketch` would draw the sketch as SVG: grid, water, roads, footprints, plots, points with labels,
encounter rings, height bands and views. This is the MU-3 mock-up of the Xeen plan (`devdocs/xeen/review.html`, plate 4,
hand-drawn there) and the evaluator's side-by-side input for outdoor structure.

## Open choices for the schema owner

1. Should the coarse height grid be allowed at all? It is close to "heightmap pixels", though at 4 cells per sample
   (2,048 units) it is still a sketch.
2. Should plots carry the building's footprint in cells? That duplicates R2-G6 `footprint_cells`; one place should own
   it.
3. Should the sketch be one file, or `sketch.yml` plus an optional `sketch.png` underlay for review only?

---

# Round 3 (2026-11-12): L3 sketches for the two dungeons

`mm7_7d06/L3/` and `mm6_6d16/L3/` each hold project.yml, plan.yml (L2 plus `level: L3` and
`sketch: {file: rooms.yml, grid: 512}`) and `rooms.yml`. A temporary start-only `objects.yml` was removed once R3-V1 was fixed.
Both pass `oymap validate`, `fmt --check` and `build --dry-run`:
- Temple: 30 rooms, 29 openings, 23 × 24 cells, floors from −896 to +384.
- Fortress: 41 rooms for its 38 spaces, 42 openings, 19 × 14 cells, floors from −256 to +512.

Every corner lies on the 512 grid. Where today's lowering could not draw a space honestly, the room's `notes` say so
and the gap is listed below. The sketches were not bent into boxes without a note.

Sketching from measurements also found errors in L2 (and in L1 and the prose). These are being corrected in every
level now, and each prose brief ends with an "L3 pass" corrections note. One consequence: **R2-G18's evidence from
Warlord's Fortress was wrong.** It has no stacked rooms; only the Temple's dome needs vertical stacking (R3-K7).

The fixes below would be needed for a builder to reproduce either dungeon from its sketch; without them the build
cannot be walked end to end.

## Sketch and schema gaps (`rooms.yml`)

| # | Wanted | Content it would carry | Why v0 or today's lowering cannot | From |
| --- | --- | --- | --- | --- |
| R3-K1 | **Path rooms**: `path: [points]` with `width`, which may curve | 256-wide corridors (about 18 in the fortress); the bending entry tunnels | Outlines are convex polygons on the 512 grid, so corridors come out 512 wide and floor area is overstated (fortress 38.5 against 32 M units²) | W, T |
| R3-K2 | **Non-convex outlines**, or `parts:` under one room id joined without walls | L-, U- and T-shaped rooms (bent caverns, L-shaped stairs and passages, a hall with a side bay) | Convex, no collinear points, at most 16 points. Splitting a room leaves 16-unit wall stubs at the joins; the alternative, convex hulls, adds about 37 % area in the caves | W, T |
| R3-K3 | **Sloped floors**: `floor: {from, to, toward}`, plus `relief: uneven` | Cave ramps (0 → +448, −640 → −900 …); entry tunnels rising toward the door | One flat floor per room. Each ramp becomes a riser or a doorway high in a wall, so the build is not walkable end to end | W, T |
| R3-K4 | **Stairs**: `openings[].steps: {count, rise}`, or a stair kind of room with run, rise and landings | A 9 × 32 temple flight; 5 steps from nave to apse; the fortress's flights of 256 to 512 | Different floors at an opening produce a sheer wall below the hole | W, T |
| R3-K5 | **Ceiling shape**: a centre height and an edge height, coves, vaults | A great hall at +768 in the middle with coves down to about +600 | One flat ceiling per room | W |
| R3-K6 | **Floor regions inside a room**: `wells` or `daises: [{outline, rise, edge: steps\|ledge}]` | The nave's octagonal well 128 below its rim; the altar dais | One floor per room; splitting the rim ring into rooms invents walls | T |
| R3-K7 | **Horizontal openings or stacked rooms**: `ceiling_openings` or `above:` | The dome: about 1,000 across, from a +224 ring up to about +864, over the nave | Openings need facing parallel walls, so portals are only vertical; a stacked room builds as a sealed box | T |
| R3-K8 | **Holes in an outline**: `islands` or `pillars: [{at, size}]` | Four walk-round rock pillars; the aisle columns | An outline is one ring with no holes | T |
| R3-K9 | **Full-width openings with columns**: `openings[].width: full`, `columns: n` | Nave open to both aisles and to the apse along whole sides | Width is capped at the shared wall minus 32, leaving stubs; nothing can stand inside an opening | T |
| R3-K10 | **Wall thickness** (`walls: {thickness}` with the outlines inset, or an `openings[].depth`), or a finer sanctioned snap for shells | Walls 64–256 thick; door passages about 240 deep; closets about 0.05 M units² | On the 512 grid a wall is 0 or 512 thick. 16 fortress doorways sit in zero-thickness walls, which the door-thickness check will reject once doors are added | W, T |
| R3-K11 | **Per-opening kind and look**: `openings[].kind` (door, secret, portcullis, open, stairs) and `look` | Rooms with both a plank door and a secret wall | The door leaf look comes from the room's theme | W |
| R3-K12 | **Theme bands and per-wall surfaces**: `bands: [{texture, height}]`, `walls: {north: …}` | Trim bands; bookcase, bed and cabinet faces; the dome's lighter stone | A theme has only wall, floor, ceiling, reveal and door | T |
| R3-K13 | **Niches and alcoves** in `rooms.yml` | Bunk and chest niches about 256 deep; a chest alcove | Not expressible | W |
| R3-K14 | **Placement inside a room**: `start.where`, wall anchors | The arrival at the tunnel's north-west end by the gate door | Only the room is named | W |
| R3-K15 | **A stated datum** for room `floor`/`ceiling` z, following `plan.datum` | The whole sketch uses arrival = 0 | The schema says only "Floor height (z)" | T |

## Validator and tool issues

| # | Issue | From |
| --- | --- | --- |
| R3-V1 | Once `rooms.yml` exists, `validate` runs the full lowering and requires `objects.yml` `start`. A sketch-only L3 should take its arrival from the plan's `entrances[]`. Both briefs carry an `objects.yml` holding only `start` until then | W, T |
| R3-V2 | No overlap check between room outlines: a scratch copy with overlapping rooms passed `validate` and `build --dry-run`. Zero-thickness shared walls are not reported either | T |
| R3-V3 | `rooms[].space` and `openings[].link` are not checked against `plan.yml`, and there is no coverage check (every space has a room, every link an opening) | W |
| R3-V4 | An internal opening between the parts of one split space cannot be marked as internal | T |
| R3-V5 | Themes must name texture files and their sizes, but L2's `d1trim` is not in the shared texture inventory (`d1trimle` was used) | W |

## Left over from round 2

- `map_stats` has no field for the alert period (7 days at Harmondale), and `steal_fine` does not cover it.
- The four open round 2 checks remain on c5's list: `handed_in_at`, `diagram.file`, `rules.respawn` and
  `rim.broken_by`.

## Round 3 status (2026-11-12, from c5)

| Status | Ids |
| --- | --- |
| **Closed** | R3-V1 (the start now comes from the plan's arrival entrance), R3-V2 (overlapping rooms are refused), the `diagram.file` check (part of R2-V1), the `map_stats` alert period (`alert_days`, `steal_perm`) |
| **Open, in progress** | R3-V3: coverage is not checked yet (every space has a room, every link an opening); id references are already checked |
| **Deferred to indoor authoring (S3)** | R3-K1 to K15, R3-V4, R3-V5 |
| **Deferred to S3 or S4** | R2-G1 to G19 |
| **Outdoor L3 sketch** | **Decided 2026-11-12** (the user left the choice to c5): the proposal above as written, with (1) the coarse height grid allowed, optional, step 4 cells or coarser, points and cliffs winning where both speak; (2) the building owns its footprint (`footprint_cells`), a plot carries `at` (north-west corner), `facing` and `door_to`, no `rect`; (3) one file, `sketch.yml`; no image is read by anything, the review picture is generated. Schema file and checks come with S4 |

## Round 4 status (2026-11-12, from c5, after S3's first part)

| Status | Ids |
|---|---|
| **Closed** | R3-K1 (`path` and `width`), K2 (outlines of any simple shape, 64 points), K3 and K4 (`slope: {to, toward, steps}`), K8 (`pillars`), K10 (outlines need not be on the 512 grid; the gap between facing walls is the wall), K13 (a niche is a small room), K14 (`at`, `offset`); conditions `gold`, `stat`, `award`, `autonote`, `all`; event `effects` and `else_effects` |
| **Partly** | K6 (raised `platforms`; no sunken regions), K12 (`walls` with their own surface; no trim bands) |
| **Open** | K5, K7, K9, K11, uneven relief, R3-V3, V4, V5, R2-G1 to G19 |


---

# Round 4 (2026-11-12): outdoor L3 sketches and the Xeen Act I briefs

The outdoor L3 sketches exist: `mm8_out02/L3/sketch.yml` (Ravenshore) and `mm7_7out02/L3/sketch.yml` (Harmondale).
Both are in the decided format: c5's three answers to the proposal, coordinates in terrain cells, plots carrying
`{building, at, facing, door_to}`, and footprints parked in each building's plan `notes` until R2-G6 adds
`footprint_cells`.

Both plan folders pass `oymap validate` and `fmt --check`. `sketch.yml` has no validator until S4, so each brief had an
interim self-check in `tools/` (both reported 0 errors). Both scripts are now retired: `oymap validate` checks sketches. Measured L2 errors found while sketching are being corrected in
L1–L3 and the prose briefs.

Five Xeen Act I L1 briefs also exist: `devdocs/xeen/briefs/xd01`–`xd05/L1/`, all valid. They are new designs, with
provisional ids in the Xeen ranges.

## Outdoor sketch format (`sketch.yml`)

These were **invented to fill an undefined shape** in the proposal, and need fixing in the S4 schema. The two sketches
did not always choose the same form:

| # | Wanted | Content | Used for now | From |
| --- | --- | --- | --- | --- |
| R4-S1 | **`footprint_cells: [front, depth]`** as a real building field, rotated by the plot's `facing` | Every building's size | Text in the building's plan `notes`; the two sketches use different note conventions | R, H |
| R4-S2 | **Addressing one member of a group** (a house of `count: 22`, one fruit tree of 4, one camp of 2, one fort wave): `index`, or per-member sub-ids | 47–54 plots per map | `{building, index}`, with the meaning of each index in plan notes | R, H |
| R4-S3 | **`door_to` accepting a space id** (square, plaza, pier, shelf, back yard), a minor-street layer, and door positions for buildings with two doors or an off-centre door | Doors onto the square or harbour plaza; houses on an open shelf | Nearest link (up to about 7 cells off), or `door_to` left out | R, H |
| R4-S4 | **Ids for structures and treasure**, so they can be placed: piers, bridges, crate stacks (R2-G7), chests, the beacon, the magic pedestal | 13 chests and a chest tree; bridges; unnamed lights | Not placed; notes only | R, H |
| R4-S5 | **Several positions under one id**: packs, two sightline targets, a landmark with two notches | 10 wolf-pack circles; a view of two targets | Repeated ids, or `index` | R, H |
| R4-S6 | **Frame shapes**: `frame.playable [x, y, w, d]`, `frame.rim {space, side, depth}`, and an edge pointing at its arrival entrance | Playable square; rim strip; arrivals about 19 cells in from the edge | Invented as written | R, H |
| R4-S7 | **Water body ids and shapes**: `kind`, `level`, falls and outlets between bodies | Three lakes under one plan id, the upper at 384 spilling into the lower at 0 | `index`; `level` invented; falls not stated | R, H |
| R4-S8 | **A ring-shaped district**: polygons with `holes`, or a `rest: true` flag | Harmondale's outer rim | Full square plus `rest: true` | H |
| R4-S9 | **Cliff side**: `down: left\|right` along the line | Which side of each cliff is low | Invented as written | H |
| R4-S10 | **Cuttings and overpasses**: `roads[].cut: {depth}`, and bridges `over:` a road | South road in a 640-deep cutting under a stone bridge | Notes | H |
| R4-S11 | **Raised pads**: `pads: [{polygon, height}]` | Crystal plinth at 320, temple terrace at 640 | Height points | R |
| R4-S12 | **Areas: `kind` (encounter, keep_clear, open) and `count` (markers)**, with their own ids for keep-clear and open areas | Fields of fire; quiet approaches | Invented; keep-clear areas borrow set-piece ids | H |
| R4-S13 | **Water routes as a layer** | Boat route to a sea cave | A road with `surface: water` | R |
| R4-S14 | **Distinct facing meanings**: an entrance's arrival facing against a plot's door side; bridges and buildings without a front | — | Overloaded `facing` | R, H |
| R4-S15 | **One grid for districts and plots**: half cells for district polygons inside towns | Sub-district outlines in town | Districts whole cells, plots half cells | H |
| R4-S16 | **Views**: `height` defined as above ground | — | Defined as written | R |

## Xeen Act I L1 briefs (new designs)

| # | Wanted | Content | Used for now |
| --- | --- | --- | --- |
| R4-X1 | **`link.kind: ride`** (or `lift` with a horizontal motion) | Mine carts on a trestle and along a rail line | `lift` plus `purpose` text, which the flow graph reads as vertical |
| R4-X2 | **A vehicle `neighbours[].kind`** | The cart down to the Deep Mine; the escape-shaft cage | `scripted` and `door` |
| R4-X3 | **`opens_from: inside` on neighbours and entrances**, two-way afterwards | Culvert grate, caved-in adit with winch, escape shaft, orc back gate | A qbit `condition` plus `variants`; `one_way: true` becomes false once opened |
| R4-X4 | **`keys[].found_in` accepting a neighbour or map code, and a giver or quest step** | A key under a rain barrel on X1; the Crystal Key from Valia | `how` text |
| R4-X5 | **The effect vocabulary (R2-G1), still open** | +2 stat pools, a stat vat, gold veins, gem clusters, a skull vendor taking gems, a curse until rest | `behaviour` text |
| R4-X6 | **`gold` on treasure** (part of R2-G5) | Caches of 50–400 gold | Notes |
| R4-X7 | **Declared map variables** (`variables:` in the plan or project), checked in conditions | 10 names (turntable, gate bars, hoist) | Unchecked strings; a typo passes |
| R4-X8 | **Declared awards** (`awards:` like `qbits:`) | The Crusader title; the Red Dwarf Badge | The roof gated on a qbit instead |
| R4-X9 | **Sightlines out of the map** (`to:` a neighbour, map code or backdrop) | The tower roof's view over X1 to the world rim | A placeholder room plus notes |
| R4-X10 | **Harmful floors**: `hazard: {kind: lava\|fluid\|poison, damage}` on spaces and zones | Slag channel, cauldron, flooded working | `features` and set-piece text |
| R4-X11 | **Monster modifiers on a population, with a condition** | Orcs frenzied while the drummer drums | Set-piece prose |
| R4-X12 | **Reinforcements that move on a trigger** (part of R2-G4) | Barracks sergeants pouring out at the gong | Prose |
| R4-X13 | **Slots for a world with no monster rows yet**: family, allowed ranks and levels per slot | "Spiders rank b–c only"; "witches rank a only" | Family names in `monster`; `tier` too coarse |
| R4-X14 | **A walkable ring round a hole** | The tower balcony round the open cauldron shaft | `islands: 1` plus a note |
| R4-X15 | **`goals[].handed_in_at`: defined form and check** (part of R2-V1) | Neighbour id or a bare map code | Both forms used |

## Round 4, part 2: from the dungeon redraws with the S3 room shapes

Both dungeon L3 sketches were redrawn with the S3 shapes: non-convex outlines, path rooms, flights and ramps, real
wall thickness, pillars, platforms and niches. Both walk end to end. c5's reading of floor area:

| Map | Sketch | Original | Rooms reached |
| --- | --- | --- | --- |
| Temple of the Moon | 38.2 M units² | 37.4 | 40 of 42; the other two are niches too small to stand in |
| Warlord's Fortress | 31.5 M units² | 31.7 | 51 of 51 |

Measured plan corrections made during the redraws were carried into L1 and L2.

| # | Wanted | Content | Status |
| --- | --- | --- | --- |
| R4-K1 | **An opening naming its wall**: `from_wall` / `to_wall` | Openings between parallel corridors 256 apart landed in the wrong wall; the competing walls were broken into short in-line pieces to steer them | c5 is adding `from_wall` / `to_wall` |
| R4-K2 | **Several openings between the same two rooms** | The octagon's diagonal ledges | Answered: allowed, as long as each opening finds its own facing pair |
| R4-K3 | **An opening in a sloped room's side wall** | The tunnel end with its secret wall; the original eases along it | Answered: use a landing, a short flat room beside the slope |
| R4-K4 | **Low walls and parapets** | Stair parapets drawn as full-height walls | Open |
| R4-K5 | **Curved ramps** | The curving entry tunnel, built as ramp, level bend and ramp | Open |
| R4-K6 | **Irregular pillars** (polygon pillars) | Rock pillars, which are boxes for now | Open |
| R4-K7 | **Stacked platforms** | The altar's low step round its foot | Open |
| R4-K8 | **A platform or pillar against a wall** | Bunks and a chest ledge, which now stand 4 units clear | Open |
| R4-K9 | **Point budget for outlines** | Temple cave outlines use 9–20 points from the measurements. c5's rule is about a dozen points before asking, so the largest caves are over that; flagged to c5 | Open (rule) |

---

# Round 5 (2026-11-12): review redraws, Temple L4, Xeen XD-01 to XD-05 at L2 and L3

**Folders:**
- Temple and Fortress L3 redrawn after the user's review:
  - Temple: islands, full-width cave joins, rough walls, more corners, measured doorways.
  - Fortress: smoothed tunnel bends, measured doorways and connectors.
- `mm7_7d06/L4/`: objects and wiring for a playable rebuild. Being merged onto the redrawn caves now.
- `devdocs/xeen/briefs/xd01`–`xd05/L2` and `L3`: new designs.

All of these validate, `fmt --check` passes and `build --dry-run` succeeds.

**Walk checks:**
- Walked in the game (headless): XD-01, XD-03, XD-04 (including the hoist ride), XD-05, the Fortress and the Temple L4.
- Checked by reach audit and route probes only: XD-02.

**compare.py against the originals:**

| Map | Readings (in / near / out) | Floor area (sketch / original, M units²) | Doorway width (sketch / original) |
| --- | --- | --- | --- |
| Temple | 23 / 10 / 2 | 37.15 / 37.44 | 512 / 512 |
| Fortress | 19 / 10 / 6 | 31.63 / 31.7 | 256 / 256 |

## Tool defects

| # | Defect | From |
| --- | --- | --- |
| R5-V1 | **`audit --reach` / `metrics` report 0 rooms reached when the start is more than about 256 from every wall.** Cause: `PathMap::snapToNearestWalkableFloor` (`game/pathfinding/PathMap.cpp`) never counts a floor the point lies inside. Repro: shapes_gallery plus one 1024 × 768 room at (3000, 3000) with the start in its middle gives 9 of 9 unreached. It also stays stuck in a pit that `probe` and the game both walk out of. **This is shared game code: a fix touches the game's pathfinding** | XD-03, XD-05 |
| R5-V2 | **Start choice ignores conditions:** the build takes the first non-exit entrance by id, even a barred one (XD-05's back gate) | XD-05 |
| R5-V3 | **Music by name installs a row the game refuses** ("invalid redbook track"). `music` should be validated as a track number, or a world music table should map names to numbers. Xeen side: `devdocs/xeen/PRODUCTION.md` E10 | XD-01, XD-03, XD-04, XD-05 |
| R5-V4 | **Texture names and sizes are not validated**: a made-up name passes, and the 10-character limit (e.g. `cloudsabove`) is not checked | XD-03, XD-04 |
| R5-V5 | **A sloped room with corners partway along its slope fails** ("non-planar after coordinate quantization") unless the corners fall on whole-number heights. Undocumented | Temple caves |
| R5-V6 | **Rough walls skip any stretch shorter than two steps**, and an island whose hole fails to cut is skipped silently. Both undocumented | Temple caves |
| R5-V7 | **A smoothed path's inside wall can get near-duplicate points** on a tight bend (a 1-unit edge) | Fortress |
| R5-V8 | **The metrics build folder is named from the brief path**, so two runs on one brief at once collide (two unexplained "reached 0" readings) | Temple caves |
| R5-V9 | **A headless exit by MoveToMap needs** `execute_event` → `select_topic OK` → `advance_runtime {follow_map_move: true}`; a bookcase's GiveItem puts the item in the cursor (`held()`). Worth documenting for playtests | Temple L4 |

## `rooms.yml` (beyond R3/R4-K, still open)

| # | Wanted | Content | From |
| --- | --- | --- | --- |
| R5-K1 | **Stacked rooms** (R3-K7) are now the main blocker for Xeen | XD-04's tower had to become a "crooked tower" with each floor a quarter turn round the shaft. XD-02's spiral went from 1.5 turns to 0.6, and its trestle cannot be walked. XD-03's gallery cannot overhang the hall, and its slag channel cannot pass under a bridge. XD-01's cellar cannot lie under the hall | XD-01–05 |
| R5-K2 | **Diagonal joins at any width**: joins need exactly parallel walls on whole units, so a diagonal 256 tunnel had to be 260 | Fortress |
| R5-K3 | **A door flush in a corner**: 16 units of wall stay beside every door that is not full width | Fortress |
| R5-K4 | **Ramps that pinch or bulge**: ramps must be convex | Temple caves |
| R5-K5 | **Cave floor relief** (uneven, not ramps) | Temple, XD-05 |
| R5-K6 | **Sunken floors and liquids**: pools, slag gutters with a state (dry, then slag), the drain pool, the toad tank, the snake pool | XD-01–05 |
| R5-K7 | **Open sky over a room** (a tower roof) | XD-04 |
| R5-K8 | **Rough islands** (islands have smooth walls) | Temple caves |

## `objects.yml` and `wiring.yml` (L4)

| # | Wanted | Content | From |
| --- | --- | --- | --- |
| R5-O1 | **Placed actors**: monster family, rank, level, HP, hostility, group, carried item, NPC identity | Three swordsmen and a captain carrying the longbow | Temple L4 |
| R5-O2 | **Floor items**: a named item, or random at a treasure level | The moon floor tile (a goal); 7 random floor items | Temple L4 |
| R5-O3 | **Timed events and a spell-cast effect**: `trigger: {every: <game time>}` or on load, and `{cast: {spell, skill, mastery, from, to}}` | The fire-bolt trap | Temple L4 |
| R5-O4 | **Script and teleport presets in a new (non-overlay) build**: refused today ("a script preset cannot have the X as its source") | — | Temple L4 |
| R5-O5 | **Spawns**: count per spawn and a forced rank | Rank-a spawns of 2–5 | Temple L4 |
| R5-O6 | **Chests**: a treasure level per roll, a wall-face chest placed with `wall`/`along`, and `secret: true` | The cabinets' mixed tiers; secret rock-face chests | Temple L4 |
| R5-O7 | **Doors**: sideways slide, two leaves that part, a `secret` flag | Double sliding doors; a secret lifting wall; XD-05's rolling boulder | Temple L4, XD-05 |
| R5-O8 | **Switches**: a tiling `off` surface, and plates on platform sides | 128-wide bookcase texture on wider plates; library cases | Temple L4 |
| R5-O9 | **Ladders** (the engine has scene ladders) | Loft ladder, herb-loft ladder, pit and rope ladders | XD-01, XD-03, XD-04, XD-05 |
| R5-O10 | **Horizontal movers (rides)** with a route, speed and a run condition | Mine carts on a trestle and the Deep Line | XD-02 |
| R5-O11 | **A lift tied to an upper opening**, stopping flush | The hoist cage at the rim gate | XD-02 |
| R5-O12 | **Destructibles and placed ambient sounds in objects.yml** | Burnable war drums and their sound loops | XD-05 |
| R5-O13 | **An exit that appears on a condition** | The X4 adit wall after the winch is used | XD-02 |

## Decoration library (art, not schema)

Missing shared models, used as placeholders for now:
- glass bug tanks, a hoist frame, a heart trough;
- herbs, beds, tables, a winch, cloaks;
- a weapon rack, a gong, a mine cart, a lever, a lectern;
- war drums.

---

# Round 6 (2026-11-12): sketch schema, the Temple nave and status

**Outdoor sketches:** c5 added a sketch schema, checks and `render-sketch`. Both outdoor L3 sketches now pass
`oymap validate` with no issues, and the interim check scripts are deleted.
- 19 (Ravenshore) and 40 (Harmondale) buildings carry `footprint_cells`, and no plots overlap.
- Height points outside their bands were fixed by notching or splitting band outlines; no ranges were widened.
- Round 4 closed by this: S1, S2, S9 and S16. Partly closed: S3, S5, S6, S7, S8 and S12.

**Temple of the Moon:** redrawn with c5's new features:
- levels, inner flights and parapets;
- ceiling levels (the dome);
- bookcases as chest furniture with end surfaces;
- wall bands, gabled openings and stair risers;
- raking flight sides, a tapered altar, and the dome's ring and ribs as beams.

The Temple's checks, from the latest pass:
- L3 `compare.py`: 23 in / 11 near / 1 out. The one "out" is the smallest sector area; the original has tiny sectors.
- L4 playtest: 188 of 188 steps pass.

## Still open

| # | Wanted | Content | From |
| --- | --- | --- | --- |
| R6-1 | **A sketch group member's form** | Which house form each index is (tower house, ogre hut) | Ravenshore, Harmondale |
| R6-2 | **A band cut by a sea-level pass, and a band ridge** | A pass through the uplands; a one-cell spit between two lakes | Ravenshore, Harmondale |
| R6-3 | **Holes in band outlines** | The fort mound inside the basin | Harmondale |
| R6-4 | **A default ground material** | Grass everywhere else | Ravenshore |
| R6-5 | **More sketch checks**: a height point inside water, and ground that no height point names | The spit inside the lower lake; unflagged rises inside the basin outline | Harmondale |
| R6-6 | **What a footprint covers and where its doors are** | A base, yard, forecourt or bridge deck; door positions on a plot | Harmondale |
| R6-7 | **Plots without a front** | Bridges | Harmondale |
| R6-8 | **Comments survive `fmt`** (or are documented as dropped) | — | Ravenshore |
| R6-9 | **Flight sides**: a surface, a thickness, and a foot height different from the head height | The original's 7tfb11 parapets, 32 thick, 64 above floor at both ends | Temple |
| R6-10 | **Curved beams, or beams that follow a ceiling level** | Dome ribs curving down to the collar; a domed drum | Temple |
| R6-11 | **Niche hoods** | Two niches at the nave's west end | Temple (c5 has this queued) |

c5's queue also holds, from earlier rounds: a sequence of textures along a wall, a level reaching the room's walls,
`top_surface` and `random_items: 0` on chests, fixed actors and floor items, and stacked rooms (the Xeen blocker).
