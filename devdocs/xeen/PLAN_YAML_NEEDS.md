# Xeen: what the plan format must express

Written 2026-11-12 for Map Studio (`devdocs/map_studio/`), so that Xeen's map plans (PRODUCTION.md MU-3 to-scale map
plans and MU-6 dungeon graphs) and the studio's `plan.yml` / flow graph are **one format**. Xeen writes no plan tool of
its own; it uses the studio's schema v0 when that exists. Section 1 maps Xeen's needs onto the brief levels of
`devdocs/map_studio/CALIBRATION.md`. Section 2 lists what CALIBRATION's "What a brief specifies" lists do not cover.
Section 3 is a draft of X1 at L1 to show the shape (field names are suggestions; the studio owns the schema).

## 1. Fields Xeen needs, by brief level

| Level | Outdoor (MU-3) | Indoor (MU-6) |
| --- | --- | --- |
| L0 | pitch, mood, map code (`X1`, `XD-04`) → stem | same |
| L1 | face/layer; neighbours with travel kind (edge, boat, stable, pyramid, mirror, roof, fall, scripted); height bands and landforms; water bodies; road graph with purposes; districts (town footprint, hamlets) with role; dungeon entrances; POIs with behaviour; landmarks and **signature views**; encounter zones (slot A/B/C, d-level, count, pack size); deliberate open spaces with a written purpose; quest hooks (QUESTS.md ids) | room graph with size classes; floors/bands; entrances and exits **to several maps**; critical path; loops; locks and keys (where each key comes from, by QUESTS.md id); set pieces as rules; secrets; quest hooks |
| L2 | building kit per district and buildings by service; decoration palette per zone; POI parameters (stat, permanent/temporary, charges); population per zone incl. named uniques and factions; atmosphere (sky preset, theme, weather, music area, ambient emitters); map rules | kit/theme per wing; mechanism inventory; population per room incl. uniques with modifiers/actor scripts; treasure per room (chest tier, fixed items); light density; map rules |
| L3 | to-scale sketch on the 128-cell grid (512 units): footprints, road lines, water, key heights, rim strip, camera positions | room outlines on the 512 grid, heights per band, vertical core of a tower |

## 2. Not covered by CALIBRATION's lists

Each item says where it is used in the Xeen design. "World-level" items probably belong in a file above the map
projects; see 2.1.

### 2.1 World-level (above one map)

| Need | Fields | Used by |
| --- | --- | --- |
| **Faces and layers** | per map: `face` (cloudside, darkside) and `layer` (surface, sky, plane, finale); default sky, death map and Town Portal page per face | WORLD_DESIGN D1, E3 |
| **Travel graph beyond neighbours** | typed links: map edge (days), boat/stable (schedule, days), **paired pyramids** (gate qbit), **mirror network** (discovery qbit per mirror, face-local), celestial boats, **one-way** links (tower roof → sky map), **falls** (sky → surface), **scripted** transitions (griffin flight into Castle Blackfang) | WORLD_DESIGN §3.3 |
| **World critical path** | main-quest steps (M1–M42) as goals placed on maps/rooms, with the qbits/items each needs and gives, so the flow-graph solve can run across maps | QUESTS §1 |
| **Level and treasure bands** | per map: A/C monster levels, map_stats treasure level, lock/trap | MAPS sheets |

A world plan (e.g. `devdocs/xeen/world_plan.yml` now, a studio world file later) could hold these; per-map projects
reference it by map code. Xeen is the first case with ~70 maps whose links matter, so this is worth deciding early.

### 2.2 Outdoor

| Need | Fields | Used by |
| --- | --- | --- |
| **World rim** | `rim: {sides, cliff_band, fall: death or target}`; rim strip drawn on L3 | D9, E5 (X1, X2, X5, X6, X7, D1, D3, D4, D6) |
| **Staged states** | `states:` keyed by qbit: BModel groups shown/hidden (incl. translucent "out of phase"), actor groups present/absent, houses open/closed, atmosphere or music override | Newcastle (4 stages), Castle Kalindra exterior (4), five cursed towns |
| **Time conditions** | day/night/month on POIs, encounters and doors (coffin at night, Nightshadow bats at night, month shrines) | Q-C7, shrines |
| **Map rules** | `no_fly`, `no_spells`, local weather override (always overcast), town buffer radius (no spawns), `no_teleport` | WORLD_DESIGN §3.4, E7 |
| **Ambient emitters (ODM)** | point and area sounds (lava, waterfall at the rim, wind, machines) | E9 |
| **POI behaviours** beyond wells/fountains/shrines | obelisk (riddle word), destructible camp with reward ("burn the camp"), genie lamp (choice table), readable statue gated by an award (Linguist), reflector (story device), outdoor teacher NPC (skill, tier), market stalls (vendor ids), stat challenge, talking skull vendor (gems) | QUESTS §4.3 |
| **Factions on encounter zones** | faction id, peaceful until/unless qbit (diplomacy flips relations) | 8 factions, `relations.yml` |
| **Signature views** | named cameras (position on the grid, target, purpose) used for MU-4 concepts and later fixed review cameras | MU-4 |

### 2.3 Indoor

| Need | Fields | Used by |
| --- | --- | --- |
| **Open-air BLV profile** | sky over rooms, cloud floor, `fall_through: {target map, position mapping}`, no-Fly | Sky maps X8, X9, D7; planes P1–P4; Shangri-La (E4) |
| **Multi-map entrances** | entrances/exits on different outdoor maps (mines on X1 and X4; Cave of Illusion's two mouths; tower roof exit to a sky map) | XD-02, XD-10, XD-04, XD-11, XD-12 |
| **Pocket sets** | one project with several disconnected pockets, each with its own entrance (incl. entry by falling) and one way out | DD-10 Gemstone Mines, DD-11 Troll Holes |
| **Stacked towers** | floors as bands around a stair/lift core; the four-floor towers become one BLV | XD-04, XD-11, XD-12, DD-02, DD-05–08 |
| **Staged wings** | rooms/wings sealed by qbit (translucent shimmering walls until a stage) | DD-03 Castle Kalindra, XD-13 Newcastle Keep |
| **Door conditions beyond keys** | password (typed answer), dialogue choice ("think positive" gates), stat check (Might ≥ n), time of day, party award, item count (5 Megacredits) | XD-12, DD-12, XD-10, XD-24 |
| **Room-scale mechanisms** | illusory walls (visible, no collision), water level mover (drain plug), conveyor floors, trapdoor floors, teleport maze, element sundials, generators whose destruction drops barriers | XD-10, DD-17, XD-12, DD-15, XD-19 |
| **Map-wide counters** | kill counts as quest goals (Vertigo pests, three ghost waves), wave summons on a trigger (gongs) | M1, Q-C6 |
| **Puzzles as rules** | inputs, states, solution (colour pedestals, sundials to 9, Golem Dungeon's three puzzles, PALADIN boulders, true-name gate) | QUESTS |

## 3. Draft: X1 at L1 (shape only)

```yaml
map: X1                       # devdocs/xeen/MAPS.md
stem: xeen_x1                 # placeholder
kind: outdoor
face: cloudside
layer: surface
levels: {a: [2, 4], c: 12, treasure: 1, lock_trap: [0, 1]}
pitch: >
  Start pocket. A walled river town in green meadows; the east edge is the world rim, where the river falls into
  the stars. Witch Tower visible from town from day one.
neighbours:
  - {to: X3, kind: edge, side: west, days: 5}
  - {to: X7, kind: edge, side: north, days: 5}
  - {to: X2, kind: boat, from: vertigo_dock, schedule: [mon, thu], days: 2}
  - {to: D1, kind: pyramid, at: pyramid_knoll, gate: {qbit: M7}}
rim: {sides: [east], fall: death}
landform:
  height_bands: {hills_north: high, meadow: low, dead_forest: mid, rim_cliff: cliff}
  water: [{id: pitchfork_creek, kind: river, ends: rim_falls}, {id: delta, kind: shallows}]
roads:
  - {id: west_road, from: vertigo.west_gate, to: edge.west, purpose: travel}
  - {id: north_road, from: vertigo.north_gate, to: edge.north, purpose: travel}
  - {id: orchard_road, from: vertigo.east_gate, to: pyramid_knoll, purpose: landmark}
districts:
  - {id: vertigo, role: start_town, services: full, residences: 18, buffer: no_spawns}
  - {id: toad_meadow, role: hamlet, npcs: [myra, valia]}
dungeons: [XD-01, XD-02, XD-04, XD-05, XD-06]
pois:
  - {id: obelisk, kind: obelisk}
  - {id: fountain_ability, kind: fountain, effect: {stat: luck, permanent: 2, charges: mapvar}}
  - {id: waters_of_power, kind: well, effect: {hp: temporary}}
  - {id: shrine_poison, kind: shrine, effect: {resist: body, permanent_once: true}}
  - {id: orc_outpost_1, kind: camp, destructible: true, reward: xp}
  - {id: water_reflector, kind: story_device, quest: M37}
encounters:
  - {id: orcs_north, slot: A, family: orcs, d: 1, packs: 3, pack_size: [2, 4]}
  - {id: toads_meadow, slot: B, family: swamp_things, d: 1, packs: 2}
  - {id: dead_forest, slot: C, family: rotting_dead, d: 2, packs: 3}
open_spaces:
  - {id: orchard, purpose: "view east to the rim; quiet place between town and pyramid"}
views:
  - {id: rim_view, from: orchard_road, look: east, purpose: signature}
quests: [M1, M2, M3, M4, Q-C20, Q-C21, Q-C22]
```
