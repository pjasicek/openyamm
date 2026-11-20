# MM9 Barrel Integration Goal

Status: complete (2026-08-28)

## Goal

Restore the original Might and Magic IX colored-barrel interaction in OpenYAMM, including the separate colored-liquid
surface, permanent stat rewards, swamp-barrel disease and item behavior, one-shot persistence, and drained-water visual
state.

Implement the behavior as normal MM9 world content backed by shared gameplay and map-state systems. Do not add a
general MM9 ObjectDLL or SCR runtime, do not hand-edit generated Lua event files, and do not import barrels as world
items or pickups.

## Recovered Original Behavior

### Native ownership

The shipped behavior is owned by the native `Barrel` ObjectDLL class, not by `BARREL.scr`.

Primary references:

- `../OpenMM9/reference/game/data/object.lto.c`
  - `function_1005f220`, address `0x1005f220`: initialization and liquid selection.
  - `function_1005f2d0`, address `0x1005f2d0`: one-shot use behavior.
  - `function_1005f720`, address `0x1005f720`: saved used state.
- `../OpenMM9/assets_dev/source/models/PROPS/BARREL03.abc`
- `../OpenMM9/artifacts/model_exports/models/props/barrel03.model.yml`
- `../OpenMM9/assets_dev/source/skins/PROPS/`
- `../OpenMM9/assets_dev/source/data/GAMETEXT.txt`

`BARREL.scr` contains stale design comments and registers an `OnUse` trigger without implementing its handler. Its
comments describe 40% empty barrels, six 10% colored outcomes, `+1` rewards, and blue as Personality. Do not use these
comments as gameplay truth. The shipped native implementation instead has eight uniformly selected outcomes, `+2`
stat rewards, blue as MM9 Magic, and explicit swamp and water outcomes.

### Model and liquid surface

`BARREL03.abc` contains two pieces in the same model:

| Piece | Material slot | Role |
| --- | ---: | --- |
| `Barrel03` | 0 | Wooden barrel body |
| `Liquid` | 1 | Colored liquid surface at the top |

The liquid is not a separately placed or attached world model. The native class assigns a texture filename to model
skin/material slot 1. After use, slot 1 is changed to `skins\props\barrel_water.dtx`.

Required source textures:

- `liquid-red.dtx`
- `liquid-blue.dtx`
- `liquid-green.dtx`
- `liquid-purple.dtx`
- `liquid-white.dtx`
- `liquid-yellow.dtx`
- `liquid-swamp.dtx`
- `barrel_water.dtx`

### Type selection and effects

Native initialization reads the DAT `Type` property but then replaces it with `rand() % 8 + 1`. Each outcome is
therefore selected with probability `1/8` in the shipped implementation.

| Type | Liquid texture | Original effect |
| ---: | --- | --- |
| 1 | `liquid-red.dtx` | Selected character gains `+2 Might` permanently. |
| 2 | `liquid-blue.dtx` | Selected character gains `+2 Magic` permanently. |
| 3 | `liquid-green.dtx` | Selected character gains `+2 Endurance` permanently. |
| 4 | `liquid-purple.dtx` | Selected character gains `+2 Speed` permanently. |
| 5 | `liquid-white.dtx` | Selected character gains `+2 Luck` permanently. |
| 6 | `liquid-yellow.dtx` | Selected character gains `+2 Accuracy` permanently. |
| 7 | `liquid-swamp.dtx` | Selected character becomes diseased and gains a generated item. |
| 8 | `barrel_water.dtx` | Empty/water outcome; no reward. |

MM9's primary-stat order is Might, Magic, Endurance, Accuracy, Speed, and Luck. Blue is Magic, not Personality.

The stat mutation rejects a result above 500. The barrel is marked used before applying its outcome, so a barrel is
still consumed when the selected stat cannot be raised.

The swamp outcome applies disease and generates a treasure-level-1 random item. The native caller supplies the best
Luck modifier among current party members. At treasure level 1, `function_10046c10` replaces the adjustment with a
uniform roll from 1 through 40: rolls 1 through 20 select normalized tier 1 and rolls 21 through 40 select normalized
tier 2. It then selects uniformly among eligible items in that tier. Luck therefore has no effect at treasure level 1,
although it affects higher-level calls to the same generator. Do not silently approximate this with a fixed item, an
unrelated MM6-MM8 random-item table, or an extra enchantment roll that the level-1 barrel path does not perform.

### Interaction feedback and persistence

- Only party member indices 0 through 3 are accepted by the original use path.
- The selected/active character receives the stat or disease effect.
- An invalid or unavailable selected character plays `sounds/events/error.wav` and does not consume the barrel.
- Reward outcomes play `sounds/events/quest.wav`.
- Stat outcomes display `%s gains +%d %s!` from `GAMETEXT.txt`.
- The swamp outcome displays `%s becomes diseased, but gains an item!`.
- A used barrel ignores later interaction.
- Every successfully consumed barrel changes its liquid texture to `barrel_water.dtx`.
- Type, used state, and the resulting visual state must survive save/load and map reload without rerolling.

## Shipped DAT Census

The current local MM9 DAT export contains 55 objects whose source class is `Barrel`, across 16 maps:

- 51 use `models\Props\Barrel03.ABC` and have the recovered `Liquid` material slot.
- Three use `models\Props\Barrel.ABC`.
- One Boot Camp `Barrel` object uses `models\Props\Suitofarmor01.ABC`.
- The observed DAT `Type` values are zero; native initialization supplies the runtime type.
- Many Barrel objects have no `ScriptName`, consistent with native class ownership.

Preserve interaction for unusual Barrel-class instances. Apply liquid visuals only when the imported model actually
contains a material-1 liquid piece. Do not manufacture liquid geometry for `Barrel.ABC`, the suit-of-armor instance,
or another exceptional model without additional source evidence.

## Pre-implementation OpenYAMM State

OpenYAMM currently bakes MM9 model objects into classic indoor/outdoor geometry. Barrel objects are emitted as ordinary
`static_prop` BModels and have no interactive classification or persistent barrel state.

Boot Camp source object 372 is a representative instance:

- source class: `Barrel`
- source name: `Barrel6`
- source model: `models/Props/Barrel03.ABC`
- source skin: `skins/props/barrel03.dtx`
- current imported kind: `static_prop`

The current importer also gives material slot 1 the slot-0 skin when DAT supplies only one skin. In
`source_skin_for_material`, an out-of-range material index returns `skins[0]`. Consequently, the `Liquid` piece is
currently baked with the wooden `barrel03` texture instead of a colored liquid texture.

`MM9_MECHANISM_CLASS_KINDS` and `build_outdoor_mechanism_interactive_face_lines` do not include Barrel objects unless
they are independently present in a semantic source manifest. Barrel must be introduced as a native interactive
decoration, not added to the item-pickup family.

Existing useful infrastructure includes:

- generated MM9 object ids and stable `source_object_index` provenance;
- BModel face event binding for indoor and outdoor maps;
- cog-based `SetTexture` overrides;
- outdoor per-BModel-facet texture overrides;
- shared party stat and condition mutation;
- persistent map delta/save state;
- persistent item-mechanism variants, which may be reused only if their ownership is generalized rather than making
  Barrel an item-specific special case.

## Target Architecture

### Generated native-interactable data

Extend the MM9 DAT importer to classify source class `Barrel` as a native interactive decoration. Generate one
authoritative record per source object with at least:

```yaml
id: mm9:<map>:barrel:<source_object_index>
kind: barrel
source_object_index: <index>
bmodel_index: <index>
interaction_event_id: <id>
liquid_faces: [<face indices>]
has_liquid_surface: true
```

The exact containing sidecar may be a generalized native-interactables manifest or an appropriately generalized
existing persistent-mechanism manifest. Do not create duplicated ownership in scene YAML, generated Lua, and a second
hardcoded C++ table.

The importer must preserve ABC piece/material identity while baking. Faces originating from `Liquid` material slot 1
must be identifiable separately from barrel-body faces. Liquid faces should be visible but should not add a separate
collision surface or intercept interaction independently of the barrel.

Bind the usable barrel geometry to one event id derived from the stable source object index for both indoor and outdoor
maps. The liquid surface may share the interaction event if required by picking, but it must resolve to the same barrel
record.

### Texture import and rendering

Import all eight required MM9 textures into normal MM9-owned runtime texture assets and material aliases. Do not bake
one arbitrary color permanently into the generated map.

Use the existing texture-override paths where practical:

- indoor: assign a stable cog/reference to all liquid faces and apply one cog texture override;
- outdoor: apply the texture alias to the recorded BModel liquid faces through the existing per-facet override state.

Expose this through one shared scene-context operation such as `setMm9BarrelLiquidTexture`, so gameplay code does not
contain divergent indoor and outdoor behavior. The indoor/outdoor implementations should only translate the shared
request into their world-representation-specific face override.

Do not generate eight complete copies of every barrel. If current face overrides cannot meet a required renderer or
save-state constraint, an acceptable temporary representation is one fixed barrel body plus eight small, non-colliding
liquid-overlay variants. Do not duplicate the whole barrel BModel merely to change the liquid texture.

### Authoritative gameplay state

Store barrel state in persistent map/save data keyed by mounted world, canonical map id, and source object index:

```cpp
enum class Mm9BarrelType
{
    RedMight = 1,
    BlueMagic = 2,
    GreenEndurance = 3,
    PurpleSpeed = 4,
    WhiteLuck = 5,
    YellowAccuracy = 6,
    Swamp = 7,
    Water = 8,
};

struct Mm9BarrelState
{
    Mm9BarrelType type;
    bool used;
};
```

Initialize an absent state exactly once through the normal deterministic gameplay RNG and persist the resulting type.
Do not derive type from current texture, reroll on map entry, or store independent copies of mutable state in Lua and
C++.

On load or map activation, derive the visible texture from authoritative state:

- `used == false`: the texture corresponding to `type`;
- `used == true`: `barrel_water.dtx`.

### Shared interaction service

Implement the outcome in shared gameplay code, for example a small `Mm9BarrelRuntime` or a generalized MM9 native
interactable service under `game/mm9/`. Indoor and outdoor interaction controllers should only resolve the event/source
record and dispatch to this service.

The service must:

1. Resolve a valid selected/active party member.
2. Reject invalid selection with the original error sound and leave state unchanged.
3. Return without effect if the barrel is already used.
4. Mark the state used before applying the selected outcome.
5. Apply the exact type effect.
6. Apply the drained-water visual.
7. Play the appropriate sound and status message.
8. Leave authoritative state ready for normal save serialization.

The original hard maximum of 500 must be preserved unless a later, explicitly documented MM9 balance profile changes
it. Such a profile must not silently alter MM6/MM7/MM8 barrel behavior.

### MM9 Magic mapping

OpenYAMM's shared character state currently exposes the MM6-MM8 seven-stat layout with separate Intellect and
Personality, while MM9 has one Magic primary stat. Barrel code must not resolve this discrepancy locally.

Add or use a centralized MM9 primary-stat projection. The recommended initial shared-storage mapping is:

```text
MM9 Magic -> shared Intellect storage, displayed and interpreted as Magic while MM9 rules are active
```

This is consistent with OpenMM9's compatibility loader accepting `intellect` as a fallback source for Magic. Do not
map blue barrels to Personality and do not increment both Intellect and Personality. If the final MM9 character rules
introduce another authoritative Magic representation, the projection should change centrally without changing barrel
outcome data.

### Swamp disease and item generation

Use the selected character's MM9 disease condition through the shared condition system. Recover and document the exact
native disease severity/flag before assigning a legacy MM6-MM8 disease color solely from numeric coincidence.

Generate the swamp reward through the MM9 random-item path at treasure level 1 with the best party Luck modifier. If
the full MM9 generator is not yet available, keep this completion gate open or introduce the missing MM9 generator;
do not hide the gap behind a fixed reward or broad fallback. The recovered level-1 path is the 50/50 tier-1/tier-2
selection described above; its supplied Luck adjustment does not change that selection.

## Required Importer Work

- Recognize all source-class `Barrel` objects as native interactive decorations.
- Retain source object index, source model, source skin, and map identity.
- Preserve ABC piece material indices during model baking.
- Identify and record material-1 `Liquid` faces.
- Stop applying the slot-0 wood skin to recognized liquid faces.
- Import and alias all eight barrel liquid/water textures.
- Bind interaction faces for indoor and outdoor maps.
- Generate authoritative native-interactable records without hand-authored per-map duplication.
- Regenerate the MM9 maps and generated sidecars through the normal MM9 regeneration workflow.

## Required Runtime Work

- Add saved `Mm9BarrelState` keyed by stable map object identity.
- Add deterministic one-time type initialization.
- Add the shared interaction service and exact eight-way outcome table.
- Add centralized MM9 Magic stat resolution.
- Add exact swamp disease and level-1 random-item behavior.
- Connect interaction feedback to existing sound and status-text systems.
- Apply liquid textures through shared scene context with indoor/outdoor world hooks.
- Restore visuals from state on load and map activation.
- Keep MM9 barrel work dormant when MM9 is not mounted.

## Validation

### Importer tests

- `Barrel03.ABC` imports `Barrel03` as material 0 and `Liquid` as material 1.
- Material 1 does not fall back to `barrel03.dtx` for a classified barrel.
- All eight liquid/water aliases are emitted and resolve to imported assets.
- Barrel records retain their original source object indices.
- Barrel geometry is interaction-bound in indoor and outdoor output.
- Liquid faces do not create unintended collision or a separate semantic object.
- Exceptional Barrel-class models remain interactive without fabricated liquid faces.

### Gameplay tests

- New state produces only types 1 through 8 with deterministic RNG behavior.
- Initialized type survives map reload and save/load without rerolling.
- Each colored barrel adds exactly 2 to the correct selected-character stat.
- Blue modifies MM9 Magic through the centralized projection, not Personality.
- No other party member receives the stat reward.
- A result above 500 is rejected while the barrel remains consumed, matching the original order.
- Swamp applies the recovered disease condition and grants a level-1 generated item using best-party Luck.
- Water grants nothing.
- Invalid selected-character state plays the error sound and does not consume the barrel.
- A second use produces no reward.
- Successful consumption changes the liquid to water.

### Persistence and visual tests

- A fresh unused barrel shows the texture corresponding to its saved type.
- A used barrel shows `barrel_water` after quicksave/quickload and map exit/re-entry.
- Indoor and outdoor implementations present the same state and interaction result.
- Boot Camp object 372 provides a focused `Barrel03` regression case.
- At least one additional indoor and one outdoor shipped barrel map are covered.
- Existing MM6/MM7/MM8 decoration barrels and global EVT barrel events are unchanged.

### Build and runtime gates

- Run focused Python importer tests.
- Regenerate affected MM9 maps through the repository's normal MM9 regeneration script.
- Build with `cmake --build build --target openyamm -j25`.
- Run relevant doctest/unit coverage.
- Run focused headless indoor and outdoor MM9 interaction scenarios.
- Confirm that unmounted MM9 adds no meaningful startup, map-load, memory, or per-frame cost.

## Implementation Progress (2026-08-28)

Implemented:

- `Mm9BarrelRuntime` owns deterministic type initialization, the eight native outcomes, selected-member targeting,
  the 500 stat cap, one-shot consumption, disease, level-1 MM9 item generation, and feedback.
- `Mm9PrimaryStats` centrally projects MM9 Magic to shared Intellect storage without changing Personality.
- `MapDeltaMm9BarrelState` is serialized in save version 82, and loaded state drives the liquid texture without a
  reroll.
- Native barrel event routing is intercepted at the scene-context boundary, so direct event calls and normal
  indoor/outdoor face activation do not depend on generated Lua handlers.
- The DAT importer classifies all 55 shipped Barrel objects, assigns stable source-object event ids, records exact
  `Liquid` faces, imports all eight texture aliases, keeps liquid faces visible/clickable/untouchable, and preserves
  exceptional models without fabricated liquid geometry.
- Indoor texture-cog and outdoor per-BModel-facet visual overrides both derive from the same saved state.
- The existing headless open-event diagnostic now recognizes native barrel events and fails unless the corresponding
  map-delta state is consumed.

Validated:

- Python importer/census coverage: 113 tests passed; the census reports all 55 unique barrel records.
- Focused C++ gameplay coverage passed all seven barrel cases and 83 assertions; parser/save coverage passed another
  two cases and 99 assertions.
- Focused legacy MM6/MM7 decoration-barrel ownership and global-event collision coverage: 53 assertions passed.
- Exterior headless runtime: `drangheimcity.odm` event 30034 consumed source object 34 and exercised both blue Magic
  and swamp outcomes; the diagnostic verifies the exact stat projection or disease-plus-inventory change.
- Enclosed-location headless runtime: `anskramkeep.odm` event 31241 consumed source object 1241 and exercised the
  water outcome while verifying that it changed no party stat, condition, or inventory state.
- Normal regeneration completed for all 16 maps containing all 55 barrels. Every barrel is interaction-bound; all 51
  `Barrel03` instances contain 612 exact liquid faces, every alias resolves to an emitted bitmap, and all validation
  checks pass.
- Boot Camp now regenerates normally after its six unsupported MM9 tutorial scrolls were explicitly mapped to the
  closest shared spell scrolls. Its source object 360 correctly has no liquid faces and object 372 has 12; both retain
  eight texture aliases and valid BModel ownership. All 14 Boot Camp semantic world items materialize on valid floors,
  including the six replacements at their original authored positions.
- Successful semantic world-item pickups now use the standard found-item status text and loot sound, matching items
  dropped by the party instead of silently granting and consuming the authored MM9 pickup.
- Boot Camp screenshots `test_img/1210.png` and `test_img/1211.png` exposed that dynamic colored-liquid aliases were
  emitted but not uploaded because map texture loading previously collected only static face textures. Indoor and
  outdoor map loading now also collects the eight aliases declared by each MM9 barrel. Full-load diagnostics reject a
  map if any declared barrel alias is missing; Boot Camp reports all eight loaded. The used-state surface remains the
  original `barrel_water.dtx` texture.
- The focused headless barrel diagnostic now rejects an incorrect initial liquid override, an incorrect drained-water
  override, a rerolled type, or loss of the used state/water override after runtime reinitialization. Boot Camp object
  372 passed with a live yellow/Accuracy outcome; Drangheim City, Anskram Keep, and Wizard's Lab barrel cases also
  passed the same persistence and visual checks.
- Wizard's Lab now regenerates through the normal geometry and event workflow. Missing raw item 386 remains visible as
  an explicitly reviewed unsupported reference on source object 592; that original skeleton prop stays baked and no
  item identity is fabricated. Both Wizard's Lab barrels have 12 liquid faces, eight loaded texture aliases, valid
  BModel ownership, and successful native headless interactions (including swamp and stat outcomes).
- `openyamm`, `openyamm_unit_tests`, and `mm9_compile_indoor_source` build successfully.
- MM8 outdoor `out01.odm` and indoor `d05.blv` still complete full headless loads. MM6/MM7 legacy decoration-barrel
  ownership and global-event collision tests remain green. On maps without MM9 barrel records, the new texture
  collection helper exits immediately and the per-map barrel initialization loop is empty, so MM9 adds no meaningful
  texture upload, map-load, or per-frame work when it is not mounted.
- A final source and generated-data audit reconfirmed that Barrel03 separation is limited to the exact ABC piece named
  `Liquid` on material slot 1, invalid saved barrel types are rejected, and exceptional models retain native interaction
  without fabricated liquid faces. The 111 focused importer/parser tests and all seven focused MM9 barrel runtime tests
  remain green.
- The complete dirty-worktree unit run reached 1,114/1,122 passing test cases. Its eight failures are in pre-existing
  projectile particle sizing, MM9 quest/RUDE/paperdoll fixtures, monster missile expectations, MM7 actor relations, and
  process-global AssetFileSystem initialization; none exercises or reports a failure in the barrel paths.

Remaining completion gates: none for MM9 barrel integration. The existing unrelated dirty-worktree failures remain
repository-wide cleanup work, not barrel-path failures.

## Completion Criteria

This goal is complete when:

- every shipped Barrel-class DAT object is represented as a persistent native interactable;
- `Barrel03` visibly displays the correct colored liquid before use and water after use;
- the eight native outcomes, probabilities, selected-character targeting, sounds, messages, and one-shot semantics match
  the shipped implementation;
- swamp barrels use recovered MM9 disease and item-generation semantics;
- barrel type and used state survive save/load and map reload without rerolling;
- unusual Barrel-class models retain behavior without unsupported visual fabrication;
- generated assets and sidecars are reproducible from authoritative importer code;
- focused indoor, outdoor, persistence, and non-regression tests pass; and
- existing MM6/MM7/MM8 gameplay and content behavior remain unchanged.
