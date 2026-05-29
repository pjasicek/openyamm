# Dialogue System Assumptions And Revisit List

This file tracks dialogue-system behavior that is currently:

- hardcoded as engine semantics
- inferred from data rather than directly declared by data
- or still incomplete / only partially verified

The goal is to keep these cases explicit so they can be revisited later.

## How To Read This

- `Status: engine semantic`
  Means the behavior is hardcoded on purpose as part of MM8-style engine logic.
- `Status: data-backed inference`
  Means the current behavior is based on strong evidence from tables and references, but is not
  yet expressed by a dedicated data field.
- `Status: incomplete`
  Means the current implementation is knowingly partial.

## Current Cases

### Roster-Join Topic Block

- Status: data-backed inference
- Current implementation:
  - roster-join offers are classified during topic-table import in
    [NpcDialogTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/NpcDialogTable.cpp)
  - the loader recognizes topic rows whose imported label is `Roster Join Event` or `Join`
  - the current imported MM8 data still constrains those rows to topic ids `601..649`
- Evidence:
  - [NPC_TOPIC.txt](/home/pjasicek/github/OpenYAMM/assets_dev/Data/NPC_TOPIC.txt) contains a contiguous
    block of rows `601..649` labeled `Roster Join Event` or `Join`
  - OpenMM8 normalizes `Roster Join Event` to `Join` in
    `/home/pjasicek/github/OpenMM8/Assets/OpenMM8/Scripts/Data/Databases/NpcTopicDb.cs`
- Why this is not fully proven:
  - OpenMM8 does not currently implement the whole block generically; its live `TalkEventMgr`
    explicitly handles at least topic `602`, not the whole range
- Revisit:
  - replace the current label-plus-id inference if a more explicit original/OpenMM8 source for
    roster-offer classification is found

### Roster Id And Join Text Mapping

- Status: data-backed inference
- Current implementation:
  - explicit roster-join offer metadata is built when the topic rows are imported in
    [NpcDialogTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/NpcDialogTable.cpp)
  - the current import logic still derives that metadata by:
    - `rosterId = topicId - 600`
    - `inviteTextId = 198 + rosterId * 2`
    - `partyFullTextId = inviteTextId + 1`
- Evidence:
  - the imported `NPC_TOPIC.txt` roster block and `NPC_TOPIC_TEXT.txt` join/full-party text pairs
    line up with that formula for the tested characters
- Why this is not fully proven:
  - there is no dedicated imported table that explicitly declares this mapping, so the loader still
    derives it rather than reading it from a canonical source
- Revisit:
  - replace the formula if a more direct original/OpenMM8 roster-join mapping source is found

### Adventurer's Inn Overflow House

- Status: engine semantic
- Current implementation:
  - full-party roster join redirects the NPC to house id `185`
  - implemented in [OutdoorGameView.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorGameView.cpp)
    and [HeadlessOutdoorDiagnostics.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp)
- Evidence:
  - dialogue text explicitly says the NPC will wait at the Adventurer's Inn
  - Dagger Wound Island inn service event is `185`
- Why this should still be tracked:
  - the inn destination is currently hardcoded, not resolved from house metadata
- Revisit:
  - derive the overflow destination from a better inn/service lookup if one exists in MM8 data

### `Players[...]` Variable Tag `0x013e`

- Status: engine semantic
- Current implementation:
  - EVT variable tag `0x013e` is decoded as `Players[index]` in
    [EventIr.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventIr.cpp)
    and [EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
  - the comparison succeeds when the specified roster id is present in the party
- Evidence:
  - OpenMM8 decompiled scripts use `Players`-style `CanShowTopic` checks for party-member-sensitive
    dialogue, for example the Dyson/Sandro flow
- Why this should still be tracked:
  - the exact original variable taxonomy is still partly reconstructed from script evidence
- Revisit:
  - confirm the full tag meaning against more original-script cases

### QBits `400..449` As Roster-In-Party Reflection

- Status: incomplete
- Current implementation:
  - `QBits[400..449]` are treated as `roster member (qbit - 399) is in party` in
    [EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- Evidence:
  - MM8 `quests.txt` labels this range as roster-character-in-party style bits
- Why this is incomplete:
  - this is currently a read-side convenience in dialogue evaluation, not a thoroughly verified
    recreation of every original engine interaction with those bits
- Revisit:
  - verify whether these should remain synthetic reflections or be modeled as normal persisted qbits

### `ForPartyMember` Selector Values

- Status: incomplete
- Current implementation:
  - selector byte values are currently interpreted as:
    - `0..4` = fixed party member slots
    - `5` = `Players.All`
    - `7` = `Players.Current`
  - implemented in
    [EventRuntime.cpp](/home/pjasicek/github/OpenYAMM/game/events/EventRuntime.cpp)
- Evidence:
  - extracted directly from the raw `Global.EVT` payloads and checked against the decompiled MM8
    scripts
- Why this is incomplete:
  - selector value `6` does not currently appear in the imported MM8 dialogue/event paths we rely on
    here, so it is still unmodeled
- Revisit:
  - add the remaining selector values if a verified MM8 use case for them shows up

### Awards Ownership And Global Award Writes

- Status: incomplete
- Current implementation:
  - awards are now stored per character in
    [Party.cpp](/home/pjasicek/github/OpenYAMM/game/party/Party.cpp)
  - member-scoped `ForPartyMember` award reads/writes use the selected character
  - unscoped party-level award writes still broadcast to all current party members
- Evidence:
  - MM8 uses per-character award semantics together with `ForPartyMember`
- Why this is incomplete:
  - the exact original behavior for every unscoped `Awards[...]` mutation has not been fully audited
    across all scripts
- Revisit:
  - tighten global award write behavior if a script case proves it should not broadcast to all members

### Mastery Teacher Topic Block

- Status: engine semantic
- Current implementation:
  - topics `300..416` are treated as mastery-teacher offers in
    [NpcDialogTable.cpp](/home/pjasicek/github/OpenYAMM/game/tables/NpcDialogTable.cpp)
    and [MasteryTeacherDialog.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/MasteryTeacherDialog.cpp)
- Evidence:
  - OpenMM8 uses the same topic block and a hardcoded mastery-teacher mapping
- Why this should still be tracked:
  - the topic-range classification is hardcoded in the engine rather than expressed by imported data
- Revisit:
  - move the classification behind explicit loader metadata if a cleaner data-driven description is
    introduced later

### Mastery Teacher Skill Mapping

- Status: engine semantic
- Current implementation:
  - topic ids in the mastery-teacher block map to skills via a hardcoded array in
    [MasteryTeacherDialog.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/MasteryTeacherDialog.cpp)
- Evidence:
  - OpenMM8 also uses a hardcoded mastery teacher skill map
- Why this should still be tracked:
  - the mapping is not imported from a table
- Revisit:
  - replace the hardcoded map only if a trustworthy original/OpenMM8 data source for it is added

### Mastery Teacher Base Prices

- Status: engine semantic
- Current implementation:
  - mastery training costs are hardcoded in
    [MasteryTeacherDialog.cpp](/home/pjasicek/github/OpenYAMM/game/gameplay/MasteryTeacherDialog.cpp)
- Evidence:
  - OpenMM8 also hardcodes these base prices in its talk event manager
- Why this should still be tracked:
  - there is no current data table that declares these costs
- Revisit:
  - keep as engine logic unless a canonical data source is found

### `NPCGROUP.TXT` Legacy Location

- Status: incomplete
- Current implementation:
  - generic outdoor NPC news still depends on
    [NPCGROUP.TXT](/home/pjasicek/github/OpenYAMM/assets_dev/Data/EnglishT/NPCGROUP.TXT)
- Evidence:
  - this is the only remaining dialogue-related table still intentionally loaded from `EnglishT`
- Why this is incomplete:
  - it breaks the otherwise cleaned-up canonical dialogue data layout under `assets_dev/Data/`
- Revisit:
  - move it into the canonical data area once a replacement or migration is prepared

### Player-Class / Party-Composition `CanShowTopic` Conditions

- Status: incomplete
- Current implementation:
  - roster-member-sensitive `Players` checks are implemented
  - member-scoped `ClassIs` event execution is implemented through `ForPartyMember`
  - broader player-identity variables beyond the currently verified tags are not fully modeled yet
- Evidence:
  - some dialogue semantics in MM8 depend on richer player/party identity checks
- Revisit:
  - extend runtime condition evaluation once more cases are encountered and verified

### Nested Special Dialogue States Beyond Current Typed Flows

- Status: incomplete
- Current implementation:
  - normal NPC talk, NPC news, house service, roster join, and mastery teacher flows are implemented
  - deeper special nested systems are not fully generalized yet
- Evidence:
  - MM8 dialogue has more special-case typed flows than plain topic -> message/event
- Revisit:
  - add new typed dialogue states as they are identified, instead of folding them into string-based
    or ad hoc logic
