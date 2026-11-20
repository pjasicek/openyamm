# MM9 Scripted Actor Import Goal

## Status

Planning and source audit. The Guaire A'Velsi failure in Drangheim City is the first vertical slice. Implementation is
not complete until the same source-driven classification covers every MM9 map and every actor-like DAT object whose
SCR changes its identity, availability, interaction, combat transition, death result, or lifetime.

The current discovery snapshot found:

- 33 monster-class objects with dialogue behavior across seven maps;
- 137 actor-like objects associated with 40 SCR behavior families involving dialogue, QBits, visibility, removal,
  death, damage, or combat transitions;
- 45 objects whose scripts manipulate visibility or physical presence;
- 35 objects whose scripts manipulate quest keys; and
- five objects with explicit `OnDeath` entry points.

These counts are an audit baseline, not hardcoded acceptance data. The generated audit is authoritative after include
resolution, trigger reachability, and actor-versus-helper classification are implemented.

## Objective

Import MM9 scripted actors without flattening them into ordinary always-present NPCs or hostile monsters merely
because their DAT class matches a generic actor archetype.

The importer must combine each DAT object's properties with the behavior reachable through its assigned SCR. It must
compile the supported actor-local behavior into declarative map data and existing OpenYAMM runtime operations. It must
not introduce a general MM9 SCR virtual machine or duplicate MM9 actor AI.

The completed slice provides:

- correct actor identity and dialogue binding;
- QBit-controlled presence and removal;
- source-required active-state statistic overrides;
- neutral-to-hostile transitions when the source requests them;
- idempotent death actions and ordinary death loot as separate concerns;
- stable save/load behavior; and
- an exhaustive generated classification report for all MM9 DAT maps.

This goal complements `MM9_RUDE_SCR_INTEGRATION.md`. That contract owns dialogue graphs and dialogue-linked rewards.
This document owns the import and runtime lifecycle of the map actors that expose those conversations or participate
in scripted quest encounters.

## Motivating Case: Guaire A'Velsi

Drangheim City source object 352 demonstrates why DAT class alone is insufficient:

- DAT class: `Bandit`;
- DAT name: `CommonerElfMaleA1`;
- source model: `models/PeasantMale.abc`;
- assigned script: `NPC95.scr`;
- dialogue identity: RUDE/NPC id 95, Guaire A'Velsi; and
- `GiveTreasure`: enabled.

The source actor lifecycle is:

1. Before raw quest key 222, the actor is hidden, non-solid, and unaffected by gravity.
2. With key 222 and without key 225, the actor is present, has 300 hit points and 50 armor class, and wanders.
3. Normal use stops and faces the actor toward the party, then opens dialogue 95.
4. Damage starts combat; the actor is not generically hostile before that transition.
5. Death grants raw key 225 if it is absent.
6. Once key 225 is present, the actor is removed and remains absent across reloads.
7. `GiveTreasure` remains an independent request for the normal actor death-loot path.

With the MM9 QBit mapping, raw keys 222 and 225 are QBits 90222 and 90225. The current incorrect conversion treats the
object as an always-visible hostile Bandit because generic monster classification claims it before SCR-derived actor
behavior and dialogue identity are considered.

Guaire is the required end-to-end acceptance example. The implementation must remain generic and source-driven; no
runtime condition may special-case Drangheim City, object 352, `NPC95.scr`, or Guaire's name.

## Non-Negotiable Architecture

- Classify scripted behavior before generic NPC or monster conversion claims a DAT object.
- Treat DAT class as an archetype hint, not complete gameplay identity.
- Use the assigned SCR and its transitively required includes as source behavior evidence.
- Compile a strict supported subset at import time. Do not add a general SCR interpreter or VM.
- Use shared OpenYAMM actor interaction, AI, combat, loot, party QBit, map delta, and save systems.
- Keep generated behavior map-scoped and source-owned under `assets_dev/worlds/mm9/`.
- Bind behavior by stable map source-object identity, not only by script filename, class, actor index, or RUDE id.
- Do not directly edit generated scene or Lua files. Fix the importer or add an explicit reviewed source override.
- Do not copy OpenMM9, OpenEnroth, or other reference-project code.
- Fail generation for required unsupported behavior. Do not silently emit an ordinary monster or a no-op callback.

## Source Authority

Use local sources in this order:

1. The original extracted DAT object, including class, name, model, properties, parameters, and assigned `ScriptName`.
2. The assigned SCR and only the include closure and routines reachable from actor lifecycle triggers.
3. The referenced RUDE graph and MM9 NPC-name data for dialogue identity.
4. Recovered behavior in the local OpenMM9 checkout as a structural and behavioral cross-check.
5. Existing shared OpenYAMM actor systems as the target runtime contract.

An SCR filename such as `NPC95.scr` may suggest identity but is not sufficient classification. Shared and descriptive
scripts such as guard, monk, or `dorude` scripts can bind multiple source objects with different parameters. Conversely,
some monster-named or actor-class objects are encounter helpers or spawners rather than persistent actors.

## Import Classification

Every DAT object that could represent or control an actor must receive exactly one generated ownership classification:

| Classification | Meaning | Runtime representation |
| --- | --- | --- |
| Generic NPC | Ordinary non-hostile actor with no required scripted lifecycle | Existing NPC actor path |
| Generic monster | Ordinary hostile encounter actor | Existing monster actor path |
| Scripted actor | Actor whose required SCR changes identity or lifecycle | Actor plus declarative profile |
| Encounter actor | Hostile actor with supported encounter/death conditions | Monster plus declarative profile |
| Helper/spawner | Script object that controls actors but is not itself an actor | Map event/mechanism profile |
| Unsupported | Required behavior cannot yet be represented faithfully | Generation error |

Classification must consider behavior signatures including:

- `DoRude` and dialogue entry;
- `HasKey`, `GiveKey`, and `TakeKey`;
- visibility, solidity, gravity, disable, enable, and removal operations;
- `OnUse`, `OnFoundPlayer`, `OnDamage`, and `OnDeath` registrations;
- statistic changes such as hit points and armor class;
- combat initialization and hostility transitions;
- spawn, create, respawn, resurrection, or model-changing operations; and
- `GiveTreasure` or other source loot declarations.

The importer must distinguish behavior attached to the actor from behavior attached to a controller. A helper object
must not become a visible actor simply because its DAT class happens to match a monster table row.

## SCR Compilation Boundary

Parse SCR into an importer IR and resolve only routines reachable from relevant object triggers. Compile actor-local
state and actions needed for this goal, including:

- QBit predicates and mutations;
- presence state: visible, enabled, solid, gravity-enabled, and removed;
- active statistic overrides;
- dialogue id and use interaction;
- source-requested hostile-on-damage behavior;
- one-shot death actions; and
- source parameters needed by shared-script bindings.

Do not compile generic MM9 AI from `NPCBASE.inc`, `BASEWANDER.inc`, `BASEMELEE.inc`, follow-player logic, navigation
includes, animation state machines, or social behavior. Map those intentions onto existing shared OpenYAMM actor
profiles such as idle, wander, neutral, hostile, and hostile-on-damage.

The compiler must retain source file, routine, line where available, source object index, and binding parameters in
diagnostics. Unsupported syntax in a required path is an import error. Unreachable generic include machinery does not
make an otherwise supported binding fail.

## Generated Data Contract

The exact schema may follow existing scene and sidecar conventions, but it must carry data equivalent to:

```yaml
scripted_actor_profiles:
  - source_object_index: 352
    source_class: Bandit
    source_name: CommonerElfMaleA1
    source_script: NPC95.scr
    actor_index: 39
    identity:
      display_name: Guaire A'Velsi
      rude_id: 95
    visual:
      source_model: models/PeasantMale.abc
      replacement_family: commoner_elf_male
    presence:
      required_qbits: [90222]
      removed_qbits: [90225]
      hidden_is_non_solid: true
      hidden_uses_gravity: false
    active_overrides:
      hit_points: 300
      armor_class: 50
      movement: wander
    interaction:
      dialogue_on_use: true
      hostile_on_damage: true
    on_death:
      grant_qbits: [90225]
    loot:
      procedural_death_loot: true
```

This example is descriptive, not permission to hand-author Guaire's generated record. The importer must derive it from
the source object and script. Runtime data should use canonical full-width MM9 QBits while retaining raw key values in
generated provenance and audit output.

The profile may be embedded in the generated scene when that is the established ownership point, or stored in a
generated map sidecar. There must be one authoritative generated representation, not duplicated mutable copies in
scene YAML, event Lua, and C++ tables.

## Runtime Ownership

The shared actor runtime owns the live actor. The MM9 profile supplies declarative initial conditions and event actions:

- map load evaluates presence and active overrides against party QBits;
- save restoration applies persistent map delta and QBits without resurrecting a removed actor;
- relevant QBit changes refresh affected actor presence without reloading the map;
- interaction opens the imported RUDE dialogue through the normal actor-use path;
- damage applies the declared disposition transition before shared combat handling;
- death applies declared actions exactly once through the shared actor-death path; and
- procedural death loot uses the existing generic monster loot system independently of quest death actions.

Do not create a second MM9 actor collection, QBit store, loot system, dialogue runner, or save format. Extend indoor and
outdoor world hooks only where required to expose the same shared actor-profile behavior in both world types.

The actor's persistent identity must use source map id plus source object index. Generated actor indexes are output
details and may change after regeneration; they must not be the sole save or binding identity.

## Import Pipeline

### Phase 0: Exhaustive Audit

Add a deterministic audit generator that scans all MM9 DAT maps and their assigned SCR include closures. For every
actor candidate it emits:

- map and source object identity;
- DAT class, name, model, properties, and parameters;
- assigned script and reachable lifecycle triggers;
- detected behavior signatures;
- chosen ownership classification;
- resolved dialogue identity, if any;
- compiled profile features;
- ignored unreachable include behavior with a reason;
- unsupported required operations with source provenance; and
- the resulting scene actor, event, or helper binding.

Emit both a machine-readable report under `assets_dev/worlds/mm9/state/` and a concise human-readable audit. Generated
reports must record their regeneration command and must not be maintained manually.

### Phase 1: Guaire Vertical Slice

Implement the classifier ordering, declarative profile, loader, shared runtime hooks, save behavior, and focused tests
needed for Guaire. Regenerate Drangheim City from source. Remove the incorrect always-hostile Bandit interpretation by
fixing source-driven classification, not by deleting or rewriting the generated actor after conversion.

### Phase 2: Dialogue Actor Families

Apply the same flow to every detected direct-dialogue actor, including shared guard, monk, god, and descriptive-script
families. Resolve identity through actual `DoRude` behavior and binding parameters rather than an `NPC*.scr` filename
heuristic.

The current baseline contains 33 such monster-class objects across Afterworld, Dook's Castle, Drangheim City,
Drangheim Prison, Hall of Gods, Lindisfarne, and Lindisfarne Monastery. The regenerated audit determines the final set.

### Phase 3: Conditional And Death-Scripted Actors

Compile the supported QBit presence, removal, active-stat, hostile-on-damage, and death-action families for legitimate
actors. Group tests by unique script behavior so a shared script bound to many objects is verified once structurally
and at representative parameterized bindings.

### Phase 4: Encounter Helpers And Advanced Lifecycles

Explicitly classify spawn controllers, autoresurrection, scurry/activation gates, model-changing objects, and similar
encounter behavior. Implement supported declarative mechanisms in shared map/event systems. Keep an unsupported
binding as a visible generation failure until its semantics are deliberately implemented.

### Phase 5: Full Regeneration And Closure

Regenerate all MM9 maps, scripted actor profiles, dialogue hooks, and audit reports. Resolve every required unsupported
entry or list it as an explicit scope decision that prevents declaring this goal complete.

## Guaire Acceptance Tests

The Drangheim City test scenario must prove:

1. Without QBit 90222, Guaire is not rendered, pickable, collidable, or gravity-simulated.
2. Granting QBit 90222 while the map is active makes him present without requiring asset regeneration.
3. He appears with Guaire's name and an appropriate commoner visual, not generic Bandit identity.
4. He has 300 hit points and 50 armor class while active.
5. He is non-hostile before attack and opens RUDE dialogue 95 on use.
6. Taking damage starts combat through the shared disposition/AI path.
7. Death grants QBit 90225 exactly once.
8. Any ordinary `GiveTreasure` result uses normal actor death loot and does not replace the QBit action.
9. QBit 90225 removes him and prevents reappearance after map transition, save/load, or process restart.
10. A save made before activation, while active, and after death restores the corresponding state.

## Coverage And Regression Gates

This goal is complete only when all of the following pass:

- The audit enumerates every MM9 DAT map used by the world package; the current expected map count is 45.
- Every actor candidate has exactly one ownership classification and a stable source-object binding.
- Every direct-dialogue actor has a resolved dialogue id or a provenance-rich generation error.
- No dialogue-bearing actor falls through to an always-hostile generic monster unless source behavior requires it.
- Every required QBit, presence, removal, damage, and death operation is compiled or blocks generation explicitly.
- Helper/spawner objects have representative tests proving that they do not become visible generic actors.
- Shared scripts with multiple bindings retain per-object parameters and state.
- Death actions are idempotent, including save/load and repeated corpse interaction.
- Actor presence refreshes on relevant QBit changes and remains stable across map transitions and save/load.
- Regeneration is deterministic and a stale generated report or profile fails the repository check.
- Drangheim City passes a focused headless/runtime scenario covering the complete Guaire lifecycle.
- Representative indoor and outdoor scripted actors pass runtime coverage.
- Existing MM6/MM7/MM8 generic NPC, monster, dialogue, loot, and save tests remain unchanged and passing.

The audit may report informational source behavior intentionally mapped to shared OpenYAMM AI. It may not contain an
unresolved error-severity required behavior when this goal is declared complete.

## Deliverables

- A deterministic all-map scripted-actor audit generator and generated reports.
- SCR parsing/IR support for the required actor lifecycle subset and include reachability.
- Source-driven actor, encounter actor, and helper/spawner classification before generic fallback.
- A generated declarative actor-lifecycle schema with source provenance.
- Scene/sidecar loaders and shared actor runtime hooks.
- Full-width MM9 QBit predicates and actions using the established `90000 + raw key` mapping.
- Dialogue binding derived from reachable `DoRude` behavior.
- Persistent presence, disposition, death-action, and source-object identity behavior.
- Unit tests for classification and compilation.
- Runtime/headless tests for Guaire and representative shared-script, indoor, outdoor, and helper cases.
- Regenerated MM9 maps and events with deterministic stale-output validation.

## Explicit Non-Goals

- A general MM9 SCR interpreter or virtual machine.
- Reimplementation of MM9's complete NPC, monster, navigation, animation, or combat AI.
- Exact runtime use of every original MM9 3D actor model; approved legacy billboard replacements remain valid.
- Manual per-map C++ branches or generated-file edits for Guaire or any other named actor.
- Treating every script-bearing DAT object as an actor.
- Folding quest death actions into procedural treasure generation.
- Changing the global MM9 QBit mapping, RUDE graph contract, or portable item-id contract.
- Broad changes to MM6/MM7/MM8 actor behavior beyond generic hooks required by declarative profiles.

## Completion Definition

The slice is complete when Guaire behaves correctly from quest activation through dialogue, combat, death, loot, map
transition, and save/load; the same source-driven path handles all equivalent dialogue and scripted-actor families; all
45 MM9 maps have a deterministic actor ownership audit; and no required actor lifecycle behavior is silently flattened
into a generic NPC, monster, or inert object.
