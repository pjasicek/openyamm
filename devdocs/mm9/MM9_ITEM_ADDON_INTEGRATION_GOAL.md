# MM9 Item Addon Integration Goal

## Implementation Status

Implemented. The deterministic import currently classifies all 529 source rows as 390 world-owned definitions, 138
intentional exclusions, and one engine mapping (Cure Wounds to item 222). It emits 390 converted source icons, 115
readable bindings, all 22 skill-learning items, 63 explicit L7 effect profiles, four complete equipment sets, and a
raw-id alias table. The literal SCR audit resolves 164 references to world definitions and one to the health-potion
mapping; the two references to excluded spellbook 347 remain explicit unsupported operations.

The runtime composes mounted contributions into the global catalog, preserves package/schema requirements in saves,
keeps quest and unique content out of procedural/shop pools, exposes set activation in item inspection, and uses
shared systems for Throwing, `LearnSkill`, readable text, equipment restrictions, effects, and event item operations.
Ordinary random/shop distribution remains deliberately disabled as described below. MM9 armor paperdoll regeneration
is tracked separately in `MM9_ARMOR_PAPERDOLL_GENERATION_GOAL.md`; its prior experiments were invalidated by the
universal body-armor foot/footwear/hoof exclusion rule. Helms, boots, belts, and the remaining body-equipment families
still follow their visual gates.

## Objective

Import supported Might and Magic IX items into OpenYAMM's shared item, inventory, equipment, shop, chest, event, and
save systems without adding the MM9 rows to the MMerge-owned base tables under `assets_dev/engine/`.

MM9 owns its item definitions, mappings, provenance, and visual assets under `assets_dev/worlds/mm9/`. The mounted MM9
package contributes those definitions to one validated global runtime item catalog on top of the normal MMerge base.
The party may carry an MM9 item into another mounted world, so MM9 item definitions must remain available for the
entire session and must not be unloaded merely because the active map belongs to another world.

This goal is also the first concrete consumer of generic world/mod table contributions. Implement the contribution
mechanism generically, but keep the initial supported table set limited to what the MM9 item import actually needs.
Do not introduce a second MM9 inventory, equipment, party, shop, or save runtime.

## Architectural Decision

Build the effective runtime data in this order:

```text
MMerge/OpenYAMM base tables
          +
mounted world/addon contributions, including MM9
          +
explicitly ordered mod overrides
          =
validated global runtime tables
```

Content ownership and runtime scope are separate:

- `assets_dev/engine/` owns the unchanged MMerge/OpenYAMM base definitions.
- `assets_dev/worlds/mm9/` owns MM9 source-derived definitions and assets.
- The runtime catalog is global because items are persistent party state and can cross world boundaries.
- The flat base decides which world/addon packages are mounted. The active world does not implicitly decide which
  persistent item definitions exist.
- Engine code gains generic package contribution support; engine asset tables do not receive copied MM9 rows.

Do not implement this by letting filesystem search order replace `engine/data_tables/items.txt` with an MM9 file. Table
composition must be typed and explicit: load the base table, load declared contributions, validate them, and merge them
into one catalog.

## Initial Scope

Import the supported MM9 item definitions from the authoritative source `mm9/extracted/DATA/DATA/MASTERITEMLIST.csv`.
The local file currently contains 529 sparse definitions with raw ids from 2 through 600.

The initial supported set includes:

- weapons and ranged weapons, including returning thrown daggers and axes backed by a complete shared OpenYAMM
  Throwing skill;
- armor, shields, helms, gloves, boots, belts, rings, and amulets;
- artifacts, relics, named equipment, and equipment sets with normalized statistics and implemented special/set effects;
- all quest items, with deterministic content placement rather than random distribution;
- letters, books, tutorial manuscripts, journal scraps, and other readable documents together with their underlying
  MM9 text data;
- MM9 skill-learning books, implemented as consumables that teach normalized OpenYAMM skills;
- ordinary miscellaneous items, including source rows whose MM9 category is demonstrably incorrect;
- item names, descriptions, values, source categories, restrictions, and other source facts needed for auditing;
- explicit normalized OpenYAMM gameplay statistics and equip rules;
- stable MM9 raw-id to global item-id mappings;
- lossless source-icon provenance; and
- generated, deterministic reports describing every imported, excluded, deferred, or invalid source row.

Catalog import and gameplay distribution are separate. An imported definition must not automatically enter random
treasure, shops, or monster drops. Those systems require explicit contribution rows after the item's balance and visual
state have passed their respective gates.

## Explicitly Excluded From This Goal

- MM9 spell scrolls;
- MM9 spellbooks;
- MM9 potions;
- MM9 spell-casting runestones;
- MM9 wands;
- MM9 spells or a second spell catalog;
- a separate MM9 skill runtime;
- generic loadable mod-defined skills as part of this item-import work;
- AI-generated or AI-edited inventory and paper-doll art;
- implicit replacement of an unrelated MM6/MM7/MM8/MMerge item;
- automatic random-loot or shop distribution for every imported row;
- direct runtime parsing of `MASTERITEMLIST.csv`; and
- loading package definitions by nondeterministic "next free id" allocation.

Dialogue and script references to excluded MM9 spell scrolls, spellbooks, potions, runestones, and wands must use an
explicitly authored mapping to an existing OpenYAMM item when the content design calls for an equivalent. Otherwise the
operation remains unsupported and fails visibly with source provenance. It must never resolve through a coincidentally
equal raw id.

The known MM9 Cure Wounds/health-potion use maps to the appropriate existing OpenYAMM health potion; it does not create
a duplicate MM9 potion definition. MM9 wand definitions are omitted even when an approximate OpenYAMM spell exists;
content may explicitly grant an existing OpenYAMM wand instead. Item 590, `Clover`, is not treated as a potion despite
its incorrect MM9 source category: import it as an audited miscellaneous item. Potion-like objects categorized and
used as quest items remain quest items and are not usable potion definitions.

## Source And Reference Policy

Use these sources in descending order of authority:

1. Extracted MM9 data, especially `MASTERITEMLIST.csv`, `BOOK AND SCROLL TEXT.csv`, and the referenced files under
   `mm9/extracted/ART/ART/INVENTORYICONS/`.
2. Recovered MM9 behavior and source findings in the local `/home/pjasicek/github/OpenMM9` checkout.
3. The local `/home/pjasicek/github/GodotMM9` checkout as an independent import, asset, and presentation cross-check.
4. Current OpenYAMM shared item, inventory, equipment, paper-doll, event, and save behavior as the target runtime
   contract.

OpenMM9 and GodotMM9 are behavioral and structural references. Do not copy their code, native MM9 runtime architecture,
or engine-specific ownership into OpenYAMM.

## Package Layout

Use a world-owned layout equivalent to:

```text
assets_dev/worlds/mm9/
  world.yml
  data_tables/
    items.txt
    random_items.txt                    optional; only accepted distribution rows
    complex_item_pictures.txt           later paper-doll placement contribution
    complex_item_picture_offsets.txt    later portrait-specific corrections
    item_skill_mapping.yml
    item_balance_profile.yml
    item_balance_overrides.yml
    item_sets.yml                         authored normalized set membership and bonuses
    readable_items.txt                   normalized readable-item to text bindings
    readable_item_text.txt               preserved/normalized readable document text
  state/
    item_id_map.yml
    item_import_report.yml
  icons/
    mm9_item_*.png
```

Exact filenames may be adjusted to match the generic contribution manifest, but ownership must stay under the MM9
package. Generated files must identify their source and regeneration command and must not be edited by hand. Authored
balance and compatibility overrides must remain separate from generated source conversions.

## Manifest And Stable Id Contract

Extend the world/mod manifest model with declared, per-domain id ranges and table contributions. The MM9 item package
should reserve the item-id range `10000-10999`, subject to a one-time audit proving every item-id consumer and save path
can represent that range without narrowing.

The initial deterministic mapping is:

```text
global item id = 10000 + raw MM9 item id
```

This maps the current raw range to `10002-10600` and leaves space for later MM9-authored compatibility items. Item,
QBit, event, NPC, and other identifiers are separate domains and may use overlapping numeric values without colliding.

Each definition also has a stable canonical id, for example:

```text
mm9:item/poor_sword
```

The generated `item_id_map.yml` records at least:

- package id;
- canonical item id;
- raw MM9 item id;
- global OpenYAMM item id;
- source row and source-file identity;
- import status; and
- content-schema/importer version.

Never assign item ids from mount order or from the current highest loaded id. At package composition time, reject:

- overlapping declared item-id ranges;
- duplicate global ids;
- duplicate canonical ids;
- rows outside their owner's declared range;
- undeclared attempts to replace base rows; and
- mappings that changed incompatibly without an explicit migration.

Save metadata must record the required package ids and compatible content-schema versions. Loading a save containing an
MM9 item without the required MM9 package or stable mapping must produce a specific missing-content/migration error;
it must not silently delete, replace, or reinterpret the item.

## Table Composition Semantics

Use the existing OpenYAMM table layouts for normalized runtime data so shared systems consume one `ItemDefinition`
shape regardless of source package.

Contribution modes are explicit:

- `append`: add new canonical definitions within the contributor's declared id range;
- `override`: replace selected fields of a named existing canonical definition, allowed only from an explicitly
  declared override file with dependency and priority metadata; and
- `distribution`: add accepted item ids to random treasure, shop, chest, or drop tables without redefining the item.

The MM9 item import uses `append`. It must not use implicit row replacement. The merge result should retain package and
source provenance in memory for diagnostics and editor inspection even when gameplay code only needs the normalized
definition.

All mounted portable definitions are composed once into the global catalog. Switching active worlds may change maps,
events, presentation, and world-local services, but it must not invalidate item pointers, ids, inventory instances, or
saved equipment.

## Normalized `items.txt` And Extension Columns

Columns 0-16 retain the existing OpenYAMM `items.txt` layout and meaning. Shared runtime code continues to consume
those normalized fields.

Columns 17-31 are standardized OpenYAMM package-item fields. They are available to every world or mod and are consumed
by shared runtime systems; they must not contain MM9-only meanings. Begin package-specific audit/provenance fields at
column 32. Every extension column must have a header and an `x_<package>_` prefix. Do not use anonymous positional
values.

| Column | Header | Purpose |
| --- | --- | --- |
| 17 | `package_id` | Owning mounted package. |
| 18 | `canonical_id` | Stable namespaced identity. |
| 19 | `source_item_id` | Package-local source/import alias. |
| 20 | `content_flags` | Shared policies such as `Quest`, `NoRandom`, `NoShop`, `NoDrop`, or `Readable`. |
| 21 | `normalized_tier` | Audited `L0-L7` balance comparison. |
| 22 | `use_action` | Shared data-driven use action, for example `LearnSkill` or `ReadText`. |
| 23 | `use_target` | Argument to the shared use action. |
| 24 | `set_id` | Data-owned equipment-set membership. |
| 25 | `effect_profile` | Shared content-effect profile id. |
| 26 | `allowed_class_roots` | Optional canonical class-root restrictions. |
| 27 | `required_might` | Optional Might requirement. |
| 28 | `required_accuracy` | Optional Accuracy requirement. |
| 29 | `inventory_width` | Shared inventory-grid width. |
| 30 | `inventory_height` | Shared inventory-grid height. |
| 31 | `visual_status` | Explicit imported/final/provisional visual state. |

The initial MM9 extension tail includes:

| Column | Header | Purpose |
| --- | --- | --- |
| 32 | `x_mm9_raw_item_id` | Original sparse MM9 id. |
| 33 | `x_mm9_canonical_id` | Stable namespaced identity. |
| 34 | `x_mm9_source_equip_type` | Original equip/category token. |
| 35 | `x_mm9_source_skill` | Original skill token, including spelling and case. |
| 36 | `x_mm9_source_icon_pcx` | Original PCX virtual path or source-relative path. |
| 37 | `x_mm9_source_name_type` | Original MM9 item subtype/name-type field. |
| 38 | `x_mm9_source_min` | First original numeric combat/stat field. |
| 39 | `x_mm9_source_max` | Second original numeric combat/stat field. |
| 40 | `x_mm9_source_field_05` | Preserved source field pending or retaining decoded semantics. |
| 41 | `x_mm9_source_flags` | Original source flags/token. |
| 42 | `x_mm9_source_restrictions` | Original class/use restriction text. |
| 43 | `x_mm9_import_status` | Imported, deferred, excluded, or invalid. |
| 44 | `x_mm9_balance_profile` | Versioned normalization profile or override id. |

Use meaningful recovered names instead of generic names such as `source_field_05` as soon as semantics are established.
The importer owns these columns for audit and regeneration. The gameplay loader must ignore unknown extension columns;
it must not accidentally derive MM9 behavior from them.

The extension tail is not a substitute for the canonical id map or manifest validation. It makes the generated table
self-describing and preserves useful source facts beside each normalized row. `MASTERITEMLIST.csv` remains the source
authority, while the mapping and reports are reproducible generated products.

## Skill Compatibility And Core Throwing Decision

For this goal, map MM9 item requirements and bonuses into the existing OpenYAMM skill set through a data-owned
compatibility table, except for Throwing, which becomes a complete shared OpenYAMM core skill. Do not add a generic
custom/mod-defined skill registry as a side effect of importing items.

Adding a real skill affects character state, save schemas, class/race caps, trainers, mastery, UI, formulas, combat,
items, and scripting. A minimally used registry entry would create a misleading partial feature. If a future world or
mod needs a genuinely new skill, define that work in a separate engine-level goal with complete semantics and tests.

Keep the item format forward-compatible by using canonical string skill ids in contribution data and by preserving
`x_mm9_source_skill`. Do not store package skills as load-order-dependent enum ordinals. Throwing receives a stable
engine-owned skill id exactly like Sword, Axe, or Bow.

Throwing is not an MM9-only compatibility shim. Implement it across shared character state, saves and migrations,
class/race mastery caps, skill descriptions and UI, trainers, LearnSkill items, attack formulas, recovery, projectiles,
equipment checks, editor/debug inspection, and tests. Initial weapon behavior is:

- throwing daggers and throwing axes are ranged weapons which use the shared ranged attack/projectile path;
- the weapon returns, consumes no ammunition, and remains equipped after an attack;
- Normal adds Throwing rank to attack;
- Expert also adds rank to damage;
- Master halves the throwing recovery penalty; and
- Grandmaster removes that penalty and enables the additional throwing-dagger attack, with exact timing and balance
  verified against the normalized OpenYAMM combat model.

Use these initial class-family caps as authored defaults, then expand them into explicit entries for every concrete
class column in `class_skills.txt`:

| Class path | Initial progression/cap |
| --- | --- |
| Thief -> Rogue -> Assassin | Basic -> Expert -> Grandmaster |
| Thief -> Rogue -> Spy | Basic -> Expert -> Master |
| Monk -> Initiate -> Ninja | Basic -> Expert -> Grandmaster |
| Monk -> Initiate -> Master | Basic -> Expert -> Master |
| Ranger -> Hunter -> Bounty Hunter or Ranger Lord | Basic -> Expert -> Master |
| Knight -> Cavalier -> Champion or Black Knight | Basic -> Expert -> Master |
| Paladin -> Crusader -> Hero or Villain | Basic -> Expert -> Master |
| Archer -> Warrior Mage -> Master Archer or Sniper | Basic -> Expert -> Master |
| Dark Elf -> Patriarch | Expert -> Master |
| Minotaur -> Minotaur Lord | Expert -> Grandmaster |
| Troll -> War Troll | Expert -> Master |

Classes outside the audited table default to unable to learn Throwing. Do not infer access from another weapon skill.
Race bonuses may raise a lower class cap only through explicit `race_skills.yml` rules; add and test the Minotaur
Throwing affinity deliberately rather than deriving it from Axe.

Initial mapping principles:

- MM9 `Blade` training maps to the existing Sword and Dagger compatibility group, but an individual sword item maps to
  Sword and an individual dagger maps to Dagger according to its source subtype.
- MM9 `Cudgel` normally maps to Mace; staff-like or otherwise distinct source subtypes must be classified explicitly
  rather than flattened blindly.
- MM9 `Bow`, `Spear`, and `Shield` map to their direct OpenYAMM equivalents where behavior matches.
- MM9 `Armor` maps each concrete item to Leather, Chain, or Plate according to that item's source type and evidence.
- MM9 `Thrown` maps to the new shared Throwing skill rather than Dagger, Axe, Bow, or an item-local pseudo-skill.
- MM9 composite or magic skill labels map through explicit compatibility rows and never create hidden MM9-only skills.
- Misspellings and case variants such as `Sheild` remain preserved in provenance but normalize through an audited
  alias table.
- An unmapped skill or ambiguous subtype is an import failure for that row, not `Misc`, `None`, or an arbitrary
  fallback.

Dialogue/training compatibility and concrete item proficiency may therefore differ: a composite training operation can
affect several base skills, while one physical item requires the single base skill matching its actual subtype.

### Skill-Learning Item Behavior

Import all 22 existing `Items_Skill` definitions, including item 307, `Thrown Skill`. Add a generic `LearnSkill`
item-use action to the shared item system. A learning item targets the active/selected character, resolves its authored
canonical skill or compatibility group, validates class/race access, and is consumed only after the complete learning
operation succeeds. Already-known skills, forbidden skills, and an atomic composite mapping which cannot be completed
must fail without consuming the item and must present a specific reason.

Use the same authored compatibility groups as MM9 dialogue teachers: `Armor` resolves to the applicable normalized
armor group, `Elemental` resolves to Fire/Air/Water/Earth, and `Blade` resolves to Sword/Dagger. Preserve the
discrepancy where `SKILLBOOK.scr` describes raw item 285 as a Blade book but `MASTERITEMLIST.csv` has no row 285. If
that book is needed, add it as an explicitly authored MM9 compatibility item with script provenance; do not pretend it
was imported from a missing CSV row.

## Stat Normalization

Preserve original source values and normalized gameplay values as distinct concepts.

The importer must retain source damage/stat fields, value, category, restrictions, and provenance. A versioned,
data-owned balance profile then produces OpenYAMM fields such as equip category, skill group, damage dice, armor class,
value, identification/repair difficulty, rarity, and treasure tier. Apply this process to every imported equippable
item, not only artifacts and relics.

Do not apply one global multiplier. Normalize by role and progression tier against the active MMerge/OpenYAMM item
catalog:

- compare weapons with weapons of the same handedness and proficiency;
- compare armor within its concrete armor class;
- preserve relative progression within an MM9 family;
- assign ordinary equipment to an audited OpenYAMM `L0-L7` progression tier by comparing role, source progression,
  rarity, price, and effective power with the current merged catalog;
- use the tier to constrain expected base damage/armor, value, repair/identify difficulty, enchantment budget, and
  approved distribution, rather than copying MM9 numbers directly;
- handle artifacts, relics, quest items, and named specials through explicit audited overrides without exempting them
  from the same compatibility comparison;
- keep source prices as provenance while allowing normalized OpenYAMM prices; and
- never encode balance exceptions as item-id conditionals in gameplay code.

Artifacts and relics are required imports, not deferred catalog omissions. Preserve their identity and intended role,
translate every recovered modifier into existing shared effects where semantics match, and implement a named shared
effect when the behavior is genuinely missing. Do not silently discard an unsupported modifier or compensate only by
raising generic statistics. An artifact/relic may use L7 as a comparison ceiling while remaining a unique item outside
ordinary random tier rolls.

Equipment sets are also required. Add data-owned set membership and threshold bonuses, evaluate them from currently
equipped items in the shared equipment/stat path, expose active/inactive bonuses in item or character inspection, and
test equip, unequip, death/condition transitions, cross-world travel, and save/load. Set activation must be derived from
equipped canonical item ids; do not store redundant mutable activation flags in saves.

The generated report must show both source and normalized values and name the rule or override that produced each
normalized field.

The initial `mm9_balance_v1` profile keeps ordinary source damage dice and armor points only where they already fit the
equivalent shared handedness/armor layout. It normalizes ordinary equippable gold values through category-specific
`L1-L6` envelopes measured from the current engine random-item catalog, rather than through a global MM9 multiplier.
Quest values are forced to zero and `L7` artifacts, relics, and set pieces use their explicit unique overrides. Every
row records which of these rules was applied so later tuning can be regenerated and reviewed as data.

## Readable Documents And Quest Items

Import MM9 letters, books, tutorial documents, journal scraps, and similar records as shared readable items using the
same runtime interaction as existing OpenYAMM readable scrolls and scraps. Import their underlying text from
`BOOK AND SCROLL TEXT.csv`, retain raw text identity/provenance, and emit an explicit item-to-text binding. A document
does not require a map binding to exist in the catalog, although it remains unobtainable until content places or grants
it. Duplicate display names are not duplicate identities.

MM9 tutorial documents remain readable source content even when they describe MM9-specific controls or interfaces.
They are not authoritative OpenYAMM help and must not replace current engine instructions. Any Bootcamp flow which is
intended to teach the actual OpenYAMM interface may grant an explicitly authored OpenYAMM tutorial document instead,
while the original MM9 manuscript remains available to source-faithful content.

Import every MM9 quest item definition. Normalize every quest item's runtime value to `0`, apply the shared quest-item
sale/drop restrictions, and exclude it from all random treasure, monster-drop, shop-stock, and procedural generation
tables. Quest items may enter play only through deterministic authored sources such as a specific map pickup,
container/chest slot, NPC/event grant, quest transformation, or scripted reward. Source value remains in provenance.

Quest-labelled equipment remains equippable when that is part of its intended behavior, but it retains the same
non-random and non-shop quest distribution policy. Potion-like quest tokens remain non-consumable unless an authored
quest action explicitly transforms or consumes them. Keys remain inventory items where MM9 scripts use item
checks/takes; do not silently convert them into QBits.

## Visual Asset Policy

MM9 currently provides 315 item-specific/source-shared PCX files under
`mm9/extracted/ART/ART/INVENTORYICONS/`, generally 64x64, for the 529 source definitions. Preserve the exact source PCX
path in `x_mm9_source_icon_pcx` even when several definitions share one image.

For the current goal phase:

- use the original 64x64 PCX as a binding image-generation input for every distinct promoted design; the generated
  item must remain visibly recognizable as that MM9 object rather than becoming a generic item of the same family;
- use MM6-MM8 assets only as style, lighting, scale, and inventory-presentation references; they must not replace the
  MM9 object's silhouette, colors, fittings, or distinctive details;
- render every equippable item upright on its main equipment axis, with the functional head/muzzle/top above the
  grip, shaft, stock, or lower end. A diagonal source PCX must be normalized to an upright MM6-MM8 inventory pose;
- use a transparent, low-resolution canvas selected for the final silhouette, and derive inventory-grid width and
  height from that final canvas rather than retaining the source PCX's fixed 64x64 dimensions;
- allow one generated asset to be reused where multiple source rows intentionally reference the identical PCX;
- retain deterministic, lossless PCX decoding/conversion as the provisional runtime fallback until each accepted
  design is promoted and reviewed;
- namespace every promoted filename, for example `mm9_item_10002.png`;
- preserve transparency, source hash, source dimensions, conversion command/version, and item bindings in a generated
  manifest;
- do not place MM9 images in `assets_dev/engine/icons`;
- do not use an unrelated base item icon as a fallback; and
- do not distribute an item whose required runtime visual is missing without an explicit visible development-only
  status.

The original 64x64 icon is binding source material, not proof that the final OpenYAMM inventory and paper-doll
presentation is complete. The generated/adapted visual pass produces:

- an inventory-grid image with appropriate transparent canvas and slot footprint;
- an equipped/paper-doll image, which may initially be the same image where that is visually valid;
- doll-type variants for armor or other body-fitting equipment;
- grip/anchor coordinates for weapons and shields; and
- rows for `complex_item_pictures.txt` and `complex_item_picture_offsets.txt` where body equipment needs per-doll or
  per-portrait placement.

Generated/adapted art must be explicitly reviewed and recorded in the authored generation manifest, including its
source PCX, target canvas, generation intent, transparency correction, and post-processing. Promotion is per distinct
source design; no unrelated base icon or family-generic generated fallback is accepted.

Weapon, ranged-weapon, and shield placement is owned by the authored
`tools/mm9_import_discovery/mm9_item_equipment_visuals.yml` overlay. The overlay records the sprite-local `Equip X/Y`
anchor, the compatible MM6-MM8 reference item, derivation method, and review state. The MM9 item importer requires
complete overlay coverage for those equipment families and emits the standard item-table fields; generated
`assets_dev/worlds/mm9/data_tables/items.txt` must not be edited directly. Candidate anchors may be used for development
previews but retain a visible `generated_equipped_anchor_candidate` status until reviewed on the supported doll types.
The reference/preview helper is `tools/mm9_import_discovery/generate_mm9_item_equipment_visuals.py`.

Body-fitting equipment uses the separate authored overlay,
`tools/mm9_import_discovery/mm9_item_body_equipment_visuals.yml`. It owns each promoted design's fitted variant names,
closest MM6-MM8 geometric references, per-doll base positions, exceptional portrait adjustments, source-icon binding,
and review state. The armor-variant generator uses it to emit the MM9-owned `complex_item_pictures.txt` contribution
and will emit `complex_item_picture_offsets.txt` when a reviewed portrait exception is needed; generated table output
must not be hand-edited.

The paperdoll-equipment portion is implemented by
`tools/mm9_import_discovery/generate_mm9_equipment_variants.py`. It consumes the
original MM9 PCX and promoted inventory PNG, transfers their design onto an explicitly mapped fitted reference alpha
geometry without AI generation, and emits 350 world-owned PNGs, 35 complex-picture placement rows, and a hashed
provenance manifest. Every armor currently has reviewed `v1/v1a` through `v5/v5a` output.

The existing MMerge paperdoll assets establish these required final variants:

| Slot | Required fitted assets per promoted runtime item | Notes |
| --- | --- | --- |
| Armor | `v1/v1a`, `v2/v2a`, `v3/v3a`, `v4/v4a`, `v5/v5a` | One fitted silhouette per equippable doll type and two right-arm poses. The `a` pose is used when no right-hand weapon is equipped. |
| Helm | `v1`, `v2`, `v4`, `v5` | Minotaur/type 2 cannot equip helms, so no `v3` is required. A deliberately fitted base image may be reused only when the rendered review proves it already fits that type. |
| Boots | `v1`, `v2`, `v4`, `v5` | Minotaur/type 2 cannot equip boots, so no `v3` is required. |
| Belt | `v1`, `v2`, `v3`, `v4`, `v5` | Every normal equippable doll type needs its own fitted silhouette. |

Type 5 is the non-equippable dragon paperdoll and receives none of these assets. With the current imported definitions,
the full target is 350 armor displays, 64 helm displays, 44 boot displays, and 30 belt displays: 488 logical fitted
bindings. Use separate runtime files by default. Explicit reviewed reuse can reduce physical files: three existing base
hats demonstrate that an inventory image can occasionally already be a valid type-1 fitted helm, while the current
MM9 catalog-icon fallbacks visibly are not. The 16 MM9 helm definitions also contain only 15 distinct source-PCX
designs, so one reviewed four-image fitted design may be reused through explicit bindings.

Offsets alone are not a substitute for these variants. Existing belts, boots, helms, and armor change width,
perspective, limb openings, occlusion, and silhouette between doll types. Armor also changes sleeve/arm pose between
the normal and `a` image. A deterministic scale or warp may provide an alignment candidate, but it cannot be promoted
as precise fitted art without a rendered review.

Use `tools/mm9_import_discovery/render_paperdoll_equipment_preview.py` to perform that review. It loads the actual
character, doll-type, item, complex-picture, portrait-adjustment, and icon data, composites a selected item in the
runtime layer order, and emits a contact-sheet PNG plus an optional JSON report. `--mode runtime` reproduces current
OpenYAMM suffix selection; `--mode complete` checks the intended full convention. `--character-ids` can validate exact
portraits instead of only one representative per doll type. For example:

```sh
python3 tools/mm9_import_discovery/render_paperdoll_equipment_preview.py \
  --item-id 84 --mode complete --right-hand-weapon \
  --output /tmp/item84-paperdolls.png --report /tmp/item84-paperdolls.json
```

The fitted-art workflow is:

1. Use the original MM9 PCX as binding design input and select the closest existing fitted item separately for each
   target doll type; armor also selects both arm-pose references.
2. Generate or redraw within the target fitted silhouette while preserving recognizable MM9 colors, panels, trim,
   openings, and other distinctive features. The inventory image remains upright, but it is not pasted onto the doll.
3. Derive a per-type base position against the actual target doll and record it in the body-equipment overlay.
4. Render every eligible representative in both armor poses where applicable, then render portraits whose body geometry
   needs an exception and record only those deltas in the portrait-offset contribution.
5. Promote only reviewed transparent assets whose seams, hands, head openings, feet, belt line, and occlusion match the
   doll at native resolution.

The shared renderer now selects armor `v1/v1a` through `v5/v5a`, including dwarf and alternate minotaur/troll/dwarf
poses, and belts use their fitted type-specific variants. MM9-owned `complex_item_pictures.txt` rows compose through
the mounted table-contribution contract. The loaded `complex_item_picture_offsets.txt` table is still not applied by
the renderer; add that shared support before any body item needs a portrait-specific exception.

## Import Pipeline

Implement a deterministic pipeline equivalent to:

1. Parse all `MASTERITEMLIST.csv` rows losslessly with source-row provenance.
2. Classify each row as supported, excluded, deferred, or invalid using explicit category and item rules.
3. Allocate the stable canonical/global identity from the declared MM9 range.
4. Resolve and validate the source PCX reference case-insensitively while preserving its canonical source spelling.
5. Normalize equip categories and concrete OpenYAMM skill requirements through data-owned mappings.
6. Apply the versioned balance profile and explicit item overrides.
7. Emit the OpenYAMM-layout contribution table with its MM9 extension tail.
8. Emit readable-item text/bindings, set membership, the canonical id map, import report, and deterministic
   visual-source manifest.
9. Validate every quest item's distribution policy and every equippable item's normalized tier/effect coverage.
10. Compose the contribution with the base catalog and reject all collisions or unresolved required fields.
11. Verify regeneration idempotency and ensure authored override files are not rewritten.

The importer must report every source row. Excluded categories are successful only when they are explicitly named and
counted; silently dropping a row is a failure.

## Implementation Milestones

### 1. Generic Package Contribution Foundation

- Extend world/mod manifests with package dependencies, table contributions, per-domain id ranges, and content-schema
  versions.
- Compose base plus mounted item contributions without changing the engine `items.txt` rows.
- Validate canonical ids, numeric ranges, collisions, override authority, and stable save dependencies.
- Add focused tests with synthetic packages before using MM9 data.

### 2. Lossless MM9 Item Inventory

- Parse and classify all 529 current source rows.
- Emit a complete audit report, including the explicitly excluded spell scroll, spellbook, potion, spell-runestone, and
  wand sets, the Clover reclassification, and the health-potion content mapping.
- Emit stable identities and provenance fields for every supported row.
- Verify every referenced PCX path and shared-icon relationship.
- Import and bind the underlying text for every readable item.

### 3. Core Throwing, LearnSkill, And Equipment Mapping

- Implement the data-owned skill alias and concrete subtype mappings.
- Add Throwing as a complete shared skill, populate every class/race mastery entry, and implement returning ranged
  dagger/axe attacks without ammunition.
- Add the generic `LearnSkill` action and import all existing MM9 skill-learning books.
- Map equipment slots and two-handed/off-hand rules into shared OpenYAMM behavior.
- Fail ambiguous and unsupported rows visibly.
- Cover representative Blade sword/dagger, Cudgel, Throwing dagger/axe, armor class, shield, bow, spear, jewelry,
  learning-item, and quest-item cases.

### 4. Balance Conversion

- Define the initial versioned normalization profile against MMerge/OpenYAMM item tiers.
- Assign and validate normalized `L0-L7` comparisons for every ordinary equippable item without changing preserved
  source facts.
- Add explicit artifact/relic/special overrides and implement all required named and set effects before enabling them.
- Keep imported items out of loot and shops until their distribution rows are approved.

### 5. Initial Non-AI Visual Path

- Decode or convert accepted source PCX icons deterministically.
- Load namespaced world-owned icons through the shared inventory renderer.
- Record inventory footprints and weapon/shield anchors where source-derived presentation is acceptable.
- Mark missing paper-doll variants explicitly rather than borrowing unrelated base assets.

### 6. Runtime And Save Integration

- Use the composed catalog in inventory, equipment, shops, chests, world pickups, dialogue item operations, debug tools,
  and save/load.
- Keep definitions valid across cross-world travel.
- Verify missing-package and incompatible-mapping save failures are specific and recoverable through an explicit content
  installation or migration, not silent fallback.

### 7. Content Enablement

- Enable deterministic dialogue, map, event, and container placement for quest items without adding them to procedural
  item pools.
- Expand to approved equipment families.
- Add explicit shop, treasure, chest, monster-drop, or authored-map distribution only after each item family passes its
  balance and visual gates.

## Verification Gates

Completion requires focused automated coverage proving:

- the engine `assets_dev/engine/data_tables/items.txt` contents remain unchanged by MM9 regeneration;
- base-only loading produces the same item catalog and ids as before this feature;
- the MM9 package contributes only ids in its declared range;
- contribution order does not change canonical or numeric ids;
- overlapping ranges, duplicate ids, duplicate canonical ids, and undeclared overrides fail deterministically;
- all 529 current source rows are reported exactly once as imported, excluded, deferred, or invalid;
- MM9 spell scrolls, spellbooks, potions, spell-casting runestones, and wands are not imported as MM9 runtime
  definitions;
- the known MM9 health-potion content reference resolves explicitly to an existing OpenYAMM health potion, Clover is
  imported as miscellaneous rather than potion content, and potion-like quest tokens remain quest items;
- every supported row preserves its raw id, source skill, source equip type, source icon path, and source values;
- every supported equippable item resolves to a valid shared OpenYAMM skill, including Throwing, and equipment slot;
- ambiguous skills and subtypes fail generation instead of falling back;
- Throwing is represented in saves, UI, trainers, class/race caps, equipment checks, attack/damage/recovery formulas,
  and returning projectiles, with Assassin, Ninja, and Minotaur Lord Grandmaster caps covered explicitly;
- every existing MM9 skill-learning item resolves to a supported skill/group, teaches only when permitted, and is not
  consumed on a failed learn operation;
- normalized values for every ordinary and unique equippable item are reproducible, fit their audited `L0-L7`
  comparison or unique override, and identify their balance rule/override;
- every artifact/relic effect and equipment-set threshold has explicit shared runtime behavior and equip/save tests;
- every readable item has a stable text binding and its underlying MM9 text is available through the shared readable
  item interaction;
- every quest item has normalized value `0`, cannot enter random/shop/procedural pools, and can be obtained only
  through an audited deterministic content source;
- every enabled runtime item has an accepted world-owned icon and no unrelated base-icon fallback;
- dialogue item grants/checks/removals use the canonical raw-to-global mapping;
- inventory, equipment, cross-world travel, and save/load preserve exact MM9 item identities; and
- loading a save without the required MM9 package or mapping reports a specific error without deleting or replacing
  item state.

## Completion Standard

This goal is complete when supported MM9 items behave as ordinary shared OpenYAMM items while their definitions and
assets remain owned by the mounted MM9 package, the base MMerge assets remain untouched, all ids are stable and
collision-checked, source provenance remains reproducible, excluded MM9 consumable/spell/wand categories cannot leak
into the runtime catalog, Throwing and LearnSkill are complete shared engine features, readable and quest content obeys
its authored access rules, and no MM9-specific parallel inventory or skill runtime exists.

Final AI-generated OpenYAMM-compatible item art and generic mod-defined skills are not completion requirements. They
remain explicit future goals rather than partially implemented behavior hidden inside this import.
