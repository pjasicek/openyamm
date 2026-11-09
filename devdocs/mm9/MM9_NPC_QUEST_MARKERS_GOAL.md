# MM9 NPC Quest Marker Goal

## Status

Implemented. The deterministic source inventory contains 119 bound quest interactions (including 21 authored pure
predicates for dialogue-linked SCR), 71 explicit source-provenance exclusions, and no unresolved candidates. The
shared resolver, eligibility revision, loaded-location cache, MM9-only indoor/outdoor presentation, gameplay setting,
save/map reconstruction, and focused automated/headless gates are in place. Markers anchor to the visible top of the
actor sprite through its opacity mask.

## Objective

Render clear, reactive quest-state markers above MM9 NPCs without adding marker behavior to MM6, MM7, or MM8:

- a gold `!` when the NPC currently offers a quest;
- a grey `?` when the NPC is the intended handoff target for an active quest that is still in progress; and
- a gold `?` when the NPC can currently accept a completed quest or quest stage.

Markers must update promptly when relevant gameplay state changes. They must not be fixed map-import properties,
recomputed continuously every frame, or refreshed by an arbitrary polling timer. The runtime must derive them from
authoritative MM9 content and the current saved party/map state.

This is an assistance and presentation feature. It must not change RUDE choice visibility, journal state, quest
rewards, script execution, NPC availability, or original quest progression.

## Marker Semantics

The marker states are:

| State | Marker | Meaning |
| --- | --- | --- |
| `None` | none | The NPC has no currently relevant quest interaction. |
| `InProgress` | grey `?` | This NPC is the handoff target for an active, incomplete quest stage. |
| `Available` | gold `!` | A currently reachable dialogue path can offer or start a quest or quest stage. |
| `Ready` | gold `?` | A currently reachable dialogue path can complete or hand in an active quest or quest stage. |

When one NPC has several quest interactions in different states, render exactly one marker with this priority (see
the trainer marker below for where `Trainer` falls):

```text
Ready > Available > InProgress > None
```

### Skill Trainer Marker (2026-11-06)

A fourth state, `Trainer`, puts a blue open book (`worlds/mm9/sprites/trainer_marker_book.png`, drawn by
`tools/mm9_import_discovery/generate_mm9_trainer_marker.py`, tinted with the interface's learnable-skill blue) over an
MM9 skill trainer when one of its rows (`skill_trainers.txt`) is shown on some dialogue path and some party member
could take one of its lessons through the shared `evaluateSkillMasteryTraining`: rank, class/race cap, current mastery
and the stat requirements. Gold is left out, so the book also shows where the party can train once it has the money.
The book goes away when nobody can learn anything more there.

The full priority is `Ready > Available > Trainer > InProgress > None`: a trainer with a lesson is more useful than a
quest that only waits. The same resolver and loaded-location cache compute it. Characters change skills, class and
stats in many places, so instead of a party revision the session folds a signature of every member's class, race,
base Intellect/Personality/Endurance and skill levels/masteries into the map stamp each update; an unchanged
signature does no work.

Screenshot tours pause gameplay updates, and the marker cache is rebuilt in the gameplay update, so a tour can show no
markers at all; check markers with a single `debug.screenshot_path` capture instead.

`InProgress` belongs to the intended handoff NPC for the active stage. Do not keep a grey `?` over the original quest
giver when the quest is meant to be handed to a different NPC. Branching quests and stages with several valid handoff
targets may deliberately associate the active stage with more than one NPC.

Completing one quest and exposing a follow-up in the same conversation must produce the correct state after the
conversation action is committed. For example, a gold `?` may become a gold `!` immediately after a handoff.

## Source Of Truth

No single MM9 DAT property identifies a quest giver or quest handoff. Resolve marker state from the combined source
model:

| Source | Responsibility |
| --- | --- |
| Map DAT/imported scene | Identifies the actor, source-object identity, `DoRude` binding, script, and RUDE id. |
| `NPC*.rude` | Defines the conditional dialogue graph, choice reachability, and ordinary-row key mutations. |
| `NPC997.rude` / `quests_overlay.txt` | Defines which full-width QBit conditions make each MM9 journal stage active. |
| Dialogue-linked SCR | Defines additional conditions, object state, rewards, and consequences on dialogue exit. |
| Authored overrides | Resolve exceptional or ambiguous classifications not proven by source structures. |

RUDE remains authoritative for dialogue. Do not classify markers by parsing English prompts or journal prose such as
"return to", "we have completed", or "here is your reward". That would be fragile, localization-dependent, and unable
to represent conditional or branching behavior correctly.

Use the actor's imported MM9 source-object identity in addition to its RUDE id when behavior depends on a generic
script, script parameters, object variables, or an object-specific compiled callback. Several actors may share a RUDE
graph without sharing all script state.

## Generated Quest-Interaction Metadata

Extend the MM9 import pipeline to emit a deterministic, world-owned quest-interaction index, with an exact filename
chosen to match the existing MM9 state/data layout. A suitable shape is:

```text
assets_dev/worlds/mm9/state/quest_interactions.yml
```

Each interaction must retain at least:

- a stable interaction or quest-stage id;
- RUDE id;
- map/source-object identity when the binding is object-specific;
- associated journal entry or entries;
- role of the NPC for that stage, such as offer target or handoff target;
- conditions for `Available`, `InProgress`, and `Ready`;
- the reachable RUDE row/path or SCR consequence that justifies the classification;
- relevant required, forbidden, granted, and removed QBits;
- non-QBit dependencies such as items, class/promotion, skills, mastery, or persisted script variables;
- source file and line/row provenance; and
- whether the record is generated, explicitly overridden, or intentionally excluded.

The generator should construct candidates by combining DAT bindings, RUDE graph reachability, journal-stage
conditions, and the required dialogue-linked SCR subset. It must emit a coverage report for candidates that are
ambiguous, unsupported, or reachable only through behavior that the compiler cannot model.

Keep authored classification overrides separate from generated output. Overrides must name their source interaction,
state why generation is insufficient, and remain narrow. Do not silently guess a marker state for unresolved content.

A deal MM9 keeps in quest keys only, with no journal entry (Drangheim Prison's cook Aymril, dialogue 419, and his
brother Antoni, 427: keys 5004, 369, 370), has no journal stage to mark. The overrides' `key_interactions` author its
marker as `source_kind: keys`: up to three key conditions (`available`, `in_progress`, `ready`, each required and
forbidden QBits) bound to one placed NPC; the runtime shows the first of ready, in progress and available that holds
(`Mm9QuestMarkers.cpp`). Use them only for such journal-less deals. The generator writes the review list of
candidates, [MM9_KEY_DEAL_CANDIDATES](../mm9_rework/MM9_KEY_DEAL_CANDIDATES.md): dialogues on placed NPCs that grant
non-journal keys tested outside their own dialogue (another dialogue, map Lua or an MM9 script).
A candidate reviewed and left without a marker (a cutscene flag, a service, flavour) goes in the overrides'
`key_deal_reviews` with its reason, so the list shows it as reviewed. Most authored entries are steps of journal
quests that no NPC marks (`ready` while the stage's open key is held). MM9 data quirk found in the review: journal
stage 510 ("Find the Green Man") requires key 263, which MM9 never grants, so it never shows; Menja's entry marks the
step instead.

The NPC bindings come from the scenes the game loads (`assets_dev/worlds/mm9/maps/*.scene.yml`, which the converters
write as JSON), not from the editor import: that import lacks the NPCs added or moved by the rework (all of Lindisfarne
Monastery, the Afterworld, the Green Man, Thronheim City's council). Scripted NPCs that the editor import's event
inventories (`dialogue_callbacks`) lack are scanned too, through their script's first dialogue-closing routine
(`onrude`, `onrudeexit`, `onexit`). Author their SCR predicates from the map's Lua handler, which is what the game runs.
Every MM9 promotion quest is offered to any party (`dialogue/promotions.yml`), so no offer may wait for MM9's
per-character promotion keys 401-448, which are never set.

The source audit performed while defining this goal found the following provisional baseline:

- 436 normal NPC RUDE graphs;
- 4,215 normal dialogue rows;
- 59 RUDE ids with a graph-reachable row that grants a key used by the MM9 journal;
- 28 of those RUDE ids with such a mutation directly on a root-node row;
- 208 distinct raw keys used by MM9 journal conditions;
- 144 of those journal keys granted by ordinary RUDE rows; and
- 57 additional journal keys observed only as literal `GiveKey` operations in SCR, with other keys driven by
  parameters, mechanisms, or additional behavior.

These are discovery numbers, not completion claims. The checked-in generator/report must reproduce an authoritative
inventory and explain every difference.

## Runtime Resolution

Implement a pure MM9 quest-marker resolver that answers:

```text
markerFor(loaded actor identity, current gameplay state) -> None | InProgress | Available | Ready
```

The resolver must:

- use the same authoritative condition evaluation as RUDE choice visibility;
- evaluate journal visibility through the shared `JournalQuestTable` semantics;
- consider reachable dialogue paths rather than only immediate root rows;
- preview quest effects without mutating the real party, inventory, dialogue, object, or map state;
- distinguish an active-but-incomplete handoff (`InProgress`) from a currently actionable handoff (`Ready`);
- identify offers that become available through nested dialogue nodes;
- respect object-specific SCR state and parameters where required;
- ignore service-row tail fields that are opcode parameters rather than ordinary QBit actions;
- resolve multiple interactions using the documented priority; and
- return no marker for hidden, removed, dead, hostile, or otherwise non-interactable actors.

Do not speculatively execute generated SCR callbacks to decide a marker. Import the required predicates and effects
into pure metadata that can be evaluated without awarding gold, experience, items, QBits, sounds, or other side
effects.

## Centralized Change Tracking

Marker state is a derived cache over gameplay state. Introduce one centralized monotonic
`dialogueEligibilityRevision` or equivalently scoped revision owned by the authoritative gameplay/session state.

Increment the revision only when a value relevant to dialogue or quest-marker eligibility actually changes,
including:

- party QBits;
- inventory items used by validated RUDE/SCR conditions;
- class and promotion state;
- skills and mastery;
- other validated party facts used by dialogue conditions; and
- persisted map-object or script variables used by object-specific quest interactions.

All authoritative mutation paths must participate. In particular, QBit invalidation belongs in the central party QBit
setter rather than only in the MM9 dialogue controller, so map mechanisms, generated Lua, dialogue, debug/scenario
drivers, and other gameplay systems cannot leave marker state stale. Inventory and character-progression invalidation
must similarly occur in their authoritative mutation paths.

The revision is runtime cache bookkeeping and does not need to be serialized. Save load, new game, world mount
changes, and map load must force a complete initial evaluation.

If party state and map-local script state cannot share one owner cleanly, expose a composite eligibility stamp to the
cache, for example party and loaded-map revisions. Do not introduce forwarding layers that merely duplicate ownership.

## Loaded-Location Cache

On map load:

1. Collect the interactable MM9 actors with resolved RUDE/source-object bindings.
2. Build a compact loaded-location quest-marker cache keyed by stable loaded actor identity.
3. Evaluate every collected actor once against the restored party and map state.
4. Store only the resolved marker state and data needed by presentation.

During gameplay:

1. Compare the cache's evaluated revision/stamp with the current authoritative revision/stamp.
2. If unchanged, do no quest-marker resolution work.
3. If changed, mark the cache stale.
4. Re-evaluate all relevant dialogue actors in the loaded location once during the next gameplay update.
5. Record the new revision/stamp and let the renderer consume the new cached states.

Initially, rebuild every relevant MM9 dialogue actor in the loaded location after a relevant change. The number of
such actors and dialogue rows is small, and this is simpler and safer than maintaining a QBit-to-actor dependency
graph. Multiple state mutations in one frame may advance the revision several times but must result in at most one
cache rebuild for that gameplay update.

Add fine-grained dependency indexing only if profiling demonstrates a real problem. Do not optimize based on the
total number of MM9 dialogue files when only actors in the loaded location need marker states.

When a dialogue row changes state, refresh the active dialogue through its existing visibility path and refresh the
world marker cache through the centralized revision. A quest acceptance or handoff must therefore update the marker
no later than the next gameplay update, not after closing and reopening the map.

## No Polling Timer

Do not use a fixed periodic rebuild, including a ten-second refresh, as the correctness mechanism. Polling would:

- leave a visibly incorrect marker on screen until the next interval;
- perform work when no relevant state changed;
- make tests timing-dependent; and
- mask mutation paths that bypass the authoritative state APIs.

A periodic full comparison may be used temporarily as a development diagnostic to detect missed invalidation, but it
must not ship. Fix every missed authoritative mutation path and remove the diagnostic before completion.

## Presentation

Presentation is MM9-only while this goal remains MM9-only. Use world-space markers anchored above the resolved actor
height:

- gold `!` for `Available`;
- neutral, readable grey `?` for `InProgress`; and
- gold `?` for `Ready`.

The grey state must remain distinguishable from fog, sky, stone interiors, and disabled UI. It should be visibly
subdued relative to gold without becoming illegible. Use an outline or shadow when necessary rather than changing the
semantic color.

Markers should:

- fade or hide beyond a configured assistance distance;
- respect actor visibility and normal occlusion/line-of-sight policy;
- remain screen-readable without growing excessively at close range;
- avoid overlapping the interaction prompt or combat UI;
- optionally repeat the marker state in the targeted-actor interaction prompt;
- expose a gameplay setting that can disable quest markers; and
- avoid loading or evaluating MM9 marker assets when MM9 is not mounted/active.

Keep marker-state calculation in shared gameplay code. Indoor and outdoor world code may supply actor position,
height, visibility, occlusion, and projection, but must not independently reimplement quest semantics or state
priority.

## Save, Load, And World Scope

Marker states are derived and must not be serialized. Serialize only the authoritative QBits, inventory,
character/progression state, and map/script variables already required by MM9 behavior.

After loading a save:

- restore all authoritative state first;
- bind the active world/map and actor source identities;
- force a marker-cache rebuild; and
- render only the state derived from the fully restored snapshot.

Switching maps discards the previous loaded-location cache. Switching away from MM9 must remove the markers and their
runtime work. Mounted MM9 quest state may remain in the global party/save state, but non-MM9 maps must incur no
meaningful marker-resolution cost.

## Verification Gates

Completion requires focused automated coverage proving at least:

- every imported MM9 dialogue actor used by a quest interaction resolves a RUDE/source-object binding;
- generated quest-interaction metadata is deterministic and carries source provenance;
- all candidate quest interactions are classified, explicitly excluded, or reported as unresolved;
- nested dialogue paths can expose an `Available` marker;
- accepting a quest changes gold `!` to the correct grey `?`, gold `?`, follow-up `!`, or no marker;
- an active incomplete stage shows grey `?` only over its intended handoff NPC or NPCs;
- satisfying a completion condition changes grey `?` to gold `?` by the next gameplay update;
- handing in a quest removes gold `?` or replaces it with the correct follow-up marker by the next update;
- an NPC with several interactions follows `Ready > Available > InProgress > None`;
- ordinary no-op setters do not cause unnecessary rebuilds;
- several relevant mutations in one update cause at most one loaded-location rebuild;
- QBit changes from RUDE, generated Lua/SCR, map mechanisms, items, and scenario/test drivers all invalidate the cache;
- inventory, promotion, skill, and object-specific state conditions invalidate the cache where used;
- save/load and map transitions rebuild markers from restored authoritative state;
- hidden, unavailable, hostile, dead, or removed actors do not render markers;
- service rows are not misread as ordinary quest-key mutations;
- MM6, MM7, and MM8 render no quest markers and pay no meaningful runtime cost; and
- marker rendering works for both MM9 indoor and outdoor actors without duplicating quest logic.

Add pure unit tests for classification and priority, importer tests for generated metadata and coverage, and focused
headless runtime scenarios for live state transitions. Include a representative sequence that performs all three
visible states on one NPC:

```text
gold ! -> grey ? -> gold ? -> none or follow-up gold !
```

## Implementation Phases

### Phase 0: Source Inventory And Contract

- Generate the complete DAT/RUDE/journal/SCR quest-interaction inventory.
- Define stable interaction identities, NPC roles, conditions, and source provenance.
- Review ambiguous and branching cases and add narrow authored overrides.
- Make unresolved reachable interactions visible generation failures or explicit exclusions.

### Phase 1: Pure Resolver

- Add typed marker states and generated metadata loading.
- Reuse shared journal and RUDE condition evaluation.
- Implement side-effect-free nested-path and object-specific interaction resolution.
- Cover `None`, `InProgress`, `Available`, `Ready`, and state priority with unit tests.

### Phase 2: Central Invalidation And Cache

- Add the authoritative dialogue-eligibility revision/stamp.
- Wire every relevant party and map-state mutation path.
- Build and lazily refresh the loaded-location actor cache.
- Verify same/next-update transitions without a polling timer.

### Phase 3: MM9 Presentation

- Add the gold `!`, grey `?`, and gold `?` assets/styles.
- Render markers above MM9 indoor and outdoor actors through shared marker presentation data.
- Add distance, visibility, overlap, and user-setting behavior.

### Phase 4: Coverage And Regression Gates

- Run importer coverage across all MM9 dialogue graphs and bindings.
- Add representative map/runtime transition scenarios and save/load coverage.
- Profile loaded-location rebuilds and verify no meaningful non-MM9 cost.
- Remove temporary diagnostics and any periodic validation refresh.

## Completion Standard

This goal is complete when every supported MM9 quest interaction displays the correct gold `!`, grey `?`, gold `?`,
or no marker from current authoritative state; marker changes are visible by the next gameplay update after a relevant
mutation; all classification has source provenance or an explicit narrow override; indoor and outdoor presentation
consume one centralized cached result; no polling timer is required; save/load reconstructs marker state correctly;
and MM6/MM7/MM8 behavior and performance remain unchanged.
