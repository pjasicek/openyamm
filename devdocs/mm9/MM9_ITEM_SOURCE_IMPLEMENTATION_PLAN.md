# MM9 Item-Source Implementation Plan

Status: core runtime and focused persistent mechanisms implemented; full-content regeneration remains gated by
explicit canonical mappings for excluded MM9 item families.

## Current Implementation Status

The shared semantic-import foundation is implemented:

- `mm9_item_sources.py` classifies all 68 audited placed pickups, 163 chests, four authored treasure bags, 77 bone
  piles, 22 destructible treasure-bag spawns, and 1,911 authored `GiveTreasure=true` actors;
- ODM and BLV exporters consume that shared manifest, emit the typed scene sections, and exclude only the exact 68
  pickup plus four authored-bag ABC instances from baked geometry;
- indoor and outdoor scene loaders parse the same shared C++ item-source schema;
- simple QBit/item availability has a shared gameplay evaluator, including the declarative Drangheim
  Plow/Herbs/Dolly policies;
- indoor and outdoor semantic pickups use one transactional action implementation, materialize as the normal shared
  billboard item representation, re-evaluate QBit/item visibility, and persist stable semantic source ids;
- typed chests and authored treasure bags synthesize ordinary chest records and therefore reuse the existing
  first-open materialization, trap resolution, transfer view, and save behavior; authored bags are billboards removed
  when depleted and never enter the bone-pile disease path;
- all 22 destructible bag definitions bind the retained source prop faces, create a dense shared loot container and
  bag billboard only when triggered, then hide/disable the source prop; indoor projectile-trigger faces and outdoor
  party-projectile face collisions both reach this path, while context activation remains available as a fallback;
- bone piles use a separate shared one-shot searchable-prop operation with the native strict disease comparison,
  direct single-item award, retained visual, and persistent searched source ids;
- ODM export and the BLV compiler preserve retained chest/bone-pile face groups, bind their faces to stable
  source-object event ids, and generated Lua routes those ids to `OpenChest` or `SearchLootProp`; generation rejects
  duplicate interaction event ids;
- actor procedural-death-loot overrides reach the shared corpse-loot path and persist in save version 75;
- semantic source state and the MM9 genie-lamp timed primary-stat reward now persist through save version 79; and
- exceptional placed pickups now route through generated `30000 + source_object_index` map events in both world
  runtimes; the audited callback compiler preserves alternate QBit branches, multi-item grants, experience, the Kluso
  alarm, and explicit source-id consumption rather than assuming every successful event removes its billboard;
- loot-container presentation names now resolve through the shared `ChestTable`; `mm9_chest` and
  `mm9_treasure_bag` registry rows select distinct existing placeholder layouts without branching the HUD renderer;
  and
- all 33 retained item-mechanism interactions are imported: 25 visible/stateful model nodes and eight controller
  bindings. Generated handlers cover the Lich Lab burner/cookpot, Thjorad broken/repaired slag extractor, Verhoffin
  capstone pedestal/socket, all six Ta'Sar tables and 20 staged books, and the 1000 Terrors genie lamp. Alternate
  static ABC/skin pairs are baked at the source transform as hidden BModel variants and switched through shared
  source-id state/variant operations;
- generated callback bindings preserve Crona Kiga's mummy wake-up, the accountant proximity/hostility reaction,
  Golden Honk faction hostility, Thjorad's monk-hostility gate, and QBit-locked Yanmir/Honk mechanism events through
  narrow shared actor-state queries and normal generated mechanism handlers; and
- importer and runtime-schema tests enforce the shipped native-source counts, the bone-pile/treasure-bag split, and
  the complete persistent-handler inventory.

`MM9_ITEM_SOURCE_AUDIT.md` is generated from all original DAT files and records the per-map and total census. The
two world-owned 460x344 MM9 container backgrounds are generated, provenance-recorded, and enabled by their
data-driven `ChestTable` rows. The Honk secret-door letter-button sequence is map-mechanism behavior rather than
item-source behavior; the accountant key supplies its native QBit and actor reaction, while the broader puzzle
controller remains owned by the MM9 mechanism importer.

MM9 raw item 347, `Eye of the Storm`, is explicitly mapped to the shared Implosion spellbook (item 419). This keeps
the Verhoffin-book interaction functional without importing MM9's Magic-family item definitions.

Boot Camp's six authored tutorial scroll pickups use reviewed mappings to the closest shared spell scrolls: Chain
Lightning (511) to Lightning Bolt (317), Eye of Leggib (523) to Wizard Eye (311), Magic Mine (532) to Fire Spike
(306), Sparks (547) to Sparks (314), Spell Reaver (548) to Dispel Magic (379), and Wrath of Bugs (555) to Slow (334).
The importer records the original MM9 ids and the replacement engine ids while preserving the authored positions.

Full generation is intentionally gated by 24 unresolved raw item ids in the genie-lamp source:
`254, 318, 319, 320, 327, 332, 333, 334, 335, 346, 349, 350, 415, 420, 421, 422, 510, 518, 519, 530, 538, 552,
553, 554`. They are excluded MM9 `Magic` pseudo-items exposed by the genie-lamp random pool. Wizard's Lab raw item
386 remains in the audit as a reviewed non-blocking unsupported pickup because it is absent from the shipped item
table; source object 592 remains normal baked geometry and no replacement identity is fabricated.
`MM9_ITEM_ADDON_INTEGRATION_GOAL.md` requires explicit mappings to existing OpenYAMM items for those excluded
families; the importer reports every affected reference instead of allowing raw-id collisions or silently dropping a
source.

This plan turns the classification in `MM9_PICKABLE_ITEM_CLASSIFICATION.md` into generated OpenYAMM content. It covers
all six agreed categories without adding an MM9 SCR virtual machine or a second inventory/loot runtime.

## Decisions

1. Fixed placed pickup -> shared billboard `WorldItem`.
2. Quest-gated placed pickup -> shared billboard `WorldItem` plus declarative conditions and actions.
3. `TreasureChest` and `TreasureBag` -> one shared loot-container runtime and the existing chest inventory view;
   `BonePile` -> a retained one-shot searchable prop that directly awards at most one generated item and may disease
   the active character.
4. Actor `GiveTreasure` -> per-actor enablement of the shared MM6-MM8 monster/corpse loot profile.
5. NPC, minigame, or controller reward -> direct event award; no world object.
6. Converter, socket, staged object, or model-changing object -> retained persistent model/decoration plus focused
   generated Lua or an explicit authored overlay.

The DAT-to-map importer owns classification and conversion. The ODM/BLV binary remains geometry only. Runtime gameplay
definitions belong in generated scene YAML; map interaction routing belongs in generated Lua. Import diagnostics may
repeat data for auditing, but they are not runtime authorities.

```text
MM9 DAT objects + bound SCR + MM9 item-id map
                    |
                    v
          narrow semantic importer
                    |
          +---------+----------+
          |                    |
          v                    v
  ODM/BLV geometry       generated scene YAML
  - retained models      - placed WorldItems
  - no WI/QWI ABC        - loot containers
    instances            - actor loot flags
  - retained IP/BP       - searchable loot props
    models               - model-state bindings
          |                    |
          +---------+----------+
                    v
             generated map Lua
             - face -> container
             - direct awards
             - stateful IP logic
```

## Source Of Truth And Generation Boundary

Add a shared Python module, tentatively `tools/mm9_import_discovery/mm9_item_sources.py`. It should consume normalized
DAT objects, the extracted SCR files, and `assets_dev/worlds/mm9/state/item_ids.yml`, and return one typed in-memory
manifest for a map.

Both `transcode_mm9_dat_to_odm.py` and `transcode_mm9_dat_to_blv.py` must use this module. `generate_mm9_events.py`
must consume the same generated semantic data rather than independently reinterpreting SCR. This prevents geometry,
scene data, and Lua from disagreeing about an object's category.

The importer must be a strict translator for the audited item-producing script families and native object classes. It
must not become a general SCR interpreter. A known binding produces one of the six typed results; an unsupported or
ambiguous reachable operation fails generation with map, source object, script, and line provenance.

Generated map Lua remains generated. Fix the semantic importer or add a clearly named `_authored.lua` overlay for an
exception; do not edit generated Lua directly.

## Proposed Runtime Scene Schema

The exact C++ names may change, but the generated scene data should express these concepts directly. Raw MM9 ids must
be translated to canonical/global runtime ids during import. Preserve raw ids only as provenance.

```yaml
world_items:
  - source_id: "mm9:drangheim:object:26"
    source_object_index: 26
    item_id: 10371
    position: {x: 0, y: 0, z: 0}
    original_model: "models/props/farmerplow.abc"
    original_skin: "skins/props/farmerplow.dtx"
    required_qbits: [90128]
    forbidden_qbits: [90130]
    required_items: []
    grant_items: [{item_id: 10371, quantity: 1}]
    take_items: []
    set_qbits: [90130]
    clear_qbits: []
    consume_on_success: true

loot_containers:
  - container_id: 0
    source_id: "mm9:drangheim:object:19"
    source_object_index: 19
    kind: "chest"
    presentation: "mm9_chest"
    world_visual: {kind: "bmodel", bmodel_name: "MM9_chest_19_TreasureChest0"}
    random_treasure_level: 3
    gold_only: false
    fixed_items: []
    remove_when_empty: false

searchable_loot_props:
  - source_id: "mm9:drangheim:object:192"
    source_object_index: 192
    kind: "bone_pile"
    world_visual: {kind: "model", model_name: "BonePile2"}
    random_treasure_level: 1
    loot_rolls: 1
    hazard: {condition: "disease", chance: 50, severity: "mm9_native_fixed"}
    source_disease_power: 0
    keep_visual_after_search: true

actor_loot_overrides:
  - source_object_index: 42
    procedural_death_loot: true

persistent_item_mechanisms:
  - source_id: "mm9:thjoradmine:object:1464"
    source_object_index: 1464
    handler: "slag_extractor"
    grant_items: [{item_id: 10398, quantity: 1}]
    model_variants: ["models/PickUpItems/Quest/Machine-Part_Whole.ABC"]
    model_variant_skins: ["skins/PickUpItems/Quest/MachinePart_Whole.dtx"]
```

Do not make the importer hand-maintain this YAML. It must be regenerated from DAT/SCR. The snippet only defines the
runtime contract.

Use `source_id` as persistent identity. Local `container_id` values may remain dense indices for compatibility with
`evt.OpenChest`, but the generator must sort them by original DAT object index and preserve the source id for save
validation and future migration.

## 1. Fixed Placed Pickups

For every classified `WI`:

- emit a shared WorldItem definition at the converted DAT position;
- translate the raw MM9 item id through `item_ids.yml`;
- use the imported item's MM9-owned ground-object mapping from `items.txt` to choose the billboard sprite;
- preserve source object index, model, skin, script, parameters, and source position as provenance; and
- persist removal after successful pickup through the normal map WorldItem save state.

The item importer gives every imported MM9 quest or miscellaneous item a stable dedicated ObjectId and sprite-frame
id. It reuses that item's transparent MM9 inventory art as its ground billboard, which preserves the original object
silhouette instead of substituting an unrelated MM6-MM8 family. The generated contract is:

- `data_tables/object_descriptors.txt`: world-owned object descriptors;
- `rendering/sprite_frame_data_world_items.yml`: world-owned sprite-frame contribution;
- `sprites/mm9wiNNNN.png`: ground billboard textures; and
- `state/world_item_sprite_manifest.yml`: exhaustive source-to-item-to-object-to-sprite audit.

The current MM9 source classifies 173 imported quest/miscellaneous items across 49 source visual families. Each item
keeps its own ObjectId even when several items share identical artwork, so a later per-item visual replacement does not
require an id migration. Ordinary equipment continues to use the compatible shared MM6-MM8 ground-object families.

The converter must skip baking the exact ABC instance classified as `WI`. It must not globally suppress that ABC
asset: another non-pickup instance may still need the same model.

The shared WorldItem pickup path remains responsible for inventory-first, held-item fallback, gold handling, inspect,
collision, and save/load. Do not reproduce those rules in MM9 Lua.

## 2. Quest-Gated Placed Pickups

For every classified `QWI`, emit the same billboard representation plus a declarative interaction policy:

- required and forbidden global QBits;
- required inventory items;
- items granted and consumed;
- QBits set and cleared;
- optional focused event callback; and
- whether the object is consumed after successful completion.

Raw MM9 quest keys must use the established mapping `90000 + raw_key`. The semantic output should contain full-width
global QBits, not ambiguous raw integers.

The shared runtime should evaluate availability:

- when the map is initialized or restored;
- after a party/QBit/item event transaction changes relevant state; and
- immediately before rendering, picking, and activating the item as a safety check.

This replaces handwritten `OnLoad` loops. An unavailable `QWI` is neither rendered, pickable, nor collidable. A failed
condition must not consume the item. On successful pickup, actions execute in source order and the resulting state is
saved. Multi-item examples such as the real Verhoffin book use the action list rather than pretending the billboard
contains only one ordinary item.

The converter skips the original `QWI` ABC instance exactly as for `WI`. Plow, Herbs, Dolly, Honk, keys, books, and
similar carried/disappearing objects do not need facet visibility manipulation after conversion.

Add shared policy evaluation beside `GameplayWorldItemInteraction`; call it from both indoor and outdoor WorldItem
activation paths. Do not implement separate MM9 pickup rules in `IndoorGameView` or `OutdoorGameView`.

## 3. Chests, Treasure Bags, And Searchable Bone Piles

### Recovered Native Split

Do not group `BonePile` with the two `TreasureBase` classes:

- `TreasureBag -> TreasureBase -> Prop` inherits the complete `TreasureBase` USE, treasure-list, gold, trap, and
  save/load flow. Its only meaningful native overrides are destruction and model setup. It is therefore a real loot
  container, not a disease-free bone pile.
- The four authored bags use `Random`; two are treasure-level-4 bags and two are `GoldOnly`. Dynamically spawned bags
  use `AIDrop` and can carry `TreasureType0_7`, `TreasureLevel`, `Gold`, and a fixed `Item1`. A bag payload can
  therefore contain multiple generated/fixed entries and must use a transfer view.
- `BonePile -> Prop` has a separate native USE handler. It owns `TreasureLevel`, `DiseaseChance`, and `DiseasePower`,
  sets a serialized searched flag, performs one disease roll, calls the item generator once, and directly awards the
  returned item. It never creates a treasure list or sends the treasure-menu message.

This distinction is an importer invariant. A future DAT class with the same fields is not automatically a bone pile or
container; classification follows the recovered native class behavior.

### Shared Chest And Treasure-Bag Mechanics

Refactor the existing chest implementation into a shared loot-container concept while retaining the current chest
view and item-transfer controls. A container has:

- stable source identity and local container id;
- kind: chest or treasure bag;
- presentation profile;
- fixed items, gold, random treasure level, treasure type, `AIDrop`, and gold-only option;
- lock/trap/opened/emptied state where applicable; and
- world visual binding and `remove_when_empty` behavior.

The existing `buildMaterializedChestView`, item grid placement, `ItemGenerator`, inventory transfer, cached materialized
view, and save behavior should remain the mechanical core. Generalize names only where they genuinely prevent use by
treasure bags. Do not create a second loot generator.

The agreed compatibility behavior is intentional: MM9 random treasure levels feed the shared MM6-MM8 item generator.
Authored fixed MM9 items remain exact and are translated through `item_ids.yml`.

Materialize random contents only on first open, using the existing deterministic map/session/container seed model.
Cache and save the materialized contents so reopening cannot reroll them. Fixed `Item1`-`Item5` payloads must be
positive canonical item records; random tiers may use the existing typed/random record path. Do not expose the raw
IEEE-754 bit-pattern workaround to runtime code.

Honor `ShouldRepopulate` through the existing map-repopulation lifecycle. The four authored bags have it enabled, so
their one-shot/depleted state is persistent within the current map lifetime but is reset by an actual map repopulation.
Spawned bags inherit the lifecycle of their spawning object/event rather than being emitted at map load.

### Searchable Bone-Pile Mechanics

Implement bone piles through a shared `searchable_loot_prop` gameplay path, similar in shape to the MM8 trash-heap
interaction but parameterized by MM9 DAT data. It is not a chest specialization and does not open any inventory view.

On first use, in original order:

1. mark the bone pile searched;
2. roll `1..100 < DiseaseChance` against the active character;
3. request at most one item from the shared generator using `TreasureLevel`;
4. award the returned item directly through the shared party-inventory path; and
5. play the configured feedback sound/status and save the searched state.

The strict less-than comparison is native behavior: authored chance 50 behaves as 49 successful rolls out of 100 and
chance 75 as 74. All 77 shipped instances use treasure levels 0-4, disease chances 0/50/75, and source disease powers
0/1. The shipped USE handler registers and serializes `DiseasePower` but does not read it while applying the disease.
Preserve it as source provenance, but do not silently invent severity behavior from it. A separately documented parity
decision may intentionally fix this original dead property later.

After use, keep the original 3D model visible and make the interaction nonproductive. Do not remove it, turn it into a
billboard, or allocate container contents. The stable source id owns the searched flag. No per-map `OnLoad` Lua loop is
needed.

### World Representation

- Native chest: retain and bake its MM9 chest ABC. Mark its BModel faces clickable and bind them to its open event.
- Authored treasure bag: use a billboard loot-container object because its source model is in `PickupItems` and bags
  must also be spawnable dynamically.
- Destructible-spawned treasure bag: create the billboard container at destruction time, never at map load.
- Bone pile: retain its MM9 model, bind its clickable model/faces to the typed searchable-prop interaction, and keep
  that visual unchanged after it has been searched.

When a treasure bag is depleted, remove/hide its billboard according to the `TreasureBase` one-shot lifecycle. A chest
remains in the world and retains its opened state. A searched bone pile remains visible.

The 22 DAT `DestructableProp.SpawnObject -> TreasureBag` bindings should become a focused destruction hook carrying the
source treasure level and options. Ta'Sar object 806 still spawns its non-loot `Dagrell` prop and must not enter this
path.

### Event Routing

Follow the current MM6-MM8 chest flow for chests and bags:

```text
click chest BModel face or treasure-bag billboard
    -> evt.OpenChest(container_id), or a generalized evt.OpenLootContainer(container_id)
    -> shared trap/open resolution
    -> shared chest transfer view
```

For face-backed objects, assign the event at export time through `bmodel_faces.interactive_faces`. Use one generated
interaction event per DAT source object. The current `30000 + source_object_index` mechanism identity can be generalized
to all MM9 face interactions because a DAT index uniquely identifies the source object. The generator must compose
multiple behaviors on the same object and reject event-id collisions. Existing handwritten `32000+` vertical-slice
chest events should be migrated to generated source-object events.

Billboard treasure bags can open the container directly through the shared context-action hit; they do not need a
fake facet or a permanent Lua event id.

Bone piles use a separate, smaller route:

```text
click retained bone-pile model/face
    -> resolve searchable_loot_prop by stable source id
    -> shared disease roll + one ItemGenerator request + direct party award
    -> persist searched flag; keep model visible
```

If flattened BModel picking requires an event id, generated Lua may contain a one-line call to a typed shared operation
such as `evt.SearchLootProp(source_id)`. The scene record remains authoritative; do not generate the disease/item logic
into every map script.

### MM9-Specific Container Presentation

Reuse `assets_dev/engine/ui/gameplay/chest.yml` and the existing chest renderer. Two presentation rows now exist in
the global `chest_data.txt` registry:

- `mm9_chest`; and
- `mm9_treasure_bag`.

Each row selects its world-owned `mm9_chest` or `mm9_treasure_bag` background and grid offset/size through the shared
`ChestTable`. Extend `ChestEntry` with an optional icon
asset name only if separate right-side icons are desired. Keep presentation selection data-driven; do not branch the
HUD renderer on `world == mm9`.

The two world-owned 460x344 UI backgrounds live under `assets_dev/worlds/mm9/icons/`; their generation summary and
provenance are recorded alongside them. Both preserve a dark, low-detail 9x9 inventory region and are enabled only
after the referenced assets exist. Bone piles need no UI background because they never open the transfer view.

## 4. Actor `GiveTreasure`

Add a per-actor procedural-death-loot setting to `MapDeltaActor` and the runtime actor state. The MM9 actor importer
sets it from DAT `GiveTreasure`; non-MM9 actors retain their existing default behavior.

When enabled, use the actor's imported/replacement `MonsterStatsEntry::loot` and the existing shared corpse-loot
runtime. When disabled, suppress only procedural profile loot. Explicit carried items, event-added guaranteed items,
and authored death-drop table entries keep their existing semantics.

Apply the setting in the shared corpse/death-loot construction input so indoor and outdoor behavior cannot diverge.
Dynamically spawned MM9 actors must inherit the setting from their spawn definition or resolved MM9 monster profile.

The import gate must continue to report exactly 1,911 authored `GiveTreasure=true` actors. This is a coverage count,
not 1,911 generated item objects.

## 5. Direct NPC And Minigame Awards

Do not emit a WorldItem for `DA` entries. Keep NPC/dialogue awards in the existing focused RUDE/SCR compiler and call
the shared `MM9.giveItem`, `MM9.takeItem`, gold, experience, and QBit helpers.

For non-dialogue minigames and controllers, add a narrow semantic translator for only the audited reachable routines,
or use an explicit authored map overlay when the interaction cannot be represented safely. Preserve source operation
order and original repeatability checks. Missing item mappings must remain visible errors and must never grant a
colliding item.

Generated direct-award Lua should be map-local and regenerated by `generate_mm9_events.py`. It must not spawn an item
object unless the recovered source explicitly does so. The current audit found no shipped SCR path that spawns a
pickup, item-bearing prop, weapon object, or ground item.

## 6. Persistent Converters, Sockets, And Model-Changing Objects

Retain the original ABC instance for every `IP`. These objects are mechanisms or decorations, not carried inventory
items. The exporter must:

- bake the retained model and preserve source-object identity;
- mark the appropriate faces clickable and assign the generated use event;
- emit a model-state binding from source object to all BModel faces belonging to that instance;
- collect every model/skin variant referenced by reachable `SetModelFilenames` behavior; and
- emit a small generated handler or an explicit authored overlay for the state machine.

Lua should operate on an object/model group, not enumerate flattened facet ids. Add shared event operations such as
`SetOutdoorModelVisible(source_object_id, visible, solid)` and
`SetOutdoorModelVariant(source_object_id, variant_name)`. The runtime resolves the group to facets.

For a hidden and disabled model, the runtime sets both `FaceAttribute::Invisible` and
`FaceAttribute::Untouchable` on every face in the group. For visible but non-solid state, set only `Untouchable`.
Restoring a model clears only the bits owned by that model-state operation. This updates rendering, picking,
pathfinding, and collision through the existing mutable face-attribute state.

For model swaps, bake each referenced static variant at the same source transform as its own BModel group. Exactly one
variant is visible/solid. Native QBits remain the authoritative saved state and generated map-load handlers reconstruct
the selected source-id variant. This supports the broken/repaired Thjorad slag extractor without trying to turn the
machine itself into a billboard or duplicating the QBit state in a second save field.

Use the same pattern for the Verhoffin capstone socket, Ta'Sar staged textbook positions, cookpots, burners, random
dispensers, and similar retained interactions. Items entering or leaving the party remain ordinary inventory items;
only the persistent mechanism stays in world geometry.

## Save And Load

The implementation uses explicit save migrations through version 79. Persist:

- fixed WorldItem presence/removal and stable source id;
- materialized container contents, opened/emptied state, and spawned bag position;
- per-container first-open trap resolution state;
- bone-pile searched state;
- actor procedural-loot enablement where it differs from static map data; and
- the native QBits/items that drive IP visibility and selected model variants, then reconstruct face-group state on
  map load.

Static conditions/actions remain in map content and should not be duplicated into saves. On restore, resolve saved
source ids against the active map definitions and fail visibly on an incompatible generated map revision rather than
silently binding state to a different object.

## Implementation Phases

### Phase A: Semantic Import And Validation

Implemented. The strict census currently passes all 10 importer tests.

- Add the shared item-source importer and typed records.
- Translate raw MM9 item ids and QBits at generation time.
- Emit an audit report and compare it with `MM9_PICKABLE_ITEM_CLASSIFICATION.md`.
- Make regeneration fail on unsupported reachable operations, any of the 33 currently unmapped raw item ids, or
  unreviewed count changes.

### Phase B: WI And QWI Vertical Slice

Implemented for shared indoor and outdoor runtime paths.

- Extend scene schema and shared runtime WorldItem metadata.
- Stop baking selected pickup ABC instances.
- Implement fixed pickup and declarative QBit actions.
- Validate Drangheim Plow/Herbs/Dolly, Temple of Honk, and one plain `GiveTake` item indoors and outdoors.

### Phase C: Containers, Searchable Props, And UI

Implemented, including the two MM9-specific background images and data-driven presentation rows.

- Generalize chest state/view into chest and treasure-bag definitions while keeping one transfer UI.
- Import all 163 chests and four authored bags as containers.
- Import all 77 bone piles as retained `searchable_loot_prop` definitions.
- Bind chest and bone-pile BModel faces to their respective typed interactions.
- Preserve every fixed chest payload and use shared random item generation for random tiers.
- Add the direct one-roll bone-pile item/disease handler, persistent searched state, and unchanged post-search visual.
- Add bag depletion/removal, dynamic bag spawning, save/load, and the two MM9 container presentation assets.

### Phase D: Actor Loot And Direct Awards

Implemented, including the focused callback-side actor and keyed-mechanism bindings.

- Import `GiveTreasure` into actor state and route it through shared corpse loot.
- Verify true/false instances of the same monster type do not leak policy to one another.
- Finish focused direct-award generation and validate NPC/minigame idempotence.

### Phase E: Persistent IP Objects

Implemented for all 33 audited bindings, including real alternate-model baking and generated map-load restoration.

- Add BModel face-group visibility/solidity and variant APIs.
- Generate focused handlers for converters, sockets, and staged positions.
- Validate slag extractor repair/model swap, Verhoffin capstone placement, Lich Lab conversion, and Ta'Sar textbook
  movement across save/load.

### Phase F: Full Regeneration Gate

Pending the explicit item mappings above. Focused real-DAT transcodes for Thjorad Mine and Verhoffin Ruins pass; the
strict gate correctly refuses maps whose reachable sources still contain an unmapped item.

- Regenerate all 45 maps and both development/editor copies.
- Remove superseded handwritten vertical-slice chest definitions only after generated equivalents pass.
- Run focused unit tests, headless interaction tests, save roundtrips, and the MM9 active-map gate.

## Required Verification

Importer tests must assert:

- 45 maps are present;
- 68 fixed one-shot world pickups are emitted and their exact ABC instances are absent from BModels;
- 25 stateful/reusable model nodes and eight cooperating controller objects remain model-backed/bound (33 persistent
  interactions total);
- the two known `GiveItem` false positives do not become pickups;
- 163 chests, 77 bone piles, four authored bags, and 22 destructible bag spawns are represented;
- all nonzero fixed chest/bag item slots translate to the expected canonical MM9 items;
- exactly 1,911 authored actors have procedural death loot enabled;
- no audited SCR `Spawn`/`Spawn2` creates a ground item;
- every generated interaction event id is unique within its map; and
- every runtime item id resolves to an imported definition and renderable ground object.

Runtime tests must cover:

- ordinary pickup, inventory-full behavior, inspect, and persistent removal;
- QBit-gated show/hide, pickup actions, multiple grants, and no repeat grant;
- chest first-open materialization and stable reopen results;
- fixed unique chest payloads;
- bone-pile direct single-item award, native disease comparison, no transfer UI, no repeat grant, and retained model;
- authored and destructible-spawned treasure bags with transfer UI, multi-entry/fixed/gold payloads, and no disease;
- `GiveTreasure` enabled and disabled on otherwise identical actors;
- direct award source order and save persistence;
- IP model hide/show, collision/picking changes, variant swap, and save restoration; and
- parity of shared behavior in both indoor and outdoor runtimes.

## Completion Standard

This work is complete when the full 45-map regeneration produces no unclassified item-producing binding, every
acquirable authored MM9 item source has one runtime representation, procedural sources do not reroll after save/load,
and the generated audit still accounts for the 83 quest-classified data-only/unreferenced item definitions without
inventing locations for them.
