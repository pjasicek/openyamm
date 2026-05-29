# OE Hostility Handling Inventory

This document records the OpenEnroth hostility model as reference behavior and the realized deltas in OpenYAMM.
OpenEnroth is reference-only; do not copy code from it.

## Reference Model

OE does not treat actor hostility as one boolean. The runtime relation is the product of several independent fields:

- `hostile.txt` / `FactionTable`: a monster-type to monster-type relation matrix. Values are `0..4`.
- `MonsterInfo::hostilityType`: the actor's current engagement range/state, not its faction identity.
- `Actor::group`: map-authored group. If two nonzero actor groups are equal, OE treats the pair as friendly.
- `Actor::ally`: map-authored relation override. Nonzero ally replaces the actor's natural monster type for relation
  lookup.
- `ACTOR_AGGRESSOR`: persistent "enemy to party" override. OE's `ActorEnemy()` reads this bit.
- `ACTOR_HOSTILE`: derived nearby/minimap marker flag. OE recomputes this in `MakeActorAIList_*`.
- Buffs: Charm, Enslave, Berserk, Summon/Reanimate/Control Undead alter relation at runtime.
- Events: actor/group flag changes and group/ally changes can alter map-authored behavior after load.

The important consequence: "hostile to party", "hostile to another actor", "currently aware", and "shown as red on the
minimap" are different facts.

## Hostility Classes

OE names the relation values:

| Value | OE name | Meaning |
|---:|---|---|
| 0 | `HOSTILITY_FRIENDLY` | No hostility. |
| 1 | `HOSTILITY_CLOSE` | Hostile at melee/close range. |
| 2 | `HOSTILITY_SHORT` | Hostile at short range. |
| 3 | `HOSTILITY_MEDIUM` | Hostile at medium range. |
| 4 | `HOSTILITY_LONG` | Hostile at long range. |

OE has two range tables in practice:

- The static OE table lists `0, 1024, 2560, 5120, 10240`.
- The AI promotion path promotes friendly actors to `HOSTILITY_LONG` with thresholds `close => immediate`,
  `short => 1024`, `medium => 2560`, `long => 5120`.

For parity, implementation should keep values and transition semantics explicit instead of treating `> 0` as a
permanent actor state.

## OE Relation Resolution

OE's canonical relation function is `Actor::GetActorsRelation(subject, target)`:

- If both actors have the same nonzero `group`, relation is friendly.
- If the subject is berserk, relation is long hostile.
- The subject relation type is:
  - party type if enslaved or `ally == MONSTER_TYPE_9999`;
  - `ally` if `ally != MONSTER_TYPE_INVALID`;
  - otherwise natural `monsterTypeForMonsterId(monsterInfo.id)`.
- The target relation type is resolved the same way; `nullptr` means party.
- Charm against party makes the relation friendly.
- `ACTOR_AGGRESSOR` makes a non-enslaved subject long-hostile to the party.
- Out-of-range relation groups are friendly.
- Otherwise OE returns `FactionTable::relations[subjectType][targetType]`.

OE's relation matrix is asymmetric. The subject/target direction matters. This is required for cases like dragons
versus dragon hunters.

## OE AI And Minimap Use

OE's `MakeActorAIList_ODM` and `MakeActorAIList_BLV` recompute runtime flags every AI pass:

- Clear `ACTOR_FULL_AI_STATE`.
- Skip actors that cannot act.
- If an actor is in active range, clear `ACTOR_HOSTILE`.
- Set `ACTOR_HOSTILE` if `ActorEnemy()` or `GetActorsRelation(nullptr) != HOSTILITY_FRIENDLY`.
- Set party alert levels from hostile nearby actors.
- Mark active actors and select the closest actors for full AI.

OE's Wizard Eye/minimap actor rendering does not filter only hostile actors. It draws actors when they are not removed
or disabled and are either dead or `ActorNearby()`. Color is selected afterwards:

- `ACTOR_HOSTILE` => hostile color.
- dead => corpse color.
- otherwise => friendly color.

This means friendly nearby actors must still be visible as friendly markers. Hiding friendly actors because they are not
`hostileToParty` or have not "detected party" is not OE behavior.

## OE Source Inventory

Reference files inspected:

- `reference/OpenEnroth-git/src/Engine/Tables/FactionTable.cpp`
- `reference/OpenEnroth-git/src/Engine/Tables/FactionTable.h`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.h`
- `reference/OpenEnroth-git/src/Engine/Objects/ActorEnums.h`
- `reference/OpenEnroth-git/src/Engine/Objects/MonsterEnums.h`
- `reference/OpenEnroth-git/src/Engine/Objects/MonsterEnumFunctions.h`
- `reference/OpenEnroth-git/src/GUI/UI/UIGame.cpp`
- `reference/OpenEnroth-git/src/Engine/Evt/EvtInterpreter.cpp`

OpenYAMM files inspected for deltas:

- `game/tables/MonsterTable.cpp`
- `game/gameplay/GameplayActorService.cpp`
- `game/gameplay/GameplayRuntimeInterfaces.h`
- `game/outdoor/OutdoorWorldRuntime.cpp`
- `game/indoor/IndoorWorldRuntime.cpp`
- `game/events/EventRuntime.cpp`
- `assets_dev/Data/scripts/common/event_support.lua`
- `assets_dev/Data/scripts/maps/out05.lua`
- `assets_dev/Data/scripts/maps/d17.lua`
- `assets_dev/Data/games/out01.scene.yml`
- `assets_dev/Data/games/out05.scene.yml`
- `assets_dev/Data/data_tables/monster_relation_data.txt`
- `assets_dev/Data/data_tables/monster_data.txt`

## Map-Specific Inventory

### Dagger Wound Island (`out01.odm`)

Relevant base data from `monster_relation_data.txt`:

| Subject | Target | Relation | Expected behavior |
|---|---|---:|---|
| Lizardmen Male Peasant | Party | 0 | Lizardmen peasants are friendly to party by default. |
| Lizardmen Warrior | Party | 0 | Lizardmen warriors are friendly to party by default. |
| Pirate Warrior Male | Party | 3 | Pirates are hostile to party at medium range. |
| Wimpy Pirate Warrior Male | Party | 1 | Wimpy pirates are hostile to party at close range. |
| Lizardmen Peasant | Wimpy Pirate Warrior Male | 3 | Lizardmen can engage pirates. |
| Lizardmen Warrior | Wimpy Pirate Warrior Male | 4 | Lizardmen warriors can engage pirates. |
| Wimpy Pirate Warrior Male | Lizardmen Peasant | 4 | Pirates can engage lizardmen. |
| Wimpy Pirate Warrior Male | Lizardmen Warrior | 4 | Pirates can engage lizardmen warriors. |

Observed authored data:

- `out01.scene.yml` has placed lizardmen with `monster_info_id` `1..3`, and lizardman warriors with
  `monster_info_id` `5`.
- It also has placed Regnan Brigadiers with `monster_info_id` `12`.
- Spawn groups include multiple lizardman/pirate group ids. Group equality must only make same-group actors friendly;
  it must not flatten faction relations across groups.

### Garrote Gorge (`out05.odm`)

Relevant base data:

| Subject | Target | Relation | Expected behavior |
|---|---|---:|---|
| Dragon Hunter | Party | 0 | Dragon slayers are friendly to party by default. |
| Dragon | Party | 0 | Dragons are friendly to party by default. |
| Wimpy Dragon | Party | 0 | Dragon hunter pets are friendly to party by default. |
| Naga | Party | 4 | Nagas are hostile to party. |
| Dragon Hunter | Naga | 4 | Dragon slayers attack nagas. |
| Naga | Dragon Hunter | 2 | Nagas can attack dragon slayers. |
| Dragon Hunter | Dragon | 4 | Dragon slayers attack dragons. |
| Dragon | Dragon Hunter | 0 | Raw table is asymmetric; regular dragons do not necessarily initiate on dragon slayers. |
| Dragon Hunter | Wimpy Dragon | 4 before override | Base table would make dragon slayers attack dragons. |
| Wimpy Dragon | Dragon Hunter | 0 | Pet dragon direction is naturally friendly to dragon slayers. |

Observed authored direct actors:

- `out05.scene.yml` actor `0..2`: `monster_info_id = 72` / Great Wyrm, `ally = 15`.
- `out05.scene.yml` actor `3`: `monster_info_id = 45` / Dragonslayer, `group = 24`, `ally = 15`.
- Existing regression intent confirms this is special authored state: the pet dragons use `ally = 15`, which maps them
  into the Dragon Hunter relation type and prevents dragon slayers from targeting them.

Relevant map script:

- `assets_dev/Data/scripts/maps/out05.lua` on-load event sets groups `22, 23, 24` hostile when `QBit(22)` is set.
- The same event sets groups `44, 45` hostile when `QBit(21)` is set.
- These are quest-state overlays. The default state must remain party-friendly for dragon slayers and dragons, while
  nagas remain hostile by base relation.
- Acceptance should not assume regular dragons initiate combat with dragon slayers unless a runtime side effect changes
  the dragon's relation state. OE target selection checks subject-to-target relation, so `Dragon Hunter -> Dragon = 4`
  makes dragon slayers initiate, while `Dragon -> Dragon Hunter = 0` means regular dragons may only join via retaliation,
  damage side effects, or map/quest event state.

### Dragon Cave (`d17.blv`)

Relevant base data:

| Subject | Target | Relation | Expected behavior |
|---|---|---:|---|
| Dragon | Party | 0 | Dragons are friendly to party by default. |
| Wimpy Dragon | Party | 0 | Wimpy dragons are friendly to party by default. |
| Dragon Hunter | Party | 0 | Dragon hunters are friendly to party by default unless quest state overrides. |

Relevant map script:

- `assets_dev/Data/scripts/maps/d17.lua` on-load event 5:
  - If `QBit(21)` is set, it sets groups `44`, `45`, and `11` hostile, and reveals group `11`.
  - If `QBit(233)` is set and a time condition is not met, it does the same.
  - Otherwise it clears hostility for groups `44`, `45`, and `11`, hides group `11`, clears `QBit(233)`, and resets
    `MapVar(11)`.
- Event 453 also sets groups `44`, `45`, and `11` hostile and updates `MapVar(11)`.
- Therefore d17 dragons must be friendly by default. They are only made hostile by quest/map events.

Implementation caution:

- The generated Lua currently calls `evt.SetMonGroupBit(..., MonsterBits.Hostile, ...)`.
- In OE, `ACTOR_HOSTILE` is a derived marker cleared and recomputed in `MakeActorAIList_*`, while `ACTOR_AGGRESSOR`
  is the persistent "enemy to party" bit used by `GetActorsRelation(nullptr)`.
- Before fixing d17 by forcing `hostileToParty`, verify whether the event bit should alter persistent aggression,
  current hostility type, or only marker state in the MM8 data path. The acceptance tests below should expose the
  correct semantic result.

## OpenYAMM Realized Deltas

Current code already has some pieces of the model, but they are not composed like OE:

- `MonsterTable` loads `monster_relation_data.txt` and can query relation by monster type.
- `GameplayActorService::relationMonsterId(monsterId, ally)` maps `ally` to representative monster id.
- `GameplayActorService::resolveActorTargetPolicy` can resolve actor-vs-actor relation.
- Outdoor and indoor actor state still stores and propagates `hostileToParty` as a central boolean.
- Outdoor and indoor map load currently initialize `hostileToParty` from map bits or
  `isHostileToParty(relationMonsterId)`.
- Actor target policy still receives `hostileToParty`, so party hostility and actor-vs-actor faction relation are
  coupled.
- Wizard Eye marker collection in both outdoor and indoor skips live actors when `hasDetectedParty` is false. That hides
  friendly actors and actor-vs-actor-only actors.
- Event-generated `MonsterBits.Hostile` currently maps to `EvtActorAttribute::Hostile`, and load/runtime code treats
  this as `hostileToParty` in several places. That is risky because OE treats `ACTOR_HOSTILE` as derived, not canonical.
- There are existing tests around Garrote pets and DWI pirate/lizardman combat, but they do not fully lock the OE
  subject/target relation table, d17 default friendliness, and Wizard Eye marker behavior.

Likely structural fix direction:

- Introduce/restore one shared relation resolver that mirrors OE concepts:
  - natural monster type;
  - group equality;
  - ally override;
  - party-controlled actor modes;
  - persistent aggressor-to-party override;
  - charm/enslave/berserk/control states;
  - asymmetric relation lookup.
- Treat `hostileToParty` as a derived runtime answer, not as the stored canonical faction.
- Store explicit persistent actor flags separately from derived `ACTOR_HOSTILE`/minimap marker state.
- Make actor AI ask "subject can target target" and "subject can target party" from the resolver.
- Make Wizard Eye collect visible/nearby valid actors first and choose marker color from party relation afterwards.

## Acceptance Table

These should become unit tests where possible. Map materialization cases can be headless tests if the map loader is
needed.

| ID | Scope | Acceptance |
|---|---|---|
| HST-001 | Pure relation | Lizardman Peasant -> Party is friendly (`0`). |
| HST-002 | Pure relation | Lizardman Warrior -> Party is friendly (`0`). |
| HST-003 | Pure relation | Pirate Warrior Male -> Party is hostile medium (`3`). |
| HST-004 | Pure relation | Wimpy Pirate Warrior Male -> Lizardmen Peasant is hostile long (`4`). |
| HST-005 | Pure relation | Lizardmen Peasant -> Wimpy Pirate Warrior Male is hostile medium (`3`). |
| HST-006 | DWI runtime/headless | In `out01.odm`, pirates and lizardmen can target/damage each other. |
| HST-007 | DWI runtime/headless | In `out01.odm`, a lizardman near party remains party-friendly by default. |
| HST-008 | DWI runtime/headless | In `out01.odm`, a pirate near party is party-hostile and can attack party. |
| HST-009 | Pure relation | Dragon Hunter -> Party is friendly (`0`). |
| HST-010 | Pure relation | Dragon -> Party is friendly (`0`). |
| HST-011 | Pure relation | Naga -> Party is hostile long (`4`). |
| HST-012 | Pure relation | Dragon Hunter -> Naga is hostile long (`4`). |
| HST-013 | Pure relation | Naga -> Dragon Hunter is hostile short (`2`). |
| HST-014 | Pure relation | Dragon Hunter -> Dragon is hostile long (`4`). |
| HST-015 | Pure relation | Dragon -> Dragon Hunter raw table relation is friendly (`0`). |
| HST-016 | Map data | `out05.odm` actors `0..2` are Great Wyrms with `ally = 15`. |
| HST-017 | Map data | `out05.odm` actor `3` is a Dragonslayer with `ally = 15`. |
| HST-018 | Resolver with ally | Dragon Hunter cannot target direct pet dragon with `ally = 15`. |
| HST-019 | Garrote runtime/headless | Default `out05.odm` has party-friendly dragon slayers and dragons. |
| HST-020 | Garrote runtime/headless | Default `out05.odm` has party-hostile nagas. |
| HST-021 | Garrote runtime/headless | Dragon slayers can target nagas. |
| HST-022 | Garrote runtime/headless | Dragon slayers can target normal dragons. |
| HST-023 | Garrote runtime/headless | Dragon slayers cannot target dragon hunter pets. |
| HST-024 | D17 map data/headless | Default `d17.blv` with no relevant QBits has party-friendly dragons. |
| HST-025 | D17 event/headless | D17 default on-load keeps groups `44`, `45`, and `11` non-party-hostile. |
| HST-026 | D17 event/headless | D17 default on-load keeps group `11` hidden. |
| HST-027 | D17 event/headless | With `QBit(21)`, D17 on-load makes groups `44`, `45`, and `11` party-hostile. |
| HST-028 | D17 event/headless | With `QBit(21)`, D17 on-load makes group `11` visible. |
| HST-029 | D17 event/headless | D17 event 453 makes groups `44`, `45`, and `11` party-hostile. |
| HST-030 | Wizard Eye | Wizard Eye shows a nearby friendly live actor as friendly-colored. |
| HST-031 | Wizard Eye | Wizard Eye shows a nearby hostile live actor as hostile-colored. |
| HST-032 | Wizard Eye | Wizard Eye shows a nearby dead actor as corpse-colored independent of hostility. |
| HST-033 | Wizard Eye | Party-friendly actor-vs-actor-hostile actors still show as friendly relative to party. |

## Implementation Notes For Next Slice

Do not patch this by forcing individual maps or actors to `hostileToParty`.

The next implementation should first create the shared relation tests, then change runtime code so outdoor and indoor
both derive:

- `relationToParty`;
- `canTargetParty`;
- `canTargetActor`;
- minimap marker color;
- alert state;
- spell/attack target eligibility;

from the shared resolver. Existing `hostileToParty` fields should either disappear or be clearly derived/cached per
frame from canonical relation state.
