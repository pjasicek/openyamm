# Bind appearance to gameplay

**Review policy:** use [visual calibration](VISUAL_CALIBRATION.md) and the [quick checklist](REVIEW_CHECKLIST.md).
The semantic requirements below still apply, but ordinary outdoor content uses one quick static face/event/target
check. References to runtime/state/transaction tests are diagnostic guidance for new behavior, observed defects or
explicitly requested testing; they are not a requirement to rerun scenarios for every reused service or texture edit.


Use this checklist for both BLV and ODM. Record each requested feature in the manifest, with a stable identity, visible
target, data records, event handlers, state scope and acceptance test. Geometry, random-generation settings and scripted
behavior are separate responsibilities. Reuse shared gameplay systems rather than adding indoor/outdoor copies.

## Houses, dialogue and travel

Two “house entrances” normally mean two event-bearing faces calling `evt.EnterHouse` with different registered house
IDs. This opens the house interface; it does not require modeling two interior rooms. A walkable interior instead needs
a destination map and `evt.MoveToMap` arrival coordinates/facing. Clarify this distinction in the brief through an explicit
assumption or a question when the intended experience is ambiguous.

Resolve house/service/movie/exit data and NPC/topic/greeting references through the merged engine-owned tables under
[data_tables](../assets_dev/engine/data_tables). House IDs from a legacy world are import aliases, not safe new global
IDs. Author the requested dialogue and conditions using the existing event/NPC APIs; verify both displayed text and
actions. A house face, a speak-to-NPC event, and a topic's conditional visibility are distinct bindings. Track all three
when needed. Castle Harmondale and Balthazar demonstrate state-dependent house access.

Every travel destination must exist in the mounted world/mod context. Test arrival clearance, facing, transition hint,
return route, and correct world activation. A MoveToMap call can be a local teleport; classify it by destination rather
than counting it automatically as an exit. Outdoor edge travel also needs navigation metadata; an edge painted like a
road is not a working connection.

## Chests, rewards and map statistics

In a merged base, random tier placeholders draw from the **merged** item registry. They do not imply MM8-only
equipment just because the map is in the MM8 world. If the brief requires an explicit palette, semantic
`loot_containers` can declare `random_item_pool: [5, 15, 35, ...]` and `random_item_count: 3` alongside
`random: true`. The pool must contain unique positive item IDs and the count must fit both the pool and native
chest capacity. This generates ordinary positive native item records without replacement, using the persistent
session/map/container seed. Existing containers without these fields keep their normal tier remapping.
Explicit pool draws use the listed base items; they do not add random enchantments. Correlate the selected
equipment quality and gold with the requested map treasure level and record that policy. Use `fixed_items`
for a guaranteed final reward. Keep original/global registries intact.

Inspect real `.oysav` contents with `build/tools/openyamm_levelgen_inspect_save SAVE.oysav` after actual chest
opening, looting and revisit. The tool is read-only and reports materialized/active chests, seeds, item identities,
enchantments, party resources and house stock. Global base hooks still run: for example, MMerge can insert its
cross-continent letter for an eligible party. Identify such base behavior separately from the map's authored loot.

Create the visible chest target, a valid chest slot/template, the open event binding, and scene/state records together.
Many legacy maps contain **20 chest records with unused slots**. Use reachable `OpenChest` bindings and event flow to
count playable chests. d48 has 20 records but only slot 1 directly bound. Balthazar has no directly bound chest slots.
Direct scanning can miss indirectly called or conditionally exposed chests; trace those cases explicitly.

[ChestRuntime.cpp](../game/gameplay/ChestRuntime.cpp) remaps random item-level placeholders using the map's treasure
level; it is not simply “set every chest to the same number as map_stats.” Negative placeholders represent random loot
levels (including a special level-7 case); positive IDs represent fixed items. Have an authoritative writer encode the
template, not hand-written binary/hex edits. Record requested reward quality, raw template policy, effective map treasure
level, fixed rewards, trap policy and refill behavior. Inspect sampled generated inventory across seeds and verify a
fixed unique reward is exact and not duplicated.

[MapStats](../game/tables/MapStats.h) controls treasure level, disarm difficulty, trap damage dice, perception difficulty,
refill and encounter settings. The surveyed merged MM6 rows all currently have treasure level 6, even New Sorpigal.
Treat that as a fact about this checkout, **not** an original-game progression recipe. Check any active bolster/difficulty
overrides too. Choose new-map balancing deliberately against the party and reference experience, not a copied row.

Chest traps and floor traps are different. Test disarm success/failure, trap damage, opening with the intended interaction
methods, emptied/reopened state, map revisit, refill and save/load. Define whether a quest reward may ever respawn.

## Encounters, fixed actors and unique monsters

Map stats provide three encounter families, weights, difficulty selectors and group-count ranges. Actual spawn records
provide places and types at which those definitions are used. Existing scene actors provide specific actor state.
Scripted summons add another path. Configure the relevant layers explicitly. Zero-weight random families can still have
placed/scripted instances; zero scene actors can still produce a populated map.

Inspect [MapAssetLoader.cpp](../game/maps/MapAssetLoader.cpp) `resolveMonsterNameForSpawn` before encoding native spawn
indices: they select family slots and variants, not arbitrary monster IDs. Position encounters on valid floors/terrain,
with clearance for the actual creature size, groups and hostility. Test pathing through doors and portals, ranged attacks,
LOS, pursuit, encounter overlap and arrival safety. Outdoor encounter territories should relate to routes and guarded
rewards rather than being uniformly scattered.

For “a unique monster named X, stronger than Y, dropping Z,” record a canonical monster definition, display-name binding,
strength changes (HP, attacks, defenses/resistances as relevant), group/hostility, spawn policy and exact item identity.
The actor HP field alone does not override all combat stats. Use a separate registered variant when the species' base
definition should remain unchanged. Check merged `monster_data.txt`, `monster_descriptors.txt`, unique-name resolution,
`monster_death_drops.txt` and `items.txt`; do not mutate a shared species to strengthen one boss.

Use supported carried-item or scripted drop behavior deliberately (`evt.SetMonsterItem` exists). Validate the runtime's
corpse/drop handling so one guaranteed item is awarded once, persists across saves and does not also appear through a
second loot path. Test killing, looting, leaving/reentering, saving before/after death, and refill policy. Check monster
kill/damage hooks if the encounter changes doors or quest state.

## Doors, elevators, plates, traps and secret faces

Treat a mechanism as moving geometry plus control logic plus persistent state. A lever event can move multiple native
doors, and several controls can operate one mechanism. Store that graph explicitly. Validate direction, endpoints,
travel speed, moving vertex ownership, texture movement, obstruction and party carrying. Test both ends of an elevator,
activation while riding, repeated activation, save/load mid-motion where supported, and escape after a reset.

The indoor source compiler currently supports linear door records. Outdoor moving models have a separate existing
`RegisterOutdoorModelMechanism` path in [OutdoorWorldRuntime.cpp](../game/outdoor/OutdoorWorldRuntime.cpp); this is not
automatic reuse of BLV doors. Inspect its naming, event binding, motion, save and collision behavior before generating
an outdoor lift. The Blender bridge for that path still needs implementation/validation.

[FaceEnums.h](../game/FaceEnums.h) defines separate bits for `Clickable`, `TriggerByTouch`, `PressurePlate`,
`TriggerByMonster`, `TriggerByObject`, `IsSecret`, `Invisible`, `Untouchable`, and `TextureMoveByDoor`. A plate is not
automatically a trap, and a trap is not necessarily a plate. Naga Vault has scripted projectile traps without pressure-
plate faces. Configure activation and effects separately; define debounce/cooldown/one-shot behavior so standing on a
plate does not accidentally repeat damage or summons every tick.

Perception does not automatically reveal every pressure plate. The current shared `partyDetectsSecretFaces` check in
[GameMechanics.cpp](../game/gameplay/GameMechanics.cpp) compares effective party Perception against twice the map's
perception difficulty for secret-face detection. If a trap should be detectable, specify its secret marking and intended
visual response separately from its activation. Verify the actual highlight with low/high Perception and the current
party/UI settings. Discovery, clickability, lock/key requirements, collision and open state are independent.

For secret doors, plan the concealed opening, moving leaf, `IsSecret` face semantics, event and reward space. After
triangulation, all relevant faces must retain the flags and logical groups. `SetFacetBit` group identifiers must not be
confused with raw face indices. Check low/high detection, closed/open collision, visibility through the doorway, reward
reachability and persistent state. Never “hide” an opening by removing its floor or making an unrelated wall untouchable.

## Lights and decorations

Record decoration sprite key, orientation, placement and optional interaction. Pictures can be textured wall faces;
torches commonly use decorations plus light behavior. Verify ownership to avoid double illumination. Native static
lights need game-space position, radius, color and activation; Blender watts are not a native radius.

Sector ambient and runtime party/decor/FX lighting contribute alongside explicit BLV lights. The renderer has a bounded
per-draw light selection budget (currently 12 in [IndoorLightingRuntime.h](../game/indoor/IndoorLightingRuntime.h)); that
is not a maximum of 12 lights per dungeon. Zero-radius BLV lights are skipped by the current lighting path. The sampled
MM7 imported BLVs have such lights, so their records are unsuitable as an unquestioned lighting template.

Use pools of light to explain supports, routes and focal objects, with controlled dark stretches and readable floors.
Check torch on/off, light switches before/after load, nearby-room leakage and competing sources. Avoid solving a dark
preview by covering the map in lights without testing actual ambient and runtime behavior.

## State and Lua completion

Specify state scope for each interaction: transient activation, map-persistent variable, per-character reward, party
quest bit, daily charge, map refill or world/global registry. Wells in the outdoor studies demonstrate why “once” needs
an owner and reset policy. On-load handlers must restore textures, light states, hidden faces, NPC access and mechanisms
from authoritative state, rather than awarding the reward again.

The generator emits complete event registration/metadata and placeholders; the agent authors logic. Follow the
[assembly and ownership contract](AUTHORING_CONTRACT.md#events-and-generated-files). Validate bindings, lifecycle hooks,
timers, hints/context actions, monster hooks and conditional topics. Keep a list of unresolved implementations and fail
the finished-map gate until it is empty. Test negative conditions as well as the happy path: missing key/item, wrong
party state, insufficient skill, already-used reward, dead boss, closed gate and return travel.
