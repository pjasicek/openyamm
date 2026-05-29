# PoE-Like ARPG Mode Design Plan

## Goal

Explore and eventually implement an optional action RPG presentation and rules layer for OpenYAMM:

- isometric or high three-quarter camera;
- one visible player character represented initially as a 2D billboard;
- click-to-move ground navigation;
- LMB/RMB plus keyboard action slots such as `Q`, `W`, `E`, `R`, `T`, with optional modifier variants;
- real-time monster killing, loot pickup, potion use, spell use, and aura maintenance;
- higher monster density and faster combat pacing than the original Might and Magic loop;
- story, maps, quests, NPCs, trainers, shops, houses, dialogue, and world progression remain recognizable and usable.

This document is a pickup point for later work. It is intentionally a design and implementation plan, not an active
instruction to start rewriting systems.

## Design Principle

OpenYAMM remains the engine. The ARPG mode is a gameplay/control/camera/presentation mode layered onto the existing
world, party, data, event, and save systems.

Do not make a separate Diablo-like engine inside the repository. The first implementation should prove that the
existing runtime can support an ARPG-style player loop while still preserving the Might and Magic content model.

## Non-Goals

- Do not remove first-person/classic gameplay.
- Do not delete party support. Treat ARPG mode as single-active-character or one-member-party first.
- Do not hardcode a new campaign fork for MM6/MM7/MM8.
- Do not duplicate map loaders, item loaders, spell tables, trainer systems, house systems, or quest systems.
- Do not directly edit generated Lua event files.
- Do not make broad compatibility fallbacks that hide stale data. Add explicit data, migration, or mode-aware rules.

## Current OpenYAMM Shape

Useful existing systems:

- `GameSession` owns persistent gameplay state and can synchronize active map runtime state.
- `Party` owns characters, inventory, buffs, conditions, gold, food, QBits, awards, and timed states.
- Indoor and outdoor runtimes own authoritative map movement, collision, actor state, projectiles, chests, corpses,
  events, and map transitions.
- `GameplayInputFrame` already carries keyboard, mouse buttons, cursor position, wheel delta, and action states.
- `GameplayActorAiSystem` and world runtimes already drive monster behavior, hostility, pursuit, attacks, spells,
  corpses, drops, and blood/fx.
- `GameplayProjectileService`, `GameplaySpellService`, and `GameplayCombatController` already encode much of the
  combat/spell behavior.
- `game/pathfinding/*` and indoor/outdoor path builders already provide a native pathfinding direction for actors.
- Existing potion tables, potion mixing, spell tables, buffs, inventory, shops, trainers, and dialogue are already
  global/base content in the MMerge-style architecture.

Important mismatch:

- The player is currently a first-person party, not a visible actor.
- Movement is velocity/input based, not destination/path based.
- Interaction is crosshair or cursor target based, not top-down target picking.
- UI assumes party portraits and MM hotkeys rather than an action bar.
- Monsters and maps are tuned for a small party moving through first-person spaces, not high-density ARPG packs.

## Target User Experience

The player selects or creates one main character and enters the normal world/story. The camera follows from an
isometric angle. The player clicks on the ground to move, clicks monsters to attack, clicks loot to pick it up, and uses
bound skills from an action bar.

The player still talks to NPCs, uses trainers, enters houses, completes quests, travels between maps, opens chests,
uses shops, reads story text, and progresses through the original campaign structure.

The combat loop changes:

- move through maps with mouse clicks;
- fight larger monster packs;
- use active skills and attacks from the bar;
- maintain aura buffs that reserve mana;
- drink health, mana, and utility potions;
- pick up item drops and crafting/currency orbs;
- improve equipment through drops, shops, trainers, and crafting.

## Runtime Mode Model

Add an explicit gameplay presentation/control mode:

```text
GameplayMode::ClassicFirstPerson
GameplayMode::ModernFirstPerson
GameplayMode::ArpgIsometric
```

This can live near the existing control scheme/settings work, but should not be treated as only an input binding
variant. ARPG mode affects camera, player representation, targeting, interaction, HUD, combat activation, movement, and
possibly spawn tuning.

Persist the selected mode in settings and save metadata:

- settings: preferred default mode;
- save: mode used by the save, plus enough compatibility metadata to restore UI/control state.

The mode should be switchable during development, but the first playable prototype can restrict switching to map load or
main menu if that avoids unsafe runtime transitions.

## Player Representation

### First Implementation

Represent the player as:

- authoritative position: existing party movement state;
- visible presentation: a player billboard rendered at the party position;
- stats/inventory/spells: the active `Character` inside `Party`;
- world interactions: still owned by active world runtime and event systems.

This avoids creating a separate player actor type that duplicates party ownership.

### One-Member Party

For the first implementation, use a party with exactly one member in ARPG mode:

- character creation should allow or force one member;
- existing trainers, quests, awards, conditions, buffs, inventory, gold, and spell knowledge continue to work;
- existing party-wide mechanics can apply to the one-member party without special casing everything.

Later, the mode can support companions, mercenaries, or retained inactive party members, but those are not needed for the
first vertical slice.

### Billboard Character

Initial player rendering should use 2D billboard assets:

- idle, run, attack, cast, hit, and death states;
- directional facings if available, otherwise camera-facing billboard as a prototype;
- scale tied to existing actor/world units;
- simple shadow/decal under the player for readability.

A later 3D model can replace the billboard without changing the authoritative player state if the renderer exposes a
small `PlayerAvatarRenderer` interface.

## Camera

### Target Camera

Use a high three-quarter camera:

- fixed yaw or rotatable yaw;
- fixed pitch, likely 45-60 degrees downward;
- orthographic projection for strongest ARPG readability, or narrow-FOV perspective if orthographic causes too much
  renderer friction;
- smooth follow on party/player position;
- zoom levels controlled by mouse wheel or settings.

Recommended prototype:

- outdoor-only first;
- fixed yaw and fixed pitch;
- perspective projection if it is faster to integrate;
- add orthographic only after picking/rendering are stable.

### Indoor Concerns

Indoor maps are harder because:

- ceilings and upper floors can hide the player;
- portal visibility and sector rendering were built for first-person camera rays;
- walls may block view in ways that need cutaway/fade rules;
- ground picking must respect indoor face/sector geometry.

Indoor ARPG support should come after outdoor proof. Possible solutions:

- hide ceilings above the player sector;
- fade walls between camera and player;
- render only visible/current sector plus portal-connected sectors;
- author ARPG-friendly camera masks or cutaway volumes for problem maps;
- allow selected indoor dungeons to remain first-person until ARPG indoor support is mature.

## Mouse Picking And Targeting

ARPG mode needs top-down target queries:

- screen point to world ray;
- raycast against terrain/floor faces for movement destinations;
- raycast or projected hit tests against actors for attack targets;
- raycast or projected hit tests against loot, decorations, doors, chests, houses, NPCs, and event faces;
- prioritization rules when targets overlap.

Target priority should be deterministic:

1. active modal UI;
2. hovered loot label or held item interaction;
3. hostile actor under cursor;
4. interactive NPC/decoration/chest/door/event target;
5. ground movement destination.

The cursor should communicate target type:

- move;
- attack;
- talk/interact;
- loot;
- blocked/invalid;
- area-target skill.

## Click-To-Move

### Destination Movement

Clicking valid ground sets a movement destination. The player follows a path to the destination until:

- destination reached;
- another command replaces it;
- movement is blocked and repath fails;
- skill activation interrupts movement;
- player opens modal interaction;
- player dies or is otherwise immobilized.

The first implementation can move directly toward destination if the path is directly reachable. Full pathfinding should
be added before enabling dense dungeons or complex outdoor obstacles.

### Pathfinding

Reuse the native pathfinding design:

- `PathMap` for static map path queries;
- indoor/outdoor path builders for map geometry;
- `ActorPathRuntime` concepts for waypoint following and repath cooldowns;
- movement controllers remain authoritative for collision and floor resolution.

Add a player-specific path following layer rather than routing player movement through monster AI:

```text
ArpgPlayerMoveController
  destination
  current path
  waypoint index
  repath timers
  stuck detection
  desired velocity output
```

Then feed desired velocity into:

- `OutdoorPartyRuntime::update(...)` outdoors;
- `IndoorPartyRuntime::update(...)` indoors.

### Movement Feel

Needed for ARPG feel:

- immediate click response;
- small stopping radius;
- no first-person turning delay;
- path smoothing where safe;
- optional attack-move behavior;
- hold LMB to continuously update destination;
- shift/control modifier to stand still while attacking or casting.

## Input Bindings

Default ARPG bindings:

```text
LMB       Move / interact / default attack on target
RMB       Bound skill slot
Q         Skill slot 1
W         Skill slot 2
E         Skill slot 3
R         Skill slot 4
T         Skill slot 5
1-5       Potion slots
Ctrl      Modifier for alternate skill bar or force stand still
Shift     Force stand still, depending on final binding choice
Space     Pick up nearby loot or interact, optional
Tab       Map overlay
I         Inventory
C         Character
S         Skills/spells
Esc       Menu/cancel
```

The exact modifier choice should be data-driven. `Ctrl` was suggested, but `Shift` is common for force-stand-still in
ARPGs. The implementation can support both and let settings decide.

Required binding model:

- keyboard keys;
- mouse buttons;
- modifier-aware bindings;
- slots rather than hardcoded spell names;
- per-character action bar assignment saved in `Party` or character state.

## Action Bar

The action bar should be an explicit runtime/UI model:

```text
ActionBar
  slots:
    LMB
    RMB
    Q
    W
    E
    R
    T
    Ctrl+LMB
    Ctrl+RMB
    Ctrl+Q
    ...
```

Each slot binds to an `ArpgAction`:

```text
None
Move
DefaultAttack
Spell(spell id)
Potion(potion slot index)
AuraToggle(spell/buff id)
ItemUse(item id or inventory reference)
Interact
Pickup
```

The action bar UI should show:

- icon;
- key label;
- cooldown overlay;
- resource cost or reservation warning;
- disabled state;
- charges for potions or consumables;
- aura active state.

Use existing spell, item, and buff icons where possible. New ARPG-only icons belong under `assets_dev/engine/` unless
world-specific.

## Active Skills

Active skills can initially map to existing spells and attacks:

- melee attack;
- bow/ranged attack;
- fire bolt or fire projectile;
- area damage spell;
- healing spell;
- curse/debuff;
- movement utility if available later.

Long-term, define an ARPG skill descriptor table:

```text
id
display name
icon
required skill/school/class
activation type
targeting type
resource cost
cooldown
cast time / attack time
recovery
projectile/fx
damage formula
status effects
allowed bindings
```

Targeting types:

- self;
- target actor;
- ground point;
- direction;
- cone;
- line;
- area around caster;
- area at cursor;
- aura toggle.

Activation should be handled through a shared `ArpgActionService` that delegates to existing spell/combat/projectile
services where possible. Do not embed ARPG-specific spell effects directly inside UI code.

## Auras And Mana Reservation

Aura buffs reserve part of maximum mana while active.

Example aura categories:

- offensive aura: increased elemental damage or accuracy;
- defensive aura: armor/resistance/avoidance;
- utility aura: movement speed, detection, loot highlighting, regeneration;
- party-like aura: existing party buffs adapted to one-character mode.

Reservation model:

```text
reservedManaFlat
reservedManaPercent
activeAuraIds
availableMana = maxMana - reservedMana - spentMana
```

Rules:

- activating an aura fails if available mana would drop below zero;
- reserved mana reduces usable mana but should not damage current mana unexpectedly;
- deactivating an aura restores reservation capacity, not spent mana;
- aura state must save/load cleanly;
- trainer/spell progression can unlock stronger aura versions;
- existing timed party buffs can remain timed buffs unless explicitly converted to reservation auras.

Do not overload existing temporary buff duration state until the reservation lifecycle is clear. Add explicit aura state
if needed.

## Potions And Flasks

OpenYAMM already has MM-style potions and potion mixing. ARPG mode should add quick-use potion slots without destroying
that system.

Potion categories:

- health recovery;
- mana recovery;
- hybrid recovery;
- utility: speed, armor, resistance, ailment cleanse, damage boost, detection;
- special story or quest potions that preserve original behavior.

Two possible models:

### Consumable Stack Model

- Potions are normal inventory consumables.
- Pressing a potion slot consumes one item from the linked stack or inventory search.
- Simple to implement and close to existing MM behavior.

### Rechargeable Flask Model

- Potion slot holds a flask item.
- Flask has charges.
- Charges refill from monster kills, rest, fountains, or shops.
- More PoE-like and better for ARPG pacing.

Recommended path:

1. implement quick-use consumable slots using existing potions;
2. add reusable flasks later as distinct item definitions and runtime state.

Potion slot UI should show:

- item icon;
- key binding;
- remaining stack or charges;
- cooldown/recovery;
- disabled state when no item is available.

Existing alchemy/mixing should remain useful. Later, alchemy can create flask modifiers or stronger utility potions.

## Loot And Crafting Currency

The ARPG loop needs more frequent item decisions than the original MM loot loop.

### Loot Drops

Preserve existing treasure/chest/corpse behavior, then add mode-aware tuning:

- higher monster density;
- more frequent small drops;
- more gold/currency shards;
- more white/magic/rare equipment drops;
- loot labels on ground;
- click or hotkey pickup;
- loot filters later.

Avoid making all drops go straight to inventory. Ground loot readability is part of the ARPG loop.

### Crafting Orbs

Add consumable crafting currency as normal item definitions:

- transmute: normal item to magic;
- alteration: reroll magic affixes;
- augmentation: add missing magic affix;
- alchemy: normal item to rare;
- chaos: reroll rare item;
- regal: magic item to rare;
- exalt-like: add rare affix;
- scouring: remove affixes;
- quality stone: improve weapon/armor quality;
- socket/gem systems only if a later design explicitly adds them.

These should not be called or implemented as direct copies of any proprietary item set. Use original names, icons, and
tables.

Crafting action:

- right-click currency;
- cursor changes to crafting mode;
- click valid equipment item;
- item service validates rarity/type/level/corruption/quest restrictions;
- result is deterministic from OpenYAMM's RNG/state rules;
- consume currency only on successful application unless table says otherwise.

Add an `ItemCraftingService` rather than burying this in inventory UI.

### Itemization

Existing MM item tables can seed the first version. Long-term ARPG itemization likely needs:

- explicit item rarity tiers;
- affix pools by item class and item level;
- quality;
- level requirements;
- stat requirements;
- skill/spell modifiers;
- resistance and defense values that work in faster combat;
- loot weights per monster/map/level.

This should extend the global/base item tables under `assets_dev/engine/`, with world-local aliases only for content
that truly belongs to a world.

## Monster Density And Encounter Tuning

ARPG mode needs more monsters and faster kill pacing, but map scripts and quests must remain intact.

Options:

- mode-aware spawn multipliers on map load;
- additional spawn groups defined in world or mod overlays;
- dynamic pack generation around existing monster families;
- bolster profile tuned for one character and faster combat;
- map-specific encounter overrides for problem areas.

Recommended first pass:

- add ARPG-specific bolster/density profile;
- avoid modifying original map data;
- generate additional non-quest-critical monsters only from declared spawn groups;
- never duplicate unique/story actors unless explicitly marked safe.

Monster tuning dimensions:

- health;
- damage;
- movement speed;
- attack/cast recovery;
- aggro radius;
- pack size;
- leash range;
- XP and loot rewards;
- projectile speed and readability.

The actor AI should remain shared where possible. Add ARPG profile inputs to existing AI/combat systems rather than
forking all monster behavior.

## Combat Rules

The existing MM combat model can provide the first version, but ARPG feel needs additional concepts:

- action cooldowns;
- cast time or attack windup;
- recovery after action;
- animation lock or partial movement lock;
- hit confirmation timing;
- area hit queries;
- target prediction for projectiles;
- clearer status effects;
- death/loot timing tuned for fast play.

Add an `ArpgCombatRuntime` or `ArpgActionRuntime` that owns:

- action slot activation;
- cooldown timers;
- current cast/attack state;
- queued/repeated input behavior;
- force-stand-still behavior;
- resource payment;
- final delegation to existing combat/spell/projectile services.

Do not make UI directly mutate character HP, mana, cooldowns, or monster state.

## Interaction With Story, Trainers, And Houses

The story should remain the same unless a world/mod explicitly changes it.

Required compatibility:

- NPC dialogue still opens when clicking/talking to NPCs;
- trainers still inspect the active character and train skills/mastery;
- shops still trade with the same inventory/gold model;
- houses/guilds/temples/taverns still use the same house services;
- quest QBits, awards, autonotes, history, and map events remain global party/save state;
- map transitions, town portal, Lloyd's Beacon, boats/stables, and scripted teleports still work.

ARPG-specific UI may need wrappers:

- action bar hides or compresses when a dialogue/shop overlay is active;
- inventory remains grid-based unless redesigned later;
- character screen should work for one character without party strip assumptions;
- trainers should train the one active member.

## Inventory

Keep the existing inventory first:

- grid inventory;
- item inspect;
- equip/unequip;
- shop buy/sell;
- potion mixing;
- held item cursor;
- chest/corpse loot.

ARPG improvements can be incremental:

- ground loot labels;
- quick pickup;
- inventory search/filter;
- currency tab or currency stacking rules;
- compare equipped item;
- stash only after the core loop works.

Do not replace inventory early. Too many existing systems rely on it.

## Save/Load

Save data must cover:

- selected gameplay mode;
- one-character party shape;
- player action bar bindings;
- potion/flask slots;
- active aura reservations;
- cooldown state if cooldowns should persist across save/load;
- ground loot that has not been picked up;
- ARPG density/spawn profile state;
- any generated pack ids needed to avoid respawn duplication.

Prefer explicit versioned save fields. If old saves need migration, make the migration explicit.

## Data Tables

Likely new or extended tables:

```text
assets_dev/engine/data_tables/arpg_actions.txt
assets_dev/engine/data_tables/arpg_action_bar_defaults.txt
assets_dev/engine/data_tables/arpg_auras.txt
assets_dev/engine/data_tables/arpg_flasks.txt
assets_dev/engine/data_tables/arpg_crafting_currency.txt
assets_dev/engine/data_tables/arpg_affix_pools.txt
assets_dev/engine/data_tables/arpg_loot_profiles.txt
assets_dev/engine/data_tables/arpg_density_profiles.txt
```

Use namespaced canonical ids:

```text
arpg.action.firebolt
arpg.aura.flame_ward
arpg.flask.minor_life
arpg.currency.reforge_rare
arpg.loot_profile.mm8.out01.default
```

World-local overrides can live under `assets_dev/worlds/*` only when the content is genuinely map/world-specific.

## UI/HUD

ARPG HUD elements:

- health globe/bar;
- mana globe/bar with reserved portion shown;
- action bar;
- potion/flask bar;
- buff/aura row;
- minimap or overlay map;
- loot labels;
- target highlight/health bar;
- experience bar;
- optional quest tracker.

First UI pass can be simple and functional:

- bottom action bar;
- compact HP/mana;
- potion slots;
- hovered target name/health;
- loot labels.

The original MM HUD should remain available in first-person modes.

## Audio And FX

Reuse existing audio/fx where possible:

- spell cast sounds;
- projectile impacts;
- monster sounds;
- item pickup;
- UI click;
- potion drink;
- death sounds.

ARPG mode will likely need:

- stronger hit feedback;
- loot drop sound tiers;
- skill cooldown/failed cast feedback;
- aura loop or activation sounds;
- clearer area skill visuals.

Avoid noisy debug logs or temporary diagnostic output in final changes.

## Outdoor First, Indoor Later

Recommended order:

1. outdoor maps;
2. simple terrain picking;
3. visible player billboard;
4. click-to-move;
5. LMB attack;
6. action bar;
7. loot labels;
8. potion slots;
9. aura reservation;
10. higher density outdoor profile;
11. selected indoor maps;
12. indoor cutaway/occlusion support.

Outdoor maps are more forgiving because the camera has open space and terrain is easier to raycast/pick. Indoor support
should not block the first proof.

## Suggested Code Ownership

Possible new files/modules:

```text
game/arpg/ArpgGameplayMode.h
game/arpg/ArpgPlayerMoveController.h/.cpp
game/arpg/ArpgTargeting.h/.cpp
game/arpg/ArpgActionBar.h/.cpp
game/arpg/ArpgActionService.h/.cpp
game/arpg/ArpgActionRuntime.h/.cpp
game/arpg/ArpgAuraRuntime.h/.cpp
game/arpg/ArpgPotionSlotRuntime.h/.cpp
game/arpg/ArpgLootLabelRuntime.h/.cpp
game/arpg/ArpgCraftingService.h/.cpp
game/arpg/ArpgDensityProfile.h/.cpp
game/ui/ArpgHudRenderer.h/.cpp
game/outdoor/OutdoorArpgCameraController.h/.cpp
game/indoor/IndoorArpgCameraController.h/.cpp
```

Existing systems that should be extended rather than duplicated:

- `Party`;
- `Character`;
- `GameSession`;
- `GameplayInputFrame`;
- `GameplaySpellService`;
- `GameplayCombatController`;
- `GameplayProjectileService`;
- `GameplayActorAiSystem`;
- `OutdoorPartyRuntime`;
- `IndoorPartyRuntime`;
- item and potion services;
- save/load data structures;
- table loaders.

## Implementation Phases

### Phase 0: Feasibility Probe

Goal: prove the renderer/input/runtime can support an ARPG camera outdoors.

Deliverables:

- settings/debug toggle for ARPG outdoor camera;
- camera follows party from fixed angle;
- party/player position rendered as a simple billboard or debug marker;
- mouse ray to outdoor terrain displayed in debug overlay;
- no gameplay changes yet.

Tests/checks:

- build succeeds;
- outdoor map loads;
- camera follows party;
- terrain ray produces stable world coordinates;
- first-person modes unaffected.

### Phase 1: Click-To-Move Prototype

Goal: move the party by clicking ground outdoors.

Deliverables:

- `ArpgPlayerMoveController`;
- click sets destination;
- desired velocity feeds existing `OutdoorPartyRuntime`;
- stop at destination;
- cancel/reissue destination;
- simple blocked/stuck handling.

Tests/checks:

- unit tests for destination/waypoint controller;
- headless scenario if available for click destination movement;
- manual outdoor map smoke test.

### Phase 2: Player Avatar And Basic Combat

Goal: make the player visible and able to attack monsters from ARPG view.

Deliverables:

- player billboard renderer;
- actor picking under cursor;
- LMB attack/move/interact priority;
- simple target highlight;
- active character performs default attack against selected target;
- monster AI still attacks party/player normally.

Tests/checks:

- attack does not fire through invalid state;
- actor picking respects dead/hostile/friendly targets;
- monster death/corpse/loot behavior still works.

### Phase 3: Action Bar

Goal: bind spells and attacks to ARPG slots.

Deliverables:

- action bar data model;
- save/load action bar assignments;
- UI rendering for LMB/RMB/Q/W/E/R/T;
- activation service for default attack and selected existing spells;
- cooldown/resource display.

Tests/checks:

- action slots serialize/deserialize;
- spell activation spends mana and respects known spell/skill rules;
- first-person quick spell behavior remains unaffected.

### Phase 4: Potion Slots

Goal: quick-use health/mana/utility potions.

Deliverables:

- potion slot runtime;
- bind slots to `1-5` or action bar slots;
- consume inventory potion or linked item stack;
- cooldown/recovery;
- UI charge/stack display.

Tests/checks:

- potion use consumes correct item;
- invalid/empty slots fail without side effects;
- existing potion mixing and inventory use still pass tests.

### Phase 5: Aura Reservation

Goal: persistent toggle buffs that reserve mana.

Deliverables:

- aura descriptor table;
- aura runtime state;
- mana reservation calculation;
- action slot aura toggle;
- UI reserved mana display;
- save/load active auras.

Tests/checks:

- activation fails without enough unreserved mana;
- deactivation restores available mana;
- save/load preserves aura state;
- existing timed buffs remain correct.

### Phase 6: Loot Labels And Crafting Currency

Goal: make drops and crafting fit the ARPG loop.

Deliverables:

- ground loot labels;
- click/hotkey pickup;
- new crafting currency item definitions;
- crafting service for a small initial set of currency effects;
- item inspect shows relevant rarity/affix info.

Tests/checks:

- pickup respects inventory capacity;
- crafting validates item/currency compatibility;
- failed crafting does not consume currency unless explicitly intended;
- shops/chests/corpses still work.

### Phase 7: Density And Balance Profile

Goal: make combat pacing closer to an ARPG.

Deliverables:

- ARPG density profile;
- mode-aware additional spawn generation;
- one-character bolster profile;
- loot profile tuning;
- monster pack behavior tuning if needed.

Tests/checks:

- unique/story actors are not duplicated;
- generated monsters do not break map events;
- save/load does not duplicate generated packs;
- performance remains acceptable.

### Phase 8: Indoor Support

Goal: selected indoor maps become playable in ARPG mode.

Deliverables:

- indoor ground picking;
- indoor camera follow;
- ceiling/wall cutaway or fade rules;
- indoor click-to-move pathing;
- indoor actor/loot/interact picking.

Tests/checks:

- selected dungeon smoke tests;
- portal/sector visibility does not hide required content;
- doors/elevators/mechanisms remain usable.

## Testing Strategy

Unit tests:

- action bar binding and serialization;
- destination movement controller;
- mana reservation;
- potion slot selection/use;
- crafting validation and outcomes;
- loot filter/label priority if implemented as pure logic.

Regression tests:

- existing potion mixing;
- spell casting;
- inventory equip/use;
- party buffs;
- actor AI;
- projectile service;
- save/load;
- chest/corpse loot;
- trainer/house dialogue.

Runtime/headless tests:

- load outdoor ARPG map;
- click move to known point;
- attack known monster;
- pick up known loot;
- activate aura, save, load, confirm reservation;
- use potion under damage/mana deficit;
- transition maps with ARPG mode active.

Manual smoke tests:

- outdoor visibility/readability;
- input feel;
- cursor target priority;
- loot label readability;
- action bar usability;
- no UI overlap on common resolutions.

## Major Risks

- Indoor camera/occlusion may be the largest technical sink.
- First-person event and interaction assumptions may not map cleanly to top-down picking.
- Existing monster/projectile speeds may feel unfair from ARPG camera angles.
- High monster density may expose pathfinding, collision, and performance limits.
- Existing inventory may feel too slow for frequent ARPG loot.
- Mana reservation may conflict with current spell point restoration assumptions.
- Save compatibility needs explicit versioning to avoid corrupting classic saves.
- Balance may require far more data work than code work.

## Open Questions

- Should ARPG mode be a full campaign option at new game start, or a runtime toggle?
- Should character creation force one character, or allow inactive party members?
- Should first implementation use orthographic camera or perspective camera?
- Should utility potions be consumables, rechargeable flasks, or both?
- Should crafting currency modify existing MM items directly, or should ARPG-mode items use a separate affix model?
- How much monster density can current outdoor/indoor runtimes handle before performance work is needed?
- Should some indoor maps remain first-person until authored cutaway/camera data exists?
- Should trainers unlock ARPG skill variants, original MM skills, or both?
- Should auras be new ARPG-only mechanics or reinterpret selected existing party buffs?

## Recommended First Milestone

Build the smallest useful outdoor prototype:

```text
ARPG outdoor camera
visible player billboard/debug marker
mouse terrain picking
click-to-move
LMB attack hostile target
simple bottom action bar with default attack and one spell
```

Do not start with crafting, flasks, aura reservation, or monster density. Those systems depend on the core control loop
feeling viable.

Success criteria:

- it is possible to load an outdoor map, click around naturally, see the player, target a monster, kill it, and pick up
  loot without using first-person controls;
- first-person gameplay still works;
- no original story/event/trainer/shop systems are broken by the prototype.
