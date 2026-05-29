# Implementation Assumptions And Data Gaps

This file tracks cross-system assumptions, heuristics, inferred mappings, and places where
OpenYAMM currently uses engine-defined conventions because the original extracted data does not
fully declare the behavior on its own.

Use this together with:

- [dialogue-system-assumptions.md](/home/pjasicek/github/OpenYAMM/docs/dialogue-system-assumptions.md)
- [plan-finish-outdoor-dwi-complete.md](/home/pjasicek/github/OpenYAMM/codex/plan-finish-outdoor-dwi-complete.md)
- [plan-core-gameplay-and-ui.md](/home/pjasicek/github/OpenYAMM/codex/plan-core-gameplay-and-ui.md)

## Standing Rule

Default to data-first implementations.

That means:

- if the original assets already contain the required data, load it and reference it
- do not hardcode content values in code when they can be resolved from available tables or other
  extracted assets
- do not add heuristics when a real data source exists and can be consumed instead

When the original game data does not fully contain the needed information:

- first verify whether the behavior is original engine semantics rather than missing data
- if extra project-owned data is still needed, prefer:
  - augmenting an existing relevant table when that keeps the model coherent
  - otherwise creating a small dedicated table/file for the missing metadata
- avoid burying such metadata directly in code unless there is a strong reason

Every time code still needs:

- a heuristic
- an inferred mapping
- a hardcoded convention
- a project-owned data augmentation

document it here or in a more specific assumptions file if one already exists for that subsystem.

## Current Scope

This file is intentionally broad.

Examples that belong here:

- missing metadata that must be supplemented outside original assets
- inferred runtime conventions that are not yet fully proven
- places where UI/audio/video linkage must come from project-owned data because the original game
  stored it in binaries rather than extracted tables
- system-level mechanics assumptions outside the dialogue-specific scope

Dialogue-specific assumptions that already have their own tracker should remain documented in
[dialogue-system-assumptions.md](/home/pjasicek/github/OpenYAMM/docs/dialogue-system-assumptions.md).

## Initial Notes

At the moment, this file mainly defines process rather than enumerating many concrete cases.

As broader systems are implemented, add entries here whenever:

- the data source is incomplete
- the runtime behavior is inferred rather than fully proven
- project-owned supplemental data is introduced

## Current Entries

### Monster Relation Matrix

Status:

- project-owned supplemental data

What exists:

- [MONSTER_RELATION_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/MONSTER_RELATION_DATA.txt)

Why:

- the current extracted asset set in this repo already contains `MONSTERS.txt`, `placemon.txt`, and
  `dmonlist.bin`, but not a standalone monster-to-party / monster-to-monster relation table
- party friendliness for monsters cannot be derived correctly from the `Hst` column alone
  (`Lizardman Peasant` on DWI is the concrete counterexample)

Current choice:

- OpenYAMM loads a project-owned `MONSTER_RELATION_DATA.txt` copied from OpenMM8 resources and uses
  it as canonical relation data until/unless a more direct original-data source is recovered

Follow-up:

- if a better original source for monster relations is found, replace this augmentation with that
  source

### Random Encounter Spawn Representative Tier

Status:

- runtime approximation

What exists:

- pre-materialized outdoor actor spawn points with indices `1..3` describe an encounter family, not
  a single fixed A/B/C monster tier

Current choice:

- for initial runtime metadata on those spawn points, OpenYAMM uses the `A` tier monster row as the
  representative monster for:
  - party friendliness lookup
  - hostility-type lookup
  - debug/runtime spawn-point summary state

Why this is acceptable for now:

- the A/B/C variants share the same relation-group identity
- this is only used for spawn-point metadata before a real spawned monster instance exists

Follow-up:

- once spawn materialization is authoritative, the live spawned actor should own the actual chosen
  tier and this representative approximation should not be used beyond the spawn-point definition

### MM8 `CheckMonstersKilled` Actor-Id Policy Value

Status:

- inferred engine semantic, verified against MM8 map scripts

What exists:

- OE references `ActorKillCheckPolicy::KILL_CHECK_ACTORID` as value `3`
- MM8 Dagger Wound Island event data uses policy value `4` for actor-id checks in `Out01.EVT`
  event `460`

Current choice:

- OpenYAMM accepts both:
  - `3` as the OE-style actor-id check
  - `4` as the MM8 actor-id check observed in real map data

Why:

- DWI uses `CheckMonstersKilled(4, 8, 1)` and `CheckMonstersKilled(4, 9, 1)`
- treating only `3` as actor-id would make those real MM8 checks fail

Follow-up:

- verify whether MM8 uses `4` universally for actor-id checks or only in some data/compiler paths

### `SummonMonsters.Level` To Monster Tier Mapping

Status:

- inferred from original data shape and verified against DWI behavior

What exists:

- `SummonMonsters` carries a `Level` field with values `1..3`
- `mapstats.txt` encounter families define picture-name bases, while `MONSTERS.txt` contains the
  concrete A/B/C monster rows
- DWI reinforcement waves use:
  - encounter slot `2`, level `2` for pirate reinforcements
  - encounter slot `1`, level `2` for lizardman reinforcements

Current choice:

- OpenYAMM maps:
  - `1 -> A`
  - `2 -> B`
  - `3 -> C`

Why:

- with that mapping, DWI event `463` summons the expected monsters from data:
  - pirates use `Wimpy Pirate Warrior Male B`
  - lizardmen use `Lizardmen Warrior B`
- this matches the DWI reinforcement wave expectations and the A/B/C structure of `MONSTERS.txt`

Follow-up:

- keep this mapping documented until it is cross-verified on more maps beyond DWI

### Outdoor Monster Movement / AI-Type Semantics

Status:

- inferred engine semantics, guided by OE behavior and original data columns

What exists:

- `MONSTERS.txt` contains:
  - `Move`
  - `AI Type`
  - `Spd`
  - `Rec`
  - ranged-attack columns
- the original data does not directly say:
  - exact outdoor wander radius per movement type
  - exact realtime chase/flee thresholds
  - exact timing behavior for the non-turn-based outdoor loop
  - exact realtime attack-animation duration for outdoor monster actions

Current choice:

- OpenYAMM parses `Move` and `AI Type` directly from `MONSTERS.txt`
- the placed outdoor runtime currently maps movement types to OE-style outdoor ranges:
  - `Short -> 1024`
  - `Med -> 2560`
  - `Long -> 5120`
  - `Free/Global -> 10240`
  - `Stationary -> 0`
- flee thresholds currently follow OE-style AI semantics:
  - `Wimp` always flees when engaged
  - `Normal` flees below 20% HP
  - `Aggress` flees below 10% HP
  - `Suicidal` never flees
- attack recovery and attack action duration are treated separately:
  - `Rec` drives the cooldown/recovery window
  - the visible realtime attack action currently uses a shorter derived duration
  - this preserves the OE-style "attack finishes, then monster can still be recovering" behavior
    until exact animation timing is reconstructed from runtime sprite data
- hostile attack-style selection is now parsed from the real MM8 combat columns instead of the old
  boolean shortcut:
  - column `19` -> `attack1MissileType`
  - column `20` -> `attack2Chance`
  - column `23` -> `attack2MissileType`
  - column `24` -> `spell1UseChance`
  - column `25` -> `spell1`
  - column `26` -> `spell2UseChance`
  - column `27` -> `spell2`
- OpenYAMM currently derives runtime attack buckets from those fields as:
  - `attack1 missile` -> ranged-primary
  - otherwise any ranged/spell secondary with nonzero chance -> mixed melee+ranged
  - otherwise -> melee-only
- non-hostile placed actors are allowed to idle-wander within their movement radius, but still do not
  engage the party unless another hostility path marks them hostile

Why:

- the content classification is data-driven
- the runtime distances and flee thresholds are engine behavior, not table content
- OE provides a solid behavior reference here without being copied directly
- allowing idle wandering matches outdoor monster behavior more closely while keeping hostility
  transitions explicit in runtime state

Follow-up:

- verify these outdoor realtime thresholds against more original MM8 behavior
- replace the temporary ranged-release combat hook with real projectile spawning later
- revisit richer civilian/patrol/job behavior once those higher-level systems exist

### Monster Action Sprite Slot Mapping

Status:

- inferred engine semantic, strongly data-backed

What exists:

- `dmonlist.bin` monster entries expose eight sprite-name slots
- OE maps those slots onto actor animation ids in this order:
  - standing
  - walking
  - melee attack
  - ranged attack
  - hit
  - dying
  - dead
  - bored

Current choice:

- OpenYAMM uses that same slot order as the authoritative mapping for placed-monster rendering

Why:

- the original monster data clearly stores multiple action sprite names, but the slot meaning is an
  engine semantic rather than explicit table text
- this mapping is the cleanest way to make runtime animation state use the original sprite data

Follow-up:

- keep this documented until it is cross-verified on more monster families and indoor actors

### Friendly-NPC Aggro Spread Faction Matching

Status:

- data-backed approximation

What exists:

- OE spreads player-hit aggro with `AggroSurroundingPeasants(...)`, using internal monster
  ally/race metadata that OpenYAMM does not currently load
- OpenYAMM does already load the monster relation-family labels from
  [MONSTER_RELATION_DATA.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/MONSTER_RELATION_DATA.txt)

Current choice:

- when the party attacks a previously friendly outdoor actor, OpenYAMM spreads aggro to nearby
  same-faction actors within `4096`
- same-faction is currently inferred from the monster relation-family label:
  - same relation-family index counts as same faction
  - otherwise the first significant word from the relation label is used as the faction key
  - leading `Wimpy` is ignored so pirate variants stay grouped with pirates

Why:

- this gives the intended DWI behavior for lizardmen and pirates without hardcoding map-specific
  factions in code
- it keeps the logic data-backed until OE-style ally/race metadata is loaded directly

Follow-up:

- replace this with a more direct OE-equivalent faction source if/when ally/race monster metadata is
  available in the runtime
