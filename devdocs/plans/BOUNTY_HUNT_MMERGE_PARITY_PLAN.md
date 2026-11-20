# Bounty Hunt MMerge Parity Plan

## Goal

Implement MMerge-compatible bounty hunt behavior across MM6, MM7, and MM8, and remove the synthetic blank town hall
clerk participant currently shown in MM6 town halls such as New Sorpigal.

This plan is based on local references only:

- `reference/mmmerge/Scripts/General/BountyHunt.lua`
- `reference/mmmerge/Scripts/Global/StdQuestsFunctions.lua`
- `reference/mmmerge/Scripts/Global/Reputation.lua`
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCData.txt`
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/NPCTopic.txt`
- `reference/mmerge_data_forus/Data/mmmerge.T.lod/2DEvents.txt`
- `reference/OpenEnroth-git/src/GUI/UI/Houses/TownHall.cpp`

Do not copy OpenEnroth or MMerge code. Use these files only as behavioral references.

## Current Gaps

1. MM6 town halls show an extra synthetic proprietor row.
   - Example: house `208`, New Sorpigal Town Hall, has proprietor name/title `Janice, Clerk` in `house_data.txt`
     but no proprietor portrait.
   - The real resident NPC `Janice` is also present in `house_animations.txt` and `npc.txt`, with portrait `0020`.
   - OpenYAMM currently shows both: a blank synthetic `Janice, Clerk` row and the real `Janice` row.

2. MM6 bounty hunt topic is data-driven in MMerge but not routed in OpenYAMM.
   - MMerge assigns topic `1712` directly to real NPCs:
     - `Janice`, house `208`, New Sorpigal.
     - `Earnest`, house `210`, Mist.
     - `Jake`, house `211`, Silver Cove.
   - `NPCTopic.txt` topic `1712` is `Bounty Hunt`.
   - `StdQuestsFunctions.lua` maps `evt.Global[1712]` to `BountyHuntFunctions.SetCurrentHunt()`.
   - OpenYAMM currently exposes bounty through generic town hall service actions instead of this NPC topic path.

3. MM8 bounty hunt topic needs to route through the same shared bounty hunt runtime.
   - MMerge patches the MM8 hardcoded bounty path to call `BountyHuntFunctions.SetCurrentHunt()`.
   - Merged NPC data has Guild of Bounty Hunters NPCs:
     - `Bryant Conlan`, house `895`, topic `579`.
     - `Cahalli Evenall`, house `523`, topic `579`.
   - `NPCTopic.txt` topic `579` is `This Month's Bounty`.

4. Runtime behavior is close but not full MMerge parity.
   - OpenYAMM stores map-based bounty state and uses reward `monster level * 100`, matching MMerge.
   - OpenYAMM spawn placement is currently near the party; MMerge uses random indoor/outdoor spawn-point selection.
   - OpenYAMM kill marking is current-map scoped; MMerge scans all active bounty entries and marks any matching
     monthly monster id.
   - OpenYAMM text, award, reputation, and total bounty updates need to be aligned with MMerge.

## Desired Placement

### MM6

Use real NPC topics, not generic synthetic town hall service rows.

- New Sorpigal Town Hall: `Janice` gets `Bounty Hunt` from topic `1712`.
- Mist Town Hall: `Earnest` gets `Bounty Hunt` from topic `1712`.
- Silver Cove Town Hall: `Jake` gets `Bounty Hunt` from topic `1712`.
- The blank synthetic `Janice, Clerk` / `Earnest, Clerk` / `Jake, Clerk` participant should not appear.
- Do not add `Current Fine` or `Pay Fine` to these MM6 residents unless a separate reference proves it belongs there.

### MM7

Keep town hall service behavior.

- Harmondale, Steadwick, Pierpont, Hall of Dawn, and Hall of Midnight should expose:
  - `Current Fine`
  - `Pay Fine`, when a fine exists
  - `Bounty Hunt`
- This follows the OpenEnroth MM7 town hall path and MMerge's repaired town hall bounty action.

### MM8

Use Guild of Bounty Hunters NPC topics.

- Ravenshore and Garrote Gorge Guild of Bounty Hunters NPCs should expose `This Month's Bounty` topic `579`.
- Topic `579` should call the same shared bounty hunt interaction used by MM6 topic `1712` and MM7 town hall action.

## Implementation Plan

### 1. Preserve Data Ownership

- Do not edit generated Lua event files directly.
- Do not edit imported/generated event output for this feature.
- Prefer runtime routing and shared gameplay code over patching merged TXT rows.
- Treat existing merged `npc.txt`, `npc_topic.txt`, `house_data.txt`, and `house_animations.txt` as the intended
  data source unless a converter bug is found.

### 2. Suppress MM6 Synthetic Town Hall Proprietor Rows

Update the house dialog participant-building logic in `game/events/EventDialogContent.cpp`.

Add a narrow predicate for resident-driven MM6 town halls:

- house service resolves as `TownHall`;
- proprietor picture id is empty or zero;
- house has resident NPCs;
- at least one resident has topic `1712`, or the house id is one of the known merged MM6 town hall bounty houses
  `208`, `210`, `211`.

When the predicate is true:

- do not add the synthetic `HouseProprietor` participant action;
- show only resident NPC actions;
- keep existing special handling for Free Haven High Council;
- do not affect MM7 town halls, which have proprietor portraits and no resident-driven MM6 topic path.

Add a regression test that builds the New Sorpigal Town Hall dialog and asserts:

- no blank `Janice, Clerk` proprietor participant exists;
- real `Frank Fairchild` exists;
- real `Janice` exists and carries her NPC topics.

Add equivalent focused coverage for Mist and Silver Cove if the dialog test helpers make that cheap.

### 3. Add Shared Bounty Hunt Interaction Entry Point

Refactor the current `TownHallBountyHunt` action implementation in `game/gameplay/HouseInteraction.cpp` into a shared
function that can be called by:

- MM7 town hall house action;
- MM6 NPC topic `1712`;
- MM8 NPC topic `579`.

The shared function should:

- use the current map name as the bounty state key, matching `vars.BountyHunt[Map.Name]`;
- return the same kind of user-facing message as current house actions;
- create a new monthly hunt when absent or expired;
- show active hunt text when not completed;
- claim reward when completed and not claimed;
- show already-claimed text when already claimed for the month.

Keep the state implementation in `BountyHuntRuntime` or move more of the state machine there if it makes the call sites
smaller and testable.

### 4. Route NPC Topics

Update NPC topic execution in `game/gameplay/GameplayDialogController.cpp` or the nearest existing NPC topic dispatch
layer.

Add explicit runtime handling for:

- topic `1712`: MM6 `Bounty Hunt`;
- topic `579`: MM8 `This Month's Bounty`.

For these topics:

- call the shared bounty hunt interaction;
- display its returned message in the NPC dialog;
- do not fall through to missing-event text;
- do not require a generated Lua event handler.

Keep the topic ids documented next to the dispatch code so the routing is understandable.

Add tests for:

- topic `1712` on Janice invokes bounty hunt instead of missing-event fallback;
- topic `579` on Bryant/Cahalli invokes bounty hunt instead of static text or missing-event fallback.

### 5. Align Spawn Selection With MMerge

Move bounty spawn selection out of the house-action UI layer and into runtime/world hooks.

Target behavior:

- Indoor: choose a random valid room/facet-based point similar to MMerge's `NewBHSpawnPoint()`.
- Outdoor: choose random map coordinates and avoid water when possible.
- Use a bounded retry loop and a deterministic fallback if no valid point is found.
- Spawn the selected monster as hostile, group `39`, matching MMerge.

Implementation shape:

- add a shared `chooseBountyHuntSpawnPoint()` hook to the world runtime interface;
- implement indoor and outdoor versions near existing world spawn/floor-resolution logic;
- keep collision/floor checks world-specific;
- keep bounty state and reward logic shared.

Add focused tests or headless diagnostics for:

- indoor bounty spawn returns a valid floor-supported point;
- outdoor bounty spawn avoids water on maps where this can be tested deterministically;
- fallback does not crash or spawn at invalid coordinates when no ideal point is found.

### 6. Align Kill Marking

MMerge marks an active bounty entry done when any player-killed monster has the same monthly bounty monster id, scanning
all active entries in `vars.BountyHunt`.

Update OpenYAMM so monster kill handling:

- requires a party/player kill, not environmental or unrelated death;
- scans all active monthly bounty entries, not only the current map key;
- marks each matching unclaimed entry as done;
- keeps current named-global save compatibility or adds an explicit migration/index if scanning named globals is not
  practical.

Add tests for:

- bounty generated on map A can be completed by killing the same monster id on map B, if the entry is still current;
- expired entries are not completed;
- already claimed entries are not re-opened.

### 7. Align Rewards, Reputation, Awards, And Totals

Use MMerge reward semantics:

- reward gold is `monster level * 100`;
- add reward amount to the total bounty counter used by Bounty Hunter promotion checks;
- set the per-character bounty award if OpenYAMM models the MMerge award used by the source games;
- apply the claim-time reputation change from `BountyHunt.lua`;
- preserve the kill-time reputation effect from `Reputation.lua` if it is already represented in OpenYAMM, but verify
  the sign and thresholds against MMerge.

Confirm the OpenYAMM variable mapping before changing totals:

- MMerge variable: `MontersHunted`;
- current OpenYAMM candidate: `EvtVariable::ArenaWinsPage`;
- `EventRuntime::luaIsTotalBountyInRange()` already reads this value for scripted checks.

Add tests for:

- reward gold amount;
- total bounty counter increment;
- Bounty Hunter promotion checks see the incremented total;
- reputation changes match the MMerge scripts for kill and claim;
- repeated claim does not duplicate gold, total bounty, awards, or reputation changes.

### 8. Align Text

Prefer MMerge text sources where already imported:

- hunt text: MMerge `NPCText[133]`;
- reward text: MMerge `NPCText[134]`;
- claimed text: MMerge `NPCText[135]`;
- MM8 guild topic label: `NPCTopic[579]`, `This Month's Bounty`;
- MM6 topic label: `NPCTopic[1712]`, `Bounty Hunt`.

If the text table plumbing does not expose these by numeric id yet, add a small table lookup helper rather than embedding
new hardcoded English strings in gameplay logic.

Add snapshot-style tests for message selection:

- new hunt text;
- active hunt text;
- reward claim text;
- already claimed text.

### 9. Keep Existing MM7 Town Hall Fine Behavior Intact

Do not remove or hide:

- current fine display;
- pay fine action;
- MM7 town hall bounty action.

Add regression tests for one MM7 town hall showing town hall service actions after the MM6 synthetic-row fix.

### 10. Verification Checklist

Manual verification:

- MM6 New Sorpigal Town Hall shows only Frank Fairchild and real Janice; Janice has `Bounty Hunt`.
- MM6 Mist Town Hall shows real resident NPCs; Earnest has `Bounty Hunt`; no blank `Earnest, Clerk`.
- MM6 Silver Cove Town Hall shows real Jake; Jake has `Bounty Hunt`; no blank `Jake, Clerk`.
- MM7 town halls still show fine and bounty service actions.
- MM8 Ravenshore Guild of Bounty Hunters NPC has `This Month's Bounty` and starts/claims a hunt.
- MM8 Garrote Gorge Guild of Bounty Hunters NPC has `This Month's Bounty` and starts/claims a hunt.
- Saving and loading preserves active, done, and claimed bounty state.

Automated verification:

- focused dialog regression tests;
- focused bounty runtime tests;
- build with `cmake --build build --target openyamm -j25`;
- run the relevant unit/regression test target.

## Acceptance Criteria

- No synthetic blank clerk participant appears in MM6 resident-driven town halls.
- MM6 topic `1712` and MM8 topic `579` execute bounty hunt logic.
- MM7 town hall service actions continue to work.
- Bounty generation, completion, reward, total bounty, award, reputation, and text behavior match MMerge unless a
  deliberate OpenYAMM deviation is documented in code and tests.
- Indoor and outdoor bounty monster spawn placement is valid and no longer hardcoded next to the party.
- Save/load keeps bounty state stable across maps and worlds.
