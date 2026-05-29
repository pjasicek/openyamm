# MM9 TXT Data Table Inventory

This inventory covers MM9 table-like source data currently present under
`assets_dev/worlds/mm9/source/data/` and how it should fit into OpenYAMM's flat engine/base plus world-package model.

The guiding rule is the same as `docs/WORLD_CAMPAIGN_MOD_ARCHITECTURE.md`: OpenYAMM is the engine, worlds are content.
Data the party can carry or retain across worlds should be global engine/base data with explicit availability filters.
Data tied to MM9 geography, NPCs, monsters, map presentation, or LithTech assets should remain in `worlds/mm9`.

## Current MM9 Source Tables

Top-level MM9 data files found locally:

- `ACTOR.txt`, 2100 rows: actor/monster/NPC combat rows, model/skin refs, movement, attacks, resists, scripts.
  Recommended owner: `worlds/mm9`. Add an MM9 actor/monster loader later; do not merge into the global monster table.
- `AISPAWN.txt`, 35 rows: spawn scenario groups.
  Recommended owner: `worlds/mm9`. This is world-local encounter/spawn support.
- `BOOK AND SCROLL TEXT.csv`, 505 rows: readable books and scroll text keyed by item/text id.
  Recommended owner: engine/base text with MM9 availability, or `worlds/mm9` until item import lands.
- `CONCAT.csv`, 104 rows: MM9 item affixes/concatenations and enchant metadata.
  Recommended owner: engine/base item system with `available_worlds: [mm9]`.
- `CREDITS.txt`, 201 rows: MM9 credits text.
  Recommended owner: `worlds/mm9`.
- `ENGLISHGAMETEXT.txt`, 547 rows: UI/global text strings.
  Recommended owner: mostly `worlds/mm9`; promote shared strings only when reused.
- `GAMETEXT.txt`, 568 rows: UI/global text strings.
  Recommended owner: mostly `worlds/mm9`; decide relationship to `ENGLISHGAMETEXT.txt` during import.
- `INFO.txt`, 80 rows: in-game informational/Legends text with camera-ish metadata.
  Recommended owner: `worlds/mm9`; presentation/help content, not base mechanics.
- `JOURNAL.txt`, 9 rows: chronicle/history prose.
  Recommended owner: `worlds/mm9`, with qbit-backed journal registry bridge if needed.
- `MAPSTATS.txt`, 47 rows: MM9 map metadata, music, encounters, town flags.
  Recommended owner: `worlds/mm9`; convert to canonical `world.mm9.map.*`.
- `MASTERITEMLIST.csv`, 529 rows: MM9 items, descriptions, icon/model keys, restrictions, value, size/quality fields.
  Recommended owner: engine/base item registry with MM9 availability.
- `MATERIALS.txt`, 19 rows: surface/material hit sounds.
  Recommended owner: `worlds/mm9` table with an engine loader.
- `MMIXNAMES.csv`, 78 rows: name pools.
  Recommended owner: `worlds/mm9`.
- `MMIXSHOPS.txt`, 92 rows: shop metadata, NPC ids, stock classes, restock, treasure levels.
  Recommended owner: `worlds/mm9`; rows may reference global item categories.
- `MONSTERS.txt`, 286 rows: monster stats similar to `ACTOR.txt`, with extra FX/voice fields.
  Recommended owner: `worlds/mm9`; compare against `ACTOR.txt` before choosing authority.
- `PLAYER.txt`, 9 rows: LithTech player/class templates, movement, voices, starting items, melee weapon.
  Recommended owner: `worlds/mm9` reference until proven RPG-authoritative.
- `PROJECTILE.txt`, 72 rows: projectile physics/audio/explosion/homing data.
  Recommended owner: `worlds/mm9` content with an engine projectile loader.
- `SKILL AND MASTERY DESC.csv`, 25 rows: skill descriptions and mastery effect text.
  Recommended owner: engine/base skill registry with MM9 availability/effect ruleset.
- `SPELL.txt`, 49 rows: MM9 spell definitions, school tags, mastery blocks, costs, recovery, FX/audio.
  Recommended owner: engine/base spell registry, separate MM9 spellbook/ruleset.
- `STATDESC.csv`, 24 rows: MM9 stat descriptions.
  Recommended owner: engine/base stat text with MM9 character-ruleset availability.
- `WEAPON.txt`, 44 rows: LithTech weapon model/projectile/audio/runtime attack data.
  Recommended owner: `worlds/mm9` equipment-presentation/combat table.
- `PCVOICES/*.txt` / `*.csv`, 36 files: voice/personality text and sound rows.
  Recommended owner: `worlds/mm9`.

Existing generated/converted MM9 runtime data already lives under `assets_dev/worlds/mm9/dialogue/`,
`assets_dev/worlds/mm9/maps/`, `assets_dev/worlds/mm9/models/`, and related asset folders. This inventory does not
propose moving those generated sidecars by hand.

## Recommended Ownership Model

### Engine/Base Global With Availability

Promote these when implementing cross-world-capable MM9 gameplay data:

- `MASTERITEMLIST.csv`
- `CONCAT.csv`
- `BOOK AND SCROLL TEXT.csv`
- `SPELL.txt`
- `SKILL AND MASTERY DESC.csv`
- `STATDESC.csv`

These are global because a party can carry items, learn skills/spells, retain stats, and inspect descriptions while
moving between worlds. They still need explicit availability so MM9-only data does not leak into MM6-MM8 shops,
treasure, teachers, or spellbooks.

Recommended metadata fields for promoted rows:

```yaml
canonical_id: item.mm9.scramasax
source_game: mm9
source_table: MASTERITEMLIST.csv
source_id: 7
available_worlds: [mm9]
available_rulesets: [mm9]
treasure_worlds: [mm9]
shop_worlds: [mm9]
legacy_aliases:
  - mm9.item.7
```

Use the same pattern for spells, skills, and stats:

```yaml
canonical_id: spell.mm9.bless
spellbook: mm9
ruleset: mm9
available_worlds: [mm9]
legacy_aliases:
  - mm9.spell.1
```

`available_worlds` answers "can this appear naturally in this world?" It should not necessarily mean "delete from the
party when leaving the world." Party-owned instances and learned abilities should remain in save data unless the active
world's rules explicitly forbid use.

### World-Scoped Data

Keep these under `assets_dev/worlds/mm9/`:

- `ACTOR.txt`
- `AISPAWN.txt`
- `MONSTERS.txt`
- `MAPSTATS.txt`
- `MMIXSHOPS.txt`
- `MATERIALS.txt`
- `PROJECTILE.txt`
- `WEAPON.txt`
- `MMIXNAMES.csv`
- `PLAYER.txt`
- `INFO.txt`
- `JOURNAL.txt`
- `CREDITS.txt`
- `GAMETEXT.txt`
- `ENGLISHGAMETEXT.txt`
- `PCVOICES/*`

Most of these can still use engine loaders. Ownership is about data scope, not code location. For example, a shared
projectile system can load `worlds/mm9/data_tables/projectiles.yml`, and a shared shop system can consume MM9 shop
definitions through a world package.

## Items

MM9 items should become engine/base item definitions, not a separate world-only inventory type.

Reasons:

- The party can carry items across world boundaries.
- Shops, treasure, quest rewards, readable books, equipment, and save/load should reference one canonical item
  repository.
- Artifacts/relics can sit on top of the same registry with rarity/source metadata.

Recommended approach:

1. Convert `MASTERITEMLIST.csv` to a new normalized source, probably `assets_dev/engine/data_tables/mm9_items.yml` at
   first or an appended engine `items` registry once schema support exists.
2. Keep raw MM9 ids as aliases, not canonical ids.
3. Add availability/world-generation fields instead of duplicating item tables per world.
4. Convert `CONCAT.csv` into MM9 enchant/affix rows attached to the engine item system with `ruleset: mm9`.
5. Keep MM9 pickup models/icons/skins in `worlds/mm9` unless the same visual asset is intentionally shared.
6. Keep `WEAPON.txt` as MM9 equipment runtime/presentation data linked by canonical item id or source id.

Do not squash MM9 item columns into the current MMerge `items.txt` shape until the missing concepts are modeled:
class restrictions, MM9 item categories, icon/model asset names, size/quality fields, and MM9 affix rules.

## Spells

MM9 spells should be global definitions, but they should not be folded into the MM6-MM8 spellbook as if they were the
same table.

MM6-MM8 currently use a legacy nine-school spellbook model. MM9 uses a different spell schema with `Elemental`,
`Spirit`, `Light`, and `Dark` tags plus per-mastery parameter blocks. Some names overlap, but mechanics and school
requirements can differ.

Recommended model:

- Add a global spell registry keyed by canonical ids.
- Add `spellbook` or `ruleset` as a first-class field.
- Store learned spells by canonical id in party/save data.
- Let active world/UI select a spellbook view, e.g. `spellbook: mm9` or `spellbook: mm678`.
- Casting checks should use both the spell's ruleset and current world policy.

World switching policy should be explicit:

- Learned MM9 spells stay learned when leaving MM9.
- The MM6-MM8 spellbook UI should not show MM9 spells unless a base/mod deliberately enables cross-spellbook display.
- Quick spell should store a canonical id and become inactive/unusable if the active world/ruleset does not allow it.
- Teachers and shops should filter by `available_worlds` and `spellbook`.

## Skills

MM9 skills should be global skill definitions with MM9-specific effect rules, not simple aliases to MM6-MM8 skills.

Likely MM9 skill families from `SKILL AND MASTERY DESC.csv`:

- combat/equipment: `Armor`, `Shield`, `Blade`, `Spear`, `Cudgel`, `Bow`, `Thrown Weapons`, `Unarmed`;
- magic: `Elemental Magic`, `Light Magic`, `Dark Magic`, `Spirit Magic`;
- utility: `Identify Item`, `Disarm Trap`, `Merchant`, `Perception`, `Learning`, `Meditation`;
- condition/protection text rows appear in the same table and need classification during import.

Some are conceptually shared with MM6-MM8, but effect semantics differ enough that canonical ids should initially be
MM9-specific, for example:

```text
skill.mm9.blade
skill.mm9.cudgel
skill.mm9.elemental_magic
skill.mm9.spirit_magic
```

Common skills can later gain alias or equivalence metadata if cross-world trainers/items need it. Do not make `Blade`
silently mean MM6-MM8 `Sword` or `Dagger`; that will break class caps, equipment checks, and mastery effects.

## Stats

MM9 does not line up cleanly with the current MM6-MM8 stat model.

MM9 visible base stats from `STATDESC.csv`:

- `Might`
- `Magic`
- `Endurance`
- `Accuracy`
- `Speed`
- `Luck`

MM6-MM8 use separate `Intellect` and `Personality`, while MM9 text says maximum spell points are based on `Magic`.
Therefore `Magic` should not be treated as a display alias for either existing field.

Recommended model:

- Add a character ruleset/stat-set concept.
- Store stat definitions in a global registry with `available_rulesets`.
- Allow derived UI labels and formula inputs to differ by ruleset.
- For MM9 characters, use `Magic` as its own stored or projected stat.
- For cross-world travel, define an explicit projection rule before allowing MM6-MM8 and MM9 character rulesets to
  share one party without restrictions.

Until projection rules are designed, assume MM9 stat handling is a separate ruleset in engine/base data.

## Classes And Character Creation

No obvious MM9 RPG class table equivalent to MMerge `Class Skills.txt` was found in the top-level source-data set.
`PLAYER.txt` has rows such as `Warrior`, `PaladinL`, `Heretic`, `ArcherL`, `Druid`, `Sorceress`, `GoodKing`, and
`EvilKing`, but its columns are LithTech player-template data: movement speeds, voice command text, starting item ids,
scale, melee weapon, and "uber weapon". Treat it as reference/presentation data until validated against actual MM9
RPG character creation.

Class availability probably needs to be reconstructed from multiple sources:

- item restrictions in `MASTERITEMLIST.csv`;
- spell skill requirements in `SPELL.txt`;
- skill descriptions in `SKILL AND MASTERY DESC.csv`;
- generated dialogue/training data under `assets_dev/worlds/mm9/dialogue/`;
- scripts under `assets_dev/worlds/mm9/source/scripts/` and generated Lua sidecars.

Recommended direction:

- Keep MM9 class/race rules in engine/base once validated.
- Use `available_worlds: [mm9]` and `ruleset: mm9`.
- Do not graft MM9 classes onto the current MMerge class matrix until the source authority is clear.

## Monsters, Actors, And Spawns

MM9 actor/monster data should remain world-scoped.

`ACTOR.txt` and `MONSTERS.txt` overlap heavily but are not byte-identical in shape. `ACTOR.txt` has many more rows and
appears to include commoners/NPCs and monsters; `MONSTERS.txt` has additional FX/voice columns. Before runtime import,
decide which table is authoritative for:

- combat stats;
- display/model/skin data;
- NPC-like actors vs monsters;
- resists and damage profiles;
- scripts and special behavior;
- death/resurrection FX.

This should not be merged into the flat MMerge `monster_data.txt`. MM9 monsters use LithTech model assets and MM9
movement/combat metadata; they belong to `world.mm9.monster.*` canonical ids.

## Shops, Maps, Dialogue, And Journals

These are world-local by default:

- `MMIXSHOPS.txt` should become `worlds/mm9/data_tables/shops.*` or generated YAML consumed by shared shop code.
- `MAPSTATS.txt` should become canonical MM9 map metadata tied to `world.mm9.map.*`.
- `JOURNAL.txt`, generated `dialogue/journal_*.yml`, and generated NPC files should remain MM9 story data.

QBits remain global save bits per OpenYAMM architecture, but MM9 story text does not need to live in the engine root
unless a shared journal registry requires a merged index. If promoted, use the reserved MM9 qbit/key namespace rather
than raw ids.

## Projectiles, Weapons, Materials, And Voices

These should use shared engine systems but world-owned definitions:

- `PROJECTILE.txt`: shared projectile runtime, MM9 projectile definitions.
- `WEAPON.txt`: shared combat/equipment runtime hooks, MM9 first-person/LithTech weapon definitions.
- `MATERIALS.txt`: shared material-hit sound lookup, MM9 material rows and MM9 sound assets.
- `PCVOICES/*`: shared voice-set API, MM9 voice packages.

This keeps runtime code reusable without making MM9-specific assets globally visible.

## Suggested Import Targets

Initial conservative layout:

```text
assets_dev/engine/data_tables/
  item_availability.yml
  mm9_items.yml
  mm9_item_affixes.yml
  mm9_spells.yml
  mm9_skills.yml
  mm9_stats.yml

assets_dev/worlds/mm9/data_tables/
  actors.yml
  monsters.yml
  ai_spawns.yml
  map_stats.yml
  shops.yml
  projectiles.yml
  weapons.yml
  materials.yml
  names.yml
  voices.yml
```

The final engine format can differ, but the ownership boundary should stay this way.

## Implementation Checklist

- [ ] Add source inventory tests that confirm every top-level `source/data` file is classified in this document.
- [ ] Add CSV/TSV parsing tests for `MASTERITEMLIST.csv`, `CONCAT.csv`, `SPELL.txt`,
  `SKILL AND MASTERY DESC.csv`, and `STATDESC.csv`.
- [ ] Define a minimal availability schema shared by items, spells, skills, stats, classes, shops, and treasure.
- [ ] Add canonical id generation for MM9 items and raw-id aliases.
- [ ] Convert `MASTERITEMLIST.csv` into a typed MM9 item table without losing source columns.
- [ ] Convert `CONCAT.csv` into typed MM9 affix/enchant data.
- [ ] Convert `BOOK AND SCROLL TEXT.csv` and link readable text to canonical item ids.
- [ ] Add a spellbook/ruleset field before importing `SPELL.txt`.
- [ ] Import `SPELL.txt` into a typed MM9 spell table with all mastery blocks preserved.
- [ ] Import `SKILL AND MASTERY DESC.csv` as MM9 skill text/effect metadata.
- [ ] Import `STATDESC.csv` as MM9 stat text tied to a stat-set/ruleset.
- [ ] Decide whether `ACTOR.txt`, `MONSTERS.txt`, or a merge of both is authoritative for MM9 monsters.
- [ ] Convert world-local `MAPSTATS.txt`, `MMIXSHOPS.txt`, `PROJECTILE.txt`, `WEAPON.txt`, and `MATERIALS.txt`
  only after the shared runtime consumer exists.
- [ ] Add idempotency tests for generated tables: source data -> normalized YAML/TXT -> source-equivalent typed rows.

## Open Questions

- What is the authoritative MM9 class/race source for normal RPG character creation?
- Should MM9 items be appended to the existing engine `items.txt`, or should engine item loading accept multiple typed
  item registries with one merged canonical view?
- Should `Magic` be stored as a separate stat or projected from a hidden `Intellect`/`Personality` pair for engine
  compatibility?
- Which spells, if any, should be intentionally cross-spellbook after world switching?
- Are `ACTOR.txt` and `MONSTERS.txt` separate runtime concepts or editor/export variants of the same actor registry?
